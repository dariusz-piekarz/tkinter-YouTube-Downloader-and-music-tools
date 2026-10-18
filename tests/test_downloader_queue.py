import sys
import tempfile
import time
import unittest
from pathlib import Path
from tkinter import TclError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "YTDownloader_v2"))

from app_core import YTDownloader
from downloader_core import DownloadItem


class DownloaderQueueTests(unittest.TestCase):
    def test_multiple_fields_download_in_order_and_reset_after_success(self):
        try:
            app = YTDownloader()
        except TclError as error:
            self.skipTest(f"Tk display unavailable: {error}")
        try:
            downloader = app.frames["download"]
            with tempfile.TemporaryDirectory() as directory:
                downloader.folder.set(directory)
                downloader.url.insert(0, "https://example.com/first")
                downloader.add_url_field()
                downloader.url_rows[1][1].insert(0, "https://example.com/second")
                self.assertEqual(len(downloader.url_rows), 2)
                downloader.remove_url_field(downloader.url_rows[0][0])
                self.assertEqual(len(downloader.url_rows), 1)
                self.assertEqual(downloader.url.get(), "https://example.com/second")
                downloader.add_url_field()
                downloader.url_rows[1][1].insert(0, "https://example.com/first")

                items = [DownloadItem("https://example.com/second", "Same title"),
                         DownloadItem("https://example.com/first", "Same title")]
                downloaded = []

                def fake_download(url, destination, _format, _ffmpeg, _bitrate, progress, cancel):
                    downloaded.append((url, Path(destination).name))
                    progress("downloading", 50)
                    Path(destination).write_bytes(b"file")

                with patch("downloader_frame.expand_urls", return_value=items) as expand, \
                     patch("downloader_frame.download_media", side_effect=fake_download), \
                     patch("downloader_frame.messagebox.showinfo") as success:
                    downloader.action()
                    deadline = time.monotonic() + 5
                    while not success.called and time.monotonic() < deadline:
                        app.root.update()
                        time.sleep(0.01)
                self.assertTrue(success.called)
                expand.assert_called_once_with(
                    ["https://example.com/second", "https://example.com/first"],
                    downloader.config_data.ffmpeg, unittest.mock.ANY,
                )
                self.assertEqual(downloaded, [
                    ("https://example.com/second", "Same title.mp3"),
                    ("https://example.com/first", "Same title (2).mp3"),
                ])
                self.assertEqual(len(downloader.url_rows), 1)
                self.assertEqual(downloader.url.get(), "")
                self.assertEqual(str(downloader.cancel_button.cget("state")), "disabled")

                downloader.url.insert(0, "https://example.com/retry")
                downloader.add_url_field()
                downloader.url_rows[1][1].insert(0, "https://example.com/retry2")
                with patch("downloader_frame.messagebox.showerror"):
                    downloader.finish("failure")
                self.assertEqual(len(downloader.url_rows), 2)
                self.assertEqual(downloader.url.get(), "https://example.com/retry")
        finally:
            app.root.destroy()
