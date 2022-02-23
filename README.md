## YouTube Download-Upload (YT-du)

### Easy to use qBittorent-inspired application for downloading entire playlists or single videos from YouTube

### Demo: <a href="https://www.youtube.com/watch?v=Xr7d6p3E5n4">YouTube demo</a>

<br/>

---

## What can you do with it?

<br/>

- download entire playlists or single videos from YouTube by simply passing its url
- download videos in any quality by choosing it on the YouTube platform itself, no need for any application-specific configuration
- manage the lifecycle of the download process, pause downloading of the entire playlists or selected videos, then resume it once convenient
- have centralized database containing history and file system locations of your downloads
- monitor speed and possible errors of the download process
- resume the download from the point where your network (or power, with some luck) went down, without wasting time downloading it from the beginning again
- upload downloaded videos back to YouTube, but this time as private videos on your own account, taking advantage of YouTube's infinite-ish video storage capabilities

<br/>

---

<br/>

## Problems

- as of this writing only Unix platforms (Linux, probably macOS) are supported
- installation might be somewhat complex (see Installation section below)
- requires Chrome browser running on owner's PC
- it is still "work in progress", if you want to break it, you will likely succeed

<br/>

---

<br/>

## How does it work?

### High level overview

When we click on a YouTube video, 2 streams of data start flowing to the browser. The first stream contains video, the second contains audio. The YouTube player manages those streams to play the media.

Streams are sent via HTTP methods. Those methods have rich headers containing metadata, which makes it possible to capture and play them without a sophisticated YouTube player.

YT-du uses the Chrome browser extension, which uses the Chrome API to intercept those streams. Specifically, we need only endpoints to the first chunk of those streams; every succeeding chunk can be generated from the previous one, which minimizes the contribution of the browser.

Sidenote: As far as I managed to find out, <a href="https://github.com/ytdl-org/youtube-dl">youtube-dl</a> extracts those streams by emulating browser (parsing and running JS code from desktop). Here, a different approach has been taken, which makes it easier to use at the cost of limited extendibility.

<br/>

Workflow of the download process:

1. The user enters the url of the playlist (or video, which is similar; let's focus on playlists here) to the Yt-du client.
2. YT-du client commands the manager of the browser extension to fetch the url's of the above-mentioned streams for every video in the playlist.
3. The manager preprocesses these commands and sends them to the browser extension using websockets.
4. The browser extension opens a link to the playlist, from which it extracts links to videos in that playlist; for each video link, one Chrome tab is opened, from which the extension intercepts required media stream urls.
5. Browser Extension sends intercepted urls back to the YT-du client. At this point, we have everything that's necessary for the download.
6. YT-du client contacts the process manager to schedule download-workers to download every video in the playlist. The number of parallel downloads can be configured.
7. YT-du download-worker starts the download process, generating urls to the next chunks of the media streams.
8. YT-du download-worker sends information about the download process to the YT-du client. The client uses that data to update the GUI. The client can stop the download-worker at any time, which leaves the downloaded data consistent.
9. Once audio and video streams are downloaded, YT-du download-worker merges them using an ffmpeg subprocess, creating a video that we can watch on the YouTube platform.
10. The YT-du download worker saves that video in a file system location specified by the user.

<br/>

---

<br/>

### Low level overview (TODO)

- YT-du uses a bunch of processes, main one is mostly single threaded (excluding threads used for communication with other processes), it's job is to manage GUI and control downloads
- each video is downloaded in separate process, pool size can be configured, each stream is downloaded in it's own thread, streams are joined in ffmpeg subprocess
- browser extension is managed from separate process
- YT-du download worker (soruce code: backed/ipc/yt-dl.py) was designed to be independant of the rest of the application (as long as you can provide it with urls to first audio and video streams), you can easily adapt it to your needes by implementing abstract classes specified in that file (see backend/ipc/piped_status_observer.py for example) 

...

<br/>

---

<br/>


## The "u" upload part of the YT-du

It is still work in progress (I planned to use YouTube API here but quota is ridiculous). For now you can upload videos by:

1. open <a href="https://studio.youtube.com/">youtube studio</a>
2. click UPLOAD VIDEOS
3. drag&drop files
4. go to "Content" tab
5. select videos you wish to make priviate by clicking squares to the left of each video
6. Browser extension has created "Fast Upload" button to the bottom right of your screen, click it and all videos will be configured as "private" and "made for kids"

<br/>

---

<br/>

## Installation

### 1. Download requirements:
- postgresql, follow instructions from <a href="https://www.postgresql.org/download/">here</a>, then <a href="https://ubiq.co/database-blog/create-user-postgresql/">create user</a> with full priviliges, finally <a href="https://www.postgresql.org/docs/8.4/tutorial-createdb.html">create database</a>, or use <a href="https://hub.docker.com/_/postgres"> docker</a>, pull version 12.x
- ffmpeg 4.x, follow instructions from <a href="https://ffmpeg.org/download.html">here</a>
- make sure that python3.8 and pip are installed, then in main repo directory run:
```
    python -m venv env
    source ./env/bin/activate
    pip install -r requirements.txt
```
---

### 2. Install the browser extension:

- go to chrome extensions, make sure that developer mode is ON, click "Load unpacked" and select "ext" directory from this repo

### 3. Create .env file in backend/assets directory as below:
```
# DATABASE CONFIG
DB_USERNAME="<username you entered in postgres installation>"
DB_PASSWORD="<password you entered in postgres installation>"
DB_ADDRESS="localhost:5432" # this should be default, if you use remote database or different port modify it appropriately
DB_NAME="<name of the database you entered in postgres installation" 

# EXTENSION CONFIG
WS_HOST="127.0.0.1"
WS_PORT=5555 # or whatever is specified in ext/background.js (sorry for that :))
BROWSER="/usr/bin/google-chrome" # YT-du might want to run your browser if it detects that its turned off, you can specify path to the chrome executable here

# OTHERS
FILE_OPENER="xdg-open" # default file explorer for Linux 
TMP_FILES_PATH="/home/<your host name>/ytdl/.tmp" # select anything you want
DEFAULT_OUT_PATH='/home/<your host name>/ytdl' # select anything you want
MAX_DOWNLOAD_BATCH=10 # how many videos can be downloaded in parallel
```
 
### 4. Run the Application
- make sure that browser extension in turned on
- make sure that virtual environment is activated
```
    source ./env/bin/activate
```
- run application
```
    python backend/app.py
```