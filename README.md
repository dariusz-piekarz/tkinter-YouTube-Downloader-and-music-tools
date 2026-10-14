# YouTube Downloader and Music Tools

A desktop Tkinter app with three tools: download YouTube videos as MP3 or MP4, trim MP3/MP4 files, and edit MP3 metadata and cover art.

## Requirements

- Windows, Python 3.14.8, and [uv](https://docs.astral.sh/uv/)
- FFmpeg and FFprobe available in `PATH`, or an absolute FFmpeg path in `YTDownloader_v2/config.yaml`

## Run

From the repository root:

```powershell
uv sync
uv run python YTDownloader_v2/main.py
```

If `uv` is installed but not in `PATH`, use `$env:USERPROFILE\.local\bin\uv.exe` instead.

The settings file is `YTDownloader_v2/config.yaml`. Set the download directory, default image, MP3 bitrate, or FFmpeg executable there. The default download directory is `~/Downloads`; if it does not exist, the app uses your home directory.

## Test

```powershell
uv run python -m unittest discover -s tests -v
```

The automated tests cover configuration loading, time validation, metadata editing, and the download options. A live YouTube download needs network access and may require updating `yt-dlp` when YouTube changes.

## Possible next steps

- Add a progress bar and a cancel button for downloads and conversions.
- Support batch downloads and playlist selection.
- Add waveform preview for choosing trim points.
- Allow metadata editing for MP4/M4A as well as MP3.
