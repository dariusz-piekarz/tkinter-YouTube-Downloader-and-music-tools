from pathlib import Path
from threading import Thread
from tkinter import Button, Entry, Frame, Label, StringVar, messagebox
from tkinter.filedialog import asksaveasfilename
from tkinter.ttk import Combobox

from Config import Config
from downloader_core import download_media
from menu import RightClicker


class Downloader(Frame):
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language
        self.config_data = Config()
        self.columnconfigure(1, weight=1)
        self.title_label = Label(self, font="Arial 12 bold")
        self.title_label.grid(row=0, column=0, columnspan=3, pady=20)
        self.url_label = Label(self)
        self.url_label.grid(row=1, column=0, padx=12)
        self.url = Entry(self, width=55)
        self.url.grid(row=1, column=1, sticky="ew")
        self.url.bind("<Button-3>", lambda event: RightClicker(event, self.language))
        self.media_format = StringVar(value="mp3")
        Combobox(self, textvariable=self.media_format, values=("mp3", "mp4"), state="readonly", width=5).grid(row=1, column=2, padx=12)
        self.download_button = Button(self, command=self.action)
        self.download_button.grid(row=2, column=1, pady=15)
        self.downloading = False
        self.set_language()

    def set_language(self):
        t = self.language.text
        self.title_label.config(text=t("downloader_title"))
        self.url_label.config(text=t("video_url"))
        self.download_button.config(text=t("downloading" if self.downloading else "download"))

    def action(self):
        url = self.url.get().strip()
        if not url:
            messagebox.showerror(self.language.text("download"), self.language.text("enter_url"))
            return
        media_format = self.media_format.get()
        filename = asksaveasfilename(
            initialdir=self.config_data.default_path,
            defaultextension=f".{media_format}",
            filetypes=[(media_format.upper(), f"*.{media_format}")],
            title=self.language.text("save_download"),
        )
        if not filename:
            return
        destination = Path(filename)
        self.downloading = True
        self.download_button.config(state="disabled")
        self.set_language()

        def worker():
            try:
                download_media(url, destination, media_format, self.config_data.ffmpeg, self.config_data.bitrate)
            except Exception as error:
                self.after(0, lambda message=str(error): self.finish(message))
            else:
                self.after(0, lambda: self.finish(None))

        Thread(target=worker, daemon=True).start()

    def finish(self, error):
        self.downloading = False
        self.download_button.config(state="normal")
        self.set_language()
        if error:
            messagebox.showerror(self.language.text("download_failed"), self.language.error(error))
        else:
            messagebox.showinfo(self.language.text("download"), self.language.text("file_saved"))
