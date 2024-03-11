from tkinter import Tk
from menu import MenuBar
from downloader_frame import Downloader
from shrinker_frame import Shrinker
from fields_editor_frame import FieldsEditor


class YTDownloader:
    __root = Tk()
    __thisWidth = 700
    __thisHeight = 360

    def __init__(self, **kwargs):
        try:
            self.__thisWidth = kwargs['width']
        except KeyError:
            pass
        try:
            self.__thisHeight = kwargs['height']
        except KeyError:
            pass
        self.__root.title("YTD")
        self.bg_color = 'white'
        screenWidth = self.__root.winfo_screenwidth()
        screenHeight = self.__root.winfo_screenheight()
        left = (screenWidth / 2) - (self.__thisWidth / 2)
        top = (screenHeight / 2) - (self.__thisHeight / 2)
        self.__root.geometry('%dx%d+%d+%d' % (self.__thisWidth, self.__thisHeight, left, top))
        self.menu = MenuBar(self.__root, {'download': self.choose_downloader,
                                          'shrink': self.choose_shrinker,
                                          'fields editor': self.choose_fields_editor})
        self.frame1 = Downloader(self.__root)
        self.frame2 = Shrinker(self.__root)
        self.frame3 = FieldsEditor(self.__root)
        self.frame2.pack_forget()
        self.frame3.pack_forget()

    def choose_shrinker(self):
        self.frame1.pack_forget()
        self.frame3.pack_forget()
        self.frame2.pack(fill='both', expand=True)

    def choose_downloader(self):
        # clear currently displayed window
        self.frame2.pack_forget()
        self.frame3.pack_forget()
        # display new window
        self.frame1.pack(fill='both', expand=True)

    def choose_fields_editor(self):
        # clear currently displayed window
        self.frame1.pack_forget()
        self.frame2.pack_forget()
        # display new window
        self.frame3.pack(fill='both', expand=True)

    def run(self):
        # Run main application
        self.__root.mainloop()

    def __quitApplication(self):
        self.__root.destroy()
