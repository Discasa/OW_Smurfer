import ctypes
import base64
import json
import os
import sys
import threading
import time
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows fallback
    winreg = None

import keyboard
from PySide6.QtCore import QEasingCurve, QObject, QRectF, QSize, QSignalBlocker, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)


# ---- theme.py ----
class Palette:
    SURFACE = "#242426"
    SURFACE_RAISED = "#202124"
    SURFACE_PILL = "#282b2e"
    SURFACE_INTERACTIVE = "#2b2e31"
    SURFACE_ACTIVE = "#2a2c2f"
    SURFACE_DIVIDER = "#2c2f34"
    BORDER = "#45484d"
    TEXT_PRIMARY = "#d4d7dd"
    TEXT_MUTED = "#9aa0aa"
    TEXT_HINT = "#70757f"
    ACCENT = "#da8826"
    CLOSE = "#c7302b"


class Typography:
    WINDOW_TITLE = 15
    OVERLAY_TITLE = 13
    WINDOW_SUBTITLE = 10
    ACCOUNT_NAME = 12
    ACCOUNT_DETAIL = 10
    LOGIN_ACCOUNT = 14
    ACTION = 11
    HUD = 10


class FontFamily:
    UI = "Segoe UI"


class FontWeight:
    MEDIUM = 300
    SEMIBOLD = 500
    BOLD = 700


class Radius:
    SOFT = 10
    SMALL = 8
    BUTTON = 15
    CONTAINER = 18
    INTERACTIVE = 15
    PILL = 21


class Space:
    ZERO = 0
    SMALL = 4
    MID = 8
    LARGE = 10
    BIG = 12
    FRAME = 14


class Border:
    WIDTH = 1
    NONE = "none"
    TRANSPARENT = f"{WIDTH}px solid transparent"


class Size:
    MAIN_WINDOW = (480, 410)
    LOGIN_WINDOW_MIN_WIDTH = 300
    INPUT_DIALOG = (380, 150)
    CONFIRM_DIALOG = (380, 160)
    MODAL_CLOSE = (14, 14)
    MAIN_ACTION_BUTTON = (140, 48)
    HOTKEY_BUTTON = (218, 46)
    ACCOUNT_ROW_HEIGHT = 38
    LOGIN_ACCOUNT_BUTTON_HEIGHT = 64
    MODE_TOGGLE_HEIGHT = 56
    STARTUP_ROW = (218, 46)
    STARTUP_ROW_HEIGHT = 46
    DIALOG_CONFIRM_BUTTON = (90, 30)
    DIALOG_PRIMARY_BUTTON = (80, 30)
    SCROLLBAR_HANDLE_MIN = 28
    STARTUP_SWITCH_TRACK = (48, 26)
    STARTUP_SWITCH_HANDLE = 18
    TRAY_SWITCH_TRACK = (36, 20)
    TRAY_SWITCH_HANDLE = 14
    TRAY_MENU_BUTTON = (116, 38)


class Insets:
    NONE = (Space.ZERO, Space.ZERO, Space.ZERO, Space.ZERO)
    MAIN_WINDOW = (16, 16, 14, 16)
    OVERLAY = (Space.FRAME, Space.FRAME, Space.FRAME, Space.FRAME)
    MODAL = (Space.FRAME, Space.BIG, Space.FRAME, Space.BIG)
    ACCOUNT_ITEM = (16, 8, 16, 8)
    SETTING_ROW = (8, 10, 8, 10)
    STARTUP_ROW_CONTENT = (20, 8, 10, 8)
    MENU = (Space.SMALL, Space.SMALL, Space.SMALL, Space.SMALL)
    MENU_ITEM = (Space.SMALL, Space.LARGE, Space.SMALL, Space.LARGE)
    MENU_PILL_ITEM = (8, 24, 8, 24)
    MENU_PILL_MARGIN = (4, 6, 4, 6)
    MENU_BUTTON_ROW = (6, 5, 6, 5)
    MENU_SEPARATOR = (Space.SMALL, Space.LARGE, Space.SMALL, Space.LARGE)
    TRAY_TOGGLE_ROW = (Space.SMALL, Space.LARGE, Space.SMALL, Space.MID)


class Padding:
    BUTTON_BASE = (5, 12)
    BUTTON_DEFAULT = (5, 14)
    ACCOUNT_BUTTON = (9, 18)
    DIALOG_ACTION = (6, 12)
    MODE_TOGGLE = (3, 10)
    BATTLE_TAG_LABEL = (0, 0)


class Offset:
    BATTLE_TAG_HEIGHT = 6
    DETAILS_HEIGHT = Space.SMALL
    SWITCH_HANDLE = Space.SMALL
    TRAY_SWITCH_HANDLE = Space.SMALL


class Motion:
    BUTTON_HOVER_MS = 150
    SWITCH_TOGGLE_MS = 140


class Mode:
    ENTER = "enter"
    TAB = "tab"


@dataclass(frozen=True)
class HeaderPreset:
    title: str
    subtitle: str
    title_size: int
    subtitle_size: int
    show_close: bool = True


class HeaderTokens:
    LOGO_SIZE = 30
    LOGO_MIN_DIMENSION = 4
    LOGO_CROP = 1
    LOGO_FALLBACK_RADIUS = 15
    TITLE_COLOR = Palette.ACCENT
    TITLE_WEIGHT = FontWeight.BOLD
    SUBTITLE_COLOR = Palette.TEXT_PRIMARY
    SUBTITLE_LETTER_SPACING = 1
    CLOSE_SIZE = 16
    CLOSE_RADIUS = Radius.SMALL


class Headers:
    MAIN = HeaderPreset(
        title="OVERWATCH SMURFER",
        subtitle="ACCOUNT MANAGER",
        title_size=Typography.WINDOW_TITLE,
        subtitle_size=Typography.WINDOW_SUBTITLE,
    )
    LOGIN = HeaderPreset(
        title="SELECT ACCOUNT",
        subtitle="QUICK LOGIN",
        title_size=Typography.OVERLAY_TITLE,
        subtitle_size=Typography.WINDOW_SUBTITLE,
        show_close=False,
    )


class Text:
    MAIN_WINDOW_ADD = "ADD"
    MAIN_WINDOW_EDIT = "EDIT"
    MAIN_WINDOW_DELETE = "DELETE"
    HOTKEY_BUTTON = "HOTKEY: {hotkey}"
    HOTKEY_HINT = "ESC: CLOSE | {hotkey}: TOGGLE MODE"
    MODE_LABEL = "MODE:"
    MODE_SEPARATOR = "|"
    MODE_ENTER = "ENTER"
    MODE_TAB = "TAB"
    STARTUP_ROW_TITLE = "START WITH PC"
    TRAY_STARTUP_TITLE = "Start With Windows"
    MENU_SETTINGS = "Settings"
    MENU_EXIT = "Exit"
    DIALOG_CONFIRM_ACCEPT = "YES"
    DIALOG_INPUT_ACCEPT = "OK"
    FIELD_LABEL_TEMPLATE = "{label}:"
    FIELD_EMAIL = "Email"
    FIELD_PASSWORD = "Password"
    FIELD_BATTLETAG = "Battletag"
    FIELD_SHORTCUT = "Shortcut"
    TITLE_NEW_ACCOUNT = "New Account"
    TITLE_EDIT_ACCOUNT = "Edit"
    TITLE_DELETE_ACCOUNT = "Delete Account"
    TITLE_HOTKEY = "Hotkey"
    DELETE_ACCOUNT_PROMPT = "Delete account {battle_tag}?"


