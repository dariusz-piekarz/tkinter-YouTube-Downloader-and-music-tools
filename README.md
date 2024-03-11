YTDownloader Application Overview
YTDownloader is a Tkinter-based application comprising three tabs, each serving distinct functions:

Downloader Tab
The 'Downloader' tab enables users to download both mp3 and mp4 files from YouTube.

Shrinker Tab
The 'Shrinker' tab facilitates the reduction of the length of mp3 files.

Fields Editor Tab
The 'Fields Editor' tab empowers users to edit metadata such as title, author, album name, album cover, track number, and genre.

WARNINGS:
Proper functionality of the project requires specifying the path to ffmpeg in the 'config.yaml' file. To correctly set up ffmpeg, please refer to the following instructions: How to Install FFmpeg on Windows.
Additionally, in the 'config.yaml' file, please specify a default path where downloaded files are stored.
In case of issues related to 'pytube', it is recommended to reinstall it from the Anaconda prompt using the command: pip install git+https://github.com/nficano/pytube.git.
