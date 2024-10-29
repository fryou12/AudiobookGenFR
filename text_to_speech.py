# text_to_speech.py

import asyncio
import edge_tts
import os
import logging
import tempfile
import shutil
import re
import json
from utils import sanitize_filename  # Ajout de l'import
from audio_quality_checker import AudioQualityChecker  # Ajout de l'import

# Définition des voix supportées
SUPPORTED_VOICES = {
    1: 'fr-FR-VivienneMultilingualNeural',
    2: 'fr-FR-DeniseNeural',
    3: 'fr-FR-EloiseNeural',
    4: 'fr-FR-RemyMultilingualNeural',
    5: 'fr-FR-HenriNeural'
}

def get_temp_audio_dir():
    """Crée et retourne le chemin vers le dossier audioTemp"""
    # Obtenir le chemin de la racine du projet
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(project_root, 'audioTemp')
    
    # Créer le dossier s'il n'existe pas
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    return temp_dir

async def text_to_speech(text, voice_index=4, rate=0, volume=0, output_file="output.mp3", chapter_title=None):
    chapter_name = os.path.basename(output_file)
    logging.info(f"=== Début de la conversion du chapitre : {chapter_name} ===")
    logging.info(f"Fichier de sortie : {output_file}")
    
    if voice_index not in SUPPORTED_VOICES:
        raise ValueError(f"Voice index '{voice_index}' is not supported. Choose from {list(SUPPORTED_VOICES.keys())}.")
    
    # Utiliser le nouveau dossier temporaire
    temp_dir = get_temp_audio_dir()
    
    # Créer un sous-dossier spécifique pour ce chapitre
    if chapter_title:
        chapter_temp_dir = os.path.join(temp_dir, sanitize_filename(chapter_title))
        if not os.path.exists(chapter_temp_dir):
            os.makedirs(chapter_temp_dir)
    else:
        chapter_temp_dir = temp_dir
    
    # Fichier de suivi des phrases générées
    progress_file = os.path.join(chapter_temp_dir, "progress.json")
    failed_sentences_file = os.path.join(chapter_temp_dir, "failed_sentences.txt")
    
    try:
        # Diviser le texte en phrases
        sentences = re.split(r'(?<=[.!?])\s+', text)
        total_sentences = len(sentences)
        logging.info(f"Nombre total de phrases à convertir : {total_sentences}")
        
        # Charger la progression existante si elle existe
        progress = {}
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            logging.info(f"Progression précédente chargée : {len(progress)} phrases traitées")
        
        # Liste pour suivre les échecs
        failed_sentences = []
        
        # Générer l'audio pour le titre si nécessaire
        if chapter_title:
            title_file = os.path.join(chapter_temp_dir, "title.mp3")
            if not os.path.exists(title_file):
                try:
                    communicate_title = edge_tts.Communicate(
                        chapter_title, 
                        'fr-FR-HenriNeural',
                        rate=f"+{rate}%" if rate >= 0 else f"{rate}%",
                        volume=f"+{volume}%" if volume >= 0 else f"{volume}%"
                    )
                    await communicate_title.save(title_file)
                    logging.info(f"Titre généré avec succès : {chapter_title}")
                except Exception as e:
                    error_msg = f"Erreur lors de la génération du titre : {e}"
                    logging.error(error_msg)
                    failed_sentences.append(("TITLE", chapter_title, str(e)))
                    raise
        
        # Générer l'audio pour chaque phrase
        main_voice = SUPPORTED_VOICES[voice_index]
        rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
        volume_str = f"+{volume}%" if volume >= 0 else f"{volume}%"
        
        quality_checker = AudioQualityChecker()
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                logging.debug(f"Phrase {i+1} vide, ignorée")
                continue
                
            sentence_file = os.path.join(chapter_temp_dir, f"sentence_{i:04d}.mp3")
            
            # Vérifier si la phrase a déjà été générée avec succès
            if str(i) in progress and progress[str(i)] and os.path.exists(sentence_file):
                logging.debug(f"Phrase {i+1}/{total_sentences} déjà générée")
                continue
            
            try:
                logging.info(f"Génération de la phrase {i+1}/{total_sentences}")
                logging.debug(f"Contenu de la phrase : {sentence[:100]}...")  # Log des 100 premiers caractères
                
                # Première tentative avec la voix multilingue
                await generate_audio(sentence, main_voice, rate_str, volume_str, sentence_file)
                
                # Vérifier la qualité en passant le texte original
                quality_result = await quality_checker.check_audio_quality(sentence_file, sentence)
                if quality_result is None:
                    # Le fichier audio n'a pas été généré ou erreur technique
                    logging.info(f"Génération audio échouée pour la phrase {i+1}, nouvelle tentative nécessaire")
                    raise Exception("Échec de la génération audio - nouvelle tentative nécessaire")
                elif not quality_result:
                    # L'audio existe mais est de mauvaise qualité
                    logging.info(f"Qualité insuffisante détectée pour la phrase {i+1}, utilisation de fr-FR-HenriNeural")
                    backup_file = os.path.join(chapter_temp_dir, f"sentence_{i:04d}_backup.mp3")
                    await generate_audio(sentence, 'fr-FR-HenriNeural', rate_str, volume_str, backup_file)
                    shutil.move(backup_file, sentence_file)
                
                progress[str(i)] = True
                
            except Exception as e:
                error_msg = f"Erreur lors de la génération de la phrase {i+1}: {e}"
                logging.error(error_msg)
                progress[str(i)] = False
                failed_sentences.append((i+1, sentence[:100], str(e)))  # Stocke les 100 premiers caractères
                
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress, f)
                
                # Sauvegarder les détails des phrases échouées
                with open(failed_sentences_file, 'a', encoding='utf-8') as f:
                    f.write(f"=== Chapitre : {chapter_name} ===\n")
                    f.write(f"Phrase {i+1}/{total_sentences}\n")
                    f.write(f"Contenu : {sentence}\n")
                    f.write(f"Erreur : {e}\n\n")
                
                raise
        
        # Vérifier que toutes les phrases ont été générées
        missing_sentences = [i for i, status in progress.items() if not status]
        if missing_sentences:
            error_msg = f"Phrases manquantes dans {chapter_name} : {', '.join(missing_sentences)}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        # Résumé de la conversion
        logging.info(f"=== Résumé de la conversion pour {chapter_name} ===")
        logging.info(f"Total des phrases : {total_sentences}")
        logging.info(f"Phrases réussies : {len([s for s in progress.values() if s])}")
        if failed_sentences:
            logging.error(f"Phrases échouées : {len(failed_sentences)}")
            for num, content, error in failed_sentences:
                logging.error(f"- Phrase {num}: {content}... | Erreur: {error}")
        
        # Créer la liste des fichiers à concaténer
        files_to_merge = []
        if chapter_title and os.path.exists(os.path.join(chapter_temp_dir, "title.mp3")):
            files_to_merge.append(os.path.join(chapter_temp_dir, "title.mp3"))
            
        files_to_merge.extend([
            os.path.join(chapter_temp_dir, f"sentence_{i:04d}.mp3")
            for i in range(total_sentences)
            if os.path.exists(os.path.join(chapter_temp_dir, f"sentence_{i:04d}.mp3"))
        ])
        
        # Créer le fichier de concaténation pour ffmpeg
        concat_file = os.path.join(chapter_temp_dir, "concat.txt")
        with open(concat_file, 'w', encoding='utf-8') as f:
            for audio_file in files_to_merge:
                f.write(f"file '{audio_file}'\n")
        
        # Fusionner tous les fichiers
        cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" -c copy "{output_file}"'
        result = os.system(cmd)
        
        if result != 0:
            raise Exception("Erreur lors de la fusion des fichiers audio")
        
        logging.info(f"Audio généré avec succès : {output_file}")
        
        # À la fin de la conversion du chapitre, afficher les statistiques
        stats = quality_checker.get_statistics()
        if stats:
            logging.info("Statistiques de qualité audio du chapitre:")
            logging.info(json.dumps(stats, indent=2))
        
    except Exception as e:
        logging.error(f"=== Échec de la conversion du chapitre {chapter_name} ===")
        logging.error(f"Erreur : {str(e)}")
        raise e
        
    finally:
        # Ne pas supprimer le dossier temp ici, on le fera plus tard
        pass

async def convert_chapters(self, output_dir, voice_index=4, rate=0, volume=0):
    for i, chapitre in enumerate(self.chapitres, start=1):
        if chapitre['content'].strip():
            chapter_name = f"chapitre_{i}.mp3"
            output_file = os.path.join(output_dir, chapter_name)
            await text_to_speech(chapitre['content'], voice_index, rate, volume, output_file)
            print(f"Converted chapter {i}/{len(self.chapitres)}")
        else:
            print(f"Skipping empty chapter {i}")

# Fonction utilitaire pour exécuter des tâches asynchrones
def run_async(coroutine):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

# Nouvelle fonction auxiliaire pour la génération audio
async def generate_audio(text, voice, rate, volume, output_file):
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
        volume=volume
    )
    await communicate.save(output_file)
