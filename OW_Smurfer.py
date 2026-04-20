import os
import sys
import json
import time
import threading
import keyboard

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QFrame, QDialog, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QObject, Signal, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QFontMetrics

# --- Configurações de Caminhos ---
APPDATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'OW_Smurfer')
CONFIG_FILE = os.path.join(APPDATA_PATH, 'config.json')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PNG_PATH = os.path.join(BASE_DIR, 'img', 'OW_Smurfer_logo.png')
ICON_ICO_PATH = os.path.join(BASE_DIR, 'img', 'OW_Smurfer_logo.ico')

os.makedirs(APPDATA_PATH, exist_ok=True)

DEFAULT_CONFIG = {"contas": [], "atalho": "ctrl+l", "modo": "enter"}


def load_app_icon():
    if os.path.exists(ICON_ICO_PATH):
        return QIcon(ICON_ICO_PATH)
    if os.path.exists(LOGO_PNG_PATH):
        return QIcon(LOGO_PNG_PATH)
    return QIcon()


class Palette:
    PANEL_BG = "#1a1a1b"
    SURFACE_BG = "#242426"
    SURFACE_BUTTON = "#202124"
    SURFACE_BUTTON_HOVER = "#2b2e31"
    SURFACE_ITEM_HOVER = "#343940"
    SURFACE_SELECTED = "#2a2c2f"
    BORDER = "#333333"
    BORDER_SUBTLE = "#666666"
    TEXT_PRIMARY = "#ffffff"
    TEXT_MUTED = "#9aa0a9"
    TEXT_ACCOUNT = "#b8bcc4"
    TEXT_DIM = "#777777"
    TEXT_SOFT = "#888888"
    TEXT_SUBTLE = "#bbbbbb"
    TEXT_HINT = "#575b61"
    ACCENT = "#da8826"
    DANGER = "#c7302b"


class Typography:
    WINDOW_TITLE = 14
    OVERLAY_TITLE = 12
    WINDOW_SUBTITLE = 10
    ACCOUNT_BUTTON = 14
    BATTLETAG = 17
    DETAILS = 11
    BUTTON = 12
    MODE_LABEL = 9
    MODE_OPTION = 10
    DIALOG_TITLE = 11
    HINT = 8


class Radius:
    CLOSE = 7
    CLOSE_DOT = 8
    INPUT = 10
    BUTTON = 15
    BUTTON_SOFT = 16
    ACCOUNT = 18
    PANEL = 20
    OVERLAY = 25


class Space:
    XXS = 3
    XS = 4
    SM = 7
    MD = 8
    LG = 10
    XL = 12
    XXL = 14
    XXXL = 15
    PANEL = 20
    WINDOW = 22
    OVERLAY = 30
    SCROLLBAR = 7


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


def label_style(color=Palette.TEXT_PRIMARY, size=Typography.DETAILS, weight=None, letter_spacing=None):
    return style_rules(
        color=color,
        font_size=size,
        font_weight=weight,
        letter_spacing=letter_spacing,
        border="none",
        background="transparent",
    )


def frame_style(background, radius, border_color=Palette.BORDER):
    return style_rules(
        background_color=background,
        border_radius=radius,
        border=f"1px solid {border_color}",
    )


def input_style():
    return style_rules(
        background=Palette.PANEL_BG,
        color=Palette.TEXT_PRIMARY,
        border=f"1px solid {Palette.BORDER}",
        border_radius=Radius.INPUT,
        padding=Space.MD,
    )


def close_button_style(radius):
    return style_rules(
        background_color=Palette.DANGER,
        border_radius=radius,
        border="none",
    )


def transparent_style():
    return style_rules(background="transparent", border="none")


