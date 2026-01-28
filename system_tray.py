from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import os
import sys
import platform

from resource_path import resource_path
from popup_window import PopupWindow
from app_logger import app_logger
from user_automation_manager import IdleCycleStatus, UserAutomationManager


class SystemTrayApp:
    def __init__(self, user_automation_manager: UserAutomationManager):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")
        self.app.setQuitOnLastWindowClosed(False)

        self.user_automation_manager = user_automation_manager
        self.behaviour_manager = user_automation_manager.behaviour_manager

        self.popup = PopupWindow(self.user_automation_manager, self.toggle_idle_cycle)

        try:
            stylesheet_path = resource_path("static/styles.qss")
            app_logger.info(f"Loading stylesheet from: {stylesheet_path}")
            with open(stylesheet_path, "r") as f:
                styles = f.read()
                self.app.setStyleSheet(styles)
        except Exception as e:
            app_logger.error(f"Error loading stylesheet: {str(e)}")

        # Log platform and environment info
        app_logger.info(f"Platform: {platform.system()}")
        app_logger.info(f"Desktop environment: {os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')}")
        app_logger.info(f"Session type: {os.environ.get('XDG_SESSION_TYPE', 'Unknown')}")
        app_logger.info(f"Wayland display: {os.environ.get('WAYLAND_DISPLAY', 'Not set')}")

        # Initialize Qt system tray icon
        self.tray = None
        self.init_retry_count = 0
        app_logger.info("Using QSystemTrayIcon for system tray")
        self.init_system_tray()

        # Status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

    def init_system_tray(self):
        """Initialize Qt system tray with retry logic"""

        app_logger.info(f"Attempting Qt tray init (attempt #{self.init_retry_count + 1})")

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.init_retry_count += 1
            if self.init_retry_count < 10:
                app_logger.warning(f"System tray not available yet. Retry #{self.init_retry_count}")
                QTimer.singleShot(500, self.init_system_tray)
            else:
                app_logger.error("System tray not available after retries. Showing popup as fallback.")
                self.popup.show()
            return

        app_logger.info("Qt system tray is available!")

        # Load icon - try multiple sizes for best display
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        icon = QIcon()

        # Add multiple icon sizes for different DPI/scaling scenarios
        for size in [16, 22, 24, 32, 48, 64]:
            icon_path = os.path.join(parent_dir, "static", "logos", f"user_automation_logo_{size}.png")
            if os.path.exists(icon_path):
                icon.addFile(icon_path, QSize(size, size))
                app_logger.info(f"Added icon size: {size}x{size}")
            elif size == 32:  # Fallback to the one we know exists
                icon_path_32 = os.path.join(parent_dir, "static", "logos", "user_automation_logo_32.png")
                if os.path.exists(icon_path_32):
                    pixmap = QPixmap(icon_path_32)
                    scaled_pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation)
                    icon.addPixmap(scaled_pixmap)
                    app_logger.info(f"Added scaled icon from 32x32 to {size}x{size}")

        if icon.isNull():
            app_logger.warning("Failed to load custom icon, using fallback")
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

        try:
            self.tray = QSystemTrayIcon(self.app)
            self.tray.setIcon(icon)

            # Set tooltip based on platform
            is_ubuntu = "ubuntu" in platform.platform().lower()
            if is_ubuntu:
                self.tray.setToolTip("User Automation Client - Right-click for menu")
            else:
                self.tray.setToolTip("User Automation Client - Click to show/hide")

            # Connect activated signal for clicks - handle ALL click types
            self.tray.activated.connect(self.on_tray_activated)

            # Create context menu - required for Ubuntu/AppIndicator to work properly
            # Note: On Ubuntu/GNOME, left-clicks don't work with QSystemTrayIcon
            # Users must use the context menu to interact with the app
            menu = QMenu()

            # Make Show/Hide the first and most prominent action
            show_hide_action = menu.addAction("Show/Hide Window")
            show_hide_action.triggered.connect(self.toggle_popup)
            # Set as default action (bold text) - triggered on double-click where supported
            menu.setDefaultAction(show_hide_action)

            menu.addSeparator()
            quit_action = menu.addAction("Quit")
            quit_action.triggered.connect(self.quit_app)

            self.tray.setContextMenu(menu)

            self.tray.show()

            app_logger.info(f"Qt tray icon created. Visible: {self.tray.isVisible()}")
            if is_ubuntu:
                app_logger.warning("Ubuntu detected: Left-click on tray icon may not work due to AppIndicator limitations. Use right-click menu instead.")
            else:
                app_logger.info("Tray icon with context menu - left-click should toggle popup")

        except Exception as e:
            app_logger.error(f"Error creating Qt system tray icon: {str(e)}")
            self.popup.show()

    def on_tray_activated(self, reason):
        """Handle Qt system tray activation - toggle popup on left/middle/double click"""
        app_logger.info(f"Qt tray activated with reason: {reason} ({reason.name})")

        try:
            # Toggle popup on left-click, middle-click, and double-click
            # Right-click (Context) will show the menu automatically
            if reason == QSystemTrayIcon.ActivationReason.Trigger:
                app_logger.info("Left-click detected - toggling popup")
                self.toggle_popup()
            elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
                app_logger.info("Middle-click detected - toggling popup")
                self.toggle_popup()
            elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                app_logger.info("Double-click detected - toggling popup")
                self.toggle_popup()
            elif reason == QSystemTrayIcon.ActivationReason.Context:
                # Right-click shows context menu - don't toggle popup
                app_logger.info("Right-click detected - showing context menu")
            else:
                # Unknown reason - toggle popup
                app_logger.info("Unknown activation reason - toggling popup")
                self.toggle_popup()

        except Exception as e:
            app_logger.error(f"Error handling tray icon click: {str(e)}")

    def toggle_idle_cycle(self):
        try:
            if self.user_automation_manager.idle_cycle_status == IdleCycleStatus.PAUSED:
                self.user_automation_manager.set_idle_cycle_status(
                    IdleCycleStatus.RUNNING
                )
                if self.popup.isVisible():
                    self.popup.update_idle_cycle_button(False)
            else:
                self.user_automation_manager.set_idle_cycle_status(
                    IdleCycleStatus.PAUSED
                )
                if self.popup.isVisible():
                    self.popup.update_idle_cycle_button(True)

        except Exception as e:
            app_logger.error(f"Error toggling idle cycle: {str(e)}")

    def update_status(self):
        try:
            # Update popup status if visible
            if self.popup.isVisible():
                self.popup.update_status()

        except Exception as e:
            app_logger.error(f"Error updating status: {str(e)}")

    def toggle_popup(self):
        try:
            if self.popup.isVisible():
                app_logger.info("Hiding popup window")
                self.popup.hide()
            else:
                app_logger.info("Showing popup window")
                self.popup.update_status()
                self.popup.update_idle_cycle_button(
                    self.user_automation_manager.idle_cycle_status
                    == IdleCycleStatus.PAUSED
                )
                self.popup.position_for_os()
                self.popup.show()
                self.popup.raise_()
                self.popup.activateWindow()
        except Exception as e:
            app_logger.error(f"Error showing popup: {str(e)}")

    def quit_app(self):
        try:
            app_logger.info("Quitting application...")

            if self.behaviour_manager.is_behaviour_running():
                self.behaviour_manager.terminate_behaviour()

            # Hide tray icon before quitting
            if self.tray:
                self.tray.hide()

            self.app.quit()
        except Exception as e:
            app_logger.error(f"Error quitting app: {str(e)}")
            sys.exit(1)

    def run(self):
        try:
            return self.app.exec()
        except Exception as e:
            app_logger.error(f"Error in app.exec_: {str(e)}")
            return 1
