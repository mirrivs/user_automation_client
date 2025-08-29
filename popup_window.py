from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtSvg, QtGui
from enum import Enum
from typing import TypedDict, Optional, Dict
import platform
import os

from resource_path import resource_path
from user_automation_manager import UserAutomationManager


class BehaviourCategory(Enum):
    IDLE = "Idle"
    ATTACK = "Attack"


class Behaviour(TypedDict):
    name: str
    category: BehaviourCategory
    description: Optional[str]


class BehaviourListWidget(QWidget):
    """Widget for displaying behaviors grouped by categories"""
    
    def __init__(self, behaviours: Dict, run_behaviour_callback):
        super().__init__()
        self.behaviours = behaviours
        self.run_behaviour_callback = run_behaviour_callback
        self.init_ui()
    
    def init_ui(self):
        # Main layout with proper margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)
        
        # Group behaviours by category
        categories = {}
        for behaviour_id, behaviour in self.behaviours.items():
            category = behaviour["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((behaviour_id, behaviour))
        
        # Create sections for each category
        for category, behaviours in categories.items():
            # Category label
            category_label = QLabel(f"{category.value} Behaviours:")
            category_label.setProperty("class", "category-label")
            content_layout.addWidget(category_label)
            
            # Behaviours in this category
            for behaviour_id, behaviour in behaviours:
                behaviour_btn = QPushButton(behaviour["name"])
                behaviour_btn.setProperty("behaviour_id", behaviour_id)
                behaviour_btn.setProperty("class", "behaviour-button")
                behaviour_btn.clicked.connect(self.run_behaviour_callback)
                behaviour_btn.setToolTip(behaviour.get("description", ""))
                content_layout.addWidget(behaviour_btn)
        
        # Add stretch at the end
        content_layout.addStretch()
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)


class SettingsWidget(QWidget):
    """Widget for settings - currently empty but structured for future expansion"""
    
    def __init__(self, toggle_idle_cycle_callback, update_idle_button_callback):
        super().__init__()
        self.toggle_idle_cycle_callback = toggle_idle_cycle_callback
        self.update_idle_button_callback = update_idle_button_callback
        self.init_ui()
    
    def init_ui(self):
        # Main layout with proper margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(10)
        
        # Idle Cycle Control Section
        idle_section_label = QLabel("Idle Cycle Control:")
        idle_section_label.setProperty("class", "section-label")
        content_layout.addWidget(idle_section_label)
        
        # Toggle idle cycle button
        self.toggle_idle_btn = QPushButton("Pause Idle Cycle")
        self.toggle_idle_btn.setProperty("class", "settings-button")
        self.toggle_idle_btn.clicked.connect(self.toggle_idle_cycle_callback)
        content_layout.addWidget(self.toggle_idle_btn)
        
        # Future settings placeholder
        placeholder_label = QLabel("Additional settings will be added here...")
        placeholder_label.setProperty("class", "placeholder-text")
        content_layout.addWidget(placeholder_label)
        
        # Add stretch at the end
        content_layout.addStretch()
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
    
    def update_idle_cycle_button(self, is_paused: bool):
        """Update the idle cycle button based on current state"""
        if is_paused:
            self.toggle_idle_btn.setText("Resume Idle Cycle")
            self.toggle_idle_btn.setProperty("class", "settings-button-paused")
        else:
            self.toggle_idle_btn.setText("Pause Idle Cycle")
            self.toggle_idle_btn.setProperty("class", "settings-button")
        
        # Force style refresh
        self.toggle_idle_btn.style().unpolish(self.toggle_idle_btn)
        self.toggle_idle_btn.style().polish(self.toggle_idle_btn)


