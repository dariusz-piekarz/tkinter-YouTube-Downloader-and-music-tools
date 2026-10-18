# YouTube Downloader and Music Tools

A desktop Tkinter app with three tools: download YouTube videos as MP3 or MP4 with progress and cancellation controls, trim MP3/MP4 files with an audio waveform preview, and edit MP3 metadata and cover art.

Use the Language/Język menu to switch between Polish and English at any time. Polish is the initial language, and the choice is saved per Windows user.

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
The repository includes VS Code settings that select `.venv\Scripts\python.exe` and a `YTDownloader` launch configuration. If plain `python` opens the Microsoft Store prompt or reports that Python was not found, use `uv run python` or `.\.venv\Scripts\python.exe` from the repository root.

The settings file is `YTDownloader_v2/config.yaml`. Set the download directory, default image, MP3 bitrate, or FFmpeg executable there. The default download directory is `~/Downloads`; if it does not exist, the app uses your home directory.

## Test

```powershell
uv run python -m unittest discover -s tests -v
```

The automated tests cover configuration loading, time validation, metadata editing, and the download options. A live YouTube download needs network access and may require updating `yt-dlp` when YouTube changes.

## Build a Windows executable

Run this in PowerShell from the repository root. FFmpeg and FFprobe must be installed on the build computer.

```powershell
$project = (Get-Location).Path
$ffmpeg = (Get-Command ffmpeg).Source
$ffprobe = (Get-Command ffprobe).Source
uv run --with pyinstaller python -m PyInstaller --noconfirm --onedir --windowed --name YTDownloader --distpath "$env:USERPROFILE\Desktop" --add-data "${project}\YTDownloader_v2\config.yaml:." --add-data "${project}\YTDownloader_v2\default.png:." --add-binary "${ffmpeg}:." --add-binary "${ffprobe}:." --collect-submodules yt_dlp.extractor YTDownloader_v2/main.py
```

The output is `Desktop\YTDownloader\YTDownloader.exe`. Distribute the entire `YTDownloader` folder. It includes FFmpeg and FFprobe, so the target computer does not need Python, uv, or a separate FFmpeg installation. Edit `config.yaml` before building if you need different defaults.

## Possible next steps
- Support batch downloads and playlist selection.

