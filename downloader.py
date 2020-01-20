# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 23:32:02 2019

@author: DarioViva
"""

from song import Song
from tqdm import tqdm
from io import BytesIO
from time import sleep
from json import loads
from requests import get
from html import unescape
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from os.path import isfile, dirname, abspath
from os import environ, chdir, listdir, remove
from tkinter import (Tk, Checkbutton, IntVar, Label, Canvas,
                     filedialog, Frame, DISABLED, NORMAL, Scrollbar)
from json.decoder import JSONDecodeError

try:
    if get_ipython().__class__.__module__ == 'ipykernel.zmqshell':
        NEW_LINE = ''
    else:
        NEW_LINE = '\n'
except NameError:
    NEW_LINE = '\n'

base_url = 'https://genius.com'
search_url = "https://api.genius.com/search"

# Change directoy to the script's location
chdir(dirname(abspath(__file__)))

if isfile('token'):
    with open('token', 'rb') as file:
        token = file.read().decode('ascii')
else:
    token = input('Please, input your genius access-token.\n')
    with open('token', 'wb') as file:
        print()
        file.write(token.encode('ascii'))

bearer_token = f'Bearer {token}'
headers = {'Authorization': bearer_token}

songs_list = list()
album_ids = list()
added_songs = dict()

def get_track(song_info):
    tracks = song_info['primary_album_tracks']
    song_path = song_info['song']['path']

    tracks = [(e['number'], e['song']['path'], e['song']['title'])
              for e in tracks if e['number']]
    tracks = [(*e, i) for i, e in enumerate(tracks)]
    album_track = [(e[0], e[3]) for e in tracks
                   if song_path == e[1]]
    if album_track and album_track[0][0]: album_track = album_track[0]
    else: album_track = None

    return tracks, album_track

def search_api(user_in):
    if user_in[0] == '/': return user_in
    print(user_in, end = NEW_LINE)
    while True:
        params  = {'q': user_in}
        while True:
            try: r = get(search_url, params=params, headers=headers)
            except ConnectionError:
                sleep(1)
                continue
            if r.status_code == 200:
                break
            else: sleep(1)

        search_results = r.json()['response']['hits']
        search_results = [e['result']['path'] for e in search_results]
        search_results = [e for e in search_results
                          if e[:15] != '/Screen-genius-']
        if len(search_results):
            top_result = search_results[0]
            correction = input(top_result + '\n')
            if len(correction):
                print()
                return correction
            return top_result
        try:
            user_in = user_in[user_in.index(' '):].lstrip()
        except ValueError:
            correction = input('No song found with this query...\n')
            if len(correction):
                print()
                return correction
            return None

def get_info(song_path):
    URL = base_url + song_path
    while True:
        try: page = get(URL)
        except ConnectionError:
            sleep(1)
            continue
        if page.status_code == 200:
            html = BeautifulSoup(page.text, "html.parser")
            song_info = html.find("meta", {"itemprop":"page_data"})
            try:
                json_string = song_info.attrs['content']
                json_string = json_string.replace('&quot;', '\\"')
                return loads(unescape(json_string))
            except JSONDecodeError:
                return None
        if page.status_code == 404:
            return None
        sleep(1)

def ask_album(song, mapping):
    if song.album_id and (song.album_id not in album_ids):
        add_songs(song.tracks, mapping[song.album_id],
                  song.album, song.track0, song.cover)

        album_ids.append(song.album_id) # Remember albums

# collect urls about other songs in album
def add_songs(tracks, mapping, album, track, album_cover):
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

    song_paths = [p for n, p, t, i in tracks
                  if box_values[i][0].get()]
    for song in song_paths:
        added_songs[song] = (album, tracks, track)

#opens a file-dialog
def open_file(directory = False):
    root = Tk()
    root.withdraw()

    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.attributes('-alpha', 0)

    root.deiconify()
    root.lift()
    root.focus_force()

    if directory:
        file_path = filedialog.askdirectory(
            parent=root,
            initialdir = environ['USERPROFILE'],
            title = "Where do you want to save the songs?")
    else:
        file_path = filedialog.askopenfilename(
            parent=root,
            initialdir = environ['USERPROFILE'],
            filetypes = (("Text File", "*.txt"),),
            title = "Choose the file in wich your songs are listed...")
    root.destroy()

    if file_path == '': return open_file(directory)
    else:
        if directory: chdir(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            lines = [e for e in content.splitlines()
                     if not e.isspace()]
            if lines: return lines
            else: return open_file()

def get_mapping(song_infos):
    album_list = [(e['song']['album']['id'], get_track(e)[1])
              for e in song_infos if 'primary_album_tracks' in e]
    album_list = [e for e in album_list if e[1]]
    album_mapping = dict()
    for i, j in album_list:
        if i not in album_mapping: album_mapping[i] = [j]
        else: album_mapping[i].append(j)
    return album_mapping

# select the file with the songs-list
input_list = open_file()

# change working directory
open_file(True)

print('Mapping from Queries to Genius-Paths...\n'
      '---------------------------------------')

# find the songs on Genius
song_paths = [search_api(e) for e in input_list]
song_paths = [e for e in song_paths if e]

print('\nGet information about the songs...\n'
        '----------------------------------')

song_infos = [get_info(e) for e in tqdm(song_paths)]
song_infos = [e for e in song_infos if e]

album_mapping = get_mapping(song_infos)

print('\n\nCollecting and rearranging data...\n'
          '----------------------------------')

for info in tqdm(song_infos):
    songs_list.append(Song(info))

for song in songs_list:
    ask_album(song, album_mapping)

if added_songs:
    print('\n\nGet information about additional songs...\n'
              '-----------------------------------------')

    added_infos = [(e, get_info(e)) for e in tqdm(added_songs)]
    added_infos = [e for e in added_infos if e[1]]

    print('\n\nCollecting and rearranging data...\n'
              '----------------------------------')

    for song_path, info in tqdm(added_infos):
        songs_list.append(Song(info, xt = added_songs[song_path]))

print('\n\nDownload and save songs on computer...\n'
          '--------------------------------------', end = '')

for song in songs_list:
    song.to_disk()

for item in listdir():
    if item.endswith(".webm"):
        remove(item)

print('All songs downloaded!')
