import os
import platform
import sys

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from resource_path import resource_path
from src.gui.popup_window import PopupWindow
from src.logger import app_logger
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
            app_logger.debug(f"Loading stylesheet from: {stylesheet_path}")
            with open(stylesheet_path, "r") as f:
                self.app.setStyleSheet(f.read())
        except Exception as e:
            app_logger.error(f"Error loading stylesheet: {str(e)}")

        app_logger.debug(f"Platform: {platform.system()}")
        app_logger.debug(f"Desktop environment: {os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')}")
        app_logger.debug(f"Session type: {os.environ.get('XDG_SESSION_TYPE', 'Unknown')}")
        app_logger.debug(f"Wayland display: {os.environ.get('WAYLAND_DISPLAY', 'Not set')}")

        self.tray = None
        self.tray_menu = None
        self.status_action = None
        self.init_retry_count = 0
        self.init_system_tray()

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

    def init_system_tray(self):
        app_logger.debug(f"Attempting Qt tray init (attempt #{self.init_retry_count + 1})")

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.init_retry_count += 1
            if self.init_retry_count < 10:
                app_logger.warning(f"System tray not available yet. Retry #{self.init_retry_count}")
                QTimer.singleShot(500, self.init_system_tray)
            else:
                app_logger.error("System tray not available after retries. Showing popup as fallback.")
                self.popup.show()
            return

        icon = QIcon()
        for size in [16, 22, 24, 32, 48, 64]:
            icon_path = resource_path(os.path.join("static", "logos", f"user_automation_logo_{size}.png"))
            if os.path.exists(icon_path):
                icon.addFile(icon_path, QSize(size, size))
            elif size == 32:
                icon_path_32 = resource_path(os.path.join("static", "logos", "user_automation_logo_32.png"))
                if os.path.exists(icon_path_32):
                    pixmap = QPixmap(icon_path_32)
                    scaled_pixmap = pixmap.scaled(
                        size,
                        size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    icon.addPixmap(scaled_pixmap)

        if icon.isNull():
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

        try:
            self.tray = QSystemTrayIcon(self.app)
            self.tray.setIcon(icon)
            self.tray.setToolTip("User Automation Client")
            self.tray.activated.connect(self.on_tray_activated)

            self.tray_menu = QMenu()
            self.status_action = self.tray_menu.addAction("Status: Ready")
            self.status_action.setEnabled(False)
            self.tray_menu.addSeparator()

            open_action = self.tray_menu.addAction("Open Dashboard")
            open_action.triggered.connect(self.toggle_popup)

            settings_action = self.tray_menu.addAction("Settings")
            settings_action.triggered.connect(self.show_settings)

            pause_action = self.tray_menu.addAction("Pause/Resume Idle Cycle")
            pause_action.triggered.connect(self.toggle_idle_cycle)

            stop_action = self.tray_menu.addAction("Stop Current Behaviour")
            stop_action.triggered.connect(self.popup.stop_behaviour)

            self.tray_menu.addSeparator()
            quit_action = self.tray_menu.addAction("Quit")
            quit_action.triggered.connect(self.quit_app)

            self.tray.setContextMenu(self.tray_menu)
            self.tray.show()
            self.update_status()

        except Exception as e:
            app_logger.error(f"Error creating Qt system tray icon: {str(e)}")
            self.popup.show()

    def on_tray_activated(self, reason):
        try:
            if reason in {
                QSystemTrayIcon.ActivationReason.Trigger,
                QSystemTrayIcon.ActivationReason.MiddleClick,
                QSystemTrayIcon.ActivationReason.DoubleClick,
            }:
                self.toggle_popup()
        except Exception as e:
            app_logger.error(f"Error handling tray icon click: {str(e)}")

    def toggle_idle_cycle(self):
        try:
            if self.user_automation_manager.idle_cycle_status == IdleCycleStatus.PAUSED:
                self.user_automation_manager.set_idle_cycle_status(IdleCycleStatus.RUNNING)
                if self.popup.isVisible():
                    self.popup.update_idle_cycle_button(False)
            else:
                self.user_automation_manager.set_idle_cycle_status(IdleCycleStatus.PAUSED)
                if self.popup.isVisible():
                    self.popup.update_idle_cycle_button(True)
            self.update_status()
        except Exception as e:
            app_logger.error(f"Error toggling idle cycle: {str(e)}")

    def update_status(self):
        try:
            if self.popup.isVisible():
                self.popup.refresh_ui()
                self.popup.update_status()

            if self.status_action:
                current = self.behaviour_manager.current_behaviour
                if current is not None:
                    status = f"Running: {current.display_name}"
                else:
                    status = f"Idle Cycle: {self.user_automation_manager.idle_cycle_status.value.title()}"
                self.status_action.setText(f"Status: {status}")

        except Exception as e:
            app_logger.error(f"Error updating status: {str(e)}")

    def show_settings(self):
        try:
            self.popup.refresh_ui()
            self.popup.show_settings()
            self.popup.position_for_os()
            self.popup.show()
            self.popup.raise_()
            self.popup.activateWindow()
        except Exception as e:
            app_logger.error(f"Error opening settings: {str(e)}")

    def toggle_popup(self):
        try:
            if self.popup.isVisible():
                self.popup.hide()
            else:
                self.popup.refresh_ui()
                self.popup.show_behaviours()
                self.popup.update_idle_cycle_button(
                    self.user_automation_manager.idle_cycle_status == IdleCycleStatus.PAUSED
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
