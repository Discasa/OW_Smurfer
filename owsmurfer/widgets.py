from PySide6.QtCore import QEasingCurve, QRectF, QSize, QSignalBlocker, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QAbstractButton, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .assets import LOGO_PNG_PATH
from .theme import (
    Border,
    FontWeight,
    HeaderTokens,
    Insets,
    Mode,
    Motion,
    Offset,
    Padding,
    Palette,
    Radius,
    Space,
    Size,
    Text,
    Typography,
    close_button_style,
    frame_style,
    label_style,
    style_rules,
    transparent_style,
)


class AnimatedButton(QPushButton):
    def __init__(
        self,
        text="",
        parent=None,
        *,
        background_color=Palette.SURFACE_RAISED,
        hover_background_color=Palette.SURFACE_INTERACTIVE,
        text_color=Palette.TEXT_MUTED,
        hover_text_color=Palette.TEXT_PRIMARY,
        border_color=Palette.BORDER,
        hover_border_color=None,
        radius=Radius.BUTTON,
        font_size=Typography.ACTION,
        font_weight=FontWeight.MEDIUM,
        padding=Padding.BUTTON_BASE,
    ):
        super().__init__(text, parent)
        self._base_background_color = QColor(background_color)
        self._hover_background_color = QColor(hover_background_color)
        self._base_text_color = QColor(text_color)
        self._hover_text_color = QColor(hover_text_color)
        self._base_border_color = QColor(border_color)
        self._hover_border_color = QColor(hover_border_color or border_color)
        self._radius = radius
        self._font_size = font_size
        self._font_weight = font_weight
        self._padding = padding
        self._animation_progress = 0.0

        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFlat(True)

        self._hover_animation = QVariantAnimation(self)
        self._hover_animation.setDuration(Motion.BUTTON_HOVER_MS)
        self._hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._hover_animation.valueChanged.connect(self._on_value_changed)
        self._apply_style(0.0)

    def _blend(self, start, end, progress):
        return QColor(
            int(start.red() + (end.red() - start.red()) * progress),
            int(start.green() + (end.green() - start.green()) * progress),
            int(start.blue() + (end.blue() - start.blue()) * progress),
        )

    def _apply_style(self, animation_progress):
        self.update()

    def _animate_to(self, target_progress):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._animation_progress)
        self._hover_animation.setEndValue(target_progress)
        self._hover_animation.start()

    def _on_value_changed(self, animation_value):
        self._animation_progress = float(animation_value)
        self._apply_style(self._animation_progress)

    def sizeHint(self):
        font = QFont(self.font())
        font.setPixelSize(self._font_size)
        font.setWeight(QFont.Weight(self._font_weight))
        metrics = QFontMetrics(font)
        vertical_padding, horizontal_padding = self._padding
        width = metrics.horizontalAdvance(self.text()) + (horizontal_padding * 2) + (Border.WIDTH * 2)
        height = metrics.height() + (vertical_padding * 2) + (Border.WIDTH * 2)
        return QSize(width, height)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        del event

        background_color = self._blend(self._base_background_color, self._hover_background_color, self._animation_progress)
        text_color = self._blend(self._base_text_color, self._hover_text_color, self._animation_progress)
        border_color = self._blend(self._base_border_color, self._hover_border_color, self._animation_progress)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(
            Border.WIDTH / 2,
            Border.WIDTH / 2,
            -(Border.WIDTH / 2),
            -(Border.WIDTH / 2),
        )
        painter.setPen(QPen(border_color, Border.WIDTH))
        painter.setBrush(background_color)
        painter.drawRoundedRect(rect, self._radius, self._radius)

        font = QFont(self.font())
        font.setPixelSize(self._font_size)
        font.setWeight(QFont.Weight(self._font_weight))
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

    def enterEvent(self, event):
        self._animate_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_to(0.0)
        super().leaveEvent(event)


