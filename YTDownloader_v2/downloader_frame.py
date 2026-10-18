from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from tkinter import Button, Canvas, Entry, Frame, Label, StringVar, messagebox
from tkinter.filedialog import askdirectory
from tkinter.ttk import Combobox, Progressbar, Scrollbar

from Config import Config
from downloader_core import DownloadCancelled, download_media, expand_urls, unique_destination
from menu import RightClicker


class Downloader(Frame):
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language
        self.config_data = Config()
        self.columnconfigure(1, weight=1)

        self.title_label = Label(self, font="Arial 12 bold")
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(16, 12))

        self.url_label = Label(self)
        self.url_label.grid(row=1, column=0, padx=12, sticky="n")
        self.url_canvas = Canvas(self, height=140, highlightthickness=0)
        self.url_canvas.grid(row=1, column=1, sticky="ew")
        self.url_rows_frame = Frame(self.url_canvas)
        self.url_window = self.url_canvas.create_window((0, 0), window=self.url_rows_frame, anchor="nw")
        self.url_rows_frame.bind("<Configure>", self.update_scroll_region)
        self.url_canvas.bind("<Configure>", self.resize_url_rows)
        url_tools = Frame(self)
        url_tools.grid(row=1, column=2, padx=12, sticky="n")
        self.add_button = Button(url_tools, text="+", width=3, command=self.add_url_field)
        self.add_button.pack()
        self.url_scrollbar = Scrollbar(url_tools, orient="vertical", command=self.url_canvas.yview)
        self.url_scrollbar.pack(fill="y", expand=True)
        self.url_canvas.configure(yscrollcommand=self.url_scrollbar.set)
        self.url_rows = []
        self.downloading = False
        self.add_url_field()

        self.format_label = Label(self)
        self.format_label.grid(row=2, column=0, padx=12, pady=8, sticky="e")
        self.media_format = StringVar(value="mp3")
        self.format_combo = Combobox(self, textvariable=self.media_format, values=("mp3", "mp4"),
                                     state="readonly", width=6)
        self.format_combo.grid(row=2, column=1, pady=8, sticky="w")

        self.folder_label = Label(self)
        self.folder_label.grid(row=3, column=0, padx=12, sticky="e")
        self.folder = StringVar(value=str(self.config_data.default_path))
        self.folder_entry = Entry(self, textvariable=self.folder, state="readonly")
        self.folder_entry.grid(row=3, column=1, sticky="ew")
        self.folder_button = Button(self, command=self.choose_folder)
        self.folder_button.grid(row=3, column=2, padx=12)

        progress_row = Frame(self)
        progress_row.grid(row=4, column=1, sticky="ew", pady=(16, 3))
        progress_row.columnconfigure(0, weight=1)
        self.progress_bar = Progressbar(progress_row, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        Frame(progress_row, width=self.url_rows[0][2].winfo_reqwidth() + 5).grid(row=0, column=1)
        self.progress_label = Label(self)
        self.progress_label.grid(row=5, column=1)
        self.queue_label = Label(self)
        self.queue_label.grid(row=6, column=1, pady=(3, 0))
        self.current_label = Label(self, wraplength=620)
        self.current_label.grid(row=7, column=1, pady=(3, 0))

        controls = Frame(self)
        controls.grid(row=8, column=1, pady=15)
        self.download_button = Button(controls, command=self.action)
        self.download_button.pack(side="left", padx=5)
        self.cancel_button = Button(controls, command=self.cancel_download, state="disabled")
        self.cancel_button.pack(side="left", padx=5)

        self.progress_updates = Queue()
        self.progress_stage = None
        self.progress_percent = None
        self.cancel_event = None
        self.request_id = 0
        self.polling = False
        self.items = []
        self.completed = 0
        self.queue_done = False
        self.current_item = None
        self.reserved_paths = set()
        self.set_language()

    def update_scroll_region(self, _event=None):
        self.url_canvas.configure(scrollregion=self.url_canvas.bbox("all"))

    def resize_url_rows(self, event):
        self.url_canvas.itemconfigure(self.url_window, width=event.width)

    def add_url_field(self):
        if getattr(self, "downloading", False):
            return
        row = Frame(self.url_rows_frame)
        row.columnconfigure(0, weight=1)
        entry = Entry(row)
        entry.grid(row=0, column=0, sticky="ew", pady=2)
        entry.bind("<Button-3>", lambda event: RightClicker(event, self.language))
        remove_button = Button(row, text="−", width=3, command=lambda: self.remove_url_field(row))
        remove_button.grid(row=0, column=1, padx=(5, 0))
        row.pack(fill="x")
        self.url_rows.append((row, entry, remove_button))
        self.url = self.url_rows[0][1]
        self.update_remove_buttons()
        self.url_rows_frame.update_idletasks()
        self.update_scroll_region()
        self.url_canvas.yview_moveto(1.0)

    def remove_url_field(self, row):
        if self.downloading or len(self.url_rows) == 1:
            return
        for index, (frame, _entry, _button) in enumerate(self.url_rows):
            if frame == row:
                frame.destroy()
                del self.url_rows[index]
                break
        self.url = self.url_rows[0][1]
        self.update_remove_buttons()

    def update_remove_buttons(self):
        state = "disabled" if self.downloading or len(self.url_rows) == 1 else "normal"
        for _row, _entry, button in self.url_rows:
            button.config(state=state)

    def clear_url_fields(self):
        for row, _entry, _button in self.url_rows:
            row.destroy()
        self.url_rows.clear()
        self.add_url_field()

    def choose_folder(self):
        selected = askdirectory(initialdir=self.folder.get(), title=self.language.text("choose_folder"))
        if selected:
            self.folder.set(selected)

    def set_inputs_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for _row, entry, _button in self.url_rows:
            entry.config(state=state)
        self.add_button.config(state=state)
        self.folder_button.config(state=state)
        self.format_combo.config(state="readonly" if enabled else "disabled")
        self.update_remove_buttons()

    def set_language(self):
        t = self.language.text
        self.title_label.config(text=t("downloader_title"))
        self.url_label.config(text=t("video_urls"))
        self.format_label.config(text=t("format"))
        self.folder_label.config(text=t("folder"))
        self.folder_button.config(text=t("browse"))
        self.download_button.config(text=t("downloading" if self.downloading else "download"))
        self.cancel_button.config(text=t("cancel"))
        if self.progress_stage == "title":
            progress_text = t("fetching_title")
        elif self.progress_stage == "processing":
            progress_text = t("processing_download")
        elif self.progress_stage == "downloading":
            progress_text = (t("downloading") if self.progress_percent is None else
                             t("download_progress").format(percent=round(self.progress_percent)))
        elif self.progress_stage == "canceling":
            progress_text = t("canceling")
        elif self.progress_stage == "cancelled":
            progress_text = t("download_cancelled")
        else:
            progress_text = ""
        self.progress_label.config(text=progress_text)
        if self.items:
            queue_text = (t("queue_done").format(count=len(self.items)) if self.queue_done else
                          t("queue_progress").format(done=self.completed, total=len(self.items)))
        else:
            queue_text = ""
        self.queue_label.config(text=queue_text)
        if self.current_item:
            title = self.current_item.title
            display_title = title[:90] + ("…" if len(title) > 90 else "")
            self.current_label.config(text=t("current_download").format(title=display_title))
        else:
            self.current_label.config(text="")

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
        urls = [entry.get().strip() for _row, entry, _button in self.url_rows if entry.get().strip()]
        if not urls:
            messagebox.showerror(self.language.text("download"), self.language.text("enter_url"))
            return
        folder = Path(self.folder.get())
        if not folder.is_dir():
            messagebox.showerror(self.language.text("download"), self.language.text("folder_missing"))
            return
        self.request_id += 1
        request_id = self.request_id
        self.cancel_event = Event()
        self.downloading = True
        self.items = []
        self.completed = 0
        self.queue_done = False
        self.current_item = None
        self.reserved_paths = set()
        self.download_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.set_inputs_enabled(False)
        self.show_progress("title")
        Thread(target=self.prepare_items, args=(request_id, urls, self.cancel_event), daemon=True).start()
        if not self.polling:
            self.polling = True
            self.after(100, self.poll_progress)

    def prepare_items(self, request_id, urls, cancel_event):
        try:
            items = expand_urls(urls, self.config_data.ffmpeg, cancel_event)
        except DownloadCancelled:
            self.progress_updates.put((request_id, "cancelled", None))
        except Exception as error:
            self.progress_updates.put((request_id, "error", str(error)))
        else:
            self.progress_updates.put((request_id, "items", items))

    def start_next_item(self, request_id):
        if self.cancel_event.is_set():
            self.finish(cancelled=True)
            return
        if self.completed >= len(self.items):
            self.finish()
            return
        item = self.items[self.completed]
        self.current_item = item
        media_format = self.media_format.get()
        try:
            destination = unique_destination(self.folder.get(), item.title, media_format, self.reserved_paths)
        except OSError as error:
            self.finish(str(error))
            return
        self.show_progress("downloading")
        cancel_event = self.cancel_event

        def worker():
            try:
                download_media(item.url, destination, media_format, self.config_data.ffmpeg,
                               self.config_data.bitrate,
                               progress=lambda stage, percent: self.progress_updates.put((request_id, "progress", (stage, percent))),
                               cancel=cancel_event)
            except DownloadCancelled:
                self.progress_updates.put((request_id, "cancelled", None))
            except Exception as error:
                self.progress_updates.put((request_id, "error", str(error)))
            else:
                self.progress_updates.put((request_id, "item_done", None))

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
                if kind == "items":
                    self.items = value
                    self.start_next_item(request_id)
                elif kind == "progress":
                    if self.cancel_event is not None and not self.cancel_event.is_set():
                        self.show_progress(*value)
                elif kind == "item_done":
                    self.completed += 1
                    self.start_next_item(request_id)
                elif kind == "error":
                    if self.cancel_event is not None and self.cancel_event.is_set():
                        self.finish(cancelled=True)
                    else:
                        self.finish(value)
                elif kind == "cancelled":
                    self.finish(cancelled=True)
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
        self.current_item = None
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.set_inputs_enabled(True)
        self.show_progress(None)

    def finish(self, error=None, cancelled=False):
        failed_title = self.current_item.title if self.current_item else None
        if not error and not cancelled:
            self.queue_done = True
        self.reset_progress()
        if cancelled:
            self.show_progress("cancelled")
        elif error:
            details = self.language.error(error)
            if failed_title:
                details = f"{failed_title}\n{details}"
            messagebox.showerror(self.language.text("download_failed"), details)
        else:
            self.clear_url_fields()
            messagebox.showinfo(self.language.text("download"), self.language.text("batch_saved"))
