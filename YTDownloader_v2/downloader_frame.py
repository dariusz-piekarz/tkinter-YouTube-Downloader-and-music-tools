from os.path import join, abspath
from os import remove, rename, pardir
from tkinter import Frame, Label, Button, Entry, END, StringVar
from downloader_core import download_audio_from_youtube
from tkinter.ttk import Combobox
from tkinter.filedialog import asksaveasfilename
from Config import Config
from menu import RightClicker
import subprocess
from loguru import logger


class Downloader(Frame):
    directory = str()
    name = str()
    font = 'Arial 12'
    url = str()
    config = Config(r"config.yaml")

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.pack(fill='both', expand=True, anchor="center")
        self.labels()
        self.entries()
        self.button()
        self.format_choice()

    def labels(self):
        self.space = Label(self, text="     ", font=self.font)
        self.space.grid(row=1, column=1, sticky='ew')
        self.space1 = Label(self, text="               ", font=self.font)
        self.space1.grid(row=1, column=3, sticky='ew')
        self.title = Label(self, text="YouTube downloader", font=f"{self.font} bold")
        self.title.grid(row=1, column=2, sticky='ew')
        self.url_label = Label(self, text="URL address of the YT Video ", font=self.font)
        self.url_label.grid(row=3, column=2, sticky='ew')

    def button(self):
        button = Button(self, text="Download", command=self.action, width=12)
        button.grid(row=4, column=2, columnspan=1, sticky="w")
        button = Button(self, text="Clear", command=self.clear, width=14)
        button.grid(row=4, column=2, columnspan=1, sticky="e")

    def action(self):
        url = self.url.get()
        self.file = download_audio_from_youtube(url, self.combo.get())
        self.save()

    def clear(self):
        self.url.delete(0, END)

    def entries(self):
        self.url = Entry(self, self.url, font=self.font)
        self.url.bind('<Button-3>', RightClicker)
        self.url.grid(row=3, columnspan=2, column=3, sticky='w')

    def format_choice(self):
        mp3 = StringVar(self).set('mp3')
        self.combo = Combobox(self, values=['mp3', 'mp4'], textvariable=mp3, width=4)
        self.combo.current(0)
        self.combo.grid(row=3, column=5, sticky='w')

    @logger.catch
    def save(self):
        audio_params = {
                        "bitrate": self.config.YTDownloader.bitrate,
                        "sample_rate": self.config.YTDownloader.sample_rate,
                        "channels": self.config.YTDownloader.channels
                        }
        if self.combo.get() == 'mp3':
            a = asksaveasfilename(filetypes=(("MPEG Layer 3", "*.mp3"), ("All Files", "*.*")),
                                      defaultextension='.mp3',
                                      title="Window-2", initialdir=self.config.YTDownloader.default_path,
                                      initialfile=self.file.title)
        elif self.combo.get() == 'mp4':
                a = asksaveasfilename(filetypes=(("MP4", "*.mp4"), ("All Files", "*.*")), defaultextension='.mp4',
                                      title="Window-2", initialdir=self.config.YTDownloader.default_path,
                                      initialfile=self.file.title)
        new_name = a.split("/")[-1]
        a = abspath(join(a, pardir))
        file = self.file.download(output_path=a)

        if audio_params and self.combo.get() == 'mp3':
            ffmpeg_command = [self.config.YTDownloader.ffmpeg, "-i", file, file.replace(".mp4", ".mp3")]
            for key, value in audio_params.items():
                ffmpeg_command.extend([f"-{key}", str(value)])
            subprocess.run(ffmpeg_command)
            remove(file)

        if self.combo.get() == 'mp4':
            rename(file, join(a, new_name))
