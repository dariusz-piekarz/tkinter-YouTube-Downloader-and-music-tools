from io import BytesIO
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from time import monotonic
from tkinter import Button, Canvas, Entry, Frame, Label, END, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename

from PIL import Image, ImageTk

from Config import Config
from shrink_core import media_duration, parse_time, preview_media, trim_media, waveform_image


class Shrinker(Frame):
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language
        self.config_data = Config()
        self.source = None
        self.duration = 0.0
        self.entries = []
        self.selection = (0.0, 0.0)
        self.waveform = None
        self.waveform_photo = None
        self.waveform_photo_size = None
        self.waveform_loading = False
        self.waveform_error = False
        self.waveform_updates = Queue()
        self.preview_request = 0
        self.preview_polling = False
        self.drag_marker = None
        self.playback_process = None
        self.playback_after = None
        self.playback_started_at = 0.0
        self.playback_start = 0.0
        self.playback_end = 0.0
        self.playhead = None
        self.columnconfigure(1, weight=1)
        self.source_label = Label(self)
        self.source_label.grid(row=0, column=0, columnspan=2, pady=12)
        self.open_button = Button(self, command=self.open_file)
        self.open_button.grid(row=1, column=0, padx=12)
        self.time_labels = []
        for row in (2, 3):
            label = Label(self)
            label.grid(row=row, column=0, padx=12, pady=8, sticky="e")
            self.time_labels.append(label)
            time_frame = Frame(self)
            time_frame.grid(row=row, column=1, sticky="w")
            group = []
            for index, width in enumerate((4, 3, 4)):
                entry = Entry(time_frame, width=width, justify="center")
                entry.pack(side="left")
                entry.insert(0, "0")
                entry.bind("<KeyRelease>", self.time_changed)
                group.append(entry)
                if index < 2:
                    Label(time_frame, text=":" if index == 0 else ".").pack(side="left")
            self.entries.append(group)
        self.waveform_canvas = Canvas(self, height=150, background="#111827", highlightthickness=0, cursor="crosshair")
        self.waveform_canvas.grid(row=4, column=0, columnspan=2, padx=12, sticky="ew")
        self.waveform_canvas.bind("<Configure>", self.draw_waveform)
        self.waveform_canvas.bind("<Button-1>", self.start_drag)
        self.waveform_canvas.bind("<B1-Motion>", self.drag)
        self.waveform_canvas.bind("<ButtonRelease-1>", self.stop_drag)
        playback_frame = Frame(self)
        playback_frame.grid(row=5, column=0, columnspan=2, pady=(8, 0))
        self.play_button = Button(playback_frame, command=self.play_selection, state="disabled")
        self.play_button.pack(side="left", padx=6)
        self.stop_button = Button(playback_frame, command=self.stop_playback, state="disabled")
        self.stop_button.pack(side="left", padx=6)
        self.waveform_label = Label(self)
        self.waveform_label.grid(row=6, column=0, columnspan=2, pady=(4, 0))
        self.extract_button = Button(self, command=self.extract)
        self.extract_button.grid(row=7, column=0, columnspan=2, pady=12)
        self.set_language()

    def set_language(self):
        t = self.language.text
        if self.source is None:
            self.source_label.config(text=t("no_file"))
        self.open_button.config(text=t("open_media"))
        for label, key in zip(self.time_labels, ("start", "end")):
            label.config(text=t(key))
        if self.source is None:
            waveform_text = t("waveform_empty")
        elif self.waveform_loading:
            waveform_text = t("waveform_loading")
        elif self.waveform_error:
            waveform_text = t("waveform_unavailable")
        else:
            waveform_text = t("waveform_hint")
        self.waveform_label.config(text=waveform_text)
        self.play_button.config(text=t("play_selection"))
        self.stop_button.config(text=t("stop_preview"))
        self.extract_button.config(text=t("extract"))

    def draw_waveform(self, _event=None):
        canvas = self.waveform_canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 2 or height < 2:
            return
        canvas.delete("all")
        if self.waveform is not None:
            if self.waveform_photo_size != (width, height):
                resized = self.waveform.resize((width, height), Image.Resampling.BILINEAR)
                self.waveform_photo = ImageTk.PhotoImage(resized)
                self.waveform_photo_size = (width, height)
            canvas.create_image(0, 0, image=self.waveform_photo, anchor="nw")
        else:
            canvas.create_line(0, height // 2, width, height // 2, fill="#475569")
        if self.duration > 0:
            start, end = self.selection
            left = round(width * start / self.duration)
            right = round(width * end / self.duration)
            canvas.create_rectangle(0, 0, left, height, fill="#0f172a", stipple="gray50", outline="")
            canvas.create_rectangle(right, 0, width, height, fill="#0f172a", stipple="gray50", outline="")
            canvas.create_line(left, 0, left, height, fill="#22c55e", width=2)
            canvas.create_line(right, 0, right, height, fill="#ef4444", width=2)
            if self.playhead is not None:
                position = round(width * self.playhead / self.duration)
                canvas.create_line(position, 0, position, height, fill="#facc15", width=2)

    def time_changed(self, _event=None):
        self.stop_playback()
        if self.duration <= 0:
            return
        try:
            start, end = (parse_time(*(entry.get() for entry in group)) for group in self.entries)
        except ValueError:
            return
        if 0 <= start <= end <= self.duration + 0.01:
            self.selection = (min(start, self.duration), min(end, self.duration))
            self.draw_waveform()

    def set_entry_time(self, group_index, seconds):
        total_ms = round(seconds * 1000)
        minutes, remainder = divmod(total_ms, 60_000)
        whole_seconds, milliseconds = divmod(remainder, 1000)
        for entry, value in zip(self.entries[group_index], (minutes, whole_seconds, milliseconds)):
            entry.delete(0, END)
            entry.insert(0, str(value))

    def start_drag(self, event):
        if self.duration <= 0:
            return
        width = max(self.waveform_canvas.winfo_width(), 1)
        position = min(max(event.x / width, 0), 1) * self.duration
        self.drag_marker = 0 if abs(position - self.selection[0]) <= abs(position - self.selection[1]) else 1
        self.drag(event)

    def drag(self, event):
        if self.drag_marker is None or self.duration <= 0:
            return
        self.stop_playback()
        width = max(self.waveform_canvas.winfo_width(), 1)
        position = min(max(event.x / width, 0), 1) * self.duration
        start, end = self.selection
        if self.drag_marker == 0:
            start = min(position, end)
        else:
            end = max(position, start)
        self.selection = (start, end)
        self.set_entry_time(self.drag_marker, self.selection[self.drag_marker])
        self.draw_waveform()

    def stop_drag(self, _event=None):
        self.drag_marker = None

    def open_file(self):
        filename = askopenfilename(initialdir=self.config_data.default_path,
                                   filetypes=[(self.language.text("media_files"), "*.mp3 *.mp4")])
        if not filename:
            return
        try:
            duration = media_duration(filename, self.config_data.ffmpeg)
        except Exception as error:
            messagebox.showerror(self.language.text("open_failed"), self.language.error(error))
            return
        self.stop_playback()
        self.source = Path(filename)
        self.duration = duration
        self.source_label.config(text=self.source.name)
        self.selection = (0.0, duration)
        self.play_button.config(state="normal")
        self.set_entry_time(0, 0)
        self.set_entry_time(1, duration)
        self.waveform = None
        self.waveform_photo = None
        self.waveform_photo_size = None
        self.waveform_loading = True
        self.waveform_error = False
        self.preview_request += 1
        request = self.preview_request
        self.set_language()
        self.draw_waveform()

        def render():
            try:
                data = waveform_image(filename, self.config_data.ffmpeg)
            except Exception:
                self.waveform_updates.put((request, None))
            else:
                self.waveform_updates.put((request, data))

        Thread(target=render, daemon=True).start()
        if not self.preview_polling:
            self.preview_polling = True
            self.after(100, self.poll_waveform)

    def poll_waveform(self):
        try:
            while True:
                request, data = self.waveform_updates.get_nowait()
                if request != self.preview_request:
                    continue
                self.waveform_loading = False
                try:
                    self.waveform = Image.open(BytesIO(data)).convert("RGBA") if data else None
                except (OSError, ValueError):
                    self.waveform = None
                self.waveform_error = self.waveform is None
                self.waveform_photo = None
                self.waveform_photo_size = None
                self.set_language()
                self.draw_waveform()
        except Empty:
            pass
        if self.waveform_loading:
            self.after(100, self.poll_waveform)
        else:
            self.preview_polling = False

    def play_selection(self):
        if self.source is None:
            return
        try:
            start, end = (parse_time(*(entry.get() for entry in group)) for group in self.entries)
            if end <= start or end > self.duration + 0.01:
                raise ValueError("Choose an end time after the start and within the file.")
            end = min(end, self.duration)
            self.stop_playback()
            process = preview_media(self.source, start, end, self.config_data.ffmpeg)
        except (OSError, ValueError) as error:
            messagebox.showerror(self.language.text("preview_failed"), self.language.error(error))
            return
        self.selection = (start, end)
        self.playback_process = process
        self.playback_started_at = monotonic()
        self.playback_start = start
        self.playback_end = end
        self.playhead = start
        self.play_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.draw_waveform()
        self.playback_after = self.after(100, lambda: self.poll_playback(process))

    def poll_playback(self, process):
        if self.playback_process is not process:
            return
        self.playback_after = None
        result = process.poll()
        if result is not None:
            self.stop_playback()
            if result != 0:
                messagebox.showerror(self.language.text("preview_failed"),
                                     self.language.text("preview_could_not_play"))
            return
        self.playhead = min(self.playback_end,
                            self.playback_start + monotonic() - self.playback_started_at)
        self.draw_waveform()
        self.playback_after = self.after(100, lambda: self.poll_playback(process))

    def stop_playback(self):
        if self.playback_after is not None:
            self.after_cancel(self.playback_after)
            self.playback_after = None
        process = self.playback_process
        self.playback_process = None
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
            else:
                Thread(target=process.wait, daemon=True).start()
        self.playhead = None
        self.play_button.config(state="normal" if self.source is not None else "disabled")
        self.stop_button.config(state="disabled")
        self.draw_waveform()

    def destroy(self):
        self.stop_playback()
        super().destroy()

    def extract(self):
        if self.source is None:
            messagebox.showerror(self.language.text("extract"), self.language.text("open_first"))
            return
        try:
            start, end = (parse_time(*(entry.get() for entry in group)) for group in self.entries)
            if end <= start or end > self.duration + 0.01:
                raise ValueError("Choose an end time after the start and within the file.")
        except ValueError as error:
            messagebox.showerror(self.language.text("invalid_time"), self.language.error(error))
            return
        suffix = self.source.suffix.lower()
        filename = asksaveasfilename(initialdir=self.config_data.default_path, defaultextension=suffix,
                                     filetypes=[(suffix.upper(), f"*{suffix}")])
        if not filename:
            return
        self.stop_playback()
        self.extract_button.config(state="disabled")

        def worker():
            try:
                trim_media(self.source, filename, start, end, self.config_data.ffmpeg)
            except Exception as error:
                self.after(0, lambda message=str(error): self.finish(message))
            else:
                self.after(0, lambda: self.finish(None))

        Thread(target=worker, daemon=True).start()

    def finish(self, error):
        self.extract_button.config(state="normal")
        if error:
            messagebox.showerror(self.language.text("extract_failed"), self.language.error(error))
        else:
            messagebox.showinfo(self.language.text("extract"), self.language.text("file_saved"))
