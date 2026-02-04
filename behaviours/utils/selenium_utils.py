from abc import ABC
import os
import platform
import random
import sys
import time
import jinja2
import pyautogui as pag
import pyperclip
from typing import Literal

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webelement import WebElement

from models.email_client import EmailClient

# Append to path for custom imports
parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

behaviour_dir = os.path.join(parent_dir, "..")
sys.path.append(behaviour_dir)

top_dir = os.path.join(parent_dir, "..", "..")
sys.path.append(top_dir)

# Custom imports
from behaviour import BehaviourException
from app_logger import app_logger

DEFAULT_TIMEOUT = 5

class SeleniumDriver:
    def __init__(self, driver: (webdriver.Firefox | webdriver.Edge)):
        self.driver: (webdriver.Firefox | webdriver.Edge) = driver

    def maximize_driver_window(self):
        """
        Maximize driver window\n
        """
        self.driver.maximize_window()


    def quit_driver(self):
        """
        Quit the WebDriver and close all associated windows
        """
        self.driver.quit()


    def wait(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Wait for the set time for action to be complete
        """
        return WebDriverWait(self.driver, timeout)

class SeleniumController(SeleniumDriver):
    def __init__(self, driver: webdriver, email_client_type: EmailClient = None):
        super().__init__(driver)
        self.email_client: (OutlookWebAccessClient | RoundcubeClient) = getEmailClient(email_client_type, self.driver)

    def switch_tab(self):
        """
        Switch to the next tab in browser
        """
        original_window = self.driver.current_window_handle
        windows = self.driver.window_handles
        for window in windows:
            if window != original_window:
                new_window = window
                break

        if not new_window:
            raise BehaviourException("Could not find new tab")
        self.driver.switch_to.window(new_window)

    def phishing_enter_credentials(self, email: str, password: str):
        """
        Enter credentials into roundcube phishing web\n
        Prerequisites:
            - Opened roundcube phishing login page 
        """
        try:
            # Click on subject input field and copy and paste new subject
            if self.email_client == "owa":
                self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//input[contains(@name,'email')]"))).click()
            else:
                self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='email']"))).click()
            time.sleep(0.5)
            pag.write(email, 0.1)
            time.sleep(0.5)
            if self.email_client == "owa":
                self.wait(5).until(EC.presence_of_element_located(
                (By.XPATH, "//input[contains(@name,'password')]"))).click()
            else:
                self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))).click()
            time.sleep(0.5)
            pag.write(password, 0.1)
            time.sleep(0.5)
            if self.email_client == "owa":
                self.wait(5).until(EC.presence_of_element_located(
                    (By.XPATH, "//button[contains(@id,'rcmloginsubmit')]"))).click()
            else:
                self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='signinbutton']"))).click()

        except Exception as ex:
            raise BehaviourException(f"Error entering credentials into phishing web", ex)
        
    def email_client_logout(self):
        """
        Log out of roundcube web client\n
        Prerequisites:
            - Logged into roundcube web client
        """
        # TODO: Implement OWA
        try:
            if self.email_client == "owa":
                self.wait(5).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Logout')]"))).click()
                time.sleep(1.5)

        except Exception as ex:
            raise BehaviourException(f"Error logging out of roundcube web client", ex)


    def roundcube_set_language(self, set_language="en"):
        """
        Check the language setting of the Roundcube client, if the language is Slovak, change it to English.
        If the Slovak language option is not found, do nothing.
        Prerequisites:
            - Logged into the Roundcube web client 
        """
        try:
            element_found = True

            # Attempt to find the settings button
            try:
                settings_button = self.wait(5).until(EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'Nastavenia')]")))
            except Exception as ex:
                app_logger.info("Slovak language not found, no change made")
                return

            if element_found and settings_button.is_displayed():
                settings_button.click()
                time.sleep(1)
                self.wait(5).until(EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(text(), 'Nastavenia')]"))).click()
                time.sleep(1)
                self.wait(5).until(EC.presence_of_element_located(
                    (By.XPATH, "//td[contains(text(), 'Používateľské rozhranie')]"))).click()
                time.sleep(1)
                # Switch to email Iframe
                iframe = self.driver.find_element(By.ID, "preferences-frame")
                self.driver.switch_to.frame(iframe)
                time.sleep(1)
                language_dropdown = self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//select[@name='_language']")))
                Select(language_dropdown).select_by_value("en_US")
                time.sleep(1)
                self.wait(5).until(EC.presence_of_element_located(
                    (By.XPATH, "//button[contains(text(), 'Uložiť')]"))).click()
                time.sleep(1)
                # Switch to default Iframe
                self.driver.switch_to.default_content()
                self.wait(5).until(EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'E-mail')]"))).click()

        except Exception as ex:
            raise BehaviourException(f"Error changing Roundcube language", ex)

    def procrastinate_watch_youtube_shorts(self, duration: float):
        """
        Watch youtube shorts for set duration
        """
        try:
            # Wait for the "Accept all" button to be visible
            accept_button = self.wait(10).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@aria-label, 'Accept')]")))
            accept_button.click()
            time.sleep(3)

            # Wait for the "Shorts" button to be visible
            shorts_button = self.wait(10).until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Shorts']")))
            shorts_button.click()

            total_duration = 0
            while total_duration < duration:
                watch_duration = random.uniform(10.0, 20.0)
                time.sleep(watch_duration)

                # Watch next video
                next_video_button = self.wait(10).until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@aria-label='Next video']")))
                next_video_button.click()

                total_duration += watch_duration

        except Exception as ex:
            custom_message = f"Error watching youtube shorts"
            app_logger.error(f"{custom_message}, Original Exception: {ex}")
            raise Exception(f"{custom_message}. Original Exception: {ex}")

    def accept_google_cookies(self):
        """
        Try to find and click the cookie accept button in Slovak or English.
        """
        try:
            # XPath for both versions of the accept cookies button
            original_text_xpath = "//div[text()='Prijať všetko']"
            english_text_xpath = "//div[text()='Accept all']"

            found = False

            for xpath in [original_text_xpath, english_text_xpath]:
                try:
                    accept_button = self.wait(3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    accept_button.click()
                    found = True
                    break
                except:
                    continue

            if not found:
                raise Exception("Accept cookies button not found.")

        except Exception as ex:
            raise BehaviourException(f"Error accepting google cookies", ex)

    def procrastinate_scroll_images(self, duration: int):
        """
        Scroll using pg down with random pauses inbetween for set duration\n
        """
        try:
            # Wait for the "Images" link to be visible
            images_link = self.wait(10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Images')]")))
            images_link.click()
            time.sleep(1)

            timer = 0
            while timer < duration:
                pag.press("pgdn")
                sleep_time = random.randint(3, 6)
                time.sleep(sleep_time)
                timer += sleep_time

        except Exception as ex:
            raise BehaviourException(f"Error scrolling images", ex)

    def browse_organization_website(self, duration: float):
        """
        Change between pages and scroll on them using pg down\n
        """
        try:
            nav_links = self.wait(5).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@class, 'govuk-link idsk-header-web__nav-list-item-link')]"))
            )
            random.choice(nav_links).click()

            min_scroll_count = 4
            scroll_count = 0
            timer = 0
            while timer < duration:
                if scroll_count >= min_scroll_count:
                    pag.press("home")
                    nav_links = self.wait(5).until(EC.presence_of_all_elements_located(
                        (By.XPATH, "//a[contains(@class, 'govuk-link idsk-header-web__nav-list-item-link')]")))
                    self.wait(5).until(EC.element_to_be_clickable(random.choice(nav_links))).click()
                    scroll_count = 0

                pag.press("pgdn")
                scroll_count += 1

                sleep_time = random.randint(3, 6)
                time.sleep(sleep_time)
                timer += sleep_time

        except Exception as ex:
            raise BehaviourException(f"Error browsing organisation website", ex)

    def phishing_owa_enter_credentials(self, email: str, password: str):
        """
        Enter credentials into owa phishing web\n
        Prerequisites:
            - Opened owa phishing login page 
        """
        try:
            self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='email']"))).click()
            time.sleep(0.5)
            pag.write(email, 0.1)
            time.sleep(0.5)
            self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))).click()
            time.sleep(0.5)
            pag.write(password, 0.1)
            time.sleep(0.5)
            self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='signinbutton']"))).click()

        except Exception as ex:
            raise BehaviourException(f"Error logging into outlook web access", ex)

    def email_client_download_email_attachments(self):
        """
        Returns list of downloaded attachments from email
        Prerequisites:
            - Logged into outlook web access
            - Opened email
        """
        try:
            downloaded_attachments = []

            email_attachments = self.email_client_get_email_attachments()
            for attachment in email_attachments:
                attachment_name_element = None
                if self.email_client == "owa":
                    attachment_name_element = attachment.find_element(
                    By.XPATH, "//span[contains(@class, '_ay_x ms-font-m')]")
                else:
                    attachment_name_element = attachment.find_element(By.XPATH, "//span[@class='attachment-name']")

                downloaded_attachments.append(attachment_name_element.text)
                attachment.click()
                time.sleep(5)

            return downloaded_attachments

        except Exception as ex:
            raise BehaviourException(f"Error trying to download email attachments", ex)

    def email_client_get_email_attachments(self) -> list[WebElement]:
        """
        Returns list of attachments from selected email, if there are no attachments return empty list
        Prerequisites:
            - Logged into outlook web access
            - Opened email
        """
        try:
            attachments = []
            if self.email_client == "owa":
                attachments = self.wait(5).until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[contains(@class, 'attachmentWell')]//a[contains(@class, 'o365button')]")))
            else:
                attachments = self.wait(5).until(EC.presence_of_all_elements_located(
                (By.XPATH, "//ul[contains(@class, 'attachmentslist')]/li/a[contains(@class, 'filename')]")))
            return attachments
        except TimeoutException:
            return []
        except Exception as ex:
            raise BehaviourException(f"Error trying to get email attachments", ex)

    def owa_search_link_in_email(self):
        """
        Find link in email body\n
        Prerequisites:
            - Logged into outlook web access
            - Opened email
        """
        try:
            spans = self.driver.find_elements(By.XPATH, "//span[text()='click here.']")

            for span in spans:
                parent = span.find_element(By.XPATH, "./..")
                parent.click()

            email_body = None

            try:
                email_body = self.driver.find_element(By.XPATH, "//div[@id='Item.MessageNormalizedBody']")
            except NoSuchElementException:
                pass

            if not email_body:
                try:
                    email_body = self.driver.find_element(By.XPATH, "//div[@id='Item.MessageUniqueBody']")
                except NoSuchElementException:
                    raise NoSuchElementException("Failed to locate email body")

            if email_body:
                link = email_body.find_element(By.XPATH, ".//a[contains(@href, 'http')]")

                if link:
                    link.click()

        except Exception as ex:
            raise BehaviourException(f"Unexpected error: {str(ex)}")


class EdgeSeleniumController(SeleniumController):
    """
    Controller for edge selenium\n
    Prerequisites:
        - Installed edge webdriver
    """

    def __init__(self, email_client_type: EmailClient = None):
        options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--enable-chrome-browser-cloud-management')
        super().__init__(webdriver.Edge(options=options), email_client_type)


class FirefoxSeleniumController(SeleniumController):
    """
    Controller for firefox selenium\n
    Prerequisites:
        - Installed firefox webdriver
    """

    def __init__(self, email_client_type: EmailClient = None):
        options = webdriver.FirefoxOptions()
        options.set_preference("acceptInsecureCerts", True)
        options.add_argument("--start-maximized")
        options.add_argument('--ignore-certificate-errors')
        super().__init__(webdriver.Firefox(options=options), email_client_type)

class BaseEmailWebClient(SeleniumDriver):
    def __init__(self, driver: webdriver):
        self.driver = driver
        self.type = "base"

    def login(self):
        raise NotImplementedError()

    def logout(self):
        raise NotImplementedError()
    
    def get_unread_emails(self):
        raise NotImplementedError()

    def send_email(self):
        raise NotImplementedError()

    def reply_to_email(self):
        raise NotImplementedError()
    
    def email_allow_files(self):
        raise NotImplementedError()
    

class OutlookWebAccessClient(BaseEmailWebClient):
    def __init__(self, driver: webdriver):
        super().__init__(driver)
        self.type = EmailClient.OWA

    def login(self, email: str, password: str):
        """
        Log in to the outlook web client\n
        Prerequisites:
            - Opened outlook login page
        """
        try:
            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))).click()

            time.sleep(0.5)
            pag.write(email, 0.1)
            time.sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))).click()

            time.sleep(0.5)
            pag.write(password, 0.1)
            time.sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//div[@class='signinbutton']"))).click()

            try:
                self.wait().until(EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'chooseLanguageLabel')]")))
            except Exception as ex:
                pass
            else:
                # If user logs in for the first time set timezone
                timezone_dropdown = self.wait().until(
                    EC.presence_of_element_located((By.XPATH, "//select[@id='selTz']")))
                Select(timezone_dropdown).select_by_value("Central Europe Standard Time")
                time.sleep(0.5)
                self.wait().until(EC.presence_of_element_located(
                    (By.XPATH, "//div/span[contains(text(), 'Save')]/.."))).click()

        except Exception as ex:
            raise BehaviourException(f"Error logging into email web client", ex)
        

    def logout(self):
        """
        Log out of outlook web client\n
        Prerequisites:
            - Logged into outlook web client
        """
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Logout')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error logging out of outlook web client", ex)


    def get_unread_emails(self):
        """
        Returns list of unread emails, if there are no unread emails return empty list
        Prerequisites:
            - Logged into outlook web client
        """
        
        try:
            try:
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Unread')]]").click()
            except NoSuchElementException:
                # Filter by unread if unread button is unavailable, indicating that filter by unread is already set
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Filter')]]").click()
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Unread')]]").click()
            unread_emails = self.wait().until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, '_lvv_w') and contains(@class, '_lvv_z') and (@role='option') and (contains(@class, 'listItemDefaultBackground') or contains(@class, 'ms-bgc-nl'))]"))
            )
            return unread_emails
        
        except TimeoutException:
            return []

        except Exception as ex:
            raise BehaviourException(f"Error trying to get emails", ex)

    def send_email(self, sender_name, receivers, subject, email_body):
        """
        Writes and sends email\n
        Prerequisites:
            - Logged into outlook web client
        """
        try:
            receiver_name = ""
            if len(receivers) > 0:
                receiver_name = receivers[0].split(".")[0].capitalize()
            email_body = jinja2.Template(email_body).render(sender_name=sender_name, receiver_name=receiver_name)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Write a new message')]"))).click()
            
            time.sleep(2)

            self.driver.find_element(By.XPATH, "//input[contains(@aria-label, 'To')]").click()
            for receiver in receivers:
                time.sleep(0.5)
                pyperclip.copy(receiver)
                pag.hotkey("ctrl", "v")
            time.sleep(1)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Add a subject']"))).click()
            
            time.sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//textarea[@name='_message']"))).click()

            # Click on message textarea field and copy-paste the message
            time.sleep(0.5)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click send button
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error sending email '{subject}' to {receivers}", ex)

    def reply_to_email(self, sender_name, subject, email_body):
        """
        Respond to an email based on the conversation\n
        Prerequisites:
            - Logged into outlook web client
            - Opened email
        """
        try:
            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@title, 'Reply all')]"))).click()
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Expand')]"))).click()

            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, "//input[contains(@placeholder, 'Add a subject')]"))).click()

            pag.hotkey("ctrl", "a")
            time.sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click on meassage textarea field and copy and paste new message
            self.wait().until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@aria-label, 'Message body')]"))).click()

            pag.hotkey("ctrl", "a")
            time.sleep(0.5)
            receiver_name = ""
            email_body = jinja2.Template(email_body).render(sender_name=sender_name, receiver_name=receiver_name)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click the send button
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error replying to email: {subject}", ex)


    def open_specific_email(self, subject: str):
        """
        Opens specific email by email subject\n
        Prerequisites:
            - Logged into roundcube web client
        """
        # TODO: OWA behaviour
        try:
            # Click on the email subject
            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, f"//span[contains(text(), '{subject}')]"))).click()
        except NoSuchElementException:
            app_logger.error(f"No email found with subject: {subject}")

        except Exception as ex:
            raise BehaviourException(f"Error opening specific email with subject: '{subject}'", ex)

    def email_allow_files(self):
        """
        Allow files like images to show in emails\n
        Prerequisites:
            - Opened email
        """
        try:
            self.wait(5).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='InfobarImmediateTextContainer'][contains(text(), 'To always show content from this sender,')]/following-sibling::a[@role='link']"))).click()

        except Exception as ex:
            pass

class O365Client(BaseEmailWebClient):
    def __init__(self, driver: webdriver):
        super().__init__(driver)
        self.type = EmailClient.O365

    def login(self, email: str, password: str):
        """
        Log in to the outlook web client\n
        Prerequisites:
            - Opened outlook login page
        """
        try:
            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))).click()

            time.sleep(0.5)
            pag.write(email, 0.1)
            time.sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))).click()

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))).click()

            time.sleep(0.5)
            pag.write(password, 0.1)
            time.sleep(0.5)

            self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))).click()

            time.sleep(1)

            # Handle "DontShowAgain" checkbox if it appears
            try:
                self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox' and name='DontShowAgain']"))).click()
                self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))).click()
            except Exception:
                pass  # Continue if DontShowAgain window doesn't appear

            # try:
            #     self.wait().until(EC.presence_of_element_located(
            #         (By.XPATH, "//div[contains(@class, 'chooseLanguageLabel')]")))
            # except Exception as ex:
            #     pass
            # else:
            #     # If user logs in for the first time set timezone
            #     timezone_dropdown = self.wait().until(
            #         EC.presence_of_element_located((By.XPATH, "//select[@id='selTz']")))
            #     Select(timezone_dropdown).select_by_value("Central Europe Standard Time")
            #     time.sleep(0.5)
            #     self.wait().until(EC.presence_of_element_located(
            #         (By.XPATH, "//div/span[contains(text(), 'Save')]/.."))).click()

        except Exception as ex:
            raise BehaviourException(f"Error logging into email web client", ex)
        

    def logout(self):
        """
        Log out of outlook web client\n
        Prerequisites:
            - Logged into outlook web client
        """
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//div[@id='O365_UniversalMeContainer']//button[@id='mectrl_main_trigger']"))).click()
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//div[@id='mectrl_main_body']//a[@id='mectrl_body_signOut']"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error logging out of outlook web client", ex)


    def get_unread_emails(self):
        """
        Returns list of unread emails, if there are no unread emails return empty list
        Prerequisites:
            - Logged into outlook web client
        """
        
        try:
            try:
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Unread')]]").click()
            except NoSuchElementException:
                # Filter by unread if unread button is unavailable, indicating that filter by unread is already set
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Filter')]]").click()
                self.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Unread')]]").click()
            unread_emails = self.wait().until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, '_lvv_w') and contains(@class, '_lvv_z') and (@role='option') and (contains(@class, 'listItemDefaultBackground') or contains(@class, 'ms-bgc-nl'))]"))
            )
            return unread_emails
        
        except TimeoutException:
            return []

        except Exception as ex:
            raise BehaviourException(f"Error trying to get emails", ex)

    def send_email(self, sender_name, receivers, subject, email_body):
        """
        Writes and sends email\n
        Prerequisites:
            - Logged into outlook web client
        """
        try:
            receiver_name = ""
            if len(receivers) > 0:
                receiver_name = receivers[0].split(".")[0].capitalize()
            email_body = jinja2.Template(email_body).render(sender_name=sender_name, receiver_name=receiver_name)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Write a new message')]"))).click()
            
            time.sleep(2)

            self.driver.find_element(By.XPATH, "//input[contains(@aria-label, 'To')]").click()
            for receiver in receivers:
                time.sleep(0.5)
                pyperclip.copy(receiver)
                pag.hotkey("ctrl", "v")
            time.sleep(1)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Add a subject']"))).click()
            
            time.sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//textarea[@name='_message']"))).click()

            # Click on message textarea field and copy-paste the message
            time.sleep(0.5)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click send button
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error sending email '{subject}' to {receivers}", ex)

    def reply_to_email(self, sender_name, subject, email_body):
        """
        Respond to an email based on the conversation\n
        Prerequisites:
            - Logged into outlook web client
            - Opened email
        """
        try:
            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@title, 'Reply all')]"))).click()
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Expand')]"))).click()

            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, "//input[contains(@placeholder, 'Add a subject')]"))).click()

            pag.hotkey("ctrl", "a")
            time.sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click on meassage textarea field and copy and paste new message
            self.wait().until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@aria-label, 'Message body')]"))).click()

            pag.hotkey("ctrl", "a")
            time.sleep(0.5)
            receiver_name = ""
            email_body = jinja2.Template(email_body).render(sender_name=sender_name, receiver_name=receiver_name)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click the send button
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error replying to email: {subject}", ex)


    def open_specific_email(self, subject: str):
        """
        Opens specific email by email subject\n
        Prerequisites:
            - Logged into roundcube web client
        """
        # TODO: OWA behaviour
        try:
            # Click on the email subject
            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, f"//span[contains(text(), '{subject}')]"))).click()
        except NoSuchElementException:
            app_logger.error(f"No email found with subject: {subject}")

        except Exception as ex:
            raise BehaviourException(f"Error opening specific email with subject: '{subject}'", ex)

    def email_allow_files(self):
        """
        Allow files like images to show in emails\n
        Prerequisites:
            - Opened email
        """
        try:
            self.wait(5).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='InfobarImmediateTextContainer'][contains(text(), 'To always show content from this sender,')]/following-sibling::a[@role='link']"))).click()

        except Exception as ex:
            pass


class RoundcubeClient(BaseEmailWebClient):
    def __init__(self, driver: webdriver):
        super().__init__(driver)
        self.type = EmailClient.ROUNDCUBE

    def login(self, email: str, password: str):
        """
        Log in to the roundcube client\n
        Prerequisites:
            - Opened roundcube login page
        """

        self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='_user']"))).click()

        time.sleep(0.5)
        pag.write(email, 0.1)
        time.sleep(0.5)
        
        self.wait().until(EC.presence_of_element_located((By.XPATH, "//input[@name='_pass']"))).click()

        time.sleep(0.5)
        pag.write(password, 0.1)
        time.sleep(0.5)

        self.wait().until(EC.presence_of_element_located((By.XPATH, "//button[@id='rcmloginsubmit']"))).click()

    def logout(self):
        """
        Log out of roundcube web client\n
        Prerequisites:
            - Logged into roundcube web client
        """
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Logout')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error logging out of roundcube web client", ex)

    def get_unread_emails(self):
        """
        Returns list of unread emails, if there are no unread emails return empty list
        Prerequisites:
            - Logged into roundcube web client
        """
        
        try:
            unread_emails = self.wait().until(
                EC.presence_of_all_elements_located((By.XPATH, "//tr[contains(@class, 'unread')]"))
            )
            return unread_emails
        except TimeoutException:
            return []

        except Exception as ex:
            raise BehaviourException(f"Error trying to get emails", ex)

    def send_email(self, sender_name, receivers, subject, email_body):
        """
        Writes and sends email\n
        Prerequisites:
            - Logged into roundcube web client
        """
        try:
            receiver_name = ""
            if len(receivers) > 0:
                receiver_name = receivers[0].split(".")[0].capitalize()
            email_body = jinja2.Template(email_body).render(sender_name=sender_name, receiver_name=receiver_name)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Create a new message']"))).click()
            
            time.sleep(2)

            self.driver.find_element(By.XPATH, "//input[contains(@aria-label, 'To')]").click()
            for receiver in receivers:
                time.sleep(0.5)
                pyperclip.copy(receiver)
                pag.hotkey("ctrl", "v")
            time.sleep(1)

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[@name='_subject']"))).click()

            time.sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@aria-label, 'Message body')]"))).click()

            # Click on message textarea field and copy-paste the message
            time.sleep(0.5)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click send button
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Send')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error sending email '{subject}' to {receivers}", ex)

    def reply_to_email(self, sender_name, subject, email_body):
        """
        Respond to an email based on the conversation\n
        Prerequisites:
            - Logged into roundcube web client
            - Opened email
        """
        try:
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Reply to sender']"))).click()

            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//input[@name='_subject']"))).click()

            pag.hotkey("ctrl", "a")
            time.sleep(0.5)
            pyperclip.copy(subject)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click on meassage textarea field and copy and paste new message
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//textarea[@name='_message']"))).click()

            pag.hotkey("ctrl", "a")
            time.sleep(0.5)
            receiver_name = ""
            email_body = jinja2.Template(email_body).render(sender_name=sender_name, receiver_name=receiver_name)
            pyperclip.copy(email_body)
            pag.hotkey("ctrl", "v")
            time.sleep(1)

            # Click the send button
            self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Send')]"))).click()
            time.sleep(1)

        except Exception as ex:
            raise BehaviourException(f"Error replying to email: {subject}", ex)


    def open_specific_email(self, subject: str):
        """
        Opens specific email by email subject\n
        Prerequisites:
            - Logged into roundcube web client
        """
        # TODO: OWA behaviour
        try:
            # Click on the email subject
            self.wait().until(EC.element_to_be_clickable(
                (By.XPATH, f"//span[contains(text(), '{subject}')]"))).click()
        except NoSuchElementException:
            app_logger.error(f"No email found with subject: {subject}")

        except Exception as ex:
            raise BehaviourException(f"Error opening specific email with subject: '{subject}'", ex)
        
    def email_allow_files(self):
        """
        NOT IMPLEMENTED!

        Allow files like images to show in emails\n
        Prerequisites:
            - Opened email
        """
        pass

def getEmailClient(email_client: str | EmailClient, driver: webdriver) -> BaseEmailWebClient:
    email_client_mapping = {
        EmailClient.ROUNDCUBE: RoundcubeClient,
        EmailClient.OWA: OutlookWebAccessClient,
        EmailClient.O365: O365Client
    }

    # Convert string to enum if necessary
    if isinstance(email_client, str):
        email_client = EmailClient(email_client)

    if email_client not in email_client_mapping:
        raise NoSuchElementException(f"Email client could not be found for: {email_client}")

    return email_client_mapping[email_client](driver)

def getSeleniumController(email_client: EmailClient = None):
    if platform.system() == "Linux":
        return FirefoxSeleniumController(email_client)
    return EdgeSeleniumController(email_client)