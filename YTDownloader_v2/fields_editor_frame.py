from tkinter import Button, Entry, Frame, Label, END, messagebox
from tkinter import filedialog

from PIL import Image, ImageGrab, ImageTk

from Config import Config
from fields_editor_core import edit_fields, load_metadata
from menu import RightClicker


class FieldsEditor(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.config_data = Config()
        self.file = None
        self.cover_image = None
        self.fields = {}
        self.columnconfigure(1, weight=1)
        self.file_label = Label(self, text="No MP3 selected")
        self.file_label.grid(row=0, column=0, columnspan=2, pady=8)
        Button(self, text="Open MP3", command=self.open_file).grid(row=0, column=2, padx=10)
        for row, name in enumerate(("title", "artist", "album", "genre", "track"), start=1):
            Label(self, text=name.title()).grid(row=row, column=0, padx=10)
            entry = Entry(self, width=55)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            entry.bind("<Button-3>", RightClicker)
            self.fields[name] = entry
        self.cover_label = Label(self, cursor="hand2")
        self.cover_label.grid(row=6, column=1, pady=8)
        self.cover_label.bind("<Button-1>", lambda event: self.open_image())
        self.cover_label.bind("<Button-3>", self.paste_image)
        Button(self, text="Select cover", command=self.open_image).grid(row=6, column=2)
        Button(self, text="Clear fields", command=self.clear).grid(row=7, column=1, sticky="w")
        Button(self, text="Save", command=self.save_file).grid(row=7, column=1, sticky="e")
        self.show_cover(None)

    def show_cover(self, image):
        display = image if image is not None else Image.open(self.config_data.default_image)
        preview = display.copy()
        preview.thumbnail((180, 180), Image.Resampling.LANCZOS)
        self.cover_photo = ImageTk.PhotoImage(preview)
        self.cover_label.config(image=self.cover_photo)

    def open_file(self):
        filename = filedialog.askopenfilename(initialdir=self.config_data.default_path, filetypes=[("MP3", "*.mp3")])
        if not filename:
            return
        try:
            metadata = load_metadata(filename)
        except Exception as error:
            messagebox.showerror("Open failed", str(error))
            return
        self.file = filename
        self.file_label.config(text=filename)
        for name, entry in self.fields.items():
            entry.delete(0, END)
            entry.insert(0, metadata[name])
        self.cover_image = metadata["cover_image"]
        self.show_cover(self.cover_image)

    def open_image(self):
        filename = filedialog.askopenfilename(initialdir=self.config_data.default_path,
                                               filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if filename:
            try:
                with Image.open(filename) as image:
                    self.cover_image = image.copy()
                self.show_cover(self.cover_image)
            except Exception as error:
                messagebox.showerror("Cover", str(error))

    def paste_image(self, event=None):
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            self.cover_image = image.copy()
            self.show_cover(self.cover_image)
        else:
            messagebox.showerror("Cover", "The clipboard does not contain an image.")

    def clear(self):
        for entry in self.fields.values():
            entry.delete(0, END)
        self.cover_image = None
        self.show_cover(None)

    def save_file(self):
        if not self.file:
            messagebox.showerror("Save", "Open an MP3 file first.")
            return
        try:
            edit_fields(self.file, cover_image=self.cover_image,
                        **{name: entry.get() for name, entry in self.fields.items()})
        except Exception as error:
            messagebox.showerror("Save failed", str(error))
        else:
            messagebox.showinfo("Save", "Metadata saved.")
