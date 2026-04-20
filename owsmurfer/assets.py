from pathlib import Path

from PySide6.QtGui import QIcon


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
IMG_DIR = PROJECT_ROOT / "img"
LOGO_PNG_PATH = IMG_DIR / "OW_Smurfer_logo.png"
ICON_ICO_PATH = IMG_DIR / "OW_Smurfer_logo.ico"


def load_app_icon():
    if ICON_ICO_PATH.exists():
        return QIcon(str(ICON_ICO_PATH))
    if LOGO_PNG_PATH.exists():
        return QIcon(str(LOGO_PNG_PATH))
    return QIcon()