UNITLESS_CSS_RULES = {"font_weight"}


def _css_value(rule_name, value):
    if isinstance(value, (tuple, list)):
        return " ".join(_css_value(rule_name, part) for part in value)
    if isinstance(value, int):
        if rule_name in UNITLESS_CSS_RULES:
            return str(value)
        return f"{value}px"
    return str(value)


def style_rules(**rules):
    return "; ".join(
        f"{name.replace('_', '-')}: {_css_value(name, value)}"
        for name, value in rules.items()
        if value is not None
    ) + ";"


def qss_block(selector, **rules):
    return f"{selector} {{ {style_rules(**rules)} }}"


def solid_border(color, width=Border.WIDTH):
    return f"{width}px solid {color}"


def label_style(color=Palette.TEXT_PRIMARY, size=Typography.HUD, weight=None, letter_spacing=None):
    return style_rules(
        color=color,
        font_size=size,
        font_weight=weight,
        letter_spacing=letter_spacing,
        border=Border.NONE,
        background="transparent",
    )


def frame_style(background, radius, border_color=Palette.BORDER):
    return style_rules(
        background_color=background,
        border_radius=radius,
        border=solid_border(border_color),
    )


def input_style():
    return style_rules(
        background=Palette.SURFACE,
        color=Palette.TEXT_PRIMARY,
        border=solid_border(Palette.BORDER),
        border_radius=Radius.SOFT,
        padding=Space.MID,
    )


def close_button_style(radius):
    return style_rules(
        background_color=Palette.CLOSE,
        border_radius=radius,
        border=Border.NONE,
    )


def transparent_style():
    return style_rules(background="transparent", border=Border.NONE)


def menu_style():
    return "\n".join([
        qss_block(
            "QMenu",
            background_color=Palette.SURFACE,
            color=Palette.TEXT_MUTED,
            border=solid_border(Palette.BORDER),
            border_radius=Radius.CONTAINER,
            padding=Insets.MENU,
        ),
        qss_block(
            "QMenu::item",
            color=Palette.TEXT_MUTED,
            background_color=Palette.SURFACE_RAISED,
            border=solid_border(Palette.BORDER),
            padding=Insets.MENU_PILL_ITEM,
            margin=Insets.MENU_PILL_MARGIN,
            border_radius=Radius.PILL,
        ),
        qss_block(
            "QMenu::item:selected",
            background_color=Palette.SURFACE_INTERACTIVE,
            color=Palette.TEXT_PRIMARY,
            border=solid_border(Palette.BORDER),
        ),
        qss_block(
            "QMenu::separator",
            height=Border.WIDTH,
            background=Palette.SURFACE_DIVIDER,
            margin=Insets.MENU_SEPARATOR,
        ),
    ])


