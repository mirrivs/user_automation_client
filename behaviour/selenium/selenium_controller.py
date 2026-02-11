import platform
import random
import time
from typing import Optional

import pyautogui as pag
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from app_logger import app_logger
from behaviour.models.exceptions import BehaviourException
from behaviour.selenium.email_web_client import (
    EmailClientUser,
    O365Client,
    OutlookWebAccessClient,
    RoundcubeClient,
    getEmailClient,
)
from behaviour.selenium.models.email_client import EmailClient
from behaviour.selenium.selenium_driver import SeleniumDriver


class SeleniumController(SeleniumDriver):
    def __init__(self, driver: webdriver, user: EmailClientUser, email_client_type: Optional[EmailClient] = None):
        super().__init__(driver)
        if email_client_type is not None:
            self.email_client: OutlookWebAccessClient | RoundcubeClient | O365Client = getEmailClient(
                email_client_type
            )(driver, user)

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
                self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@name,'email')]"))
                ).click()
            else:
                self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='email']"))).click()
            time.sleep(0.5)
            pag.write(email, 0.1)
            time.sleep(0.5)
            if self.email_client == "owa":
                self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@name,'password')]"))
                ).click()
            else:
                self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))).click()
            time.sleep(0.5)
            pag.write(password, 0.1)
            time.sleep(0.5)
            if self.email_client == "owa":
                self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@id,'rcmloginsubmit')]"))
                ).click()
            else:
                self.wait(5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='signinbutton']"))).click()

        except Exception as ex:
            raise BehaviourException("Error entering credentials into phishing web", ex)

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
            raise BehaviourException("Error logging out of roundcube web client", ex)

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
                settings_button = self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Nastavenia')]"))
                )
            except Exception:
                app_logger.info("Slovak language not found, no change made")
                return

            if element_found and settings_button.is_displayed():
                settings_button.click()
                time.sleep(1)
                self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Nastavenia')]"))
                ).click()
                time.sleep(1)
                self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Používateľské rozhranie')]"))
                ).click()
                time.sleep(1)
                # Switch to email Iframe
                iframe = self.driver.find_element(By.ID, "preferences-frame")
                self.driver.switch_to.frame(iframe)
                time.sleep(1)
                language_dropdown = self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//select[@name='_language']"))
                )
                Select(language_dropdown).select_by_value("en_US")
                time.sleep(1)
                self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Uložiť')]"))
                ).click()
                time.sleep(1)
                # Switch to default Iframe
                self.driver.switch_to.default_content()
                self.wait(5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'E-mail')]"))
                ).click()

        except Exception as ex:
            raise BehaviourException("Error changing Roundcube language", ex)

    def procrastinate_watch_youtube_shorts(self, duration: float):
        """
        Watch youtube shorts for set duration
        """
        try:
            # Wait for the "Accept all" button to be visible
            accept_button = self.wait(10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Accept')]"))
            )
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
                next_video_button = self.wait(10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next video']"))
                )
                next_video_button.click()

                total_duration += watch_duration

        except Exception as ex:
            custom_message = "Error watching youtube shorts"
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
                except Exception:
                    continue

            if not found:
                raise Exception("Accept cookies button not found.")

        except Exception as ex:
            raise BehaviourException("Error accepting google cookies", ex)

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
            raise BehaviourException("Error scrolling images", ex)

    def browse_organization_website(self, duration: float):
        """
        Change between pages and scroll on them using pg down\n
        """
        try:
            nav_links = self.wait(5).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@class, 'govuk-link idsk-header-web__nav-list-item-link')]")
                )
            )
            random.choice(nav_links).click()

            min_scroll_count = 4
            scroll_count = 0
            timer = 0
            while timer < duration:
                if scroll_count >= min_scroll_count:
                    pag.press("home")
                    nav_links = self.wait(5).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, "//a[contains(@class, 'govuk-link idsk-header-web__nav-list-item-link')]")
                        )
                    )
                    self.wait(5).until(EC.element_to_be_clickable(random.choice(nav_links))).click()
                    scroll_count = 0

                pag.press("pgdn")
                scroll_count += 1

                sleep_time = random.randint(3, 6)
                time.sleep(sleep_time)
                timer += sleep_time

        except Exception as ex:
            raise BehaviourException("Error browsing organisation website", ex)

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
            raise BehaviourException("Error logging into outlook web access", ex)

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
                        By.XPATH, "//span[contains(@class, '_ay_x ms-font-m')]"
                    )
                else:
                    attachment_name_element = attachment.find_element(By.XPATH, "//span[@class='attachment-name']")

                downloaded_attachments.append(attachment_name_element.text)
                attachment.click()
                time.sleep(5)

            return downloaded_attachments

        except Exception as ex:
            raise BehaviourException("Error trying to download email attachments", ex)

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
                attachments = self.wait(5).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class, 'attachmentWell')]//a[contains(@class, 'o365button')]")
                    )
                )
            else:
                attachments = self.wait(5).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//ul[contains(@class, 'attachmentslist')]/li/a[contains(@class, 'filename')]")
                    )
                )
            return attachments
        except TimeoutException:
            return []
        except Exception as ex:
            raise BehaviourException("Error trying to get email attachments", ex)

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

    def __init__(self, email_client_type: EmailClient, user: EmailClientUser):
        options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--enable-chrome-browser-cloud-management")
        super().__init__(webdriver.Edge(options=options), email_client_type, user)


class FirefoxSeleniumController(SeleniumController):
    """
    Controller for firefox selenium\n
    Prerequisites:
        - Installed firefox webdriver
    """

    def __init__(self, email_client_type: EmailClient, user: EmailClientUser):
        options = webdriver.FirefoxOptions()
        options.set_preference("acceptInsecureCerts", True)
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        super().__init__(webdriver.Firefox(options=options), email_client_type, user)


def getSeleniumController(email_client: EmailClient, user: EmailClientUser):
    if platform.system() == "Linux":
        return FirefoxSeleniumController(email_client, user)
    return EdgeSeleniumController(email_client, user)
