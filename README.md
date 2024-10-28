# ePub & PDF to Audiobook Converter

## Description

Cette application permet de convertir des fichiers ePub et PDF en livres audio. Elle utilise la technologie de synthèse vocale d'Edge TTS pour créer des fichiers audio à partir du contenu textuel des livres électroniques.

## Fonctionnalités

- Conversion de fichiers ePub et PDF en fichiers audio MP3
- Extraction automatique des chapitres
- Choix de différentes voix en français
- Prévisualisation du texte avant la conversion
- Gestion robuste des erreurs avec tentatives multiples
- Interface graphique conviviale
- Nettoyage automatique des fichiers temporaires

## Nouveautés et Améliorations

### Gestion des Limitations de l'API Edge TTS
- Découpage intelligent des phrases pour respecter les limites de l'API gratuite
- Système de retry progressif en cas d'échec (backoff exponentiel)
- Logs détaillés des erreurs de conversion par phrase

### Robustesse
- Sauvegarde de la progression par chapitre
- Reprise possible après interruption
- Gestion des timeouts et des erreurs réseau
- Nettoyage automatique des fichiers temporaires

### Performance
- Traitement optimisé des grands chapitres
- Gestion de la mémoire améliorée
- Temps de pause adaptatifs entre les requêtes

## Prérequis

- Python 3.7 ou supérieur
- Bibliothèques Python : tkinter, edge-tts, beautifulsoup4, PyPDF2, pdfminer.six, pygame

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers source.
2. Installez les dépendances requises :
   ```
   pip install -r requirements.txt
   ```

## Utilisation

1. Lancez l'application :
   ```
   python main.py
   ```
2. Sélectionnez le fichier ePub ou PDF à convertir
3. Choisissez le dossier de sortie
4. Sélectionnez et testez la voix souhaitée
5. Analysez le document
6. Lancez la conversion

## Limitations Connues

- L'API Edge TTS gratuite impose des limites sur la longueur des textes
- Les très longs chapitres sont découpés en sections plus petites
- Certaines requêtes peuvent échouer en cas de surcharge du service
- Un VPN peut être nécessaire en cas de quota dépassé

## Limitations et Artefacts Connus

### Limitations de l'API Edge TTS Gratuite
- Limite sur la longueur des textes
- Quotas de requêtes
- Temps de réponse variables
- Pas de contrôle fin sur la prononciation

### Artefacts de Synthèse Vocale
- **Voix fr-FR-RemyMultilingualNeural (recommandée)**
  - Meilleure qualité générale de synthèse
  - Naturel dans l'intonation
  - MAIS : Confusion occasionnelle de langue due à sa nature multilingue
  - Certaines phrases peuvent être lues avec une prononciation anglaise ou autre
  - Certains mots peuvent être mal interprétés ou incompréhensibles

- **Autres Voix**
  - fr-FR-HenriNeural : Plus stable en français mais moins naturel
  - fr-FR-DeniseNeural : Bonne alternative pour les textes techniques
  - fr-FR-EloiseNeural : Recommandée pour la littérature jeunesse
  - fr-FR-VivienneMultilingualNeural : Similaire à Rémy, mêmes limitations

### Recommandations pour Minimiser les Artefacts
1. **Prétraitement du Texte**
   - Éviter les abréviations complexes
   - Vérifier la ponctuation
   - Simplifier les nombres et dates

2. **Choix de la Voix**
   - Utiliser Rémy pour la littérature générale
   - Basculer sur Henri pour les textes techniques
   - Tester différentes voix sur des extraits problématiques

### Améliorations Futures Prévues
- Localisation précise des phrases problématiques dans le texte
- Interface de test des différentes voix sur des passages spécifiques
- Possibilité de reconvertir uniquement les sections problématiques
- Système de rapport détaillé des erreurs de conversion
- Gestion avancée des cas particuliers de prononciation

## Dépannage

### Erreurs de Conversion
- Le système réessaiera automatiquement avec des délais croissants
- Les logs détaillés sont disponibles pour chaque erreur
- Utilisez un VPN en cas d'erreurs de quota persistantes

### Recommandations VPN
- ProtonVPN (gratuit) est recommandé
- Changez de serveur si les erreurs persistent
- Attendez quelques minutes entre les tentatives

### Fichiers Temporaires
- Les fichiers sont automatiquement nettoyés

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE`.
