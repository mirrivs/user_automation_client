from typing import List

import jinja2
import pyautogui as pag
import pyperclip
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

from behaviour.models.exceptions import BehaviourException
from lib.cancellable_futures import sleep
from lib.email_manager.email_manager import EmailManager
from lib.selenium.models import EmailClient, EmailClientUser
from lib.selenium.selenium_driver import SeleniumDriver
from lib.selenium.types import DriverType
from src.logger import app_logger


class BaseEmailWebClient(SeleniumDriver):
    def __init__(self, driver: DriverType, user: EmailClientUser):
        self.driver = driver
        self.user = user
        self.email_manager = EmailManager()
        self.type = "base"

    def login(self):
        raise NotImplementedError()

    def logout(self):
        raise NotImplementedError()

    def get_unread_emails(self):
        raise NotImplementedError()

    def send_email(self, receivers: list[str], subject: str, email_body: str):
        raise NotImplementedError()

    def reply_to_email(self, subject: str, email_body: str):
        raise NotImplementedError()

    def reply_to_emails(self, email_list: List[WebElement] | list) -> int:
        if self.type == "base":
            raise NotImplementedError()

        responded_count = 0
        for email in email_list:
            subject_element = None
            if self.type == EmailClient.OWA:
                subject_element = email.find_element(
                    By.XPATH,
                    ".//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]",
                )
            elif self.type == EmailClient.O365:
                subject_element = email.find_element(By.XPATH, ".//div[2]//span[@title='']")
            else:
                subject_element = email.find_element(By.CSS_SELECTOR, "td.subject a")

            email_id = self.email_manager.get_email_id_by_subject(subject_element.text)
            if email_id:
                if self.type == EmailClient.OWA:
                    subject_element.click()
                else:
                    email.click()

                sleep(2)

                reply = self.email_manager.get_email_response(email_id)
                if reply is not None:
                    self.reply_to_email(reply["subject"], reply["email_body"])
                    responded_count += 1
                else:
                    sleep(5)

        return responded_count

    def _open_email_by_subject(self, subject_text: str):
        """Find and open an email by its subject text."""
        safe_subject = subject_text.replace("'", "\\'")

        if self.type == EmailClient.OWA:
            element = self.wait().until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//span[contains(@class, 'lvHighlightAllClass') and contains(text(), '{safe_subject}')]",
                    )
                )
            )
        elif self.type == EmailClient.O365:
            element = self.wait().until(
                EC.element_to_be_clickable((By.XPATH, f"//span[contains(@title, '{safe_subject}')]"))
            )
        elif self.type == EmailClient.ROUNDCUBE:
            element = self.wait().until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//td[contains(@class, 'subject')]//a[contains(text(), '{safe_subject}')]",
                    )
                )
            )
        else:
            raise ValueError(f"Unknown email client type: {self.type}")

        element.click()

    def _type_receivers(self, element: WebElement, receivers: list[str]):
        self.click_element(element)
        sleep(0.5)

        for receiver in receivers:
            self.type_text(element, receiver)
            self.check_cancellation()
            element.send_keys(Keys.ENTER)
            sleep(0.2)

    def email_allow_files(self):
        raise NotImplementedError()


