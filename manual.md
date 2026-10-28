# Instrukcja projektu

## Środowisko i zależności

Projekt jest aplikacją Windows/Tkinter. `pyproject.toml` wymaga Pythona 3.14 (poniżej 3.15); sprawdzono Python 3.14.8, uv 0.13.1 oraz FFmpeg, FFprobe i FFplay 6.1.1 (pełny zestaw Gyan). Zależności Pythona (`yt-dlp`, `mutagen`, `Pillow`, `PyYAML`, ClipMaker i jego MoviePy) są zapisane w `pyproject.toml` i `uv.lock`. ClipMaker jest pobierany z repozytorium GitHub w przypiętej rewizji `c2c0f519454beb673efa153fdd38641e2bdff98f`; przy pierwszym `uv sync --locked` potrzebna jest sieć. Odsłuch i podgląd filmu wymagają `ffplay.exe`; przycinanie i przebieg dźwięku korzystają z `ffmpeg.exe`, a długość pliku z `ffprobe.exe`.

**Polecenia przygotowane do samodzielnego wykonania** na Windows, w PowerShell:

```powershell
winget install --id astral-sh.uv --exact
winget install --id Gyan.FFmpeg --exact
uv python install 3.14.8
Set-Location "C:\Users\DXD\Desktop\projekty\Python\tkinter-YouTube-Downloader-and-music-tools"
uv sync --locked
Get-Command ffmpeg,ffprobe,ffplay
```

