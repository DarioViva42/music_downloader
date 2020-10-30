# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 23:32:02 2019

@author: DarioViva
"""

from os.path import dirname, abspath
from os import chdir, listdir, remove
from logging import getLogger, Formatter, FileHandler, basicConfig

# Change directoy to the script's location
# cd C:\Users\dario\Documents\Python Scripts\music_downloader
chdir(dirname(abspath(__file__)))

basicConfig()
logger = getLogger()
logger.setLevel(15)

# disable logging to stdout
stdout = logger.handlers[0]
stdout.close()
logger.removeHandler(stdout)

# set up logging to file
fh = FileHandler('information.log', mode = 'w', encoding = 'utf-8')
fh.setLevel(15)
formatter = Formatter('[%(asctime)s] %(levelname)8s - %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info("Start of logging")

from song import Song
from tqdm import tqdm
from time import sleep
from json import loads
from requests import get
from bs4 import BeautifulSoup
from interactions import open_file, set_directory, album_menu

base_url = 'https://genius.com'
search_url = f"{base_url}/api/search/song"

album_ids = list()
added_songs = dict()

def search_api(user_in):
    if user_in[0] == '/': return user_in
    while True:
        params  = {'q': user_in}
        while True:
            try: r = get(search_url, params=params)
            except ConnectionError:
                logger.error(f'"{user_in}" wasn\'t handled correctly')
                sleep(1)
                continue
            if r.status_code == 200: break
            logger.warning(f'API returned status {r.status_code}')
            sleep(1)

        search_results = r.json()['response']['sections'][0]['hits']
        if len(search_results):
            top_result = search_results[0]['result']['path']
            logger.info(f'"{user_in}" mapped to {top_result}')
            return top_result
        try:
            logger.warning(f'No song found with "{user_in}"')
            user_in = user_in[user_in.index(' '):].lstrip()
            logger.info(f'Try searching for "{user_in}"')
        except ValueError:
            logger.critical('Absolutely nothing found for this query')
            return None

def make_Song(song_path, xt = False):
    URL = base_url + song_path
    while True:
        try: page = get(URL)
        except ConnectionError:
            logger.error(f"Couldn't connect with {song_path}")
            sleep(1)
            continue
        if page.status_code == 404:
            logger.critical(f'{song_path} not found on genius')
            return None
        if page.status_code == 200:
            html = BeautifulSoup(page.text, "html.parser")
            song_info = html.find("meta", {"itemprop":"page_data"})
            if song_info is not None: break
            logger.warning(f"The page_data was not found with {song_path}")
            sleep(1)
            continue
        logger.warning(f'{song_path} returned status {page.status_code}')
        sleep(1)

    json_string = song_info.attrs['content']
    info = loads(json_string)
    logger.info(f'Collected info about {song_path}')
    if xt: return Song(info, added_songs[song_path])
    else: return Song(info)

def ask_album(song, mapping):
    if song.album_id and (song.album_id not in album_ids):
        added_songs.update(album_menu(song.tracks, mapping[song.album_id],
                                      song.album, song.cover))

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
set_directory()

print('Mapping from Queries to Genius-Paths...\n'
      '---------------------------------------')

# find the songs on Genius
song_paths = [search_api(e) for e in tqdm(input_list)]
song_paths = [e for e in song_paths if e]

print('\nCollect information about the songs.\n'
        '------------------------------------')

songs_list = [make_Song(e) for e in tqdm(song_paths)]
songs_list = [e for e in songs_list if e]

album_mapping = get_mapping(songs_list)

for song in songs_list:
    ask_album(song, album_mapping)

if added_songs:
    print('\n\nCollect information about additional songs.\n'
              '-------------------------------------------')

    songs_list += [make_Song(e, True) for e in tqdm(added_songs)]

print('\n\nDownload and save songs on computer...\n'
          '--------------------------------------', end = '')

for song in songs_list:
    song.to_disk()

for item in listdir():
    if item.endswith(".webm"):
        remove(item)

print('\n\nAll songs downloaded!')
logger.info('End of logging')
fh.close()
logger.removeHandler(fh)
