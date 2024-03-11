from tkinter import Menu


class MenuBar(Menu):
    def __init__(self, parent, fun_names):
        super().__init__(parent)
        __thisMenuBar = Menu(self, tearoff=0)
        __thisCommandMenu = Menu(__thisMenuBar, tearoff=0)

        __thisCommandMenu.add_command(label="Downloader", command=fun_names['download'])
        __thisCommandMenu.add_command(label="Shrinker", command=fun_names['shrink'])
        __thisCommandMenu.add_command(label="Fields Editor", command=fun_names['fields editor'])

        __thisMenuBar.add_cascade(label="Menu", menu=__thisCommandMenu)

        # this command display menu, if __thisMenuBar was self. argument, then it does not work
        parent.config(menu=__thisMenuBar)


class RightClicker:
    def __init__(self, event):
        right_click_menu = Menu(None, tearoff=0, takefocus=0)
        for txt in ['Cut', 'Copy', 'Paste']:
            right_click_menu.add_command(
                label=txt, command=lambda event=event, text=txt:
                RightClicker.right_click_command(event, text))
        right_click_menu.tk_popup(event.x_root + 40, event.y_root + 10, entry='0')

    @staticmethod
    def right_click_command(event, cmd):
        event.widget.event_generate(f'<<{cmd}>>')

# the author: Dariusz Piekarz
