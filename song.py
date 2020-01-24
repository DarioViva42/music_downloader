# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 20:19:03 2020

@author: DarioViva
"""

from PIL import Image
from time import sleep
from io import BytesIO
from requests import get
from os.path import isfile
from bs4 import BeautifulSoup
from pydub import AudioSegment
from youtube_dl import DownloadError, YoutubeDL
from mutagen.id3 import (ID3, APIC, USLT, TIT2, TPE1,
                         TRCK, TALB, TCON, TPE2, TDRC)

options = {
  'format': 'bestaudio/best',
  'extractaudio' : True,  # only keep the audio
  'noplaylist' : True     # only download single song, not playlist
}

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

def rep_chars(s):
    if type(s) == list:
        return [e.replace('’', '\'') for e in s]
    return s.replace('’', '\'')

def get_artist(song_info):
    artist = rep_chars(song_info['song']['primary_artist']['name'])
    artists = rep_chars(song_info['dmp_data_layer']['page']['artists'])
    if artist in artists:
        artists.remove(artist)
        artists = [artist, *artists]
    return artist, artists

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

class Song:

    def __init__(self, song_info, xt = None):

        song_path = song_info['song']['path']
        title = rep_chars(song_info['song']['title'])
        song_id = song_info['song']['id']
        artist, artists = get_artist(song_info)
        song_cover = song_info['song']['song_art_image_url']
        song_year = song_info['song']['release_date_components']
        song_year = (str(song_year['year'])
                     if song_year else '9999')
        genre = rep_chars(song_info['song']['primary_tag']['name'])

        # find out if song appears in an album
        album = xt[0] if xt else song_info['song']['album']
        if album:
            album_name = rep_chars(album['name'])
            album_artist = rep_chars(album['artist']['name'])
            album_year = album['release_date_components']
            album_year = (str(album_year['year'])
                          if album_year else '9999')
            cover = xt[3] if xt else get_picture(album['cover_art_url'])
            tracks, track0 = (xt[1], xt[2]) if xt else get_track(song_info)
            album_id = album['id']
            if track0:
                album_length = max([e[0] for e in tracks])
                track = f'{track0[0]}/{album_length}'
            else: album = None

        if not album:
            album_id = None
            tracks = None
            track0 = None
            album_name = title + ' - Single'
            album_artist = artist
            album_year = song_year
            cover = get_picture(song_cover)
            track = '1/1'

        lyrics = song_info['lyrics_data']['body']['html']
        lyrics = BeautifulSoup(lyrics, "html.parser").get_text().strip()

        if song_info['song']['youtube_url']:
            youtube_url = song_info['song']['youtube_url']
            youtube_start = song_info['song']['youtube_start']
            youtube_start = int(youtube_start) if youtube_start else 0
        else:
            youtube_url = None
            youtube_start = 0

        self.song_id = song_id
        self.song_path = song_path
        self.title = title
        self.artists = artists
        self.genre = genre
        self.album = album
        self.album_id = album_id
        self.album_name = album_name
        self.album_artist = album_artist
        self.album_year = album_year
        self.cover = cover
        self.tracks = tracks
        self.track0 = track0
        self.track = track
        self.lyrics = lyrics
        self.youtube_url = youtube_url
        self.youtube_start = youtube_start

    def to_disk(self):
        print('\n' + self.song_path)
        if self.youtube_url:
            try: get_youtube(self.song_id, self.youtube_url)
            except:
                self.youtube_start = 0
                search_youtube(self.song_id, self.title, self.artists)
        else:
            self.youtube_start = 0
            search_youtube(self.song_id, self.title, self.artists)

        cut_video(self.song_id, self.youtube_start)
        addID3(self.song_id, self.cover, self.lyrics, self.genre,
               self.artists, self.title, self.album_year,
               self.album_name, self.album_artist, self.track)
