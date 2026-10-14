from tkinter import Tk

from downloader_frame import Downloader
from fields_editor_frame import FieldsEditor
from menu import MenuBar
from shrinker_frame import Shrinker


class YTDownloader:
    def __init__(self):
        self.root = Tk()
        self.root.title("YTD")
        self.root.geometry("760x440")
        self.frames = {
            "download": Downloader(self.root),
            "shrink": Shrinker(self.root),
            "fields editor": FieldsEditor(self.root),
        }
        MenuBar(self.root, {name: lambda selected=name: self.show(selected) for name in self.frames})
        self.show("download")

    def show(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()
