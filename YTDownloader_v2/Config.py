from pathlib import Path
import shutil

import yaml


APP_DIR = Path(__file__).resolve().parent


class Config:
    def __init__(self, path=APP_DIR / "config.yaml"):
        with open(path, encoding="utf-8") as config_file:
            settings = (yaml.safe_load(config_file) or {}).get("YTDownloader", {})
        self.default_path = Path(settings.get("default_path") or Path.home() / "Downloads").expanduser()
        if not self.default_path.is_dir():
            self.default_path = Path.home()
        self.default_image = APP_DIR / settings.get("default_image", "default.png")
        self.bitrate = str(settings.get("bitrate", "192k"))
        configured_ffmpeg = str(settings.get("ffmpeg") or "ffmpeg")
        bundled_ffmpeg = APP_DIR / "ffmpeg.exe"
        if configured_ffmpeg.lower() in {"ffmpeg", "ffmpeg.exe"} and bundled_ffmpeg.is_file():
            self.ffmpeg = str(bundled_ffmpeg)
        else:
            self.ffmpeg = shutil.which(configured_ffmpeg) or configured_ffmpeg
