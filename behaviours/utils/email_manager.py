import os
import random
import sys
import yaml

# Append to path for custom imports
parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

behaviour_dir = os.path.join(parent_dir, "..")
sys.path.append(behaviour_dir)

top_dir = os.path.join(parent_dir, "..", "..")
sys.path.append(top_dir)

emails_file = os.path.join(parent_dir, "..", "templates", "emails.yml")

# Custom imports
import utils.config_handler as config_handler
from utils.app_logger import app_logger


class EmailManager:
    """
    Email manager for email communication
    """

    def __init__(self):
        try:
            self.emails: dict = config_handler.load_config(emails_file)
            self.email_starters: dict = self.emails.get("starters", {})
            self.email_responses: dict = self.emails.get("responses", {})
        except yaml.YAMLError as ex:
            app_logger.error(f"Failed reading emails from '{emails_file}', Ex: {ex}")
            sys.exit(1)

    def get_email_starter(self):
        """
        Get random email from email starters
        """
        try:
            email_ids = list(self.email_starters.keys())
            email_id = random.choice(email_ids)
            return self.email_starters[email_id]
        except Exception as ex:
            app_logger.error(f"Failed getting starter email, Ex: {ex}")
            sys.exit(1)

    def get_email_id_by_subject(self, subject: str):
        """
        Get email id by subject id from both starters and responses
        """
        try:
            email_starter_subjects = [
                (x, self.email_starters[x]["subject"]) for x in self.email_starters
            ]
            email_responses_subjects = [
                (x, self.email_responses[x]["subject"]) for x in self.email_responses
            ]
            email_subjects = email_starter_subjects + email_responses_subjects

            matched_emails = [x for x in email_subjects if x[1] == subject]
            if matched_emails:
                email_id = matched_emails[0][0]
                return email_id
            else:
                return None
        except Exception as ex:
            app_logger.error(f"Failed getting email id by subject, Ex: {ex}")
            sys.exit(1)

    def get_email_by_id(self, email_id: int):
        """
        Get email by id
        """
        try:
            if email_id in self.email_starters:
                return self.email_starters[email_id]
            elif email_id in self.email_responses:
                return self.email_responses[email_id]
            else:
                return None

        except Exception as ex:
            app_logger.error(f"Failed getting email by id, Ex: {ex}")
            sys.exit(1)

    def get_email_response(self, email_id: int):
        """
        Get email response for email by id
        """
        try:
            responses = self.email_starters.get(email_id, {}).get("responses", [])
            if responses:
                response_id = random.choice(responses)
                return self.email_responses.get(response_id)
            else:
                return None
        except Exception as ex:
            app_logger.error(f"Failed getting response for email, Ex: {ex}")
            sys.exit(1)
