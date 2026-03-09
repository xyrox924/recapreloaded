import psutil
import winreg
import sys
import os

def get_time_formatted(time):
    if time < 10800:
        return f"{int(time / 60)} minutes"
    else:
        return f"{(time / 3600):.1f} hours"
    
def get_running_process_names():
    names = set()
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name']:
                names.add(proc.info['name'].lower())
                #print(proc.info['name'].lower())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return names

def add_to_startup(app_name: str):
    if getattr(sys, 'frozen', False): # for pyinstaller
        exe_path = sys.executable

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f"{exe_path}")
        winreg.CloseKey(key)
    else:
        print("not in pyinstaller form so not adding it to autostart registry")

def remove_from_startup(app_name: str):
    if getattr(sys, 'frozen', False): # for pyinstaller
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)
    else:
        print("not in pyinstaller form so not removing it to autostart registry")


def is_in_startup(app_name: str) -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False