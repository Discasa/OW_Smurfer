import os
import sys

# SILENCIAR LOGS E CORRIGIR ESCALA DPI
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"  # FIX 1: era QT_PA_PLATFORM (faltava o Q)

import json
import time
import threading
import keyboard
import pyautogui
from PIL import Image, ImageDraw
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QListWidget,
                               QFrame, QDialog)
from PySide6.QtCore import Qt, QPoint, QObject, Signal   # FIX 2: adicionado QObject, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

# ==========================================================
# GESTÃO DE DADOS
# ==========================================================
APPDATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'OW_Smurfer')
CONFIG_FILE = os.path.join(APPDATA_PATH, 'config.json')

if not os.path.exists(APPDATA_PATH):
    os.makedirs(APPDATA_PATH)

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                data.setdefault('modo', 'enter')
                data.setdefault('contas', [])
                data.setdefault('atalho', 'ctrl+l')
                return data
        except:
            pass
    return {"contas": [], "atalho": "ctrl+l", "modo": "enter"}

def salvar_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# ==========================================================
# ESTILO
# ==========================================================
STYLE_SHEET = """
QFrame#MainFrame {
    background-color: #1a1a1b;
    border-radius: 12px;
    border: 1px solid #333537;
}
QLabel {
    color: #bbbbbb;
    font-family: 'Segoe UI';
    font-size: 13px;
}
QLineEdit {
    background-color: #2b2d2f;
    color: white;
    border: 1px solid #3e4144;
    border-radius: 6px;
    padding: 6px;
}
QPushButton {
    background-color: #3e4144;
    color: white;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover { background-color: #4e5256; }
QPushButton#PrimaryBtn { background-color: #47a1eb; color: #1a1a1b; }
QPushButton#PrimaryBtn:hover { background-color: #63b1f2; }
QPushButton#DangerBtn { background-color: #e06c75; }

QListWidget {
    background-color: #2b2d2f;
    border-radius: 8px;
    color: white;
    outline: none;
}
QListWidget::item { padding: 8px; border-bottom: 1px solid #37393b; }
QListWidget::item:selected { background-color: #37393b; color: #47a1eb; }
"""

# ==========================================================
# BRIDGE THREAD-SAFE PARA HOTKEYS
# FIX 2: keyboard dispara callbacks em thread secundária; usar Signal
# garante que o Qt processe tudo na thread principal (event loop).
# ==========================================================
class HotkeyBridge(QObject):
    triggered = Signal()

# ==========================================================
# COMPONENTES
# ==========================================================
class CustomInputDialog(QDialog):
    def __init__(self, parent, title, label_text, is_password=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.result_text = None

        layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        self.frame.setStyleSheet(STYLE_SHEET)
        f_layout = QVBoxLayout(self.frame)

        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignCenter)
        f_layout.addWidget(lbl)

        self.input = QLineEdit()
        if is_password:
            self.input.setEchoMode(QLineEdit.Password)
        f_layout.addWidget(self.input)

        btns = QHBoxLayout()
        ok = QPushButton("OK")
        ok.setObjectName("PrimaryBtn")
        ok.clicked.connect(self.accept_data)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        f_layout.addLayout(btns)

        layout.addWidget(self.frame)
        self.input.setFocus()

    def accept_data(self):
        self.result_text = self.input.text()
        self.accept()


class ConfigWindow(QWidget):
    def __init__(self, config, on_save):
        super().__init__()
        self.config = config
        self.on_save = on_save
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(400, 500)
        layout = QVBoxLayout(self)
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet(STYLE_SHEET)
        content = QVBoxLayout(self.main_frame)

        header = QLabel("OVERWATCH SMURFER")
        header.setStyleSheet("font-weight: bold; font-size: 15px; color: #47a1eb; margin: 5px;")
        header.setAlignment(Qt.AlignCenter)
        content.addWidget(header)

        content.addWidget(QLabel("Atalho de ativação:"))
        self.edit_atalho = QLineEdit(self.config['atalho'])
        self.edit_atalho.setMaximumHeight(35)
        content.addWidget(self.edit_atalho)

        content.addWidget(QLabel("Gerenciar Contas:"))
        self.lista = QListWidget()
        self.refresh_list()
        content.addWidget(self.lista)

        btn_row = QHBoxLayout()
        add = QPushButton("Adicionar")
        add.clicked.connect(self.add_conta)
        rem = QPushButton("Remover")
        rem.setObjectName("DangerBtn")
        rem.clicked.connect(self.rem_conta)
        btn_row.addWidget(add)
        btn_row.addWidget(rem)
        content.addLayout(btn_row)

        save = QPushButton("SALVAR ALTERAÇÕES")
        save.setObjectName("PrimaryBtn")
        save.setFixedHeight(38)
        save.clicked.connect(self.finalizar)
        content.addWidget(save)

        layout.addWidget(self.main_frame)

    def refresh_list(self):
        self.lista.clear()
        for c in self.config['contas']:
            self.lista.addItem(f"{c['bnet']} - {c['email']}")

    def add_conta(self):
        e = CustomInputDialog(self, "Add", "E-mail:")
        if e.exec() and e.result_text:
            s = CustomInputDialog(self, "Add", "Senha:", True)
            if s.exec() and s.result_text:
                n = CustomInputDialog(self, "Add", "BattleTag:")
                if n.exec() and n.result_text:
                    self.config['contas'].append({
                        "bnet": n.result_text,
                        "email": e.result_text,
                        "senha": s.result_text
                    })
                    self.refresh_list()

    def rem_conta(self):
        idx = self.lista.currentRow()
        if idx >= 0:
            self.config['contas'].pop(idx)
            self.refresh_list()

    def finalizar(self):
        self.config['atalho'] = self.edit_atalho.text().lower()
        salvar_config(self.config)
        self.on_save()
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    # FIX 3: mouseReleaseEvent ausente fazia old_pos nunca ser resetado,
    # mantendo o drag ativo mesmo após soltar o botão do mouse.
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None


