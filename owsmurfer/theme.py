from dataclasses import dataclass


class Palette:
    SURFACE = "#242426"
    SURFACE_RAISED = "#202124"
    SURFACE_INTERACTIVE = "#2b2e31"
    SURFACE_ACTIVE = "#2a2c2f"
    SURFACE_DIVIDER = "#2c2f34"
    BORDER = "#45484d"
    TEXT_PRIMARY = "#b8bcc4"
    TEXT_MUTED = "#888888"
    TEXT_HINT = "#575b61"
    ACCENT = "#da8826"
    CLOSE = "#c7302b"


class Typography:
    WINDOW_TITLE = 14
    OVERLAY_TITLE = 12
    WINDOW_SUBTITLE = 10
    ACTION = 11
    HUD = 9


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
    CONTAINER = 20
    INTERACTIVE = 13


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
    MAIN_WINDOW = (430, 360)
    INPUT_DIALOG = (380, 150)
    CONFIRM_DIALOG = (380, 160)
    MODAL_CLOSE = (14, 14)
    DIALOG_CONFIRM_BUTTON = (90, 30)
    DIALOG_PRIMARY_BUTTON = (80, 30)
    SCROLLBAR_HANDLE_MIN = 28
    STARTUP_SWITCH_TRACK = (46, 26)
    STARTUP_SWITCH_HANDLE = 18
    TRAY_SWITCH_TRACK = (36, 20)
    TRAY_SWITCH_HANDLE = 14


class Insets:
    NONE = (Space.ZERO, Space.ZERO, Space.ZERO, Space.ZERO)
    MAIN_WINDOW = (Space.FRAME, Space.FRAME, Space.FRAME, Space.FRAME)
    OVERLAY = (Space.FRAME, Space.FRAME, Space.FRAME, Space.FRAME)
    MODAL = (Space.FRAME, Space.BIG, Space.FRAME, Space.BIG)
    ACCOUNT_ITEM = (Space.LARGE, Space.BIG, Space.LARGE, Space.BIG)
    SETTING_ROW = (Space.LARGE, Space.MID, Space.LARGE, Space.MID)
    MENU = (Space.SMALL, Space.SMALL, Space.SMALL, Space.SMALL)
    MENU_ITEM = (Space.SMALL, Space.LARGE, Space.SMALL, Space.LARGE)
    MENU_SEPARATOR = (Space.SMALL, Space.LARGE, Space.SMALL, Space.LARGE)
    TRAY_TOGGLE_ROW = (Space.SMALL, Space.LARGE, Space.SMALL, Space.MID)


class Padding:
    BUTTON_BASE = (8, 12)
    BUTTON_DEFAULT = (8, 16)
    ACCOUNT_BUTTON = (8, 18)
    DIALOG_ACTION = (6, 12)
    MODE_TOGGLE = (0, 4)
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
    STARTUP_ROW_TITLE = "START WITH WINDOWS"
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
            color=Palette.TEXT_PRIMARY,
            border=solid_border(Palette.BORDER),
            border_radius=Radius.SOFT,
            padding=Insets.MENU,
        ),
        qss_block(
            "QMenu::item",
            color=Palette.TEXT_PRIMARY,
            background="transparent",
            padding=Insets.MENU_ITEM,
            margin=Space.ZERO,
            border_radius=Radius.SMALL,
        ),
        qss_block(
            "QMenu::item:selected",
            background_color=Palette.SURFACE_INTERACTIVE,
            color=Palette.TEXT_PRIMARY,
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
        qss_block("QListWidget::item", border=Border.TRANSPARENT, border_radius=Radius.INTERACTIVE, outline=Border.NONE),
        qss_block("QListWidget::item:hover", background=Palette.SURFACE_ACTIVE, border=Border.TRANSPARENT, border_radius=Radius.INTERACTIVE),
        qss_block("QListWidget::item:selected", background=Palette.SURFACE_INTERACTIVE, border=Border.TRANSPARENT, border_radius=Radius.INTERACTIVE),
        qss_block("QListWidget::item:selected:hover", background=Palette.SURFACE_ACTIVE, border=Border.TRANSPARENT, border_radius=Radius.INTERACTIVE),
        scrollbar_style(),
    ])
