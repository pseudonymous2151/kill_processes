"""Python requirements installer script

uses python pip to install packages listed in requirements file
in platform-neutral way on Linux platform uses pip -r option to
directly install packages, on others uses pip install 'package_name',
In a scrolled text window showing packages installation progress
and assumes its dependencies to be in current working directory.

# Note: this module runs on import as well, to install packages for
current module or being launched as a process from any other program
enabling itself to be used in both contexts for wider use cases.
"""

import http.client as httplib
import subprocess
import sys

import pkg_resources

# python executable file
PYEXEC: str = sys.executable
# Requirements file
REQ_FILE: str = 'requirements.txt'


class GuiOutput:
    """
    A file like GUI interface which displays
    writes in a separate scrolledtext window.
    """

    def __init__(self):
        self.pipe = subprocess.Popen(
            [PYEXEC, '-u', 'installer_window.py', 'Packages Installer'], stdin=subprocess.PIPE)

    def close(self):
        if self.pipe.stdin:
            self.pipe.kill()

    def write(self, text: str):
        self.pipe.stdin.write(text.encode())
        self.pipe.stdin.flush()

    def writelines(self, lines):
        for line in lines:
            self.write(line)


def is_connected(host: str = "8.8.8.8") -> bool:
    "Check if device is connected to internet."

    conn = httplib.HTTPSConnection(host, timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except OSError:
        return False
    finally:
        conn.close()


def get_packages(requirement_file: str) -> list[str]:
    "Return not installed packages listed in requirements file."

    packages = pkg_resources.working_set
    installed_packages = [p.key for p in packages]

    installation_packages: list[str] = []
    with open(requirement_file) as file:
        for line in file:
            package, _ = line.split('==')
            if package not in installed_packages:
                installation_packages.append(line)
    return installation_packages


def install_packages(packages: list[str]) -> None:
    "Install packages using python pip module."

    gui_window = GuiOutput()
    print('Installing required packages:', file=gui_window)
    for package in packages:
        pipe = subprocess.Popen(
            [PYEXEC, '-m', 'pip', 'install', package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = pipe.communicate()
        print(out.decode(), file=gui_window)
        print(err.decode(), file=gui_window)


def install_requirements(requirement_file: str) -> None:
    "Install requirements using python pip installer."

    gui_window = GuiOutput()
    print('Installing required packages:', file=gui_window)
    pipe = subprocess.Popen(
        [PYEXEC, '-m', 'pip', 'install', '-r', requirement_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = pipe.communicate()
    print(out.decode(), file=gui_window)
    print(err.decode(), file=gui_window)


def main() -> None:
    import os
    requirement_file: str = REQ_FILE
    if not os.path.exists(requirement_file):
        from tkinter.messagebox import showerror
        showerror("Unable to locate file",
                  f"'{requirement_file}' not found in {os.getcwd()}")

    installation_packages = get_packages(requirement_file)
    if not installation_packages:
        return  # return if packages are already installed.

    if not is_connected():
        gui_window = GuiOutput()
        print("Following packages aren't installed:", file=gui_window)
        for package in installation_packages:
            print(' ' + package, file=gui_window)
        print("\nConnect Internet to install these packages.", file=gui_window)
        sys.exit(1)  # exit with error code 1 if packages
        # installation are remaining without internet.

    operating_system = sys.platform
    if operating_system == 'linux':
        install_requirements(requirement_file)
    else:
        install_packages(installation_packages)


if __name__:
    main()  # run on import as well
