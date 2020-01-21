# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 23:32:02 2019

@author: DarioViva
"""

from song import Song
from tqdm import tqdm
from time import sleep
from json import loads
from requests import get
from html import unescape
from bs4 import BeautifulSoup
from os import chdir, listdir, remove
from json.decoder import JSONDecodeError
from os.path import isfile, dirname, abspath
from interactions import open_file, album_menu

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

album_ids = list()
added_songs = dict()

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
        added_songs.update(album_menu(song.tracks, mapping[song.album_id],
                                      song.album, song.track0, song.cover))

        album_ids.append(song.album_id) # Remember albums

def get_mapping(songs):
    album_list = [(e.album_id, e.track0)
                  for e in songs if e.album_id]
    album_mapping = dict()
    for i, j in album_list:
        if i not in album_mapping: album_mapping[i] = [j]
        else: album_mapping[i].append(j)
    return album_mapping

# select the file with the songs-list
input_list = open_file()

# change working directory
open_file(True)

songs_list = list()

print('Mapping from Queries to Genius-Paths...\n'
      '---------------------------------------')

# find the songs on Genius
song_paths = [search_api(e) for e in input_list]
song_paths = [e for e in song_paths if e]

print('\nGet information about the songs...\n'
        '----------------------------------')

song_infos = [get_info(e) for e in tqdm(song_paths)]
song_infos = [e for e in song_infos if e]

print('\n\nCollecting and rearranging data...\n'
          '----------------------------------')

songs_list = [Song(info) for info in tqdm(song_infos)]

album_mapping = get_mapping(songs_list)

for song in songs_list:
    ask_album(song, album_mapping)

if added_songs:
    print('\n\nGet information about additional songs...\n'
              '-----------------------------------------')

    added_infos = [(e, get_info(e)) for e in tqdm(added_songs)]
    added_infos = [e for e in added_infos if e[1]]

    print('\n\nCollecting and rearranging data...\n'
              '----------------------------------')

    songs_list += [Song(info, xt = added_songs[song_path])
                   for song_path, info in tqdm(added_infos)]

print('\n\nDownload and save songs on computer...\n'
          '--------------------------------------', end = '')

for song in songs_list:
    song.to_disk()

for item in listdir():
    if item.endswith(".webm"):
        remove(item)

print('\n\nAll songs downloaded!')
