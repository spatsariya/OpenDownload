"""Capture the app with fictitious, local-only sample data for the website."""
import ctypes
import tempfile
import sys
from pathlib import Path
from PIL import ImageGrab

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from app import App
from engine import Manager

with tempfile.TemporaryDirectory() as folder:
    app=App()
    app.geometry('1320x740+50+50')
    app.manager=Manager(Path(folder)/'history.json')
    app.manager.running=False
    for name,state,total,done in [('Design-resources.zip','Complete',238000000,238000000),
            ('Product-walkthrough.mp4','Complete',86000000,86000000),
            ('Desktop-wallpapers.zip','Complete',42000000,42000000),
            ('Project-backup.zip','Paused',920000000,390000000),
            ('Release-notes.pdf','Queued',2400000,0),
            ('Sample-library.zip','Paused',140000000,62000000)]:
        job=app.manager.add('https://example.com/'+name,folder)
        job.destination=str(Path('C:/Users/You/Downloads')/name)
        job.status,job.total,job.done=state,total,done
    app.update()
    app.refresh()
    app.table.selection_set(app.manager.jobs[3].id)
    app.show_selection()
    app.update()
    app.after(450,app.quit)
    app.mainloop()
    ImageGrab.grab(window=ctypes.windll.user32.GetParent(app.winfo_id())).save(root/'docs'/'assets'/'app-preview.png')
    app.destroy()
