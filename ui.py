"""Small, dependency-free widgets for the frosted desktop theme."""
import math
import tkinter as tk

INK = '#24324b'
MUTED = '#7b879c'
SURFACE = '#f8faff'
BLUE = '#3478f6'


def background(widget):
    try:
        return widget.cget('bg')
    except tk.TclError:
        return SURFACE


def rounded(canvas, x1, y1, x2, y2, r=16, **kwargs):
    return canvas.create_polygon(x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
        x2,y2-r, x2,y2, x2-r,y2, x1+r,y2, x1,y2, x1,y2-r,
        x1,y1+r, x1,y1, smooth=True, splinesteps=24, **kwargs)


class Button(tk.Canvas):
    def __init__(self, parent, text, command, width=110, primary=False, quiet=False):
        super().__init__(parent, width=width, height=38, bg=background(parent),
                         highlightthickness=0, cursor='hand2', takefocus=1)
        self.text, self.command = text, command
        self.primary, self.quiet, self.active = primary, quiet, False
        self.hover = False
        self.bind('<Enter>', lambda e:self.set_hover(True))
        self.bind('<Leave>', lambda e:self.set_hover(False))
        self.bind('<Button-1>', lambda e:self.command())
        self.bind('<Return>', lambda e:self.command())
        self.bind('<space>', lambda e:self.command())
        self.bind('<FocusIn>', lambda e:self.draw())
        self.bind('<FocusOut>', lambda e:self.draw())
        self.bind('<Configure>', lambda e:self.draw())
        self.draw()

    def set_hover(self, value):
        self.hover = value
        self.draw()

    def draw(self):
        self.delete('all')
        w = max(self.winfo_width(), int(self.cget('width')))
        fill = '#2564de' if self.hover and self.primary else BLUE if self.primary else '#dce8fc' if self.active else '#e8edf6' if self.hover else self.cget('bg') if self.quiet else '#edf1f8'
        outline = BLUE if self.focus_get() == self else '#ffffff' if not self.primary else fill
        rounded(self, 1,1,w-2,36,12,fill=fill,outline=outline)
        self.create_text(w/2,19,text=self.text,fill='white' if self.primary else BLUE if self.active else INK,
                         font=('Segoe UI',10,'bold' if self.primary or self.active else 'normal'))


class Panel(tk.Canvas):
    def __init__(self, parent, color=SURFACE, padding=18, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), highlightthickness=0, **kwargs)
        self.color, self.padding = color, padding
        self.inner = tk.Frame(self, bg=color)
        self.window = self.create_window(padding, padding, anchor='nw', window=self.inner)
        self.bind('<Configure>', self.resize)

    def resize(self, event):
        self.delete('glass')
        rounded(self, 2,4,event.width-2,event.height-1,22,fill='#d5deec',outline='',tags='glass')
        rounded(self, 1,1,event.width-3,event.height-4,22,fill=self.color,outline='#ffffff',width=1,tags='glass')
        self.tag_lower('glass')
        self.itemconfigure(self.window, width=max(1,event.width-self.padding*2),
                           height=max(1,event.height-self.padding*2))


def label(parent, text='', size=10, bold=False, color=INK, **kwargs):
    return tk.Label(parent, text=text, bg=background(parent), fg=color,
                    font=('Segoe UI',size,'bold' if bold else 'normal'), **kwargs)


class Wallpaper(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg='#e9edf8', highlightthickness=0)
        # Soft ambient light, generated locally rather than shipped bitmap assets.
        img = tk.PhotoImage(width=180, height=120)
        rows = []
        for y in range(120):
            row = []
            for x in range(180):
                a = math.exp(-((x-15)**2+(y-20)**2)/2500)
                b = math.exp(-((x-170)**2+(y-105)**2)/2800)
                c = math.exp(-((x-135)**2+(y-5)**2)/2000)
                rgb = (int(239-20*a-5*b+3*c),int(242-14*a-7*b-15*c),int(249-2*a-3*b))
                row.append('#%02x%02x%02x' % rgb)
            rows.append('{'+' '.join(row)+'}')
        img.put(' '.join(rows))
        self.image = img.zoom(10)
        self.create_image(0,0,anchor='nw',image=self.image)
