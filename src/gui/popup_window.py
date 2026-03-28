import os
import platform

from PyQt6.QtCore import QObject, QSize, Qt
from PyQt6.QtGui import QFontMetrics, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from behaviour.behaviour import BaseBehaviour
from behaviour.registry import get_registered_behaviour_ids
from resource_path import resource_path
from src.logger import app_logger
from user_automation_manager import UserAutomationManager


class PopupWindow(QWidget):
    def __init__(self, user_automation_manager: UserAutomationManager, toggle_idle_cycle_fn):
        super().__init__()

        self.user_automation_manager = user_automation_manager
        self.behaviour_manager = user_automation_manager.behaviour_manager
        self.toggle_idle_cycle = toggle_idle_cycle_fn
        self.settings_checkboxes: dict[str, QCheckBox] = {}
        self.behaviour_buttons: dict[str, QPushButton] = {}

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(332, 468)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setProperty("class", "main-frame")

        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(8, 8, 8, 8)
        window_layout.addWidget(self.main_frame)

        self.content_layout = QVBoxLayout(self.main_frame)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(6)

        self._build_header()
        self._build_summary()
        self._build_pages()
        self._build_footer()
        self.show_behaviours()
        self.refresh_ui()

    def _build_header(self) -> None:
        navbar = QWidget()
        navbar.setProperty("class", "navbar")
        navbar_layout = QHBoxLayout(navbar)
        navbar_layout.setContentsMargins(0, 0, 0, 0)

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel("User Automation Client")
        self.title.setProperty("class", "title")
        self.subtitle = QLabel("Desktop automation and behaviour control")
        self.subtitle.setProperty("class", "muted-label")
        title_block.addWidget(self.title)
        title_block.addWidget(self.subtitle)

        navbar_layout.addLayout(title_block)
        navbar_layout.addStretch(1)

        self.back_btn = self._create_icon_button("static/ic--round-person.svg", "Back")
        self.back_btn.clicked.connect(self.show_behaviours)
        navbar_layout.addWidget(self.back_btn)

        self.settings_btn = self._create_icon_button("static/ic--round-settings.svg", "Open Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        navbar_layout.addWidget(self.settings_btn)

        close_btn = self._create_icon_button("static/ic--round-close.svg", "Close")
        close_btn.clicked.connect(self.hide)
        navbar_layout.addWidget(close_btn)

        self.content_layout.addWidget(navbar)

    def _build_summary(self) -> None:
        self.summary = QFrame()
        self.summary.setProperty("class", "hero-card")
        summary_layout = QGridLayout(self.summary)
        summary_layout.setContentsMargins(8, 8, 8, 8)
        summary_layout.setHorizontalSpacing(8)
        summary_layout.setVerticalSpacing(2)

        self.summary_idle = QLabel()
        self.summary_idle.setProperty("class", "hero-value")
        self.summary_available = QLabel()
        self.summary_available.setProperty("class", "hero-value")
        self.summary_running = QLabel()
        self.summary_running.setProperty("class", "hero-value")

        summary_layout.addWidget(self._metric_label("Idle Cycle"), 0, 0)
        summary_layout.addWidget(self.summary_idle, 0, 1)
        summary_layout.addWidget(self._metric_label("Available"), 1, 0)
        summary_layout.addWidget(self.summary_available, 1, 1)
        summary_layout.addWidget(self._metric_label("Current"), 2, 0)
        summary_layout.addWidget(self.summary_running, 2, 1)

        self.content_layout.addWidget(self.summary)

    def _metric_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("class", "metric-label")
        return label

    def _build_pages(self) -> None:
        self.page_stack = QStackedWidget()
        self.behaviours_page = QWidget()
        self.settings_page = QWidget()
        self.page_stack.addWidget(self.behaviours_page)
        self.page_stack.addWidget(self.settings_page)

        self._build_behaviours_page()
        self._build_settings_page()
        self.content_layout.addWidget(self.page_stack, 1)

    def _build_behaviours_page(self) -> None:
        page_layout = QVBoxLayout(self.behaviours_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(6)

        intro = QLabel("Run any behaviour that is currently available on this machine.")
        intro.setProperty("class", "muted-label")
        page_layout.addWidget(intro)

        self.behaviour_tabs = QTabWidget()
        self.behaviour_tabs.setDocumentMode(True)
        page_layout.addWidget(self.behaviour_tabs)
        self._rebuild_behaviour_tabs()

    def _build_settings_page(self) -> None:
        page_layout = QVBoxLayout(self.settings_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(6)

        intro = QLabel("Change config-backed settings. Runtime availability still takes precedence over toggles.")
        intro.setWordWrap(True)
        intro.setProperty("class", "muted-label")
        page_layout.addWidget(intro)

        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.Shape.NoFrame)

        settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(settings_widget)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(8)

        section_label = QLabel("Behaviour Toggles")
        section_label.setProperty("class", "section-title")
        self.settings_layout.addWidget(section_label)

        self.settings_checkboxes.clear()
        all_behaviours = self.behaviour_manager.all_behaviours
        toggles = self.user_automation_manager.get_behaviour_toggles()

        for behaviour_id in get_registered_behaviour_ids():
            behaviour = all_behaviours.get(behaviour_id)
            row = QFrame()
            row.setProperty("class", "settings-row")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 8, 10, 8)

            copy_layout = QVBoxLayout()
            copy_layout.setContentsMargins(0, 0, 0, 0)
            title = QLabel(behaviour.display_name if behaviour else behaviour_id)
            title.setProperty("class", "settings-title")
            description = QLabel(behaviour.description if behaviour else behaviour_id)
            description.setWordWrap(True)
            description.setProperty("class", "muted-label")
            copy_layout.addWidget(title)
            copy_layout.addWidget(description)

            toggle = QCheckBox("Enabled")
            toggle.setChecked(toggles.get(behaviour_id, True))
            toggle.stateChanged.connect(lambda state, bid=behaviour_id: self._on_behaviour_toggle_changed(bid, state))
            self.settings_checkboxes[behaviour_id] = toggle

            row_layout.addLayout(copy_layout, 1)
            row_layout.addWidget(toggle)
            self.settings_layout.addWidget(row)

        self.settings_layout.addStretch(1)
        settings_scroll.setWidget(settings_widget)
        page_layout.addWidget(settings_scroll)

    def _build_footer(self) -> None:
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "status-label")
        self.content_layout.addWidget(self.status_label)

        self.current_behaviour_label = QLabel("")
        self.current_behaviour_label.setProperty("class", "current-behaviour-label")
        self.content_layout.addWidget(self.current_behaviour_label)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(6)

        self.toggle_idle_btn = QPushButton("Pause Idle Cycle")
        self.toggle_idle_btn.setProperty("class", "primary-button")
        self.toggle_idle_btn.clicked.connect(self.toggle_idle_cycle)
        control_layout.addWidget(self.toggle_idle_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.setProperty("class", "danger-button")
        stop_btn.clicked.connect(self.stop_behaviour)
        control_layout.addWidget(stop_btn)

        self.content_layout.addLayout(control_layout)

    def _rebuild_behaviour_tabs(self) -> None:
        self.behaviour_buttons.clear()
        while self.behaviour_tabs.count() > 0:
            self.behaviour_tabs.removeTab(0)

        all_tab = self._create_behaviour_list_tab(list(self.behaviour_manager.available_behaviours.values()))
        self.behaviour_tabs.addTab(all_tab, "All")

        for category, behaviours in self.behaviour_manager.behaviours_by_category.items():
            category_tab = self._create_behaviour_list_tab(behaviours)
            self.behaviour_tabs.addTab(category_tab, category.value)

    def _create_behaviour_list_tab(self, behaviours: list[BaseBehaviour]) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(6)

        for behaviour in behaviours:
            tile = QPushButton(self._format_behaviour_tile_text(behaviour))
            tile.setProperty("class", "behaviour-tile")
            tile.setProperty("behaviour_id", behaviour.id)
            tile.setCursor(Qt.CursorShape.PointingHandCursor)
            tile.clicked.connect(self.run_behaviour)
            self.behaviour_buttons[behaviour.id] = tile
            scroll_layout.addWidget(tile)

        if not behaviours:
            placeholder = QLabel("No behaviours are currently available.")
            placeholder.setProperty("class", "placeholder-text")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(placeholder)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        return container

    def _create_icon_button(self, icon_relative_path: str, tooltip: str) -> QPushButton:
        svg_path = resource_path(icon_relative_path)
        svg_renderer = QSvgRenderer(svg_path)
        img = QImage(18, 18, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        svg_renderer.render(painter)
        painter.end()

        button = QPushButton()
        button.setIcon(QIcon(QPixmap.fromImage(img)))
        button.setIconSize(QSize(18, 18))
        button.setToolTip(tooltip)
        button.setMaximumWidth(30)
        button.setProperty("class", "icon-button")
        return button

    def _format_behaviour_tile_text(self, behaviour: BaseBehaviour) -> str:
        description = behaviour.description or behaviour.id
        metrics = QFontMetrics(self.font())
        trimmed_description = metrics.elidedText(description, Qt.TextElideMode.ElideRight, 230)
        return f"{behaviour.display_name}\n{trimmed_description}"

    def _on_behaviour_toggle_changed(self, behaviour_id: str, state: int) -> None:
        enabled = state == int(Qt.CheckState.Checked.value)
        self.user_automation_manager.update_behaviour_toggle(behaviour_id, enabled)
        self.refresh_ui()
        status = "enabled" if enabled else "disabled"
        self.status_label.setText(f"Saved setting: {behaviour_id} {status}")
        self.status_label.setProperty("class", "status-label")
        self._refresh_status_style(self.status_label)

    def _refresh_status_style(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def update_idle_cycle_button(self, is_paused: bool):
        self.toggle_idle_btn.setText("Resume Idle Cycle" if is_paused else "Pause Idle Cycle")
        self.toggle_idle_btn.setProperty("class", "success-button" if is_paused else "primary-button")
        self._refresh_status_style(self.toggle_idle_btn)

    def refresh_ui(self) -> None:
        self._rebuild_behaviour_tabs()
        toggles = self.user_automation_manager.get_behaviour_toggles()
        for behaviour_id, checkbox in self.settings_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(toggles.get(behaviour_id, True))
            checkbox.blockSignals(False)

        self.summary_available.setText(str(len(self.behaviour_manager.available_behaviours)))
        self.summary_idle.setText(self.user_automation_manager.idle_cycle_status.value.title())
        self.update_idle_cycle_button(self.user_automation_manager.idle_cycle_status.value == "paused")
        current = self.behaviour_manager.current_behaviour
        self.summary_running.setText(current.display_name if current else "Idle")
        self.update_status()

    def run_behaviour(self):
        sender: QObject | None = self.sender()
        if sender is None:
            app_logger.error("Popup window sender is missing")
            return

        behaviour_id = sender.property("behaviour_id")

        if self.behaviour_manager.is_behaviour_running():
            self.status_label.setText("Wait for the current behaviour to finish before starting another.")
            self.status_label.setProperty("class", "status-label-warning")
            self._refresh_status_style(self.status_label)
            return

        self.status_label.setText(f"Running behaviour: {behaviour_id}")
        self.status_label.setProperty("class", "status-label-running")
        self._refresh_status_style(self.status_label)
        self.behaviour_manager.run_behaviour(behaviour_id)
        self.refresh_ui()

    def stop_behaviour(self):
        if self.behaviour_manager.is_behaviour_running():
            self.behaviour_manager.terminate_behaviour()
            self.status_label.setText("Behaviour stopped")
            self.status_label.setProperty("class", "status-label-warning")
            self._refresh_status_style(self.status_label)
        else:
            self.status_label.setText("No behaviour is currently running")
            self.status_label.setProperty("class", "status-label")
            self._refresh_status_style(self.status_label)
        self.refresh_ui()

    def update_status(self):
        current_behaviour = self.behaviour_manager.current_behaviour
        if self.behaviour_manager.is_behaviour_running() and current_behaviour:
            self.status_label.setText("Behaviour is running")
            self.status_label.setProperty("class", "status-label-running")
            self.current_behaviour_label.setText(f"Current: {current_behaviour.display_name}")
            self.current_behaviour_label.setProperty("class", "current-behaviour-label-running")
        else:
            self.status_label.setText("Ready to run behaviours")
            self.status_label.setProperty("class", "status-label")
            self.current_behaviour_label.setText("Select a behaviour to start it.")
            self.current_behaviour_label.setProperty("class", "current-behaviour-label")

        self.summary_idle.setText(self.user_automation_manager.idle_cycle_status.value.title())
        current = self.behaviour_manager.current_behaviour
        self.summary_running.setText(current.display_name if current else "Idle")
        self._refresh_status_style(self.status_label)
        self._refresh_status_style(self.current_behaviour_label)

    def show_settings(self) -> None:
        self.page_stack.setCurrentWidget(self.settings_page)
        self.back_btn.show()
        self.settings_btn.hide()
        self.summary.hide()
        self.subtitle.setText("Settings")
        self.refresh_ui()

    def show_behaviours(self) -> None:
        self.page_stack.setCurrentWidget(self.behaviours_page)
        self.back_btn.hide()
        self.settings_btn.show()
        self.summary.show()
        self.subtitle.setText("Desktop automation and behaviour control")

    def position_for_os(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        padding = 20

        if platform.system() == "Windows":
            x = screen_geometry.width() - self.width() - padding
            y = screen_geometry.height() - self.height() - padding
        elif platform.system() == "Darwin":
            x = screen_geometry.width() - self.width() - padding
            y = padding
        else:
            desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

            if "gnome" in desktop_env or "unity" in desktop_env:
                x = screen_geometry.width() - (self.width() - screen_geometry.x()) - padding
                y = screen_geometry.y() + padding
            elif "kde" in desktop_env:
                x = screen_geometry.width() - (self.width() - screen_geometry.x()) - padding
                y = screen_geometry.height() - (self.height() - screen_geometry.y()) - padding
            else:
                x = screen_geometry.width() - (self.width() - screen_geometry.x()) - padding
                y = screen_geometry.height() - (self.height() - screen_geometry.y()) - padding

        self.move(x, y)

    def mousePressEvent(self, event):
        event.accept()

    def mouseMoveEvent(self, event):
        event.accept()
