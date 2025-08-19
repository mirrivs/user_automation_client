from utils.app_logger import app_logger


class BehaviourException(Exception):
    def __init__(self, msg: str, exception: Exception = None):
        log_message = msg
        if exception is not None:
            log_message += f", Original Exception: {exception}"

        app_logger.error(log_message)
        super().__init__(log_message)
