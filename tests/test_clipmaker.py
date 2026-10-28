import math
import sys
import tempfile
import unittest
import wave
import struct
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "YTDownloader_v2"))

from PIL import Image
from moviepy import VideoFileClip
import numpy as np

from clipmaker_core import AudioRow, MediaRow, format_clock, parse_clock, preview_size, render_clip, render_config, render_project, validate_project
from Config import Config


class ClipMakerIntegrationTests(unittest.TestCase):
    def test_clock_time_uses_base_sixty_and_optional_milliseconds(self):
        self.assertEqual(parse_clock("1:30"), 90)
        self.assertEqual(parse_clock("12:05.25"), 725.25)
        self.assertEqual(format_clock(90), "1:30.000")
        self.assertEqual(format_clock(59.9995), "1:00.000")
        for value in ("90", "1:60", "1:30.1234", "-1:00", "1:30:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_clock(value)

    def test_audio_range_and_visual_rows_render_one_complete_montage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / "first.png", root / "second.png"
            audio, output = root / "audio.wav", root / "montage.mp4"
            Image.new("RGB", (16, 16), "red").save(first)
            Image.new("RGB", (16, 16), "blue").save(second)
            with wave.open(str(audio), "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(8000)
                stream.writeframes(b"\0\0" * 16000)

            config = render_config(audio, 0.5, 1.5,
                                   [MediaRow(first, 0.4), MediaRow(second, 0.6)],
                                   (16, 16), output, Config().ffmpeg)
            self.assertEqual(config["media_time_schedule"], [0.4])
            self.assertEqual(config["audio_time"], [0.5, 1.5])
            with patch.object(sys, "stdout", None), patch.object(sys, "stderr", None):
                render_clip(config)
            with VideoFileClip(str(output)) as video:
                self.assertTrue(math.isclose(video.duration, 1, abs_tol=0.05))
                self.assertIsNotNone(video.audio)
                self.assertGreater(video.get_frame(0.1)[0, 0, 0], 200)
                self.assertGreater(video.get_frame(0.8)[0, 0, 2], 200)

    def test_visual_duration_must_cover_selected_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image, audio, output = root / "photo.png", root / "audio.wav", root / "output.mp4"
            image.touch()
            audio.touch()
            with patch("clipmaker_core.media_duration", return_value=3):
                with self.assertRaisesRegex(ValueError, "total media duration"):
                    render_config(audio, 0, 2, [MediaRow(image, 1)], (16, 16), output, "ffmpeg")
            self.assertEqual(preview_size((1080, 1920)), (270, 480))

    def test_video_row_uses_its_first_seconds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video, image, audio = root / "scene.mp4", root / "photo.png", root / "audio.wav"
            for path in (video, image, audio):
                path.touch()
            with patch("clipmaker_core.media_duration", side_effect=lambda path, _ffmpeg: 2 if path == audio else 1):
                config = render_config(audio, 0, 2,
                                       [MediaRow(video, 1), MediaRow(image, 1)],
                                       (16, 16), root / "output.mp4", "ffmpeg")
            self.assertEqual(config["media_time_schedule"], [[0, 1]])

    def test_two_music_segments_render_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / "first.png", root / "second.png"
            music_a, music_b, output = root / "a.wav", root / "b.wav", root / "montage.mp4"
            Image.new("RGB", (16, 16), "red").save(first)
            Image.new("RGB", (16, 16), "blue").save(second)
            for audio, frequency in ((music_a, 440), (music_b, 880)):
                with wave.open(str(audio), "wb") as stream:
                    stream.setnchannels(1)
                    stream.setsampwidth(2)
                    stream.setframerate(8000)
                    stream.writeframes(b"".join(struct.pack("<h", round(12000 * math.sin(2 * math.pi * frequency * n / 8000)))
                                                for n in range(8000)))
            audio_rows = [AudioRow(music_a, 0.2, 0.7), AudioRow(music_b, 0.1, 0.6)]
            media_rows = [MediaRow(first, 0.5), MediaRow(second, 0.5)]
            self.assertAlmostEqual(validate_project(audio_rows, media_rows, (16, 16), output, Config().ffmpeg), 1)
            with patch.object(sys, "stdout", None), patch.object(sys, "stderr", None):
                render_project(audio_rows, media_rows, (16, 16), output, Config().ffmpeg)
            with VideoFileClip(str(output)) as video:
                self.assertTrue(math.isclose(video.duration, 1, abs_tol=0.05))
                self.assertIsNotNone(video.audio)
                self.assertGreater(video.get_frame(0.2)[0, 0, 0], 200)
                self.assertGreater(video.get_frame(0.8)[0, 0, 2], 200)
                for offset, expected in ((0.1, 440), (0.6, 880)):
                    segment = video.audio.get_frame(np.arange(offset, offset + 0.2, 1 / 8000))[:, 0]
                    frequencies = np.fft.rfftfreq(len(segment), 1 / 8000)
                    peak = frequencies[np.argmax(np.abs(np.fft.rfft(segment)))]
                    self.assertAlmostEqual(peak, expected, delta=10)

    def test_editor_is_a_main_view_with_two_lists(self):
        from tkinter import TclError
        from app_core import YTDownloader
        from i18n import Language

        with tempfile.TemporaryDirectory() as directory:
            with patch("app_core.Language", return_value=Language(Path(directory) / "settings.json")):
                try:
                    app = YTDownloader()
                except TclError as error:
                    self.skipTest(f"Tk display unavailable: {error}")
            try:
                app.show("clipmaker")
                window = app.frames["clipmaker"]
                self.assertEqual(len(window.rows), 1)
                self.assertEqual(len(window.audio_rows), 1)
                self.assertEqual(window.winfo_toplevel(), app.root)
                window.add_row()
                window.add_audio_row()
                self.assertEqual(len(window.rows), 2)
                self.assertEqual(len(window.audio_rows), 2)
                window.audio_rows[0].start.set("0:10")
                window.audio_rows[0].end.set("2:10")
                window.audio_rows[1].start.set("0:05")
                window.audio_rows[1].end.set("0:35")
                window.rows[0].seconds.set("0:45.500")
                window.fill_last()
                self.assertEqual(window.rows[1].seconds.get(), "1:44.500")
                self.assertIn("2:30.000", window.total_label.cget("text"))
                for index, row in enumerate(window.audio_rows):
                    path = Path(directory) / f"audio{index}.wav"
                    path.touch()
                    row.path.set(str(path))
                for index, row in enumerate(window.rows):
                    path = Path(directory) / f"visual{index}.png"
                    path.touch()
                    row.path.set(str(path))
                with patch("clipmaker_core.media_duration", return_value=300):
                    audio_rows, media_rows, *_ = window.collect_project(Path(directory) / "result.mp4")
                self.assertEqual([(row.start, row.end) for row in audio_rows], [(10, 130), (5, 35)])
                self.assertEqual([row.seconds for row in media_rows], [45.5, 104.5])
                window.remove_row(window.rows[0])
                window.remove_audio_row(window.audio_rows[0])
                self.assertEqual(len(window.rows), 1)
                self.assertEqual(len(window.audio_rows), 1)
                app.show("download")
                app.show("clipmaker")
                self.assertIs(app.frames["clipmaker"], window)
                app.set_language("en")
                self.assertEqual(window.preview_button.cget("text"), "Preview full video")
            finally:
                app.root.destroy()


if __name__ == "__main__":
    unittest.main()
