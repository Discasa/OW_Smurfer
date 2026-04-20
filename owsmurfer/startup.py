import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows fallback
    winreg = None


APP_NAME = "OW_Smurfer"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAUNCHER_PATH = PROJECT_ROOT / "OW_Smurfer.py"


def is_startup_supported():
    return sys.platform.startswith("win") and winreg is not None


def _startup_command():
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'

    interpreter = Path(sys.executable).resolve()
    pythonw = interpreter.with_name("pythonw.exe")
    if pythonw.exists():
        interpreter = pythonw

    return f'"{interpreter}" "{LAUNCHER_PATH}"'


def is_startup_enabled():
    if not is_startup_supported():
        return False

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as registry_key:
            startup_command, _ = winreg.QueryValueEx(registry_key, APP_NAME)
    except FileNotFoundError:
        return False
    except OSError:
        return False

    return startup_command == _startup_command()


def set_startup_enabled(enabled):
    if not is_startup_supported():
        return False

    if enabled:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as registry_key:
            winreg.SetValueEx(registry_key, APP_NAME, 0, winreg.REG_SZ, _startup_command())
        return is_startup_enabled()

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as registry_key:
            winreg.DeleteValue(registry_key, APP_NAME)
    except FileNotFoundError:
        pass

    return is_startup_enabled()
