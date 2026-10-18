from pathlib import Path
from typing import Callable

from yt_dlp import YoutubeDL


def download_media(url: str, destination: str | Path, media_format: str, ffmpeg: str,
                   bitrate: str = "192k",
                   progress: Callable[[str, float | None], None] | None = None) -> Path:
    """Download a single video to the file selected by the user."""
    if not url.strip():
        raise ValueError("Enter a video URL.")
    if media_format not in {"mp3", "mp4"}:
        raise ValueError("Choose MP3 or MP4.")
    destination = Path(destination)
    if destination.suffix.lower() != f".{media_format}":
        raise ValueError(f"The output filename must end in .{media_format}.")

    options = {
        "outtmpl": str(destination.with_suffix("")) + ".%(ext)s",
        "noplaylist": True,
        "ffmpeg_location": ffmpeg,
        "quiet": True,
        "noprogress": True,
        "overwrites": True,
    }
    if progress is not None:
        def download_hook(data):
            if data.get("status") == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes", 0)
                percent = min(100.0, max(0.0, downloaded * 100 / total)) if total else None
                progress("downloading", percent)
            elif data.get("status") == "finished":
                progress("processing", None)

        def postprocessor_hook(data):
            if data.get("status") == "started":
                progress("processing", None)

        options["progress_hooks"] = [download_hook]
        options["postprocessor_hooks"] = [postprocessor_hook]
    if media_format == "mp3":
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate.removesuffix("k"),
            }],
        })
    else:
        options.update({
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "merge_output_format": "mp4",
            "recodevideo": "mp4",
        })
    with YoutubeDL(options) as downloader:
        downloader.download([url.strip()])
    if not destination.is_file():
        raise RuntimeError("The download finished without creating the selected file.")
    return destination


def get_title(url: str, ffmpeg: str) -> str:
    """Get the title of a video."""
    if not url.strip():
        raise ValueError("Enter a video URL.")
    options = {
        "ffmpeg_location": ffmpeg,
        "quiet": True,
        "noprogress": True,
    }
    with YoutubeDL(options) as downloader:
        info = downloader.extract_info(url.strip(), download=False)
    return info.get("title", "unknown_title")
