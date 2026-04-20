from PySide6.QtWidgets import QApplication


def center(widget):
    screen = QApplication.primaryScreen()
    if screen is None:
        return

    window_geometry = widget.frameGeometry()
    window_geometry.moveCenter(screen.geometry().center())
    widget.move(window_geometry.topLeft())
