from threading import Thread
from tkinter import BOTH, DISABLED, END, YES
from tkinter.scrolledtext import ScrolledText


class Window(ScrolledText):
    "A scrolledtext window reading input on stdin."

    font = ('courier', 9, 'normal')

    def __init__(self, parent=None, *, title: str, size: str = "625x350"):
        ScrolledText.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)
        self.config(font=self.font)
        self.master.master.title(title)
        self.master.master.geometry(size)
        self.start_stdin()

    def start_stdin(self):
        thread = Thread(target=self.read_stdin)
        thread.daemon = True
        thread.start()

    def read_stdin(self):
        while True:
            try:
                inp = input()
            except EOFError:
                self.config(state=DISABLED)
                return  # exit thread
            else:
                self.write(inp)

    def write(self, text: str):
        self.insert(END, text + '\n')
        self.see(END)


if __name__ == '__main__':
    from sys import argv
    if len(argv) > 1:
        name = argv[1]
    else:
        name = __name__
    Window(title=name).mainloop()
