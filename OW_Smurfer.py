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
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QIcon, QPixmap

# --- Configurações de Caminhos ---
APPDATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'OW_Smurfer')
CONFIG_FILE = os.path.join(APPDATA_PATH, 'config.json')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ajuste o caminho da imagem se necessário
LOGO_PATH = os.path.join(BASE_DIR, 'img', 'OW_Smurfer_logo.png')

os.makedirs(APPDATA_PATH, exist_ok=True)

DEFAULT_CONFIG = {"contas": [], "atalho": "ctrl+l", "modo": "enter"}

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
class HeaderWidget(QWidget):
    def __init__(self, title, subtitle, show_close=True, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.logo = QLabel()
        self.logo.setFixedSize(32, 32)
        pix = QPixmap(LOGO_PATH)
        if not pix.isNull():
            self.logo.setPixmap(pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo.setStyleSheet("background-color: #da8826; border-radius: 16px;")

        t_layout = QVBoxLayout(); t_layout.setSpacing(0)
        lbl_title = QLabel(title); lbl_title.setStyleSheet("color: #da8826; font-size: 14px; font-weight: bold;")
        lbl_sub = QLabel(subtitle); lbl_sub.setStyleSheet("color: #ffffff; font-size: 10px; letter-spacing: 1px;")
        t_layout.addWidget(lbl_title); t_layout.addWidget(lbl_sub)
        
        layout.addWidget(self.logo)
        layout.addLayout(t_layout)
        layout.addStretch()

        if show_close:
            self.btn_close = QPushButton()
            self.btn_close.setFixedSize(16, 16)
            self.btn_close.setCursor(Qt.PointingHandCursor)
            self.btn_close.setStyleSheet("background-color: #c7302b; border-radius: 8px; border: none;")
            self.btn_close.clicked.connect(lambda: self.window().hide())
            layout.addWidget(self.btn_close, alignment=Qt.AlignTop)

class AccountItemWidget(QWidget):
    def __init__(self, bnet, email, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 12, 10, 12)
        self.lbl_bnet = QLabel(bnet); self.lbl_bnet.setAlignment(Qt.AlignCenter)
        self.lbl_details = QLabel(f"{email} | {'*' * 8}"); self.lbl_details.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_bnet); layout.addWidget(self.lbl_details)
        self.set_style(False)

    def set_style(self, selected):
        if selected:
            self.lbl_bnet.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px;")
            self.lbl_details.setStyleSheet("color: #ffffff; font-size: 11px;")
        else:
            self.lbl_bnet.setStyleSheet("color: #da8826; font-size: 13px;")
            self.lbl_details.setStyleSheet("color: #888888; font-size: 11px;")

class ModeToggle(QWidget):
    toggled = Signal(str)
    def __init__(self, current):
        super().__init__()
        layout = QHBoxLayout(self); layout.setAlignment(Qt.AlignCenter)
        self.btn_enter = QPushButton("ENTER"); self.btn_tab = QPushButton("TAB")
        for b in (self.btn_enter, self.btn_tab):
            b.setFlat(True); b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(self.on_click)
        layout.addWidget(QLabel("MODE:")); layout.addWidget(self.btn_enter); layout.addWidget(self.btn_tab)
        self.update_ui(current)

    def on_click(self):
        m = "enter" if self.sender() == self.btn_enter else "tab"
        self.update_ui(m); self.toggled.emit(m)

    def update_ui(self, m):
        active = "color: #da8826; font-weight: bold; font-size: 10px; border: none;"
        inactive = "color: #555555; font-size: 10px; border: none;"
        self.btn_enter.setStyleSheet(active if m == "enter" else inactive)
        self.btn_tab.setStyleSheet(active if m == "tab" else inactive)

# --- Janelas de Diálogo e Configuração ---
class CustomInputDialog(DraggableDialog):
    def __init__(self, parent, title, label, password=False, default=""):
        super().__init__(parent)
        self.setFixedSize(380, 150); self.result = None
        frame = QFrame(self); frame.resize(self.size())
        frame.setStyleSheet("background-color: #242426; border-radius: 20px; border: 1px solid #333;")
        layout = QVBoxLayout(frame); layout.setContentsMargins(20, 15, 20, 15)
        
        header = QHBoxLayout()
        lbl_head = QLabel(title.upper()); lbl_head.setStyleSheet("color: white; font-weight: bold; font-size: 11px; border: none;")
        btn_close = QPushButton(); btn_close.setFixedSize(14, 14); btn_close.setStyleSheet("background-color: #c7302b; border-radius: 7px; border: none;")
        btn_close.clicked.connect(self.reject)
        header.addWidget(lbl_head); header.addStretch(); header.addWidget(btn_close); layout.addLayout(header)

        self.input = QLineEdit(default)
        if password: self.input.setEchoMode(QLineEdit.Password)
        self.input.setStyleSheet("background: #1a1a1b; color: white; border: 1px solid #333; border-radius: 10px; padding: 8px;")
        layout.addWidget(QLabel(label.upper() + ":")); layout.addWidget(self.input)

        btn_ok = QPushButton("OK"); btn_ok.setFixedSize(80, 30)
        btn_ok.setStyleSheet("QPushButton { border: 1px solid #333; border-radius: 15px; color: #888; } QPushButton:hover { border-color: #da8826; color: white; }")
        btn_ok.clicked.connect(self.accept_data); layout.addWidget(btn_ok, alignment=Qt.AlignRight)

    def accept_data(self):
        self.result = self.input.text(); self.accept()

class ConfigWindow(DraggableWindow):
    def __init__(self, config, on_save):
        super().__init__()
        self.config = config; self.on_save = on_save
        self.setFixedSize(480, 380)
        frame = QFrame(self); frame.resize(self.size())
        frame.setStyleSheet("QFrame { background-color: #242426; border-radius: 20px; border: 1px solid #333; }")
        layout = QVBoxLayout(frame); layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(HeaderWidget("OVERWATCH SMURFER", "ACCOUNT MANAGER"))
        
        self.list = QListWidget()
        self.list.setStyleSheet("QListWidget { background: transparent; border: none; } QListWidget::item:selected { background: #da8826; border-radius: 10px; }")
        self.list.itemSelectionChanged.connect(self.on_sel_change); layout.addWidget(self.list)

        btn_layout = QHBoxLayout()
        for t, s in [("ADD", self.add), ("EDIT", self.edit), ("DELETE", self.remove)]:
            b = QPushButton(t); b.setStyleSheet("QPushButton { border: 1px solid #333; border-radius: 15px; color: #888; padding: 8px; } QPushButton:hover { border-color: #da8826; color: white; }")
            b.clicked.connect(s); btn_layout.addWidget(b)
        layout.addLayout(btn_layout); self.refresh()

    def refresh(self):
        self.list.clear()
        for c in self.config['contas']:
            item = QListWidgetItem(); w = AccountItemWidget(c['bnet'], c['email'])
            item.setSizeHint(w.sizeHint()); self.list.addItem(item); self.list.setItemWidget(item, w)

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
        if d.exec() and d.result: c.update({"email": d.result}); self.save()

    def remove(self):
        row = self.list.currentRow()
        if row >= 0: self.config['contas'].pop(row); self.save()

    def save(self):
        salvar_config(self.config); self.on_save(); self.refresh()

# --- Overlay Principal ---
class Overlay(DraggableWindow):
    def __init__(self, config, login_callback, mode_callback):
        super().__init__()
        self.config = config; self.login_callback = login_callback; self.mode_callback = mode_callback
        self.frame = QFrame(self); self.frame.setStyleSheet("background-color: #1a1a1b; border-radius: 25px; border: 1px solid #333;")
        self.main_layout = QVBoxLayout(self); self.main_layout.addWidget(self.frame)
        self.content = QVBoxLayout(self.frame); self.content.setContentsMargins(30, 30, 30, 30); self.content.setSpacing(15)
        self.refresh_ui()

    def refresh_ui(self):
        for i in reversed(range(self.content.count())): 
            w = self.content.itemAt(i).widget()
            if w: w.setParent(None)
        self.content.addWidget(HeaderWidget("SELECT ACCOUNT", "QUICK LOGIN", show_close=False))
        for c in self.config['contas']:
            btn = QPushButton(c['bnet']); btn.setStyleSheet("QPushButton { background: transparent; border: 1px solid #333; border-radius: 18px; color: #888; padding: 12px; } QPushButton:hover { border-color: #da8826; color: #da8826; }")
            btn.clicked.connect(lambda _, x=c: self.login_callback(x)); self.content.addWidget(btn)
        self.toggle_btn = ModeToggle(self.config.get('modo', 'enter'))
        self.toggle_btn.toggled.connect(self.mode_callback); self.content.addWidget(self.toggle_btn)
        lbl_esc = QLabel("ESC: CLOSE | CTRL+L: TOGGLE MODE"); lbl_esc.setAlignment(Qt.AlignCenter); lbl_esc.setStyleSheet("color: #444; font-size: 8px;")
        self.content.addWidget(lbl_esc); self.adjustSize()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape: self.hide()

# --- Núcleo do Aplicativo ---
class App:
    def __init__(self):
        self.config = carregar_config()
        self.bridge = HotkeyBridge()
        self.bridge.triggered.connect(self.handle_hotkey)
        
        self.overlay = Overlay(self.config, self.login, self.set_mode)
        self.config_win = None

        self.tray = QSystemTrayIcon(QIcon(LOGO_PATH) if os.path.exists(LOGO_PATH) else QIcon())
        menu = QMenu(); menu.addAction("Settings", self.open_settings); menu.addAction("Exit", QApplication.quit)
        self.tray.setContextMenu(menu); self.tray.show()

        keyboard.add_hotkey(self.config['atalho'], self.bridge.triggered.emit)

    def handle_hotkey(self):
        if self.overlay.isVisible():
            novo_modo = "tab" if self.config['modo'] == "enter" else "enter"
            self.set_mode(novo_modo)
            self.overlay.toggle_btn.update_ui(novo_modo)
        else:
            self.overlay.refresh_ui(); self.overlay.show(); center(self.overlay)

    def open_settings(self):
        if not self.config_win: self.config_win = ConfigWindow(self.config, self.on_config_saved)
        self.config_win.show(); center(self.config_win)

    def on_config_saved(self):
        self.overlay.refresh_ui()

    def set_mode(self, m):
        self.config['modo'] = m; salvar_config(self.config)

    def login(self, conta):
        self.overlay.hide()
        def run():
            time.sleep(0.4)
            keyboard.write(conta['email'])
            time.sleep(0.1)
            keyboard.press_and_release('tab' if self.config['modo'] == 'tab' else 'enter')
            time.sleep(0.4)
            keyboard.write(conta['senha'])
            keyboard.press_and_release('enter')
        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    core = App()
    sys.exit(app.exec())