class PopupWindow(QWidget):
    def __init__(self, user_automation_manager: UserAutomationManager, toggle_idle_cycle_fn):
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

        self.setFixedSize(320, 450)  # Slightly larger to accommodate new layout

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setProperty("class", "main-frame")

        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(self.main_frame)

        content_layout = QVBoxLayout(self.main_frame)

        # Navigation bar
        navbar = self.create_navbar()
        content_layout.addWidget(navbar)

        # Create tabs
        tabs = QTabWidget()
        
        # Behaviours tab
        behaviours_tab = BehaviourListWidget(
            self.behaviour_manager.available_behaviours, 
            self.run_behaviour
        )
        
        # Settings tab
        self.settings_tab = SettingsWidget(
            self.toggle_idle_cycle,
            self.update_idle_cycle_button
        )

        tabs.addTab(behaviours_tab, "Behaviours")
        tabs.addTab(self.settings_tab, "Settings")
        content_layout.addWidget(tabs)

        # Status section
        status_section = self.create_status_section()
        content_layout.addLayout(status_section)

        # Control buttons
        control_layout = self.create_control_buttons()
        content_layout.addLayout(control_layout)

    def create_navbar(self):
        """Create the navigation bar with title and close button"""
        navbar = QWidget()
        navbar.setProperty("class", "navbar")
        navbar_layout = QHBoxLayout(navbar)

        title = QLabel("User Automation Client")
        title.setProperty("class", "title")
        navbar_layout.addWidget(title)

        # Close button with SVG icon
        close_btn = self.create_close_button()
        navbar_layout.addWidget(close_btn)
        
        return navbar

    def create_close_button(self):
        """Create the close button with SVG icon"""
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
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.hide)
        close_btn.setMaximumWidth(20)
        close_btn.setProperty("class", "btn-transparent")
        
        return close_btn

    def create_status_section(self):
        """Create the status display section"""
        status_layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "status-label")
        status_layout.addWidget(self.status_label)

        # Current behaviour info
        self.current_behaviour_label = QLabel("")
        self.current_behaviour_label.setProperty("class", "current-behaviour-label")
        status_layout.addWidget(self.current_behaviour_label)
        
        return status_layout

    def create_control_buttons(self):
        """Create the control buttons layout"""
        control_layout = QHBoxLayout()

        # Stop button
        stop_btn = QPushButton("Stop Current")
        stop_btn.setProperty("class", "stop-button")
        stop_btn.clicked.connect(self.stop_behaviour)
        control_layout.addWidget(stop_btn)

        return control_layout

    def update_idle_cycle_button(self, is_paused: bool):
        """Update the idle cycle button in the settings tab"""
        self.settings_tab.update_idle_cycle_button(is_paused)

    def run_behaviour(self):
        """Handle running a behavior"""
        sender = self.sender()
        behaviour_id = sender.property("behaviour_id")

        if self.behaviour_manager.is_behaviour_running():
            self.status_label.setText("Wait for current behaviour to finish")
            self.status_label.setProperty("class", "status-label-error")
        else:
            behaviour_name = self.behaviour_manager.available_behaviours[behaviour_id]["name"]
            self.status_label.setText(f"Running: {behaviour_name}")
            self.status_label.setProperty("class", "status-label-running")
            self.behaviour_manager.run_behaviour(behaviour_id)
        
        # Force style refresh for status label
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def stop_behaviour(self):
        """Handle stopping the current behavior"""
        if self.behaviour_manager.is_behaviour_running():
            self.behaviour_manager.terminate_behaviour()
            self.status_label.setText("Behaviour stopped")
            self.status_label.setProperty("class", "status-label-error")
        else:
            self.status_label.setText("No behaviour running")
            self.status_label.setProperty("class", "status-label")
        
        # Force style refresh for status label
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def update_status(self):
        """Update the status display"""
        if self.behaviour_manager.is_behaviour_running():
            current_behaviour = self.behaviour_manager.current_behaviour
            self.status_label.setText("Behaviour is running")
            self.status_label.setProperty("class", "status-label-running")
            self.current_behaviour_label.setText(f"Current: {current_behaviour['name']}")
            self.current_behaviour_label.setProperty("class", "current-behaviour-label-running")
        else:
            self.status_label.setText("Ready to run behaviours")
            self.status_label.setProperty("class", "status-label")
            self.current_behaviour_label.setText("")
            self.current_behaviour_label.setProperty("class", "current-behaviour-label")
        
        # Force style refresh for labels
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.current_behaviour_label.style().unpolish(self.current_behaviour_label)
        self.current_behaviour_label.style().polish(self.current_behaviour_label)

    def position_for_os(self):
        """Position the window according to the operating system's tray location"""
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
                y = screen_geometry.height() - (self.height() - screen_pos.y()) - padding
            else:
                x = screen_geometry.width() - (self.width() - screen_pos.x()) - padding
                y = screen_geometry.height() - (self.height() - screen_pos.y()) - padding

        self.move(x, y)

    def mousePressEvent(self, event):
        event.accept()

    def mouseMoveEvent(self, event):
        event.accept()