def scrollbar_style(width=Space.MID):
    handle_radius = max(Space.SMALL, width // 2)
    return "\n".join([
        qss_block(
            "QScrollBar:vertical",
            background=Palette.SURFACE,
            width=width,
            margin=Space.ZERO,
            border=Border.NONE,
        ),
        qss_block(
            "QScrollBar::handle:vertical",
            background=Palette.BORDER,
            min_height=Size.SCROLLBAR_HANDLE_MIN,
            border_radius=handle_radius,
            border=Border.NONE,
        ),
        qss_block(
            "QScrollBar::handle:vertical:hover",
            background=Palette.TEXT_HINT,
            border=Border.NONE,
        ),
        qss_block("QScrollBar::groove:vertical", background="transparent", border=Border.NONE, margin=Space.ZERO),
        qss_block("QScrollBar::add-line:vertical", height=Space.ZERO, width=Space.ZERO, margin=Space.ZERO, padding=Space.ZERO, background=Palette.SURFACE, border=Border.NONE),
        qss_block("QScrollBar::sub-line:vertical", height=Space.ZERO, width=Space.ZERO, margin=Space.ZERO, padding=Space.ZERO, background=Palette.SURFACE, border=Border.NONE),
        qss_block("QScrollBar::up-arrow:vertical", height=Space.ZERO, width=Space.ZERO, background="transparent"),
        qss_block("QScrollBar::down-arrow:vertical", height=Space.ZERO, width=Space.ZERO, background="transparent"),
        qss_block("QScrollBar::add-page:vertical", background=Palette.SURFACE, margin=Space.ZERO, border=Border.NONE),
        qss_block("QScrollBar::sub-page:vertical", background=Palette.SURFACE, margin=Space.ZERO, border=Border.NONE),
        qss_block(
            "QScrollBar:horizontal",
            background=Palette.SURFACE,
            height=width,
            margin=Space.ZERO,
            border=Border.NONE,
        ),
        qss_block(
            "QScrollBar::handle:horizontal",
            background=Palette.BORDER,
            min_width=Size.SCROLLBAR_HANDLE_MIN,
            border_radius=handle_radius,
            border=Border.NONE,
        ),
        qss_block(
            "QScrollBar::handle:horizontal:hover",
            background=Palette.TEXT_HINT,
            border=Border.NONE,
        ),
        qss_block("QScrollBar::groove:horizontal", background="transparent", border=Border.NONE, margin=Space.ZERO),
        qss_block("QScrollBar::add-line:horizontal", height=Space.ZERO, width=Space.ZERO, margin=Space.ZERO, padding=Space.ZERO, background=Palette.SURFACE, border=Border.NONE),
        qss_block("QScrollBar::sub-line:horizontal", height=Space.ZERO, width=Space.ZERO, margin=Space.ZERO, padding=Space.ZERO, background=Palette.SURFACE, border=Border.NONE),
        qss_block("QScrollBar::left-arrow:horizontal", height=Space.ZERO, width=Space.ZERO, background="transparent"),
        qss_block("QScrollBar::right-arrow:horizontal", height=Space.ZERO, width=Space.ZERO, background="transparent"),
        qss_block("QScrollBar::add-page:horizontal", background=Palette.SURFACE, margin=Space.ZERO, border=Border.NONE),
        qss_block("QScrollBar::sub-page:horizontal", background=Palette.SURFACE, margin=Space.ZERO, border=Border.NONE),
    ])


def list_widget_style():
    return "\n".join([
        qss_block("QListWidget", background="transparent", border=Border.NONE, outline=Border.NONE),
        qss_block("QAbstractScrollArea", background="transparent", border=Border.NONE, outline=Border.NONE),
        qss_block("QAbstractScrollArea::corner", background=Palette.SURFACE, border=Border.NONE),
        qss_block("QListWidget::item", background="transparent", border=Border.NONE, outline=Border.NONE),
        qss_block("QListWidget::item:hover", background="transparent", border=Border.NONE),
        qss_block("QListWidget::item:selected", background="transparent", border=Border.NONE),
        qss_block("QListWidget::item:selected:hover", background="transparent", border=Border.NONE),
        scrollbar_style(),
    ])


# ---- config.py ----
LOCAL_APPDATA = os.getenv("LOCALAPPDATA")
APPDATA_PATH = Path(LOCAL_APPDATA) / "OW_Smurfer" if LOCAL_APPDATA else Path.home() / ".owsmurfer"
CONFIG_FILE = APPDATA_PATH / "config.json"
DEFAULT_CONFIG = {"accounts": [], "hotkey": "ctrl+l", "mode": Mode.ENTER}
VALID_MODES = {Mode.ENTER, Mode.TAB}
ACCOUNTS_DATA_KEY = "accounts_data"
OBFUSCATION_PREFIX = "ow1:"
OBFUSCATION_KEY = b"OW_Smurfer portable config"

APPDATA_PATH.mkdir(parents=True, exist_ok=True)


def default_config():
    return deepcopy(DEFAULT_CONFIG)


def normalize_account(raw_account):
    if not isinstance(raw_account, dict):
        return None

    email = raw_account.get("email", "")
    password = raw_account.get("password", "")
    battle_tag = raw_account.get("battle_tag", "")

    if not all(isinstance(value, str) for value in (email, password, battle_tag)):
        return None

    return {
        "email": email,
        "password": password,
        "battle_tag": battle_tag,
    }


def normalized_accounts(raw_accounts):
    if not isinstance(raw_accounts, list):
        return []

    return [
        normalized_account
        for account in raw_accounts
        for normalized_account in [normalize_account(account)]
        if normalized_account is not None
    ]


def xor_bytes(data):
    return bytes(
        byte ^ OBFUSCATION_KEY[index % len(OBFUSCATION_KEY)]
        for index, byte in enumerate(data)
    )


def encode_accounts(accounts):
    payload = json.dumps(
        normalized_accounts(accounts),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(xor_bytes(payload)).decode("ascii")
    return f"{OBFUSCATION_PREFIX}{encoded_payload}"


def decode_accounts(encoded_accounts):
    if not isinstance(encoded_accounts, str) or not encoded_accounts.startswith(OBFUSCATION_PREFIX):
        return []

    try:
        encoded_payload = encoded_accounts[len(OBFUSCATION_PREFIX):].encode("ascii")
        payload = xor_bytes(base64.urlsafe_b64decode(encoded_payload))
        decoded_accounts = json.loads(payload.decode("utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return []

    return normalized_accounts(decoded_accounts)


def load_config():
    if not CONFIG_FILE.exists():
        return default_config()

    try:
        raw_config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_config()

    if not isinstance(raw_config, dict):
        return default_config()

    validated_config = default_config()
    if ACCOUNTS_DATA_KEY in raw_config:
        validated_config["accounts"] = decode_accounts(raw_config.get(ACCOUNTS_DATA_KEY))
    else:
        validated_config["accounts"] = raw_config.get("accounts", DEFAULT_CONFIG["accounts"])
    validated_config["hotkey"] = raw_config.get("hotkey", DEFAULT_CONFIG["hotkey"])
    validated_config["mode"] = raw_config.get("mode", DEFAULT_CONFIG["mode"])

    validated_config["accounts"] = normalized_accounts(validated_config["accounts"])

    if not isinstance(validated_config["hotkey"], str) or not validated_config["hotkey"].strip():
        validated_config["hotkey"] = DEFAULT_CONFIG["hotkey"]
    if validated_config["mode"] not in VALID_MODES:
        validated_config["mode"] = DEFAULT_CONFIG["mode"]

    if ACCOUNTS_DATA_KEY not in raw_config:
        save_config(validated_config)

    return validated_config


def save_config(config_data):
    stored_config = {
        "hotkey": config_data.get("hotkey", DEFAULT_CONFIG["hotkey"]),
        "mode": config_data.get("mode", DEFAULT_CONFIG["mode"]),
        ACCOUNTS_DATA_KEY: encode_accounts(config_data.get("accounts", [])),
    }
    CONFIG_FILE.write_text(json.dumps(stored_config, indent=4), encoding="utf-8")


# ---- core.py ----
PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = PROJECT_ROOT
IMG_DIR = PROJECT_ROOT / "img"
LOGO_PNG_PATH = IMG_DIR / "OW_Smurfer_logo.png"
ICON_ICO_PATH = IMG_DIR / "OW_Smurfer_logo.ico"

APP_NAME = "OW_Smurfer"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
LAUNCHER_PATH = PROJECT_ROOT / "OW_Smurfer.py"


def load_app_icon():
    if ICON_ICO_PATH.exists():
        return QIcon(str(ICON_ICO_PATH))
    if LOGO_PNG_PATH.exists():
        return QIcon(str(LOGO_PNG_PATH))
    return QIcon()


def center(widget):
    screen = QApplication.primaryScreen()
    center_on_screen(widget, screen)


def center_on_cursor_screen(widget):
    screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
    center_on_screen(widget, screen)


def center_on_screen(widget, screen):
    if screen is None:
        return

    window_geometry = widget.frameGeometry()
    window_geometry.moveCenter(screen.geometry().center())
    widget.move(window_geometry.topLeft())


def force_window_topmost(widget):
    if not sys.platform.startswith("win"):
        return

    try:
        hwnd = int(widget.winId())
        hwnd_topmost = -1
        swp_nosize = 0x0001
        swp_nomove = 0x0002
        swp_showwindow = 0x0040
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            hwnd_topmost,
            0,
            0,
            0,
            0,
            swp_nomove | swp_nosize | swp_showwindow,
        )
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception as error:
        print(f"Topmost window error: {error}")


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


class HotkeyBridge(QObject):
    triggered = Signal()
    escape_requested = Signal()


class DragBehaviorMixin:
    def _init_drag_behavior(self):
        self._drag_offset = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class DraggableWindow(DragBehaviorMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._init_drag_behavior()


class DraggableDialog(DragBehaviorMixin, QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._init_drag_behavior()


# ---- widgets.py ----
class AnimatedButton(QPushButton):
    def __init__(
        self,
        text="",
        parent=None,
        *,
        background_color=Palette.SURFACE_RAISED,
        hover_background_color=Palette.SURFACE_INTERACTIVE,
        text_color=Palette.TEXT_MUTED,
        hover_text_color=Palette.TEXT_PRIMARY,
        border_color=Palette.BORDER,
        hover_border_color=None,
        radius=Radius.BUTTON,
        font_size=Typography.ACTION,
        font_weight=FontWeight.MEDIUM,
        padding=Padding.BUTTON_BASE,
    ):
        super().__init__(text, parent)
        self._base_background_color = QColor(background_color)
        self._hover_background_color = QColor(hover_background_color)
        self._base_text_color = QColor(text_color)
        self._hover_text_color = QColor(hover_text_color)
        self._base_border_color = QColor(border_color)
        self._hover_border_color = QColor(hover_border_color or border_color)
        self._radius = radius
        self._font_size = font_size
        self._font_weight = font_weight
        self._padding = padding
        self._animation_progress = 0.0

        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFlat(True)

        self._hover_animation = QVariantAnimation(self)
        self._hover_animation.setDuration(Motion.BUTTON_HOVER_MS)
        self._hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._hover_animation.valueChanged.connect(self._on_value_changed)
        self._apply_style(0.0)

    def _blend(self, start, end, progress):
        return QColor(
            int(start.red() + (end.red() - start.red()) * progress),
            int(start.green() + (end.green() - start.green()) * progress),
            int(start.blue() + (end.blue() - start.blue()) * progress),
        )

    def _apply_style(self, animation_progress):
        self.update()

    def _animate_to(self, target_progress):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._animation_progress)
        self._hover_animation.setEndValue(target_progress)
        self._hover_animation.start()

    def _on_value_changed(self, animation_value):
        self._animation_progress = float(animation_value)
        self._apply_style(self._animation_progress)

    def sizeHint(self):
        font = QFont(self.font())
        font.setPixelSize(self._font_size)
        font.setWeight(QFont.Weight(self._font_weight))
        metrics = QFontMetrics(font)
        vertical_padding, horizontal_padding = self._padding
        width = metrics.horizontalAdvance(self.text()) + (horizontal_padding * 2) + (Border.WIDTH * 2)
        height = metrics.height() + (vertical_padding * 2) + (Border.WIDTH * 2)
        return QSize(width, height)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        del event

        background_color = self._blend(self._base_background_color, self._hover_background_color, self._animation_progress)
        text_color = self._blend(self._base_text_color, self._hover_text_color, self._animation_progress)
        border_color = self._blend(self._base_border_color, self._hover_border_color, self._animation_progress)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(
            Border.WIDTH / 2,
            Border.WIDTH / 2,
            -(Border.WIDTH / 2),
            -(Border.WIDTH / 2),
        )
        painter.setPen(QPen(border_color, Border.WIDTH))
        painter.setBrush(background_color)
        painter.drawRoundedRect(rect, self._radius, self._radius)

        font = QFont(self.font())
        font.setPixelSize(self._font_size)
        font.setWeight(QFont.Weight(self._font_weight))
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

    def enterEvent(self, event):
        self._animate_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_to(0.0)
        super().leaveEvent(event)


def themed_button(text="", parent=None, **overrides):
    options = {
        "background_color": Palette.SURFACE_RAISED,
        "hover_background_color": Palette.SURFACE_INTERACTIVE,
        "text_color": Palette.TEXT_MUTED,
        "hover_text_color": Palette.TEXT_PRIMARY,
        "border_color": Palette.BORDER,
        "hover_border_color": Palette.BORDER,
        "radius": Radius.BUTTON,
        "font_size": Typography.ACTION,
        "padding": Padding.BUTTON_DEFAULT,
    }
    options.update(overrides)
    return AnimatedButton(text, parent, **options)


class HeaderWidget(QWidget):
    def __init__(self, preset, parent=None):
        super().__init__(parent)
        header_layout = QHBoxLayout(self)
        header_layout.setContentsMargins(*Insets.NONE)
        header_layout.setSpacing(Space.MID)

        logo_label = QLabel()
        logo_label.setFixedSize(HeaderTokens.LOGO_SIZE, HeaderTokens.LOGO_SIZE)
        logo_label.setStyleSheet(transparent_style())

        logo_pixmap = QPixmap(str(LOGO_PNG_PATH))
        if not logo_pixmap.isNull():
            if logo_pixmap.width() > HeaderTokens.LOGO_MIN_DIMENSION and logo_pixmap.height() > HeaderTokens.LOGO_MIN_DIMENSION:
                crop_margin = HeaderTokens.LOGO_CROP
                logo_pixmap = logo_pixmap.copy(
                    crop_margin,
                    crop_margin,
                    logo_pixmap.width() - (crop_margin * 2),
                    logo_pixmap.height() - (crop_margin * 2),
                )
            logo_label.setPixmap(logo_pixmap.scaled(
                HeaderTokens.LOGO_SIZE,
                HeaderTokens.LOGO_SIZE,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            ))
        else:
            logo_label.setStyleSheet(style_rules(
                background_color=HeaderTokens.TITLE_COLOR,
                border_radius=HeaderTokens.LOGO_FALLBACK_RADIUS,
                border=Border.NONE,
            ))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(Space.ZERO)

        title_label = QLabel(preset.title)
        title_label.setStyleSheet(label_style(
            color=HeaderTokens.TITLE_COLOR,
            size=preset.title_size,
            weight=HeaderTokens.TITLE_WEIGHT,
        ))

        subtitle_label = QLabel(preset.subtitle)
        subtitle_letter_spacing = self._subtitle_letter_spacing(preset)
        subtitle_label.setStyleSheet(label_style(
            color=HeaderTokens.SUBTITLE_COLOR,
            size=preset.subtitle_size,
            letter_spacing=subtitle_letter_spacing,
        ))

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        header_layout.addWidget(logo_label)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        if preset.show_close:
            close_button = QPushButton()
            close_button.setFixedSize(HeaderTokens.CLOSE_SIZE, HeaderTokens.CLOSE_SIZE)
            close_button.setCursor(Qt.PointingHandCursor)
            close_button.setFocusPolicy(Qt.NoFocus)
            close_button.setStyleSheet(close_button_style(HeaderTokens.CLOSE_RADIUS))
            close_button.clicked.connect(lambda: self.window().hide())
            header_layout.addWidget(close_button, alignment=Qt.AlignTop)

    def _subtitle_letter_spacing(self, preset):
        title_font = QFont(self.font())
        title_font.setPixelSize(preset.title_size)
        title_font.setWeight(QFont.Weight(HeaderTokens.TITLE_WEIGHT))

        subtitle_font = QFont(self.font())
        subtitle_font.setPixelSize(preset.subtitle_size)

        title_width = QFontMetrics(title_font).horizontalAdvance(preset.title)
        subtitle_width = QFontMetrics(subtitle_font).horizontalAdvance(preset.subtitle)
        letter_gaps = max(1, len(preset.subtitle) - 1)
        needed_spacing = round((title_width - subtitle_width) / letter_gaps)
        return max(HeaderTokens.SUBTITLE_LETTER_SPACING, needed_spacing)


class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None, *, elide_mode=Qt.ElideRight):
        super().__init__(parent)
        self._full_text = ""
        self._elide_mode = elide_mode
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setText(text)

    def setText(self, text):
        self._full_text = text
        self.setToolTip(text)
        self._refresh_elide()

    def setFont(self, font):
        super().setFont(font)
        self._refresh_elide()

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_elide()

    def _refresh_elide(self):
        available_width = self.width()
        if available_width <= 0:
            visible_text = self._full_text
        else:
            visible_text = self.fontMetrics().elidedText(self._full_text, self._elide_mode, available_width)

        if QLabel.text(self) != visible_text:
            QLabel.setText(self, visible_text)


class AccountItemWidget(QWidget):
    def __init__(self, battle_tag, email, parent=None):
        super().__init__(parent)
        self._is_selected = False
        self._is_hovered = False
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(Size.ACCOUNT_ROW_HEIGHT)

        content_layout = QHBoxLayout(self)
        content_layout.setContentsMargins(*Insets.ACCOUNT_ITEM)
        content_layout.setSpacing(Space.LARGE)

        self.battle_tag_label = ElidedLabel(battle_tag)
        self.battle_tag_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.account_details_label = ElidedLabel(email)
        self.account_details_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._apply_fonts()
        self._battle_tag_label_style = label_style(
            color=Palette.ACCENT,
            size=Typography.ACCOUNT_NAME,
            weight=FontWeight.SEMIBOLD,
        ) + style_rules(
            padding_top=Padding.BATTLE_TAG_LABEL[0],
            padding_bottom=Padding.BATTLE_TAG_LABEL[1],
        )
        self._details_label_styles = {
            True: label_style(color=Palette.TEXT_PRIMARY, size=Typography.ACCOUNT_DETAIL),
            False: label_style(color=Palette.TEXT_MUTED, size=Typography.ACCOUNT_DETAIL),
        }

        content_layout.addWidget(self.battle_tag_label, 2)
        content_layout.addWidget(self.account_details_label, 3)
        self.update_selection_state(False)

    def _apply_fonts(self):
        battle_tag_font = QFont(self.battle_tag_label.font())
        battle_tag_font.setPixelSize(Typography.ACCOUNT_NAME)
        battle_tag_font.setWeight(QFont.Weight(FontWeight.SEMIBOLD))
        self.battle_tag_label.setFont(battle_tag_font)
        self.battle_tag_label.setFixedHeight(QFontMetrics(battle_tag_font).height() + 2)

        details_font = QFont(self.account_details_label.font())
        details_font.setPixelSize(Typography.ACCOUNT_DETAIL)
        self.account_details_label.setFont(details_font)
        self.account_details_label.setFixedHeight(QFontMetrics(details_font).height() + 2)

    def item_height(self):
        return Size.ACCOUNT_ROW_HEIGHT

    def update_selection_state(self, selected):
        self._is_selected = selected
        self._apply_surface_style()
        self.battle_tag_label.setStyleSheet(self._battle_tag_label_style)
        self.account_details_label.setStyleSheet(self._details_label_styles[selected])

    def enterEvent(self, event):
        self._is_hovered = True
        self._apply_surface_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._apply_surface_style()
        super().leaveEvent(event)

    def _apply_surface_style(self):
        if self._is_selected:
            background_color = Palette.SURFACE_INTERACTIVE
            border_color = Palette.ACCENT
        elif self._is_hovered:
            background_color = Palette.SURFACE_ACTIVE
            border_color = Palette.BORDER
        else:
            background_color = Palette.SURFACE_PILL
            border_color = Palette.SURFACE_DIVIDER

        self.setStyleSheet(style_rules(
            background_color=background_color,
            border=Border.TRANSPARENT if not self._is_selected else f"{Border.WIDTH}px solid {border_color}",
            border_radius=Size.ACCOUNT_ROW_HEIGHT // 2,
        ))


class ModeToggle(QFrame):
    toggled = Signal(str)

    def __init__(self, current):
        super().__init__()
        self.setFixedHeight(Size.MODE_TOGGLE_HEIGHT)
        self.setStyleSheet(style_rules(
            background_color=Palette.SURFACE_RAISED,
            border=solid_border(Palette.BORDER),
            border_radius=Size.MODE_TOGGLE_HEIGHT // 2,
        ))

        toggle_layout = QHBoxLayout(self)
        toggle_layout.setAlignment(Qt.AlignCenter)
        toggle_layout.setContentsMargins(14, 8, 14, 8)
        toggle_layout.setSpacing(Space.SMALL)

        mode_label = QLabel(Text.MODE_LABEL)
        mode_label.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.HUD, weight=FontWeight.SEMIBOLD))

        self.enter_button = QPushButton(Text.MODE_ENTER)
        self.tab_button = QPushButton(Text.MODE_TAB)
        separator_label = QLabel(Text.MODE_SEPARATOR)
        separator_label.setStyleSheet(label_style(color=Palette.BORDER, size=Typography.HUD, weight=FontWeight.SEMIBOLD))

        for mode_button in (self.enter_button, self.tab_button):
            mode_button.setFlat(True)
            mode_button.setCursor(Qt.PointingHandCursor)
            mode_button.setFocusPolicy(Qt.NoFocus)
            mode_button.clicked.connect(self._handle_click)

        self._stabilize_button_widths()

        toggle_layout.addWidget(mode_label)
        toggle_layout.addWidget(self.enter_button)
        toggle_layout.addWidget(separator_label)
        toggle_layout.addWidget(self.tab_button)

        self.update_mode_styles(current)

    def _stabilize_button_widths(self):
        for mode_button in (self.enter_button, self.tab_button):
            base_font = QFont(mode_button.font())
            base_font.setPointSize(Typography.HUD)
            base_font.setBold(False)

            active_font = QFont(base_font)
            active_font.setBold(True)

            normal_width = QFontMetrics(base_font).horizontalAdvance(mode_button.text())
            active_width = QFontMetrics(active_font).horizontalAdvance(mode_button.text())
            mode_button.setFixedWidth(max(normal_width, active_width) + 22)
            mode_button.setFixedHeight(26)

    def _handle_click(self):
        selected_mode = Mode.ENTER if self.sender() == self.enter_button else Mode.TAB
        self.update_mode_styles(selected_mode)
        self.toggled.emit(selected_mode)

    def update_mode_styles(self, selected_mode):
        active_stylesheet = style_rules(
            color=Palette.ACCENT,
            font_weight=FontWeight.BOLD,
            font_size=Typography.HUD,
            border=f"{Border.WIDTH}px solid {Palette.BORDER}",
            background=Palette.SURFACE_INTERACTIVE,
            border_radius=13,
            outline=Border.NONE,
            padding=Padding.MODE_TOGGLE,
        )
        inactive_stylesheet = style_rules(
            color=Palette.TEXT_MUTED,
            font_size=Typography.HUD,
            border=Border.NONE,
            background="transparent",
            outline=Border.NONE,
            padding=Padding.MODE_TOGGLE,
        )

        self.enter_button.setStyleSheet(active_stylesheet if selected_mode == Mode.ENTER else inactive_stylesheet)
        self.tab_button.setStyleSheet(active_stylesheet if selected_mode == Mode.TAB else inactive_stylesheet)


class SwitchToggle(QAbstractButton):
    def __init__(
        self,
        checked=False,
        parent=None,
        *,
        track_size=None,
        handle_size=None,
        handle_offset=None,
        track_radius=None,
    ):
        super().__init__(parent)
        self._track_size = track_size or Size.STARTUP_SWITCH_TRACK
        self._handle_size = handle_size or Size.STARTUP_SWITCH_HANDLE
        self._handle_offset = Offset.SWITCH_HANDLE if handle_offset is None else handle_offset
        self._track_radius = self._track_size[1] // 2 if track_radius is None else track_radius
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(*self._track_size)

        self._handle_position = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(Motion.SWITCH_TOGGLE_MS)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._on_value_changed)
        self.toggled.connect(self._animate_to_state)

        self.set_checked_state(checked)

    def sizeHint(self):
        return QSize(*self._track_size)

    def _min_offset(self):
        return self._handle_offset

    def _max_offset(self):
        return self.width() - self._handle_offset - self._handle_size

    def _target_offset(self, checked):
        return self._max_offset() if checked else self._min_offset()

    def _on_value_changed(self, value):
        self._handle_position = float(value)
        self.update()

    def _animate_to_state(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._handle_position)
        self._animation.setEndValue(self._target_offset(checked))
        self._animation.start()

    def set_checked_state(self, checked):
        with QSignalBlocker(self):
            self.setChecked(bool(checked))
        self._animation.stop()
        self._handle_position = float(self._target_offset(self.isChecked()))
        self.update()

    def paintEvent(self, event):
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.isEnabled():
            track_color = Palette.ACCENT if self.isChecked() else Palette.SURFACE_INTERACTIVE
            border_color = Palette.ACCENT if self.isChecked() else Palette.BORDER
            handle_color = Palette.TEXT_PRIMARY
        else:
            track_color = Palette.SURFACE
            border_color = Palette.BORDER
            handle_color = Palette.TEXT_MUTED

        track_rect = QRectF(
            Border.WIDTH / 2,
            Border.WIDTH / 2,
            self.width() - Border.WIDTH,
            self.height() - Border.WIDTH,
        )
        painter.setPen(QPen(QColor(border_color), Border.WIDTH))
        painter.setBrush(QColor(track_color))
        painter.drawRoundedRect(track_rect, self._track_radius, self._track_radius)

        handle_rect = QRectF(
            self._handle_position,
            self._handle_offset,
            self._handle_size,
            self._handle_size,
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(handle_color))
        painter.drawEllipse(handle_rect)


