from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .theme import FontWeight, Insets, Palette, Radius, Size, Typography, close_button_style, frame_style, label_style


def build_modal_frame(dialog):
    modal_frame = QFrame(dialog)
    modal_frame.resize(dialog.size())
    modal_frame.setStyleSheet(frame_style(Palette.SURFACE, Radius.CONTAINER))

    modal_layout = QVBoxLayout(modal_frame)
    modal_layout.setContentsMargins(*Insets.MODAL)
    return modal_frame, modal_layout


def build_modal_header(title, close_callback):
    header_layout = QHBoxLayout()

    title_label = QLabel(title.upper())
    title_label.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.HUD, weight=FontWeight.BOLD))

    close_button = QPushButton()
    close_button.setFixedSize(*Size.MODAL_CLOSE)
    close_button.setCursor(Qt.PointingHandCursor)
    close_button.setFocusPolicy(Qt.NoFocus)
    close_button.setStyleSheet(close_button_style(Radius.SMALL))
    close_button.clicked.connect(close_callback)

    header_layout.addWidget(title_label)
    header_layout.addStretch()
    header_layout.addWidget(close_button)
    return header_layout
