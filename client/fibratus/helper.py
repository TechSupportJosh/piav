import subprocess
import os
import psutil


def start_fibratus(executable_name):
    return subprocess.Popen(
        [
            "fibratus",
            "run",
            "ps.name = '{}' and kevt.category in ('net','file','registry')".format(
                executable_name
            ),
            "-f",
            "piav_kernel_capture",
            "--filament.path",
            os.path.join(os.getcwd(), "fibratus"),
        ],
        cwd=os.getcwd(),
    )


def kill_fibratus():
    # Kill old fibratus process
    for proc in psutil.process_iter():
        if proc.name() == "fibratus.exe":
            proc.kill()
            return True

    return False