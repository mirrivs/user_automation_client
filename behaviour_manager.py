import os
import platform
import queue
import random
from typing import Optional, Type, Union

from app_logger import app_logger

# Import behaviour classes
from behaviour.behaviour import BaseBehaviour
from behaviour.models.behaviour import BehaviourCategory
from behaviour.registry import BEHAVIOURS
from cleanup_manager import CleanupManager

parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")
os_type = platform.system()


class BehaviourManager:
    """
    Behaviour controller for automation.
    Controls the execution and tracking of automated behaviours using interruptible threads.

    Uses behaviour instances directly instead of dictionaries for cleaner code.
    """

    def __init__(self, behaviour_classes: list[Type[BaseBehaviour]] = BEHAVIOURS):
        """
        Initialize the BehaviourManager.

        Args:
            behaviour_classes: List of behaviour classes to manage.
                               Defaults to BEHAVIOURS if not provided.
        """
        # Store behaviour classes by id
        self._behaviour_classes: dict[str, Type[BaseBehaviour]] = {}

        # Store prototype instances for metadata (created with cleanup_manager=None)
        cleanup_manager = CleanupManager()
        self._behaviour_prototypes: dict[str, BaseBehaviour] = {}

        # Track which behaviours are available
        self._available_behaviour_ids: list[str] = []

        # Initialize behaviours
        for behaviour_class in behaviour_classes:
            try:
                # Create prototype instance to check availability and get metadata
                prototype = behaviour_class(cleanup_manager)
                behaviour_id = prototype.id

                self._behaviour_classes[behaviour_id] = behaviour_class
                self._behaviour_prototypes[behaviour_id] = prototype

                if prototype.is_available and prototype.is_available():
                    self._available_behaviour_ids.append(behaviour_id)
                    app_logger.debug(f"Behaviour '{behaviour_id}' is available")
                else:
                    app_logger.debug(f"Behaviour '{behaviour_id}' is NOT available on this system")

            except Exception as ex:
                app_logger.warning(f"Failed to initialize behaviour class {behaviour_class.__name__}: {ex}")

        # Organize by category
        self._behaviours_by_category: dict[BehaviourCategory, list[BaseBehaviour]] = {}
        for behaviour_id in self._available_behaviour_ids:
            prototype = self._behaviour_prototypes[behaviour_id]
            category = prototype.category
            if category not in self._behaviours_by_category:
                self._behaviours_by_category[category] = []
            self._behaviours_by_category[category].append(prototype)

        # Runtime state
        self.behaviour_queue = queue.PriorityQueue()
        self.behaviour_history: list[str] = []
        self.current_behaviour: Optional[BaseBehaviour] = None
        self.behaviour_thread: Optional[BaseBehaviour] = None
        self.cleanup_manager: Optional[CleanupManager] = None

        app_logger.info(
            f"BehaviourManager initialized with {len(self._available_behaviour_ids)} available behaviours: {self._available_behaviour_ids}"
        )

    @property
    def available_behaviours(self) -> dict[str, BaseBehaviour]:
        """Get all available behaviour prototypes by id."""
        return {bid: self._behaviour_prototypes[bid] for bid in self._available_behaviour_ids}

    @property
    def all_behaviours(self) -> dict[str, BaseBehaviour]:
        """Get all behaviour prototypes (available or not) by id."""
        return self._behaviour_prototypes.copy()

    @property
    def behaviours_by_category(self) -> dict[BehaviourCategory, list[BaseBehaviour]]:
        """Get available behaviours organized by category."""
        return self._behaviours_by_category

    @property
    def idle_behaviours(self) -> list[BaseBehaviour]:
        """Get available idle behaviours."""
        return self._behaviours_by_category.get(BehaviourCategory.IDLE, [])

    @property
    def attack_behaviours(self) -> list[BaseBehaviour]:
        """Get available attack behaviours."""
        return self._behaviours_by_category.get(BehaviourCategory.ATTACK, [])

    # =========================================================================
    # Behaviour execution
    # =========================================================================

    def _check_thread_status(self):
        """Check if the current behaviour thread has finished and handle cleanup if needed."""
        if self.behaviour_thread is not None:
            if not self.behaviour_thread.is_alive():
                app_logger.info("Behaviour thread finished")
                self.handle_behaviour_finish()

    def run_behaviour(self, behaviour_id: str, force: bool = False) -> Union[BaseBehaviour, None]:
        """
        Executes a behaviour in an interruptible thread.

        Args:
            behaviour_id: The ID of the behaviour to run.
            force: If True, forcefully stop any running behaviour before starting.

        Returns:
            The started behaviour thread, or None if failed.
        """
        self._check_thread_status()

        if self.current_behaviour is not None and not force:
            app_logger.info(
                f"Behaviour '{self.current_behaviour.id}' already running. "
                f"Use force=True to stop it and start the new behaviour."
            )
            return None

        if self.behaviour_thread is not None and force:
            self.terminate_behaviour()

        try:
            if behaviour_id not in self._behaviour_classes:
                app_logger.error(f"Invalid behaviour ID: {behaviour_id}")
                return None

            if behaviour_id not in self._available_behaviour_ids:
                app_logger.error(f"Behaviour '{behaviour_id}' is not available on this system")
                return None

            app_logger.info(f"Starting behaviour: {behaviour_id}")

            # Create cleanup manager for this behaviour
            self.cleanup_manager = CleanupManager()

            # Create new instance of the behaviour class with cleanup manager
            behaviour_class = self._behaviour_classes[behaviour_id]
            self.behaviour_thread = behaviour_class(cleanup_manager=self.cleanup_manager)
            self.current_behaviour = self.behaviour_thread

            # Start the behaviour thread
            self.behaviour_thread.start()

            app_logger.info(f"Behaviour '{behaviour_id}' started (Thread ID: {self.behaviour_thread.ident})")
            self.behaviour_history.append(behaviour_id)

            return self.behaviour_thread

        except Exception as ex:
            app_logger.error(f"Error while running behaviour {behaviour_id}: {ex}", exc_info=True)
            self.current_behaviour = None
            self.behaviour_thread = None
            self.cleanup_manager = None
            return None

    def run_next_behaviour(self):
        """
        Runs the next behaviour from the queue if one is available.
        Falls back to evaluate_next_idle_behaviour if queue is empty.
        """
        try:
            self._check_thread_status()

            if not self.behaviour_queue.empty():
                _, behaviour_id = self.behaviour_queue.get()
                self.run_behaviour(behaviour_id)
            else:
                next_behaviour_id = self.evaluate_next_idle_behaviour()
                if next_behaviour_id:
                    self.run_behaviour(next_behaviour_id)
        except Exception as ex:
            app_logger.error(f"Error while running next behaviour: {ex}")

    def terminate_behaviour(self):
        """Terminates the currently running behaviour thread, if any."""
        try:
            if self.behaviour_thread is not None:
                app_logger.info(f"Terminating behaviour: {self.behaviour_thread.id}")

                if self.behaviour_thread.is_alive():
                    self.behaviour_thread.stop()
                    self.behaviour_thread.join(timeout=2.0)

                    if self.behaviour_thread.is_alive():
                        app_logger.warning("Thread did not stop gracefully after 2 seconds")

                self.handle_behaviour_finish()
                app_logger.info(
                    f"Terminated behaviour: {self.current_behaviour.id if self.current_behaviour else 'unknown'}"
                )
            else:
                app_logger.info("No behaviour is currently running to terminate.")
        except Exception as ex:
            app_logger.error(f"Error while terminating behaviour: {ex}")

    def handle_behaviour_finish(self):
        """Handle cleanup when a behaviour finishes."""
        if self.behaviour_thread is None:
            return

        if self.current_behaviour:
            app_logger.info(f"Behaviour '{self.current_behaviour.id}' finished")

        self.behaviour_thread = None
        self.current_behaviour = None
        self.cleanup_manager = None

    def is_behaviour_running(self) -> bool:
        """Checks if a behaviour thread is currently running."""
        try:
            self._check_thread_status()
            return self.behaviour_thread is not None and self.behaviour_thread.is_alive()
        except Exception as ex:
            app_logger.error(f"Error while checking if behaviour is running: {ex}")
            return False

    def evaluate_next_idle_behaviour(self) -> Union[str, None]:
        """
        Evaluates and returns the next idle behaviour to run.
        Avoids recently executed idle behaviours to provide variety.

        Only considers idle history (not attacks or other categories)
        when deciding which behaviours to exclude.
        """
        try:
            idle_behaviours = self._behaviours_by_category[BehaviourCategory.IDLE]

            if not idle_behaviours:
                return None

            idle_ids = {b.id for b in idle_behaviours}

            # Filter history to only idle behaviours so that attack runs
            # don't waste exclusion slots and cause idle repeats.
            idle_history = [bid for bid in self.behaviour_history if bid in idle_ids]

            if not idle_history:
                options = idle_behaviours
            else:
                num_to_exclude = min(len(idle_behaviours) - 1, len(idle_history))
                recent_to_exclude = set(idle_history[-num_to_exclude:])
                options = [b for b in idle_behaviours if b.id not in recent_to_exclude]

                if not options:
                    options = idle_behaviours

            return random.choice(options).id if options else None

        except Exception as ex:
            app_logger.error(f"Error while evaluating behaviour: {ex}")
            idle_behaviours = self.list_behaviours_by_category(BehaviourCategory.IDLE)
            return idle_behaviours[0].id if idle_behaviours else None

    def get_behaviour(self, behaviour_id: str) -> Union[BaseBehaviour, None]:
        """Get the prototype instance for a specific behaviour."""
        return self._behaviour_prototypes.get(behaviour_id)

    def get_behaviour_class(self, behaviour_id: str) -> Union[Type[BaseBehaviour], None]:
        """Get the class for a specific behaviour."""
        return self._behaviour_classes.get(behaviour_id)

    def get_current_behaviour_status(self) -> dict:
        """Get detailed status information about the current behaviour."""
        if self.behaviour_thread is None:
            return {
                "running": False,
                "current_behaviour": None,
            }

        return {
            "running": self.behaviour_thread.is_alive(),
            "current_behaviour": self.current_behaviour,
        }

    def queue_behaviour(self, behaviour_id: str, priority: int = 0):
        """Add a behaviour to the queue with the specified priority."""
        if behaviour_id not in self._available_behaviour_ids:
            app_logger.error(f"Cannot queue invalid/unavailable behaviour ID: {behaviour_id}")
            return

        self.behaviour_queue.put((priority, behaviour_id))
        app_logger.info(f"Queued behaviour '{behaviour_id}' with priority {priority}")

    def list_behaviours_by_category(self, category: BehaviourCategory) -> list[BaseBehaviour]:
        """Get a list of behaviour IDs for a specific category."""
        return [b for b in self._behaviours_by_category.get(category, [])]
