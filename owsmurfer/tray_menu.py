from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMenu, QSystemTrayIcon, QWidget, QWidgetAction

from .assets import load_app_icon
from .theme import Border, FontWeight, Insets, Offset, Palette, Radius, Size, Space, Text, Typography, label_style, menu_style, style_rules
from .widgets import SwitchToggle


class TrayStartupRow(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked=False, supported=True, parent=None):
        super().__init__(parent)
        self._is_hovered = False

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(*Insets.TRAY_TOGGLE_ROW)
        row_layout.setSpacing(Space.LARGE)

        self.startup_title_label = QLabel(Text.TRAY_STARTUP_TITLE)
        self.startup_title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.startup_toggle = SwitchToggle(
            checked,
            self,
            track_size=Size.TRAY_SWITCH_TRACK,
            handle_size=Size.TRAY_SWITCH_HANDLE,
            handle_offset=Offset.TRAY_SWITCH_HANDLE,
            track_radius=Radius.SOFT,
        )
        self.startup_toggle.toggled.connect(self.toggled.emit)

        row_layout.addWidget(self.startup_title_label, 1)
        row_layout.addWidget(self.startup_toggle, alignment=Qt.AlignVCenter)

        self.set_supported(supported)
        self._apply_style()

    def _apply_style(self):
        background_color = Palette.SURFACE_INTERACTIVE if self._is_hovered and self.isEnabled() else "transparent"
        self.setStyleSheet(style_rules(
            background_color=background_color,
            border_radius=Radius.SMALL,
            border=Border.NONE,
        ))
        self.startup_title_label.setStyleSheet(label_style(
            color=Palette.TEXT_PRIMARY if self.isEnabled() else Palette.TEXT_HINT,
            size=Typography.HUD,
            weight=FontWeight.MEDIUM,
        ))

    def enterEvent(self, event):
        self._is_hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled() and not self.startup_toggle.geometry().contains(event.pos()):
            self.startup_toggle.click()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def set_checked(self, checked):
        self.startup_toggle.set_checked_state(checked)

    def set_supported(self, supported):
        self.setEnabled(supported)
        self.startup_toggle.setEnabled(supported)
        self.setCursor(Qt.PointingHandCursor if supported else Qt.ArrowCursor)
        self._apply_style()


class TrayMenu(QObject):
    settings_requested = Signal()
    startup_toggled = Signal(bool)

    def __init__(self, startup_enabled=False, startup_supported=True, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(load_app_icon(), parent)
        self.tray_icon.activated.connect(self._on_activated)

        self.menu = QMenu()
        self.menu.setStyleSheet(menu_style())

        self.startup_toggle_row = TrayStartupRow(startup_enabled, startup_supported, self.menu)
        self.startup_toggle_action = QWidgetAction(self.menu)
        self.startup_toggle_action.setDefaultWidget(self.startup_toggle_row)
        self.menu.addAction(self.startup_toggle_action)
        self.startup_toggle_row.toggled.connect(self._on_startup_toggled)
        self.menu.addSeparator()
        self.menu.addAction(Text.MENU_SETTINGS, self.settings_requested.emit)
        self.menu.addAction(Text.MENU_EXIT, QApplication.quit)
        self.tray_icon.setContextMenu(self.menu)

    def _on_activated(self, activation_reason):
        if activation_reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def _on_startup_toggled(self, enabled):
        self.startup_toggled.emit(enabled)

    def set_startup_enabled(self, enabled):
        self.startup_toggle_row.set_checked(enabled)

    def set_startup_supported(self, supported):
        self.startup_toggle_row.set_supported(supported)

    def show(self):
        self.tray_icon.show()