class OverlayMenu(QWidget):
    def __init__(self, config, callback):
        super().__init__()
        self.config = config
        self.callback = callback
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        self.frame.setStyleSheet(STYLE_SHEET)
        self.content = QVBoxLayout(self.frame)
        self.refresh_ui()
        layout.addWidget(self.frame)

    def refresh_ui(self):
        while self.content.count():
            item = self.content.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        lbl = QLabel(f"MODO: {self.config['modo'].upper()}")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #47a1eb; font-weight: bold; margin-bottom: 5px;")
        self.content.addWidget(lbl)

        for c in self.config['contas']:
            btn = QPushButton(c['bnet'])
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda chk=False, item=c: self.callback(item))
            self.content.addWidget(btn)

        self.adjustSize()

# ==========================================================
# APP CORE
# ==========================================================
class SmurferApp:
    def __init__(self):
        self.config = carregar_config()
        self.overlay = None
        self.config_win = None

        # FIX 2: bridge para invocar toggle_menu com segurança a partir
        # da thread do teclado → signal é processado na thread principal do Qt.
        self.bridge = HotkeyBridge()
        self.bridge.triggered.connect(self.toggle_menu)

        self.tray = QSystemTrayIcon(self.get_icon())
        menu = QMenu()
        menu.addAction("Configurações", self.abrir_config)
        menu.addSeparator()
        menu.addAction("Sair", sys.exit)
        self.tray.setContextMenu(menu)
        self.tray.show()

        self.atualizar_hotkeys()

    def get_icon(self):
        img = Image.new('RGB', (64, 64), color=(255, 128, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((12, 12, 52, 52), fill="white")
        path = os.path.join(APPDATA_PATH, "tray.png")
        img.save(path)
        return QIcon(path)

    def atualizar_hotkeys(self):
        keyboard.unhook_all()
        # FIX 2: emite o signal em vez de chamar toggle_menu diretamente,
        # evitando acesso a widgets Qt a partir de uma thread secundária.
        keyboard.add_hotkey(self.config['atalho'], self.bridge.triggered.emit)

    def toggle_menu(self):
        if self.overlay and self.overlay.isVisible():
            self.config['modo'] = "tab" if self.config['modo'] == "enter" else "enter"
            self.overlay.refresh_ui()
        else:
            self.overlay = OverlayMenu(self.config, self.exec_login)
            # FIX 6: adjustSize() antes de move() garante que rect() tenha
            # dimensões reais; sem isso, rect().center() retorna (0, 0).
            self.overlay.adjustSize()
            center = QApplication.primaryScreen().geometry().center()
            self.overlay.move(center - self.overlay.rect().center())
            self.overlay.show()
            self.overlay.activateWindow()

    def abrir_config(self):
        self.config_win = ConfigWindow(self.config, self.atualizar_hotkeys)
        self.config_win.show()

    def exec_login(self, conta):
        self.overlay.hide()
        # FIX 4: executar em thread separada para não bloquear o event loop do Qt.
        # FIX 5: keyboard.write() usado no lugar de pyautogui.typewrite(),
        #         que descarta silenciosamente caracteres não-ASCII (@, acentos, símbolos).
        def _digitar():
            time.sleep(0.5)
            keyboard.write(conta['email'], delay=0.02)
            keyboard.press_and_release(self.config['modo'])
            time.sleep(1.2)
            keyboard.write(conta['senha'], delay=0.02)
            keyboard.press_and_release('enter')

        threading.Thread(target=_digitar, daemon=True).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    core = SmurferApp()
    sys.exit(app.exec())