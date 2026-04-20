from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QVBoxLayout

from .config import DEFAULT_CONFIG, save_config
from .theme import Headers, Insets, Palette, Radius, Size, Space, Text, frame_style, list_widget_style
from .base import DraggableWindow
from .confirm_dialog import ConfirmDialog
from .custom_input_dialog import CustomInputDialog
from .widgets import AccountItemWidget, HeaderWidget, StartupToggleRow, themed_button


class MainWindow(DraggableWindow):
    def __init__(self, config, save_callback, startup_enabled=False, on_startup_toggle=None, startup_supported=True):
        super().__init__()
        self.config = config
        self.save_callback = save_callback

        self.setFixedSize(*Size.MAIN_WINDOW)

        panel_frame = QFrame(self)
        panel_frame.resize(self.size())
        panel_frame.setStyleSheet(frame_style(Palette.SURFACE, Radius.CONTAINER))

        content_layout = QVBoxLayout(panel_frame)
        content_layout.setContentsMargins(*Insets.MAIN_WINDOW)
        content_layout.setSpacing(Space.BIG)
        content_layout.addWidget(HeaderWidget(Headers.MAIN))

        self.account_list = QListWidget()
        self.account_list.setFocusPolicy(Qt.NoFocus)
        self.account_list.setFrameShape(QFrame.NoFrame)
        self.account_list.setStyleSheet(list_widget_style())
        self.account_list.itemSelectionChanged.connect(self.on_selection_change)
        content_layout.addWidget(self.account_list)

        action_button_layout = QHBoxLayout()
        action_button_layout.setSpacing(Space.LARGE)
        for text, callback in [
            (Text.MAIN_WINDOW_ADD, self.add_account),
            (Text.MAIN_WINDOW_EDIT, self.edit_account),
            (Text.MAIN_WINDOW_DELETE, self.remove_account),
        ]:
            action_button = themed_button(text)
            action_button.clicked.connect(callback)
            action_button_layout.addWidget(action_button)
        content_layout.addLayout(action_button_layout)

        self.hotkey_button = themed_button()
        self.hotkey_button.clicked.connect(self.change_hotkey)
        content_layout.addWidget(self.hotkey_button)

        self.startup_toggle_row = StartupToggleRow(startup_enabled)
        if on_startup_toggle is not None:
            self.startup_toggle_row.toggled.connect(on_startup_toggle)
        self.startup_toggle_row.set_toggle_enabled(startup_supported)
        content_layout.addWidget(self.startup_toggle_row)

        self.refresh_hotkey()
        self.refresh_accounts()

    def hideEvent(self, event):
        self.account_list.clearSelection()
        self.account_list.setCurrentItem(None)
        self.on_selection_change()
        super().hideEvent(event)

    def refresh_accounts(self):
        self.account_list.clear()
        for account in self.config["accounts"]:
            account_item = QListWidgetItem()
            account_widget = AccountItemWidget(account["battle_tag"], account["email"])
            account_widget.ensurePolished()
            item_size = account_widget.sizeHint()
            item_size.setHeight(max(item_size.height(), account_widget.item_height()))
            account_item.setSizeHint(item_size)
            self.account_list.addItem(account_item)
            self.account_list.setItemWidget(account_item, account_widget)

    def on_selection_change(self):
        for row_index in range(self.account_list.count()):
            account_item = self.account_list.item(row_index)
            account_widget = self.account_list.itemWidget(account_item)
            if account_widget is not None:
                account_widget.update_selection_state(account_item.isSelected())

    def add_account(self):
        email_dialog = CustomInputDialog(self, Text.TITLE_NEW_ACCOUNT, Text.FIELD_EMAIL)
        if not email_dialog.exec() or not email_dialog.entered_value:
            return

        password_dialog = CustomInputDialog(self, Text.TITLE_NEW_ACCOUNT, Text.FIELD_PASSWORD, is_password=True)
        if not password_dialog.exec() or not password_dialog.entered_value:
            return

        battle_tag_dialog = CustomInputDialog(self, Text.TITLE_NEW_ACCOUNT, Text.FIELD_BATTLETAG)
        if not battle_tag_dialog.exec() or not battle_tag_dialog.entered_value:
            return

        self.config["accounts"].append({
            "email": email_dialog.entered_value,
            "password": password_dialog.entered_value,
            "battle_tag": battle_tag_dialog.entered_value,
        })
        self.persist_changes()

    def edit_account(self):
        selected_row = self.account_list.currentRow()
        if selected_row < 0:
            return

        account = self.config["accounts"][selected_row]
        email_dialog = CustomInputDialog(self, Text.TITLE_EDIT_ACCOUNT, Text.FIELD_EMAIL, default_value=account["email"])
        if not email_dialog.exec() or not email_dialog.entered_value:
            return

        password_dialog = CustomInputDialog(
            self,
            Text.TITLE_EDIT_ACCOUNT,
            Text.FIELD_PASSWORD,
            is_password=True,
            default_value=account["password"],
        )
        if not password_dialog.exec() or not password_dialog.entered_value:
            return

        battle_tag_dialog = CustomInputDialog(
            self,
            Text.TITLE_EDIT_ACCOUNT,
            Text.FIELD_BATTLETAG,
            default_value=account["battle_tag"],
        )
        if not battle_tag_dialog.exec() or not battle_tag_dialog.entered_value:
            return

        account.update({
            "email": email_dialog.entered_value,
            "password": password_dialog.entered_value,
            "battle_tag": battle_tag_dialog.entered_value,
        })
        self.persist_changes()

    def remove_account(self):
        selected_row = self.account_list.currentRow()
        if selected_row < 0:
            return

        battle_tag = self.config["accounts"][selected_row]["battle_tag"]
        confirm_dialog = ConfirmDialog(self, Text.TITLE_DELETE_ACCOUNT, Text.DELETE_ACCOUNT_PROMPT.format(battle_tag=battle_tag))
        if confirm_dialog.exec() and confirm_dialog.confirmed:
            self.config["accounts"].pop(selected_row)
            self.persist_changes()

    def change_hotkey(self):
        current_hotkey = self.config.get("hotkey", DEFAULT_CONFIG["hotkey"])
        hotkey_dialog = CustomInputDialog(self, Text.TITLE_HOTKEY, Text.FIELD_SHORTCUT, default_value=current_hotkey)
        if hotkey_dialog.exec() and hotkey_dialog.entered_value:
            self.config["hotkey"] = hotkey_dialog.entered_value
            self.persist_changes()

    def refresh_hotkey(self):
        current_hotkey = self.config.get("hotkey", DEFAULT_CONFIG["hotkey"]).upper()
        self.hotkey_button.setText(Text.HOTKEY_BUTTON.format(hotkey=current_hotkey))

    def set_startup_enabled(self, enabled):
        self.startup_toggle_row.set_checked(enabled)

    def set_startup_supported(self, supported):
        self.startup_toggle_row.set_toggle_enabled(supported)

    def persist_changes(self):
        save_config(self.config)
        self.save_callback()
        self.refresh_hotkey()
        self.refresh_accounts()
