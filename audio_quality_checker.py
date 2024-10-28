import librosa
import numpy as np
from sentence_transformers import SentenceTransformer
import whisper
import logging
import json
from datetime import datetime
import os

class AudioQualityChecker:
    def __init__(self, threshold=0.85):
        self.threshold = threshold
        self.model = SentenceTransformer('sentence-transformers/msmarco-MiniLM-L6-cos-v5')
        self.french_reference = self.model.encode("Ceci est une phrase de référence en français.")
        self.whisper_model = whisper.load_model("tiny")
        
        # Configuration des logs pour les scores
        self.setup_logging()
        self.scores_history = []
        
    def setup_logging(self):
        # Créer un logger spécifique pour les scores
        self.quality_logger = logging.getLogger('quality_scores')
        self.quality_logger.setLevel(logging.DEBUG)
        
        # Créer un fichier de log avec la date
        log_filename = f"quality_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.quality_logger.addHandler(handler)

    async def check_audio_quality(self, audio_file_path, sentence_text=None):
        try:
            # Transcription avec Whisper
            result = self.whisper_model.transcribe(audio_file_path, language="fr")
            transcribed_text = result["text"]
            
            # Encoder le texte transcrit
            transcribed_embedding = self.model.encode(transcribed_text)
            
            # Calculer la similarité
            similarity = np.dot(self.french_reference, transcribed_embedding) / (
                np.linalg.norm(self.french_reference) * np.linalg.norm(transcribed_embedding)
            )
            
            # Enregistrer les détails pour analyse
            score_details = {
                'original_text': sentence_text,
                'transcribed_text': transcribed_text,
                'similarity_score': float(similarity),
                'passed_threshold': similarity >= self.threshold,
                'audio_file': os.path.basename(audio_file_path)
            }
            
            self.scores_history.append(score_details)
            
            # Log détaillé
            self.quality_logger.info(json.dumps(score_details, ensure_ascii=False))
            
            if similarity < self.threshold:
                logging.warning(
                    f"Score bas détecté ({similarity:.2f})\n"
                    f"Texte original: {sentence_text}\n"
                    f"Transcription: {transcribed_text}"
                )
            
            return similarity >= self.threshold
            
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la qualité audio: {e}")
            return False
    
    def get_statistics(self):
        """Retourne des statistiques sur les scores analysés"""
        if not self.scores_history:
            return None
            
        scores = [item['similarity_score'] for item in self.scores_history]
        stats = {
            'total_samples': len(scores),
            'average_score': np.mean(scores),
            'median_score': np.median(scores),
            'min_score': np.min(scores),
            'max_score': np.max(scores),
            'failed_checks': sum(1 for item in self.scores_history if not item['passed_threshold']),
            'threshold': self.threshold
        }
        
        return stats
