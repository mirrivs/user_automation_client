from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtSvg, QtGui

import platform
import os

from resource_path import resource_path
from user_automation_manager import UserAutomationManager


class PopupWindow(QWidget):
    def __init__(
        self, user_automation_manager: UserAutomationManager, toggle_idle_cycle_fn
    ):
        super().__init__()

        self.user_automation_manager = user_automation_manager
        self.behaviour_manager = user_automation_manager.behaviour_manager

        self.toggle_idle_cycle = toggle_idle_cycle_fn

        # Set window flags and attributes for PyQt5
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

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
        svg_renderer = QtSvg.QSvgRenderer(svg_path)
        
        # Create QImage for PyQt5
        img = QtGui.QImage(16, 16, QtGui.QImage.Format_ARGB32)
        
        img.fill(0)
        painter = QtGui.QPainter(img)
        svg_renderer.render(painter)
        painter.end()

        # Set the icon
        icon = QtGui.QIcon(QtGui.QPixmap.fromImage(img))
        close_btn = QPushButton()
        close_btn.setIcon(icon)

        # Set common button properties
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.hide)
        close_btn.setMaximumWidth(20)
        close_btn.setProperty("class", "btn-transparent")

        navbar_layout.addWidget(close_btn)
        content_layout.addWidget(navbar)

        # Create tabs for All and Idle behaviours
        tabs = QTabWidget()

        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)

        all_subtitle = QLabel("All Behaviours:")
        all_subtitle.setProperty("class", "subtitle")
        all_layout.addWidget(all_subtitle)

        # Add buttons for each behaviour
        all_behaviours_layout = QVBoxLayout()

        for (
            behaviour_id,
            behaviour,
        ) in self.behaviour_manager.available_behaviours.items():
            behaviour_btn = QPushButton(behaviour["name"])
            behaviour_btn.setProperty("behaviour_id", behaviour_id)
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
            all_behaviours_layout.addWidget(behaviour_btn)

        all_layout.addLayout(all_behaviours_layout)
        all_layout.addStretch(1)

        # IDLE BEHAVIORS TAB
        idle_tab = QWidget()
        idle_layout = QVBoxLayout(idle_tab)

        idle_subtitle = QLabel("Idle Behaviours:")
        idle_subtitle.setProperty("class", "subtitle")
        idle_layout.addWidget(idle_subtitle)

        # Add buttons for each idle behaviour
        idle_behaviours_layout = QVBoxLayout()

        for behaviour_id, behaviour in self.behaviour_manager.idle_behaviours.items():
            behaviour_btn = QPushButton(behaviour["name"])
            behaviour_btn.setProperty("behaviour_id", behaviour_id)
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
            idle_behaviours_layout.addWidget(behaviour_btn)

        idle_layout.addLayout(idle_behaviours_layout)
        idle_layout.addStretch(1)

        # Add tabs to tab widget
        tabs.addTab(all_tab, "All")
        tabs.addTab(idle_tab, "Idle")
        content_layout.addWidget(tabs)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "font-size: 11px; color: #666; margin-top: 10px;"
        )
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
            self.status_label.setText(f"Wait for current behaviour to finish")
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
            self.status_label.setText(f"Behaviour is running")
            self.status_label.setStyleSheet("font-size: 11px; color: #008800;")
            self.current_behaviour_label.setText(
                f"Current: {current_behaviour['name']}"
            )
            self.current_behaviour_label.setStyleSheet(
                "font-size: 11px; color: #008800;"
            )
        else:
            self.status_label.setText(f"Ready to run behaviours")
            self.status_label.setStyleSheet("font-size: 11px; color: #666;")
            self.current_behaviour_label.setText("")

    def position_for_os(self):
        """Position the window according to the operating system's tray location"""

        # Use QApplication.desktop() for PyQt5
        screen_geometry = QApplication.desktop().availableGeometry()
        screen_pos = screen_geometry.topLeft()
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
                x = screen_geometry.width() - (self.width() - screen_pos.x()) - padding
                y = screen_pos.y() + padding
            elif "kde" in desktop_env:
                x = screen_geometry.width() - (self.width() - screen_pos.x()) - padding
                y = (
                    screen_geometry.height()
                    - (self.height() - screen_pos.y())
                    - padding
                )
            else:
                x = screen_geometry.width() - (self.width() - screen_pos.x()) - padding
                y = (
                    screen_geometry.height()
                    - (self.height() - screen_pos.y())
                    - padding
                )

        self.move(x, y)

    def mousePressEvent(self, event):
        event.accept()

    def mouseMoveEvent(self, event):
        event.accept()