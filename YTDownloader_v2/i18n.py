import json
import os
from pathlib import Path


STRINGS = {
    "pl": {
        "menu": "Narzędzia", "language": "Język",
        "download_tab": "Pobieranie", "shrink_tab": "Przycinanie",
        "fields_tab": "Edycja metadanych",
        "clipmaker_tab": "ClipMaker",
        "clip_audio_group": "Lista muzyki (kolejność odtwarzania)", "clip_audio_file": "Plik audio",
        "clip_audio_start": "Od (m:ss)", "clip_audio_end": "Do (m:ss)",
        "clip_media_group": "Kolejne ujęcia", "clip_media_file": "Zdjęcie lub wideo",
        "clip_duration": "Czas (m:ss)",
        "clip_fill_last": "Dopasuj ostatnie",
        "clip_total": "Ujęcia: {media} / muzyka: {audio}",
        "clip_time_format": "Wpisz czas jako minuty:sekundy[.milisekundy], np. 1:30.500.",
        "clip_output_group": "Wynik", "clip_size": "Rozmiar (px)",
        "clip_output_file": "Plik MP4", "clip_preview": "Podgląd całości",
        "clip_export": "Zapisz film", "clip_rendering": "Tworzenie filmu...",
        "clip_invalid": "Nieprawidłowy projekt", "clip_render_failed": "Błąd tworzenia filmu",
        "clip_wait_render": "Poczekaj na koniec tworzenia filmu.",
        "clip_preview_failed": "Nie udało się odtworzyć podglądu filmu.",
        "clip_choose_audio": "Wybierz plik z muzyką.",
        "clip_add_audio": "Dodaj co najmniej jeden plik muzyczny.",
        "clip_row_audio": "Wybierz muzykę w wierszu {row}.",
        "clip_row_audio_range": "Wybierz prawidłowy zakres muzyki w wierszu {row}.",
        "clip_row_audio_exceeds": "Zakres muzyki w wierszu {row} przekracza długość pliku.",
        "clip_audio_range": "Wybierz prawidłowy zakres muzyki.",
        "clip_audio_exceeds": "Zakres muzyki przekracza długość pliku.",
        "clip_add_media": "Dodaj co najmniej jedno zdjęcie lub wideo.",
        "clip_size_even": "Szerokość i wysokość muszą być dodatnimi, parzystymi liczbami.",
        "clip_total_mismatch": "Suma czasów ujęć musi być równa łącznej długości fragmentów muzyki.",
        "clip_last_no_time": "Muzyka musi być dłuższa niż poprzednie ujęcia.",
        "clip_numeric": "Wpisz prawidłowe wartości liczbowe.",
        "clip_row_media": "Wybierz zdjęcie lub wideo w wierszu {row}.",
        "clip_row_duration": "Wpisz dodatni czas w wierszu {row}.",
        "clip_row_video_exceeds": "Wiersz {row} przekracza długość wideo.",
        "downloader_title": "Pobieranie z YouTube", "video_url": "Adres filmu",
        "video_urls": "Adresy filmów / playlist", "format": "Format",
        "folder": "Folder", "browse": "Wybierz", "choose_folder": "Wybierz folder pobierania",
        "folder_missing": "Wybrany folder nie istnieje.",
        "queue_progress": "Ukończono {done} z {total}",
        "queue_done": "Ukończono {count} z {count}",
        "current_download": "Teraz: {title}",
        "batch_saved": "Wszystkie pliki zostały zapisane.",
        "no_downloadable": "Nie znaleziono filmów do pobrania.",
        "download": "Pobierz", "downloading": "Pobieranie...",
        "cancel": "Anuluj", "canceling": "Anulowanie pobierania...",
        "download_cancelled": "Pobieranie anulowane.",
        "fetching_title": "Pobieranie informacji o filmie...",
        "download_progress": "Pobrano {percent}%",
        "processing_download": "Przetwarzanie pliku...",
        "save_download": "Zapisz pobrany plik", "download_failed": "Błąd pobierania",
        "file_saved": "Plik został zapisany.", "enter_url": "Wpisz adres filmu.",
        "no_file": "Nie wybrano pliku", "open_media": "Otwórz MP3 / MP4",
        "start": "Początek", "end": "Koniec", "extract": "Przytnij",
        "waveform_empty": "Otwórz plik, aby zobaczyć przebieg dźwięku.",
        "waveform_loading": "Wczytywanie przebiegu dźwięku...",
        "waveform_unavailable": "Podgląd dźwięku niedostępny dla tego pliku.",
        "waveform_hint": "Przeciągnij zieloną lub czerwoną granicę, aby wybrać fragment.",
        "play_selection": "Odtwórz fragment", "stop_preview": "Zatrzymaj",
        "preview_failed": "Błąd odsłuchu",
        "preview_could_not_play": "Nie udało się odtworzyć wybranego fragmentu.",
        "ffplay_unavailable": "Nie znaleziono FFplay. Zainstaluj FFplay obok FFmpeg lub dodaj go do PATH.",
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
        "clipmaker_tab": "ClipMaker",
        "clip_audio_group": "Music list (playback order)", "clip_audio_file": "Audio file",
        "clip_audio_start": "From (m:ss)", "clip_audio_end": "To (m:ss)",
        "clip_media_group": "Visual sequence", "clip_media_file": "Image or video",
        "clip_duration": "Duration (m:ss)",
        "clip_fill_last": "Fill last",
        "clip_total": "Visuals: {media} / audio: {audio}",
        "clip_time_format": "Enter time as minutes:seconds[.milliseconds], e.g. 1:30.500.",
        "clip_output_group": "Output", "clip_size": "Size (px)",
        "clip_output_file": "MP4 file", "clip_preview": "Preview full video",
        "clip_export": "Save video", "clip_rendering": "Rendering video...",
        "clip_invalid": "Invalid project", "clip_render_failed": "Video render failed",
        "clip_wait_render": "Wait for the video render to finish.",
        "clip_preview_failed": "Could not play the video preview.",
        "clip_choose_audio": "Choose a soundtrack file.",
        "clip_add_audio": "Add at least one audio file.",
        "clip_row_audio": "Choose an audio file in row {row}.",
        "clip_row_audio_range": "Choose a valid audio range in row {row}.",
        "clip_row_audio_exceeds": "Audio row {row} exceeds the file duration.",
        "clip_audio_range": "Choose a valid soundtrack range.",
        "clip_audio_exceeds": "The soundtrack range exceeds the file duration.",
        "clip_add_media": "Add at least one image or video.",
        "clip_size_even": "Width and height must be positive even numbers.",
        "clip_total_mismatch": "The total visual duration must match all selected music segments.",
        "clip_last_no_time": "The soundtrack must extend past the preceding visuals.",
        "clip_numeric": "Enter valid numeric values.",
        "clip_row_media": "Choose an image or video in row {row}.",
        "clip_row_duration": "Enter a positive duration in row {row}.",
        "clip_row_video_exceeds": "Row {row} exceeds the video duration.",
        "downloader_title": "YouTube downloader", "video_url": "Video URL",
        "video_urls": "Video / playlist URLs", "format": "Format",
        "folder": "Folder", "browse": "Browse", "choose_folder": "Choose download folder",
        "folder_missing": "The selected folder does not exist.",
        "queue_progress": "Completed {done} of {total}",
        "queue_done": "Completed {count} of {count}",
        "current_download": "Now: {title}",
        "batch_saved": "All files have been saved.",
        "no_downloadable": "No downloadable videos found.",
        "download": "Download", "downloading": "Downloading...",
        "cancel": "Cancel", "canceling": "Cancelling download...",
        "download_cancelled": "Download cancelled.",
        "fetching_title": "Fetching video information...",
        "download_progress": "Downloaded {percent}%",
        "processing_download": "Processing file...",
        "save_download": "Save download", "download_failed": "Download failed",
        "file_saved": "File saved successfully.", "enter_url": "Enter a video URL.",
        "no_file": "No file selected", "open_media": "Open MP3 / MP4",
        "start": "Start", "end": "End", "extract": "Extract",
        "waveform_empty": "Open a file to see its waveform.",
        "waveform_loading": "Loading waveform...",
        "waveform_unavailable": "Audio preview is unavailable for this file.",
        "waveform_hint": "Drag the green or red marker to select a segment.",
        "play_selection": "Play selection", "stop_preview": "Stop",
        "preview_failed": "Playback failed",
        "preview_could_not_play": "Could not play the selected segment.",
        "ffplay_unavailable": "FFplay was not found. Install it beside FFmpeg or add it to PATH.",
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
    "No downloadable videos found.": "no_downloadable",
    "Time fields must contain non-negative whole numbers.": "time_digits",
    "Seconds must be below 60 and milliseconds below 1000.": "time_range",
    "Source and destination must have the same MP3 or MP4 extension.": "same_extension",
    "Choose a different output file.": "different_file",
    "End time must be later than start time.": "end_after_start",
    "End time exceeds the file duration.": "end_exceeds",
    "Choose an end time after the start and within the file.": "choose_end",
    "FFplay is unavailable.": "ffplay_unavailable",
    "Choose an audio file.": "clip_choose_audio",
    "Add at least one audio file.": "clip_add_audio",
    "Choose a valid audio range.": "clip_audio_range",
    "The audio range exceeds the file duration.": "clip_audio_exceeds",
    "Add at least one image or video.": "clip_add_media",
    "Width and height must be positive even numbers.": "clip_size_even",
    "The total media duration must match the selected audio range.": "clip_total_mismatch",
    "The soundtrack must extend past the preceding media.": "clip_last_no_time",
    "Enter valid numeric values.": "clip_numeric",
    "Enter time as minutes:seconds[.milliseconds].": "clip_time_format",
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
        for prefix, suffix, row_key in (
            ("Choose an audio file in row ", ".", "clip_row_audio"),
            ("Choose a valid audio range in row ", ".", "clip_row_audio_range"),
            ("Audio row ", " exceeds the file duration.", "clip_row_audio_exceeds"),
            ("Choose an image or video in row ", ".", "clip_row_media"),
            ("Enter a positive duration in row ", ".", "clip_row_duration"),
            ("Row ", " exceeds the video duration.", "clip_row_video_exceeds"),
        ):
            if message.startswith(prefix) and message.endswith(suffix):
                row = message[len(prefix):len(message) - len(suffix)]
                if row.isdigit():
                    return self.text(row_key).format(row=row)
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
