"""Python privilege elevation script

Provides privilege elevation functions
to get admin privilege on windows
via UAC prompt using ctypes and vbs.
"""

import ctypes
import os
import subprocess
import sys


def is_admin() -> bool:
    "Check if the current user is an administrator."

    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def is_administrator(command: str = 'dism') -> bool:
    "Check privilege using command execution exit code."

    pipe = subprocess.Popen(command, stdout=open(os.devnull, 'w'))
    return not pipe.wait()


def exec(executable: str, argument: str = '') -> None:
    "Elevate any executable using ctypes."

    return ctypes.windll.shell32.ShellExecuteW(
        None, "runas", f'"{executable}"', f'"{argument}"', None, 1)


def execute(executable: str, argument: str = '') -> None:
    "Elevate any executable using vb script."

    run_vbs = 'Run_GetPrivilege.vbs'
    esc_script = 'GetPrivilege.vbs'
    tmpdir = os.getenv('TEMP') or os.getcwd()
    launch_vbs = os.path.join(tmpdir, run_vbs)
    elevation_vbs = os.path.join(tmpdir, esc_script)
    # create elevation vb script to run executable.
    with open(elevation_vbs, 'w') as escal_file:
        escal_file.write('Set UAC = CreateObject("Shell.Application")' + '\n')
        escal_file.write(
            f'UAC.ShellExecute "{executable}", """{argument}""", "", "runas", 1'
        )
    # create vb script to run elevation vb script hidden.
    with open(launch_vbs, 'w') as launch_file:
        launch_file.write(
            f'CreateObject("Wscript.Shell").Run "{elevation_vbs}", 0, True')
    # get 'wscript.exe'
    comspec = os.getenv('COMSPEC')
    system32 = os.path.dirname(comspec)
    wscript = os.path.join(system32, 'wscript.exe')
    if not os.path.exists(wscript):
        raise FileNotFoundError(f"'wscript.exe' not found in '{system32}'")
    # run wscript.exe to execute vb script without window.
    pipe = subprocess.Popen(f'{wscript} "{launch_vbs}"',
                            stdout=open(os.devnull, "w"))
    pipe.wait()  # wait for process to finish.
    # delete files after execution.
    os.remove(launch_vbs)
    os.remove(elevation_vbs)


def get_pyexec(pyfile: str) -> str:
    "Return python executable based on pyfile."

    pyexec = sys.executable
    ext = os.path.splitext(pyfile)[-1].lower()
    if ext == '.pyw':
        pypath = os.path.dirname(pyexec)
        pywexec = os.path.join(pypath, 'pythonw.exe')
        if not os.path.exists(pywexec):
            raise FileNotFoundError(f"'pythonw.exe' not found in '{pypath}'")
        pyexec = pywexec
    return pyexec


def exec_pyscript(pyfile: str) -> None:
    "elevate python script using ctypes."

    pyexec = get_pyexec(pyfile)
    exec(pyexec, pyfile)  # elevate python file.


def execute_pyscript(pyfile: str) -> None:
    "elevate python script using vb script."

    pyexec = get_pyexec(pyfile)
    execute(pyexec, pyfile)  # elevate python file.


def runasadmin(pyfile: str = '') -> None:
    """
    Check privilege and elevate the *.py or *.pyw
    file accordingly with admin privilege using ctypes.
    """

    if is_admin():
        return  # Return if already has privilege.

    if not pyfile:
        pyfile = sys.argv[0]
    exec_pyscript(pyfile)  # elevate python file.
    sys.exit(0)  # Exit the current script to prevent running below code.


def runasadministrator(pyfile: str = ''):
    """
    Check privilege and elevate the *.py or *.pyw
    file accordingly with admin privilege using vb script.
    """

    if is_administrator():
        return  # Return if already has privilege.

    if not pyfile:
        pyfile = sys.argv[0]
    execute_pyscript(pyfile)  # elevate python file.
    sys.exit(0)  # Exit the current script to prevent running below code.