def scrollbar_style(width=Space.SCROLLBAR):
    handle_radius = max(3, width // 2)
    return "\n".join([
        qss_block(
            "QScrollBar:vertical",
            background=Palette.PANEL_BG,
            width=width,
            margin=0,
            border="none",
        ),
        qss_block(
            "QScrollBar::handle:vertical",
            background=Palette.BORDER_SUBTLE,
            min_height=28,
            border_radius=handle_radius,
            border="none",
        ),
        qss_block(
            "QScrollBar::handle:vertical:hover",
            background=Palette.TEXT_HINT,
            border="none",
        ),
        qss_block("QScrollBar::groove:vertical", background="transparent", border="none", margin=0),
        qss_block("QScrollBar::add-line:vertical", height=0, width=0, margin=0, padding=0, background=Palette.PANEL_BG, border="none"),
        qss_block("QScrollBar::sub-line:vertical", height=0, width=0, margin=0, padding=0, background=Palette.PANEL_BG, border="none"),
        qss_block("QScrollBar::up-arrow:vertical", height=0, width=0, background="transparent"),
        qss_block("QScrollBar::down-arrow:vertical", height=0, width=0, background="transparent"),
        qss_block("QScrollBar::add-page:vertical", background=Palette.PANEL_BG, margin=0, border="none"),
        qss_block("QScrollBar::sub-page:vertical", background=Palette.PANEL_BG, margin=0, border="none"),
        qss_block(
            "QScrollBar:horizontal",
            background=Palette.PANEL_BG,
            height=width,
            margin=0,
            border="none",
        ),
        qss_block(
            "QScrollBar::handle:horizontal",
            background=Palette.BORDER_SUBTLE,
            min_width=28,
            border_radius=handle_radius,
            border="none",
        ),
        qss_block(
            "QScrollBar::handle:horizontal:hover",
            background=Palette.TEXT_HINT,
            border="none",
        ),
        qss_block("QScrollBar::groove:horizontal", background="transparent", border="none", margin=0),
        qss_block("QScrollBar::add-line:horizontal", height=0, width=0, margin=0, padding=0, background=Palette.PANEL_BG, border="none"),
        qss_block("QScrollBar::sub-line:horizontal", height=0, width=0, margin=0, padding=0, background=Palette.PANEL_BG, border="none"),
        qss_block("QScrollBar::left-arrow:horizontal", height=0, width=0, background="transparent"),
        qss_block("QScrollBar::right-arrow:horizontal", height=0, width=0, background="transparent"),
        qss_block("QScrollBar::add-page:horizontal", background=Palette.PANEL_BG, margin=0, border="none"),
        qss_block("QScrollBar::sub-page:horizontal", background=Palette.PANEL_BG, margin=0, border="none"),
    ])


def list_widget_style():
    return "\n".join([
        qss_block("QListWidget", background="transparent", border="none", outline="none"),
        qss_block("QAbstractScrollArea", background="transparent", border="none", outline="none"),
        qss_block("QAbstractScrollArea::corner", background=Palette.PANEL_BG, border="none"),
        qss_block("QListWidget::item", border="1px solid transparent", border_radius=12, outline="none"),
        qss_block("QListWidget::item:hover", background=Palette.SURFACE_SELECTED, border="1px solid transparent", border_radius=12),
        qss_block("QListWidget::item:selected", background=Palette.SURFACE_ITEM_HOVER, border="1px solid transparent", border_radius=12),
        qss_block("QListWidget::item:selected:hover", background=Palette.SURFACE_SELECTED, border="1px solid transparent", border_radius=12),
        scrollbar_style(),
    ])


def themed_button(text="", parent=None, **overrides):
    options = {
        "bg": Palette.SURFACE_BUTTON,
        "hover_bg": Palette.SURFACE_BUTTON_HOVER,
        "fg": Palette.TEXT_MUTED,
        "hover_fg": Palette.TEXT_PRIMARY,
        "border": Palette.BORDER,
        "hover_border": Palette.BORDER,
        "radius": Radius.BUTTON,
        "font_size": Typography.BUTTON,
        "padding": (Space.SM, 16),
    }
    options.update(overrides)
    return AnimatedButton(text, parent, **options)

def carregar_config():
    if not os.path.exists(CONFIG_FILE): return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r') as f: data = json.load(f)
        for k, v in DEFAULT_CONFIG.items(): data.setdefault(k, v)
        return data
    except: return DEFAULT_CONFIG.copy()

def salvar_config(config):
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=4)

def center(widget):
    screen = QApplication.primaryScreen().geometry()
    geo = widget.frameGeometry()
    geo.moveCenter(screen.center())
    widget.move(geo.topLeft())

class HotkeyBridge(QObject):
    triggered = Signal()
    escape_requested = Signal()

# --- Classes de Base (Arrastáveis) ---
class DraggableWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event): self._drag_pos = None

class DraggableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event): self._drag_pos = None

