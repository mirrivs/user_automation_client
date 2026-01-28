"""
Utility functions for Roundcube web client
-
Prerequisites:
    - Opened roundcube login page
"""

import time
import os
import sys
import pyautogui as pag

from app_logger import app_logger

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

def login(email, password):
    """
    Logs into roundcube web client\n
    Prerequisites:
        - Opened roundcube login page
    """
    try:
        roundcube_logo_path = os.path.join(PARENT_DIR, "roundcube_logo.png")
        roundcube_logo = pag.locateCenterOnScreen(roundcube_logo_path, minSearchTime=3, confidence=0.7)

        if roundcube_logo:
            time.sleep(1)
            pag.write(email, 0.1)
            time.sleep(1)
            pag.press("tab")
            time.sleep(1)
            pag.write(password, 0.1)
            pag.press("enter")
        else:
            app_logger.error("Roundcube login failed, roundcube not found")
            sys.exit(1)

    except Exception as ex:
        app_logger.error(f"Failed logging into roundcube, Ex: {ex}")
        sys.exit(1)


def scan_email():
    """
    Scans email body for attachments and phishing links\n
    Prerequisites:
        - Opened email in roundcube web client
    """
    try:
        # Allow external files
        allow_ext_files_sk_path = os.path.join(PARENT_DIR, "allow_ext_file_sk.png")
        allow_ext_files_en_path = os.path.join(PARENT_DIR, "allow_ext_file_en.png")

        allow_ext_files_sk: pag.Point = pag.locateCenterOnScreen(
            allow_ext_files_sk_path, minSearchTime=1, confidence=0.7)
        if allow_ext_files_sk:
            pag.click(allow_ext_files_sk.x, allow_ext_files_sk.y)

        allow_ext_files_en: pag.Point = pag.locateCenterOnScreen(
            allow_ext_files_en_path, minSearchTime=1, confidence=0.7)
        if allow_ext_files_en:
            pag.click(allow_ext_files_en.x, allow_ext_files_en.y)

        time.sleep(2)

        # Check for office365 phishing link
        office365_phish_link_path = os.path.join(PARENT_DIR, "office365_phish_link.png")
        office365_phish_link: pag.Point = pag.locateCenterOnScreen(office365_phish_link_path, confidence=0.7)
        if office365_phish_link:
            return 0, "Found office365 phishing link"

        # Check for roundcube phishing link
        roundcube_phish_link_path = os.path.join(PARENT_DIR, "roundcube_phish_link.png")
        roundcube_phish_link: pag.Point = pag.locateCenterOnScreen(roundcube_phish_link_path, confidence=0.7)
        if roundcube_phish_link:
            return 0, "Found roundcube phishing link"

        # Check for attachments
        email_attachment_path = os.path.join(PARENT_DIR, "email_attachment.png")
        email_attachment: pag.Point = pag.locateCenterOnScreen(email_attachment_path, confidence=0.7)
        if email_attachment:
            return 0, "Found email attachment"

        return 0, "No suspicious content found"
    except Exception as ex:
        return 1, ex


def download_attachment():
    """
    Downloads attachment from email\n
    Prerequisites:
        - Opened email in roundcube web client with email attachment
    """
    try:
        email_attachment_path = os.path.join(PARENT_DIR, "email_attachment.png")
        email_attachment: pag.Point = pag.locateCenterOnScreen(email_attachment_path, minSearchTime=2, confidence=0.7)
        pag.click(email_attachment.x + 14, email_attachment.y - 2)

        download_attachment_path = os.path.join(PARENT_DIR, "download_attachment.png")
        download_attachment: pag.Point = pag.locateCenterOnScreen(
            download_attachment_path, minSearchTime=2, confidence=0.7)
        pag.click(download_attachment.x, download_attachment.y)

        time.sleep(7)
        return 0, "Downloaded email attachment"

    except Exception as ex:
        return 1, ex


def open_roundcube_phishing_website():
    """
    Opens ronudcube phishing website\n
    Prerequisites:
        - Opened email in roundcube web client with roundcube phishing button
    """
    try:
        roundcube_phish_link_path = os.path.join(PARENT_DIR, "roundcube_phish_link.png")
        roundcube_phish_link: pag.Point = pag.locateCenterOnScreen(roundcube_phish_link_path, confidence=0.7)
        if roundcube_phish_link:
            pag.click(roundcube_phish_link.x, roundcube_phish_link.y)
        else:
            return 0, "No roundcube phishing link found"

        time.sleep(3)

        roundcube_logo_path = os.path.join(PARENT_DIR, "roundcube_logo.png")
        roundcube_logo = pag.locateCenterOnScreen(roundcube_logo_path, minSearchTime=4, confidence=0.7)
        if roundcube_logo:
            return 0, "Opened roundcube phishing link"
        return 1, "Could not open roundcube phishing link"

    except Exception as ex:
        return 1, ex


def open_office365_phishing_website():
    """
    Opens office365 phishing website\n
    Prerequisites:
        - Opened email in roundcube web client with office365 phishing button
    """
    try:
        office365_phish_link_path = os.path.join(PARENT_DIR, "office365_phish_link.png")
        office365_phish_link: pag.Point = pag.locateCenterOnScreen(office365_phish_link_path, confidence=0.7)
        if office365_phish_link:
            pag.click(office365_phish_link.x, office365_phish_link.y)
        else:
            return 0, "No office365 phishing link found"
        time.sleep(2)
        pag.hotkey("ctrl", "l")
        time.sleep(0.5)
        pag.press("right")
        time.sleep(0.5)
        pag.press("enter")
        time.sleep(2)
        return 0, "Opened office365 phishing website"

    except Exception as ex:
        return 1, ex


def open_mail():
    """
    Open mailbox\n
    Prerequisites:
        - Logged into roundcube web client
    """
    try:
        email_icon_path = os.path.join(PARENT_DIR, "email_icon_white.png")
        email_icon: pag.Point = pag.locateCenterOnScreen(email_icon_path, minSearchTime=3, confidence=0.7)
        if email_icon:
            pag.click(email_icon)
            return 0, "Opened email folder"
        else:
            return 1, "No email icon found"

    except Exception as ex:
        return 1, ex


def filter_by_unread():
    """
    Filters emails by unread\n
    Prerequisites:
        - Logged into roundcube web client
    """
    try:
        email_icon_path = os.path.join(PARENT_DIR, "email_icon_black.png")
        email_icon: pag.Point = pag.locateCenterOnScreen(email_icon_path, minSearchTime=3, confidence=0.7)
        if email_icon:
            pag.click(email_icon)
            return 0, "Filtered by unread"
        else:
            return 1, "No email icon found"

    except Exception as ex:
        return 1, ex


def logout():
    """
    Log out of roundcube web client\n
    Prerequisites:
        - Logged into roundcube web client 
    """
    try:
        logout_icon_path = os.path.join(PARENT_DIR, "logout_icon.png")
        logout_icon: pag.Point = pag.locateCenterOnScreen(logout_icon_path, minSearchTime=4, confidence=0.7)
        if logout_icon:
            pag.click(logout_icon)
            return 0, "Logged out of roundcube"
        else:
            return 1, "Roundcube logout failed"

    except Exception as ex:
        return 1, ex
