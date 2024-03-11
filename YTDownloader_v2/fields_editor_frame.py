from os import remove
from tkinter import Frame, Label, Button, Entry, END, StringVar
from tkinter import filedialog
from PIL import Image, ImageTk, ImageGrab
from PIL.PngImagePlugin import PngImageFile
from Config import Config
from fields_editor_core import edit_fields, load_metadata
from pathlib import Path
from menu import RightClicker


_path = str(Path(__file__).parent)


class FieldsEditor(Frame):
    font = 'Arial 10'

    def __init__(self, *args, **kwars):
        super().__init__(*args, **kwars)
        self.file = ""
        self.author = ""
        self.title = ""
        self.album = ""
        self.album_cover_path = StringVar()
        self.album_cover_path.set("")
        self.genre = ""
        self.track = ""
        self.album_cover_image: PngImageFile
        self.config = Config(r"config.yaml")
        self.temp_path = Path()

        self.label()
        self.entries()
        self.default_picture()
        self.buttons()

    def default_picture(self):
        self.album_cover_image = Image.open(_path + self.config.YTDownloader.default_image)
        self.album_cover_image = self.album_cover_image.resize((180, 180))
        self.album_cover_photo = ImageTk.PhotoImage(self.album_cover_image)
        self.album_cover_label = Label(self, image=self.album_cover_photo, width=180, height=180)
        self.album_cover_label.bind("<Button-1>", self.on_left_label_click)
        self.album_cover_label.bind("<Button-3>", self.paste_image)
        self.album_cover_label.bind("<Enter>", self.change_cursor_on_enter)
        self.album_cover_label.bind("<Leave>", self.change_cursor_on_leave)
        self.album_cover_label.grid(row=8, column=2, sticky='w')

    def label(self):
        self.space = Label(self, text="         ", font=self.font)
        self.space.grid(row=1, column=1, sticky='ew')
        self.file_name = Label(self, text=self.file, font=self.font)
        self.file_name.grid(row=2, column=2, sticky='ew')
        self.label0 = Label(self, text="File: ", font=self.font)
        self.label0.grid(row=2, column=1, sticky='ew')
        self.label1 = Label(self, text="Title: ", font=self.font)
        self.label1.grid(row=3, column=1, sticky='ew')
        self.label2 = Label(self, text="Author:  ", font=self.font)
        self.label2.grid(row=4, column=1, sticky='ew')
        self.label3 = Label(self, text="Album:  ", font=self.font)
        self.label3.grid(row=5, column=1, sticky='ew')
        self.label4 = Label(self, text="Genre:  ", font=self.font)
        self.label4.grid(row=6, column=1, sticky='ew')
        self.label5 = Label(self, text="Track:  ", font=self.font)
        self.label5.grid(row=7, column=1, sticky='ew')
        self.label6 = Label(self, text="Cover:  ", font=self.font)
        self.label6.grid(row=8, column=1, sticky='n')

    def entries(self):
        self.title = Entry(self, font=self.font, width=60)
        self.author = Entry(self, font=self.font, width=60)
        self.album = Entry(self, font=self.font, width=60)
        self.genre = Entry(self, font=self.font, width=60)
        self.track = Entry(self, font=self.font, width=60)

        self.title.grid(row=3, column=2, sticky='e')
        self.author.grid(row=4, column=2, sticky='e')
        self.album.grid(row=5, column=2, sticky='e')
        self.genre.grid(row=6, column=2, sticky='e')
        self.track.grid(row=7, column=2, sticky='e')

        self.title.bind('<Button-3>', RightClicker)
        self.author.bind('<Button-3>', RightClicker)
        self.album.bind('<Button-3>', RightClicker)
        self.genre.bind('<Button-3>', RightClicker)
        self.track.bind('<Button-3>', RightClicker)

    def buttons(self):
        self.open_file = Button(self, text="Open file", command=self.open_file, width=12)
        self.open_file.grid(row=2, column=4, columnspan=1, sticky="w")
        self.open_image = Button(self, text="Select cover", command=self.open_image, width=12)
        self.open_image.grid(row=3, column=4, columnspan=1, sticky="w")
        self.clear_all = Button(self, text="Clear all", command=self.clear, width=12)
        self.clear_all.grid(row=4, column=4, columnspan=1, sticky="w")
        self.save_file = Button(self, text="Save file", command=self.save_file, width=12)
        self.save_file.grid(row=5, column=4, columnspan=1, sticky="w")

    def open_file(self):
        self.file = filedialog.askopenfilename(initialdir=self.config.YTDownloader.default_path,
                                               filetypes=(("MP3 files", "*.mp3"), ("MP4 files", "*.mp4")),
                                               defaultextension=".mp3")
        self.label()
        self.entries()
        self.clear()
        temp = load_metadata(self.file)
        self.title.insert(0, temp['title'])
        self.author.insert(0, temp['artist'])
        self.album.insert(0, temp['album'])
        self.genre.insert(0, temp['genre'])
        self.track.insert(0, temp['track'])
        if temp['cover_image'] is not None:
            self.album_cover_image = temp['cover_image']
            self.album_cover_image = self.album_cover_image.resize((180, 180))
            self.album_cover_photo = ImageTk.PhotoImage(self.album_cover_image)
            if hasattr(self, "album_cover_label"):
                self.album_cover_label.destroy()
            self.album_cover_label = Label(self, image=self.album_cover_photo, width=180, height=180)
            self.album_cover_label.bind("<Button-1>", self.on_left_label_click)
            self.album_cover_label.bind("<Button-3>", self.paste_image)
            self.album_cover_label.bind("<Enter>", self.change_cursor_on_enter)
            self.album_cover_label.bind("<Leave>", self.change_cursor_on_leave)
            self.album_cover_label.grid(row=8, column=2, sticky='w')

    def open_image(self):
        self.album_cover_path.set(filedialog.askopenfilename(initialdir=self.config.YTDownloader.default_path,
                                                             filetypes=(("JPG files", "*.jpg"),
                                                                        ("JPEG files", "*.jpeg"),
                                                                        ("PNG files", "*.png")),
                                                             defaultextension=".jpg"))
        self.album_cover_image = Image.open(self.album_cover_path.get())
        self.album_cover_image = self.album_cover_image.resize((180, 180), Image.ANTIALIAS)
        self.album_cover_photo = ImageTk.PhotoImage(self.album_cover_image)

        if hasattr(self, "album_cover_label"):
            self.album_cover_label.destroy()

        self.album_cover_label = Label(self, image=self.album_cover_photo, width=180, height=180)
        self.album_cover_label.bind("<Button-1>", self.on_left_label_click)
        self.album_cover_label.bind("<Button-3>", self.paste_image)
        self.album_cover_label.bind("<Enter>", self.change_cursor_on_enter)
        self.album_cover_label.bind("<Leave>", self.change_cursor_on_leave)
        self.album_cover_label.grid(row=8, column=2, sticky='w')

    def clear(self):
        self.album_cover_path.set("")
        self.title.delete(0, END)
        self.author.delete(0, END)
        self.album.delete(0, END)
        self.genre.delete(0, END)
        self.track.delete(0, END)
        self.default_picture()
        self.entries()

    def save_file(self):
        edit_fields(mp3_path=self.file,
                    cover_path=self.album_cover_path.get(),
                    title=self.title.get(),
                    artist=self.author.get(),
                    album=self.album.get(),
                    genre=self.genre.get(),
                    track=self.track.get())
        try:
            remove(self.temp_path)
        except:
            pass

    def on_left_label_click(self, event):
        self.album_cover_path.set(filedialog.askopenfilename(initialdir=self.config.YTDownloader.default_path,
                                                             filetypes=(("JPG files", "*.jpg"),
                                                                        ("JPEG files", "*.jpeg"),
                                                                        ("PNG files", "*.png")),
                                                             defaultextension=".jpg"))
        self.album_cover_image = Image.open(self.album_cover_path.get())
        self.album_cover_image = self.album_cover_image.resize((180, 180))
        self.album_cover_photo = ImageTk.PhotoImage(self.album_cover_image)
        if hasattr(self, "album_cover_label"):
            self.album_cover_label.destroy()
        self.album_cover_label = Label(self, image=self.album_cover_photo, width=180, height=180)
        self.album_cover_label.bind("<Button-1>", self.on_left_label_click)
        self.album_cover_label.bind("<Enter>", self.change_cursor_on_enter)
        self.album_cover_label.bind("<Leave>", self.change_cursor_on_leave)
        self.album_cover_label.grid(row=8, column=2, sticky='w')

    def change_cursor_on_enter(self, event):
        self.album_cover_label.config(cursor="hand2")

    def change_cursor_on_leave(self, event):
        self.album_cover_label.config(cursor="")

    def paste_image(self, event):
        self.temp_path = Path(_path + "\\temp\\temp.png")
        try:
            if hasattr(self, "album_cover_label"):
                self.album_cover_label.destroy()
            clipboard_content = ImageGrab.grabclipboard()
            clipboard_content.save(self.temp_path)
            self.album_cover_image = Image.open(self.temp_path)
            self.album_cover_image = self.album_cover_image.resize((180, 180))
            self.album_cover_photo = ImageTk.PhotoImage(self.album_cover_image)
            self.album_cover_label = Label(self, image=self.album_cover_photo, width=180, height=180)
            self.album_cover_label.bind("<Button-1>", self.on_left_label_click)
            self.album_cover_label.bind("<Button-3>", self.paste_image)
            self.album_cover_label.bind("<Enter>", self.change_cursor_on_enter)
            self.album_cover_label.bind("<Leave>", self.change_cursor_on_leave)
            self.album_cover_path.set(str(self.temp_path))
            self.album_cover_label.grid(row=8, column=2, sticky='w')

        except:
            pass


def remove_temp():
    try:
        remove(Path(_path + "\\temp\\temp.png"))
    except:
        pass
