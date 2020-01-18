# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 23:32:02 2019

@author: DarioViva
"""

from PIL import Image
from io import BytesIO
from time import sleep
from json import loads
from requests import get
from html import unescape
from bs4 import BeautifulSoup
from pydub import AudioSegment
from os.path import isfile, dirname, abspath
from os import environ, chdir, listdir, remove
from youtube_dl import DownloadError, YoutubeDL
from tkinter import Tk, Checkbutton, IntVar, DISABLED, NORMAL, filedialog
from mutagen.id3 import ID3, APIC, USLT, TIT2, TPE1, TRCK, TALB, TCON, TPE2, TDRC
from json.decoder import JSONDecodeError

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

added_songs = []

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
    print(user_in, end = '')
    while True:
        params  = {'q': user_in}
    
        r = get(search_url, params=params, headers=headers)
        if r.status_code != 200:
            raise ValueError('Can not connect to Genius-API.')
        
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
        page = get(URL)
        if page.status_code == 200:
            html = BeautifulSoup(page.text, "html.parser")
            song_info = html.find("meta", {"itemprop":"page_data"})
            try: 
                json_string = song_info.attrs['content']
                json_string = json_string.replace('&quot;', '\\&quot;')
                return loads(unescape(json_string))
            except JSONDecodeError:
                print('    Genius has a problem with this song!')
                return None
        print('Connection problems. Trying again...')

def get_picture(picture_url):  #Image.open(BytesIO(picture))
    picture = get(picture_url)
    picture = Image.open(BytesIO(picture.content))
    picture = picture.resize((500, 500), Image.LANCZOS)
    imgByteArr = BytesIO()
    picture.save(imgByteArr, format='JPEG')
    return imgByteArr.getvalue()

# collect urls about other songs in album
def add_songs(tracks, album_track, album_name, album_artist):
    root = Tk()
    root.title(f'{album_name} - {album_artist}')

    box_values = [(IntVar(value = 1), DISABLED) 
                  if n == album_track[0] 
                  else (IntVar(value = 0), NORMAL) 
                  for n, p, t, i in tracks]

    for n, p, t, i in tracks:
        l = Checkbutton(root, 
                        text=f"{n}. {t}", 
                        variable=box_values[i][0], 
                        state = box_values[i][1])
        l.pack(anchor = 'w')
    root.mainloop()
    
    box_values[album_track[1]][0].set(0)
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

def create_song(song_info, suppress = False):
    song_path = song_info['song']['path']
    print('\n' + song_path)
    title = rep_chars(song_info['song']['title'])
    song_id = song_info['song']['id']
    
    artist = rep_chars(song_info['song']['primary_artist']['name'])
    artists = rep_chars(song_info['dmp_data_layer']['page']['artists'])
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
        album_cover = album['cover_art_url']
        tracks = song_info['primary_album_tracks']
        tracks = [(e['number'], e['song']['path'], e['song']['title'])
                  for e in tracks if e['number']]
        tracks = [(*e, i) for i, e in enumerate(tracks)]
        album_track = [(e[0], e[3]) for e in tracks 
                       if song_path == e[1]]
        if len(album_track) and album_track[0][0]:
            album_track = album_track[0]
            if not suppress:
                add_songs(tracks, album_track, album_name, album_artist)
            album_track = f'{album_track[0]}/{len(tracks)}'
        else:
            album_name = title + ' - Single'
            album_artist = artist
            album_year = song_year
            album_cover = song_cover
            album_track = '1/1'
    else:
        album_name = title + ' - Single'
        album_artist = artist
        album_year = song_year
        album_cover = song_cover
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
    
    while True:
        try:
            cover = get_picture(album_cover)
            break
        except OSError: pass
    cut_video(song_id, youtube_start)
    addID3(song_id, cover, lyrics, genre, artists, title, 
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
print()
for song_info in song_infos:
    create_song(song_info)

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