class StartupToggleRow(QFrame):
    toggled = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(Size.STARTUP_ROW_HEIGHT)
        self.setStyleSheet(frame_style(Palette.SURFACE_RAISED, Size.STARTUP_ROW_HEIGHT // 2))

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(*Insets.STARTUP_ROW_CONTENT)
        row_layout.setSpacing(Space.LARGE)

        startup_title_label = QLabel(Text.STARTUP_ROW_TITLE)
        startup_title_label.setStyleSheet(label_style(
            color=Palette.TEXT_MUTED,
            size=Typography.ACTION,
            weight=FontWeight.MEDIUM,
        ))

        self.switch_toggle = SwitchToggle(checked)
        self.switch_toggle.toggled.connect(self.toggled.emit)

        row_layout.addWidget(startup_title_label, 1, alignment=Qt.AlignVCenter)
        row_layout.addWidget(self.switch_toggle, alignment=Qt.AlignVCenter)

    def set_checked(self, checked):
        self.switch_toggle.set_checked_state(checked)

    def set_toggle_enabled(self, enabled):
        self.switch_toggle.setEnabled(enabled)


# ---- windows.py ----
def build_modal_frame(dialog):
    modal_frame = QFrame(dialog)
    modal_frame.resize(dialog.size())
    modal_frame.setStyleSheet(frame_style(Palette.SURFACE, Radius.CONTAINER))

    modal_layout = QVBoxLayout(modal_frame)
    modal_layout.setContentsMargins(*Insets.MODAL)
    return modal_frame, modal_layout


def build_modal_header(title, close_callback):
    header_layout = QHBoxLayout()

    title_label = QLabel(title.upper())
    title_label.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.HUD, weight=FontWeight.BOLD))

    close_button = QPushButton()
    close_button.setFixedSize(*Size.MODAL_CLOSE)
    close_button.setCursor(Qt.PointingHandCursor)
    close_button.setFocusPolicy(Qt.NoFocus)
    close_button.setStyleSheet(close_button_style(Radius.SMALL))
    close_button.clicked.connect(close_callback)

    header_layout.addWidget(title_label)
    header_layout.addStretch()
    header_layout.addWidget(close_button)
    return header_layout


