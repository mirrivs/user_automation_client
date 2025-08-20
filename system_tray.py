from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import os
import sys
import platform

from resource_path import resource_path
from popup_window import PopupWindow
from app_logger import app_logger
from user_automation_manager import IdleCycleStatus, UserAutomationManager


class SystemTrayApp:
    def __init__(self, user_automation_manager: UserAutomationManager):
        try:
            if platform.system() == "Linux":
                from PyQt5.QtCore import QLibraryInfo
                plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)

                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
                app_logger.info(
                    f"Setting QT_QPA_PLATFORM_PLUGIN_PATH to {plugins_path}"
                )

                if "XDG_RUNTIME_DIR" not in os.environ:
                    runtime_dir = f"/run/user/{os.getuid()}"
                    if os.path.exists(runtime_dir):
                        os.environ["XDG_RUNTIME_DIR"] = runtime_dir
                        app_logger.info(f"Setting XDG_RUNTIME_DIR to {runtime_dir}")

                os.environ["QT_QPA_PLATFORM"] = "xcb"
                app_logger.info("Setting QT_QPA_PLATFORM to xcb")
        except Exception as e:
            app_logger.error(f"Error setting up Qt environment: {str(e)}")

        self.app = QApplication([])
        self.app.setStyle("Fusion")

        # Load stylesheet
        try:
            stylesheet_path = resource_path("static/styles.qss")
            app_logger.info(f"Loading stylesheet from: {stylesheet_path}")
            with open(stylesheet_path, "r") as f:
                styles = f.read()
                self.app.setStyleSheet(styles)
        except Exception as e:
            app_logger.error(f"Error loading stylesheet: {str(e)}")

        self.app.setQuitOnLastWindowClosed(False)

        self.user_automation_manager = user_automation_manager
        self.behaviour_manager = user_automation_manager.behaviour_manager

        self.popup = PopupWindow(self.user_automation_manager, self.toggle_idle_cycle)

        # Set the icon path
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(
            parent_dir, "static", "logos", "user_automation_logo_32.png"
        )
        if not os.path.exists(icon_path):
            # Fallback to a default icon if the custom one doesn't exist
            app_logger.warning(f"Icon not found at: {icon_path}, using default")
            # Use PyQt5 QStyle enum
            self.icon = QIcon(
                QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
            )
        else:
            self.icon = QIcon(icon_path)

        try:
            # Create the system tray icon
            self.tray = QSystemTrayIcon(self.icon)
            self.tray.setToolTip("User Automation Client")

            # Create the context menu for the tray
            self.menu = QMenu()

            self.tray.setContextMenu(self.menu)
            self.menu.aboutToShow.connect(self.toggle_popup)
            self.tray.activated.connect(self.on_tray_activated)

            # Make the tray icon visible
            self.tray.setVisible(True)

            # Status update timer
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_status)
            self.status_timer.start(1000)  # Update every second
        except Exception as e:
            app_logger.error(f"Error initializing system tray: {str(e)}")
            # If system tray fails, show the popup window directly
            self.popup.show()

    def on_tray_activated(self, reason):
        try:
            # Use PyQt5 QSystemTrayIcon enums
            if reason == QSystemTrayIcon.Trigger:
                # Left click (or single click)
                self.toggle_popup()
            elif reason == QSystemTrayIcon.DoubleClick:
                # Optional: handle double-click differently if needed
                self.toggle_popup()
            # Note: right-click (Context) shows the context menu automatically
        except Exception as e:
            app_logger.error(f"Error handling tray icon click: {str(e)}")

    def toggle_idle_cycle(self):
        try:
            if self.user_automation_manager.idle_cycle_status == IdleCycleStatus.PAUSED:
                self.user_automation_manager.set_idle_cycle_status(
                    IdleCycleStatus.RUNNING
                )
                if hasattr(self, 'toggle_idle_action'):
                    self.toggle_idle_action.setText("Pause Idle Cycle")
                if self.popup.isVisible():
                    self.popup.update_idle_cycle_button(False)
            else:
                self.user_automation_manager.set_idle_cycle_status(
                    IdleCycleStatus.PAUSED
                )
                if hasattr(self, 'toggle_idle_action'):
                    self.toggle_idle_action.setText("Resume Idle Cycle")
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
                self.popup.hide()
            else:
                self.popup.update_status()
                self.popup.update_idle_cycle_button(
                    self.user_automation_manager.idle_cycle_status
                    == IdleCycleStatus.PAUSED
                )
                self.popup.position_for_os()
                self.popup.show()
        except Exception as e:
            app_logger.error(f"Error showing popup: {str(e)}")

    def quit_app(self):
        try:
            # Make sure to terminate any running behaviour
            if self.behaviour_manager.is_behaviour_running():
                self.behaviour_manager.terminate_behaviour()
            self.app.quit()
        except Exception as e:
            app_logger.error(f"Error quitting app: {str(e)}")
            sys.exit(1)  # Force exit if normal quit fails

    def run(self):
        try:
            # Use PyQt5 app.exec_()
            return self.app.exec_()
        except Exception as e:
            app_logger.error(f"Error in app.exec_: {str(e)}")
            return 1