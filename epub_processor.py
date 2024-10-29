import os
import zipfile
import shutil
import re
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTTextLine, LTChar
import re
from collections import defaultdict, OrderedDict
import logging
import tempfile
from pathlib import Path

class EpubProcessor:
    class Chapter:
        def __init__(self, title, content_src, content=''):
            self.title = title
            self.content_src = content_src
            self.content = content

        def display_chapter_details(self):
            title = self.title if self.title else "Chapitre"
            content = self.content if self.content else "Contenu non disponible"
            print(f"{title} : {content[:100]}")  # Affiche les 100 premiers caractères du contenu

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
        # Créer un dossier temporaire unique dans le dossier temp du système
        temp_dir = os.path.join(tempfile.gettempdir(), 'epub_temp_' + str(os.getpid()))
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
                text_content = re.sub(r'(?<!\n)\n(?!\n)', ' ', text_content)  # Merge single newlines
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
                        if len(file_candidates) > 1:
                            logging.warning(f"Plusieurs fichiers correspondent à content_src {content_src}: {file_candidates}")
                    else:
                        logging.warning(f"Aucun fichier ne correspond à content_src {content_src}")
                        chapter.content = ''

                    if not chapter.content.strip():
                        logging.warning(f"Attention: le chapitre '{chapter.title}' est vide. Vérifiez le fichier source {content_src}.")

                chapter.content = re.sub(r'\s+', ' ', chapter.content).strip()

            # Après avoir rempli tous les chapitres, on nettoie les doublons
            cleaned_chapters = []
            i = 0
            while i < len(self.chapters):
                current = self.chapters[i]
                
                # Si on n'est pas au dernier chapitre
                if i < len(self.chapters) - 1:
                    next_chap = self.chapters[i + 1]
                    
                    # Logs de debug
                    print(f"\nComparaison des chapitres:")
                    print(f"Chapitre actuel: {current.title}")
                    print(f"Chapitre suivant: {next_chap.title}")
                    
                    # Normaliser les contenus pour la comparaison
                    current_content = re.sub(r'\s+', '', current.content)
                    next_content = re.sub(r'\s+', '', next_chap.content)
                    
                    print(f"Longueur contenu actuel: {len(current_content)}")
                    print(f"Longueur contenu suivant: {len(next_content)}")
                    print(f"Contenus identiques: {current_content == next_content}")
                    
                    # Si les contenus sont identiques après normalisation
                    if current_content == next_content:
                        print("Contenus identiques détectés!")
                        selected_chapter = self._select_best_chapter_title(current, next_chap)
                        print(f"Titre sélectionné: {selected_chapter.title}")
                        cleaned_chapters.append(selected_chapter)
                        i += 2  # On saute le chapitre suivant
                        continue
                
                cleaned_chapters.append(current)
                i += 1

            self.chapters = cleaned_chapters
            return self.chapters

        finally:
            shutil.rmtree(temp_dir)

    def _select_best_chapter_title(self, chap1, chap2):
        """Sélectionne le meilleur titre entre deux chapitres."""
        chapter_pattern = re.compile(r'^(Chapter|Chapitre)\s+\d+\.?.*$', re.IGNORECASE)
        
        print(f"\nSélection du meilleur titre entre:")
        print(f"Titre 1: {chap1.title}")
        print(f"Titre 2: {chap2.title}")
        print(f"Match pattern 1: {bool(chapter_pattern.match(chap1.title))}")
        print(f"Match pattern 2: {bool(chapter_pattern.match(chap2.title))}")
        
        if chapter_pattern.match(chap1.title) and not chapter_pattern.match(chap2.title):
            print("Sélection titre 1")
            return chap1
        elif chapter_pattern.match(chap2.title) and not chapter_pattern.match(chap1.title):
            print("Sélection titre 2")
            return chap2
        
        print("Sélection par défaut titre 1")
        return chap1

import re

def clean_and_format_text(text):
    # Supprimer les sauts de ligne multiples
    text = re.sub(r'\n{2,}', '\n\n', text)
    
    # Joindre les lignes qui ne se terminent pas par un point, sauf si la ligne suivante commence par une majuscule
    lines = text.split('\n')
    formatted_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if not line.endswith(('.', '!', '?', ':', '"', "'")) and (not next_line or not next_line[0].isupper()):
                formatted_lines.append(line + ' ')
            else:
                formatted_lines.append(line + '\n')
        else:
            formatted_lines.append(line)
    
    formatted_text = ''.join(formatted_lines)
    
    # Supprimer les espaces multiples
    formatted_text = re.sub(r' {2,}', ' ', formatted_text)
    
    return formatted_text.strip()

