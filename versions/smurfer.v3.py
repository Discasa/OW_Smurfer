import os
import sys
import json
import time
import threading
import keyboard
from PIL import Image, ImageDraw

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QFrame, QDialog, QSystemTrayIcon, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, QObject, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap

APPDATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'OW_Smurfer')
CONFIG_FILE = os.path.join(APPDATA_PATH, 'config.json')

# Caminho do ícone requerido pelo layout
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, 'img', 'OW_Smurfer_logo.png')

os.makedirs(APPDATA_PATH, exist_ok=True)

DEFAULT_CONFIG = {
    "contas": [],
    "atalho": "ctrl+l",
    "modo": "enter"
}

def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
    except:
        return DEFAULT_CONFIG.copy()

    for k, v in DEFAULT_CONFIG.items():
        data.setdefault(k, v)
    return data

def salvar_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def center(widget):
    screen = QApplication.primaryScreen().geometry()
    geo = widget.frameGeometry()
    geo.moveCenter(screen.center())
    widget.move(geo.topLeft())


class HotkeyBridge(QObject):
    triggered = Signal()


# ==============================================================================
# CLASSES DE COMPONENTES VISUAIS E ESTILOS
# ==============================================================================

class FramelessDraggable(QWidget):
    """Classe base para permitir arrastar janelas sem borda"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Se for Dialog usar flags adequadas
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        if isinstance(self, QDialog): flags |= Qt.Dialog
        self.setWindowFlags(flags)
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

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()


class HeaderWidget(QWidget):
    """Componente de cabeçalho padronizado do App"""
    def __init__(self, title, subtitle, show_close=True, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Círculo Laranja / Imagem
        self.logo = QLabel()
        self.logo.setFixedSize(32, 32)
        pixmap = QPixmap(LOGO_PATH)
        if not pixmap.isNull():
            self.logo.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo.setStyleSheet("background-color: #da8826; border-radius: 16px;")

        t_layout = QVBoxLayout()
        t_layout.setSpacing(0)
        t_layout.setAlignment(Qt.AlignVCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #da8826; font-size: 14px; font-weight: bold; font-family: 'Segoe UI', Arial;")
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #ffffff; font-size: 10px; font-family: 'Segoe UI', Arial; letter-spacing: 1px;")
        
        if title: t_layout.addWidget(lbl_title)
        if subtitle: t_layout.addWidget(lbl_sub)
        
        layout.addWidget(self.logo)
        layout.addLayout(t_layout)
        layout.addStretch()

        if show_close:
            self.btn_close = QPushButton()
            self.btn_close.setFixedSize(16, 16)
            self.btn_close.setStyleSheet("QPushButton { background-color: #c7302b; border-radius: 8px; border: none; } QPushButton:hover { background-color: #ff4c4c; }")
            self.btn_close.clicked.connect(lambda: self.window().close())
            layout.addWidget(self.btn_close, alignment=Qt.AlignTop)


class AccountItemWidget(QWidget):
    """Widget customizado para a lista de contas na Main Window"""
    def __init__(self, bnet, email, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 15, 10, 15)
        self.layout.setSpacing(3)
        
        self.lbl_bnet = QLabel(bnet)
        self.lbl_bnet.setAlignment(Qt.AlignCenter)
        self.lbl_details = QLabel(f"{email} | {'*' * 8}")
        self.lbl_details.setAlignment(Qt.AlignCenter)
        
        self.layout.addWidget(self.lbl_bnet)
        self.layout.addWidget(self.lbl_details)
        self.set_normal_style()

    def set_normal_style(self):
        self.lbl_bnet.setStyleSheet("color: #da8826; font-size: 13px; font-family: 'Segoe UI', Arial;")
        self.lbl_details.setStyleSheet("color: #888888; font-size: 12px; font-family: 'Segoe UI', Arial;")

    def set_selected_style(self):
        self.lbl_bnet.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; font-family: 'Segoe UI', Arial;")
        self.lbl_details.setStyleSheet("color: #ffffff; font-size: 12px; font-family: 'Segoe UI', Arial;")


class ModeToggle(QWidget):
    """Widget clicável para trocar os modos de entrada visualmente"""
    toggled = Signal(str)
    
    def __init__(self, current_mode):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 10, 0, 0)
        
        lbl = QLabel("MODE:")
        lbl.setStyleSheet("color: white; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        
        self.btn_enter = QPushButton("ENTER")
        self.btn_tab = QPushButton("TAB")
        
        for b in (self.btn_enter, self.btn_tab):
            b.setCursor(Qt.PointingHandCursor)
            b.setFlat(True)
            b.clicked.connect(self.on_click)
            
        self.sep = QLabel("|")
        self.sep.setStyleSheet("color: #555;")
        
        layout.addWidget(lbl)
        layout.addWidget(self.btn_enter)
        layout.addWidget(self.sep)
        layout.addWidget(self.btn_tab)
        
        self.update_ui(current_mode)
        
    def on_click(self):
        mode = "enter" if self.sender() == self.btn_enter else "tab"
        self.update_ui(mode)
        self.toggled.emit(mode)
        
    def update_ui(self, mode):
        active_qss = "color: #da8826; font-size: 10px; font-weight: bold; background: transparent; border: none; letter-spacing: 1px;"
        inactive_qss = "color: #555555; font-size: 10px; font-weight: bold; background: transparent; border: none; letter-spacing: 1px;"
        
        self.btn_enter.setStyleSheet(active_qss if mode == "enter" else inactive_qss)
        self.btn_tab.setStyleSheet(active_qss if mode == "tab" else inactive_qss)

# ==============================================================================
# JANELAS (MAIN, MODAL, ACTION)
# ==============================================================================

class CustomInputDialog(FramelessDraggable, QDialog):
    """Modal Customizado fiel ao Layout"""
    def __init__(self, parent, label, password=False, default=""):
        super().__init__(parent)
        self.setFixedSize(380, 140)
        self.result = None
        
        self.frame = QFrame(self)
        self.frame.resize(self.size())
        self.frame.setStyleSheet("QFrame#BaseFrame { background-color: #242426; border-radius: 20px; border: 1px solid #333; }")
        self.frame.setObjectName("BaseFrame")
        
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(25, 20, 25, 20)
        
        header = QHBoxLayout()
        lbl_title = QLabel(f"ENTER YOUR {label.upper()}")
        lbl_title.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold; font-family: 'Segoe UI', Arial; letter-spacing: 2px;")
        
        btn_close = QPushButton()
        btn_close.setFixedSize(16, 16)
        btn_close.setStyleSheet("QPushButton { background-color: #c7302b; border-radius: 8px; border: none; } QPushButton:hover { background-color: #ff4c4c; }")
        btn_close.clicked.connect(self.reject)
        
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(btn_close, alignment=Qt.AlignTop)
        layout.addLayout(header)
        
        row = QHBoxLayout()
        self.input = QLineEdit(default)
        if password:
            self.input.setEchoMode(QLineEdit.Password)
        self.input.setStyleSheet("""
            QLineEdit { background-color: #1a1a1b; color: white; border: 1px solid #333; border-radius: 12px; padding: 6px 15px; font-size: 12px; }
        """)
        
        btn_ok = QPushButton("ok")
        btn_ok.setFixedSize(65, 28)
        btn_ok.setStyleSheet("""
            QPushButton { background-color: transparent; color: #888; border: 1px solid #333; border-radius: 14px; font-size: 13px; }
            QPushButton:hover { border-color: #da8826; color: #da8826; }
        """)
        btn_ok.clicked.connect(self.accept_data)
        
        row.addWidget(self.input)
        row.addWidget(btn_ok)
        layout.addLayout(row)

    def showEvent(self, e):
        center(self)

    def accept_data(self):
        self.result = self.input.text()
        self.accept()


class ConfirmDialog(CustomInputDialog):
    def __init__(self, parent, text):
        super().__init__(parent, "CONFIRM")
        # Sobrescreve o layout de input do parente
        self.input.hide()
        
        layout = self.layout() # Acessando pelo frame principal
        row = layout.itemAt(1).layout()
        while row.count():
            item = row.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        lbl = QLabel(text.upper())
        lbl.setStyleSheet("color: #888;")
        row.addWidget(lbl)

        btn_cancel = QPushButton("cancel")
        btn_ok = QPushButton("yes")
        
        for b in (btn_cancel, btn_ok):
            b.setFixedSize(65, 28)
            b.setStyleSheet("""
                QPushButton { background-color: transparent; color: #888; border: 1px solid #333; border-radius: 14px; font-size: 13px; }
                QPushButton:hover { border-color: #da8826; color: #da8826; }
            """)
            
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept_data)
        
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)

    def accept_data(self):
        self.result = True
        self.accept()


class ConfigWindow(FramelessDraggable):
    """Main Window para gerenciar credenciais"""
    def __init__(self, config, on_save):
        super().__init__()
        self.config = config
        self.on_save = on_save
        self.init_ui()

    def showEvent(self, e):
        center(self)

    def init_ui(self):
        self.setFixedSize(480, 360)
        self.frame = QFrame(self)
        self.frame.resize(self.size())
        self.frame.setStyleSheet("QFrame#BaseFrame { background-color: #242426; border-radius: 20px; border: 1px solid #333; }")
        self.frame.setObjectName("BaseFrame")

        content = QVBoxLayout(self.frame)
        content.setContentsMargins(20, 20, 20, 20)
        content.setSpacing(10)

        header = HeaderWidget("OVERWATCH SMURFER", "SIMPLE MULTI LOGIN TOOL", show_close=True)
        content.addWidget(header)

        # Configuração da Lista e Scrollbar Customizada
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { border-bottom: 1px solid #333; }
            QListWidget::item:selected { background-color: #da8826; border-radius: 10px; }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px; }
            QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #da8826; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.list.itemSelectionChanged.connect(self.on_selection_changed)
        content.addWidget(self.list)

        self.refresh()

        btns = QHBoxLayout()
        btns.setSpacing(10)
        
        for text, slot in [("add", self.add), ("edit", self.edit), ("delete", self.remove)]:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton { background: transparent; border: 1px solid #333; border-radius: 15px; color: #888; padding: 7px 0px; }
                QPushButton:hover { border-color: #da8826; color: white; }
            """)
            btn.clicked.connect(slot)
            btns.addWidget(btn)

        content.addLayout(btns)

    def refresh(self):
        self.list.clear()
        for c in self.config['contas']:
            item = QListWidgetItem()
            widget = AccountItemWidget(c['bnet'], c['email'])
            item.setSizeHint(widget.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, widget)

    def on_selection_changed(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            widget = self.list.itemWidget(item)
            if widget:
                if item.isSelected():
                    widget.set_selected_style()
                else:
                    widget.set_normal_style()

    def add(self):
        e = CustomInputDialog(self, "EMAIL")
        if e.exec() and e.result:
            s = CustomInputDialog(self, "SENHA", True)
            if s.exec() and s.result:
                n = CustomInputDialog(self, "BATTLETAG")
                if n.exec() and n.result:
                    self.config['contas'].append({"email": e.result, "senha": s.result, "bnet": n.result})
                    self.salvar()

    def edit(self):
        idx = self.list.currentRow()
        if idx < 0: return

        conta = self.config['contas'][idx]
        e = CustomInputDialog(self, "EMAIL", default=conta['email'])
        if e.exec() and e.result:
            s = CustomInputDialog(self, "SENHA", True, default=conta['senha'])
            if s.exec() and s.result:
                n = CustomInputDialog(self, "BATTLETAG", default=conta['bnet'])
                if n.exec() and n.result:
                    conta.update({"email": e.result, "senha": s.result, "bnet": n.result})
                    self.salvar()

    def remove(self):
        idx = self.list.currentRow()
        if idx < 0: return

        dlg = ConfirmDialog(self, "DELETE ACCOUNT?")
        if dlg.exec() and dlg.result:
            self.config['contas'].pop(idx)
            self.salvar()

    def salvar(self):
        salvar_config(self.config)
        self.on_save()
        self.refresh()


class Overlay(FramelessDraggable):
    """Action Window que expande em tamanho automaticamente"""
    def __init__(self, config, callback, mode_cb):
        super().__init__()
        self.config = config
        self.callback = callback
        self.mode_cb = mode_cb
        
        self.frame = QFrame(self)
        self.frame.setObjectName("BaseFrame")
        self.frame.setStyleSheet("QFrame#BaseFrame { background-color: #1a1a1b; border-radius: 25px; border: 1px solid #333; }")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.frame)
        
        self.content = QVBoxLayout(self.frame)
        self.content.setContentsMargins(25, 25, 25, 25)
        self.content.setSpacing(12)
        self.content.setSizeConstraint(QVBoxLayout.SetFixedSize)
        
        header = HeaderWidget("OVERWATCH SMURFER", "SIMPLE MULTI LOGIN TOOL", show_close=False)
        self.content.addWidget(header)
        self.content.addSpacing(5)
        
        if not self.config['contas']:
            lbl = QLabel("No accounts registered")
            lbl.setStyleSheet("color: #888;")
            self.content.addWidget(lbl, alignment=Qt.AlignCenter)
        
        for c in self.config['contas']:
            btn = QPushButton(c['bnet'])
            btn.setProperty("class", "ActionBtn")
            btn.clicked.connect(lambda _, x=c: self.callback(x))
            self.content.addWidget(btn)
            
        self.mode_toggle = ModeToggle(self.config.get('modo', 'enter'))
        self.mode_toggle.toggled.connect(self.mode_cb)
        self.content.addWidget(self.mode_toggle)
        
        lbl_esc = QLabel("PRESS ESC TO CANCEL")
        lbl_esc.setAlignment(Qt.AlignCenter)
        lbl_esc.setStyleSheet("color: #444; font-size: 9px; letter-spacing: 1px; font-family: 'Segoe UI', Arial;")
        self.content.addWidget(lbl_esc)
        
        self.setStyleSheet("""
            QPushButton[class="ActionBtn"] {
                background-color: transparent; color: #888; border: 1px solid #333;
                border-radius: 16px; padding: 9px; font-size: 13px; font-family: 'Segoe UI', Arial;
            }
            QPushButton[class="ActionBtn"]:hover { border: 1px solid #da8826; color: #da8826; }
        """)

    def showEvent(self, e):
        center(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)


# ==============================================================================
# APP PRINCIPAL
# ==============================================================================

class App:
    def __init__(self):
        self.config = carregar_config()
        self.bridge = HotkeyBridge()
        self.bridge.triggered.connect(self.toggle)

        self.overlay = None
        self.config_win = None

        self.tray = QSystemTrayIcon(self.icon())
        menu = QMenu()
        menu.addAction("Config", self.open_config)
        menu.addAction("Set Hotkey", self.change_hotkey)
        menu.addSeparator()
        menu.addAction("Exit", sys.exit)
        self.tray.setContextMenu(menu)
        self.tray.show()

        self.setup_hotkey()

        if not self.config['contas']:
            self.open_config()

    def icon(self):
        if not os.path.exists(LOGO_PATH):
            # Fallback icon se não achar no diretório para não quebrar a SystemTray
            img_path = os.path.join(APPDATA_PATH, "icon.png")
            if not os.path.exists(img_path):
                img = Image.new('RGB', (64, 64), (218, 136, 38))
                ImageDraw.Draw(img).ellipse((10, 10, 54, 54), fill="white")
                img.save(img_path)
            return QIcon(img_path)
        return QIcon(LOGO_PATH)

    def setup_hotkey(self):
        keyboard.unhook_all()
        try:
            keyboard.add_hotkey(self.config['atalho'], self.bridge.triggered.emit)
        except Exception as e:
            print("Hotkey error:", e)

    def change_hotkey(self):
        d = CustomInputDialog(None, "HOTKEY", default=self.config['atalho'])
        if d.exec() and d.result:
            self.config['atalho'] = d.result
            salvar_config(self.config)
            self.setup_hotkey()

    def open_config(self):
        if not self.config_win:
            self.config_win = ConfigWindow(self.config, self.setup_hotkey)
        self.config_win.show()
        self.config_win.activateWindow()

    def update_mode(self, mode):
        self.config['modo'] = mode
        salvar_config(self.config)

    def toggle(self):
        if self.overlay and self.overlay.isVisible():
            self.overlay.hide()
            return

        self.overlay = Overlay(self.config, self.exec_login, self.update_mode)
        self.overlay.show()

    def exec_login(self, conta):
        self.overlay.hide()

        def run():
            time.sleep(0.5)
            keyboard.write(conta['email'])
            time.sleep(0.1)
            
            # Respeitando a variação de enter ou tab
            if self.config.get('modo', 'enter') == 'tab':
                keyboard.press_and_release('tab')
            else:
                keyboard.press_and_release('enter')
                
            time.sleep(0.5)
            keyboard.write(conta['senha'])
            keyboard.press_and_release('enter')

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    core = App()
    sys.exit(app.exec())