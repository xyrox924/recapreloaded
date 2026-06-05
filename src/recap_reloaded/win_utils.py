import sys
import winreg


def add_to_startup(app_name: str):
    if getattr(sys, "frozen", False):
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
    if getattr(sys, "frozen", False):
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
