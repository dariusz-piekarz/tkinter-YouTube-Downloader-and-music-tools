import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "YTDownloader_v2"))


class FakePlayer:
    def __init__(self):
        self.running = True
        self.terminations = 0

    def poll(self):
        return None if self.running else 0

    def terminate(self):
        self.running = False
        self.terminations += 1

    def wait(self):
        return 0


class ShrinkerPreviewTests(unittest.TestCase):
    def test_preview_stops_when_changing_tab_selection_and_closing(self):
        from tkinter import TclError
        from app_core import YTDownloader
        from i18n import Language

        with tempfile.TemporaryDirectory() as directory:
            language = Language(Path(directory) / "settings.json")
            with patch("app_core.Language", return_value=language):
                try:
                    app = YTDownloader()
                except TclError as error:
                    self.skipTest(f"Tk display unavailable: {error}")
            destroyed = False
            try:
                app.show("shrink")
                shrinker = app.frames["shrink"]
                shrinker.source = Path(directory) / "song.mp3"
                shrinker.duration = 10
                shrinker.selection = (1, 3)
                shrinker.set_entry_time(0, 1)
                shrinker.set_entry_time(1, 3)
                players = [FakePlayer() for _ in range(3)]
                with patch("shrinker_frame.preview_media", side_effect=players) as preview:
                    shrinker.play_selection()
                    preview.assert_called_with(shrinker.source, 1.0, 3.0, shrinker.config_data.ffmpeg)
                    self.assertEqual(shrinker.stop_button.cget("state"), "normal")
                    app.show("download")
                    self.assertEqual(players[0].terminations, 1)
                    self.assertEqual(shrinker.play_button.cget("state"), "normal")

                    app.show("shrink")
                    shrinker.play_selection()
                    shrinker.time_changed()
                    self.assertEqual(players[1].terminations, 1)

                    shrinker.play_selection()
                    app.root.destroy()
                    destroyed = True
                    self.assertEqual(players[2].terminations, 1)
            finally:
                if not destroyed:
                    app.root.destroy()


if __name__ == "__main__":
    unittest.main()
