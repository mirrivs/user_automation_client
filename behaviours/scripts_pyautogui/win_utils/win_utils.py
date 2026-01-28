"""
Utility functions for Windows operating system
-
Prerequisites:
    - Windows operating system
"""


import time
import os
import pyautogui as pag

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


# # CTRL + SHIFT + 6 = file explorer view details
# def set_sort_by_date():
#     try:
#         click("1689242090615.png")
#         wait("1689242100443.png")

#         click("1689242100443.png")
#         wait("1689242125333.png")
#         if not exists("1694091558265.png"):
#             click("1689242125333.png")
#         else:
#             click("1689242100443.png")
#         logger.log("info", "Finished setting sort by date", "success")
#     except Exception as ex:
#         logger.log("error", "Error while setting sort by date", "failure", ex)


# def set_group_by_none():
#     try:
#         click("1689242090615.png")
#         wait("1694090959285.png")
#         click("1694090959285.png")
#         wait(3)
#         if exists("1694090986683.png"):
#             click("1694090986683.png")
#         else:
#             click("1694090959285.png")
#         logger.log("info", "Finished setting group by none", "success")
#     except Exception as ex:
#         logger.log("error", "Error while setting group by none", "failure", ex)


# def open_top_file():
#     try:
#         doubleClick(Pattern("1690984136705.png").targetOffset(159,211))
#         wait(30)
#         logger.log("info", "Finished opening top file", "success")
#     except Exception as ex:
#         logger.log("error", "Error while opening top file", "failure", ex)


# def get_file_extension():
#     type(Key.F2)
#     wait(0.5)
#     type(Key.RIGHT)
#     wait(0.5)
#     for i in range(20):
#         type(Key.RIGHT, Key.SHIFT)
#         wait(0.1)
#     copy()
#     escape()
#     clipboard_content = Env.getClipboard()
#     logger.log("info", "{clipboard}".format(clipboard=clipboard_content), "success")


# def check_or_create_folder(path):
#     try:
#         splitPath = path.split("\\")
#         if splitPath[0] == "C:":
#             splitPath.pop(0)
#         if not exists("1689173481864.png"):
#             if not exists("1689157571730.png"):
#                 type("e", Key.WIN)
#             else:
#                 click("1689157571730.png")
#             wait("1689173481864.png")
#         maximizeWindow()
#         click("1689173481864.png")
#         doubleClick("1689174926315.png")
#         partialPath = "C:"

#         for pathPiece in splitPath:
#             partialPath += "\\" + pathPiece
#             if not os.path.isdir(partialPath):
#                 logger.log("info", "Created new folder: {path}".format(path=partialPath), "success")
#                 if not exists("1690288251385.png"):
#                     click("1690288271258.png")
#                     wait("1690288251385.png")
#                 click("1690288251385.png")
#                 wait(1)
#                 type(pathPiece)
#                 type(Key.ENTER)
#             else:
#                 wait(1)
#                 type(pathPiece)
#             wait(2)
#             type(Key.ENTER)
#         logger.log("info", "Finished checking folder: {path}".format(path=path), "success")
#     except Exception as ex:
#         logger.log("error", "Error while checking folder: {path}, on level: {subPath}".format(path=path, subPath=partialPath), "failure", ex)

# def selectFile(path):
#     try:
#         if not os.path.exists(partialPath):
#             raise Exception("File {file} doesn"t exist!".format(file=path))

#         splitPath = path.split("\\")
#         if splitPath[0] == "C:":
#             splitPath.pop(0)

#         item = splitPath.pop()

#         if not exists("1689173481864.png"):
#             if not exists("1689157571730.png"):
#                 type("e", Key.WIN)
#             else:
#                 click("1689157571730.png")
#             wait("1689173481864.png")
#         maximizeWindow()
#         click("1689173481864.png")
#         doubleClick("1689174926315.png")
#         partialPath = "C:"

#         for pathPiece in splitPath:
#             partialPath += "\\" + pathPiece
#             type(pathPiece)
#             wait(1)
#             type(Key.ENTER)

#         type(item)
#         wait(1)

#         logger.log("info", "Finished selecting file: {path}".format(path=path), "success")
#     except Exception as ex:
#         logger.log("error", "Error while selecting file: {path}, on level: {subPath}".format(path=path, subPath=partialPath), "failure", ex)

# def selectLastFromDownloads():
#     try:
#         if (not exists("1689157669910.png")):
#             if not exists("1689157571730.png"):
#                 type("e", Key.WIN)
#             else:
#                 click("1689157571730.png")
#             wait("1689157669910.png")
#         maximizeWindow()
#         doubleClick("1689157669910.png")
#         wait("1689157796776.png")
#         set_group_by_none()
#         set_sort_by_date()
#         click(Pattern("1689157796776.png").targetOffset(10,65))
#         logger.log("info", "Finished selecting last file from downloads", "success")
#     except Exception as ex:
#         logger.log("error", "Error while selecting last file from downloads", "failure", ex)


def escape():
    """
    Escape, ESC
    """
    pag.press("esc")


def copy():
    """
    Copy, CTRL+C
    """
    pag.hotkey("ctrl", "c")


def cut():
    """
    Cut, CTRL+X
    """
    pag.hotkey("ctrl", "x")


def open_downloads_folder():
    pag.hotkey("win", "r")
    time.sleep(0.1)
    pag.write("downloads", 0.1)
    time.sleep(0.1)
    pag.press("enter")


def paste():
    # TODO: add recognition of duplicate files
    pag.hotkey("ctrl", "v")


def rename(new_name):
    """
    Renames selected file\n
    Prerequisites:
        - File selected
    """
    time.sleep(1)
    pag.press("f2")
    time.sleep(1)
    pag.write(new_name, 0.1)
    time.sleep(1)
    pag.press("enter")
    time.sleep(1)


def maximize_window():
    """
    Maxizes window, WIN + UP\n
    Prerequisites:
        - Opened window
    """
    pag.hotkey("win", "up")


def minimize_window():
    """
    Maxizes window, WIN + DOWN\n
    Prerequisites:
        - Opened window
    """
    pag.hotkey("win", "down")


def altf4():
    """
    Quit, ALT + F4
    """
    pag.hotkey("alt", "f4")


def ctrlf():
    """
    Find, CTRL + F
    """
    pag.hotkey("ctrl", "f")
