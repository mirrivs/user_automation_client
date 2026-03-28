import queue
import random
from typing import Optional, Type, Union

from app_config import app_config
from behaviour.behaviour import BaseBehaviour
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from behaviour.registry import BEHAVIOURS, validate_behaviour_registry
from cleanup_manager import CleanupManager
from src.config.config_handler import get_automation_config, is_behaviour_enabled_in_config
from src.config.models.config import AppConfig
from src.logger import app_logger


class BehaviourManager:
    """
    Behaviour controller for automation.
    Controls the execution and tracking of automated behaviours using interruptible threads.
    """

    def __init__(
        self,
        behaviour_classes: list[Type[BaseBehaviour]] = BEHAVIOURS,
        config: AppConfig = app_config,
    ):
        validate_behaviour_registry(behaviour_classes)

        self.config = config

        # Store behaviour classes by id
        self._behaviour_classes: dict[BehaviourId, Type[BaseBehaviour]] = {}

        # Store prototype instances for metadata
        prototype_cleanup_manager = CleanupManager()
        self._behaviour_prototypes: dict[BehaviourId, BaseBehaviour] = {}

        # Track which behaviours are available
        self._available_behaviour_ids: list[BehaviourId] = []

        for behaviour_class in behaviour_classes:
            behaviour_id = behaviour_class.id
            self._behaviour_classes[behaviour_id] = behaviour_class

            try:
                self._behaviour_prototypes[behaviour_id] = behaviour_class(prototype_cleanup_manager)
            except Exception as ex:
                app_logger.warning(f"Failed to initialize behaviour class {behaviour_class.__name__}: {ex}")

        self._behaviours_by_category: dict[BehaviourCategory, list[BaseBehaviour]] = {}
        self.refresh_availability(config)

        # Runtime state
        self.behaviour_queue: queue.PriorityQueue[tuple[int, BehaviourId]] = queue.PriorityQueue()
        self.behaviour_history: list[BehaviourId] = []
        self.current_behaviour: Optional[BaseBehaviour] = None
        self.behaviour_thread: Optional[BaseBehaviour] = None
        self.cleanup_manager: Optional[CleanupManager] = None

        app_logger.info(
            f"BehaviourManager initialized with {len(self._available_behaviour_ids)} "
            f"available behaviours: {self._available_behaviour_ids}"
        )

    @property
    def available_behaviours(self) -> dict[BehaviourId, BaseBehaviour]:
        return {bid: self._behaviour_prototypes[bid] for bid in self._available_behaviour_ids}

    @property
    def all_behaviours(self) -> dict[BehaviourId, BaseBehaviour]:
        return self._behaviour_prototypes.copy()

    @property
    def behaviours_by_category(self) -> dict[BehaviourCategory, list[BaseBehaviour]]:
        return self._behaviours_by_category

    @property
    def idle_behaviours(self) -> list[BaseBehaviour]:
        return self._behaviours_by_category.get(BehaviourCategory.IDLE, [])

    @property
    def attack_behaviours(self) -> list[BaseBehaviour]:
        return self._behaviours_by_category.get(BehaviourCategory.ATTACK, [])

    def refresh_availability(self, config: Optional[AppConfig] = None) -> None:
        if config is not None:
            self.config = config

        get_automation_config(self.config)
        self._available_behaviour_ids = []
        self._behaviours_by_category = {}

        for behaviour_id, behaviour_class in self._behaviour_classes.items():
            prototype = self._behaviour_prototypes.get(behaviour_id)
            if prototype is None:
                app_logger.warning(f"Behaviour '{behaviour_id}' has no prototype instance; marking unavailable")
                continue

            runtime_available = bool(behaviour_class.is_available())
            config_enabled = is_behaviour_enabled_in_config(self.config, behaviour_id)
            final_available = runtime_available and config_enabled

            app_logger.debug(
                f"Behaviour '{behaviour_id}' availability: "
                f"runtime_available={runtime_available}, config_enabled={config_enabled}"
            )

            if not final_available:
                continue

            self._available_behaviour_ids.append(behaviour_id)
            self._behaviours_by_category.setdefault(prototype.category, []).append(prototype)

    def _check_thread_status(self):
        """Check if the current behaviour thread has finished and handle cleanup if needed."""
        if self.behaviour_thread is not None and not self.behaviour_thread.is_alive():
            app_logger.info("Behaviour thread finished")
            self.handle_behaviour_finish()

    def run_behaviour(self, behaviour_id: Union[BehaviourId, str], force: bool = False) -> Union[BaseBehaviour, None]:
        """
        Executes a behaviour in an interruptible thread.

        Args:
            behaviour_id: The ID of the behaviour to run.
            force: If True, cooperatively stop any running behaviour before starting.

        Returns:
            The started behaviour instance, or None if failed.
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
                app_logger.error(f"Behaviour '{behaviour_id}' is not available on this system or disabled in config")
                return None

            app_logger.info(f"Starting behaviour: {behaviour_id}")

            self.cleanup_manager = CleanupManager()

            behaviour_class = self._behaviour_classes[behaviour_id]
            self.behaviour_thread = behaviour_class(cleanup_manager=self.cleanup_manager)
            self.current_behaviour = self.behaviour_thread

            self.behaviour_thread.start()

            app_logger.info(f"Behaviour '{behaviour_id}' started (Thread ID: {self.behaviour_thread.ident})")
            self.behaviour_history.append(behaviour_id)

            return self.behaviour_thread

        except Exception as ex:
            app_logger.error(f"Error while running behaviour {behaviour_id}: {ex}", exc_info=True)
            self._cleanup_behaviour_resources()
            return None

    def run_next_behaviour(self):
        """Runs the next behaviour from the queue, or falls back to an idle behaviour."""
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
        """Cooperatively stop the currently running behaviour, if any.

        Calls stop() on the behaviour thread which:
          1. Sets the shared cancel event (triggers OperationCancelled in tasks)
          2. Joins with a timeout waiting for the thread to finish
          3. The thread's run() method handles cleanup in its finally block
        """
        try:
            if self.behaviour_thread is None:
                app_logger.info("No behaviour is currently running to terminate.")
                return

            behaviour_id = self.current_behaviour.id if self.current_behaviour else "unknown"
            app_logger.info(f"Terminating behaviour: {behaviour_id}")

            if self.behaviour_thread.is_alive():
                self.behaviour_thread.stop()

            app_logger.info(f"Terminated behaviour: {behaviour_id}")
            self._cleanup_behaviour_resources()

        except Exception as ex:
            app_logger.error(f"Error while terminating behaviour: {ex}", exc_info=True)
            self._cleanup_behaviour_resources()

    def _cleanup_behaviour_resources(self):
        """Clear runtime state after a behaviour has ended."""
        self.behaviour_thread = None
        self.current_behaviour = None
        self.cleanup_manager = None

    def handle_behaviour_finish(self):
        """Handle cleanup when a behaviour finishes naturally."""
        if self.behaviour_thread is None:
            return

        if self.current_behaviour:
            app_logger.info(f"Behaviour '{self.current_behaviour.id}' finished")

        self._cleanup_behaviour_resources()

    def is_behaviour_running(self) -> bool:
        """Checks if a behaviour thread is currently running."""
        try:
            self._check_thread_status()
            return self.behaviour_thread is not None and self.behaviour_thread.is_alive()
        except Exception as ex:
            app_logger.error(f"Error while checking if behaviour is running: {ex}")
            return False

    def evaluate_next_idle_behaviour(self) -> Union[BehaviourId, None]:
        """Pick the next idle behaviour, avoiding recent repeats."""
        try:
            idle_behaviours = self._behaviours_by_category.get(BehaviourCategory.IDLE, [])

            if not idle_behaviours:
                return None

            idle_ids = {b.id for b in idle_behaviours}
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

    def queue_behaviour(self, behaviour_id: Union[BehaviourId, str], priority: int = 0):
        """Add a behaviour to the queue with the specified priority."""
        if behaviour_id not in self._available_behaviour_ids:
            app_logger.error(f"Cannot queue invalid/unavailable behaviour ID: {behaviour_id}")
            return

        self.behaviour_queue.put((priority, behaviour_id))
        app_logger.info(f"Queued behaviour '{behaviour_id}' with priority {priority}")

    def get_behaviour(self, behaviour_id: Union[BehaviourId, str]) -> Union[BaseBehaviour, None]:
        return self._behaviour_prototypes.get(behaviour_id)

    def get_behaviour_class(self, behaviour_id: Union[BehaviourId, str]) -> Union[Type[BaseBehaviour], None]:
        return self._behaviour_classes.get(behaviour_id)

    def get_current_behaviour_status(self) -> dict:
        if self.behaviour_thread is None:
            return {"running": False, "current_behaviour": None}

        return {
            "running": self.behaviour_thread.is_alive(),
            "current_behaviour": self.current_behaviour,
        }

    def list_behaviours_by_category(self, category: BehaviourCategory) -> list[BaseBehaviour]:
        return [b for b in self._behaviours_by_category.get(category, [])]
