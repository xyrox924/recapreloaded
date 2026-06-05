import os

import psutil

def get_time_formatted(time):
    if time < 10800:
        return f"{int(time / 60)} minutes"
    else:
        return f"{(time / 3600):.1f} hours"

def normalize_exe_path(path: str):
    return os.path.normcase(os.path.abspath(path))

def get_running_processes():
    names = set()
    paths = set()
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            if proc.info["name"]:
                names.add(proc.info["name"].lower())
            if proc.info["exe"]:
                paths.add(normalize_exe_path(proc.info["exe"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return names, paths

def get_running_process_names():
    names = set()
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"]:
                names.add(proc.info["name"].lower())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return names
