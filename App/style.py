# Source - https://stackoverflow.com/a/49896477
# Posted by scotty3785, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-13, License - CC BY-SA 4.0

import tkinter as tk

class HoverButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self,master=master,**kw)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = 'lightgrey'
        self['cursor'] = 'hand2'
        self['relief'] = 'sunken'

    def on_leave(self, e):
        self['background'] = self.defaultBackground
        self['relief'] = 'raised'


class HoverOptionMenu(tk.OptionMenu):
    def __init__(self, *args, **kw):
        tk.OptionMenu.__init__(self, *args, **kw)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = 'lightgrey'
        self['cursor'] = 'hand2'
        self['relief'] = 'sunken'

    def on_leave(self, e):
        self['background'] = self.defaultBackground
        self['relief'] = 'raised'
