from pathlib import Path
from threading import Thread
from tkinter import Button, Entry, Frame, Label, END, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename

from Config import Config
from shrink_core import media_duration, parse_time, trim_media


class Shrinker(Frame):
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language
        self.config_data = Config()
        self.source = None
        self.duration = 0.0
        self.entries = []
        self.columnconfigure(1, weight=1)
        self.source_label = Label(self)
        self.source_label.grid(row=0, column=0, columnspan=7, pady=12)
        self.open_button = Button(self, command=self.open_file)
        self.open_button.grid(row=1, column=0, padx=12)
        self.time_labels = []
        for row in (2, 3):
            label = Label(self)
            label.grid(row=row, column=0, pady=8)
            self.time_labels.append(label)
            group = []
            for index, width in enumerate((4, 3, 4)):
                entry = Entry(self, width=width)
                entry.grid(row=row, column=index * 2 + 1)
                entry.insert(0, "0")
                group.append(entry)
                if index < 2:
                    Label(self, text=":" if index == 0 else ".").grid(row=row, column=index * 2 + 2)
            self.entries.append(group)
        self.extract_button = Button(self, command=self.extract)
        self.extract_button.grid(row=4, column=0, columnspan=7, pady=16)
        self.set_language()

    def set_language(self):
        t = self.language.text
        if self.source is None:
            self.source_label.config(text=t("no_file"))
        self.open_button.config(text=t("open_media"))
        for label, key in zip(self.time_labels, ("start", "end")):
            label.config(text=t(key))
        self.extract_button.config(text=t("extract"))

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
        self.source = Path(filename)
        self.duration = duration
        self.source_label.config(text=self.source.name)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        milliseconds = int(round((duration - int(duration)) * 1000))
        if milliseconds == 1000:
            seconds += 1
            milliseconds = 0
        if seconds == 60:
            minutes += 1
            seconds = 0
        for entry, value in zip(self.entries[1], (minutes, seconds, milliseconds)):
            entry.delete(0, END)
            entry.insert(0, str(value))

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
