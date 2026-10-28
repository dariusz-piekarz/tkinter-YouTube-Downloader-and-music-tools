# Zmiany projektu

## 2026-10-28 — odsłuch zaznaczenia w Przycinaniu

**Problem.** Dotychczas użytkownik widział przebieg dźwięku i granice fragmentu, ale nie mógł posłuchać zawartości przed zapisaniem cięcia.

**Rozwiązanie i wpływ.** `shrink_core.py` wyszukuje FFplay obok skonfigurowanego FFmpeg, a następnie w `PATH`, i uruchamia osobny proces dla dokładnie wybranego zakresu. Parametry `-nodisp` oraz `-vn` wyłączają obraz, więc MP4 odtwarza samą ścieżkę audio. Proces działa poza główną pętlą Tkinter i kończy się po fragmencie. Brak FFplay daje czytelny komunikat zamiast ukrytego błędu. Przycinanie plików nadal wykonuje dotychczasowa funkcja `trim_media`.

W `shrinker_frame.py` dodano przyciski odtwarzania i zatrzymania oraz żółtą linię pozycji na wykresie. Zakres jest czytany z pól czasu przed startem. Odsłuch zatrzymuje się przy edycji czasu, przesunięciu granicy, otwarciu kolejnego pliku, rozpoczęciu zapisu i zniszczeniu okna. `app_core.py` zatrzymuje go także przy przejściu do innego narzędzia. `i18n.py` zawiera nowe etykiety i błędy po polsku i angielsku. `README.md` opisuje obsługę oraz dodanie FFplay do pakietu Windows; `manual.md` podaje odtwarzalne polecenia i rozróżnia wykonane kontrole od instrukcji.

**Kompromisy.** FFplay jest dodatkowym programem wymaganym tylko do odsłuchu; dlatego polecenie PyInstaller dołącza teraz `ffplay.exe` obok FFmpeg i FFprobe. Linia pozycji jest liczona zegarem aplikacji, a start dźwięku może mieć opóźnienie, więc jest orientacyjna. MP4 bez ścieżki audio nie da się odsłuchać; proces zakończy się i interfejs pokaże błąd, jeśli FFplay zwróci niezerowy kod. Nie dodano nowej biblioteki Pythona do audio ani pauzy, ponieważ podstawową potrzebą jest szybkie sprawdzenie wybranego fragmentu i jego zatrzymanie.

**Sprawdzenie.** Dodano testy dla lokalizacji FFplay, parametrów początku i długości odsłuchu, braku programu oraz zatrzymywania procesu przy zmianie zakładki, zakresu i zamknięciu aplikacji. `uv run python -m unittest discover -s tests -v` zakończył się wynikiem 16/16 OK. FFplay 6.1.1 uruchomiony przez nową funkcję na wygenerowanym MP3 z testowym sterownikiem audio zakończył się kodem 0. Nie uruchamiano budowania programu przez PyInstaller ani ręcznej próby przez fizyczne głośniki; te kroki są opisane w `manual.md`.

## 2026-10-28 — pierwszy etap integracji ClipMakera (zastąpiony poniżej)

**Problem.** ClipMaker był osobnym programem sterowanym plikiem JSON. Użytkownik chce wybrać jeden fragment muzyki i pod nim ułożyć dowolną liczbę zdjęć i wideo, określając czas każdego ujęcia, oraz zobaczyć podgląd całego montażu.

**Rozwiązanie i wpływ.** `pyproject.toml` i `uv.lock` dodają ClipMaker jako zależność z przypiętą rewizją repozytorium GitHub. Zakres Pythona ograniczono do 3.14, zgodnie z wymaganiem ClipMakera. Jego oryginalny silnik renderowania pozostaje w osobnym projekcie; lokalne, niezatwierdzone zmiany w tamtym repozytorium nie były używane ani modyfikowane. MoviePy 2.2.1 zostało zainstalowane wraz z ClipMakerem, a Pillow zostało dobrane do zgodnej wersji 11.3.0. `clipmaker_core.py` sprawdza pliki, czasy, wymiary i zgodność sumy ujęć z wybranym zakresem muzyki, a następnie mapuje wiersze na istniejący schemat ClipMakera. Końcowe zdjęcie jest obsługiwane przez dotychczasową zasadę ClipMakera: wypełnia pozostały czas muzyki; sprawdzenie sumy gwarantuje, że odpowiada to czasowi wpisanemu przez użytkownika. Dla wideo używany jest zakres od początku pliku o podanej długości.

