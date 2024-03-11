from tkinter import Frame, Label, Button, Entry, END
from tkinter.filedialog import asksaveasfilename, askopenfilename
from Config import Config
from shrink_core import Segment


class Shrinker(Frame):
    font = 'Arial 12'
    min = [0, 0, 0]
    max = [0, 0, 0]
    entry_min_min = str()
    entry_min_sec = str()
    entry_min_msec = str()
    entry_max_min = str()
    entry_max_sec = str()
    entry_max_msec = str()

    config = Config(r"config.yaml")

    def __init__(self, *args, **kwars):
        super().__init__(*args, **kwars)
        self.label()
        self.entries()
        self.buttons()

    def label(self):
        self.space = Label(self, text="     ", font=self.font)
        self.space.grid(row=1, column=1, sticky='ew')
        self.label1 = Label(self, text="1. ", font=self.font)
        self.label1.grid(row=2, column=1, sticky='ew')
        self.label2 = Label(self, text="2. ", font=self.font)
        self.label2.grid(row=3, column=1, sticky='ew')
        self.label3 = Label(self, text="3. ", font=self.font)
        self.label3.grid(row=4, column=1, sticky='ew')
        self.label4 = Label(self, text="Set length", font=self.font)
        self.label4.grid(row=3, column=2, sticky='ew')
        self.label5 = Label(self, text="-", font=self.font)
        self.label5.grid(row=3, column=10, sticky='ew')
        self.label6 = Label(self, text=":", font=self.font)
        self.label6.grid(row=3, column=6, sticky='ew')
        self.label7 = Label(self, text=":", font=self.font)
        self.label7.grid(row=3, column=12, sticky='ew')
        self.label8 = Label(self, text=":", font=self.font)
        self.label8.grid(row=3, column=8, sticky='ew')
        self.label9 = Label(self, text=":", font=self.font)
        self.label9.grid(row=3, column=14, sticky='ew')

    def entries(self):
        self.entry_min_min = Entry(self, self.entry_min_min, font=self.font, width=2)
        self.entry_min_sec = Entry(self, self.entry_min_sec, font=self.font, width=2)
        self.entry_min_msec = Entry(self, self.entry_min_msec, font=self.font, width=2)
        self.entry_max_min = Entry(self, self.entry_max_min, font=self.font, width=2)
        self.entry_max_sec = Entry(self, self.entry_max_sec, font=self.font, width=2)
        self.entry_max_msec = Entry(self, self.entry_max_sec, font=self.font, width=2)
        self.entry_min_min.grid(row=3, column=5, sticky='w')
        self.entry_min_sec.grid(row=3, column=7, sticky='e')
        self.entry_min_msec.grid(row=3, column=9, sticky='e')
        self.entry_max_min.grid(row=3, column=11, sticky='w')
        self.entry_max_sec.grid(row=3, column=13, sticky='e')
        self.entry_max_msec.grid(row=3, column=15, sticky='e')

    def buttons(self):
        self.open = Button(self, text="Open", command=self.open, width=12)
        self.open.grid(row=2, column=2, columnspan=1, sticky="e")
        self.extract = Button(self, text="Extract", command=self.extract, width=12)
        self.extract.grid(row=4, column=2, columnspan=1, sticky="e")

    def open(self):
        a = askopenfilename(filetypes=(("MPEG Layer 3", "*.mp3"), ("MP4", "*.mp4"), ("All Files", "*.*")),
                               defaultextension='mp3', initialdir=self.config.YTDownloader.default_path)
        self.ext = a.split(".")[-1]
        self.file = Segment(a, ext=self.ext)
        length = self.file.sound.duration
        y = length // 60
        z = length - y * 60

        self.max = [int(length // 60), int(z), int((z - int(z)) * 60)]

        self.entry_min_min.delete(0, END)
        self.entry_min_sec.delete(0, END)
        self.entry_min_msec.delete(0, END)
        self.entry_max_min.delete(0, END)
        self.entry_max_sec.delete(0, END)
        self.entry_max_msec.delete(0, END)

        self.entry_min_min.insert(0, 0)
        self.entry_min_sec.insert(0, 0)
        self.entry_min_msec.insert(0, 0)
        self.entry_max_min.insert(0, self.max[0])
        self.entry_max_sec.insert(0, self.max[1])
        self.entry_max_msec.insert(0, self.max[2])

        self.file.set_min_max(self.min, self.max)
        # self.file.sound.preview()

    def extract(self):
        self.file.set_min_max([self.entry_min_min.get(), self.entry_min_sec.get(), self.entry_min_msec.get()],
                              [self.entry_max_min.get(), self.entry_max_sec.get(), self.entry_max_msec.get()])
        extract = self.file.extract()
        a = asksaveasfilename(filetypes=(("MPEG Layer 3", "*.mp3"), ("MP4", "*.mp4"), ("All Files", "*.*")),
                               defaultextension=self.ext, initialdir=self.config.YTDownloader.default_path)
        if self.ext == 'mp3':
            extract.write_audiofile(a)
        elif self.ext == 'mp4':
            extract.write_videofile(a)
