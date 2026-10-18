import sys
import tempfile
import unittest
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "YTDownloader_v2"))

from i18n import Language, STRINGS


class LanguageTests(unittest.TestCase):
    def test_all_translations_have_matching_keys(self):
        self.assertEqual(STRINGS["pl"].keys(), STRINGS["en"].keys())

    def test_selection_is_saved_and_errors_are_translated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            language = Language(path)
            self.assertEqual(language.code, "pl")
            self.assertEqual(language.error(ValueError("Choose a different output file.")),
                             "Wybierz inną nazwę pliku wynikowego.")
            language.select("en")
            self.assertEqual(Language(path).code, "en")
            self.assertEqual(language.error(ValueError("The output filename must end in .mp3.")),
                             "The output filename must end in .mp3.")

    def test_gui_switch_preserves_entry_contents(self):
        from tkinter import TclError
        from app_core import YTDownloader

        with tempfile.TemporaryDirectory() as directory:
            language = Language(Path(directory) / "settings.json")
            with patch("app_core.Language", return_value=language):
                try:
                    app = YTDownloader()
                except TclError as error:
                    self.skipTest(f"Tk display unavailable: {error}")
            try:
                self.assertEqual(app.frames["download"].download_button.cget("text"), "Pobierz")
                downloader = app.frames["download"]
                downloader.show_progress("downloading", 42)
                self.assertEqual(float(downloader.progress_bar.cget("value")), 42)
                self.assertEqual(downloader.progress_label.cget("text"), "Pobrano 42%")
                app.frames["download"].url.insert(0, "https://example.com/video")
                app.frames["fields editor"].fields["title"].insert(0, "Próba")
                app.set_language("en")
                self.assertEqual(app.frames["download"].download_button.cget("text"), "Download")
                self.assertEqual(downloader.progress_label.cget("text"), "Downloaded 42%")
                self.assertEqual(app.frames["shrink"].extract_button.cget("text"), "Extract")
                self.assertEqual(app.frames["fields editor"].field_labels["artist"].cget("text"), "Artist")
                self.assertEqual(app.frames["download"].url.get(), "https://example.com/video")
                self.assertEqual(app.frames["fields editor"].fields["title"].get(), "Próba")
                app.set_language("pl")
                self.assertEqual(app.frames["shrink"].extract_button.cget("text"), "Przytnij")
                downloader.show_progress("processing")
                self.assertEqual(str(downloader.progress_bar.cget("mode")), "indeterminate")
                downloader.reset_progress()
                self.assertEqual(str(downloader.progress_bar.cget("mode")), "determinate")
                self.assertEqual(downloader.progress_label.cget("text"), "")
                self.assertEqual(str(downloader.cancel_button.cget("state")), "disabled")
                downloader.downloading = True
                downloader.cancel_event = Event()
                downloader.download_button.config(state="disabled")
                downloader.cancel_button.config(state="normal")
                downloader.show_progress("title")
                downloader.cancel_download()
                self.assertEqual(downloader.progress_label.cget("text"), "Pobieranie anulowane.")
                self.assertEqual(str(downloader.download_button.cget("state")), "normal")
                self.assertEqual(str(downloader.cancel_button.cget("state")), "disabled")
                app.show("shrink")
                app.root.update()
                shrinker = app.frames["shrink"]
                minute, second, _ = shrinker.entries[0]
                self.assertLess(second.winfo_rootx() - minute.winfo_rootx() - minute.winfo_width(), 20)
                shrinker.duration = 120
                shrinker.selection = (0, 120)
                shrinker.start_drag(SimpleNamespace(x=shrinker.waveform_canvas.winfo_width() // 4))
                shrinker.stop_drag()
                self.assertEqual([entry.get() for entry in shrinker.entries[0]], ["0", "30", "0"])
            finally:
                app.root.destroy()