`clipmaker_window.py` dodaje osobne okno Tkinter z wyborem jednego audio i zakresu, listą wierszy `+`/`−`, czasem każdego medium, przyciskiem dopasowania ostatniego wiersza, wymiarami i plikiem wynikowym. `app_core.py`, `menu.py` i `i18n.py` dodają pozycję menu, aktualizację języka i komunikaty. Render działa w wątku, dzięki czemu interfejs pozostaje responsywny. Podgląd renderuje **cały** montaż do tymczasowego MP4 w mniejszej rozdzielczości i otwiera go w FFplay; wynik podglądu jest ponownie używany, dopóki ustawienia się nie zmienią. Zamknięcie okna w trakcie renderu jest wstrzymane, aby nie przerwać zapisu pliku. `README.md` i `manual.md` opisują obsługę, zależności i polecenie pakowania.

Adapter na czas renderu zapewnia strumień błędów, jeśli aplikacja jest uruchomiona jako program Windows bez konsoli. MoviePy wypisuje tam pasek postępu; bez strumienia render kończył się błędem. Zmiana działa tylko w tym przypadku i nie zmienia logowania przy uruchomieniu z terminala.

**Kompromisy.** Podgląd wymaga pełnego renderu, więc przy długim montażu trzeba poczekać; FFplay pokazuje film w swoim oknie. Obecny renderer ClipMakera rozciąga obrazy do podanych wymiarów, co może zmienić proporcje. Zależność Git wymaga sieci przy pierwszym przygotowaniu środowiska, ale przypięta rewizja zapewnia powtarzalność. MoviePy i jego zależności powiększają instalację i przyszły pakiet Windows. Nie dodano sterowania fragmentem źródłowego wideo, ponieważ opisany interfejs wymagał tylko czasu trwania medium; wideo zaczyna się od sekundy 0.

**Sprawdzenie.** Dodano test renderujący film z dwóch wygenerowanych obrazów i wybranego fragmentu wygenerowanego WAV; zweryfikowano długość filmu, audio i kolejność obrazów. Test uruchamia render z `stdout` i `stderr` równymi `None`, tak jak w aplikacji bez konsoli. Testy sprawdzają też niezgodną sumę czasów, mapowanie wideo oraz otwarcie osobnego okna, dodanie/usunięcie wiersza i dopasowanie ostatniego czasu. Pełny zestaw `uv run python -m unittest discover -s tests -v` przeszedł: 20/20. Osobna próba programowa wyrenderowała podgląd całego filmu i odtworzyła go w FFplay z testowymi sterownikami audio/wideo (kod 0). Pakietu PyInstaller ani odsłuchu przez fizyczne urządzenie nie uruchamiano.

## 2026-10-28 — ClipMaker w głównym oknie i dwie listy

**Problem.** Użytkownik doprecyzował układ: ClipMaker ma być widokiem głównego okna, jak pozostałe narzędzia. Potrzebne są dwie niezależne listy: kolejne fragmenty muzyki z własnymi zakresami „Od/Do” oraz zdjęcia i wideo z czasem trwania. Pierwszy interfejs miał osobne okno i tylko jeden fragment audio.

**Rozwiązanie i wpływ.** `clipmaker_frame.py` zastępuje `clipmaker_window.py` ramką Tkinter podłączoną do `app_core.py` jako czwarty widok. Każda lista ma osobne przyciski dodawania i usuwania. Ramka zachowuje stan po przełączeniu narzędzi; przy wyjściu z widoku zamyka odtwarzacz podglądu. Główne okno powiększa się dla edytora i wraca do poprzedniego rozmiaru dla pozostałych narzędzi. Sumy czasu audio i mediów są pokazywane razem; przycisk dopasowania ostatniego medium korzysta z sumy wszystkich fragmentów muzyki. Podgląd i eksport nadal renderują cały film, a zmiana dowolnego pliku lub zakresu unieważnia zapisany podgląd.