class PdfProcessor:
    def __init__(self):
        pass

    def extract_text_and_fonts_from_pdf(self, pdf_path):
        laparams = LAParams()
        text_content = []

        # Extract text and font information from each page
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
        chapter_pattern = re.compile(r'^(Chapter|Chapitre)\s+\d+\.?.*$', re.IGNORECASE)
        
        current_chapter = None
        chapter_content = []
        seen_content = set()

        if text_content:
            title_font_size_threshold = max(font_size for _, font_size in text_content) * 0.9
        else:
            title_font_size_threshold = 0

        # Première passe pour collecter les chapitres
        for line, font_size in text_content:
            is_standard_chapter = chapter_pattern.match(line)
            is_large_font = font_size >= title_font_size_threshold
            
            if is_standard_chapter or is_large_font:
                if current_chapter:
                    chapter_text = '\n'.join(chapter_content)
                    chapter_text = clean_and_format_text(chapter_text)
                    chapters.append({'title': current_chapter, 'content': chapter_text})
                    chapter_content = []
                current_chapter = line
            else:
                if current_chapter:
                    chapter_content.append(line)

        # Traiter le dernier chapitre
        if current_chapter and chapter_content:
            chapter_text = '\n'.join(chapter_content)
            chapter_text = clean_and_format_text(chapter_text)
            chapters.append({'title': current_chapter, 'content': chapter_text})

        # Deuxième passe pour nettoyer les doublons
        cleaned_chapters = []
        i = 0
        while i < len(chapters):
            current = chapters[i]
            
            # Si on n'est pas au dernier chapitre
            if i < len(chapters) - 1:
                next_chap = chapters[i + 1]
                
                # Ajout de logs pour debug
                print(f"\nComparaison des chapitres:")
                print(f"Chapitre actuel: {current['title']}")
                print(f"Chapitre suivant: {next_chap['title']}")
                
                # Normaliser les contenus pour la comparaison
                current_content = re.sub(r'\s+', '', current['content'])
                next_content = re.sub(r'\s+', '', next_chap['content'])
                
                print(f"Longueur contenu actuel: {len(current_content)}")
                print(f"Longueur contenu suivant: {len(next_content)}")
                print(f"Contenus identiques: {current_content == next_content}")
                
                # Si les contenus sont identiques après normalisation
                if current_content == next_content:
                    print("Contenus identiques détectés!")
                    selected_chapter = self._select_best_title(current, next_chap)
                    print(f"Titre sélectionné: {selected_chapter['title']}")
                    cleaned_chapters.append(selected_chapter)
                    i += 2
                    continue
            
            cleaned_chapters.append(current)
            i += 1
        
        return cleaned_chapters

    def _select_best_title(self, chap1, chap2):
        """Sélectionne le meilleur titre entre deux chapitres."""
        # Privilégier le format "Chapitre X"
        chapter_pattern = re.compile(r'^(Chapter|Chapitre)\s+\d+\.?.*$', re.IGNORECASE)
        
        # Ajout de logs pour debug
        print(f"\nSélection du meilleur titre entre:")
        print(f"Titre 1: {chap1['title']}")
        print(f"Titre 2: {chap2['title']}")
        print(f"Match pattern 1: {bool(chapter_pattern.match(chap1['title']))}")
        print(f"Match pattern 2: {bool(chapter_pattern.match(chap2['title']))}")
        
        if chapter_pattern.match(chap1['title']) and not chapter_pattern.match(chap2['title']):
            print("Sélection titre 1")
            return chap1
        elif chapter_pattern.match(chap2['title']) and not chapter_pattern.match(chap1['title']):
            print("Sélection titre 2")
            return chap2
        
        print("Sélection par défaut titre 1")
        return chap1

    def analyze_pdf(self, pdf_path):
        text_content = self.extract_text_and_fonts_from_pdf(pdf_path)
        return self.detect_chapters(text_content)

def clean_tmp():
    # Nettoyer tous les dossiers temporaires créés par l'application
    temp_base = tempfile.gettempdir()
    patterns = ['epub_temp_*', 'audiobook_temp*']
    
    for pattern in patterns:
        for temp_dir in Path(temp_base).glob(pattern):
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logging.info(f"Dossier temporaire supprimé : {temp_dir}")
            except Exception as e:
                logging.error(f"Erreur lors de la suppression du dossier temporaire {temp_dir}: {e}")

# Assurez-vous que clean_tmp est exportée si vous utilisez __all__
__all__ = ['EpubProcessor', 'PdfProcessor', 'clean_tmp']
