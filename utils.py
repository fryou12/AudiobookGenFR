# utils.py

import os
import sys
from pathlib import Path
import subprocess
import shutil

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def ensure_dir(file_path):
    """
    Ensure that a directory exists. If it doesn't exist, create it.
    """
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_file_size(file_path):
    """
    Get the size of a file in bytes
    """
    return os.path.getsize(file_path)

def format_file_size(size_in_bytes):
    """
    Format file size from bytes to human-readable format
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0

def is_valid_file(file_path, extension):
    """
    Check if a file exists and has the correct extension
    """
    return os.path.isfile(file_path) and file_path.lower().endswith(extension.lower())

def get_filename_without_extension(file_path):
    """
    Get the filename without its extension
    """
    return os.path.splitext(os.path.basename(file_path))[0]

def sanitize_filename(filename):
    """
    Remove or replace characters that are unsafe for filenames
    """
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename

def create_unique_filename(directory, base_name, extension):
    """
    Create a unique filename in the given directory
    """
    counter = 1
    file_name = f"{base_name}.{extension}"
    while os.path.exists(os.path.join(directory, file_name)):
        file_name = f"{base_name}_{counter}.{extension}"
        counter += 1
    return file_name

def convert_epub_to_pdf(epub_path, output_dir):
    """
    Convertit un fichier ePub en PDF en utilisant Calibre.
    
    :param epub_path: Chemin vers le fichier ePub
    :param output_dir: Répertoire de sortie pour le fichier PDF
    :return: Chemin vers le fichier PDF généré, ou None en cas d'erreur
    """
    try:
        base_name = os.path.splitext(os.path.basename(epub_path))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        # Recherche de ebook-convert dans le PATH et dans les emplacements courants de Calibre
        ebook_convert = shutil.which("ebook-convert")
        if not ebook_convert:
            # Chemins possibles pour Calibre sur différents systèmes d'exploitation
            possible_paths = [
                "/Applications/calibre.app/Contents/MacOS/ebook-convert",  # macOS
                "C:\\Program Files\\Calibre2\\ebook-convert.exe",  # Windows
                "C:\\Program Files (x86)\\Calibre2\\ebook-convert.exe",  # Windows 32-bit sur 64-bit
                "/usr/bin/ebook-convert"  # Linux
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    ebook_convert = path
                    break
        
        if not ebook_convert:
            raise FileNotFoundError("ebook-convert n'a pas été trouvé. Assurez-vous que Calibre est installé et dans le PATH.")
        
        # Commande pour convertir ePub en PDF
        command = [ebook_convert, epub_path, pdf_path]
        
        # Exécuter la commande
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        if os.path.exists(pdf_path):
            return pdf_path
        else:
            print(f"Erreur : Le fichier PDF n'a pas été créé. Sortie de Calibre : {result.stdout}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la conversion : {e}")
        print(f"Sortie d'erreur de Calibre : {e.stderr}")
        return None
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {e}")
        return None
