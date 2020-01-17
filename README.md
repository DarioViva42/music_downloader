# music_downloader
This is a simple script that downloads songs automatically and tags them with information found on genius.com.

## id3 Tags
The resulting songs will be mp3's with id3 2.3 tags for compatibility reasons with windows 10.
Although Windows 10 should support v2.4 since the anniversary edition, it still gave me too much headaches.

Fallowing Frames are filled with information:
- TIT2 Title
- TPE1 Artist
- TALB Album
- TPE2 Album-Artist
- TCON Genre
- TDRC Published-Year
- TRCK Track-Number
- USLT unsynchronized Lyrics
- APIC Cover-Front

## Genius bearer token
If you want to use this software head over to genius and create a developer account. https://genius.com/developers
Once logged in set up a new API Client and generate an Access Token.
Replace <access_token> on line 26 in the script with your generated Token.

## Requirements and Dependencies
To be able to run this script you need python 3.7+.
You can download python from their website. https://www.python.org/downloads/

Additionally be sure to install FFmpeg from their site. https://www.ffmpeg.org/
The installation-folder needs to be added to the PATH, so that python is able to use it.

Fallowing packages are requered to be installed:
- **Pillow** (https://pypi.org/project/Pillow/)
for handling cover images
- **beautifulsoup4** (https://pypi.org/project/beautifulsoup4/)
for easy-searching in html documents
- **youtube_dl** (https://pypi.org/project/youtube_dl/)
for downloading and searching youtube-videos
- **pydub** (https://pypi.org/project/pydub/)
for cutting and converting audio-files
- **mutagen** (https://pypi.org/project/mutagen/)
for taging mp3-files with id3 tags

You can install all these packages with pip or or conda using `pip install <package_name>` or `conda install <package_name>` respectively.

## Usage
Start the script with typing `python downloader.py` in the console.
A filedialog asks you to locate the text-file containing your songs. This is a new-line delimited "*.txt".
The lines in this file can either be search queries or relative genius-paths (ommit the genius-domain).
That means lines starting with a slash are interpreted as paths and all other lines function as search-queries.
After that it promts you to choose a destination folder. This is where all of you're songs get loaded into.
Watch out for any webm-files in this directory as they will get deleted at the very end of the script.

What fallows is a mapping from you're queries from the file to genius paths using their search api.
Lines that were given as paths don't need to be mapped and are hence skipped in this step.
Confirm the mapping by pressing <Return>. In case of wrong mappings, simply type in the correct path by searching on genius manually.

All queries mapped, the program will now try to collect information about the songs, this doesn't require any input from the user.

After that you have the ability to complete the albums the songs were published in.
Having checked all the songs you want from a given album, you can simply close the selection window and the script proceeds.
The script now downloads the song and tags it with id3 tags.

Last but not least, all songs are downloaded. Have fun listening!
