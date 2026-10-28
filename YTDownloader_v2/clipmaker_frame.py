"""ClipMaker view with ordered audio and visual timelines."""

import json
import subprocess
from math import isfinite
from pathlib import Path
from queue import Empty, Queue
from tempfile import TemporaryDirectory
from threading import Thread
from tkinter import Button, Canvas, Entry, Frame, Label, StringVar, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import LabelFrame, Progressbar, Scrollbar

from Config import Config
from clipmaker_core import AudioRow, MediaRow, format_clock, parse_clock, preview_size, render_project, validate_project
from shrink_core import ffplay_executable, media_duration


class AudioEditorRow(Frame):
    def __init__(self, parent, owner):
        super().__init__(parent)
        self.owner = owner
        self.path = StringVar(master=self)
        self.start = StringVar(master=self, value="0:00.000")
        self.end = StringVar(master=self)
        self.number_label = Label(self, width=4, anchor="e")
        self.number_label.grid(row=0, column=0, padx=(0, 5))
        self.path_entry = Entry(self, textvariable=self.path, state="readonly")
        self.path_entry.grid(row=0, column=1, sticky="ew")
        self.choose_button = Button(self, command=lambda: owner.choose_audio(self))
        self.choose_button.grid(row=0, column=2, padx=5)
        self.start_entry = Entry(self, textvariable=self.start, width=11, justify="center")
        self.start_entry.grid(row=0, column=3, padx=4)
        self.end_entry = Entry(self, textvariable=self.end, width=11, justify="center")
        self.end_entry.grid(row=0, column=4, padx=4)
        self.remove_button = Button(self, text="−", width=3, command=lambda: owner.remove_audio_row(self))
        self.remove_button.grid(row=0, column=5)
        self.columnconfigure(1, weight=1)
        self.start.trace_add("write", lambda *_: owner.update_total())
        self.end.trace_add("write", lambda *_: owner.update_total())

    def set_language(self):
        self.choose_button.config(text=self.owner.language.text("browse"))


class MediaEditorRow(Frame):
    def __init__(self, parent, owner):
        super().__init__(parent)
        self.owner = owner
        self.path = StringVar(master=self)
        self.seconds = StringVar(master=self, value="0:03.000")
        self.number_label = Label(self, width=4, anchor="e")
        self.number_label.grid(row=0, column=0, padx=(0, 5))
        self.path_entry = Entry(self, textvariable=self.path, state="readonly")
        self.path_entry.grid(row=0, column=1, sticky="ew")
        self.choose_button = Button(self, command=lambda: owner.choose_media(self))
        self.choose_button.grid(row=0, column=2, padx=5)
        self.seconds_entry = Entry(self, textvariable=self.seconds, width=11, justify="center")
        self.seconds_entry.grid(row=0, column=3, padx=5)
        self.remove_button = Button(self, text="−", width=3, command=lambda: owner.remove_row(self))
        self.remove_button.grid(row=0, column=4)
        self.columnconfigure(1, weight=1)
        self.seconds.trace_add("write", lambda *_: owner.update_total())

    def set_language(self):
        self.choose_button.config(text=self.owner.language.text("browse"))