class OutlookWebAccessClient(BaseEmailWebClient):
    def __init__(self, driver: DriverType, user: EmailClientUser):
        super().__init__(driver, user)
        self.type = EmailClient.OWA

    def login(self):
        try:
            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))).click()

            sleep(0.5)
            pag.write(self.user["email"], 0.1)
            sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))).click()

            sleep(0.5)
            pag.write(self.user["password"], 0.1)
            sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//div[@class='signinbutton']"))).click()

            try:
                self.wait().until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chooseLanguageLabel')]"))
                )
            except Exception:
                pass
            else:
                timezone_dropdown = self.wait().until(
                    EC.presence_of_element_located((By.XPATH, "//select[@id='selTz']"))
                )
                Select(timezone_dropdown).select_by_value("Central Europe Standard Time")
                sleep(0.5)
                self.wait().until(
                    EC.presence_of_element_located((By.XPATH, "//div/span[contains(text(), 'Save')]/.."))
                ).click()

        except Exception as ex:
            raise BehaviourException("Error logging into email web client", ex)

    def logout(self):
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Logout')]"))).click()
            sleep(1)

        except Exception as ex:
            raise BehaviourException("Error logging out of outlook web client", ex)

    def get_unread_emails(self):
        try:
            try:
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Unread')]]").click()
            except NoSuchElementException:
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Filter')]]").click()
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Unread')]]").click()
            unread_emails = self.wait().until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, '_lvv_w') and contains(@class, '_lvv_z') and (@role='option') and (contains(@class, 'listItemDefaultBackground') or contains(@class, 'ms-bgc-nl'))]",
                    )
                )
            )
            return unread_emails

        except TimeoutException:
            return []

        except Exception as ex:
            raise BehaviourException("Error trying to get emails", ex)

    def send_email(self, receivers: list[str], subject: str, email_body: str):
        try:
            receiver_name = ""
            if len(receivers) > 0:
                receiver_name = receivers[0].split(".")[0].capitalize()
            email_body = jinja2.Template(email_body).render(sender_name=self.user["name"], receiver_name=receiver_name)

            self.click_element(
                self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Write a new message')]")))
            )

            sleep(2)

            to_input = self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@aria-label, 'To')]")))
            self._type_receivers(to_input, receivers)
            sleep(1)

            subject_input = self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Add a subject']"))
            )
            self.type_text(subject_input, subject, clear_first=True)
            sleep(1)

            body_input = self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-label, 'Message body')]"))
            )
            self.type_text(body_input, email_body, clear_first=True)
            sleep(1)

            self.click_element(self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))))
            sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error sending email '{subject}' to {receivers}", ex)

    def reply_to_email(self, subject: str, email_body: str):
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Reply all')]"))).click()
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Expand')]"))).click()

            self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Add a subject')]"))
            ).click()

            pag.hotkey("ctrl", "a")
            sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            sleep(1)

            self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-label, 'Message body')]"))
            ).click()

            pag.hotkey("ctrl", "a")
            sleep(0.5)
            receiver_name = ""
            email_body = jinja2.Template(email_body).render(sender_name=self.user["name"], receiver_name=receiver_name)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            sleep(1)

            self.click_element(self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))))
            sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error replying to email: {subject}", ex)

    def open_specific_email(self, subject: str):
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{subject}')]"))).click()
        except NoSuchElementException:
            app_logger.error(f"No email found with subject: {subject}")

        except Exception as ex:
            raise BehaviourException(f"Error opening specific email with subject: '{subject}'", ex)

    def email_allow_files(self):
        try:
            self.wait(5).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@class='InfobarImmediateTextContainer'][contains(text(), 'To always show content from this sender,')]/following-sibling::a[@role='link']",
                    )
                )
            ).click()

        except Exception:
            pass


class O365Client(BaseEmailWebClient):
    def __init__(self, driver: DriverType, user: EmailClientUser):
        super().__init__(driver, user)
        self.type = EmailClient.O365

    def login(self):
        try:
            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))).click()

            sleep(0.5)
            pag.write(self.user["email"], 0.1)
            sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))).click()
            sleep(1)
            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))).click()

            sleep(0.5)
            pag.write(self.user["password"], 0.1)
            sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))).click()

            sleep(1)

            try:
                self.wait().until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//input[@type='checkbox' and @name='DontShowAgain']",
                        )
                    )
                ).click()
                self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))).click()
            except Exception:
                pass

            self.wait(10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Outlook')]")))

        except Exception as ex:
            raise BehaviourException("Error logging into email web client", ex)

    def logout(self):
        try:
            self.wait().until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@id='O365_UniversalMeContainer']//button[@id='mectrl_main_trigger']",
                    )
                )
            ).click()
            self.wait().until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@id='mectrl_main_body']//a[@id='mectrl_body_signOut']",
                    )
                )
            ).click()
            sleep(1)

        except Exception as ex:
            raise BehaviourException("Error logging out of outlook web client", ex)

    def get_unread_emails(self):
        try:
            is_filtered_unread = False
            try:
                self.driver.find_element(By.XPATH, "//button[@aria-label='Unread']").click()
                is_filtered_unread = True
            except NoSuchElementException:
                pass

            if not is_filtered_unread:
                self.wait(10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Filter']"))).click()
                self.wait(10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='menuitemradio' and @title='Unread']"))
                ).click()

            unread_emails = self.wait().until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[@id='MailList']//div[@data-focusable-row='true']")
                )
            )
            return unread_emails

        except TimeoutException:
            return []

        except Exception as ex:
            raise BehaviourException("Error trying to get emails", ex)

    def send_email(self, receivers, subject: str, email_body: str):
        try:
            receiver_name = ""
            if len(receivers) > 0:
                receiver_name = receivers[0].split(".")[0].capitalize()
            email_body = jinja2.Template(email_body).render(sender_name=self.user["name"], receiver_name=receiver_name)

            self.click_element(
                self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'New mail')]")))
            )

            sleep(2)

            to_input = self.wait().until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'To')]")))
            self._type_receivers(to_input, receivers)
            sleep(1)

            subject_input = self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Subject']")))
            self.type_text(subject_input, subject, clear_first=True)
            sleep(1)

            body_input = self.wait().until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Message body']")))
            self.type_text(body_input, email_body, clear_first=True)
            sleep(1)

            self.click_element(self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Send']"))))
            sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error sending email '{subject}' to {receivers}", ex)

    def reply_to_email(self, subject: str, email_body: str):
        try:
            self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-label, 'Reply all')]"))
            ).click()
            self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Expand header')]"))
            ).click()

            self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Add a subject')]"))
            ).click()

            pag.hotkey("ctrl", "a")
            sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            sleep(1)

            self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-label, 'Message body')]"))
            ).click()

            pag.hotkey("ctrl", "a")
            sleep(0.5)
            receiver_name = ""
            email_body = jinja2.Template(email_body).render(sender_name=self.user["name"], receiver_name=receiver_name)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            sleep(1)

            self.click_element(self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))))
            sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error replying to email: {subject}", ex)

    def open_specific_email(self, subject: str):
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{subject}')]"))).click()
        except NoSuchElementException:
            app_logger.error(f"No email found with subject: {subject}")

        except Exception as ex:
            raise BehaviourException(f"Error opening specific email with subject: '{subject}'", ex)

    def email_allow_files(self):
        try:
            self.wait(5).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@class='InfobarImmediateTextContainer'][contains(text(), 'To always show content from this sender,')]/following-sibling::a[@role='link']",
                    )
                )
            ).click()

        except Exception:
            pass


