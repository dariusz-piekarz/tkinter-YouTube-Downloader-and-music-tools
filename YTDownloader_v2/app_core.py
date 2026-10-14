from tkinter import Tk

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
        self.language = Language()
        self.frames = {
            "download": Downloader(self.root, self.language),
            "shrink": Shrinker(self.root, self.language),
            "fields editor": FieldsEditor(self.root, self.language),
        }
        self.menu = MenuBar(
            self.root,
            {name: lambda selected=name: self.show(selected) for name in self.frames},
            self.language, self.set_language,
        )
        self.show("download")

    def set_language(self, code):
        self.language.select(code)
        self.menu.set_language()
        for frame in self.frames.values():
            frame.set_language()

    def show(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()
