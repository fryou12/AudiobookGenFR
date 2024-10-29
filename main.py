import sys
import os
import logging
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from gui import EpubToAudioGUIKivy  # Import du fichier Kivy correspondant

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainScreen(Screen):
    # Référence à l'interface principale de l'application
    app_interface = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.app_interface = EpubToAudioGUIKivy()  # Instancie l'interface Kivy
        self.add_widget(self.app_interface)

class EpubToAudioApp(App):
    def build(self):
        self.title = "ePub to Audiobook Converter"
        Window.size = (500, 600)  # Dimensions minimales de la fenêtre

        # Configuration du ScreenManager
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == "__main__":
    try:
        EpubToAudioApp().run()
    except Exception as e:
        logging.error("An error occurred: %s", e)