def themed_button(text="", parent=None, **overrides):
    options = {
        "background_color": Palette.SURFACE_RAISED,
        "hover_background_color": Palette.SURFACE_INTERACTIVE,
        "text_color": Palette.TEXT_MUTED,
        "hover_text_color": Palette.TEXT_PRIMARY,
        "border_color": Palette.BORDER,
        "hover_border_color": Palette.BORDER,
        "radius": Radius.BUTTON,
        "font_size": Typography.ACTION,
        "padding": Padding.BUTTON_DEFAULT,
    }
    options.update(overrides)
    return AnimatedButton(text, parent, **options)


class HeaderWidget(QWidget):
    def __init__(self, preset, parent=None):
        super().__init__(parent)
        header_layout = QHBoxLayout(self)
        header_layout.setContentsMargins(*Insets.NONE)
        header_layout.setSpacing(Space.MID)

        logo_label = QLabel()
        logo_label.setFixedSize(HeaderTokens.LOGO_SIZE, HeaderTokens.LOGO_SIZE)
        logo_label.setStyleSheet(transparent_style())

        logo_pixmap = QPixmap(str(LOGO_PNG_PATH))
        if not logo_pixmap.isNull():
            if logo_pixmap.width() > HeaderTokens.LOGO_MIN_DIMENSION and logo_pixmap.height() > HeaderTokens.LOGO_MIN_DIMENSION:
                crop_margin = HeaderTokens.LOGO_CROP
                logo_pixmap = logo_pixmap.copy(
                    crop_margin,
                    crop_margin,
                    logo_pixmap.width() - (crop_margin * 2),
                    logo_pixmap.height() - (crop_margin * 2),
                )
            logo_label.setPixmap(logo_pixmap.scaled(
                HeaderTokens.LOGO_SIZE,
                HeaderTokens.LOGO_SIZE,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            ))
        else:
            logo_label.setStyleSheet(style_rules(
                background_color=HeaderTokens.TITLE_COLOR,
                border_radius=HeaderTokens.LOGO_FALLBACK_RADIUS,
                border=Border.NONE,
            ))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(Space.ZERO)

        title_label = QLabel(preset.title)
        title_label.setStyleSheet(label_style(
            color=HeaderTokens.TITLE_COLOR,
            size=preset.title_size,
            weight=HeaderTokens.TITLE_WEIGHT,
        ))

        subtitle_label = QLabel(preset.subtitle)
        subtitle_label.setStyleSheet(label_style(
            color=HeaderTokens.SUBTITLE_COLOR,
            size=preset.subtitle_size,
            letter_spacing=HeaderTokens.SUBTITLE_LETTER_SPACING,
        ))

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        header_layout.addWidget(logo_label)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        if preset.show_close:
            close_button = QPushButton()
            close_button.setFixedSize(HeaderTokens.CLOSE_SIZE, HeaderTokens.CLOSE_SIZE)
            close_button.setCursor(Qt.PointingHandCursor)
            close_button.setFocusPolicy(Qt.NoFocus)
            close_button.setStyleSheet(close_button_style(HeaderTokens.CLOSE_RADIUS))
            close_button.clicked.connect(lambda: self.window().hide())
            header_layout.addWidget(close_button, alignment=Qt.AlignTop)


