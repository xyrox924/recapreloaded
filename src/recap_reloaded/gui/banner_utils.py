import shutil
from pathlib import Path
from uuid import uuid4

from recap_reloaded.config import BANNERS_PATH


def copy_banner_to_storage(source_path: str | Path) -> str:
    source = Path(source_path)
    BANNERS_PATH.mkdir(parents=True, exist_ok=True)

    while True:
        destination_name = f"{uuid4().hex}{source.suffix.lower()}"
        destination = BANNERS_PATH / destination_name
        if not destination.exists():
            break

    shutil.copy2(source, destination)
    return destination_name
