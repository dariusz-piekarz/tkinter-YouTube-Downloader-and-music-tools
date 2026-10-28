"""Adapt the ClipMaker renderer to an audio range and timed visual rows."""

from dataclasses import dataclass
from contextlib import redirect_stderr
from math import isfinite
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

from clip_maker import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from clip_maker.utils import validate_inputs

from shrink_core import media_duration


@dataclass(frozen=True)
class AudioRow:
    path: Path
    start: float
    end: float


@dataclass(frozen=True)
class MediaRow:
    path: Path
    seconds: float


def parse_clock(value: str) -> float:
    """Read minutes:seconds with optional milliseconds from an editor field."""
    match = re.fullmatch(r"(\d+):([0-5]?\d)(?:\.(\d{1,3}))?", value.strip())
    if match is None:
        raise ValueError("Enter time as minutes:seconds[.milliseconds].")
    minutes, seconds, milliseconds = match.groups()
    return int(minutes) * 60 + int(seconds) + int((milliseconds or "0").ljust(3, "0")) / 1000


def format_clock(seconds: float) -> str:
    """Show the editor's canonical minutes:seconds.milliseconds format."""
    if not isfinite(seconds) or seconds < 0:
        raise ValueError("Time must be non-negative and finite.")
    minutes, remainder = divmod(round(seconds * 1000), 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{minutes}:{whole_seconds:02d}.{milliseconds:03d}"


def render_config(
    soundtrack: str | Path,
    audio_start: float,
    audio_end: float,
    rows: list[MediaRow],
    size: tuple[int, int],
    output: str | Path,
    ffmpeg: str,
) -> dict:
    """Validate the editor's timeline and map it to ClipMaker's JSON schema."""
    soundtrack = Path(soundtrack)
    if not soundtrack.is_file() or soundtrack.suffix.removeprefix(".").upper() not in AUDIO_EXTENSIONS + VIDEO_EXTENSIONS:
        raise ValueError("Choose an audio file.")
    if not isfinite(audio_start) or not isfinite(audio_end) or audio_start < 0 or audio_end <= audio_start:
        raise ValueError("Choose a valid audio range.")
    if audio_end > media_duration(soundtrack, ffmpeg) + 0.01:
        raise ValueError("The audio range exceeds the file duration.")
    if not rows:
        raise ValueError("Add at least one image or video.")
    if len(size) != 2 or any(not isinstance(value, int) or value <= 0 or value % 2 for value in size):
        raise ValueError("Width and height must be positive even numbers.")

    timings = []
    for index, row in enumerate(rows):
        path = Path(row.path)
        extension = path.suffix.removeprefix(".").upper()
        if not path.is_file() or extension not in IMAGE_EXTENSIONS + VIDEO_EXTENSIONS:
            raise ValueError(f"Choose an image or video in row {index + 1}.")
        if not isfinite(row.seconds) or row.seconds <= 0:
            raise ValueError(f"Enter a positive duration in row {index + 1}.")
        if extension in VIDEO_EXTENSIONS:
            if row.seconds > media_duration(path, ffmpeg) + 0.01:
                raise ValueError(f"Row {index + 1} exceeds the video duration.")
            timings.append([0, row.seconds])
        elif index < len(rows) - 1:
            timings.append(row.seconds)

    if abs(sum(row.seconds for row in rows) - (audio_end - audio_start)) > 0.002:
        raise ValueError("The total media duration must match the selected audio range.")

    config = {
        "media_files": [str(row.path) for row in rows],
        "clip_size": list(size),
        "media_time_schedule": timings,
        "audio_file": str(soundtrack),
        "audio_time": [audio_start, audio_end],
        "result_file": str(output),
    }
    validate_inputs(config["media_files"], size, timings, config["audio_file"],
                    config["audio_time"], config["result_file"])
    return config


def preview_size(size: tuple[int, int], maximum: int = 480) -> tuple[int, int]:
    """Keep the full timeline while lowering preview rendering cost."""
    factor = min(1.0, maximum / max(size))
    return tuple(max(2, 2 * round(value * factor / 2)) for value in size)


def validate_project(audio_rows: list[AudioRow], media_rows: list[MediaRow],
                     size: tuple[int, int], output: str | Path, ffmpeg: str) -> float:
    """Check every selected music segment and the complete visual timeline."""
    if not audio_rows:
        raise ValueError("Add at least one audio file.")
    total = 0.0
    for index, row in enumerate(audio_rows, 1):
        path = Path(row.path)
        if not path.is_file() or path.suffix.removeprefix(".").upper() not in AUDIO_EXTENSIONS + VIDEO_EXTENSIONS:
            raise ValueError(f"Choose an audio file in row {index}.")
        if not isfinite(row.start) or not isfinite(row.end) or row.start < 0 or row.end <= row.start:
            raise ValueError(f"Choose a valid audio range in row {index}.")
        if row.end > media_duration(path, ffmpeg) + 0.01:
            raise ValueError(f"Audio row {index} exceeds the file duration.")
        total += row.end - row.start
    if not media_rows:
        raise ValueError("Add at least one image or video.")
    if len(size) != 2 or any(not isinstance(value, int) or value <= 0 or value % 2 for value in size):
        raise ValueError("Width and height must be positive even numbers.")
    for index, row in enumerate(media_rows, 1):
        path = Path(row.path)
        extension = path.suffix.removeprefix(".").upper()
        if not path.is_file() or extension not in IMAGE_EXTENSIONS + VIDEO_EXTENSIONS:
            raise ValueError(f"Choose an image or video in row {index}.")
        if not isfinite(row.seconds) or row.seconds <= 0:
            raise ValueError(f"Enter a positive duration in row {index}.")
        if extension in VIDEO_EXTENSIONS and row.seconds > media_duration(path, ffmpeg) + 0.01:
            raise ValueError(f"Row {index} exceeds the video duration.")
    if abs(sum(row.seconds for row in media_rows) - total) > 0.002:
        raise ValueError("The total media duration must match the selected audio range.")
    if Path(output).suffix.lower() != ".mp4":
        raise ValueError("The output filename must end in .mp4.")
    if any(Path(output).resolve() == Path(row.path).resolve() for row in [*audio_rows, *media_rows]):
        raise ValueError("Choose a different output file.")
    return total


def render_project(audio_rows: list[AudioRow], media_rows: list[MediaRow],
                   size: tuple[int, int], output: str | Path, ffmpeg: str) -> None:
    """Join selected audio segments, then render the complete ClipMaker montage."""
    total = validate_project(audio_rows, media_rows, size, output, ffmpeg)
    if len(audio_rows) == 1:
        row = audio_rows[0]
        render_clip(render_config(row.path, row.start, row.end, media_rows, size, output, ffmpeg))
        return

    with TemporaryDirectory(prefix="clipmaker-audio-") as directory:
        soundtrack = Path(directory) / "soundtrack.flac"
        command = [ffmpeg, "-y", "-v", "error"]
        for row in audio_rows:
            command += ["-i", str(row.path)]
        filters = []
        for index, row in enumerate(audio_rows):
            filters.append(
                f"[{index}:a:0]atrim=start={row.start}:end={row.end},"
                f"asetpts=PTS-STARTPTS,aresample=48000,"
                f"aformat=sample_fmts=s16:channel_layouts=stereo[a{index}]"
            )
        inputs = "".join(f"[a{index}]" for index in range(len(audio_rows)))
        filters.append(f"{inputs}concat=n={len(audio_rows)}:v=0:a=1[out]")
        command += ["-filter_complex", ";".join(filters), "-map", "[out]",
                    "-c:a", "flac", str(soundtrack)]
        subprocess.run(command, check=True, capture_output=True, text=True)
        render_clip(render_config(soundtrack, 0, total, media_rows, size, output, ffmpeg))


def render_clip(config: dict) -> None:
    def run():
        # Import MoviePy only when rendering, so the main app starts quickly.
        from clip_maker.main import clipper_from_dict

        clipper_from_dict(config)

    # PyInstaller --windowed has no stderr; MoviePy's progress logger requires one.
    if sys.stderr is None:
        with open(os.devnull, "w", encoding="utf-8") as sink, redirect_stderr(sink):
            run()
    else:
        run()