class AccountItemWidget(QWidget):
    def __init__(self, battle_tag, email, parent=None):
        super().__init__(parent)
        self.setStyleSheet(transparent_style())

        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(*Insets.ACCOUNT_ITEM)
        content_layout.setSpacing(Space.SMALL)

        self.battle_tag_label = QLabel(battle_tag)
        self.battle_tag_label.setAlignment(Qt.AlignCenter)
        self.account_details_label = QLabel(email)
        self.account_details_label.setAlignment(Qt.AlignCenter)

        self._apply_fonts()
        self._battle_tag_label_style = label_style(color=Palette.ACCENT, size=Typography.HUD) + style_rules(
            padding_top=Padding.BATTLE_TAG_LABEL[0],
            padding_bottom=Padding.BATTLE_TAG_LABEL[1],
        )
        self._details_label_styles = {
            True: label_style(color=Palette.TEXT_PRIMARY, size=Typography.HUD),
            False: label_style(color=Palette.TEXT_MUTED, size=Typography.HUD),
        }

        content_layout.addWidget(self.battle_tag_label)
        content_layout.addWidget(self.account_details_label)
        self.update_selection_state(False)

    def _apply_fonts(self):
        battle_tag_font = QFont(self.battle_tag_label.font())
        battle_tag_font.setPixelSize(Typography.HUD)
        self.battle_tag_label.setFont(battle_tag_font)
        self.battle_tag_label.setFixedHeight(QFontMetrics(battle_tag_font).height() + Offset.BATTLE_TAG_HEIGHT)

        details_font = QFont(self.account_details_label.font())
        details_font.setPixelSize(Typography.HUD)
        self.account_details_label.setFont(details_font)
        self.account_details_label.setFixedHeight(QFontMetrics(details_font).height() + Offset.DETAILS_HEIGHT)

    def item_height(self):
        margins = self.layout().contentsMargins()
        spacing = self.layout().spacing()
        return (
            margins.top() +
            self.battle_tag_label.height() +
            spacing +
            self.account_details_label.height() +
            margins.bottom()
        )

    def update_selection_state(self, selected):
        self.battle_tag_label.setStyleSheet(self._battle_tag_label_style)
        self.account_details_label.setStyleSheet(self._details_label_styles[selected])


class ModeToggle(QWidget):
    toggled = Signal(str)

    def __init__(self, current):
        super().__init__()
        toggle_layout = QHBoxLayout(self)
        toggle_layout.setAlignment(Qt.AlignCenter)
        toggle_layout.setContentsMargins(*Insets.NONE)
        toggle_layout.setSpacing(Space.SMALL)

        mode_label = QLabel(Text.MODE_LABEL)
        mode_label.setStyleSheet(label_style(color=Palette.TEXT_PRIMARY, size=Typography.HUD, weight=FontWeight.SEMIBOLD))

        self.enter_button = QPushButton(Text.MODE_ENTER)
        self.tab_button = QPushButton(Text.MODE_TAB)
        separator_label = QLabel(Text.MODE_SEPARATOR)
        separator_label.setStyleSheet(label_style(color=Palette.BORDER, size=Typography.HUD, weight=FontWeight.SEMIBOLD))

        for mode_button in (self.enter_button, self.tab_button):
            mode_button.setFlat(True)
            mode_button.setCursor(Qt.PointingHandCursor)
            mode_button.setFocusPolicy(Qt.NoFocus)
            mode_button.clicked.connect(self._handle_click)

        self._stabilize_button_widths()

        toggle_layout.addWidget(mode_label)
        toggle_layout.addWidget(self.enter_button)
        toggle_layout.addWidget(separator_label)
        toggle_layout.addWidget(self.tab_button)

        self.update_mode_styles(current)

    def _stabilize_button_widths(self):
        for mode_button in (self.enter_button, self.tab_button):
            base_font = QFont(mode_button.font())
            base_font.setPointSize(Typography.HUD)
            base_font.setBold(False)

            active_font = QFont(base_font)
            active_font.setBold(True)

            normal_width = QFontMetrics(base_font).horizontalAdvance(mode_button.text())
            active_width = QFontMetrics(active_font).horizontalAdvance(mode_button.text())
            mode_button.setFixedWidth(max(normal_width, active_width) + Space.SMALL)

    def _handle_click(self):
        selected_mode = Mode.ENTER if self.sender() == self.enter_button else Mode.TAB
        self.update_mode_styles(selected_mode)
        self.toggled.emit(selected_mode)

    def update_mode_styles(self, selected_mode):
        active_stylesheet = style_rules(
            color=Palette.ACCENT,
            font_weight=FontWeight.BOLD,
            font_size=Typography.HUD,
            border=Border.NONE,
            background="transparent",
            outline=Border.NONE,
            padding=Padding.MODE_TOGGLE,
        )
        inactive_stylesheet = style_rules(
            color=Palette.TEXT_MUTED,
            font_size=Typography.HUD,
            border=Border.NONE,
            background="transparent",
            outline=Border.NONE,
            padding=Padding.MODE_TOGGLE,
        )

        self.enter_button.setStyleSheet(active_stylesheet if selected_mode == Mode.ENTER else inactive_stylesheet)
        self.tab_button.setStyleSheet(active_stylesheet if selected_mode == Mode.TAB else inactive_stylesheet)


