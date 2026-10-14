from pathlib import Path
from threading import Thread
from tkinter import Button, Entry, Frame, Label, END, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename

from Config import Config
from shrink_core import media_duration, parse_time, trim_media


class Shrinker(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.config_data = Config()
        self.source = None
        self.duration = 0.0
        self.entries = []
        self.columnconfigure(1, weight=1)
        self.source_label = Label(self, text="No file selected")
        self.source_label.grid(row=0, column=0, columnspan=7, pady=12)
        Button(self, text="Open MP3 / MP4", command=self.open_file).grid(row=1, column=0, padx=12)
        for row, label in ((2, "Start"), (3, "End")):
            Label(self, text=label).grid(row=row, column=0, pady=8)
            group = []
            for index, width in enumerate((4, 3, 4)):
                entry = Entry(self, width=width)
                entry.grid(row=row, column=index * 2 + 1)
                entry.insert(0, "0")
                group.append(entry)
                if index < 2:
                    Label(self, text=":" if index == 0 else ".").grid(row=row, column=index * 2 + 2)
            self.entries.append(group)
        self.extract_button = Button(self, text="Extract", command=self.extract)
        self.extract_button.grid(row=4, column=0, columnspan=7, pady=16)

    def open_file(self):
        filename = askopenfilename(initialdir=self.config_data.default_path, filetypes=[("Media", "*.mp3 *.mp4")])
        if not filename:
            return
        try:
            duration = media_duration(filename, self.config_data.ffmpeg)
        except Exception as error:
            messagebox.showerror("Open failed", str(error))
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
            messagebox.showerror("Extract", "Open a file first.")
            return
        try:
            start, end = (parse_time(*(entry.get() for entry in group)) for group in self.entries)
            if end <= start or end > self.duration + 0.01:
                raise ValueError("Choose an end time after the start and within the file.")
        except ValueError as error:
            messagebox.showerror("Invalid time", str(error))
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
            messagebox.showerror("Extract failed", error)
        else:
            messagebox.showinfo("Extract", "File saved successfully.")