# --- Componentes de Interface ---
class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None, *, bg=Palette.SURFACE_BG, hover_bg=Palette.SURFACE_BUTTON_HOVER,
                 fg=Palette.TEXT_MUTED, hover_fg=Palette.TEXT_PRIMARY, border=Palette.BORDER,
                 hover_border=None, radius=Radius.BUTTON_SOFT, font_size=Typography.BUTTON,
                 font_weight=500, padding=(Space.MD, 14)):
        super().__init__(text, parent)
        self._base_bg = QColor(bg)
        self._hover_bg = QColor(hover_bg)
        self._base_fg = QColor(fg)
        self._hover_fg = QColor(hover_fg)
        self._base_border = QColor(border)
        self._hover_border = QColor(hover_border or border)
        self._radius = radius
        self._font_size = font_size
        self._font_weight = font_weight
        self._padding = padding
        self._progress = 0.0

        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

        self._animation = QVariantAnimation(self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._on_value_changed)
        self._apply_style(0.0)

    def _blend(self, start, end, progress):
        return QColor(
            int(start.red() + (end.red() - start.red()) * progress),
            int(start.green() + (end.green() - start.green()) * progress),
            int(start.blue() + (end.blue() - start.blue()) * progress),
        )

    def _apply_style(self, progress):
        bg = self._blend(self._base_bg, self._hover_bg, progress)
        fg = self._blend(self._base_fg, self._hover_fg, progress)
        border = self._blend(self._base_border, self._hover_border, progress)
        self.setStyleSheet(qss_block(
            "QPushButton",
            background_color=bg.name(),
            color=fg.name(),
            border=f"1px solid {border.name()}",
            border_radius=self._radius,
            padding=self._padding,
            font_size=self._font_size,
            font_weight=self._font_weight,
            outline="none",
        ))

    def _animate_to(self, target):
        self._animation.stop()
        self._animation.setStartValue(self._progress)
        self._animation.setEndValue(target)
        self._animation.start()

    def _on_value_changed(self, value):
        self._progress = float(value)
        self._apply_style(self._progress)

    def enterEvent(self, event):
        self._animate_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_to(0.0)
        super().leaveEvent(event)

class HeaderWidget(QWidget):
    def __init__(self, title, subtitle, show_close=True, parent=None,
                 title_size=Typography.WINDOW_TITLE, subtitle_size=Typography.WINDOW_SUBTITLE):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.MD)
        
        logo = QLabel()
        logo.setFixedSize(30, 30)
        logo.setStyleSheet(transparent_style())
        pix = QPixmap(LOGO_PNG_PATH)
        if not pix.isNull():
            if pix.width() > 4 and pix.height() > 4:
                pix = pix.copy(1, 1, pix.width() - 2, pix.height() - 2)
            logo.setPixmap(pix.scaled(30, 30, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            logo.setStyleSheet(style_rules(
                background_color=Palette.ACCENT,
                border_radius=15,
                border="none",
            ))

        t_layout = QVBoxLayout(); t_layout.setSpacing(0)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(label_style(color=Palette.ACCENT, size=title_size, weight="bold"))
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=subtitle_size, letter_spacing=1))
        t_layout.addWidget(lbl_title); t_layout.addWidget(lbl_sub)
        
        layout.addWidget(logo)
        layout.addLayout(t_layout)
        layout.addStretch()

        if show_close:
            btn_close = QPushButton()
            btn_close.setFixedSize(16, 16)
            btn_close.setCursor(Qt.PointingHandCursor)
            btn_close.setFocusPolicy(Qt.NoFocus)
            btn_close.setStyleSheet(close_button_style(Radius.CLOSE_DOT))
            btn_close.clicked.connect(lambda: self.window().hide())
            layout.addWidget(btn_close, alignment=Qt.AlignTop)

