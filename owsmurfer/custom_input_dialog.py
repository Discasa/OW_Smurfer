from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLineEdit

from .theme import Padding, Palette, Radius, Size, Text, Typography, input_style, label_style
from .base import DraggableDialog
from .modal_common import build_modal_frame, build_modal_header
from .widgets import themed_button


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

        confirm_button = themed_button(Text.DIALOG_INPUT_ACCEPT, radius=Radius.BUTTON, font_size=Typography.BUTTON, padding=Padding.DIALOG_ACTION)
        confirm_button.setFixedSize(*Size.DIALOG_PRIMARY_BUTTON)
        confirm_button.clicked.connect(self.accept_input)
        dialog_layout.addWidget(confirm_button, alignment=Qt.AlignRight)

    def accept_input(self):
        self.entered_value = self.input_field.text()
        self.accept()
