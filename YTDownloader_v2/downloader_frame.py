from pathlib import Path
from queue import Empty, Queue
import re
from threading import Event, Thread
from tkinter import Button, Entry, Frame, Label, StringVar, messagebox
from tkinter.filedialog import asksaveasfilename
from tkinter.ttk import Combobox, Progressbar

from Config import Config
from downloader_core import DownloadCancelled, download_media, get_title
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
        Combobox(self,
                 textvariable=self.media_format, 
                 values=("mp3", "mp4"),
                 state="readonly", width=5
                 ).grid(row=1, column=2, padx=12)
        self.progress_bar = Progressbar(self, maximum=100)
        self.progress_bar.grid(row=2, column=1, sticky="ew", pady=15)
        controls = Frame(self)
        controls.grid(row=3, column=1, pady=15)
        self.download_button = Button(controls, command=self.action)
        self.download_button.pack(side="left", padx=5)
        self.cancel_button = Button(controls, command=self.cancel_download, state="disabled")
        self.cancel_button.pack(side="left", padx=5)

        self.progress_label = Label(self)
        self.progress_label.grid(row=4, column=0, columnspan=3, pady=(4, 0))
        self.progress_updates = Queue()
        self.progress_stage = None
        self.progress_percent = None
        self.downloading = False
        self.cancel_event = None
        self.request_id = 0
        self.polling = False
        self.set_language()

    def set_language(self):
        t = self.language.text
        self.title_label.config(text=t("downloader_title"))
        self.url_label.config(text=t("video_url"))
        self.download_button.config(text=t("downloading" if self.downloading else "download"))
        self.cancel_button.config(text=t("cancel"))
        if self.progress_stage == "title":
            self.progress_label.config(text=t("fetching_title"))
        elif self.progress_stage == "processing":
            self.progress_label.config(text=t("processing_download"))
        elif self.progress_stage == "downloading":
            if self.progress_percent is None:
                self.progress_label.config(text=t("downloading"))
            else:
                self.progress_label.config(text=t("download_progress").format(percent=round(self.progress_percent)))
        elif self.progress_stage == "canceling":
            self.progress_label.config(text=t("canceling"))
        elif self.progress_stage == "cancelled":
            self.progress_label.config(text=t("download_cancelled"))
        else:
            self.progress_label.config(text="")

    def show_progress(self, stage, percent=None):
        self.progress_stage = stage
        self.progress_percent = percent
        if stage in {"title", "downloading", "processing", "canceling"} and percent is None:
            if str(self.progress_bar.cget("mode")) != "indeterminate":
                self.progress_bar.configure(mode="indeterminate", value=0)
                self.progress_bar.start(12)
        else:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate", value=percent or 0)
        self.set_language()

    def action(self):
        if self.downloading:
            return
        url = self.url.get().strip()
        if not url:
            messagebox.showerror(self.language.text("download"), self.language.text("enter_url"))
            return
        media_format = self.media_format.get()
        self.request_id += 1
        request_id = self.request_id
        self.cancel_event = Event()
        self.downloading = True
        self.download_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.show_progress("title")
        Thread(target=self.fetch_title, args=(request_id, url, media_format), daemon=True).start()
        if not self.polling:
            self.polling = True
            self.after(100, self.poll_progress)

    def fetch_title(self, request_id, url, media_format):
        try:
            title = get_title(url, self.config_data.ffmpeg)
        except Exception as error:
            self.progress_updates.put((request_id, "error", str(error)))
        else:
            safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title or "video").rstrip(" .")[:150] or "video"
            self.progress_updates.put((request_id, "title", (url, media_format, safe_title)))

    def choose_destination(self, request_id, url, media_format, title):
        filename = asksaveasfilename(
            initialfile=f"{title}.{media_format}",
            initialdir=self.config_data.default_path,
            defaultextension=f".{media_format}",
            filetypes=[(media_format.upper(), f"*.{media_format}")],
            title=self.language.text("save_download"),
        )
        if not filename:
            self.reset_progress()
            return
        destination = Path(filename)
        self.show_progress("downloading")
        cancel_event = self.cancel_event

        def worker():
            try:
                download_media(url, destination, media_format, self.config_data.ffmpeg,
                               self.config_data.bitrate,
                               progress=lambda stage, percent: self.progress_updates.put((request_id, "progress", (stage, percent))),
                               cancel=cancel_event)
            except DownloadCancelled:
                self.progress_updates.put((request_id, "cancelled", None))
            except Exception as error:
                self.progress_updates.put((request_id, "error", str(error)))
            else:
                self.progress_updates.put((request_id, "done", None))

        Thread(target=worker, daemon=True).start()

    def cancel_download(self):
        if not self.downloading or self.cancel_event is None:
            return
        self.cancel_event.set()
        self.cancel_button.config(state="disabled")
        if self.progress_stage == "title":
            self.reset_progress()
            self.show_progress("cancelled")
        else:
            self.show_progress("canceling")

    def poll_progress(self):
        try:
            while True:
                request_id, kind, value = self.progress_updates.get_nowait()
                if request_id != self.request_id:
                    continue
                if kind == "title":
                    self.choose_destination(request_id, *value)
                elif kind == "progress":
                    if not self.cancel_event.is_set():
                        self.show_progress(*value)
                elif kind == "error":
                    if self.cancel_event.is_set():
                        self.finish(cancelled=True)
                    else:
                        self.finish(value)
                elif kind == "cancelled":
                    self.finish(cancelled=True)
                elif kind == "done":
                    self.finish(None)
        except Empty:
            pass
        if self.downloading:
            self.after(100, self.poll_progress)
        else:
            self.polling = False

    def reset_progress(self):
        self.request_id += 1
        self.downloading = False
        self.cancel_event = None
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.show_progress(None)

    def finish(self, error=None, cancelled=False):
        self.reset_progress()
        if cancelled:
            self.show_progress("cancelled")
            return
        if error:
            messagebox.showerror(self.language.text("download_failed"), self.language.error(error))
        else:
            messagebox.showinfo(self.language.text("download"), self.language.text("file_saved"))
