import os
import sys
import json
import time
import threading
import keyboard
from PIL import Image, ImageDraw

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget,
    QFrame, QDialog, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QIcon

APPDATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'OW_Smurfer')
CONFIG_FILE = os.path.join(APPDATA_PATH, 'config.json')

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


STYLE = """
QFrame#MainFrame { background:#1a1a1b; border-radius:12px; border:1px solid #333; }
QLabel { color:#bbb; }
QLineEdit { background:#2b2d2f; color:white; border-radius:6px; padding:5px; }
QPushButton { background:#3e4144; color:white; border-radius:6px; padding:6px; }
QPushButton:hover { background:#4e5256; }
"""


def center(widget):
    screen = QApplication.primaryScreen().geometry()
    geo = widget.frameGeometry()
    geo.moveCenter(screen.center())
    widget.move(geo.topLeft())


class HotkeyBridge(QObject):
    triggered = Signal()


class StyledDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        self.frame.setStyleSheet(STYLE)
        self.content = QVBoxLayout(self.frame)
        self.layout.addWidget(self.frame)

    def showEvent(self, e):
        center(self)


class InputDialog(StyledDialog):
    def __init__(self, parent, label, password=False, default=""):
        super().__init__(parent)
        self.result = None

        self.content.addWidget(QLabel(label))
        self.input = QLineEdit(default)
        if password:
            self.input.setEchoMode(QLineEdit.Password)
        self.content.addWidget(self.input)

        btn = QPushButton("OK")
        btn.clicked.connect(self.accept_data)
        self.content.addWidget(btn)

    def accept_data(self):
        self.result = self.input.text()
        self.accept()


class ConfirmDialog(StyledDialog):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.result = False

        self.content.addWidget(QLabel(text))

        row = QHBoxLayout()
        ok = QPushButton("Sim")
        cancel = QPushButton("Cancelar")

        ok.clicked.connect(self.yes)
        cancel.clicked.connect(self.reject)

        row.addWidget(cancel)
        row.addWidget(ok)
        self.content.addLayout(row)

    def yes(self):
        self.result = True
        self.accept()


class ConfigWindow(QWidget):
    def __init__(self, config, on_save):
        super().__init__()
        self.config = config
        self.on_save = on_save

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.init_ui()

    def showEvent(self, e):
        center(self)

    def init_ui(self):
        self.setFixedSize(400, 500)

        layout = QVBoxLayout(self)
        frame = QFrame()
        frame.setObjectName("MainFrame")
        frame.setStyleSheet(STYLE)

        content = QVBoxLayout(frame)

        content.addWidget(QLabel("Hotkey:"))
        self.edit_hotkey = QLineEdit(self.config['atalho'])
        content.addWidget(self.edit_hotkey)

        content.addWidget(QLabel("Contas:"))
        self.list = QListWidget()
        content.addWidget(self.list)

        self.refresh()

        btns = QHBoxLayout()

        add = QPushButton("Adicionar")
        add.clicked.connect(self.add)

        edit = QPushButton("Editar")
        edit.clicked.connect(self.edit)

        remove = QPushButton("Remover")
        remove.clicked.connect(self.remove)

        btns.addWidget(add)
        btns.addWidget(edit)
        btns.addWidget(remove)

        content.addLayout(btns)

        save = QPushButton("Salvar")
        save.clicked.connect(self.save)
        content.addWidget(save)

        layout.addWidget(frame)

    def refresh(self):
        self.list.clear()
        for c in self.config['contas']:
            self.list.addItem(f"{c['bnet']} - {c['email']}")

    def add(self):
        e = InputDialog(self, "Email")
        if e.exec() and e.result:
            s = InputDialog(self, "Senha", True)
            if s.exec() and s.result:
                n = InputDialog(self, "BattleTag")
                if n.exec() and n.result:
                    self.config['contas'].append({
                        "email": e.result,
                        "senha": s.result,
                        "bnet": n.result
                    })
                    self.refresh()

    def edit(self):
        idx = self.list.currentRow()
        if idx < 0:
            return

        conta = self.config['contas'][idx]

        e = InputDialog(self, "Email", default=conta['email'])
        if e.exec() and e.result:
            s = InputDialog(self, "Senha", True, conta['senha'])
            if s.exec() and s.result:
                n = InputDialog(self, "BattleTag", default=conta['bnet'])
                if n.exec() and n.result:
                    conta.update({
                        "email": e.result,
                        "senha": s.result,
                        "bnet": n.result
                    })
                    self.refresh()

    def remove(self):
        idx = self.list.currentRow()
        if idx < 0:
            return

        dlg = ConfirmDialog(self, "Deseja realmente deletar?")
        if dlg.exec() and dlg.result:
            self.config['contas'].pop(idx)
            self.refresh()

    def save(self):
        self.config['atalho'] = self.edit_hotkey.text()
        salvar_config(self.config)
        self.on_save()
        self.hide()


class Overlay(QWidget):
    def __init__(self, config, callback):
        super().__init__()
        self.config = config
        self.callback = callback

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        self.layout = QVBoxLayout(self)
        self.refresh()

    def showEvent(self, e):
        center(self)

    def refresh(self):
        while self.layout.count():
            w = self.layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not self.config['contas']:
            self.layout.addWidget(QLabel("Nenhuma conta cadastrada"))
            return

        for c in self.config['contas']:
            btn = QPushButton(c['bnet'])
            btn.clicked.connect(lambda _, x=c: self.callback(x))
            self.layout.addWidget(btn)


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
        menu.addAction("Abrir Menu", self.toggle)
        menu.addAction("Exit", sys.exit)
        self.tray.setContextMenu(menu)
        self.tray.show()

        self.setup_hotkey()

        if not self.config['contas']:
            self.open_config()

    def icon(self):
        path = os.path.join(APPDATA_PATH, "icon.png")
        if not os.path.exists(path):
            img = Image.new('RGB', (64, 64), (255, 128, 0))
            ImageDraw.Draw(img).ellipse((10, 10, 54, 54), fill="white")
            img.save(path)
        return QIcon(path)

    def setup_hotkey(self):
        keyboard.unhook_all()
        try:
            keyboard.add_hotkey(self.config['atalho'], self.bridge.triggered.emit)
        except Exception as e:
            print("Hotkey error:", e)

    def open_config(self):
        if not self.config_win:
            self.config_win = ConfigWindow(self.config, self.setup_hotkey)
        self.config_win.show()
        self.config_win.activateWindow()

    def toggle(self):
        if self.overlay and self.overlay.isVisible():
            self.overlay.hide()
            return

        self.overlay = Overlay(self.config, self.exec_login)
        self.overlay.show()

    def exec_login(self, conta):
        self.overlay.hide()

        def run():
            time.sleep(0.5)
            keyboard.write(conta['email'])
            keyboard.press_and_release('enter')
            time.sleep(1)
            keyboard.write(conta['senha'])
            keyboard.press_and_release('enter')

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    core = App()
    sys.exit(app.exec())
