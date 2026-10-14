from pathlib import Path

from yt_dlp import YoutubeDL


def download_media(url: str, destination: str | Path, media_format: str, ffmpeg: str, bitrate: str = "192k") -> Path:
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