class AccountItemWidget(QWidget):
    def __init__(self, bnet, email, parent=None):
        super().__init__(parent)
        self.setStyleSheet(transparent_style())
        layout = QVBoxLayout(self); layout.setContentsMargins(Space.LG, Space.XL, Space.LG, Space.XL)
        layout.setSpacing(Space.XS)
        self.lbl_bnet = QLabel(bnet); self.lbl_bnet.setAlignment(Qt.AlignCenter)
        self.lbl_details = QLabel(email); self.lbl_details.setAlignment(Qt.AlignCenter)
        self._apply_fonts()
        layout.addWidget(self.lbl_bnet); layout.addWidget(self.lbl_details)
        self.set_style(False)

    def _apply_fonts(self):
        bnet_font = QFont(self.lbl_bnet.font())
        bnet_font.setPixelSize(Typography.BATTLETAG)
        self.lbl_bnet.setFont(bnet_font)
        self.lbl_bnet.setFixedHeight(QFontMetrics(bnet_font).height() + 6)

        details_font = QFont(self.lbl_details.font())
        details_font.setPixelSize(Typography.DETAILS)
        self.lbl_details.setFont(details_font)
        self.lbl_details.setFixedHeight(QFontMetrics(details_font).height() + 2)

    def item_height(self):
        margins = self.layout().contentsMargins()
        spacing = self.layout().spacing()
        return (
            margins.top() +
            self.lbl_bnet.height() +
            spacing +
            self.lbl_details.height() +
            margins.bottom()
        )

    def set_style(self, selected):
        if selected:
            self.lbl_bnet.setStyleSheet(
                label_style(color=Palette.ACCENT, size=Typography.BATTLETAG) +
                style_rules(padding_top=0, padding_bottom=0)
            )
            self.lbl_details.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.DETAILS))
            return

        self.lbl_bnet.setStyleSheet(
            label_style(color=Palette.ACCENT, size=Typography.BATTLETAG) +
            style_rules(padding_top=0, padding_bottom=0)
        )
        self.lbl_details.setStyleSheet(label_style(color=Palette.TEXT_SOFT, size=Typography.DETAILS))

class ModeToggle(QWidget):
    toggled = Signal(str)
    def __init__(self, current):
        super().__init__()
        layout = QHBoxLayout(self); layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.XXS)
        mode_label = QLabel("MODE:")
        mode_label.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.MODE_LABEL, weight=600))
        self.btn_enter = QPushButton("ENTER"); self.btn_tab = QPushButton("TAB")
        self.sep_label = QLabel("|")
        self.sep_label.setStyleSheet(label_style(color=Palette.BORDER_SUBTLE, size=Typography.MODE_LABEL, weight=600))
        for b in (self.btn_enter, self.btn_tab):
            b.setFlat(True); b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(self.on_click)
        self._stabilize_button_widths()
        layout.addWidget(mode_label); layout.addWidget(self.btn_enter); layout.addWidget(self.sep_label); layout.addWidget(self.btn_tab)
        self.update_ui(current)

    def _stabilize_button_widths(self):
        for btn in (self.btn_enter, self.btn_tab):
            base_font = QFont(btn.font())
            base_font.setPointSize(Typography.MODE_OPTION)
            base_font.setBold(False)

            active_font = QFont(base_font)
            active_font.setBold(True)

            normal_width = QFontMetrics(base_font).horizontalAdvance(btn.text())
            active_width = QFontMetrics(active_font).horizontalAdvance(btn.text())
            btn.setFixedWidth(max(normal_width, active_width) + Space.XS)

    def on_click(self):
        m = "enter" if self.sender() == self.btn_enter else "tab"
        self.update_ui(m); self.toggled.emit(m)

    def update_ui(self, m):
        active = style_rules(
            color=Palette.ACCENT,
            font_weight="bold",
            font_size=Typography.MODE_OPTION,
            border="none",
            background="transparent",
            outline="none",
            padding=(0, 2),
        )
        inactive = style_rules(
            color=Palette.TEXT_DIM,
            font_size=Typography.MODE_OPTION,
            border="none",
            background="transparent",
            outline="none",
            padding=(0, 2),
        )
        self.btn_enter.setStyleSheet(active if m == "enter" else inactive)
        self.btn_tab.setStyleSheet(active if m == "tab" else inactive)

