from enum import Enum
import os
import queue
import random
import signal
import subprocess
import sys
import platform
import threading

from typing import TypedDict, Optional
from app_logger import app_logger

parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")
os_type = platform.system()

class BehaviourCategory(Enum):
    IDLE = "Idle"
    ATTACK = "Attack"

class Behaviour(TypedDict):
    name: str
    category: BehaviourCategory
    description: Optional[str]


class BehaviourWithId(Behaviour):
    id: str


class BehaviourManager:
    """
    Behaviour controller for automation 
    Controls the execution and tracking of automated behaviours.
    """

    def __init__(self, available_behaviours: dict[str, Behaviour] = None):
        self.available_behaviours = (
            available_behaviours if available_behaviours is not None else {}
        )
        self.idle_behaviours: dict[str, Behaviour] = {
            b_key: b_val
            for b_key, b_val in self.available_behaviours.items()
            if b_val["category"] == BehaviourCategory.IDLE
        }

        self.behaviour_queue = queue.PriorityQueue()
        self.behaviour_history: list[Behaviour] = []
        self.current_behaviour: BehaviourWithId = None
        self.next_behaviour: BehaviourWithId = None

        self.behaviour_process: subprocess.Popen[bytes] = None
        self.output_threads = []  # Track output forwarding threads

    def _forward_output(self, pipe, prefix=""):
        """
        Forward output from subprocess to main process stdout
        """
        try:
            if pipe is None:
                app_logger.error("Pipe is None, cannot forward output")
                return
                
            # Since we're using text=True, we can iterate directly over lines
            for line in pipe:
                line = line.rstrip()
                if line:
                    print(f"{prefix}{line}", flush=True)
        except Exception as ex:
            app_logger.error(f"Error forwarding output: {ex}")
        finally:
            if pipe:
                pipe.close()
            
            # Check if process finished while we were forwarding output
            self._check_process_status()

    def _check_process_status(self):
        """
        Check if the current behaviour process has finished and handle cleanup if needed
        """
        if self.behaviour_process is not None:
            exit_code = self.behaviour_process.poll()
            if exit_code is not None:  # Process has finished
                app_logger.info(f"Behaviour process finished with exit code: {exit_code}")
                self.handle_behaviour_finish()

    def run_next_behaviour(self):
        """
        Runs the next behaviour from the queue if one is available.
        Calls evaluate_next_idle_behaviour if the queue is empty to determine the next action.
        """
        try:
            # First check if current behaviour has finished
            self._check_process_status()
            
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
        Terminates the currently running behaviour process, if any.
        """
        try:
            if self.behaviour_process is not None:
                if os_type == "Linux":
                    self.behaviour_process.send_signal(signal.SIGINT)
                else:
                    self.behaviour_process.send_signal(signal.CTRL_BREAK_EVENT)

                # Wait for output threads to finish
                for thread in self.output_threads:
                    thread.join(timeout=1.0)
                self.output_threads.clear()

                self.handle_behaviour_finish()
                app_logger.info(f"Terminated behaviour: {self.current_behaviour['id']}")
            else:
                app_logger.info("No behaviour is currently running to terminate.")
        except Exception as ex:
            app_logger.error(f"Error while terminating behaviour: {ex}")

    def run_behaviour(self, behaviour_id: str, force: bool = False):
        """
        Executes a behaviour script as a subprocess, with the path to Python
        adjusted based on the operating system.
        """
        # Check if current behaviour has finished before starting new one
        self._check_process_status()
        
        if self.behaviour_process is not None and force == False:
            app_logger.info(
                f"Behaviour {self.current_behaviour['id']} already running. Use `force` parameter to forcefully kill and start the new behaviour."
            )
            return

        try:
            self.current_behaviour = {
                **self.available_behaviours[behaviour_id],
                "id": behaviour_id,
            }
            app_logger.info(f"Starting behaviour: {self.current_behaviour['id']}")

            if os_type == "Linux":
                env_python_path = os.path.join(parent_dir, "env", "bin", "python3")
            else:
                env_python_path = os.path.join(parent_dir, "env", "Scripts", "python")

            behaviour_file = os.path.join(parent_dir, "run_behaviour.py")
            cmd_args = [env_python_path, "-u", behaviour_file, behaviour_id]

            if os_type == "Linux":
                self.behaviour_process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
            else:
                self.behaviour_process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )

            # Check if process was created successfully and has stdout
            if self.behaviour_process and self.behaviour_process.stdout:
                # Start thread to forward stdout
                stdout_thread = threading.Thread(
                    target=self._forward_output,
                    args=(self.behaviour_process.stdout, f"[{behaviour_id}] "),
                    daemon=True
                )
                stdout_thread.start()
                self.output_threads.append(stdout_thread)
            else:
                app_logger.error(f"Failed to create subprocess or capture stdout for {behaviour_id}")

            app_logger.info(f"Behaviour {behaviour_id} started")
            self.update_behaviour_history(behaviour_id)

            return self.behaviour_process
        except Exception as ex:
            app_logger.error(f"Error while running behaviour {behaviour_id}: {ex}")
            self.current_behaviour = None

    def is_behaviour_running(self):
        """
        Checks if a behaviour process is currently running.
        """
        try:
            # First check and update status
            self._check_process_status()
            
            return (
                self.behaviour_process is not None
                and self.behaviour_process.poll() is None
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
        if self.behaviour_process is None:
            return
            
        exit_code = self.behaviour_process.poll()
        
        if exit_code == 0:
            app_logger.info(f"Behaviour `{self.current_behaviour['name']}` finished successfully")
        else:
            app_logger.error(f"Behaviour `{self.current_behaviour['name']}` finished with error (exit code: {exit_code})")

        # Wait for output threads to finish
        for thread in self.output_threads:
            thread.join(timeout=1.0)
        self.output_threads.clear()

        self.behaviour_process = None
        self.current_behaviour = None

    def get_behaviour(self, behaviour_id: str) -> str | None:
        return self.available_behaviours.get(behaviour_id)

    def get_current_behaviour_status(self):
        """
        Get detailed status information about the current behaviour
        """
        if self.behaviour_process is None:
            return {
                "running": False,
                "current_behaviour": None,
                "exit_code": None
            }
        
        exit_code = self.behaviour_process.poll()
        is_running = exit_code is None
        
        return {
            "running": is_running,
            "current_behaviour": self.current_behaviour,
            "exit_code": exit_code
        }