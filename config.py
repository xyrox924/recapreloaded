from pathlib import Path

# paths from root
# folders
PROJECT_ROOT = Path(__file__).parent
DBS_PATH = PROJECT_ROOT / "database"
ICONS_PATH = PROJECT_ROOT / "gui" / "icons"
BANNERS_PATH = PROJECT_ROOT / "gui" / "banners"

# individual files
DB_PATH = DBS_PATH / "recap.db"
ICON_PATH = ICONS_PATH / "favicon.ico"