# --- Janelas de Diálogo e Configuração ---
class CustomInputDialog(DraggableDialog):
    def __init__(self, parent, title, label, password=False, default=""):
        super().__init__(parent)
        self.setFixedSize(380, 150); self.result = None
        frame = QFrame(self); frame.resize(self.size())
        frame.setStyleSheet(frame_style(Palette.SURFACE_BG, Radius.PANEL))
        layout = QVBoxLayout(frame); layout.setContentsMargins(Space.PANEL, Space.XXXL, Space.PANEL, Space.XXXL)
        
        header = QHBoxLayout()
        lbl_head = QLabel(title.upper()); lbl_head.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.DIALOG_TITLE, weight="bold"))
        btn_close = QPushButton(); btn_close.setFixedSize(14, 14); btn_close.setStyleSheet(close_button_style(Radius.CLOSE))
        btn_close.setFocusPolicy(Qt.NoFocus)
        btn_close.clicked.connect(self.reject)
        header.addWidget(lbl_head); header.addStretch(); header.addWidget(btn_close); layout.addLayout(header)

        self.input = QLineEdit(default)
        if password: self.input.setEchoMode(QLineEdit.Password)
        self.input.setStyleSheet(input_style())
        lbl_input = QLabel(label.upper() + ":")
        lbl_input.setStyleSheet(label_style(color=Palette.TEXT_SUBTLE))
        layout.addWidget(lbl_input); layout.addWidget(self.input)

        btn_ok = themed_button("OK", radius=Radius.BUTTON, font_size=Typography.BUTTON, padding=(6, 14))
        btn_ok.setFixedSize(80, 30)
        btn_ok.clicked.connect(self.accept_data); layout.addWidget(btn_ok, alignment=Qt.AlignRight)

    def accept_data(self):
        self.result = self.input.text(); self.accept()

