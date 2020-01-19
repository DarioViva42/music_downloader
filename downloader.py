# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 23:32:02 2019

@author: DarioViva
"""

from io import BytesIO
from time import sleep
from json import loads
from requests import get
from html import unescape
from bs4 import BeautifulSoup
from pydub import AudioSegment
from PIL import Image, ImageTk
from os.path import isfile, dirname, abspath
from os import environ, chdir, listdir, remove
from youtube_dl import DownloadError, YoutubeDL
from mutagen.id3 import (ID3, APIC, USLT, TIT2, TPE1, 
                         TRCK, TALB, TCON, TPE2, TDRC)
from tkinter import (Tk, Checkbutton, IntVar, LEFT, RIGHT, 
                     filedialog, Label, Frame, DISABLED, NORMAL)
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

options = {
  'format': 'bestaudio/best',
  'extractaudio' : True,  # only keep the audio
  'noplaylist' : True     # only download single song, not playlist
}

album_ids = list()
added_songs = list()

def rep_chars(s):
    if type(s) == list:
        return [e.replace('’', '\'') for e in s]
    return s.replace('’', '\'')

def addID3(song_id, cover, lyrics, genre, artists, title, 
           album_year, album_name, album_artist, album_track):
    audio = ID3(f'{song_id}.mp3')
    
    audio['APIC'] = APIC(encoding = 3, mime = 'image/jpeg', 
                         type = 3, data = cover)
    audio['USLT'] = USLT(encoding = 3, text = lyrics)
    audio['TIT2'] = TIT2(encoding = 3, text = title)
    audio['TPE1'] = TPE1(encoding = 3, text = artists)
    audio['TRCK'] = TRCK(encoding = 3, text = album_track)
    audio['TALB'] = TALB(encoding = 3, text = album_name)
    audio['TCON'] = TCON(encoding = 3, text = genre)
    audio['TPE2'] = TPE2(encoding = 3, text = album_artist)
    audio['TDRC'] = TDRC(encoding = 3, text = album_year)
    
    audio.save(v2_version=3, v23_sep='; ')
    
def search_api(user_in):
    if user_in[0] == '/': return user_in
    print(user_in, end = NEW_LINE)
    while True:
        params  = {'q': user_in}
        while True:
            try: 
                r = get(search_url, params=params, headers=headers)
            except ConnectionError:
                sleep(1)
                print('Can not connect to Genius-API. Trying again...')
                continue
            if r.status_code != 200:
                sleep(1)
                print('Can not connect to Genius-API. Trying again...')
            else: break
        
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
    print(song_path)
    URL = base_url + song_path
    while True:
        try: page = get(URL)
        except ConnectionError: 
            sleep(1)
            print('Connection problems. Trying again...')
            continue
        if page.status_code == 200:
            html = BeautifulSoup(page.text, "html.parser")
            song_info = html.find("meta", {"itemprop":"page_data"})
            try: 
                json_string = song_info.attrs['content']
                json_string = json_string.replace('&quot;', '\\"')
                return loads(unescape(json_string))
            except JSONDecodeError:
                print('    Genius has a problem with this song!')
                return None
        sleep(1)
        print('Connection problems. Trying again...')

def get_picture(picture_url):  #Image.open(BytesIO(picture))
    while True:
        try:
            picture = get(picture_url)
            picture = Image.open(BytesIO(picture.content))
            picture = picture.resize((500, 500), Image.LANCZOS)
            imgByteArr = BytesIO()
            picture.save(imgByteArr, format='JPEG')
            return imgByteArr.getvalue()
        except OSError: pass

# collect urls about other songs in album
def add_songs(tracks, mapping, album_name, album_artist, album_cover):
    root = Tk()
    root.title('Album-Menu')
    root.maxsize(250, 1080)
    
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
        frame = Frame(root)
        c = Checkbutton(frame, text = f"{n:02}.", 
                        variable=box_values[i][0], 
                        state = box_values[i][1])
        c.pack(side = LEFT, anchor = 'n')
        song_title = Label(frame, text=t, wraplength = 200, justify=LEFT)
        song_title.pack(side = RIGHT)
        frame.pack(anchor = 'w')

    root.resizable(False, False)
    root.mainloop()
    
    for e in mapping_index:
        box_values[e][0].set(0)
        
    song_paths = [p for n, p, t, i in tracks 
                  if box_values[i][0].get()]
    global added_songs
    added_songs += song_paths

def get_youtube(song_id, youtube_url):
    options['outtmpl'] = f'{song_id}.webm'
    with YoutubeDL(options) as ydl:
        ydl.download([youtube_url])
    while not isfile(options['outtmpl']):
        sleep(1)

def search_youtube(song_id, title, artists):
    while True:
        try:
            options['outtmpl'] = f'{song_id}.webm'
            with YoutubeDL(options) as ydl:
                ydl.download([f"ytsearch:{title} {' '.join(artists)}"])
            while not isfile(options['outtmpl']):
                sleep(1)
            break
        except DownloadError: pass

def cut_video(song_id, youtube_start):
    sound = AudioSegment.from_file(f'{song_id}.webm')
    songPart = sound[youtube_start*1000:]
    songPart.export(f'{song_id}.mp3', format="mp3")

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
    
    if file_path == '':
        return open_file(directory)
    else:
        if directory: chdir(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            return content.splitlines()

def get_track(tracks, song_path):
    tracks = [(e['number'], e['song']['path'], e['song']['title'])
              for e in tracks if e['number']]
    tracks = [(*e, i) for i, e in enumerate(tracks)]
    album_track = [(e[0], e[3]) for e in tracks 
                   if song_path == e[1]]
    if album_track and album_track[0][0]: album_track = album_track[0]
    else: album_track = None
        
    return tracks, album_track

def create_song(song_info, mapping = None, suppress = False):
    song_path = song_info['song']['path']
    print('\n' + song_path)
    title = rep_chars(song_info['song']['title'])
    song_id = song_info['song']['id']
    
    artist = rep_chars(song_info['song']['primary_artist']['name'])
    artists = rep_chars(song_info['dmp_data_layer']['page']['artists'])
    if artist in artists:
        artists.remove(artist)
        artists = [artist, *artists]
    
    song_cover = song_info['song']['song_art_image_url']
    song_year = song_info['song']['release_date_components']
    if song_year: song_year = song_year['year']
    else: song_year = 9999
    genre = rep_chars(song_info['song']['primary_tag']['name'])
    
    # find out if song appears in an album
    album = song_info['song']['album']
    if album:
        album_name = rep_chars(album['name'])
        album_artist = rep_chars(album['artist']['name'])
        album_year = album['release_date_components']['year']
        album_cover = get_picture(album['cover_art_url'])
        tracks = song_info['primary_album_tracks']
        tracks, album_track = get_track(tracks, song_path)
        album_id = album['id']
        if album_track:
            if not (suppress or album_id in album_ids):
                add_songs(tracks, mapping[album_id], album_name, 
                          album_artist, album_cover)
                # Remember albums,
                # so that the user doesn't need to choose multiple times
                album_ids.append(album_id)
            album_track = f'{album_track[0]}/{len(tracks)}'
        else:
            album_name = title + ' - Single'
            album_artist = artist
            album_year = song_year
            album_cover = get_picture(song_cover)
            album_track = '1/1'
    else:
        album_name = title + ' - Single'
        album_artist = artist
        album_year = song_year
        album_cover = get_picture(song_cover)
        album_track = '1/1'
    
    lyrics = song_info['lyrics_data']['body']['html']
    lyrics = BeautifulSoup(lyrics, "html.parser").get_text().strip()
    
    if song_info['song']['youtube_url']:
        youtube_url = song_info['song']['youtube_url']
        youtube_start = song_info['song']['youtube_start']
        youtube_start = int(youtube_start) if youtube_start else 0
        try:
            get_youtube(song_id, youtube_url)
        except DownloadError:
            youtube_start = 0
            search_youtube(song_id, title, artists)
    else:
        youtube_start = 0
        search_youtube(song_id, title, artists)
    
    cut_video(song_id, youtube_start)
    addID3(song_id, album_cover, lyrics, genre, artists, title, 
           str(album_year), album_name, album_artist, album_track)


input_list = open_file()

# change working directory
open_file(True)

# find the songs on Genius
song_paths = [search_api(e) for e in input_list]
song_paths = [e for e in song_paths if e]

print('\nGet information about the songs...')
song_infos = [get_info(e) for e in song_paths]
song_infos = [e for e in song_infos if e]

album_list = [(e['song']['album']['id'], 
               get_track(e['primary_album_tracks'], e['song']['path'])[1]) 
              for e in song_infos if 'primary_album_tracks' in e]
album_list = [e for e in album_list if e[1]]

album_mapping = dict()
for i, j in album_list: 
    if i not in album_mapping: album_mapping[i] = [j]
    else: album_mapping[i].append(j)

print()
for song_info in song_infos:
    create_song(song_info, mapping = album_mapping)

if added_songs:
    print('\n\nGet information about additional songs...')
    added_infos = [get_info(e) for e in added_songs]
    added_infos = [e for e in added_infos if e]
    print()
    for song_info in added_infos:
        create_song(song_info, suppress = True)

for item in listdir():
    if item.endswith(".webm"):
        remove(item)
