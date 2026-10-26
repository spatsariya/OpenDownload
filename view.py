"""Compact desktop layout: toolbar, download list, resizable inspector."""
import tkinter as tk
from tkinter import ttk
from ui import Button

WHITE = '#fcfdff'
TEXT = '#202b3c'
GRAY = '#738096'


def text(parent, value='', color=TEXT, size=9, **kwargs):
    return tk.Label(parent, text=value, bg=parent.cget('bg'), fg=color,
                    font=('Segoe UI', size), **kwargs)


def build(a):
    style = ttk.Style(a)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI',9), background=WHITE, foreground=TEXT)
    style.configure('TFrame', background=WHITE)
    style.configure('TLabel', background=WHITE)
    style.configure('TButton', padding=(9,5), borderwidth=0, background='#edf0f5')
    style.map('TButton', background=[('active','#e1e8f2')])
    style.configure('TEntry', padding=5, fieldbackground='#edf0f5', borderwidth=0)
    style.configure('TCombobox', padding=5, borderwidth=0, background='#edf0f5', arrowsize=12)
    style.configure('TCombobox',bordercolor='#edf0f5',lightcolor='#edf0f5',darkcolor='#edf0f5',relief='flat')
    style.map('TCombobox',fieldbackground=[('readonly','#edf0f5')], selectbackground=[('readonly','#edf0f5')],selectforeground=[('readonly',TEXT)])
    style.configure('Treeview', rowheight=32, borderwidth=0, background=WHITE,
                    fieldbackground=WHITE, foreground=TEXT, font=('Segoe UI',9))
    style.configure('Treeview.Heading', background=WHITE, foreground='#52617a',
                    relief='flat', padding=(9,10), font=('Segoe UI',9))
    style.map('Treeview', background=[('selected','#e8eef8')],foreground=[('selected',TEXT)])
    style.layout('Treeview',[('Treeview.treearea',{'sticky':'nswe'})])
    style.configure('Vertical.TScrollbar', background='#d9e0e9', troughcolor=WHITE, borderwidth=0, arrowsize=0, width=7)
    style.layout('Vertical.TScrollbar',[('Vertical.Scrollbar.trough',{'sticky':'ns','children':[
        ('Vertical.Scrollbar.thumb',{'expand':'1','sticky':'nswe'})]})])
    style.configure('TNotebook', borderwidth=0, tabmargins=(8,0,0,0),background='#edf0f5')
    style.configure('TNotebook.Tab', padding=(14,7), background='#edf0f5',foreground=GRAY)
    style.map('TNotebook.Tab',background=[('selected',WHITE)],foreground=[('selected','#3276d8')])
    style.configure('Horizontal.TProgressbar', background='#4385ee', troughcolor='#e8edf5',borderwidth=0,lightcolor='#4385ee',darkcolor='#4385ee')

    toolbar = tk.Frame(a,bg=WHITE,padx=12,pady=7)
    toolbar.pack(fill='x')
    ttk.Checkbutton(toolbar,command=lambda:select_all(a)).pack(side='left',padx=(0,8))
    for variable,values,width in [(a.sort,['Newest first','Oldest first','Name'],13),
            (a.filter,['All downloads','Downloading','Queued','Paused','Complete','Error'],16)]:
        ttk.Combobox(toolbar,textvariable=variable,values=values,state='readonly',width=width).pack(side='left',padx=(0,7))
    more = tk.Menubutton(toolbar,text='⋯',font=('Segoe UI',15),bg=WHITE,fg=TEXT,relief='flat',cursor='hand2')
    more.pack(side='right',padx=(10,0))
    menu = tk.Menu(more,tearoff=False)
    for title,callback in [('Start queue',a.start_queue),('Pause all',a.pause_all),('Open download folder',a.open_folder),('Remove selected',a.remove)]:
        menu.add_command(label=title,command=callback)
    more.configure(menu=menu)
    search = tk.Frame(toolbar,bg='#edf0f5',padx=9,pady=7)
    search.pack(side='right',padx=(10,0))
    text(search,'⌕',GRAY,11).pack(side='left',padx=(0,7))
    entry=tk.Entry(search,textvariable=a.search,width=26,bg='#edf0f5',fg=TEXT,relief='flat',font=('Segoe UI',9))
    entry.pack(side='left')
    a.bind('<Control-f>',lambda e:entry.focus_set())
    Button(toolbar,'+  Add download',a.add_dialog,140,primary=True).pack(side='right',padx=(10,0))
    for title,callback in [('Resume',a.resume),('Pause',a.pause)]:
        ttk.Button(toolbar,text=title,command=callback).pack(side='left',padx=3)
    tk.Frame(a,bg='#e7ebf1',height=1).pack(fill='x')

    status = tk.Frame(a,bg=WHITE,padx=12,pady=5)
    status.pack(side='bottom',fill='x')
    a.transfer=text(status,'↓  0 B/s', '#2c69b7')
    a.transfer.pack(side='left',padx=(0,20))
    a.footer=text(status,'',GRAY)
    a.footer.pack(side='left')
    ttk.Button(status,text='Set limit',command=a.set_limit).pack(side='right')
    ttk.Entry(status,textvariable=a.limit,width=6).pack(side='right',padx=6)
    text(status,'KB/s · 0 = unlimited',GRAY).pack(side='right')

    split = tk.PanedWindow(a,orient='vertical',bg='#e7ebf1',sashwidth=4,bd=0,showhandle=False)
    split.pack(fill='both',expand=True)
    list_area=tk.Frame(split,bg=WHITE)
    split.add(list_area,minsize=200,stretch='always')
    columns=('name','size','progress','status','speed','eta')
    a.table=ttk.Treeview(list_area,columns=columns,show='headings',selectmode='extended')
    for key,title,width in zip(columns,['Name','Size','Progress','Status','Download','Time left'],[650,100,110,130,110,90]):
        a.table.heading(key,text=title,anchor='w')
        a.table.column(key,width=width,minwidth=60,stretch=key=='name',anchor='w')
    scroll=ttk.Scrollbar(list_area,orient='vertical',command=a.table.yview)
    scroll.pack(side='right',fill='y')
    a.table.configure(yscrollcommand=scroll.set)
    a.table.pack(fill='both',expand=True)
    a.table.bind('<<TreeviewSelect>>',a.show_selection)
    a.table.bind('<Double-1>',a.details)
    a.table.bind('<Button-3>',lambda event:context(a,event))
    a.table.bind('<Delete>',lambda e:a.remove())
    a.table.tag_configure('Complete',foreground='#387bd7')
    a.table.tag_configure('Error',foreground='#c03c54')
    a.empty=tk.Frame(list_area,bg=WHITE)
    a.empty_title=text(a.empty,'No downloads yet',TEXT,12)
    a.empty_title.pack(pady=(0,7))
    a.empty_hint=text(a.empty,'Add a download to get started.',GRAY)
    a.empty_hint.pack()

    inspector=tk.Frame(split,bg=WHITE)
    split.add(inspector,minsize=140,height=225,stretch='never')
    tabs=tk.Frame(inspector,bg=WHITE)
    tabs.pack(fill='both',expand=True)
    tabbar=tk.Frame(tabs,bg='#edf0f5',height=31)
    tabbar.pack(fill='x')
    general=tk.Frame(tabs,bg=WHITE,padx=18,pady=12)
    progress=tk.Frame(tabs,bg=WHITE,padx=18,pady=16)
    tab_buttons=[]
    def switch(index):
        general.pack_forget()
        progress.pack_forget()
        (general,progress)[index].pack(fill='both',expand=True)
        for i,button in enumerate(tab_buttons):
            button.configure(bg=WHITE if i==index else '#edf0f5',fg='#3276d8' if i==index else GRAY)
    for i,title in enumerate(('GENERAL','PROGRESS')):
        button=tk.Button(tabbar,text=title,command=lambda i=i:switch(i),font=('Segoe UI',8),
                         relief='flat',bd=0,padx=15,pady=8,cursor='hand2',activebackground=WHITE)
        button.pack(side='left')
        tab_buttons.append(button)
    switch(0)
    a.detail_values={}
    for row,key in enumerate(['File','URL','Save to','Status']):
        text(general,key,GRAY,anchor='w',width=10).grid(row=row,column=0,sticky='w',pady=5)
        value=text(general,'—',anchor='w')
        value.grid(row=row,column=1,sticky='ew',padx=(8,25),pady=5)
        a.detail_values[key]=value
    for row,key in enumerate(['Size','Downloaded','Speed','Connections']):
        text(general,key,GRAY,anchor='w',width=12).grid(row=row,column=2,sticky='w',pady=5)
        value=text(general,'—',anchor='w',width=18)
        value.grid(row=row,column=3,sticky='w',padx=8,pady=5)
        a.detail_values[key]=value
    general.columnconfigure(1,weight=1)
    # Prevent long URLs from dictating the inspector's requested width.
    for key in ('File','URL','Save to','Status'):
        a.detail_values[key].configure(width=1)
    a.progress_caption=text(progress,'No download selected',TEXT,10)
    a.progress_caption.pack(anchor='w',pady=(0,14))
    a.progress_bar=ttk.Progressbar(progress,maximum=100)
    a.progress_bar.pack(fill='x')
    a.detail=text(inspector,'Select a download to view its details.',GRAY,anchor='w')
    a.detail.pack(fill='x',padx=18,pady=(4,8))
    a.bind('<Control-n>',lambda e:a.add_dialog())


def select_all(a):
    rows=a.table.get_children()
    a.table.selection_set(() if len(a.table.selection())==len(rows) else rows)


def context(a,event):
    row=a.table.identify_row(event.y)
    if row and row not in a.table.selection():
        a.table.selection_set(row)
    menu=tk.Menu(a,tearoff=False)
    for name,command in [('Resume',a.resume),('Pause',a.pause),('Open folder',a.open_folder),('Details',a.details),('Remove',a.remove)]:
        menu.add_command(label=name,command=command)
    menu.tk_popup(event.x_root,event.y_root)
