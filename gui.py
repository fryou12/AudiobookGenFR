# gui_kivy.py

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from epub_processor import EpubProcessor, PdfProcessor, clean_tmp
from text_to_speech import text_to_speech, SUPPORTED_VOICES
import os
import threading
import asyncio
import pygame

class EpubToAudioGUI(BoxLayout):
    epub_path = StringProperty("")
    output_path = StringProperty("")
    selected_voice = StringProperty("4 - fr-FR-RemyMultilingualNeural")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"

        # Barre de sélection de fichier
        self.add_widget(Label(text="Fichier ePub ou PDF :"))
        self.epub_input = TextInput()
        self.add_widget(self.epub_input)
        choose_epub_btn = Button(text="Choisir un fichier")
        choose_epub_btn.bind(on_release=self.choose_epub)
        self.add_widget(choose_epub_btn)

        # Sélection du dossier de sortie
        self.add_widget(Label(text="Dossier de destination :"))
        self.output_input = TextInput()
        self.add_widget(self.output_input)
        choose_output_btn = Button(text="Choisir le dossier")
        choose_output_btn.bind(on_release=self.choose_output)
        self.add_widget(choose_output_btn)

        # Menu déroulant pour sélectionner la voix
        self.add_widget(Label(text="Sélection de la voix :"))
        voice_dropdown = DropDown()
        for voice in SUPPORTED_VOICES.keys():
            btn = Button(text=f"{voice} - {SUPPORTED_VOICES[voice]}", size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: voice_dropdown.select(btn.text))
            voice_dropdown.add_widget(btn)
        mainbutton = Button(text='Choisir une voix')
        mainbutton.bind(on_release=voice_dropdown.open)
        voice_dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', x))
        self.add_widget(mainbutton)

        # Boutons de conversion et d'analyse
        convert_btn = Button(text="Convertir en PDF")
        convert_btn.bind(on_release=self.convert_to_pdf)
        self.add_widget(convert_btn)

        analyze_btn = Button(text="Analyser le document")
        analyze_btn.bind(on_release=self.analyze_epub)
        self.add_widget(analyze_btn)

        # Barre de progression
        self.progress = ProgressBar(max=100)
        self.add_widget(self.progress)

        # Zone de texte pour les logs de conversion
        self.log_scroll = ScrollView()
        self.log_label = Label(size_hint_y=None)
        self.log_label.bind(texture_size=self.log_label.setter("size"))
        self.log_scroll.add_widget(self.log_label)
        self.add_widget(self.log_scroll)

    def choose_epub(self, instance):
        content = FileChooserIconView()
        popup = Popup(title="Sélectionnez un fichier ePub ou PDF", content=content, size_hint=(0.9, 0.9))
        content.bind(on_selection=lambda x: self.set_epub_path(x.selection, popup))
        popup.open()

    def set_epub_path(self, selection, popup):
        if selection:
            self.epub_path = selection[0]
            self.epub_input.text = self.epub_path
        popup.dismiss()

    def choose_output(self, instance):
        content = FileChooserIconView()
        popup = Popup(title="Sélectionnez un dossier de sortie", content=content, size_hint=(0.9, 0.9))
        content.bind(on_selection=lambda x: self.set_output_path(x.selection, popup))
        popup.open()

    def set_output_path(self, selection, popup):
        if selection:
            self.output_path = selection[0]
            self.output_input.text = self.output_path
        popup.dismiss()

    def convert_to_pdf(self, instance):
        # Ajouter la logique de conversion en PDF
        pass

    def analyze_epub(self, instance):
        file_path = self.epub_path
        if not file_path:
            self.log_label.text += "Veuillez sélectionner un fichier.\n"
            return

        if file_path.lower().endswith(".epub"):
            processor = EpubProcessor()
            self.chapters = processor.analyze_epub(file_path)
        elif file_path.lower().endswith(".pdf"):
            processor = PdfProcessor()
            self.chapters = processor.analyze_pdf(file_path)
        else:
            self.log_label.text += "Type de fichier non pris en charge.\n"
            return

        self.log_label.text += f"Document analysé : {len(self.chapters)} chapitres trouvés.\n"

    def start_conversion(self, instance):
        if not self.chapters:
            self.log_label.text += "Veuillez analyser un ePub avant de convertir.\n"
            return

        epub_file = self.epub_path
        if not epub_file:
            self.log_label.text += "Veuillez sélectionner un fichier ePub valide.\n"
            return

        output_dir = self.output_path
        if not output_dir:
            self.log_label.text += "Veuillez sélectionner un dossier de sortie valide.\n"
            return

        self.progress.value = 0
        voice_index = int(self.selected_voice.split(" - ")[0])
        threading.Thread(target=self.run_conversion, args=(output_dir, voice_index)).start()

    def run_conversion(self, output_dir, voice_index):
        asyncio.run(self.convert_chapters(output_dir, voice_index))

    async def convert_chapters(self, output_dir, voice_index):
        for i, chapter in enumerate(self.chapters, start=1):
            output_file = os.path.join(output_dir, f"chapitre_{i}.mp3")
            await text_to_speech(chapter.content, voice_index=voice_index, output_file=output_file)
            self.progress.value = (i / len(self.chapters)) * 100
            self.log_label.text += f"Chapitre {i} converti avec succès.\n"

class EpubToAudioApp(App):
    def build(self):
        return EpubToAudioGUI()

if __name__ == "__main__":
    EpubToAudioApp().run()
