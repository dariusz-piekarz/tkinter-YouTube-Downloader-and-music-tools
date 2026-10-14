from pathlib import Path
import json
import subprocess


def parse_time(minutes: str, seconds: str, milliseconds: str) -> float:
    parts = (minutes, seconds, milliseconds)
    if any(not part.strip().isdigit() for part in parts):
        raise ValueError("Time fields must contain non-negative whole numbers.")
    minute, second, millisecond = map(int, parts)
    if second >= 60 or millisecond >= 1000:
        raise ValueError("Seconds must be below 60 and milliseconds below 1000.")
    return minute * 60 + second + millisecond / 1000


def media_duration(path: str | Path, ffmpeg: str) -> float:
    probe = str(Path(ffmpeg).with_name("ffprobe.exe")) if Path(ffmpeg).suffix.lower() == ".exe" else "ffprobe"
    result = subprocess.run(
        [probe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def trim_media(source: str | Path, destination: str | Path, start: float, end: float, ffmpeg: str) -> Path:
    source, destination = Path(source), Path(destination)
    if source.suffix.lower() not in {".mp3", ".mp4"} or destination.suffix.lower() != source.suffix.lower():
        raise ValueError("Source and destination must have the same MP3 or MP4 extension.")
    if source.resolve() == destination.resolve():
        raise ValueError("Choose a different output file.")
    if start < 0 or end <= start:
        raise ValueError("End time must be later than start time.")
    duration = media_duration(source, ffmpeg)
    if end > duration + 0.01:
        raise ValueError("End time exceeds the file duration.")
    command = [ffmpeg, "-y", "-v", "error", "-ss", str(start), "-i", str(source), "-t", str(end - start)]
    if source.suffix.lower() == ".mp3":
        command += ["-vn", "-c:a", "libmp3lame"]
    else:
        command += ["-c:v", "libx264", "-c:a", "aac"]
    command.append(str(destination))
    subprocess.run(command, check=True, capture_output=True, text=True)
    return destination
