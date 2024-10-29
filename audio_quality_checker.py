import librosa
import numpy as np
from sentence_transformers import SentenceTransformer
import whisper
import logging
import json
from datetime import datetime
import os
import warnings
import torch

class AudioQualityChecker:
    def __init__(self, threshold=0.85):
        self.threshold = threshold
        self.model = None
        self.french_reference = None
        self.whisper_model = None
        
        # Configuration des logs pour les scores
        self.setup_logging()
        self.scores_history = []
        
        # Désactiver le parallélisme des tokenizers
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

    def initialize_models(self):
        """Initialise les modèles de manière paresseuse"""
        if self.model is None:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", category=FutureWarning)
                
                # Initialiser SentenceTransformer
                self.model = SentenceTransformer('sentence-transformers/msmarco-MiniLM-L6-cos-v5')
                self.french_reference = self.model.encode("Ceci est une phrase de référence en français.")
                
                # Initialiser Whisper avec FP32
                self.whisper_model = whisper.load_model("tiny").cpu()
                self.whisper_model = self.whisper_model.to(torch.float32)

    async def check_audio_quality(self, audio_file_path, sentence_text=None):
        try:
            # Vérifier d'abord si le fichier audio existe et n'est pas vide
            if not os.path.exists(audio_file_path) or os.path.getsize(audio_file_path) == 0:
                logging.warning(f"Fichier audio manquant ou vide: {audio_file_path}")
                return None  # Retourne None pour indiquer un problème de génération
            
            # Initialiser les modèles si nécessaire
            if self.model is None:
                self.initialize_models()
            
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
            return None  # Retourne None en cas d'erreur pour indiquer un problème technique
    
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

    def get_log_dir(self):
        """Crée et retourne le chemin vers le dossier logTemp"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, 'logTemp')
        
        # Créer le dossier s'il n'existe pas
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        return log_dir

    def setup_logging(self):
        """Configure le système de logging pour les scores de qualité"""
        # Créer un logger spécifique pour les scores
        self.quality_logger = logging.getLogger('quality_scores')
        self.quality_logger.setLevel(logging.DEBUG)
        
        # S'assurer que le logger n'a pas déjà des handlers
        if not self.quality_logger.handlers:
            # Utiliser le nouveau dossier pour les logs
            log_dir = self.get_log_dir()
            log_filename = f"quality_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            log_path = os.path.join(log_dir, log_filename)
            
            # Créer un handler pour le fichier de log
            handler = logging.FileHandler(log_path, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            self.quality_logger.addHandler(handler)
