"""Independent HTTP download engine. Python standard library only."""
import concurrent.futures
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


def safe_name(url):
    name = urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1])
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip(' .')[:180] or 'download'
    if name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}:
        name = '_' + name
    return name


class Download:
    def __init__(self, url, destination, ident=None, connections=4):
        if urllib.parse.urlsplit(url).scheme not in ('http', 'https'):
            raise ValueError('Use an HTTP or HTTPS URL.')
        self.url, self.destination = url, str(destination)
        self.id = ident or uuid.uuid4().hex
        self.connections = connections
        self.status, self.error = 'Queued', ''
        self.total = self.done = 0
        self.speed = 0
        self.limit = 0
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self._start = self._initial = 0

    @property
    def work(self):
        return Path(self.destination).parent / ('.opendownload-' + self.id)

    def record(self):
        return dict(url=self.url, destination=self.destination, ident=self.id,
                    connections=self.connections, status=self.status, total=self.total, done=self.done)

    def request(self, headers=None, method=None):
        return urllib.request.urlopen(urllib.request.Request(self.url, method=method,
            headers={'User-Agent': 'OpenDownload/1.0', 'Accept-Encoding': 'identity', **(headers or {})}), timeout=20)

    def _progress(self, count):
        with self.lock:
            self.done += count
            elapsed = max(time.monotonic() - self._start, .001)
            self.speed = (self.done - self._initial) / elapsed
            delay = (self.done - self._initial) / self.limit - elapsed if self.limit else 0
        if delay > 0:
            self.stop.wait(delay)

    def _part(self, index, begin, end, validator):
        part = self.work / str(index)
        size = part.stat().st_size if part.exists() else 0
        remaining = end - begin + 1 - size
        if remaining < 0:
            raise ValueError('Partial file is larger than expected.')
        if not remaining:
            return
        headers = {'Range': f'bytes={begin+size}-{end}', 'If-Range': validator}
        with self.request(headers) as response:
            expected = f'bytes {begin+size}-{end}/{self.total}'
            if response.status != 206 or response.headers.get('Content-Range') != expected:
                raise ValueError('Server did not honor the requested range. Retry with one connection.')
            with part.open('ab') as stream:
                while remaining and not self.stop.is_set():
                    chunk = response.read(min(65536, remaining))
                    if not chunk:
                        raise IOError('Server closed the connection before the file was complete.')
                    stream.write(chunk)
                    remaining -= len(chunk)
                    self._progress(len(chunk))

    def run(self):
        self.status, self.error = 'Downloading', ''
        try:
            self.work.mkdir(parents=True, exist_ok=True)
            # Probe with GET: some download hosts reject HEAD. Never assume range support.
            with self.request({'Range': 'bytes=0-0'}) as response:
                match = re.fullmatch(r'bytes 0-0/(\d+)', response.headers.get('Content-Range', ''))
                total = int(match[1]) if match and response.status == 206 else 0
                validator = response.headers.get('ETag') or response.headers.get('Last-Modified', '')
                if validator.startswith('W/'):
                    validator = response.headers.get('Last-Modified', '')
                segmented = bool(total and validator and self.connections > 1)
            metadata = dict(url=self.url, total=total, validator=validator,
                            connections=self.connections if segmented else 1)
            meta_path = self.work / 'metadata.json'
            old = json.loads(meta_path.read_text()) if meta_path.exists() else None
            if old != metadata or not validator:
                for part in self.work.iterdir():
                    if part.name.isdigit():
                        part.unlink()
            meta_path.write_text(json.dumps(metadata))
            self._start = time.monotonic()
            self.done = sum(p.stat().st_size for p in self.work.iterdir() if p.name.isdigit())
            self._initial = self.done
            self.total = total
            if segmented:
                count = min(self.connections, total)
                with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
                    futures = [pool.submit(self._part, i, total*i//count, total*(i+1)//count-1, validator)
                               for i in range(count)]
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                        except Exception:
                            self.stop.set()
                            raise
            else:
                self._single(validator)
            if self.stop.is_set():
                self.status = 'Paused'
                return
            # Exclusive create protects existing user files, including collision races.
            destination = Path(self.destination)
            created = False
            try:
                with destination.open('xb') as output:
                    created = True
                    for part in sorted((p for p in self.work.iterdir() if p.name.isdigit()), key=lambda p:int(p.name)):
                        with part.open('rb') as source:
                            while chunk := source.read(1024*1024):
                                output.write(chunk)
            except Exception:
                if created:
                    destination.unlink(missing_ok=True)
                raise
            self.status = 'Complete'
            # A cleanup failure must not discard an already committed download.
            try:
                for part in self.work.iterdir():
                    part.unlink()
                self.work.rmdir()
            except OSError:
                pass
        except Exception as exc:
            self.status, self.error = 'Error', str(exc)
        finally:
            self.speed = 0

    def _single(self, validator):
        part = self.work / '0'
        offset = part.stat().st_size if part.exists() else 0
        if validator and self.total and offset == self.total:
            return
        headers = {'Range': f'bytes={offset}-', 'If-Range': validator} if offset and validator else {}
        with self.request(headers) as response:
            resumed = bool(offset and response.status == 206)
            if resumed:
                match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
                if not match or int(match[1]) != offset:
                    raise ValueError('Invalid resume response.')
                self.total = int(match[3])
            else:
                offset = self.done = self._initial = 0
                self.total = int(response.headers.get('Content-Length', 0))
            with part.open('ab' if resumed else 'wb') as output:
                while not self.stop.is_set():
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    output.write(chunk)
                    self._progress(len(chunk))
            if not self.stop.is_set() and self.total and self.done != self.total:
                raise IOError('Incomplete download; resume to retry.')


class Manager:
    def __init__(self, state):
        self.state = Path(state)
        self.jobs = []
        self.workers = {}
        self.parallel = 2
        self.limit = 0
        self.running = True
        if self.state.exists():
            try:
                for row in json.loads(self.state.read_text(encoding='utf-8')):
                    job = Download(row['url'], row['destination'], row['ident'], row.get('connections', 4))
                    job.status = row['status'] if row['status'] in ('Complete', 'Paused', 'Error') else 'Paused'
                    job.total, job.done = row.get('total', 0), row.get('done', 0)
                    self.jobs.append(job)
            except (ValueError, KeyError, TypeError):
                # Preserve malformed state for diagnosis rather than overwriting it.
                self.state.rename(self.state.with_suffix('.corrupt-' + uuid.uuid4().hex + '.json'))

    def save(self):
        self.state.parent.mkdir(parents=True, exist_ok=True)
        temp = self.state.with_suffix('.tmp')
        temp.write_text(json.dumps([job.record() for job in self.jobs], indent=2), encoding='utf-8')
        os.replace(temp, self.state)

    def add(self, url, directory, connections=4):
        target = Path(directory).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        name = safe_name(url)
        path = target / name
        occupied = {j.destination for j in self.jobs}
        i = 1
        while path.exists() or str(path) in occupied:
            path = target / f'{Path(name).stem} ({i}){Path(name).suffix}'
            i += 1
        job = Download(url, path, connections=connections)
        self.jobs.append(job)
        self.save()
        return job

    def tick(self):
        for ident, thread in list(self.workers.items()):
            if not thread.is_alive():
                del self.workers[ident]
                self.save()
        if self.running:
            for job in self.jobs:
                if len(self.workers) >= self.parallel:
                    break
                if job.status == 'Queued' and job.id not in self.workers:
                    job.stop.clear()
                    job.status = 'Downloading'
                    thread = threading.Thread(target=job.run, daemon=True)
                    self.workers[job.id] = thread
                    thread.start()
        for job in self.jobs:
            job.limit = self.limit * 1024 / max(len(self.workers), 1)

    def pause(self, job):
        if job.id in self.workers:
            job.stop.set()
        elif job.status == 'Queued':
            job.status = 'Paused'

    def resume(self, job):
        if job.id not in self.workers and job.status != 'Complete':
            job.status, job.error = 'Queued', ''

