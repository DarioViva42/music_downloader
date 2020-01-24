# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 21:03:38 2020

@author: DarioViva
"""

from io import BytesIO
from os import environ, chdir
from PIL import Image, ImageTk
from tkinter import (Tk, Checkbutton, IntVar, Label, Canvas,
                     filedialog, Frame, DISABLED, NORMAL, Scrollbar)

#opens a file-dialog for input-file
def open_file():
    root = Tk()
    root.withdraw()

    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.attributes('-alpha', 0)

    root.deiconify()
    root.lift()
    root.focus_force()

    file_path = filedialog.askopenfilename(
        parent=root,
        initialdir = environ['USERPROFILE'],
        filetypes = (("Text File", "*.txt"),),
        title = "Choose the file in wich your songs are listed...")
    root.destroy()

    if file_path == '': return open_file()
    else:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        lines = [e for e in content.splitlines()
                 if not e.isspace()]
        if lines: return lines
        else: return open_file()

#opens a file-dialog for output-directory
def set_directory():
    root = Tk()
    root.withdraw()

    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.attributes('-alpha', 0)

    root.deiconify()
    root.lift()
    root.focus_force()

    file_path = filedialog.askdirectory(
        parent=root,
        initialdir = environ['USERPROFILE'],
        title = "Where do you want to save the songs?")
    root.destroy()

    if file_path == '': set_directory()
    else: chdir(file_path)


# collect urls about other songs in album
def album_menu(tracks, mapping, album, album_cover):
    root = Tk()
    root.title('Album-Menu')
    root.maxsize(250, 1000)

    if len(tracks) > 20:
        container = Frame(root)
        canvas = Canvas(container, width = 230, height = 500)
        scrollbar = Scrollbar(container, orient="vertical",
                              command=canvas.yview)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(int(e.delta/120)), "units"))

        scrollable_frame = Frame(canvas)
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="w")
        canvas.configure(yscrollcommand=scrollbar.set)

    render = Image.open(BytesIO(album_cover))
    render = ImageTk.PhotoImage(render.resize((250, 250)))
    img = Label(root, image=render)
    img.pack(anchor = 'n')

    mapping_display = [e[0] for e in mapping]
    mapping_index   = [e[1] for e in mapping]

    box_values = [(IntVar(value = 1), DISABLED)
                  if n in mapping_display
                  else (IntVar(value = 0), NORMAL)
                  for n, p, t, i in tracks]

    for n, p, t, i in tracks:
        frame = Frame(scrollable_frame if len(tracks) > 20 else root)
        c = Checkbutton(frame, text = f"{n:02}.",
                        variable=box_values[i][0],
                        state = box_values[i][1])
        c.pack(side = 'left', anchor = 'n')
        song_title = Label(frame, text=t, justify='left',
                           wraplength = 180 if len(tracks) > 20 else 200)
        song_title.pack(side = 'right')
        frame.pack(anchor = 'w')

    if len(tracks) > 20:
        container.pack(anchor = 'w')
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    root.resizable(False, False)
    root.mainloop()

    for e in mapping_index:
        box_values[e][0].set(0)

    song_infos = [(p, (n, i)) for n, p, t, i in tracks
                  if box_values[i][0].get()]

    added_songs = dict()
    for path, track0 in song_infos:
        added_songs[ path ] = (album, tracks, track0, album_cover)

    return added_songs