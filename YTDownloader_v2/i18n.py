import json
import os
from pathlib import Path


STRINGS = {
    "pl": {
        "menu": "Narzędzia", "language": "Język",
        "download_tab": "Pobieranie", "shrink_tab": "Przycinanie",
        "fields_tab": "Edycja metadanych",
        "downloader_title": "Pobieranie z YouTube", "video_url": "Adres filmu",
        "download": "Pobierz", "downloading": "Pobieranie...",
        "save_download": "Zapisz pobrany plik", "download_failed": "Błąd pobierania",
        "file_saved": "Plik został zapisany.", "enter_url": "Wpisz adres filmu.",
        "no_file": "Nie wybrano pliku", "open_media": "Otwórz MP3 / MP4",
        "start": "Początek", "end": "Koniec", "extract": "Przytnij",
        "open_failed": "Nie udało się otworzyć pliku",
        "open_first": "Najpierw otwórz plik.", "invalid_time": "Nieprawidłowy czas",
        "choose_end": "Czas końcowy musi być późniejszy niż początkowy i mieścić się w pliku.",
        "extract_failed": "Błąd przycinania", "media_files": "Pliki multimedialne",
        "no_mp3": "Nie wybrano pliku MP3", "open_mp3": "Otwórz MP3",
        "title": "Tytuł", "artist": "Wykonawca", "album": "Album",
        "genre": "Gatunek", "track": "Numer utworu",
        "select_cover": "Wybierz okładkę", "clear_fields": "Wyczyść pola",
        "save": "Zapisz", "images": "Obrazy", "cover": "Okładka",
        "clipboard_no_image": "W schowku nie ma obrazu.",
        "save_failed": "Błąd zapisu", "metadata_saved": "Metadane zostały zapisane.",
        "open_mp3_first": "Najpierw otwórz plik MP3.",
        "cut": "Wytnij", "copy": "Kopiuj", "paste": "Wklej",
        "time_digits": "Pola czasu muszą zawierać nieujemne liczby całkowite.",
        "time_range": "Sekundy muszą być mniejsze niż 60, a milisekundy niż 1000.",
        "same_extension": "Plik źródłowy i wynikowy muszą mieć ten sam format MP3 lub MP4.",
        "different_file": "Wybierz inną nazwę pliku wynikowego.",
        "end_after_start": "Czas końcowy musi być późniejszy niż początkowy.",
        "end_exceeds": "Czas końcowy przekracza długość pliku.",
        "choose_format": "Wybierz MP3 lub MP4.",
        "output_extension": "Nazwa pliku wynikowego musi kończyć się na {extension}.",
        "missing_download": "Pobieranie zakończyło się bez utworzenia pliku.",
    },
    "en": {
        "menu": "Tools", "language": "Language",
        "download_tab": "Downloader", "shrink_tab": "Trimmer",
        "fields_tab": "Metadata editor",
        "downloader_title": "YouTube downloader", "video_url": "Video URL",
        "download": "Download", "downloading": "Downloading...",
        "save_download": "Save download", "download_failed": "Download failed",
        "file_saved": "File saved successfully.", "enter_url": "Enter a video URL.",
        "no_file": "No file selected", "open_media": "Open MP3 / MP4",
        "start": "Start", "end": "End", "extract": "Extract",
        "open_failed": "Open failed", "open_first": "Open a file first.",
        "invalid_time": "Invalid time",
        "choose_end": "Choose an end time after the start and within the file.",
        "extract_failed": "Extract failed", "media_files": "Media files",
        "no_mp3": "No MP3 selected", "open_mp3": "Open MP3",
        "title": "Title", "artist": "Artist", "album": "Album",
        "genre": "Genre", "track": "Track number",
        "select_cover": "Select cover", "clear_fields": "Clear fields",
        "save": "Save", "images": "Images", "cover": "Cover",
        "clipboard_no_image": "The clipboard does not contain an image.",
        "save_failed": "Save failed", "metadata_saved": "Metadata saved.",
        "open_mp3_first": "Open an MP3 file first.",
        "cut": "Cut", "copy": "Copy", "paste": "Paste",
        "time_digits": "Time fields must contain non-negative whole numbers.",
        "time_range": "Seconds must be below 60 and milliseconds below 1000.",
        "same_extension": "Source and destination must have the same MP3 or MP4 extension.",
        "different_file": "Choose a different output file.",
        "end_after_start": "End time must be later than start time.",
        "end_exceeds": "End time exceeds the file duration.",
        "choose_format": "Choose MP3 or MP4.",
        "output_extension": "The output filename must end in {extension}.",
        "missing_download": "The download finished without creating the selected file.",
    },
}

ERROR_KEYS = {
    "Enter a video URL.": "enter_url",
    "Choose MP3 or MP4.": "choose_format",
    "The download finished without creating the selected file.": "missing_download",
    "Time fields must contain non-negative whole numbers.": "time_digits",
    "Seconds must be below 60 and milliseconds below 1000.": "time_range",
    "Source and destination must have the same MP3 or MP4 extension.": "same_extension",
    "Choose a different output file.": "different_file",
    "End time must be later than start time.": "end_after_start",
    "End time exceeds the file duration.": "end_exceeds",
    "Choose an end time after the start and within the file.": "choose_end",
}


class Language:
    def __init__(self, path=None):
        base = Path(os.environ.get("APPDATA") or Path.home() / ".config")
        self.path = Path(path) if path is not None else base / "YTDownloader" / "settings.json"
        self.code = "pl"
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(saved, dict) and saved.get("language") in STRINGS:
                self.code = saved["language"]
        except (OSError, ValueError, TypeError):
            pass

    def text(self, key):
        return STRINGS[self.code][key]

    def error(self, error):
        message = str(error)
        key = ERROR_KEYS.get(message)
        if key:
            return self.text(key)
        prefix = "The output filename must end in "
        if message.startswith(prefix) and message.endswith("."):
            return self.text("output_extension").format(extension=message[len(prefix):-1])
        return message

    def select(self, code):
        if code not in STRINGS:
            raise ValueError("Unsupported language")
        self.code = code
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"language": code}), encoding="utf-8")
        except OSError:
            pass