class ConfirmDialog(DraggableDialog):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.setFixedSize(*Size.CONFIRM_DIALOG)
        self.confirmed = False

        _, dialog_layout = build_modal_frame(self)
        dialog_layout.addLayout(build_modal_header(title, self.reject))

        message_label = QLabel(message.upper())
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY))
        dialog_layout.addWidget(message_label, alignment=Qt.AlignCenter)

        button_row = QHBoxLayout()
        confirm_button = themed_button(
            Text.DIALOG_CONFIRM_ACCEPT,
            radius=Radius.BUTTON,
            font_size=Typography.ACTION,
            padding=Padding.DIALOG_ACTION,
            text_color=Palette.ACCENT,
            hover_text_color=Palette.TEXT_PRIMARY,
        )
        confirm_button.setFixedSize(*Size.DIALOG_CONFIRM_BUTTON)
        confirm_button.clicked.connect(self.accept_confirm)
        button_row.addStretch()
        button_row.addWidget(confirm_button)
        dialog_layout.addLayout(button_row)

    def accept_confirm(self):
        self.confirmed = True
        self.accept()


class CustomInputDialog(DraggableDialog):
    def __init__(self, parent, title, label_text, is_password=False, default_value=""):
        super().__init__(parent)
        self.setFixedSize(*Size.INPUT_DIALOG)
        self.entered_value = None

        _, dialog_layout = build_modal_frame(self)
        dialog_layout.addLayout(build_modal_header(title, self.reject))

        self.input_field = QLineEdit(default_value)
        if is_password:
            self.input_field.setEchoMode(QLineEdit.Password)
        self.input_field.setStyleSheet(input_style())

        field_label = QLabel(Text.FIELD_LABEL_TEMPLATE.format(label=label_text.upper()))
        field_label.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY))

        dialog_layout.addWidget(field_label)
        dialog_layout.addWidget(self.input_field)

        confirm_button = themed_button(
            Text.DIALOG_INPUT_ACCEPT,
            radius=Radius.BUTTON,
            font_size=Typography.ACTION,
            padding=Padding.DIALOG_ACTION,
        )
        confirm_button.setFixedSize(*Size.DIALOG_PRIMARY_BUTTON)
        confirm_button.clicked.connect(self.accept_input)
        dialog_layout.addWidget(confirm_button, alignment=Qt.AlignRight)

    def accept_input(self):
        self.entered_value = self.input_field.text()
        self.accept()


