import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .app import AppController
from .theme import FontFamily


def run():
    application = QApplication(sys.argv)
    application.setFont(QFont(FontFamily.UI))
    application.setQuitOnLastWindowClosed(False)
    controller = AppController()
    application.controller = controller
    return application.exec()
