from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from .config import DEFAULT_CONFIG
from .theme import FontWeight, Headers, Insets, Padding, Palette, Radius, Space, Text, Typography, frame_style, label_style
from .base import DraggableWindow
from .widgets import HeaderWidget, ModeToggle, themed_button


class LoginWindow(DraggableWindow):
    hidden = Signal()

    def __init__(self, config, login_callback, mode_callback):
        super().__init__()
        self.config = config
        self.login_callback = login_callback
        self.mode_callback = mode_callback

        panel_frame = QFrame(self)
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
                radius=Radius.BUTTON,
                font_size=Typography.ACTION,
                font_weight=FontWeight.MEDIUM,
                padding=Padding.ACCOUNT_BUTTON,
            )
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
