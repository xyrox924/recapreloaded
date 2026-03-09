import sys

from pathlib import Path

regkey_name = "recapreloaded"

# paths from root
# folders
if getattr(sys, 'frozen', False): # for pyinstaller
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).parent

DBS_PATH = PROJECT_ROOT / "database"
ICONS_PATH = PROJECT_ROOT / "gui" / "icons"
BANNERS_PATH = PROJECT_ROOT / "gui" / "banners"

# individual files
DB_PATH = DBS_PATH / "recap.db"
ICON_PATH = ICONS_PATH / "favicon.ico"
WIN2_ICON_PATH = ICONS_PATH / "win1.ico"
WIN1_ICON_PATH = ICONS_PATH / "win2.ico"
GAMETXT_PATH = PROJECT_ROOT / "game.txt"