class ConfirmDialog(DraggableDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.setFixedSize(380, 160); self.result = False
        frame = QFrame(self); frame.resize(self.size())
        frame.setStyleSheet(frame_style(Palette.SURFACE_BG, Radius.PANEL))
        layout = QVBoxLayout(frame); layout.setContentsMargins(Space.PANEL, Space.XXXL, Space.PANEL, Space.XXXL)

        header = QHBoxLayout()
        lbl_head = QLabel(title.upper()); lbl_head.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.DIALOG_TITLE, weight="bold"))
        btn_close = QPushButton(); btn_close.setFixedSize(14, 14); btn_close.setStyleSheet(close_button_style(Radius.CLOSE))
        btn_close.setFocusPolicy(Qt.NoFocus)
        btn_close.clicked.connect(self.reject)
        header.addWidget(lbl_head); header.addStretch(); header.addWidget(btn_close); layout.addLayout(header)

        lbl_text = QLabel(text.upper())
        lbl_text.setAlignment(Qt.AlignCenter)
        lbl_text.setWordWrap(True)
        lbl_text.setStyleSheet(label_style(color=Palette.TEXT_SUBTLE))
        layout.addWidget(lbl_text, alignment=Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_ok = themed_button("YES", radius=Radius.BUTTON, font_size=Typography.BUTTON, padding=(6, 14), fg=Palette.ACCENT, hover_fg=Palette.TEXT_PRIMARY)
        btn_ok.setFixedSize(90, 30)
        btn_ok.clicked.connect(self.accept_confirm)
        btn_row.addStretch(); btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def accept_confirm(self):
        self.result = True; self.accept()

class ConfigWindow(DraggableWindow):
    def __init__(self, config, on_save):
        super().__init__()
        self.config = config; self.on_save = on_save
        self.setFixedSize(430, 360)
        frame = QFrame(self); frame.resize(self.size())
        frame.setStyleSheet(frame_style(Palette.PANEL_BG, Radius.PANEL))
        layout = QVBoxLayout(frame); layout.setContentsMargins(Space.WINDOW, Space.WINDOW, Space.WINDOW, Space.WINDOW)
        layout.setSpacing(Space.XXL)
        layout.addWidget(HeaderWidget("OVERWATCH SMURFER", "ACCOUNT MANAGER", title_size=Typography.WINDOW_TITLE, subtitle_size=Typography.WINDOW_SUBTITLE))
        
        self.list = QListWidget()
        self.list.setFocusPolicy(Qt.NoFocus)
        self.list.setFrameShape(QFrame.NoFrame)
        self.list.setStyleSheet(list_widget_style())
        self.list.itemSelectionChanged.connect(self.on_sel_change); layout.addWidget(self.list)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(Space.LG)
        for t, s in [("ADD", self.add), ("EDIT", self.edit), ("DELETE", self.remove)]:
            b = themed_button(t)
            b.clicked.connect(s); btn_layout.addWidget(b)
        layout.addLayout(btn_layout)

        self.hotkey_btn = themed_button()
        self.hotkey_btn.clicked.connect(self.change_hotkey)
        layout.addWidget(self.hotkey_btn)

        self.refresh_hotkey(); self.refresh()

    def hideEvent(self, event):
        self.list.clearSelection()
        self.list.setCurrentItem(None)
        self.on_sel_change()
        super().hideEvent(event)

    def refresh(self):
        self.list.clear()
        for c in self.config['contas']:
            item = QListWidgetItem(); w = AccountItemWidget(c['bnet'], c['email'])
            w.ensurePolished()
            size = w.sizeHint()
            size.setHeight(max(size.height(), w.item_height()))
            item.setSizeHint(size)
            self.list.addItem(item); self.list.setItemWidget(item, w)

    def on_sel_change(self):
        for i in range(self.list.count()):
            it = self.list.item(i); w = self.list.itemWidget(it)
            if w: w.set_style(it.isSelected())

    def add(self):
        d = CustomInputDialog(self, "New Account", "Email")
        if d.exec() and d.result:
            p = CustomInputDialog(self, "New Account", "Password", True)
            if p.exec() and p.result:
                b = CustomInputDialog(self, "New Account", "Battletag")
                if b.exec() and b.result:
                    self.config['contas'].append({"email": d.result, "senha": p.result, "bnet": b.result})
                    self.save()

    def edit(self):
        row = self.list.currentRow()
        if row < 0: return
        c = self.config['contas'][row]
        d = CustomInputDialog(self, "Edit", "Email", default=c['email'])
        if d.exec() and d.result:
            p = CustomInputDialog(self, "Edit", "Password", True, default=c['senha'])
            if p.exec() and p.result:
                b = CustomInputDialog(self, "Edit", "Battletag", default=c['bnet'])
                if b.exec() and b.result:
                    c.update({"email": d.result, "senha": p.result, "bnet": b.result}); self.save()

    def remove(self):
        row = self.list.currentRow()
        if row < 0: return
        bnet = self.config['contas'][row]['bnet']
        dialog = ConfirmDialog(self, "Delete Account", f"Delete account {bnet}?")
        if dialog.exec() and dialog.result:
            self.config['contas'].pop(row); self.save()

    def change_hotkey(self):
        current = self.config.get('atalho', DEFAULT_CONFIG['atalho'])
        d = CustomInputDialog(self, "Hotkey", "Shortcut", default=current)
        if d.exec() and d.result:
            self.config['atalho'] = d.result; self.save()

    def refresh_hotkey(self):
        hotkey = self.config.get('atalho', DEFAULT_CONFIG['atalho']).upper()
        self.hotkey_btn.setText(f"HOTKEY: {hotkey}")

    def save(self):
        salvar_config(self.config); self.on_save(); self.refresh_hotkey(); self.refresh()

# --- Overlay Principal ---
class Overlay(DraggableWindow):
    hidden = Signal()

    def __init__(self, config, login_callback, mode_callback):
        super().__init__()
        self.config = config; self.login_callback = login_callback; self.mode_callback = mode_callback
        frame = QFrame(self); frame.setStyleSheet(frame_style(Palette.PANEL_BG, Radius.OVERLAY))
        layout = QVBoxLayout(self); layout.addWidget(frame)
        self.content = QVBoxLayout(frame); self.content.setContentsMargins(Space.OVERLAY, Space.OVERLAY, Space.OVERLAY, Space.OVERLAY); self.content.setSpacing(Space.XXXL)
        self.refresh_ui()

    def refresh_ui(self):
        for i in reversed(range(self.content.count())): 
            w = self.content.itemAt(i).widget()
            if w: w.setParent(None)
        self.content.addWidget(HeaderWidget(
            "SELECT ACCOUNT",
            "QUICK LOGIN",
            show_close=False,
            title_size=Typography.OVERLAY_TITLE,
            subtitle_size=Typography.WINDOW_SUBTITLE,
        ))
        for c in self.config['contas']:
            btn = themed_button(
                c['bnet'],
                fg=Palette.TEXT_ACCOUNT,
                radius=Radius.ACCOUNT,
                font_size=Typography.ACCOUNT_BUTTON,
                font_weight=500,
                padding=(Space.MD, 18),
            )
            btn.clicked.connect(lambda _, x=c: self.login_callback(x)); self.content.addWidget(btn)
        self.toggle_btn = ModeToggle(self.config.get('modo', 'enter'))
        self.toggle_btn.toggled.connect(self.mode_callback); self.content.addWidget(self.toggle_btn)
        hotkey = self.config.get('atalho', DEFAULT_CONFIG['atalho']).upper()
        lbl_esc = QLabel(f"ESC: CLOSE | {hotkey}: TOGGLE MODE")
        lbl_esc.setAlignment(Qt.AlignCenter)
        lbl_esc.setStyleSheet(label_style(color=Palette.TEXT_HINT, size=Typography.HINT))
        self.content.addWidget(lbl_esc); self.adjustSize()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape: self.hide()

    def hideEvent(self, event):
        self.hidden.emit(); super().hideEvent(event)

# --- Núcleo do Aplicativo ---
class App:
    def __init__(self):
        self.config = carregar_config()
        self.bridge = HotkeyBridge()
        self.bridge.triggered.connect(self.handle_hotkey)
        self.bridge.escape_requested.connect(self.handle_escape)
        
        self.overlay = Overlay(self.config, self.login, self.set_mode)
        self.overlay.hidden.connect(self.disable_overlay_escape)
        self.config_win = None
        self.escape_hotkey = None

        app_icon = load_app_icon()
        QApplication.instance().setWindowIcon(app_icon)
        self.tray = QSystemTrayIcon(app_icon)
        self.tray.activated.connect(self.on_tray_activated)
        menu = QMenu(); menu.addAction("Settings", self.open_settings); menu.addAction("Exit", QApplication.quit)
        self.tray.setContextMenu(menu); self.tray.show()

        self.setup_hotkey()

    def handle_hotkey(self):
        if self.overlay.isVisible():
            novo_modo = "tab" if self.config['modo'] == "enter" else "enter"
            self.set_mode(novo_modo)
            self.overlay.toggle_btn.update_ui(novo_modo)
        else:
            self.overlay.refresh_ui(); self.overlay.show(); center(self.overlay)
            self.enable_overlay_escape()

    def handle_escape(self):
        if self.overlay.isVisible():
            self.overlay.hide()

    def open_settings(self):
        if not self.config_win: self.config_win = ConfigWindow(self.config, self.on_config_saved)
        self.config_win.show(); center(self.config_win)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings()

    def on_config_saved(self):
        self.setup_hotkey(); self.overlay.refresh_ui()

    def setup_hotkey(self):
        keyboard.unhook_all()
        self.escape_hotkey = None
        hotkey = self.config.get('atalho', DEFAULT_CONFIG['atalho'])
        try:
            keyboard.add_hotkey(hotkey, self.bridge.triggered.emit)
        except Exception as exc:
            print(f"Hotkey error for '{hotkey}': {exc}")
            if hotkey == DEFAULT_CONFIG['atalho']:
                return
            self.config['atalho'] = DEFAULT_CONFIG['atalho']; salvar_config(self.config)
            try:
                keyboard.add_hotkey(DEFAULT_CONFIG['atalho'], self.bridge.triggered.emit)
            except Exception as fallback_exc:
                print(f"Fallback hotkey error: {fallback_exc}")
        if self.overlay.isVisible():
            self.enable_overlay_escape()

    def enable_overlay_escape(self):
        if self.escape_hotkey is not None:
            return
        try:
            self.escape_hotkey = keyboard.add_hotkey('esc', self.bridge.escape_requested.emit, suppress=True)
        except Exception as exc:
            print(f"Overlay escape hotkey error: {exc}")
            self.escape_hotkey = keyboard.add_hotkey('esc', self.bridge.escape_requested.emit)

    def disable_overlay_escape(self):
        if self.escape_hotkey is None:
            return
        keyboard.remove_hotkey(self.escape_hotkey)
        self.escape_hotkey = None

    def set_mode(self, m):
        self.config['modo'] = m; salvar_config(self.config)

    def login(self, conta):
        self.overlay.hide()
        def run():
            time.sleep(0.4)
            keyboard.write(conta['email'])
            time.sleep(0.1)
            keyboard.press_and_release('tab' if self.config['modo'] == 'tab' else 'enter')
            time.sleep(1.0)
            keyboard.write(conta['senha'])
            keyboard.press_and_release('enter')
        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    core = App()
    sys.exit(app.exec())
