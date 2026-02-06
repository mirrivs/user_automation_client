from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QScrollArea,
    QApplication,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
import platform
import os

from behaviour.behaviour import BaseBehaviour
from resource_path import resource_path
from user_automation_manager import UserAutomationManager


class PopupWindow(QWidget):
    def __init__(self, user_automation_manager: UserAutomationManager, toggle_idle_cycle_fn):
        super().__init__()

        self.user_automation_manager = user_automation_manager
        self.behaviour_manager = user_automation_manager.behaviour_manager

        self.toggle_idle_cycle = toggle_idle_cycle_fn

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(300, 400)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setProperty("class", "main-frame")

        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(self.main_frame)

        content_layout = QVBoxLayout(self.main_frame)

        navbar = QWidget()
        navbar_layout = QHBoxLayout(navbar)

        title = QLabel("User Automation Client")
        title.setProperty("class", "title")
        navbar.setProperty("class", "navbar")
        navbar_layout.addWidget(title)

        # Close button with SVG icon
        svg_path = resource_path("static/ic--round-close.svg")
        svg_renderer = QSvgRenderer(svg_path)
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        svg_renderer.render(painter)
        painter.end()

        icon = QIcon(QPixmap.fromImage(img))
        close_btn = QPushButton()
        close_btn.setIcon(icon)

        close_btn.setIconSize(QSize(16, 16))
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.hide)
        close_btn.setMaximumWidth(20)
        close_btn.setProperty("class", "btn-transparent")

        navbar_layout.addWidget(close_btn)
        content_layout.addWidget(navbar)

        # Create tabs dynamically based on behaviour categories
        tabs = QTabWidget()

        # Create All tab with scroll area
        all_tab = QWidget()
        all_tab_layout = QVBoxLayout(all_tab)
        all_tab_layout.setContentsMargins(0, 0, 0, 0)

        all_subtitle = QLabel("All Behaviours:")
        all_subtitle.setProperty("class", "subtitle")
        all_subtitle.setContentsMargins(5, 5, 5, 5)
        all_tab_layout.addWidget(all_subtitle)

        # Create scroll area for behaviours
        all_scroll = QScrollArea()
        all_scroll.setWidgetResizable(True)
        all_scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Create widget to hold behaviour buttons
        all_scroll_widget = QWidget()
        all_behaviours_layout = QVBoxLayout(all_scroll_widget)

        # Use behaviour instances directly
        for behaviour_id, behaviour in self.behaviour_manager.available_behaviours.items():
            behaviour_btn = self._create_behaviour_button(behaviour)
            all_behaviours_layout.addWidget(behaviour_btn)

        all_behaviours_layout.addStretch(1)
        all_scroll.setWidget(all_scroll_widget)
        all_tab_layout.addWidget(all_scroll)

        tabs.addTab(all_tab, "All")

        # Create a tab for each category with scroll area
        for category, behaviours in self.behaviour_manager.behaviours_by_category.items():
            category_tab = QWidget()
            category_tab_layout = QVBoxLayout(category_tab)
            category_tab_layout.setContentsMargins(0, 0, 0, 0)

            category_subtitle = QLabel(f"{category.value} Behaviours:")
            category_subtitle.setProperty("class", "subtitle")
            category_subtitle.setContentsMargins(5, 5, 5, 5)
            category_tab_layout.addWidget(category_subtitle)

            # Create scroll area for behaviours
            category_scroll = QScrollArea()
            category_scroll.setWidgetResizable(True)
            category_scroll.setFrameShape(QFrame.Shape.NoFrame)

            # Create widget to hold behaviour buttons
            category_scroll_widget = QWidget()
            category_behaviours_layout = QVBoxLayout(category_scroll_widget)

            # behaviours is now a list of BaseBehaviour instances
            for behaviour in behaviours:
                behaviour_btn = self._create_behaviour_button(behaviour)
                category_behaviours_layout.addWidget(behaviour_btn)

            category_behaviours_layout.addStretch(1)
            category_scroll.setWidget(category_scroll_widget)
            category_tab_layout.addWidget(category_scroll)

            # Add tab with category name
            tabs.addTab(category_tab, category.value)

        content_layout.addWidget(tabs)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 11px; color: #666; margin-top: 10px;")
        content_layout.addWidget(self.status_label)

        # Current behaviour info
        self.current_behaviour_label = QLabel("")
        self.current_behaviour_label.setStyleSheet("font-size: 11px; color: #666;")
        content_layout.addWidget(self.current_behaviour_label)

        # Create a layout for the control buttons
        control_layout = QHBoxLayout()

        # Toggle idle cycle button
        self.toggle_idle_btn = QPushButton("Pause Idle Cycle")
        self.toggle_idle_btn.clicked.connect(self.toggle_idle_cycle)
        self.toggle_idle_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )
        control_layout.addWidget(self.toggle_idle_btn)

        # Stop button
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_behaviour)
        stop_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f08080;
                border: 1px solid #ff6060;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #ff6060;
            }
        """
        )
        control_layout.addWidget(stop_btn)

        content_layout.addLayout(control_layout)

    def _create_behaviour_button(self, behaviour: BaseBehaviour) -> QPushButton:
        """Helper method to create a behaviour button with consistent styling"""
        # Use display_name from the behaviour instance
        display_text = behaviour.display_name
        behaviour_btn = QPushButton(display_text)
        behaviour_btn.setProperty("behaviour_id", behaviour.id)
        behaviour_btn.clicked.connect(self.run_behaviour)
        behaviour_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px 10px;
                text-align: left;
                margin: 1px 0px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )
        return behaviour_btn

    def update_idle_cycle_button(self, is_paused: bool):
        if is_paused:
            self.toggle_idle_btn.setText("Resume Idle Cycle")
            self.toggle_idle_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #90ee90;
                    border: 1px solid #70cc70;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #70cc70;
                }
            """
            )
        else:
            self.toggle_idle_btn.setText("Pause Idle Cycle")
            self.toggle_idle_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """
            )

    def run_behaviour(self):
        sender = self.sender()
        behaviour_id = sender.property("behaviour_id")

        if self.behaviour_manager.is_behaviour_running():
            self.status_label.setText("Wait for current behaviour to finish")
            self.status_label.setStyleSheet("font-size: 11px; color: #ff5500;")
        else:
            self.status_label.setText(f"Running behaviour: {behaviour_id}")
            self.status_label.setStyleSheet("font-size: 11px; color: #008800;")
            self.behaviour_manager.run_behaviour(behaviour_id)

    def stop_behaviour(self):
        if self.behaviour_manager.is_behaviour_running():
            self.behaviour_manager.terminate_behaviour()
            self.status_label.setText("Behaviour stopped")
            self.status_label.setStyleSheet("font-size: 11px; color: #ff5500;")
        else:
            self.status_label.setText("No behaviour running")
            self.status_label.setStyleSheet("font-size: 11px; color: #666;")

    def update_status(self):
        if self.behaviour_manager.is_behaviour_running():
            current_behaviour = self.behaviour_manager.current_behaviour
            self.status_label.setText("Behaviour is running")
            self.status_label.setStyleSheet("font-size: 11px; color: #008800;")
            # current_behaviour is now a BaseBehaviour instance
            display_name = current_behaviour.display_name if current_behaviour else "Unknown"
            self.current_behaviour_label.setText(f"Current: {display_name}")
            self.current_behaviour_label.setStyleSheet("font-size: 11px; color: #008800;")
        else:
            self.status_label.setText("Ready to run behaviours")
            self.status_label.setStyleSheet("font-size: 11px; color: #666;")
            self.current_behaviour_label.setText("")

    def position_for_os(self):
        """Position the window at the top right of the screen"""

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