class ClipMakerFrame(Frame):
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language
        self.config_data = Config()
        self.rendering = False
        self.render_mode = None
        self.render_updates = Queue()
        self.render_poll = None
        self.preview_temp = None
        self.preview_path = None
        self.preview_key = None
        self.preview_player = None
        self.player_poll = None
        self.rows = []
        self.audio_rows = []

        self.audio_group = LabelFrame(self, padding=8)
        self.audio_group.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        self.audio_group.columnconfigure(0, weight=1)
        self.audio_group.rowconfigure(1, weight=1)
        audio_headings = Frame(self.audio_group)
        audio_headings.grid(row=0, column=0, sticky="ew")
        audio_headings.columnconfigure(1, weight=1)
        self.audio_heading = Label(audio_headings, anchor="w")
        self.audio_heading.grid(row=0, column=1, sticky="w", padx=36)
        self.start_label = Label(audio_headings, width=12)
        self.start_label.grid(row=0, column=3, padx=4)
        self.end_label = Label(audio_headings, width=12)
        self.end_label.grid(row=0, column=4, padx=4)
        self.audio_canvas = Canvas(self.audio_group, highlightthickness=0, height=105)
        self.audio_canvas.grid(row=1, column=0, sticky="nsew")
        self.audio_scrollbar = Scrollbar(self.audio_group, orient="vertical", command=self.audio_canvas.yview)
        self.audio_scrollbar.grid(row=1, column=1, sticky="ns")
        self.audio_canvas.config(yscrollcommand=self.audio_scrollbar.set)
        self.audio_rows_frame = Frame(self.audio_canvas)
        self.audio_rows_window = self.audio_canvas.create_window((0, 0), window=self.audio_rows_frame, anchor="nw")
        self.audio_rows_frame.bind("<Configure>", lambda _event: self.audio_canvas.config(scrollregion=self.audio_canvas.bbox("all")))
        self.audio_canvas.bind("<Configure>", lambda event: self.audio_canvas.itemconfigure(self.audio_rows_window, width=event.width))
        self.add_audio_button = Button(self.audio_group, text="+", width=4, command=self.add_audio_row)
        self.add_audio_button.grid(row=2, column=0, sticky="w", pady=(7, 0))

        self.media_group = LabelFrame(self, padding=8)
        self.media_group.pack(fill="both", expand=True, padx=12, pady=6)
        self.media_group.columnconfigure(0, weight=1)
        self.media_group.rowconfigure(1, weight=1)
        headings = Frame(self.media_group)
        headings.grid(row=0, column=0, sticky="ew")
        headings.columnconfigure(1, weight=1)
        self.media_heading = Label(headings, anchor="w")
        self.media_heading.grid(row=0, column=1, sticky="w", padx=36)
        self.duration_heading = Label(headings)
        self.duration_heading.grid(row=0, column=2, padx=13)
        self.media_canvas = Canvas(self.media_group, highlightthickness=0)
        self.media_canvas.grid(row=1, column=0, sticky="nsew")
        self.media_scrollbar = Scrollbar(self.media_group, orient="vertical", command=self.media_canvas.yview)
        self.media_scrollbar.grid(row=1, column=1, sticky="ns")
        self.media_canvas.config(yscrollcommand=self.media_scrollbar.set)
        self.rows_frame = Frame(self.media_canvas)
        self.rows_window = self.media_canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.rows_frame.bind("<Configure>", self.update_scroll_region)
        self.media_canvas.bind("<Configure>", self.resize_rows)
        row_controls = Frame(self.media_group)
        row_controls.grid(row=2, column=0, sticky="w", pady=(7, 0))
        self.add_button = Button(row_controls, text="+", width=4, command=self.add_row)
        self.add_button.pack(side="left")
        self.fill_button = Button(row_controls, command=self.fill_last)
        self.fill_button.pack(side="left", padx=8)
        self.total_label = Label(self.media_group, anchor="e")
        self.total_label.grid(row=2, column=0, sticky="e", pady=(7, 0))

        self.output_group = LabelFrame(self, padding=10)
        self.output_group.pack(fill="x", padx=12, pady=6)
        self.output_group.columnconfigure(1, weight=1)
        self.size_label = Label(self.output_group)
        self.size_label.grid(row=0, column=0, sticky="w")
        size_frame = Frame(self.output_group)
        size_frame.grid(row=0, column=1, sticky="w", padx=6)
        self.width = StringVar(master=self, value="1080")
        self.height = StringVar(master=self, value="1920")
        self.width_entry = Entry(size_frame, textvariable=self.width, width=7)
        self.width_entry.pack(side="left")
        Label(size_frame, text="×").pack(side="left", padx=6)
        self.height_entry = Entry(size_frame, textvariable=self.height, width=7)
        self.height_entry.pack(side="left")
        self.output_label = Label(self.output_group)
        self.output_label.grid(row=1, column=0, pady=(9, 0))
        self.output_path = StringVar(master=self)
        self.output_entry = Entry(self.output_group, textvariable=self.output_path, state="readonly")
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=(9, 0))
        self.output_button = Button(self.output_group, command=self.choose_output)
        self.output_button.grid(row=1, column=2, pady=(9, 0))

        controls = Frame(self)
        controls.pack(pady=(4, 2))
        self.preview_button = Button(controls, command=self.preview)
        self.preview_button.pack(side="left", padx=6)
        self.export_button = Button(controls, command=self.export)
        self.export_button.pack(side="left", padx=6)
        self.progress = Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=24, pady=(4, 2))
        self.status_label = Label(self)
        self.status_label.pack(pady=(2, 8))

        self.add_audio_row()
        self.add_row()
        self.set_language()

    def set_language(self):
        t = self.language.text
        self.audio_group.config(text=t("clip_audio_group"))
        self.audio_heading.config(text=t("clip_audio_file"))
        self.start_label.config(text=t("clip_audio_start"))
        self.end_label.config(text=t("clip_audio_end"))
        self.media_group.config(text=t("clip_media_group"))
        self.media_heading.config(text=t("clip_media_file"))
        self.duration_heading.config(text=t("clip_duration"))
        self.output_group.config(text=t("clip_output_group"))
        self.size_label.config(text=t("clip_size"))
        self.output_label.config(text=t("clip_output_file"))
        self.output_button.config(text=t("browse"))
        self.preview_button.config(text=t("clip_preview"))
        self.export_button.config(text=t("clip_export"))
        self.fill_button.config(text=t("clip_fill_last"))
        for row in self.rows:
            row.set_language()
        for row in self.audio_rows:
            row.set_language()
        self.update_total()
        self.status_label.config(text=t("clip_rendering") if self.rendering else "")

    def update_scroll_region(self, _event=None):
        self.media_canvas.config(scrollregion=self.media_canvas.bbox("all"))

    def resize_rows(self, event):
        self.media_canvas.itemconfigure(self.rows_window, width=event.width)

    def add_row(self):
        if self.rendering:
            return
        row = MediaEditorRow(self.rows_frame, self)
        row.pack(fill="x", pady=2)
        self.rows.append(row)
        row.set_language()
        self.refresh_rows()
        self.rows_frame.update_idletasks()
        self.update_scroll_region()
        self.media_canvas.yview_moveto(1.0)

    def add_audio_row(self):
        if self.rendering:
            return
        row = AudioEditorRow(self.audio_rows_frame, self)
        row.pack(fill="x", pady=2)
        self.audio_rows.append(row)
        row.set_language()
        self.refresh_audio_rows()
        self.audio_canvas.yview_moveto(1.0)

    def remove_audio_row(self, row):
        if self.rendering or len(self.audio_rows) == 1:
            return
        self.audio_rows.remove(row)
        row.destroy()
        self.refresh_audio_rows()

    def refresh_audio_rows(self):
        for number, row in enumerate(self.audio_rows, 1):
            row.number_label.config(text=f"{number}.")
            row.remove_button.config(state="disabled" if len(self.audio_rows) == 1 else "normal")
        self.update_total()

    def remove_row(self, row):
        if self.rendering or len(self.rows) == 1:
            return
        self.rows.remove(row)
        row.destroy()
        self.refresh_rows()

    def refresh_rows(self):
        for number, row in enumerate(self.rows, start=1):
            row.number_label.config(text=f"{number}.")
            row.remove_button.config(state="disabled" if len(self.rows) == 1 else "normal")
        self.update_total()

    def choose_audio(self, row):
        filename = askopenfilename(initialdir=self.config_data.default_path,
                                   filetypes=[(self.language.text("clip_audio_file"),
                                               "*.mp3 *.wav *.flac *.aac *.ogg *.wma *.mp4 *.mov *.avi *.wmv *.flv")],
                                   parent=self)
        if not filename:
            return
        try:
            duration = media_duration(filename, self.config_data.ffmpeg)
        except Exception as error:
            messagebox.showerror(self.language.text("open_failed"), self.language.error(error), parent=self)
            return
        row.path.set(filename)
        row.start.set(format_clock(0))
        row.end.set(format_clock(duration))

    def choose_media(self, row):
        filename = askopenfilename(initialdir=self.config_data.default_path,
                                   filetypes=[(self.language.text("clip_media_file"),
                                               "*.jpg *.jpeg *.png *.gif *.webp *.mp4 *.mov *.avi *.wmv *.flv")],
                                   parent=self)
        if not filename:
            return
        duration = None
        if Path(filename).suffix.lower() in {".mp4", ".mov", ".avi", ".wmv", ".flv"}:
            try:
                duration = media_duration(filename, self.config_data.ffmpeg)
            except Exception as error:
                messagebox.showerror(self.language.text("open_failed"), self.language.error(error), parent=self)
                return
        row.path.set(filename)
        if duration is not None:
            row.seconds.set(format_clock(duration))

    def choose_output(self):
        filename = asksaveasfilename(initialdir=self.config_data.default_path, defaultextension=".mp4",
                                     filetypes=[("MP4", "*.mp4")], parent=self)
        if filename:
            self.output_path.set(filename)

    def update_total(self):
        if not hasattr(self, "total_label"):
            return
        try:
            total = sum(parse_clock(row.seconds.get()) for row in self.rows)
            audio = sum(parse_clock(row.end.get()) - parse_clock(row.start.get()) for row in self.audio_rows)
            if not isfinite(total) or not isfinite(audio) or audio <= 0:
                raise ValueError("Invalid duration")
            self.total_label.config(text=self.language.text("clip_total").format(media=format_clock(total),
                                                                                 audio=format_clock(audio)),
                                    foreground="#15803d" if abs(total - audio) <= 0.002 else "#b91c1c")
        except ValueError:
            self.total_label.config(text=self.language.text("clip_total").format(media="—", audio="—"),
                                    foreground="black")

    def fill_last(self):
        try:
            remaining = (sum(parse_clock(row.end.get()) - parse_clock(row.start.get())
                             for row in self.audio_rows)
                         - sum(parse_clock(row.seconds.get()) for row in self.rows[:-1]))
            if not isfinite(remaining) or remaining <= 0:
                raise ValueError("The soundtrack must extend past the preceding media.")
        except ValueError as error:
            messagebox.showerror(self.language.text("clip_invalid"), self.language.error(error), parent=self)
            return
        self.rows[-1].seconds.set(format_clock(remaining))

    def collect_project(self, output):
        try:
            size = (int(self.width.get()), int(self.height.get()))
        except ValueError as error:
            raise ValueError("Enter valid numeric values.") from error
        rows = [MediaRow(Path(row.path.get()), parse_clock(row.seconds.get())) for row in self.rows]
        audio_rows = [AudioRow(Path(row.path.get()), parse_clock(row.start.get()), parse_clock(row.end.get()))
                      for row in self.audio_rows]
        validate_project(audio_rows, rows, size, output, self.config_data.ffmpeg)
        return audio_rows, rows, size, output, self.config_data.ffmpeg

    def preview(self):
        if self.rendering:
            return
        temporary = TemporaryDirectory(prefix="clipmaker-preview-")
        path = Path(temporary.name) / "preview.mp4"
        try:
            project = self.collect_project(path)
            audio_rows, media_rows, size, _, ffmpeg = project
            sources = [row.path for row in [*audio_rows, *media_rows]]
            key = json.dumps({
                "audio": [(str(row.path), row.start, row.end) for row in audio_rows],
                "media": [(str(row.path), row.seconds) for row in media_rows],
                "size": size,
                "files": [(source, Path(source).stat().st_mtime_ns, Path(source).stat().st_size)
                          for source in sources],
            }, sort_keys=True, default=str)
        except Exception as error:
            temporary.cleanup()
            messagebox.showerror(self.language.text("clip_invalid"), self.language.error(error), parent=self)
            return
        if self.preview_key == key and self.preview_path is not None and self.preview_path.is_file():
            temporary.cleanup()
            self.play_preview()
            return
        self.stop_preview_player()
        self.clear_preview()
        self.preview_temp = temporary
        self.preview_path = path
        project = (audio_rows, media_rows, preview_size(size), path, ffmpeg)
        self.start_render(project, "preview", key)

    def export(self):
        if self.rendering:
            return
        if not self.output_path.get():
            self.choose_output()
        if not self.output_path.get():
            return
        try:
            project = self.collect_project(self.output_path.get())
        except Exception as error:
            messagebox.showerror(self.language.text("clip_invalid"), self.language.error(error), parent=self)
            return
        self.stop_preview_player()
        self.start_render(project, "export", None)

    def start_render(self, project, mode, key):
        self.rendering = True
        self.render_mode = mode
        self.set_busy(True)
        self.progress.start(10)
        self.status_label.config(text=self.language.text("clip_rendering"))

        def worker():
            try:
                render_project(*project)
            except Exception as error:
                self.render_updates.put((mode, key, str(error)))
            else:
                self.render_updates.put((mode, key, None))

        Thread(target=worker, daemon=True).start()
        self.render_poll = self.after(100, self.poll_render)

    def poll_render(self):
        self.render_poll = None
        try:
            mode, key, error = self.render_updates.get_nowait()
        except Empty:
            self.render_poll = self.after(100, self.poll_render)
            return
        self.rendering = False
        self.render_mode = None
        self.progress.stop()
        self.set_busy(False)
        self.status_label.config(text="")
        if error:
            if mode == "preview":
                self.clear_preview()
            messagebox.showerror(self.language.text("clip_render_failed"), error, parent=self)
        elif mode == "preview":
            self.preview_key = key
            if self.winfo_ismapped():
                self.play_preview()
        else:
            messagebox.showinfo(self.language.text("clip_export"), self.language.text("file_saved"), parent=self)

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for widget in (self.add_audio_button, self.add_button,
                       self.fill_button,
                       self.width_entry, self.height_entry, self.output_button,
                       self.preview_button, self.export_button):
            widget.config(state=state)
        for row in self.rows:
            row.choose_button.config(state=state)
            row.seconds_entry.config(state=state)
            row.remove_button.config(state="disabled" if busy or len(self.rows) == 1 else "normal")
        for row in self.audio_rows:
            row.choose_button.config(state=state)
            row.start_entry.config(state=state)
            row.end_entry.config(state=state)
            row.remove_button.config(state="disabled" if busy or len(self.audio_rows) == 1 else "normal")

    def play_preview(self):
        self.stop_preview_player()
        try:
            self.preview_player = subprocess.Popen(
                [ffplay_executable(self.config_data.ffmpeg), "-autoexit", "-loglevel", "error",
                 "-window_title", self.language.text("clip_preview"), str(self.preview_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            player = self.preview_player
            self.player_poll = self.after(200, lambda: self.poll_player(player))
        except OSError as error:
            messagebox.showerror(self.language.text("preview_failed"), self.language.error(error), parent=self)

    def poll_player(self, player):
        if self.preview_player is not player:
            return
        self.player_poll = None
        result = player.poll()
        if result is None:
            self.player_poll = self.after(200, lambda: self.poll_player(player))
        else:
            self.preview_player = None
            if result != 0:
                messagebox.showerror(self.language.text("preview_failed"),
                                     self.language.text("clip_preview_failed"), parent=self)

    def stop_preview_player(self):
        if self.player_poll is not None:
            self.after_cancel(self.player_poll)
            self.player_poll = None
        player = self.preview_player
        self.preview_player = None
        if player is not None and player.poll() is None:
            try:
                player.terminate()
                player.wait(timeout=2)
            except subprocess.TimeoutExpired:
                player.kill()
                player.wait()
            except OSError:
                pass

    def clear_preview(self):
        self.preview_key = None
        self.preview_path = None
        if self.preview_temp is not None:
            self.preview_temp.cleanup()
            self.preview_temp = None

    def destroy(self):
        if self.render_poll is not None:
            self.after_cancel(self.render_poll)
            self.render_poll = None
        self.stop_preview_player()
        self.clear_preview()
        super().destroy()