Po instalacji przez WinGet otwórz nowe okno PowerShell, jeśli programy nie są jeszcze widoczne w `PATH`. Zestaw Windows FFmpeg jest opisany na [stronie Gyan](https://www.gyan.dev/ffmpeg/builds/), a instalacja uv na [stronie Astral](https://docs.astral.sh/uv/getting-started/installation/). Można też rozpakować trzy pliki `.exe` do jednego katalogu i dodać ten katalog do `PATH` na czas sesji:

```powershell
$env:PATH = "C:\Tools\ffmpeg\bin;$env:PATH"
Get-Command ffmpeg,ffprobe,ffplay
```

Ścieżkę do FFmpeg można ustawić w `YTDownloader_v2/config.yaml`, w polu `YTDownloader.ffmpeg`. Jeśli jest to pełna ścieżka do `ffmpeg.exe`, umieść obok niego `ffprobe.exe` i `ffplay.exe`. Domyślny katalog pobierania to `~/Downloads` (gdy nie istnieje, katalog domowy); inne ustawienia to `default_image` i `bitrate`. Aplikacja nie potrzebuje dodatkowych plików danych ani obowiązkowych zmiennych środowiskowych. Pobieranie filmów wymaga połączenia z siecią.

## Uruchamianie i używanie

**Polecenie przygotowane do samodzielnego wykonania** z katalogu głównego repozytorium:

```powershell
uv run python YTDownloader_v2/main.py
```

W narzędziu **Przycinanie** otwórz MP3 albo MP4. Ustaw początek i koniec w polach czasu lub przeciągnij znaczniki na wykresie. Przycisk **Odtwórz fragment** uruchamia dźwięk z wybranego zakresu; **Zatrzymaj** kończy odsłuch. Żółta linia orientacyjnie pokazuje aktualną pozycję. Zmiana zakresu lub pliku, przejście do innej zakładki i zamknięcie aplikacji zatrzymują odsłuch. Przycisk **Przytnij** zapisuje plik wynikowy w formacie źródła.

W menu **Narzędzia → ClipMaker** przejdź do widoku ClipMakera w głównym oknie. Górna lista zawiera muzykę w kolejności odtwarzania: dla każdego pliku wybierz zakres **Od/Do** w zapisie `minuty:sekundy`, np. `1:30`, albo `1:30.500`, jeśli potrzebujesz milisekund. Dolna lista zawiera zdjęcia i wideo w kolejności montażu; dla każdego wpisz czas trwania w tym samym formacie. Sekundy muszą mieścić się w przedziale 0–59; liczba minut może być większa od 59. Każda lista ma własne przyciski `+` i `−`. Suma czasów dolnej listy musi odpowiadać łącznej długości wybranych fragmentów muzyki; **Dopasuj ostatnie** wylicza pozostały czas dla ostatniego medium. Dla wideo używany jest fragment od początku pliku o podanej długości; zdjęcie pozostaje widoczne przez podany czas. Wybierz parzyste wymiary wyniku w pikselach (domyślnie 1080×1920) i ścieżkę MP4. **Podgląd całości** najpierw renderuje cały montaż w niższej rozdzielczości, a następnie otwiera go w oknie FFplay. **Zapisz film** renderuje MP4 w zadanych wymiarach. ClipMaker obecnie rozciąga obrazy do wymiarów wyniku. Podczas renderowania widok informuje o pracy i blokuje ponowny start; zamknięcie aplikacji jest dostępne po zakończeniu.

## Testowanie

**Polecenia rzeczywiście wykonane** w katalogu głównym repozytorium:

```powershell
uv add "clip-maker @ git+https://github.com/dariusz-piekarz/ClipMaker.git@c2c0f519454beb673efa153fdd38641e2bdff98f"
uv lock
uv sync --locked
uv --version
uv run python --version
Get-Command ffmpeg,ffprobe,ffplay
ffmpeg -version
ffprobe -version
ffplay -version
ffplay -h full
uv run python -m unittest discover -s tests -v
```

Z ostatniego uruchomienia pełnego zestawu: **22 testy, wszystkie OK**. Po rozszerzeniu testu widoku wykonano ponownie testy samego ClipMakera: **6 testów, wszystkie OK**. Weryfikacja obejmowała konstrukcję polecenia FFplay, brak odtwarzacza, zatrzymanie przy zmianie zakresu i zakładki, widok ClipMakera w głównym oknie, dodawanie i usuwanie w obu listach, zapis `m:ss.mmm`, dopasowanie czasu ostatniego medium, przeliczenie pól na sekundy dla renderera, mapowanie wideo oraz render montażu z jednego i dwóch fragmentów muzyki. W renderze z dwoma fragmentami osobno sprawdzono częstotliwość dźwięku przed i po przejściu między nimi. Test renderu symulował także program bez konsoli (`stdout` i `stderr` równe `None`). `ffplay -h full` potwierdził dostępność opcji `-ss`, `-t`, `-nodisp` i `-autoexit`. Polecenie `uv add` zostało użyte do aktualizacji zależności projektu; `uv lock` i `uv sync --locked` wykonano po dopasowaniu wersji Pythona.

**Rzeczywiście wykonano** również próbę odtwarzania: FFmpeg wygenerował dwusekundowy MP3, a FFplay uruchomiony przez `preview_media` odtworzył zakres 0,25–0,75 s z `SDL_AUDIODRIVER=dummy`; proces zakończył się kodem 0. Poniższy skrypt pozwala powtórzyć próbę bez urządzenia audio:

```powershell
$env:SDL_AUDIODRIVER = 'dummy'
@'
import sys
import subprocess
import tempfile
from pathlib import Path
sys.path.insert(0, 'YTDownloader_v2')
from Config import Config
from shrink_core import preview_media
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / 'tone.mp3'
    ffmpeg = Config().ffmpeg
    subprocess.run([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i',
                    'sine=frequency=440:duration=2', str(source)], check=True)
    player = preview_media(source, 0.25, 0.75, ffmpeg)
    print('ffplay exit:', player.wait(timeout=10))
'@ | uv run python -
Remove-Item Env:SDL_AUDIODRIVER
```

**Rzeczywiście wykonano** również automatyczną próbę ClipMakera: wygenerowano obrazy i pliki WAV, zbudowano pełny film MP4 z jednym oraz z dwoma wybranymi fragmentami muzyki i sprawdzono jego długość, obecność dźwięku i kolory kolejnych ujęć. Widok ClipMakera w głównym oknie sprawdzono programowo, łącznie z dodawaniem/usuwaniem w obu listach. Po zmianie widoku uruchomiono jego przycisk podglądu dla dwóch fragmentów muzyki i dwóch obrazów: wyrenderował pełny plik MP4, a kontrola obecności gotowego pliku przeszła. W tej próbie wywołanie odtwarzacza zastąpiono kontrolą pliku; wcześniejsza próba FFplay z testowymi sterownikami obrazu i dźwięku zakończyła się kodem 0. Nie wykonywano odsłuchu przez fizyczne głośniki ani oceny podglądu przez użytkownika. Do ręcznej kontroli uruchom aplikację i sprawdź podgląd na własnych plikach.

## Budowanie programu Windows

**Polecenia przygotowane do samodzielnego wykonania; build nie był uruchamiany.** Z katalogu głównego repozytorium:

```powershell
$project = (Get-Location).Path
$ffmpeg = (Get-Command ffmpeg).Source
$ffprobe = (Get-Command ffprobe).Source
$ffplay = (Get-Command ffplay).Source
uv run --with pyinstaller python -m PyInstaller --noconfirm --onedir --windowed --name YTDownloader --distpath "$env:USERPROFILE\Desktop" --add-data "${project}\YTDownloader_v2\config.yaml:." --add-data "${project}\YTDownloader_v2\default.png:." --add-binary "${ffmpeg}:." --add-binary "${ffprobe}:." --add-binary "${ffplay}:." --collect-submodules yt_dlp.extractor --collect-submodules clip_maker --collect-submodules moviepy --collect-all imageio_ffmpeg YTDownloader_v2/main.py
```

Wynik powinien znaleźć się w `Desktop\YTDownloader\YTDownloader.exe`; do dystrybucji potrzebny jest cały katalog `YTDownloader`. Dołączone trzy programy FFmpeg muszą pozostać razem; biblioteka ClipMaker i MoviePy są pakowane razem z Pythonem. Jeśli używasz dystrybucji FFmpeg opartej na dodatkowych DLL, dołącz również wymagane przez nią pliki. Po zbudowaniu sprawdź odsłuch i podgląd ClipMakera na komputerze docelowym.
