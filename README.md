# YouTube Downloader and Music Tools

A desktop Tkinter app with four tools: download YouTube videos and playlists as MP3 or MP4, trim MP3/MP4 with waveform and audio playback, edit MP3 metadata, and assemble a video with ClipMaker.

Use the Language/Język menu to switch between Polish and English at any time. Polish is the initial language, and the choice is saved per Windows user.

## Requirements

- Windows, Python 3.14.8, and [uv](https://docs.astral.sh/uv/)
- FFmpeg, FFprobe, and FFplay available in `PATH`, or FFmpeg set to an absolute path in `YTDownloader_v2/config.yaml` with FFprobe and FFplay beside it. FFplay is required for audio playback in the trimmer and ClipMaker video previews.
- `uv sync --locked` installs ClipMaker from its pinned Git commit and MoviePy from the lockfile. The first install needs network access.

## Run

From the repository root:

```powershell
uv sync --locked
uv run python YTDownloader_v2/main.py
```

If `uv` is installed but not in `PATH`, use `$env:USERPROFILE\.local\bin\uv.exe` instead.
The repository includes VS Code settings that select `.venv\Scripts\python.exe` and a `YTDownloader` launch configuration. If plain `python` opens the Microsoft Store prompt or reports that Python was not found, use `uv run python` or `.\.venv\Scripts\python.exe` from the repository root.

The settings file is `YTDownloader_v2/config.yaml`. Set the download directory, default image, MP3 bitrate, or FFmpeg executable there. The default download directory is `~/Downloads`; if it does not exist, the app uses your home directory.

In the downloader, use `+` to add a URL field and `−` to remove one. Each field accepts a video or playlist URL. Choose an output folder, then start the queue. Files with the same title receive numbered names. After every item succeeds, the URL fields reset to one empty field. Cancelling or encountering an error keeps the entered URLs.

In the trimmer, open an MP3 or MP4 file, set the start and end times or drag the markers on the waveform, and choose **Play selection** to hear exactly that range. **Stop** ends playback. The yellow line shows the approximate playback position. Editing the range, opening another file, switching tools, or closing the app stops playback. If FFplay is missing, the app shows an error when playback is requested; trimming still works.

Choose **ClipMaker** from the Tools menu to show its view in the main window. Build the ordered music list with `+` and `−`; for each audio file, enter **From** and **To** as `minutes:seconds` (for example `1:30` or `1:30.500` for milliseconds). Build a separate ordered image/video list the same way and enter each visual's duration in the same format. **Fill last** sets the last visual to the remaining total music time. The visual durations must sum to all selected music segments. A video uses its first specified seconds. Choose even output width and height, then **Preview full video** to render the entire sequence at a smaller size and play it in FFplay, or **Save video** to render the full-size MP4. The preview is cached until the inputs change. ClipMaker stretches each visual to the chosen output size, following its current renderer behavior.

## Test

```powershell
uv run python -m unittest discover -s tests -v
```

The automated tests cover configuration loading, time validation, metadata editing, playlist expansion, batch queue behavior, download options, trimmer playback, and a full ClipMaker montage rendered from generated media. A live YouTube download needs network access and may require updating `yt-dlp` when YouTube changes.

## Build a Windows executable

Run this in PowerShell from the repository root. FFmpeg, FFprobe, and FFplay must be installed on the build computer.

```powershell
$project = (Get-Location).Path
$ffmpeg = (Get-Command ffmpeg).Source
$ffprobe = (Get-Command ffprobe).Source
$ffplay = (Get-Command ffplay).Source
uv run --with pyinstaller python -m PyInstaller --noconfirm --onedir --windowed --name YTDownloader --distpath "$env:USERPROFILE\Desktop" --add-data "${project}\YTDownloader_v2\config.yaml:." --add-data "${project}\YTDownloader_v2\default.png:." --add-binary "${ffmpeg}:." --add-binary "${ffprobe}:." --add-binary "${ffplay}:." --collect-submodules yt_dlp.extractor --collect-submodules clip_maker --collect-submodules moviepy --collect-all imageio_ffmpeg YTDownloader_v2/main.py
```

The output is `Desktop\YTDownloader\YTDownloader.exe`. Distribute the entire `YTDownloader` folder. It includes FFmpeg, FFprobe, and FFplay, so the target computer does not need Python, uv, or a separate FFmpeg installation. Edit `config.yaml` before building if you need different defaults.

## Possible next steps

