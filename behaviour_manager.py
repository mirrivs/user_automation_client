from enum import Enum
import os
import queue
import random
import platform

from typing import TypedDict, Optional
from app_logger import app_logger

# Import behaviour classes
from behaviours.attack_phishing import BehaviourAttackPhishing
from behaviours.attack_ransomware import BehaviourAttackRansomware
from behaviours.attack_reverse_shell import BehaviourAttackReverseShell
from behaviours.procrastination import BehaviourProcrastination
from behaviours.work_developer import BehaviourWorkDeveloper
from behaviours.work_emails import BehaviourWorkEmails
from behaviours.work_organization_web import BehaviourWorkOrganizationWeb
from behaviours.work_word import BehaviourWorkWord
from cleanup_manager import CleanupManager

parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")
os_type = platform.system()

BEHAVIOUR_MAPPING = {
    "attack_phishing": BehaviourAttackPhishing,
    "attack_ransomware": BehaviourAttackRansomware,
    "attack_reverse_shell": BehaviourAttackReverseShell,
    "procrastination": BehaviourProcrastination,
    "work_developer": BehaviourWorkDeveloper,
    "work_emails": BehaviourWorkEmails,
    "work_organization_web": BehaviourWorkOrganizationWeb,
    "work_word": BehaviourWorkWord,
}


class BehaviourCategory(Enum):
    IDLE = "Idle"
    ATTACK = "Attack"


class Behaviour(TypedDict):
    name: str
    category: BehaviourCategory
    description: Optional[str]


class BehaviourWithId(Behaviour):
    id: str


def get_available_behaviours_from_mapping() -> dict[str, Behaviour]:
    """
    Extract behaviour metadata from BEHAVIOUR_MAPPING classes.
    Returns a dictionary compatible with the Behaviour TypedDict format.
    """
    available_behaviours = {}

    for behaviour_id, behaviour_class in BEHAVIOUR_MAPPING.items():
        # Get category enum value from string
        category_str = getattr(behaviour_class, "category", "IDLE")
        category = BehaviourCategory[category_str] if hasattr(BehaviourCategory, category_str) else BehaviourCategory.IDLE

        available_behaviours[behaviour_id] = {
            "name": getattr(behaviour_class, "name", behaviour_id),
            "display_name": getattr(behaviour_class, "display_name", behaviour_id),
            "category": category,
            "description": getattr(behaviour_class, "description", ""),
        }

    return available_behaviours


