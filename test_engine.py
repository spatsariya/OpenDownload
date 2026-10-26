import http.server
import tempfile
import threading
import unittest
from pathlib import Path
from engine import Download, Manager, safe_name

DATA = bytes(range(256)) * 16384


class Server(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        start, end = 0, len(DATA)-1
        ranged = self.headers.get('Range') and self.path != '/no-range'
        if ranged:
            start_text, end_text = self.headers['Range'][6:].split('-')
            start, end = int(start_text), int(end_text) if end_text else end
        if start >= len(DATA):
            self.send_response(416)
            self.end_headers()
            return
        self.send_response(206 if ranged else 200)
        self.send_header('Content-Length', str(end-start+1))
        self.send_header('ETag', '"test-v1"')
        if ranged:
            self.send_header('Content-Range', f'bytes {start}-{end}/{len(DATA)}')
        self.end_headers()
        try:
            self.wfile.write(DATA[start:end+1])
        except (ConnectionError, OSError):
            pass


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Server)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_segmented_integrity(self):
        job = Download(self.url+'/file', self.root/'file')
        job.run()
        self.assertEqual(job.status, 'Complete', job.error)
        self.assertEqual(Path(job.destination).read_bytes(), DATA)

    def test_range_ignored_fallback(self):
        job = Download(self.url+'/no-range', self.root/'file')
        job.run()
        self.assertEqual(job.status, 'Complete', job.error)
        self.assertEqual(Path(job.destination).read_bytes(), DATA)

    def test_pause_resume(self):
        for connections in (1, 4):
            with self.subTest(connections=connections):
                job = Download(self.url+'/file', self.root/f'file{connections}', connections=connections)
                original = job._progress
                def progress(count):
                    original(count)
                    job.stop.set()
                job._progress = progress
                job.run()
                self.assertEqual(job.status, 'Paused', job.error)
                self.assertGreater(job.done, 0)
                self.assertLess(job.done, len(DATA))
                job.stop.clear()
                job._progress = original
                job.run()
                self.assertEqual(job.status, 'Complete', job.error)
                self.assertEqual(Path(job.destination).read_bytes(), DATA)

    def test_no_overwrite(self):
        path = self.root/'existing'
        path.write_bytes(b'keep me')
        job = Download(self.url+'/file', path)
        job.run()
        self.assertEqual(job.status, 'Error')
        self.assertEqual(path.read_bytes(), b'keep me')

    def test_pause_after_final_chunk(self):
        job = Download(self.url+'/file', self.root/'file', connections=1)
        progress = job._progress
        def pause_at_end(count):
            progress(count)
            if job.done == len(DATA):
                job.stop.set()
        job._progress = pause_at_end
        job.run()
        self.assertEqual(job.status, 'Paused')
        job.stop.clear()
        job._progress = progress
        job.run()
        self.assertEqual(job.status, 'Complete', job.error)
        self.assertEqual(Path(job.destination).read_bytes(), DATA)

    def test_queue_and_persistence(self):
        manager = Manager(self.root/'history.json')
        a = manager.add(self.url+'/file', self.root)
        b = manager.add(self.url+'/file', self.root)
        self.assertNotEqual(a.destination, b.destination)
        manager.tick()
        for thread in manager.workers.values():
            thread.join(10)
        manager.tick()
        self.assertEqual([j.status for j in manager.jobs], ['Complete', 'Complete'])
        restored = Manager(manager.state)
        self.assertEqual([j.status for j in restored.jobs], ['Complete', 'Complete'])

    def test_invalid_url_and_safe_name(self):
        with self.assertRaises(ValueError):
            Download('file:///etc/passwd', self.root/'file')
        self.assertEqual(safe_name('https://example.com/CON'), '_CON')
        self.assertNotIn('/', safe_name('https://example.com/a%2Fb'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
