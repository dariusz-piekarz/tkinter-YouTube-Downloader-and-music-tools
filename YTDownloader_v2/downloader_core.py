from dataclasses import dataclass
from pathlib import Path
import re
from threading import Event
from typing import Callable

from yt_dlp import YoutubeDL


class DownloadCancelled(Exception):
    """The user requested that the current download stop."""


@dataclass(frozen=True)
class DownloadItem:
    url: str
    title: str


def expand_urls(urls: list[str], ffmpeg: str, cancel: Event | None = None) -> list[DownloadItem]:
    """Resolve individual links and playlists into an ordered download queue."""
    items = []
    options = {
        "ffmpeg_location": ffmpeg,
        "extract_flat": "in_playlist",
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(options) as downloader:
        for url in urls:
            if cancel is not None and cancel.is_set():
                raise DownloadCancelled()
            info = downloader.extract_info(url, download=False)
            if cancel is not None and cancel.is_set():
                raise DownloadCancelled()
            if not info:
                continue
            entries = (info.get("entries") or []) if info.get("_type") == "playlist" else [info]
            for entry in entries:
                if cancel is not None and cancel.is_set():
                    raise DownloadCancelled()
                if not entry:
                    continue
                item_url = entry.get("webpage_url") or entry.get("url") or entry.get("id")
                if not item_url:
                    continue
                if entry.get("ie_key") == "Youtube" and "://" not in item_url:
                    item_url = f"https://www.youtube.com/watch?v={item_url}"
                items.append(DownloadItem(item_url, entry.get("title") or "video"))
    if not items:
        raise ValueError("No downloadable videos found.")
    return items


def unique_destination(directory: str | Path, title: str, media_format: str,
                       reserved: set[Path] | None = None) -> Path:
    """Choose a Windows-safe filename without replacing an existing download."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip().rstrip(" .")[:150].rstrip(" .") or "video"
    if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                                      *(f"LPT{i}" for i in range(1, 10))}:
        name = f"_{name}"
    folder = Path(directory)
    candidate = folder / f"{name}.{media_format}"
    number = 2
    while candidate.exists() or (reserved is not None and candidate in reserved):
        candidate = folder / f"{name} ({number}).{media_format}"
        number += 1
    if reserved is not None:
        reserved.add(candidate)
    return candidate


def download_media(url: str, destination: str | Path, media_format: str, ffmpeg: str,
                   bitrate: str = "192k",
                   progress: Callable[[str, float | None], None] | None = None,
                   cancel: Event | None = None) -> Path:
    """Download a single video to the file selected by the user."""
    if not url.strip():
        raise ValueError("Enter a video URL.")
    if media_format not in {"mp3", "mp4"}:
        raise ValueError("Choose MP3 or MP4.")
    destination = Path(destination)
    if destination.suffix.lower() != f".{media_format}":
        raise ValueError(f"The output filename must end in .{media_format}.")
    if cancel is not None and cancel.is_set():
        raise DownloadCancelled()

    options = {
        "outtmpl": str(destination.with_suffix("")) + ".%(ext)s",
        "noplaylist": True,
        "ffmpeg_location": ffmpeg,
        "quiet": True,
        "noprogress": True,
        "overwrites": True,
    }
    if progress is not None or cancel is not None:
        def download_hook(data):
            if cancel is not None and cancel.is_set():
                raise DownloadCancelled()
            if data.get("status") == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes", 0)
                percent = min(100.0, max(0.0, downloaded * 100 / total)) if total else None
                if progress is not None:
                    progress("downloading", percent)
            elif data.get("status") == "finished":
                if progress is not None:
                    progress("processing", None)

        def postprocessor_hook(data):
            if cancel is not None and cancel.is_set():
                raise DownloadCancelled()
            if data.get("status") == "started":
                if progress is not None:
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
    if cancel is not None and cancel.is_set():
        raise DownloadCancelled()
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
