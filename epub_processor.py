from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
import os
import zipfile
import shutil
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine, LTChar
import re
import logging

# Classe pour traiter les fichiers EPUB
class EpubProcessor:
    class Chapter:
        def __init__(self, title, content_src, content=''):
            self.title = title
            self.content_src = content_src
            self.content = content

        def display_chapter_details(self):
            title = self.title if self.title else "Chapitre"
            content = self.content if self.content else "Contenu non disponible"
            return f"{title} : {content[:100]}"

    def __init__(self):
        self.chapters = []

    def extract_metadata(self, epub_path):
        chapters = []
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('ncx'):
                    with zip_ref.open(file, 'r') as ncx_file:
                        soup = BeautifulSoup(ncx_file, 'xml')
                        nav_points = soup.find_all('navPoint')
                        for nav_point in nav_points:
                            title = nav_point.find('text').text.strip()
                            if not title.endswith('.'):
                                title += '.'
                            content_src = nav_point.find('content').get('src')
                            chapters.append(self.Chapter(title, content_src))
        return chapters

    def extract_content_from_archive(self, epub_path):
        temp_dir = 'temp_epub'
        os.makedirs(temp_dir, exist_ok=True)
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return temp_dir

    def extract_text_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text(separator='\n', strip=True)
                text_content = re.sub(r'(?<!\n)\n(?!\n)', ' ', text_content)
                return text_content
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
            return ''

    def analyze_epub(self, epub_path):
        self.chapters = self.extract_metadata(epub_path)
        temp_dir = self.extract_content_from_archive(epub_path)
        text_by_file = {}

        try:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.html', '.htm', '.xhtml')):
                        file_path = os.path.join(root, file)
                        text_content = self.extract_text_from_file(file_path)
                        text_by_file[file] = text_content.strip()

            for chapter in self.chapters:
                content_src = chapter.content_src
                if content_src:
                    file_name = os.path.basename(content_src.split('#')[0])
                    file_candidates = [file for file in text_by_file if file_name in file]

                    if file_candidates:
                        chapter.content = text_by_file.get(file_candidates[0], '')
                    else:
                        chapter.content = ''
                
                chapter.content = re.sub(r'\s+', ' ', chapter.content).strip()
                
        finally:
            shutil.rmtree(temp_dir)

        return self.chapters

# Classe pour traiter les fichiers PDF
class PdfProcessor:
    def extract_text_and_fonts_from_pdf(self, pdf_path):
        laparams = LAParams()
        text_content = []
        for page_layout in extract_pages(pdf_path, laparams=laparams):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        if isinstance(text_line, LTTextLine):
                            line_text = text_line.get_text().strip()
                            font_sizes = [char.size for char in text_line if isinstance(char, LTChar)]
                            if font_sizes:
                                max_font_size = max(font_sizes)
                                text_content.append((line_text, max_font_size))
        return text_content

    def detect_chapters(self, text_content):
        chapters = []
        chapter_pattern = re.compile(r'^(Chapter|Chapitre|Part|Section|Titre)\s+\d+.*$', re.IGNORECASE)
        current_chapter = None
        chapter_content = []
        if text_content:
            title_font_size_threshold = max(font_size for _, font_size in text_content) * 0.9
        else:
            title_font_size_threshold = 0

        for line, font_size in text_content:
            if chapter_pattern.match(line) or font_size >= title_font_size_threshold:
                if current_chapter:
                    chapters.append({'title': current_chapter, 'content': '\n'.join(chapter_content)})
                    chapter_content = []
                current_chapter = line
            else:
                if current_chapter:
                    chapter_content.append(line)
        if current_chapter:
            chapters.append({'title': current_chapter, 'content': '\n'.join(chapter_content)})
        return chapters

    def analyze_pdf(self, pdf_path):
        text_content = self.extract_text_and_fonts_from_pdf(pdf_path)
        return self.detect_chapters(text_content)

# Interface Kivy
class MainScreen(Screen):
    epub_content = StringProperty("")
    pdf_content = StringProperty("")

    def load_epub(self, epub_path):
        processor = EpubProcessor()
        chapters = processor.analyze_epub(epub_path)
        self.epub_content = "\n".join([chapter.display_chapter_details() for chapter in chapters])
        self.show_popup("EPUB Analysis", self.epub_content)

    def load_pdf(self, pdf_path):
        processor = PdfProcessor()
        chapters = processor.analyze_pdf(pdf_path)
        self.pdf_content = "\n".join([f"{chapter['title']}:\n{chapter['content'][:100]}" for chapter in chapters])
        self.show_popup("PDF Analysis", self.pdf_content)

    def show_popup(self, title, content):
        popup = Popup(title=title, content=Label(text=content), size_hint=(0.8, 0.8))
        popup.open()

class FileProcessorApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    FileProcessorApp().run()