`clipmaker_core.py` dodaje `AudioRow`, walidację każdego pliku i zakresu oraz kontrolę zgodności całkowitego czasu z listą mediów. Dla jednego fragmentu zachowuje bezpośredni render ClipMakera. Dla wielu fragmentów FFmpeg przycina każdy z nich, normalizuje do stereo 48 kHz i łączy w podanej kolejności w tymczasowy plik FLAC, który istniejący silnik ClipMakera przyjmuje jako jedną ścieżkę. Plik tymczasowy jest usuwany po renderze. Walidacja chroni też pliki wejściowe przed nadpisaniem i wymaga wyniku `.mp4`. `i18n.py` otrzymał etykiety i komunikaty błędów dla listy muzyki; `README.md` i `manual.md` opisują nowy sposób pracy. Zależności projektu nie zmieniły się w tej korekcie.

**Kompromisy.** Przy wielu fragmentach muzyki potrzebny jest dodatkowy krok FFmpeg oraz miejsce na tymczasowy FLAC. Obrazy są nadal rozciągane przez istniejący renderer ClipMakera. Wideo zaczyna się od sekundy 0, ponieważ użytkownik określił dla niego wyłącznie czas trwania. Podgląd odtwarza się w oknie FFplay po wyrenderowaniu całości.

**Sprawdzenie.** `uv run python -m unittest discover -s tests -v`: 21/21 OK. Test integracyjny renderuje dwa różne fragmenty WAV oraz dwa obrazy, sprawdza długość filmu, kolejność ujęć i analizą częstotliwości potwierdza kolejność fragmentów audio. Test interfejsu potwierdza, że ClipMaker jest częścią głównego okna, obie listy obsługują dodawanie i usuwanie, a stan pozostaje po zmianie widoku. Osobna próba z przycisku podglądu w nowym widoku wyrenderowała pełny MP4 z dwoma fragmentami muzyki i dwoma obrazami. `uv sync --locked` i `git diff --check` przeszły. Nie wykonywano nowego builda PyInstaller; polecenie pozostaje w `manual.md`.

## 2026-10-28 — zapis czasu w systemie 60‑tkowym

**Problem.** Pola ClipMakera pokazywały surową liczbę sekund, podczas gdy Przycinanie używa minut i sekund. Przy dłuższych plikach wpisanie i odczytanie zakresu było niewygodne.

**Rozwiązanie i wpływ.** `clipmaker_core.py` dodaje parsowanie `minuty:sekundy` z opcjonalnymi milisekundami i formatowanie do `m:ss.mmm`. `clipmaker_frame.py` stosuje ten zapis we wszystkich polach muzyki i mediów, po wyborze pliku, w licznikach sum oraz w wyniku **Dopasuj ostatnie**. Wartości są przeliczane na sekundy przed walidacją i renderem, więc silnik ClipMakera pozostaje bez zmian. `i18n.py` opisuje format w nagłówkach i komunikacie błędu. `README.md` i `manual.md` podają przykłady.

**Kompromisy.** Pole ma jeden zapis zamiast trzech oddzielnych pól Przycinania. Zapis `1:30` jest krótszy, a `1:30.500` zachowuje dokładność do milisekundy. Sekundy od 60 wzwyż są odrzucane, żeby nie mylić minut z surową liczbą sekund. Interfejs zaokrągla czas wykryty przez FFprobe do milisekundy, tak jak wcześniejsze pola dziesiętne.

**Sprawdzenie.** Testy obejmują granicę 59/60 sekund, opcjonalne milisekundy, błędne zakresy sekund, dopasowanie ostatniego medium powyżej minuty i wyświetlenie sumy w minutach. Wynik pełnego zestawu podano w `manual.md`.
