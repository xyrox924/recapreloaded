# recap reloaded

Program for tracking game playtime. (ORIGINALIDEADONOTSTEAL!)

Add a game and the program will track whether it's on. When you exit the game it'll write the playtime to SQLite.

## Setup

Use a virtual environment:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
```

## Run

```bat
python main.py
```

The app runs in the system tray. Click the tray icon to open the window.

## Build

Build the Windows executable with PyInstaller:

```bat
pyinstaller "recap reloaded.spec"
```