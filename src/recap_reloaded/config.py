import sys

from pathlib import Path

regkey_name = "recapreloaded"

if getattr(sys, 'frozen', False): # for pyinstaller
    PROJECT_ROOT = Path(sys.executable).parent
    PACKAGE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / "recap_reloaded"
else:
    PACKAGE_ROOT = Path(__file__).resolve().parent
    PROJECT_ROOT = PACKAGE_ROOT.parents[1]

DBS_PATH = PROJECT_ROOT / "database"
BANNERS_PATH = PROJECT_ROOT / "gui" / "banners"
ICONS_PATH = PACKAGE_ROOT / "gui" / "icons"

# individual files
DB_PATH = DBS_PATH / "recap.db"
ICON_PATH = ICONS_PATH / "favicon.ico"
WIN2_ICON_PATH = ICONS_PATH / "win1.ico"
WIN1_ICON_PATH = ICONS_PATH / "win2.ico"
GAMETXT_PATH = PROJECT_ROOT / "game.txt"
