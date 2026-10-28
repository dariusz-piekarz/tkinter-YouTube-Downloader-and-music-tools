from tkinter import Tk

from clipmaker_frame import ClipMakerFrame
from downloader_frame import Downloader
from fields_editor_frame import FieldsEditor
from i18n import Language
from menu import MenuBar
from shrinker_frame import Shrinker


class YTDownloader:
    def __init__(self):
        self.root = Tk()
        self.root.title("YTD")
        self.root.geometry("760x440")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.language = Language()
        self.frames = {
            "download": Downloader(self.root, self.language),
            "shrink": Shrinker(self.root, self.language),
            "fields editor": FieldsEditor(self.root, self.language),
            "clipmaker": ClipMakerFrame(self.root, self.language),
        }
        commands = {name: lambda selected=name: self.show(selected) for name in self.frames}
        self.menu = MenuBar(
            self.root,
            commands,
            self.language, self.set_language,
        )
        self.show("download")

    def set_language(self, code):
        self.language.select(code)
        self.menu.set_language()
        for frame in self.frames.values():
            frame.set_language()

    def show(self, name):
        if name != "shrink":
            self.frames["shrink"].stop_playback()
        if name != "clipmaker":
            self.frames["clipmaker"].stop_preview_player()
        self.root.geometry("940x680" if name == "clipmaker" else "760x440")
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()

    def close(self):
        if self.frames["clipmaker"].rendering:
            from tkinter import messagebox
            messagebox.showinfo(self.language.text("clipmaker_tab"),
                                self.language.text("clip_wait_render"), parent=self.root)
            return
        self.root.destroy()
