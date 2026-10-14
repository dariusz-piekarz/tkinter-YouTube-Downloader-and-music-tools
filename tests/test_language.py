import sys
import tempfile
import unittest
from pathlib import Path
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
                app.frames["download"].url.insert(0, "https://example.com/video")
                app.frames["fields editor"].fields["title"].insert(0, "Próba")
                app.set_language("en")
                self.assertEqual(app.frames["download"].download_button.cget("text"), "Download")
                self.assertEqual(app.frames["shrink"].extract_button.cget("text"), "Extract")
                self.assertEqual(app.frames["fields editor"].field_labels["artist"].cget("text"), "Artist")
                self.assertEqual(app.frames["download"].url.get(), "https://example.com/video")
                self.assertEqual(app.frames["fields editor"].fields["title"].get(), "Próba")
                app.set_language("pl")
                self.assertEqual(app.frames["shrink"].extract_button.cget("text"), "Przytnij")
            finally:
                app.root.destroy()
