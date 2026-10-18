import sys
import tempfile
import unittest
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "YTDownloader_v2"))

from Config import Config
from downloader_core import download_media
from fields_editor_core import edit_fields, load_metadata
from shrink_core import media_duration, parse_time, trim_media


class CoreTests(unittest.TestCase):
    def test_config_is_independent_of_current_directory(self):
        self.assertTrue(Config().default_image.is_file())
        if shutil.which("ffmpeg"):
            self.assertTrue(Path(Config().ffmpeg).is_file())

    def test_bundled_ffmpeg_takes_priority(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            bundled = Path(directory) / "ffmpeg.exe"
            bundled.touch()
            with patch("Config.APP_DIR", Path(directory)):
                self.assertEqual(Config().ffmpeg, str(bundled))

    def test_time_parsing(self):
        self.assertEqual(parse_time("1", "02", "125"), 62.125)
        for values in (("0", "60", "0"), ("0", "0", "1000"), ("", "0", "0")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                parse_time(*values)

    def test_metadata_round_trip_on_empty_mp3(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            mp3 = Path(directory) / "test.mp3"
            mp3.write_bytes(b"")
            edit_fields(str(mp3), title="Tytuł", artist="Autor",
                        cover_image=Image.new("RGB", (2, 2), "red"))
            metadata = load_metadata(str(mp3))
            self.assertEqual(metadata["title"], "Tytuł")
            self.assertEqual(metadata["artist"], "Autor")
            self.assertEqual(metadata["cover_image"].size, (2, 2))

    def test_download_options_and_selected_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "custom.mp3"
            recorded = {}
            updates = []

            class FakeDownloader:
                def __init__(self, options):
                    recorded.update(options)

                def __enter__(self):
                    return self

                def __exit__(self, *_):
                    return False

                def download(self, urls):
                    self.urls = urls
                    recorded["progress_hooks"][0]({"status": "downloading", "downloaded_bytes": 25,
                                                     "total_bytes": 100})
                    recorded["progress_hooks"][0]({"status": "downloading", "downloaded_bytes": 50,
                                                     "total_bytes_estimate": 100})
                    recorded["progress_hooks"][0]({"status": "finished"})
                    recorded["postprocessor_hooks"][0]({"status": "started"})
                    target.write_bytes(b"test")

            with patch("downloader_core.YoutubeDL", FakeDownloader):
                self.assertEqual(download_media("https://example.com/video", target, "mp3", "ffmpeg",
                                                progress=lambda stage, percent: updates.append((stage, percent))), target)
            self.assertEqual(recorded["outtmpl"], str(target.with_suffix("")) + ".%(ext)s")
            self.assertEqual(recorded["postprocessors"][0]["preferredcodec"], "mp3")
            self.assertEqual(updates, [("downloading", 25), ("downloading", 50),
                                       ("processing", None), ("processing", None)])

    def test_trim_rejects_same_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "song.mp3"
            with self.assertRaises(ValueError):
                trim_media(path, path, 0, 1, "ffmpeg")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is unavailable")
    def test_trim_real_mp3(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.mp3"
            destination = Path(directory) / "output.mp3"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=2", str(source)], check=True)
            trim_media(source, destination, 0.25, 1.25, "ffmpeg")
            self.assertTrue(destination.is_file())
            self.assertAlmostEqual(media_duration(destination, "ffmpeg"), 1, delta=0.1)


if __name__ == "__main__":
    unittest.main()
