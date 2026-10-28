from tkinter import Menu, StringVar


class MenuBar(Menu):
    def __init__(self, parent, commands, language, on_language):
        super().__init__(parent)
        self.language = language
        self.tools_menu = Menu(self, tearoff=0)
        for command in commands.values():
            self.tools_menu.add_command(command=command)
        self.add_cascade(menu=self.tools_menu)

        self.language_menu = Menu(self, tearoff=0)
        self.language_choice = StringVar(master=parent, value=language.code)
        for code, label in (("pl", "Polski"), ("en", "English")):
            self.language_menu.add_radiobutton(
                label=label, value=code, variable=self.language_choice,
                command=lambda selected=code: on_language(selected),
            )
        self.add_cascade(menu=self.language_menu)
        parent.config(menu=self)
        self.set_language()

    def set_language(self):
        t = self.language.text
        self.entryconfig(0, label=t("menu"))
        self.entryconfig(1, label=t("language"))
        for index, key in enumerate(("download_tab", "shrink_tab", "fields_tab", "clipmaker_tab")):
            self.tools_menu.entryconfig(index, label=t(key))
        self.language_choice.set(self.language.code)


class RightClicker:
    def __init__(self, event, language):
        menu = Menu(event.widget, tearoff=0)
        for command in ("Cut", "Copy", "Paste"):
            menu.add_command(
                label=language.text(command.lower()),
                command=lambda selected=command: event.widget.event_generate(f"<<{selected}>>"),
            )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