class LoginWindow(DraggableWindow):
    hidden = Signal()

    def __init__(self, config, login_callback, mode_callback):
        super().__init__()
        self.config = config
        self.login_callback = login_callback
        self.mode_callback = mode_callback

        panel_frame = QFrame(self)
        panel_frame.setMinimumWidth(Size.LOGIN_WINDOW_MIN_WIDTH)
        panel_frame.setStyleSheet(frame_style(Palette.SURFACE, Radius.CONTAINER))

        root_layout = QVBoxLayout(self)
        root_layout.addWidget(panel_frame)

        self.content_layout = QVBoxLayout(panel_frame)
        self.content_layout.setContentsMargins(*Insets.OVERLAY)
        self.content_layout.setSpacing(Space.BIG)
        self.mode_toggle = None

        self.refresh_ui()

    def _clear_content(self):
        while self.content_layout.count():
            layout_item = self.content_layout.takeAt(0)
            child_widget = layout_item.widget()
            if child_widget is not None:
                child_widget.deleteLater()

    def refresh_ui(self):
        self._clear_content()
        self.content_layout.addWidget(HeaderWidget(Headers.LOGIN))

        for account in self.config["accounts"]:
            account_button = themed_button(
                account["battle_tag"],
                text_color=Palette.TEXT_PRIMARY,
                radius=Size.LOGIN_ACCOUNT_BUTTON_HEIGHT // 2,
                font_size=Typography.LOGIN_ACCOUNT,
                font_weight=FontWeight.MEDIUM,
                padding=Padding.ACCOUNT_BUTTON,
            )
            account_button.setFixedHeight(Size.LOGIN_ACCOUNT_BUTTON_HEIGHT)
            account_button.clicked.connect(lambda _, selected=account: self.login_callback(selected))
            self.content_layout.addWidget(account_button)

        self.mode_toggle = ModeToggle(self.config.get("mode", DEFAULT_CONFIG["mode"]))
        self.mode_toggle.toggled.connect(self.mode_callback)
        self.content_layout.addWidget(self.mode_toggle)

        current_hotkey = self.config.get("hotkey", DEFAULT_CONFIG["hotkey"]).upper()
        hint_label = QLabel(Text.HOTKEY_HINT.format(hotkey=current_hotkey))
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet(label_style(color=Palette.TEXT_HINT, size=Typography.HUD))
        self.content_layout.addWidget(hint_label)

        self.adjustSize()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

    def hideEvent(self, event):
        self.hidden.emit()
        super().hideEvent(event)


