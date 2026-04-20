from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel

from .theme import Padding, Palette, Radius, Size, Text, Typography, label_style
from .base import DraggableDialog
from .modal_common import build_modal_frame, build_modal_header
from .widgets import themed_button


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
            font_size=Typography.BUTTON,
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
