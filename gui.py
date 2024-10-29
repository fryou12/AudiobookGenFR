# gui.py

import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import threading
import asyncio
import os
import sys 
import subprocess
from pathlib import Path
from PIL import Image, ImageTk
import logging
from epub_processor import EpubProcessor, PdfProcessor, clean_tmp
from text_to_speech import text_to_speech, SUPPORTED_VOICES
import pygame
from utils import get_filename_without_extension, sanitize_filename, convert_epub_to_pdf, clean_audio_temp, clean_temp_folders
import edge_tts

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EpubToAudioGUI:
    def __init__(self, master):
        self.master = master
        master.title("ePub & PDf to Audiobook Converter")
        
        # Chargement de l'icône
        self.load_icon()

        # Variables de configuration
        self.epub_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.voice_index = tk.StringVar(value="4 - fr-FR-RemyMultilingualNeural")
        self.chapitres = []
        self.stop_requested = False
        self.grid_row = 0
        self.failed_chapters = []  # Pour stocker les chapitres qui ont échoué
        self.preview_button = None  # Ajout de cette ligne

        # Création des widgets
        self.create_widgets()

        # Configuration de la mise en page
        self.configure_layout()

    def load_icon(self):
        icon_path = "ico.ico"
        if os.path.exists(icon_path):
            try:
                icon = Image.open(icon_path)
                photo = ImageTk.PhotoImage(icon)
                self.master.iconphoto(False, photo)
                self.icon_image = photo  # Garder une référence
            except Exception as e:
                logging.error(f"Erreur lors du chargement de l'icône : {e}")
        else:
            logging.warning(f"Fichier d'icône non trouvé : {icon_path}")

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Widgets de sélection de fichier ePub
        self.create_file_selection_widgets()

        # Widgets de sélection du dossier de sortie
        self.create_output_selection_widgets()

        # Widget de sélection de la voix
        self.create_voice_selection_widget()

        # Boutons d'analyse et de prévisualisation
        self.create_analyze_preview_buttons()

        # Détails des chapitres
        self.create_chapter_details_widget()

        # Boutons d'action
        self.create_action_buttons()

        # Barre de progression et statut
        self.create_progress_and_status_widgets()

        # Détails de la conversion
        self.create_conversion_details_widget()

    def create_file_selection_widgets(self):
        ttk.Label(self.main_frame, text="Fichier ePub ou PDF:").grid(row=self.grid_row, column=0, sticky=tk.W, pady=5)
        self.epub_entry = ttk.Entry(self.main_frame, textvariable=self.epub_path)
        self.epub_entry.grid(row=self.grid_row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(self.main_frame, text="Choisir", command=self.choose_epub).grid(row=self.grid_row, column=2, sticky=tk.W, padx=(5,0), pady=5)
        self.grid_row += 1

    def create_output_selection_widgets(self):
        ttk.Label(self.main_frame, text="Dossier de Destination:").grid(row=self.grid_row, column=0, sticky=tk.W, pady=5)
        self.output_entry = ttk.Entry(self.main_frame, textvariable=self.output_path)
        self.output_entry.grid(row=self.grid_row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(self.main_frame, text="Choisir", command=self.choose_output).grid(row=self.grid_row, column=2, sticky=tk.W, padx=(5,0), pady=5)
        self.grid_row += 1

    def create_voice_selection_widget(self):
        voice_frame = ttk.LabelFrame(self.main_frame, text="Sélection de la voix")
        voice_frame.grid(row=self.grid_row, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        self.grid_row += 1

        self.selected_voice = tk.StringVar()
        voice_options = [f"{k} - {v}" for k, v in SUPPORTED_VOICES.items()]
        voice_dropdown = ttk.Combobox(voice_frame, textvariable=self.selected_voice, values=voice_options)
        voice_dropdown.set(voice_options[3] if voice_options else "Aucune voix disponible")
        voice_dropdown.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        test_button = ttk.Button(voice_frame, text="Tester", command=self.test_voice)
        test_button.grid(row=0, column=1, padx=5, pady=5)

        voice_frame.columnconfigure(0, weight=1)

    def create_analyze_preview_buttons(self):
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=self.grid_row, column=0, columnspan=3, pady=10)

        # Bouton "Convertir en PDF"
        self.pdf_conversion_button = ttk.Button(button_frame, text="Convertir en PDF", command=self.convert_to_pdf)
        self.pdf_conversion_button.pack(side=tk.LEFT, padx=(0, 10))  # Ajout d'un padding à droite

        # Bouton "Analyze Document"
        ttk.Button(button_frame, text="Analyser le Document", command=self.analyze_epub_button_clicked).pack(side=tk.LEFT)

        self.grid_row += 1

    def create_chapter_details_widget(self):
        self.chapter_frame = ttk.LabelFrame(self.main_frame, text="Détails des chapitres")
        self.chapter_frame.grid(row=self.grid_row, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
        self.grid_row += 1

        self.chapter_listbox = tk.Listbox(self.chapter_frame, height=10, width=50)
        self.chapter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Ajouter le gestionnaire d'événements
        self.chapter_listbox.bind('<<ListboxSelect>>', self.on_chapter_select)

        scrollbar = ttk.Scrollbar(self.chapter_frame, orient=tk.VERTICAL, command=self.chapter_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chapter_listbox.config(yscrollcommand=scrollbar.set)

    def on_chapter_select(self, event):
        if self.chapter_listbox.curselection():
            self.preview_button.config(state=tk.NORMAL)
        else:
            self.preview_button.config(state=tk.DISABLED)

    def create_action_buttons(self):
        # Création d'un frame pour contenir tous les boutons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=self.grid_row, column=0, columnspan=3, pady=10)

        # Bouton Prévisualiser
        self.preview_button = ttk.Button(
            button_frame, 
            text="Prévisualiser", 
            command=self.preview_chapter,
            state=tk.DISABLED
        )
        self.preview_button.pack(side=tk.LEFT, padx=5)

        # Bouton Convertir
        ttk.Button(
            button_frame, 
            text="Convertir", 
            command=self.start_conversion
        ).pack(side=tk.LEFT, padx=5)

        # Bouton Stop
        self.stop_button = ttk.Button(
            button_frame, 
            text="Stop", 
            command=self.stop_conversion, 
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.grid_row += 1

    def create_progress_and_status_widgets(self):
        self.progress = ttk.Progressbar(self.main_frame, length=300, mode='determinate')
        self.progress.grid(row=self.grid_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=self.grid_row, column=0, columnspan=3, pady=5)
        self.grid_row += 1

    def create_conversion_details_widget(self):
        self.conversion_details = scrolledtext.ScrolledText(self.main_frame, height=10, width=50)
        self.conversion_details.grid(row=self.grid_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.conversion_details.config(state=tk.DISABLED)
        self.grid_row += 1

    def configure_layout(self):
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(8, weight=1)
        for child in self.main_frame.winfo_children():
            child.grid_configure(padx=5)

    def choose_epub(self):
        filename = filedialog.askopenfilename(filetypes=[("ePub & PDF files", "*.pdf *.epub")])
        if filename:
            self.epub_path.set(filename)

    def choose_output(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_path.set(dirname)
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, dirname)

    def analyze_epub_button_clicked(self):
        file_path = self.epub_path.get()
        if not file_path:
            self.status_label.config(text="Please select a file.")
            return

        if file_path.lower().endswith('.epub'):
            processor = EpubProcessor()
            self.chapitres = processor.analyze_epub(file_path)
        elif file_path.lower().endswith('.pdf'):
            processor = PdfProcessor()
            self.chapitres = processor.analyze_pdf(file_path)
        else:
            self.status_label.config(text="Unsupported file type. Please select an EPUB or PDF file.")
            return

        # Filtrer les chapitres vides
        self.chapitres = [chapitre for chapitre in self.chapitres if chapitre.content.strip()]

        logging.info(f"Contenu extrait : {self.chapitres}")
        if not self.chapitres:
            logging.warning("Aucun chapitre détecté.")
        self.display_chapter_details()

    def display_chapter_details(self):
        self.chapter_listbox.delete(0, tk.END)
        total_words = 0
        if self.chapitres is None or len(self.chapitres) == 0:
            self.chapter_listbox.insert(tk.END, "Aucun chapitre trouvé ou chapitres non initialisés")
            self.preview_button.config(state=tk.DISABLED)
            return

        for i, chapitre in enumerate(self.chapitres, 1):
            title = chapitre.title if hasattr(chapitre, 'title') else f"Chapitre {i}"
            content = chapitre.content if hasattr(chapitre, 'content') else ""
            word_count = len(content.split())
            total_words += word_count
            self.chapter_listbox.insert(tk.END, f"{title}: {word_count} mots")
        
        # Activer le bouton de prévisualisation
        self.preview_button.config(state=tk.NORMAL)
        
        logging.info(f"Affichage des détails des chapitres : {len(self.chapitres)} chapitres, {total_words} mots au total")

    def start_conversion(self):
        if not self.chapitres:
            self.status_label.config(text="Veuillez analyser un document avant de convertir.")
            return

        epub_file = self.epub_path.get()
        if not epub_file:
            self.status_label.config(text="Veuillez sélectionner un fichier valide.")
            return

        base_output_dir = self.output_path.get()
        if not base_output_dir:
            self.status_label.config(text="Veuillez sélectionner un dossier de sortie valide.")
            return

        # Créer un sous-dossier avec le nom du fichier
        epub_filename = get_filename_without_extension(epub_file)
        epub_foldername = sanitize_filename(epub_filename)
        output_dir = os.path.join(base_output_dir, epub_foldername)
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Création du dossier de sortie: {output_dir}")
            
            # Vérifier les permissions d'écriture
            test_file = os.path.join(output_dir, "test.txt")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logging.info("Test d'écriture dans le dossier de sortie réussi")
            except Exception as e:
                raise PermissionError(f"Impossible d'écrire dans le dossier de sortie: {e}")
            
        except Exception as e:
            error_msg = f"Erreur lors de la création du dossier de sortie: {e}"
            logging.error(error_msg)
            self.status_label.config(text=error_msg)
            return

        self.status_label.config(text="Conversion en cours... Veuillez patienter.")
        voice_index = int(self.selected_voice.get().split(' - ')[0])
        
        if not self.stop_button.cget("state") == tk.NORMAL:
            self.stop_button.config(state=tk.NORMAL)

        self.conversion_thread = threading.Thread(target=self.run_conversion, args=(output_dir, voice_index))
        self.conversion_thread.start()

    def run_conversion(self, output_dir, voice_index):
        self.master.after(0, self.update_conversion_details, "Début de la conversion...")
        self.master.after(0, self.update_progress, 0)
        try:
            asyncio.run(self.convert_chapters(output_dir, voice_index))
        except Exception as e:
            logging.error(f"Une erreur s'est produite pendant la conversion : {str(e)}")
            self.master.after(0, lambda: self.status_label.config(text="Erreur pendant la conversion. Voir les détails."))
            self.master.after(0, self.update_conversion_details, f"Erreur : {str(e)}")
        finally:
            epub_file = self.epub_path.get()
            if epub_file:
                clean_tmp()  # Appel sans argument
            self.master.after(0, self.conversion_complete)
            self.master.after(0, lambda: self.stop_button.config(state=tk.DISABLED))

    async def convert_chapters(self, output_dir, voice_index):
        total_chapters = len(self.chapitres)
        padding_length = len(str(total_chapters))
        pending_chapters = [(i, chapitre) for i, chapitre in enumerate(self.chapitres, start=1)]
        failed_attempts = {}  # Pour suivre le nombre d'échecs par chapitre
        
        while pending_chapters and not self.stop_requested:
            current_batch = pending_chapters[:]
            pending_chapters = []
            
            for i, chapitre in current_batch:
                if self.stop_requested:
                    break
                    
                if not chapitre.content.strip():
                    self.master.after(0, self.update_conversion_details, f"Chapitre {i} vide, ignoré.")
                    continue
                
                chapter_number = str(i).zfill(padding_length)
                chapter_name = f"chapitre_{chapter_number}.mp3"
                output_file = os.path.join(output_dir, chapter_name)
                
                # Obtenir le nombre d'échecs précédents pour ce chapitre
                attempts = failed_attempts.get(i, 0)
                
                # Calculer le temps de pause en fonction du nombre d'échecs
                pause_time = min(30 * (2 ** attempts), 300)  # Max 5 minutes de pause
                
                if attempts > 0:
                    self.master.after(0, self.update_conversion_details,
                                    f"Tentative #{attempts+1} pour le chapitre {i} après une pause de {pause_time} secondes...")
                    await asyncio.sleep(pause_time)
                
                try:
                    self.master.after(0, self.update_conversion_details,
                                    f"Conversion du chapitre {i}/{total_chapters}...")
                    
                    await text_to_speech(chapitre.content, voice_index=voice_index,
                                       output_file=output_file, chapter_title=chapitre.title)
                    
                    progress = (len([c for c in range(1, total_chapters + 1) if c not in failed_attempts]) / total_chapters) * 100
                    self.master.after(0, self.update_progress, progress)
                    self.master.after(0, self.update_conversion_details,
                                    f"Chapitre {i}/{total_chapters} converti avec succès en tant que {chapter_name}")
                    
                    # Retirer ce chapitre des échecs s'il était présent
                    failed_attempts.pop(i, None)
                    
                    # Petite pause entre les chapitres réussis
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_message = f"Échec de la conversion du chapitre {i} : {str(e)}"
                    logging.error(error_message)
                    self.master.after(0, self.update_conversion_details, error_message)
                    
                    # Incrémenter le compteur d'échecs pour ce chapitre
                    failed_attempts[i] = attempts + 1
                    
                    # Remettre le chapitre dans la file d'attente
                    pending_chapters.append((i, chapitre))
                    
                    self.master.after(0, self.update_conversion_details,
                                    f"Le chapitre {i} sera réessayé plus tard (échec #{attempts+1})")
            
            # Si des chapitres sont toujours en échec, faire une pause plus longue
            if pending_chapters:
                longest_wait = max(failed_attempts.values())
                pause_time = min(30 * (2 ** longest_wait), 300)
                self.master.after(0, self.update_conversion_details,
                                f"Pause de {pause_time} secondes avant de réessayer {len(pending_chapters)} chapitres...")
                await asyncio.sleep(pause_time)
        
        # Rapport final
        if failed_attempts:
            self.master.after(0, self.update_conversion_details,
                             f"\nConversion terminée avec {len(failed_attempts)} chapitres toujours en échec :"
                             f"\nChapitres problématiques : {', '.join(str(i) for i in failed_attempts.keys())}"
                             f"\nNombre de tentatives : {failed_attempts}")
        else:
            self.master.after(0, self.update_conversion_details,
                             "\nTous les chapitres ont été convertis avec succès!")

    def stop_conversion(self):
        self.stop_requested = True
        self.status_label.config(text="Arrêt de la conversion...")
        self.stop_button.config(state=tk.DISABLED)
        
        # Nettoyer les fichiers temporaires
        clean_temp_folders()
        
        self.status_label.config(text="Conversion arrêtée et fichiers temporaires nettoyés.")

    def conversion_complete(self):
        self.status_label.config(text="Conversion complete!")
        self.progress['value'] = 100

    def update_conversion_details(self, message):
        self.conversion_details.config(state=tk.NORMAL)
        self.conversion_details.insert(tk.END, message + "\n")
        self.conversion_details.see(tk.END)
        self.conversion_details.config(state=tk.DISABLED)
        self.master.update()  # Force la mise à jour de l'interface immédiatement

    def update_progress(self, value):
        self.progress['value'] = value
        self.master.update_idletasks()  # Force la mise à jour de l'interface

    def test_voice(self):
        selected_voice = self.selected_voice.get()
        voice_index = int(selected_voice.split(' - ')[0])
        voice_name = SUPPORTED_VOICES[voice_index]
        
        test_text = f"Bonjour, je suis {voice_name}, et cela devrait ressembler à peu près à ceci lorsque je lirai un livre pour vous."
        
        output_file = "test_voice.mp3"
        
        self.status_label.config(text="Génération de l'échantillon vocal...")
        
        async def generate_test_audio():
            try:
                # Utiliser directement edge_tts sans passer par text_to_speech
                communicate = edge_tts.Communicate(
                    test_text,
                    voice_name
                )
                await communicate.save(output_file)
                self.master.after(0, self.play_test_audio, output_file)
                self.master.after(0, lambda: self.status_label.config(text="Test vocal généré avec succès."))
            except Exception as e:
                self.master.after(0, lambda: self.status_label.config(text=f"Erreur lors du test: {str(e)}"))
                logging.error(f"Erreur lors du test vocal: {str(e)}")
        
        def run_test():
            asyncio.run(generate_test_audio())
        
        threading.Thread(target=run_test).start()

    def play_test_audio(self, file_path):
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self.status_label.config(text="Lecture de l'échantillon vocal...")
        
        def check_if_playing():
            if pygame.mixer.music.get_busy():
                self.master.after(100, check_if_playing)
            else:
                pygame.mixer.quit()
                os.remove(file_path)
                self.status_label.config(text="Test terminé.")
        
        check_if_playing()

    def convert_to_pdf(self):
        epub_path = self.epub_path.get()
        if not epub_path or not epub_path.lower().endswith('.epub'):
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier ePub valide.")
            return

        self.status_label.config(text="Conversion en PDF en cours...")
        self.master.update()

        output_dir = os.path.dirname(epub_path)
        pdf_path = convert_epub_to_pdf(epub_path, output_dir)

        if pdf_path:
            self.status_label.config(text="Conversion en PDF terminée.")
            messagebox.showinfo("Succès", f"Le fichier PDF a été créé : {pdf_path}")
            # Mise à jour du champ de sélection du fichier avec le chemin du PDF
            self.epub_path.set(pdf_path)
            self.epub_entry.delete(0, tk.END)
            self.epub_entry.insert(0, pdf_path)
        else:
            self.status_label.config(text="Échec de la conversion en PDF.")
            messagebox.showerror("Erreur", "La conversion en PDF a échoué. Veuillez vérifier les logs pour plus de détails.")

    def preview_chapter(self):
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un chapitre à prévisualiser")
            return

        index = selection[0]
        if index >= len(self.chapitres):
            messagebox.showerror("Erreur", "Chapitre invalide")
            return

        chapitre = self.chapitres[index]
        preview_text = chapitre.content[:500] + "..." if len(chapitre.content) > 500 else chapitre.content
        
        # Créer une fenêtre de prévisualisation
        preview_window = tk.Toplevel(self.master)
        preview_window.title(f"Prévisualisation - {chapitre.title}")
        preview_window.geometry("600x400")

        # Zone de texte avec scrollbar
        text_widget = scrolledtext.ScrolledText(
            preview_window, 
            wrap=tk.WORD, 
            padx=10, 
            pady=10,
            font=("Arial", 11)
        )
        text_widget.pack(expand=True, fill='both', padx=10, pady=10)
        text_widget.insert(tk.END, preview_text)
        text_widget.config(state='disabled')