class RoundcubeClient(BaseEmailWebClient):
    def __init__(self, driver: DriverType, user: EmailClientUser):
        super().__init__(driver, user)
        self.type = EmailClient.ROUNDCUBE

    def login(self):
        self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='_user']"))).click()

        sleep(0.5)
        pag.write(self.user["email"], 0.1)
        sleep(0.5)

        self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='_pass']"))).click()

        sleep(0.5)
        pag.write(self.user["password"], 0.1)
        sleep(0.5)

        self.wait().until(EC.presence_of_element_located((By.XPATH, "//button[@id='rcmloginsubmit']"))).click()

    def logout(self):
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Logout')]"))).click()
            sleep(1)

        except Exception as ex:
            raise BehaviourException("Error logging out of roundcube web client", ex)

    def get_unread_emails(self):
        try:
            unread_emails = self.wait().until(
                EC.presence_of_all_elements_located((By.XPATH, "//tr[contains(@class, 'unread')]"))
            )
            return unread_emails
        except TimeoutException:
            return []

        except Exception as ex:
            raise BehaviourException("Error trying to get emails", ex)

    def send_email(self, receivers, subject: str, email_body: str):
        try:
            receiver_name = ""
            if len(receivers) > 0:
                receiver_name = receivers[0].split(".")[0].capitalize()
            email_body = jinja2.Template(email_body).render(sender_name=self.user["name"], receiver_name=receiver_name)

            self.click_element(self.wait().until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Create a new message']"))))

            sleep(2)

            to_input = self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@aria-label, 'To')]")))
            self._type_receivers(to_input, receivers)
            sleep(1)

            subject_input = self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[@name='_subject']")))
            self.type_text(subject_input, subject, clear_first=True)
            sleep(1)

            body_input = self.wait().until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-label, 'Message body')]"))
            )
            self.type_text(body_input, email_body, clear_first=True)
            sleep(1)

            self.click_element(self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))))
            sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error sending email '{subject}' to {receivers}", ex)

    def reply_to_email(self, subject: str, email_body: str):
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Reply to sender']"))).click()

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[@name='_subject']"))).click()

            pag.hotkey("ctrl", "a")
            sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            sleep(1)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//textarea[@name='_message']"))).click()

            pag.hotkey("ctrl", "a")
            sleep(0.5)
            receiver_name = ""
            email_body = jinja2.Template(email_body).render(sender_name=self.user["name"], receiver_name=receiver_name)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            sleep(1)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Send')]"))).click()
            sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error replying to email: {subject}", ex)

    def open_specific_email(self, subject: str):
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{subject}')]"))).click()
        except NoSuchElementException:
            app_logger.error(f"No email found with subject: {subject}")

        except Exception as ex:
            raise BehaviourException(f"Error opening specific email with subject: '{subject}'", ex)

    def email_allow_files(self):
        pass


def getEmailClient(
    email_client: str | EmailClient,
) -> type[BaseEmailWebClient]:
    email_client_mapping = {
        EmailClient.ROUNDCUBE: RoundcubeClient,
        EmailClient.OWA: OutlookWebAccessClient,
        EmailClient.O365: O365Client,
    }

    if isinstance(email_client, str):
        email_client = EmailClient(email_client)

    if email_client not in email_client_mapping:
        raise NoSuchElementException(f"Email client could not be found for: {email_client}")

    return email_client_mapping[email_client]

