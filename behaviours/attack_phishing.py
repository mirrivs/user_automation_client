import os
import platform
import time
import sys

from app_config import get_app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.selenium_utils import EdgeSeleniumController, EmailClientType, FirefoxSeleniumController, getSeleniumController
from utils.behaviour_utils import BehaviourThread

# Scripts imports
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class BehaviourAttackPhishing(BehaviourThread):
    """
    Behaviour for opening phishing website from email.

    This class can be directly instantiated and started from the behaviour manager.
    """

    # Behaviour metadata
    name = "attack_phishing"
    display_name = "Phishing"
    category = "ATTACK"
    description = "Phishing attack"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        app_config = get_app_config()
        self.landscape_id = int(app_config["app"]["landscape"])
        self.user = app_config["behaviour"]["general"]["user"]
        self.behaviour_general = app_config["behaviour"]["general"]
        self.behaviour_cfg = app_config["behaviour"]["behaviours"]["attack_phishing"]
        self.selenium_controller = None

    def run_behaviour(self):
        """Main behaviour execution - can be interrupted at any time"""
        app_logger.info("Starting attack_phishing behaviour")

        self.selenium_controller = getSeleniumController("owa" if self.landscape_id in [2] else "roundcube")
        email_client = self.selenium_controller.email_client

        # Register selenium controller with cleanup manager
        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(self.behaviour_general["organization_mail_server_url"])

        email_client.login(self.user["email"], self.user["password"])

        if email_client.type == "roundcube":
            self.selenium_controller.roundcube_set_language()

        time.sleep(4)

        unread_emails = email_client.get_unread_emails()

        # Search for email with phishing subject in unread emails
        for email in unread_emails:
            if email_client.type == "roundcube":
                subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")
            else:
                subject_link = email.find_element(
                    By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]")
            if subject_link.text == self.behaviour_cfg["malicious_email_subject"]:
                subject_link.click()
                break

        if email_client.type == "roundcube":
            iframe = self.selenium_controller.driver.find_element(By.NAME, "messagecontframe")
            time.sleep(1)
            self.selenium_controller.driver.switch_to.frame(iframe)

        email_client.email_allow_files()
        found_phishing_link = False
        # Roundcube phishing link
        try:
            self.selenium_controller.driver.find_element(
                By.XPATH, "//a[contains(text(), 'SECURE ACCOUNT') or contains(text(), 'ZABEZPEČIŤ ÚČET')]").click()

            if email_client.type == "roundcube":
                self.selenium_controller.driver.switch_to.default_content()
            found_phishing_link = True
            time.sleep(2)

            self.selenium_controller.switch_tab()
            self.selenium_controller.phishing_roundcube_enter_credentials(self.user["email"], self.user["password"])
            time.sleep(1)
            BrowserUtils.close_latest_tab()

            app_logger.info("Entered roundcube phishing credentials")
        except NoSuchElementException:
            # No phishing link found
            pass

        # Office365 phishing link - owa
        try:
            self.selenium_controller.driver.find_element(
                By.XPATH, "//a[contains(text(), 'Verify Password') or contains(text(), 'Overiť heslo')]").click()

            if email_client.type == "roundcube":
                self.selenium_controller.driver.switch_to.default_content()

            found_phishing_link = True
            time.sleep(2)

            self.selenium_controller.switch_tab()
            self.selenium_controller.phishing_owa_enter_credentials(self.user["email"], self.user["password"])
            time.sleep(1)
            BrowserUtils.close_latest_tab()

            app_logger.info("Entered owa phishing credentials")
        except NoSuchElementException:
            # No phishing link found
            pass

        if found_phishing_link:
            # Switch back to original tab
            self.selenium_controller.switch_tab()
        else:
            app_logger.error("No phishing link found")
            sys.exit(1)

        app_logger.info("Completed attack_phishing behaviour")


# Legacy function wrapper for backward compatibility
def behaviour_attack_phishing(cleanup_manager: CleanupManager):
    """
    Legacy function wrapper - creates and runs the behaviour class.
    """
    behaviour = BehaviourAttackPhishing(cleanup_manager)
    behaviour.start()
    behaviour.join()


