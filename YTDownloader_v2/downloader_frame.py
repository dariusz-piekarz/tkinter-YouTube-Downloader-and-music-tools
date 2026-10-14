from pathlib import Path
from threading import Thread
from tkinter import Button, Entry, Frame, Label, StringVar, messagebox
from tkinter.filedialog import asksaveasfilename
from tkinter.ttk import Combobox

from Config import Config
from downloader_core import download_media
from menu import RightClicker


class Downloader(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.config_data = Config()
        self.columnconfigure(1, weight=1)
        Label(self, text="YouTube downloader", font="Arial 12 bold").grid(row=0, column=0, columnspan=3, pady=20)
        Label(self, text="Video URL").grid(row=1, column=0, padx=12)
        self.url = Entry(self, width=55)
        self.url.grid(row=1, column=1, sticky="ew")
        self.url.bind("<Button-3>", RightClicker)
        self.media_format = StringVar(value="mp3")
        Combobox(self, textvariable=self.media_format, values=("mp3", "mp4"), state="readonly", width=5).grid(row=1, column=2, padx=12)
        self.download_button = Button(self, text="Download", command=self.action)
        self.download_button.grid(row=2, column=1, pady=15)

    def action(self):
        url = self.url.get().strip()
        if not url:
            messagebox.showerror("Download", "Enter a video URL.")
            return
        media_format = self.media_format.get()
        filename = asksaveasfilename(
            initialdir=self.config_data.default_path,
            defaultextension=f".{media_format}",
            filetypes=[(media_format.upper(), f"*.{media_format}")],
            title="Save download",
        )
        if not filename:
            return
        destination = Path(filename)
        self.download_button.config(state="disabled", text="Downloading...")

        def worker():
            try:
                download_media(url, destination, media_format, self.config_data.ffmpeg, self.config_data.bitrate)
            except Exception as error:
                self.after(0, lambda message=str(error): self.finish(message))
            else:
                self.after(0, lambda: self.finish(None))

        Thread(target=worker, daemon=True).start()

    def finish(self, error):
        self.download_button.config(state="normal", text="Download")
        if error:
            messagebox.showerror("Download failed", error)
        else:
            messagebox.showinfo("Download", "File saved successfully.")