class SwitchToggle(QAbstractButton):
    def __init__(
        self,
        checked=False,
        parent=None,
        *,
        track_size=None,
        handle_size=None,
        handle_offset=None,
        track_radius=None,
    ):
        super().__init__(parent)
        self._track_size = track_size or Size.STARTUP_SWITCH_TRACK
        self._handle_size = handle_size or Size.STARTUP_SWITCH_HANDLE
        self._handle_offset = Offset.SWITCH_HANDLE if handle_offset is None else handle_offset
        self._track_radius = Radius.INTERACTIVE if track_radius is None else track_radius
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(*self._track_size)

        self._handle_position = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(Motion.SWITCH_TOGGLE_MS)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._on_value_changed)
        self.toggled.connect(self._animate_to_state)

        self.set_checked_state(checked)

    def sizeHint(self):
        return QSize(*self._track_size)

    def _min_offset(self):
        return self._handle_offset

    def _max_offset(self):
        return self.width() - self._handle_offset - self._handle_size

    def _target_offset(self, checked):
        return self._max_offset() if checked else self._min_offset()

    def _on_value_changed(self, value):
        self._handle_position = float(value)
        self.update()

    def _animate_to_state(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._handle_position)
        self._animation.setEndValue(self._target_offset(checked))
        self._animation.start()

    def set_checked_state(self, checked):
        with QSignalBlocker(self):
            self.setChecked(bool(checked))
        self._animation.stop()
        self._handle_position = float(self._target_offset(self.isChecked()))
        self.update()

    def paintEvent(self, event):
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.isEnabled():
            track_color = Palette.ACCENT if self.isChecked() else Palette.SURFACE_INTERACTIVE
            border_color = Palette.ACCENT if self.isChecked() else Palette.BORDER
            handle_color = Palette.TEXT_PRIMARY
        else:
            track_color = Palette.SURFACE
            border_color = Palette.BORDER
            handle_color = Palette.TEXT_MUTED

        track_rect = QRectF(
            Border.WIDTH / 2,
            Border.WIDTH / 2,
            self.width() - Border.WIDTH,
            self.height() - Border.WIDTH,
        )
        painter.setPen(QPen(QColor(border_color), Border.WIDTH))
        painter.setBrush(QColor(track_color))
        painter.drawRoundedRect(track_rect, self._track_radius, self._track_radius)

        handle_rect = QRectF(
            self._handle_position,
            self._handle_offset,
            self._handle_size,
            self._handle_size,
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(handle_color))
        painter.drawEllipse(handle_rect)


class StartupToggleRow(QFrame):
    toggled = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setStyleSheet(frame_style(Palette.SURFACE, Radius.INTERACTIVE))

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(*Insets.SETTING_ROW)
        row_layout.setSpacing(Space.LARGE)

        startup_title_label = QLabel(Text.STARTUP_ROW_TITLE)
        startup_title_label.setStyleSheet(label_style(
            color=Palette.TEXT_PRIMARY,
            size=Typography.HUD,
            weight=FontWeight.SEMIBOLD,
        ))

        self.switch_toggle = SwitchToggle(checked)
        self.switch_toggle.toggled.connect(self.toggled.emit)

        row_layout.addWidget(startup_title_label, 1, alignment=Qt.AlignVCenter)
        row_layout.addWidget(self.switch_toggle, alignment=Qt.AlignVCenter)

    def set_checked(self, checked):
        self.switch_toggle.set_checked_state(checked)

    def set_toggle_enabled(self, enabled):
        self.switch_toggle.setEnabled(enabled)
