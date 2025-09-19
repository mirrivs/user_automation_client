import threading
import time
import socket
import json
import logging
from enum import Enum
from typing import Optional

import requests
import websocket

from app_config import AppConfig, app_config, save_app_config
from behaviour_manager import Behaviour, BehaviourCategory, BehaviourManager
from config_handler import save_config
from json_encoder import EnumEncoder

available_behaviours: dict[Behaviour] = {
    "attack_phishing": {
        "name": "attack_phishing",
        "category": BehaviourCategory.ATTACK,
        "description": "Phishing attack",
    },
    "attack_ransomware": {
        "name": "attack_ransomware",
        "category": BehaviourCategory.ATTACK,
        "description": "Ransomware attack",
    },
    "attack_reverse_shell": {
        "name": "attack_reverse_shell",
        "category": BehaviourCategory.ATTACK,
        "description": "Reverse shell attack",
    },
    "procrastination": {
        "name": "procrastination",
        "category": BehaviourCategory.IDLE,
        "description": "Simulates procrastination activities like browsing",
    },
    # "work_developer": {"name": "work_developer", "category": BehaviourCategory.IDLE,
    #     "description": "Simulates developer activities"},
    "work_emails": {
        "name": "work_emails",
        "category": BehaviourCategory.IDLE,
        "description": "Simulates working with emails",
    },
    "work_organization_web": {
        "name": "work_organization_web",
        "category": BehaviourCategory.IDLE,
        "description": "Simulates browsing organization website",
    },
    # "work_word": {"name": "work_word", "category": BehaviourCategory.IDLE,
    #     "description": "Simulates word on Microsoft Word"},
}


class IdleCycleStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class UserAutomationManager:
    """
    User Automation Manager
    Used to manage server config synchronization and behaviour execution
    """

    def __init__(self, config: AppConfig = {}):
        # Use a single configuration source
        self.config: AppConfig = config

        self.behaviour_manager = BehaviourManager(available_behaviours)

        self.behaviour_cycle_thread = threading.Thread(
            target=self._run_behaviour_cycle, name="Behaviour cycle thread", daemon=True
        )
        self.server_connection_thread = threading.Thread(
            target=self._run_server_connection,
            name="Server connection thread",
            daemon=True,
        )

        self.idle_cycle_status = IdleCycleStatus.RUNNING

        # Server connection attributes
        self.access_token: Optional[str] = None
        self.websocket_connection: Optional[websocket.WebSocket] = None
        self.is_connected = False

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def set_idle_cycle_status(self, status: IdleCycleStatus):
        self.idle_cycle_status = status

    def _authenticate_with_server(self) -> bool:
        """Authenticate with the server and get access token"""
        try:
            username = app_config["behaviour"]["general"]["user"]["email"]
            password = app_config["behaviour"]["general"]["user"]["password"]
            hostname = socket.gethostname()

            if not username or not password:
                self.logger.error("Username or password not configured")
                return False

            # Prepare authentication data
            auth_data = {
                "username": username,
                "password": password,
                "hostname": hostname,
            }

            # Send authentication request
            auth_url = f"{app_config['app']['user_automation_server_http']}/client/connect"
            self.logger.info(f"Authenticating with server at {auth_url}")

            response = requests.post(
                auth_url,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )

            if response.status_code == 200:
                auth_response = response.json()
                self.access_token = auth_response.get("access_token")
                
                # Merge server config with local config
                server_config = auth_response.get("client_config", {})
                if server_config:
                    self._merge_config(server_config)
                    
                self.logger.info("Successfully authenticated with server")
                return True
            else:
                self.logger.error(
                    f"Authentication failed: {response.status_code} - {response.text}"
                )
                return False

        except requests.RequestException as e:
            self.logger.error(f"Error during authentication: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            return False

    def _connect_websocket(self) -> bool:
        """Establish WebSocket connection for real-time updates"""
        try:
            ws_url = f"{app_config['app']['user_automation_server_websocket']}/client/client_socket"

            self.logger.info(f"Connecting to WebSocket at {ws_url}")

            # Create WebSocket connection
            self.websocket_connection = websocket.WebSocket()
            self.websocket_connection.connect(ws_url)

            # Send authentication token
            self.websocket_connection.send(self.access_token)

            self.logger.info("WebSocket connection established")
            return True

        except Exception as e:
            self.logger.error(f"Error connecting to WebSocket: {e}")
            return False

    def _handle_websocket_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "config_update":
                config = data.get("config", {})
                if config:
                    self._merge_config(config)

            elif action == "update_behaviour_config":
                behaviour_id = data.get("behaviour_id")
                behaviour_config = data.get("config", {})

                if behaviour_id and behaviour_config:
                    self._update_behaviour_config(behaviour_id, behaviour_config)

            elif action == "run_behaviour":
                behaviour_id = data.get("behaviour_id")
                if behaviour_id:
                    self.run_behaviour(behaviour_id, True)
                    
            else:
                self.logger.debug(f"Unknown action type: {action}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing WebSocket message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
    
    def run_behaviour(self, behaviour_id: str, force: bool = False):
        """Run a specific behaviour"""
        self.behaviour_manager.run_behaviour(behaviour_id, force)
        self.logger.info(f"Running behaviour: {behaviour_id}")

    def _merge_config(self, new_config: dict):
        """Merge new configuration with existing config and save to file"""
        try:
            # Deep merge the configuration
            self._deep_merge_dict(self.config, new_config)
            
            # Save to file
            save_app_config(self.config)
            
            self.logger.info(f"Configuration updated and saved: {list(new_config.keys())}")
                
        except Exception as e:
            self.logger.error(f"Error merging config: {e}")
            raise e

    def _deep_merge_dict(self, target: dict, source: dict):
        """Deep merge source dictionary into target dictionary"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(target[key], value)
            else:
                target[key] = value

    def _update_behaviour_config(self, behaviour_id: str, behaviour_config: dict):
        """Update configuration for a specific behaviour and save to file"""
        try:
            # Ensure the nested structure exists
            if "behaviour" not in self.config:
                self.config["behaviour"] = {}
            if "behaviours" not in self.config["behaviour"]:
                self.config["behaviour"]["behaviours"] = {}
            if behaviour_id not in self.config["behaviour"]["behaviours"]:
                self.config["behaviour"]["behaviours"][behaviour_id] = {}
            
            self.config["behaviour"]["behaviours"][behaviour_id] = behaviour_config 
                
            save_app_config(self.config)
            
            self.logger.info(f"Behaviour configuration updated and saved for {behaviour_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating behaviour config for {behaviour_id}: {e}")
            raise e

    def _send_status_update(self):
        """Send status update to server via WebSocket"""
        try:
            if not self.websocket_connection:
                return

            status_data = {
                "type": "status_update",
                "hostname": socket.gethostname(),
                "current_behaviour": self.behaviour_manager.current_behaviour,
                "idle_cycle_status": self.idle_cycle_status.value,
                "timestamp": time.time(),
            }

            self.websocket_connection.send(json.dumps(status_data, cls=EnumEncoder))
            self.logger.debug("Status update sent to server")

        except Exception as e:
            self.logger.error(f"Error sending status update: {e}")

    def _run_server_connection(self):
        """Main server connection loop"""
        reconnect_delay = 5  # seconds
        max_reconnect_delay = 60  # seconds

        while True:
            try:
                # Authenticate with server
                if not self.is_connected:
                    if self._authenticate_with_server():
                        # Establish WebSocket connection
                        if self._connect_websocket():
                            self.is_connected = True
                            reconnect_delay = 5  # Reset delay on successful connection
                            self.logger.info("Successfully connected to server")
                        else:
                            self.logger.error(
                                "Failed to establish WebSocket connection"
                            )
                    else:
                        self.logger.error("Failed to authenticate with server")

                # Handle WebSocket messages
                if self.is_connected and self.websocket_connection:
                    try:
                        # Check for incoming messages (non-blocking)
                        self.websocket_connection.settimeout(1.0)
                        message = self.websocket_connection.recv()

                        if message:
                            self._handle_websocket_message(message)

                    except websocket.WebSocketTimeoutException:
                        # Timeout is expected for non-blocking receive
                        pass
                    except websocket.WebSocketConnectionClosedException:
                        self.logger.warning("WebSocket connection closed by server")
                        self.is_connected = False
                        self.websocket_connection = None
                    except Exception as e:
                        self.logger.error(f"Error in WebSocket communication: {e}")
                        self.is_connected = False
                        self.websocket_connection = None

                # Send periodic status updates
                if self.is_connected:
                    self._send_status_update()

                # If not connected, wait before retry
                if not self.is_connected:
                    self.logger.info(
                        f"Retrying connection in {reconnect_delay} seconds..."
                    )
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                else:
                    time.sleep(10)  # Status update interval

            except KeyboardInterrupt:
                self.logger.info("Server connection thread interrupted")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in server connection: {e}")
                self.is_connected = False
                time.sleep(reconnect_delay)

    def _run_behaviour_cycle(self):
        """Main behaviour execution cycle"""
        old_config = self.config.copy()

        while True:
            try:
                config_changed = old_config != self.config
                if config_changed:
                    old_config = self.config.copy()

                if config_changed:
                    # Only reload if behaviour manager has this method
                    if hasattr(self.behaviour_manager, 'load_behaviour_queue'):
                        self.behaviour_manager.load_behaviour_queue()
                    self.logger.info("Configuration changed - behaviour manager reloaded")

                # Run next behaviour if cycle is running and no behaviour is currently active
                if (
                    self.idle_cycle_status == IdleCycleStatus.RUNNING
                    and not self.behaviour_manager.is_behaviour_running()
                ):
                    self.behaviour_manager.run_next_behaviour()

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in behaviour cycle: {e}")
                time.sleep(5)  # Wait before retrying

    def start(self):
        """Start both behaviour cycle and server connection threads"""
        self.logger.info("Starting User Automation Manager")
        self.behaviour_cycle_thread.start()
        self.server_connection_thread.start()

    def stop(self):
        """Stop the manager and close connections"""
        self.logger.info("Stopping User Automation Manager")
        self.idle_cycle_status = IdleCycleStatus.STOPPED

        if self.websocket_connection:
            try:
                self.websocket_connection.close()
            except:
                pass

        self.is_connected = False

    def get_config(self):
        """Get the current configuration"""
        return self.config.copy()

    def get_behaviour_config(self, behaviour_id: str):
        """Get configuration for a specific behaviour"""
        try:
            return self.config.get("behaviour", {}).get("behaviours", {}).get(behaviour_id, {}).copy()
        except Exception:
            return {}

    def is_server_connected(self):
        """Check if connected to server"""
        return self.is_connected