class BehaviourManager:
    """
    Behaviour controller for automation
    Controls the execution and tracking of automated behaviours using interruptible threads.
    """

    def __init__(self, available_behaviours: dict[str, Behaviour] = None):
        self.available_behaviours = (
            available_behaviours if available_behaviours is not None else {}
        )

        self.behaviours: dict[str, Behaviour] = self.available_behaviours

        # Organize behaviours by category
        self.behaviours_by_category: dict[BehaviourCategory, dict[str, Behaviour]] = {}
        for b_key, b_val in self.available_behaviours.items():
            category = b_val["category"]
            if category not in self.behaviours_by_category:
                self.behaviours_by_category[category] = {}
            self.behaviours_by_category[category][b_key] = b_val

        # Keep idle_behaviours for backward compatibility
        self.idle_behaviours: dict[str, Behaviour] = self.behaviours_by_category.get(
            BehaviourCategory.IDLE, {}
        )

        self.behaviour_queue = queue.PriorityQueue()
        self.behaviour_history: list[Behaviour] = []
        self.current_behaviour: BehaviourWithId = None
        self.next_behaviour: BehaviourWithId = None

        # Changed from process to thread
        self.behaviour_thread = None
        self.cleanup_manager = None

    def _check_thread_status(self):
        """
        Check if the current behaviour thread has finished and handle cleanup if needed
        """
        if self.behaviour_thread is not None:
            if not self.behaviour_thread.is_alive():
                app_logger.info("Behaviour thread finished")
                self.handle_behaviour_finish()

    def run_next_behaviour(self):
        """
        Runs the next behaviour from the queue if one is available.
        Calls evaluate_next_idle_behaviour if the queue is empty to determine the next action.
        """
        try:
            # First check if current behaviour has finished
            self._check_thread_status()

            if not self.behaviour_queue.empty():
                _, behaviour = self.behaviour_queue.get()
                self.run_behaviour(behaviour)
            else:
                next_behaviour = self.evaluate_next_idle_behaviour()
                if next_behaviour:
                    self.run_behaviour(next_behaviour)
        except Exception as ex:
            app_logger.error(f"Error while running next behaviour: {ex}")

    def terminate_behaviour(self):
        """
        Terminates the currently running behaviour thread, if any.
        Immediately stops the thread and triggers cleanup.
        """
        try:
            if self.behaviour_thread is not None:
                app_logger.info(f"Terminating behaviour: {self.current_behaviour['id']}")

                if self.behaviour_thread.is_alive():
                    self.behaviour_thread.stop()
                    self.behaviour_thread.join(timeout=2.0)

                    if self.behaviour_thread.is_alive():
                        app_logger.warning("Thread did not stop gracefully after 2 seconds")

                self.handle_behaviour_finish()
                app_logger.info(f"Terminated behaviour: {self.current_behaviour['id']}")
            else:
                app_logger.info("No behaviour is currently running to terminate.")
        except Exception as ex:
            app_logger.error(f"Error while terminating behaviour: {ex}")

    def run_behaviour(self, behaviour_id: str, force: bool = False):
        """
        Executes a behaviour in an interruptible thread.
        """
        # Check if current behaviour has finished before starting new one
        self._check_thread_status()

        if self.behaviour_thread is not None and force is False:
            app_logger.info(
                f"Behaviour {self.current_behaviour['id']} already running. "
                f"Use `force` parameter to forcefully stop and start the new behaviour."
            )
            return

        try:
            # Validate behaviour ID
            if behaviour_id not in BEHAVIOUR_MAPPING:
                app_logger.error(f"Invalid behaviour ID: {behaviour_id}")
                return

            self.current_behaviour = {
                **self.available_behaviours[behaviour_id],
                "id": behaviour_id,
            }
            app_logger.info(f"Starting behaviour: {self.current_behaviour['id']}")

            # Create cleanup manager for this behaviour
            self.cleanup_manager = CleanupManager()

            # Get behaviour class and instantiate
            behaviour_class = BEHAVIOUR_MAPPING[behaviour_id]
            self.behaviour_thread = behaviour_class(self.cleanup_manager)

            # Start the behaviour thread
            self.behaviour_thread.start()

            app_logger.info(f"Behaviour '{behaviour_id}' started (Thread ID: {self.behaviour_thread.ident})")
            self.update_behaviour_history(behaviour_id)

            return self.behaviour_thread
        except Exception as ex:
            app_logger.error(f"Error while running behaviour {behaviour_id}: {ex}", exc_info=True)
            self.current_behaviour = None
            self.behaviour_thread = None
            self.cleanup_manager = None

    def is_behaviour_running(self):
        """
        Checks if a behaviour thread is currently running.
        """
        try:
            # First check and update status
            self._check_thread_status()

            return (
                self.behaviour_thread is not None
                and self.behaviour_thread.is_alive()
            )
        except Exception as ex:
            app_logger.error(f"Error while checking if behaviour is running: {ex}")
            return False

    def update_behaviour_history(self, behaviour_id: str):
        """
        Appends the executed behaviour to the history.
        """
        try:
            self.behaviour_history.append(behaviour_id)
        except Exception as ex:
            app_logger.error(f"Error while updating behaviour history: {ex}")

    def evaluate_next_idle_behaviour(self):
        try:
            idle_behaviour_ids = list(self.idle_behaviours.keys())

            if not idle_behaviour_ids:
                return None

            if not self.behaviour_history:
                options_list = idle_behaviour_ids
            else:
                num_to_exclude = min(
                    len(idle_behaviour_ids) - 1, len(self.behaviour_history)
                )

                if num_to_exclude < 0:
                    num_to_exclude = 0

                recent_history_ids_to_exclude = self.behaviour_history[-num_to_exclude:]
                recent_id_set = set(recent_history_ids_to_exclude)

                options_list = [
                    key for key in idle_behaviour_ids if key not in recent_id_set
                ]

                if not options_list:
                    options_list = idle_behaviour_ids

            if options_list:
                return random.choice(options_list)
            return None

        except Exception as ex:
            print(f"Error while evaluating behaviour: {ex}")
            if self.idle_behaviours:
                return next(iter(self.idle_behaviours.keys()))
            return None

    def handle_behaviour_finish(self):
        """
        Handle cleanup when a behaviour finishes (either successfully or with an error)
        """
        if self.behaviour_thread is None:
            return

        # Thread cleanup is already handled by BehaviourThread.run() method
        app_logger.info(f"Behaviour `{self.current_behaviour['name']}` finished")

        # Clear references
        self.behaviour_thread = None
        self.current_behaviour = None
        self.cleanup_manager = None

    def get_behaviour(self, behaviour_id: str) -> str | None:
        return self.available_behaviours.get(behaviour_id)

    def get_current_behaviour_status(self):
        """
        Get detailed status information about the current behaviour
        """
        if self.behaviour_thread is None:
            return {
                "running": False,
                "current_behaviour": None,
            }

        is_running = self.behaviour_thread.is_alive()

        return {
            "running": is_running,
            "current_behaviour": self.current_behaviour,
        }