import threading
import time

import keyboard
from PySide6.QtWidgets import QApplication

from .assets import load_app_icon
from .config import DEFAULT_CONFIG, load_config, save_config
from .base import HotkeyBridge
from .login_window import LoginWindow
from .main_window import MainWindow
from .startup import is_startup_enabled, is_startup_supported, set_startup_enabled as apply_startup_enabled
from .theme import Mode
from .tray_menu import TrayMenu
from .utils import center


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
        center(self.login_window)
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
