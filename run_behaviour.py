#! ./env/bin/python3

import atexit
import os
import signal
import sys
import platform

from typing import Callable

from behaviours.attack_phishing import behaviour_attack_phishing
from behaviours.attack_ransomware import behaviour_attack_ransomware
from behaviours.attack_reverse_shell import behaviour_attack_reverse_shell
from behaviours.procrastination import behaviour_procrastination
from behaviours.work_developer import behaviour_work_developer
from behaviours.work_emails import behaviour_work_emails
from behaviours.work_organization_web import behaviour_work_organization_web
from behaviours.work_word import behaviour_work_word

from cleanup_manager import CleanupManager

# Custom imports
from app_logger import app_logger

behaviour_mapping: dict[str, Callable] = {
    "attack_phishing": behaviour_attack_phishing,
    "attack_ransomware": behaviour_attack_ransomware,
    "attack_reverse_shell": behaviour_attack_reverse_shell,
    "procrastination": behaviour_procrastination,
    "work_developer": behaviour_work_developer,
    "work_emails": behaviour_work_emails,
    "work_organization_web": behaviour_work_organization_web,
    "work_word": behaviour_work_word,
}

cleanup_manager = CleanupManager()


def run_behaviour(behaviour_fn, behaviour_name: str | None = None):
    """
    Run behaviour function and handle cleanup
    """
    try:
        behaviour_fn(cleanup_manager)
        app_logger.info(f"Behaviour '{behaviour_name}' finished successfully")

    except Exception as ex:
        app_logger.error(ex)
        sys.exit(1)

    else:
        sys.exit()


def signal_handler(sig, frame):
    app_logger.info("Signal received, cleaning up...")
    sys.exit(0)


def exit_handler():
    """
    Exit handler called at exiting the process. Closes Selenium WebDriver.
    """
    cleanup_manager.run_cleanup()


if __name__ == "__main__":
    # Run only if the user is the one specified in the first argument
    if len(sys.argv) < 2:
        sys.exit("Behaviour name argument not provided!")

    if sys.argv[1] not in behaviour_mapping.keys():
        sys.exit("Invalid behaviour name")

    behaviour_fn = behaviour_mapping[sys.argv[1]]
    atexit.register(exit_handler)

    if platform.system() == "Windows" and hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    run_behaviour(behaviour_fn)