def behaviour_roundcube():
    """
    This behaviour opens all types of phishing websites using roundcube web client
    """
    try:
        os_type = platform.system()
        driver = selenium_controller.driver

        selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(user["roundcube_url"])
        time.sleep(4)

        selenium_controller.roundcube_login(user["email"], user["password"])
        time.sleep(4)

        selenium_controller.roundcube_set_language()
        unread_emails = selenium_controller.roundcube_get_unread_emails()
        
        for email in unread_emails:
            # Search for email with phishing subject in unread emails
            subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")
            if subject_link.text == roundcube_phishing_cfg["phish_email_subject"]:
                subject_link.click()
                break

        # Switch to email Iframe
        iframe = driver.find_element(By.NAME, "messagecontframe")
        time.sleep(1)
        driver.switch_to.frame(iframe)

        found_phishing_link = False
        # Roundcube phishing link
        try:
            driver.find_element(
                By.XPATH, "//a[contains(text(), 'SECURE ACCOUNT') or contains(text(), 'ZABEZPEČIŤ ÚČET')]").click()
            driver.switch_to.default_content()
            found_phishing_link = True
            time.sleep(2)

            selenium_controller.switch_tab()
            selenium_controller.phishing_roundcube_enter_credentials(user["email"], user["password"])
            time.sleep(1)
            BrowserUtils.close_latest_tab()

            app_logger.info("Entered roundcube phishing credentials")
        except NoSuchElementException:
            # No phishing link found
            pass

        # Office365 phishing link - owa
        try:
            driver.find_element(
                By.XPATH, "//a[contains(text(), 'Verify Password') or contains(text(), 'Overiť heslo')]").click()
            driver.switch_to.default_content()
            found_phishing_link = True
            time.sleep(2)

            selenium_controller.switch_tab()
            selenium_controller.phishing_owa_enter_credentials(user["email"], user["password"])
            time.sleep(1)
            BrowserUtils.close_latest_tab()

            app_logger.info("Entered roundcube phishing credentials")
        except NoSuchElementException:
            # No phishing link found
            pass

        if found_phishing_link:
            # Switch back to original tab
            selenium_controller.switch_tab()
        else:
            app_logger.error("No phishing link found")
            sys.exit(1)

        time.sleep(1)

        print("Roundcube phishing behaviour finished successfully")

    except Exception as ex:
        app_logger.error(ex)
        sys.exit()

    finally:
        selenium_controller.quit_driver()
        sys.exit()


def behaviour_owa():
    """
    This behaviour opens all types of phishing websites using outlook web access
    """
    driver = selenium_controller.driver

    selenium_controller.maximize_driver_window()
    time.sleep(4)

    BrowserUtils.search_by_url(user["owa_url"])
    time.sleep(4)

    selenium_controller.owa_login(user["email"], user["password"])
    time.sleep(4)

    unread_emails = selenium_controller.owa_get_unread_emails()

    # Find email with phishing subject
    for email in unread_emails:
        subject_link = email.find_element(
            By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]")
        if subject_link.text == roundcube_phishing_cfg["phish_email_subject"]:
            subject_link.click()
            break

    selenium_controller.owa_allow_email_files()
    found_phishing_link = False
    # Roundcube phishing link
    try:
        driver.find_element(
            By.XPATH, "//a[contains(text(), 'SECURE ACCOUNT') or contains(text(), 'ZABEZPEČIŤ ÚČET')]").click()
        found_phishing_link = True
        time.sleep(2)

        selenium_controller.switch_tab()
        selenium_controller.phishing_roundcube_enter_credentials(user["email"], user["password"])
        time.sleep(1)
        BrowserUtils.close_latest_tab()

        app_logger.info("Entered roundcube phishing credentials")
    except NoSuchElementException:
        # No phishing link found
        pass

    # Office365 phishing link - owa
    try:
        driver.find_element(
            By.XPATH, "//a[contains(text(), 'Verify Password') or contains(text(), 'Overiť heslo')]").click()
        found_phishing_link = True
        time.sleep(2)

        selenium_controller.switch_tab()
        selenium_controller.phishing_owa_enter_credentials(user["email"], user["password"])
        time.sleep(1)
        BrowserUtils.close_latest_tab()

        app_logger.info("Entered owa phishing credentials")
    except NoSuchElementException:
        # No phishing link found
        pass

    if found_phishing_link:
        # Switch back to original tab
        selenium_controller.switch_tab()
    else:
        app_logger.error("No phishing link found")
        sys.exit(1)

    print("Exchange phishing behaviour finished successfully")
