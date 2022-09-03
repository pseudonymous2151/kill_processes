#!/usr/local/bin/python3

"""A simple Tkinter based Process killer GUI

uses psutil to list running processes and provides similar files
like multi-select option for processes allowing easier process killing
and supports multi-platforms as its underlying libraries and tkinter do.
"""


from platform import system
OS: str = system()  # get platform
import os  # always run in script dir
os.chdir(os.path.dirname(__file__))

# Both run on import and perform their functions.
__import__('install_requirements')       # install requirements
if OS == 'Windows':       # escalate privilege on windows.
    __import__('getprivilege').runasadmin()


import psutil
import threading
import time
from tkinter import (BOTH, END, EXTENDED, LEFT, RIGHT, SUNKEN, YES, Button,
                     Frame, Listbox, Scrollbar, X, Y, messagebox)


def get_system_processes(processes_file: str) -> list[str]:
    """
    Return system processes from file for the current platform
    or return empty list if file or configuration is not found.
    """

    from json import load
    try:
        with open(processes_file) as file:
            obj: dict = load(file)
            # return empty list if no system
            # configuration for the platform.
            return obj.get(OS) or []
    except FileNotFoundError:
        from os import getcwd
        print(f'"{processes_file}" not found in "{getcwd()}"')
        return []   # return empty list if no system file found.

SYSTEM_PROCESSES = get_system_processes('system_processes.json')


class ProcessIter:
    "Iterate over processes 'id'."

    def __init__(self, processes: list[tuple[int, str]]) -> None:
        self.processes = processes

    def __iter__(self):
        self.index = -1
        return self

    def __next__(self) -> int:
        self.index += 1
        try:
            return self.processes[self.index][0]
        except IndexError:
            raise StopIteration from None


class Process:
    "Manage Process Related Tasks."

    @staticmethod
    def get_processes() -> list[tuple[int, str]]:
        "Return list of all the running processes."

        processes: list[tuple[int, str]] = []
        for process in psutil.process_iter():
            process_name = process.name()
            if process_name in SYSTEM_PROCESSES:
                continue
            processes.append((process.pid, process_name))
        return processes

    @staticmethod
    def kill(pid: int) -> str:
        "Return kill status for the process."

        try:
            psutil.Process(pid).kill()
        except psutil.AccessDenied:
            return 'access denied'
        except psutil.NoSuchProcess:
            return 'not running'
        except psutil.Error:
            return 'failed'
        else:
            return 'success'

    def kill_process(self, pos: int) -> str:
        "Return kill message for process."

        pid, name = self.processes[pos]
        status = self.kill(pid)
        if status == 'success':
            return f"killed process: {name} with pid: {pid}"
        elif status == 'not running':
            return f"{name} is not running with pid: {pid}"
        elif status == 'access denied':
            return f"No permission to kill process: {name} with pid: {pid}"
        else:
            return f"Failed to kill process: {name} with pid: {pid}"

    def kill_processes(self, event=None) -> None:
        """
        Kill multiple-processes and popup error
        message for failed to terminate processes.
        """

        indexes: tuple[int] = self.listbox.curselection()
        error_messages: str = ''
        for index in indexes:
            message = self.kill_process(index)
            if 'killed' not in message:
                error_messages += message + '\n'

        if not error_messages:
            return  # Return if no error messages to show
        title_message: str = 'Unable to terminate process'
        if len(indexes) != 1:
            title_message += 'es'
        messagebox.showerror(title_message, error_messages)


class MainWindow(Process, Frame):
    def __init__(self, parent=None, *, size: str = "675x525", title: str = "Kill Processes"):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)
        self.master.geometry(size)
        self.master.title(title)
        self.makeWidgets()

    def makeWidgets(self):
        sbar = Scrollbar(self)
        lbox = Listbox(self, relief=SUNKEN)
        sbar.config(command=lbox.yview)
        lbox.config(yscrollcommand=sbar.set)
        lbox.config(selectmode=EXTENDED)
        sbar.pack(side=RIGHT, fill=Y)
        lbox.pack(side=LEFT, expand=YES, fill=BOTH)
        lbox.bind('<Double-1>', self.kill_processes)
        self.listbox = lbox

        Button(self.master, text='END',
               command=self.kill_processes, width=10).pack(fill=X, side=RIGHT)
        Button(self.master, text='Refresh',
               command=self.reload, width=8).pack(fill=X, side=LEFT)
        Button(self.master, text='Sort',
               command=self.sort).pack(fill=X)
        self.master.bind('<F5>', self.reload)

        self.mutex = threading.Lock()
        self.thread = None  # initial thread instance value
        self.start_load()
        self.start_updater()

    def start_load(self):
        if self.thread and self.thread.is_alive():
            return 0  # return if previous thread is still alive.

        thread = threading.Thread(target=self.load)
        thread.daemon = True
        self.thread = thread  # save the thread instance
        thread.start()

    def start_updater(self):
        thread = threading.Thread(target=self.updater)
        thread.daemon = True
        thread.start()

    def load(self):
        with self.mutex:
            self.processes = self.get_processes()
            for _, process_name in self.processes:
                self.listbox.insert(END, process_name)

    def reload(self, event=None):
        self.listbox.delete(0, END)
        self.start_load()

    def sort(self):
        self.processes.sort(key=lambda x: x[1])
        self.listbox.delete(0, END)
        for _, process_name in self.processes:
            with self.mutex:
                self.listbox.insert(END, process_name)

    def updater(self, delay: int | float = 0.5):
        time.sleep(1)  # delay startup
        self.pids = ProcessIter(self.processes)
        while True:
            time.sleep(delay)
            # update if focused
            if self.focus_get():
                self.update()

    def update(self):
        pids = psutil.pids()
        # Remove not running processes
        for pos, (pid, _) in enumerate(self.processes):
            if pid not in pids:
                self.listbox.delete(pos)
                self.processes.pop(pos)
        # Add new running processes
        for pid in pids:
            if pid in self.pids:
                continue
            try:
                process_name = psutil.Process(pid).name()
            except psutil.NoSuchProcess:  # incase process
                continue   # terminated in nick of the time.
            if process_name in SYSTEM_PROCESSES:
                continue
            self.listbox.insert(0, process_name)
            self.processes.insert(0, (pid, process_name))
        # update ProcessIter because self.processes isn't updated
        # accordingly in time fast enough within the threads.
        self.pids = ProcessIter(self.processes)


if __name__ == '__main__':
    MainWindow().mainloop()