class MainWindow(DraggableWindow):
    def __init__(self, config, save_callback, startup_enabled=False, on_startup_toggle=None, startup_supported=True):
        super().__init__()
        self.config = config
        self.save_callback = save_callback

        self.setFixedSize(*Size.MAIN_WINDOW)

        panel_frame = QFrame(self)
        panel_frame.resize(self.size())
        panel_frame.setStyleSheet(frame_style(Palette.SURFACE, Radius.CONTAINER))

        content_layout = QVBoxLayout(panel_frame)
        content_layout.setContentsMargins(*Insets.MAIN_WINDOW)
        content_layout.setSpacing(Space.LARGE)
        content_layout.addWidget(HeaderWidget(Headers.MAIN))

        self.account_list = QListWidget()
        self.account_list.setFocusPolicy(Qt.NoFocus)
        self.account_list.setFrameShape(QFrame.NoFrame)
        self.account_list.setSpacing(Space.SMALL)
        self.account_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.account_list.setStyleSheet(list_widget_style())
        self.account_list.itemSelectionChanged.connect(self.on_selection_change)
        content_layout.addWidget(self.account_list, 1)

        action_button_layout = QHBoxLayout()
        action_button_layout.setSpacing(10)
        for text, callback in [
            (Text.MAIN_WINDOW_ADD, self.add_account),
            (Text.MAIN_WINDOW_EDIT, self.edit_account),
            (Text.MAIN_WINDOW_DELETE, self.remove_account),
        ]:
            action_button = themed_button(text, radius=Size.MAIN_ACTION_BUTTON[1] // 2)
            action_button.setFixedSize(*Size.MAIN_ACTION_BUTTON)
            action_button.clicked.connect(callback)
            action_button_layout.addWidget(action_button)
        content_layout.addLayout(action_button_layout)

        self.hotkey_button = themed_button(radius=Size.HOTKEY_BUTTON[1] // 2)
        self.hotkey_button.setFixedSize(*Size.HOTKEY_BUTTON)
        self.hotkey_button.clicked.connect(self.change_hotkey)

        self.startup_toggle_row = StartupToggleRow(startup_enabled)
        self.startup_toggle_row.setFixedSize(*Size.STARTUP_ROW)
        if on_startup_toggle is not None:
            self.startup_toggle_row.toggled.connect(on_startup_toggle)
        self.startup_toggle_row.set_toggle_enabled(startup_supported)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(Space.ZERO)
        bottom_layout.addWidget(self.hotkey_button)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.startup_toggle_row)
        content_layout.addLayout(bottom_layout)

        self.refresh_hotkey()
        self.refresh_accounts()

    def hideEvent(self, event):
        self.account_list.clearSelection()
        self.account_list.setCurrentItem(None)
        self.on_selection_change()
        super().hideEvent(event)

    def refresh_accounts(self):
        self.account_list.clear()
        for account in self.config["accounts"]:
            account_item = QListWidgetItem()
            account_widget = AccountItemWidget(account["battle_tag"], account["email"])
            account_widget.ensurePolished()
            item_size = account_widget.sizeHint()
            item_size.setHeight(max(item_size.height(), account_widget.item_height()))
            account_item.setSizeHint(item_size)
            self.account_list.addItem(account_item)
            self.account_list.setItemWidget(account_item, account_widget)

    def on_selection_change(self):
        for row_index in range(self.account_list.count()):
            account_item = self.account_list.item(row_index)
            account_widget = self.account_list.itemWidget(account_item)
            if account_widget is not None:
                account_widget.update_selection_state(account_item.isSelected())

    def add_account(self):
        email_dialog = CustomInputDialog(self, Text.TITLE_NEW_ACCOUNT, Text.FIELD_EMAIL)
        if not email_dialog.exec() or not email_dialog.entered_value:
            return

        password_dialog = CustomInputDialog(self, Text.TITLE_NEW_ACCOUNT, Text.FIELD_PASSWORD, is_password=True)
        if not password_dialog.exec() or not password_dialog.entered_value:
            return

        battle_tag_dialog = CustomInputDialog(self, Text.TITLE_NEW_ACCOUNT, Text.FIELD_BATTLETAG)
        if not battle_tag_dialog.exec() or not battle_tag_dialog.entered_value:
            return

        self.config["accounts"].append({
            "email": email_dialog.entered_value,
            "password": password_dialog.entered_value,
            "battle_tag": battle_tag_dialog.entered_value,
        })
        self.persist_changes()

    def edit_account(self):
        selected_row = self.account_list.currentRow()
        if selected_row < 0:
            return

        account = self.config["accounts"][selected_row]
        email_dialog = CustomInputDialog(self, Text.TITLE_EDIT_ACCOUNT, Text.FIELD_EMAIL, default_value=account["email"])
        if not email_dialog.exec() or not email_dialog.entered_value:
            return

        password_dialog = CustomInputDialog(
            self,
            Text.TITLE_EDIT_ACCOUNT,
            Text.FIELD_PASSWORD,
            is_password=True,
            default_value=account["password"],
        )
        if not password_dialog.exec() or not password_dialog.entered_value:
            return

        battle_tag_dialog = CustomInputDialog(
            self,
            Text.TITLE_EDIT_ACCOUNT,
            Text.FIELD_BATTLETAG,
            default_value=account["battle_tag"],
        )
        if not battle_tag_dialog.exec() or not battle_tag_dialog.entered_value:
            return

        account.update({
            "email": email_dialog.entered_value,
            "password": password_dialog.entered_value,
            "battle_tag": battle_tag_dialog.entered_value,
        })
        self.persist_changes()

    def remove_account(self):
        selected_row = self.account_list.currentRow()
        if selected_row < 0:
            return

        battle_tag = self.config["accounts"][selected_row]["battle_tag"]
        confirm_dialog = ConfirmDialog(self, Text.TITLE_DELETE_ACCOUNT, Text.DELETE_ACCOUNT_PROMPT.format(battle_tag=battle_tag))
        if confirm_dialog.exec() and confirm_dialog.confirmed:
            self.config["accounts"].pop(selected_row)
            self.persist_changes()

    def change_hotkey(self):
        current_hotkey = self.config.get("hotkey", DEFAULT_CONFIG["hotkey"])
        hotkey_dialog = CustomInputDialog(self, Text.TITLE_HOTKEY, Text.FIELD_SHORTCUT, default_value=current_hotkey)
        if hotkey_dialog.exec() and hotkey_dialog.entered_value:
            self.config["hotkey"] = hotkey_dialog.entered_value
            self.persist_changes()

    def refresh_hotkey(self):
        current_hotkey = self.config.get("hotkey", DEFAULT_CONFIG["hotkey"]).upper()
        self.hotkey_button.setText(Text.HOTKEY_BUTTON.format(hotkey=current_hotkey))

    def set_startup_enabled(self, enabled):
        self.startup_toggle_row.set_checked(enabled)

    def set_startup_supported(self, supported):
        self.startup_toggle_row.set_toggle_enabled(supported)

    def persist_changes(self):
        save_config(self.config)
        self.save_callback()
        self.refresh_hotkey()
        self.refresh_accounts()


# ---- app.py ----
def run():
    application = QApplication(sys.argv)
    application.setFont(QFont(FontFamily.UI))
    application.setQuitOnLastWindowClosed(False)
    controller = AppController()
    application.controller = controller
    return application.exec()


class TrayStartupRow(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked=False, supported=True, parent=None):
        super().__init__(parent)
        self._is_hovered = False

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(*Insets.TRAY_TOGGLE_ROW)
        row_layout.setSpacing(Space.LARGE)

        self.startup_title_label = QLabel(Text.TRAY_STARTUP_TITLE)
        self.startup_title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.startup_toggle = SwitchToggle(
            checked,
            self,
            track_size=Size.TRAY_SWITCH_TRACK,
            handle_size=Size.TRAY_SWITCH_HANDLE,
            handle_offset=Offset.TRAY_SWITCH_HANDLE,
            track_radius=Radius.SOFT,
        )
        self.startup_toggle.toggled.connect(self.toggled.emit)

        row_layout.addWidget(self.startup_title_label, 1)
        row_layout.addWidget(self.startup_toggle, alignment=Qt.AlignVCenter)

        self.set_supported(supported)
        self._apply_style()

    def _apply_style(self):
        background_color = Palette.SURFACE_INTERACTIVE if self._is_hovered and self.isEnabled() else "transparent"
        self.setStyleSheet(style_rules(
            background_color=background_color,
            border_radius=Radius.SMALL,
            border=Border.NONE,
        ))
        self.startup_title_label.setStyleSheet(label_style(
            color=Palette.TEXT_PRIMARY if self.isEnabled() else Palette.TEXT_HINT,
            size=Typography.HUD,
            weight=FontWeight.MEDIUM,
        ))

    def enterEvent(self, event):
        self._is_hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled() and not self.startup_toggle.geometry().contains(event.pos()):
            self.startup_toggle.click()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def set_checked(self, checked):
        self.startup_toggle.set_checked_state(checked)

    def set_supported(self, supported):
        self.setEnabled(supported)
        self.startup_toggle.setEnabled(supported)
        self.setCursor(Qt.PointingHandCursor if supported else Qt.ArrowCursor)
        self._apply_style()


class TrayMenu(QObject):
    settings_requested = Signal()
    startup_toggled = Signal(bool)

    def __init__(self, startup_enabled=False, startup_supported=True, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(load_app_icon(), parent)
        self.tray_icon.activated.connect(self._on_activated)

        self.menu = QMenu()
        self.menu.setStyleSheet(menu_style())
        self._menu_actions = []

        self._add_menu_button(Text.MENU_SETTINGS, self.settings_requested.emit)
        self._add_menu_button(Text.MENU_EXIT, QApplication.quit)
        self.tray_icon.setContextMenu(self.menu)

    def _add_menu_button(self, text, callback):
        row_widget = QWidget(self.menu)
        row_widget.setStyleSheet(transparent_style())

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(*Insets.MENU_BUTTON_ROW)
        row_layout.setSpacing(Space.ZERO)

        button = themed_button(
            text,
            radius=Size.TRAY_MENU_BUTTON[1] // 2,
            font_size=Typography.ACTION,
            font_weight=FontWeight.MEDIUM,
            text_color=Palette.TEXT_MUTED,
            hover_text_color=Palette.TEXT_PRIMARY,
        )
        button.setFixedSize(*Size.TRAY_MENU_BUTTON)
        button.clicked.connect(lambda _, selected_callback=callback: self._trigger_menu_action(selected_callback))
        row_layout.addWidget(button)

        action = QWidgetAction(self.menu)
        action.setDefaultWidget(row_widget)
        self.menu.addAction(action)
        self._menu_actions.append(action)

    def _trigger_menu_action(self, callback):
        self.menu.hide()
        callback()

    def _on_activated(self, activation_reason):
        if activation_reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def _on_startup_toggled(self, enabled):
        self.startup_toggled.emit(enabled)

    def set_startup_enabled(self, enabled):
        del enabled

    def set_startup_supported(self, supported):
        del supported

    def show(self):
        self.tray_icon.show()


class AppController:
    def __init__(self):
        self.config = load_config()
        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.triggered.connect(self.handle_hotkey)
        self.hotkey_bridge.escape_requested.connect(self.handle_escape)

        self.login_window = LoginWindow(self.config, self.login, self.set_mode)
        self.login_window.hidden.connect(self.disable_login_escape)
        self.main_window = None
        self.escape_hotkey = None
        self.startup_supported = is_startup_supported()
        self.startup_enabled = is_startup_enabled() if self.startup_supported else False

        application = QApplication.instance()
        if application is not None:
            application.setWindowIcon(load_app_icon())

        self.tray_menu = TrayMenu(self.startup_enabled, self.startup_supported)
        self.tray_menu.settings_requested.connect(self.open_settings)
        self.tray_menu.startup_toggled.connect(self.set_startup_enabled)
        self.tray_menu.show()

        self.setup_hotkey()

    def handle_hotkey(self):
        if self.login_window.isVisible():
            toggled_mode = Mode.TAB if self.config["mode"] == Mode.ENTER else Mode.ENTER
            self.set_mode(toggled_mode)
            self.login_window.mode_toggle.update_mode_styles(toggled_mode)
            return

        self.login_window.refresh_ui()
        self.login_window.show()
        self.login_window.raise_()
        self.login_window.activateWindow()
        center_on_cursor_screen(self.login_window)
        force_window_topmost(self.login_window)
        self.enable_login_escape()

    def handle_escape(self):
        if self.login_window.isVisible():
            self.login_window.hide()

    def open_settings(self):
        if self.main_window is None:
            self.main_window = MainWindow(
                self.config,
                self.on_config_saved,
                startup_enabled=self.startup_enabled,
                on_startup_toggle=self.set_startup_enabled,
                startup_supported=self.startup_supported,
            )
        else:
            self.main_window.set_startup_enabled(self.startup_enabled)
            self.main_window.set_startup_supported(self.startup_supported)
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        center(self.main_window)
        force_window_topmost(self.main_window)

    def on_config_saved(self):
        self.setup_hotkey()
        self.login_window.refresh_ui()

    def _register_hotkey(self, hotkey, *, fallback=False):
        try:
            keyboard.add_hotkey(hotkey, self.hotkey_bridge.triggered.emit)
            return True
        except Exception as error:
            if fallback:
                print(f"Fallback hotkey error: {error}")
            else:
                print(f"Hotkey error for '{hotkey}': {error}")
            return False

    def setup_hotkey(self):
        keyboard.unhook_all()
        self.escape_hotkey = None
        configured_hotkey = self.config.get("hotkey", DEFAULT_CONFIG["hotkey"])

        if not self._register_hotkey(configured_hotkey) and configured_hotkey != DEFAULT_CONFIG["hotkey"]:
            self.config["hotkey"] = DEFAULT_CONFIG["hotkey"]
            save_config(self.config)
            self._register_hotkey(DEFAULT_CONFIG["hotkey"], fallback=True)

        if self.login_window.isVisible():
            self.enable_login_escape()

    def enable_login_escape(self):
        if self.escape_hotkey is not None:
            return
        try:
            self.escape_hotkey = keyboard.add_hotkey("esc", self.hotkey_bridge.escape_requested.emit, suppress=True)
        except Exception as error:
            print(f"Overlay escape hotkey error: {error}")
            self.escape_hotkey = keyboard.add_hotkey("esc", self.hotkey_bridge.escape_requested.emit)

    def disable_login_escape(self):
        if self.escape_hotkey is None:
            return
        keyboard.remove_hotkey(self.escape_hotkey)
        self.escape_hotkey = None

    def set_mode(self, selected_mode):
        self.config["mode"] = selected_mode
        save_config(self.config)

    def set_startup_enabled(self, enabled):
        if not self.startup_supported:
            return

        try:
            self.startup_enabled = apply_startup_enabled(enabled)
        except OSError as error:
            print(f"Startup registration error: {error}")
            self.startup_enabled = is_startup_enabled()

        self.tray_menu.set_startup_enabled(self.startup_enabled)
        self.tray_menu.set_startup_supported(self.startup_supported)
        if self.main_window is not None:
            self.main_window.set_startup_enabled(self.startup_enabled)
            self.main_window.set_startup_supported(self.startup_supported)

    def login(self, account_credentials):
        self.login_window.hide()

        def perform_login_sequence():
            time.sleep(0.4)
            keyboard.write(account_credentials["email"])
            time.sleep(0.1)
            keyboard.press_and_release("tab" if self.config["mode"] == Mode.TAB else "enter")
            time.sleep(1.0)
            keyboard.write(account_credentials["password"])
            keyboard.press_and_release("enter")

        threading.Thread(target=perform_login_sequence, daemon=True).start()


if __name__ == "__main__":
    sys.exit(run())
