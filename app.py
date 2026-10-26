import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from engine import Manager
from platform_support import VERSION, data_directory, open_directory
from ui import Button, Panel, Wallpaper, label, INK, MUTED, SURFACE, BLUE


def size(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} PB'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('OpenDownload — Download Manager')
        self.geometry('1320x800')
        self.minsize(980, 560)
        self.configure(bg='white')
        self.manager = Manager(data_directory() / 'history.json')
        self.directory = tk.StringVar(value=str(Path.home() / 'Downloads'))
        self.filter = tk.StringVar(value='All downloads')
        self.search = tk.StringVar()
        self.limit = tk.StringVar(value='0')
        self.sort = tk.StringVar(value='Newest first')
        self.last_save = time.monotonic()
        from view import build
        build(self)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.refresh)

    def window_material(self):
        # Rounded Windows 11 frame when supported; the glass palette works on older Windows.
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd,33,ctypes.byref(value),4)
            color = ctypes.c_int(0x00f8ede9)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd,35,ctypes.byref(color),4)
        except (AttributeError, OSError):
            pass

    def selected(self):
        ids = set(self.table.selection())
        return [j for j in self.manager.jobs if j.id in ids]

    def add_dialog(self):
        win = tk.Toplevel(self)
        win.title('Add downloads')
        win.geometry('680x470')
        win.configure(bg=SURFACE)
        win.transient(self)
        win.grab_set()
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill='both', expand=True)
        label(frame, 'Add download', 16, True).pack(anchor='w', pady=(0,6))
        label(frame, 'URLs, one per line.', 10, color=MUTED).pack(anchor='w')
        urls = tk.Text(frame, height=7, font=('Segoe UI', 11), bg='#edf2fa', fg=INK, insertbackground=BLUE, relief='flat', borderwidth=0, padx=14, pady=12)
        urls.pack(fill='both', expand=True, pady=8)
        try:
            clipboard = self.clipboard_get().strip()
            if clipboard.startswith(('http://', 'https://')):
                urls.insert('1.0', clipboard)
        except tk.TclError:
            pass
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=6)
        ttk.Entry(row, textvariable=self.directory).pack(side='left', fill='x', expand=True)
        def browse():
            chosen = filedialog.askdirectory(parent=win, initialdir=self.directory.get())
            if chosen:
                self.directory.set(chosen)
        Button(row, text='Browse…', command=browse, width=90).pack(side='right', padx=(8,0))
        connections = tk.StringVar(value='4')
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=8)
        ttk.Label(row, text='Connections per file: ').pack(side='left')
        ttk.Combobox(row, textvariable=connections, values=['1', '2', '4', '8'], state='readonly', width=4).pack(side='left')
        def add(queued):
            links = [x.strip() for x in urls.get('1.0','end').splitlines() if x.strip()]
            try:
                if not links:
                    raise ValueError('Enter at least one URL.')
                from urllib.parse import urlsplit
                if any(urlsplit(link).scheme not in ('http','https') or not urlsplit(link).hostname for link in links):
                    raise ValueError('Each line must contain a full HTTP or HTTPS URL.')
                for link in links:
                    job = self.manager.add(link, self.directory.get(), int(connections.get()))
                    if not queued:
                        job.status = 'Paused'
                self.manager.save()
                win.destroy()
            except Exception as exc:
                messagebox.showerror('Cannot add download', str(exc), parent=win)
        Button(row, text='Add paused', command=lambda:add(False), width=110).pack(side='right', padx=4)
        Button(row, text='Download', command=lambda:add(True), width=110, primary=True).pack(side='right')
        urls.focus_set()

    def resume(self):
        self.manager.running = True
        for job in self.selected():
            self.manager.resume(job)
        self.manager.save()

    def pause(self):
        for job in self.selected():
            self.manager.pause(job)
        self.manager.save()

    def pause_all(self):
        self.manager.running = False
        for job in self.manager.jobs:
            self.manager.pause(job)
        self.manager.save()

    def start_queue(self):
        self.manager.running = True
        for job in self.manager.jobs:
            if job.status == 'Paused':
                self.manager.resume(job)

    def open_folder(self):
        selected = self.selected()
        path = Path(selected[0].destination).parent if selected else Path(self.directory.get())
        path.mkdir(parents=True, exist_ok=True)
        try:
            open_directory(path)
        except OSError as exc:
            messagebox.showerror('Cannot open folder', str(exc))

    def remove(self):
        for job in self.selected():
            if job.id in self.manager.workers:
                messagebox.showinfo('Download is active', 'Pause the download and wait for it to stop before removing it.')
                return
        for job in self.selected():
            self.manager.jobs.remove(job)
        self.manager.save()

    def show_selection(self, event=None):
        selected = self.selected()
        if not selected:
            self.detail.configure(text='Select a download to view its details.')
            for value in self.detail_values.values():
                value.configure(text='—')
            self.progress_bar['value'] = 0
            self.progress_caption.configure(text='No download selected')
            return
        job = selected[0]
        self.detail.configure(text=job.error or Path(job.destination).name)
        values = {'File':Path(job.destination).name, 'URL':job.url,
                  'Save to':job.destination, 'Status':job.status,
                  'Size':size(job.total) if job.total else 'Unknown',
                  'Downloaded':size(job.done), 'Speed':size(job.speed)+'/s',
                  'Connections':str(job.connections)}
        for key,value in values.items():
            self.detail_values[key].configure(text=value)
        percent = min(100, job.done/job.total*100) if job.total else 0
        self.progress_bar['value'] = percent
        self.progress_caption.configure(text=f'{percent:.1f}%  ·  {size(job.done)} of {size(job.total)}' if job.total else size(job.done))

    def details(self, event=None):
        selected = self.selected()
        if selected:
            job = selected[0]
            messagebox.showinfo('Download details', f'{job.url}\n\n{job.destination}\n\n{job.status}\n{job.error}')

    def set_limit(self):
        try:
            limit = int(self.limit.get())
            if limit < 0:
                raise ValueError()
            self.manager.limit = limit
        except ValueError:
            messagebox.showerror('Invalid limit', 'Enter a whole number of KB/s, or 0 for unlimited.')

    def refresh(self):
        self.manager.tick()
        visible = set()
        for job in self.manager.jobs:
            if self.filter.get() != 'All downloads' and job.status != self.filter.get():
                continue
            if self.search.get().lower() not in Path(job.destination).name.lower():
                continue
            visible.add(job.id)
            percent = min(100, job.done / job.total * 100) if job.total else 0
            eta = max(0, int((job.total-job.done)/job.speed)) if job.speed and job.total else None
            values = (Path(job.destination).name, size(job.total) if job.total else 'Unknown',
                      f'{percent:.1f}%' if job.total else size(job.done), job.status,
                      size(job.speed)+'/s' if job.speed else '—', f'{eta//60}:{eta%60:02}' if eta is not None else '—')
            if self.table.exists(job.id):
                self.table.item(job.id, values=values, tags=(job.status,))
            else:
                self.table.insert('', 'end', iid=job.id, values=values, tags=(job.status,))
        for ident in self.table.get_children():
            if ident not in visible:
                self.table.delete(ident)
        self.footer.configure(text=f'{len(self.manager.jobs)} downloads  ·  {len(self.manager.workers)} active')
        self.transfer.configure(text='↓  '+size(sum(j.speed for j in self.manager.jobs))+'/s')
        ordered = sorted((j for j in self.manager.jobs if j.id in visible),
                         key=(lambda j: Path(j.destination).name.casefold()) if self.sort.get() == 'Name' else (lambda j:self.manager.jobs.index(j)),
                         reverse=self.sort.get() == 'Newest first')
        for index, job in enumerate(ordered):
            self.table.move(job.id, '', index)
        self.empty.place_forget()
        if not visible:
            self.empty_title.configure(text='No downloads yet' if not self.manager.jobs else 'No matching downloads')
            self.empty_hint.configure(text='Add a download to get started.' if not self.manager.jobs else 'Change your search or filter.')
            self.empty.place(relx=.5, rely=.48, anchor='center')
        self.show_selection()
        if time.monotonic()-self.last_save > 5:
            self.manager.save()
            self.last_save = time.monotonic()
        self.after(300, self.refresh)

    def close(self):
        self.pause_all()
        self.detail.configure(text='Saving download progress…')
        self.withdraw()
        def wait():
            if any(t.is_alive() for t in self.manager.workers.values()):
                self.after(100, wait)
            else:
                self.manager.save()
                self.destroy()
        wait()


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        # Exercise the bundled Tk runtime without touching real download history.
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as folder:
            os.environ['OPENDOWNLOAD_DATA_DIR'] = folder
            app = App()
            app.update()
            app.refresh()
            app.add_dialog()
            app.update()
            Path(sys.argv[2]).write_text(json.dumps({'ok': True, 'frozen': bool(getattr(sys, 'frozen', False)),
                'tk': tk.TkVersion, 'version': VERSION}), encoding='utf-8')
            app.destroy()
    else:
        App().mainloop()
