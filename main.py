# main.py

import sys
import os
import logging
import tkinter as tk
from gui import EpubToAudioGUI

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    try:
        root = tk.Tk()
        root.title("ePub to Audiobook Converter")
        root.minsize(500, 600)

        # Optionally, set an icon for the application
        # icon_path = resource_path("icon.ico")
        # if os.path.exists(icon_path):
        #     root.iconbitmap(icon_path)

        app = EpubToAudioGUI(root)
        root.mainloop()
    except Exception as e:
        logging.error("An error occurred: %s", e)

if __name__ == "__main__":
    main()