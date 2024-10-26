# ePub & PDF to Audiobook Converter

## Description

Cette application permet de convertir des fichiers ePub et PDF en livres audio. Elle utilise la technologie de synthèse vocale d'Edge TTS pour créer des fichiers audio à partir du contenu textuel des livres électroniques.

## Fonctionnalités

- Conversion de fichiers ePub et PDF en fichiers audio MP3
- Extraction automatique des chapitres
- Choix de différentes voix en français
- Prévisualisation du texte avant la conversion
- Possibilité de fusionner ou supprimer des chapitres
- Conversion par chapitres avec gestion des erreurs
- Interface graphique conviviale

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

1. Lancez l'application en exécutant `main.py` :
   ```
   python main.py
   ```
2. Sélectionnez le fichier ePub ou PDF à convertir.
3. Choisissez le dossier de sortie pour les fichiers audio.
4. Sélectionnez la voix souhaitée et testez-la si nécessaire.
5. Analysez le document pour extraire les chapitres.
6. Ajustez les chapitres si nécessaire (fusion, suppression).
7. Lancez la conversion.

## Note importante sur l'extraction des chapitres

Si l'application rencontre des difficultés pour extraire correctement les chapitres d'un fichier ePub, vous pouvez utiliser la fonction intégrée de conversion en PDF. Les fichiers PDF sont généralement plus simples à traiter pour notre script, ce qui permet une extraction plus cohérente des chapitres.

Pour convertir un ePub en PDF directement dans l'application :
1. Chargez votre fichier ePub dans l'application
2. Cliquez sur le bouton "Convertir en PDF"
3. Attendez que la conversion soit terminée
4. Un message vous indiquera l'emplacement du fichier PDF créé

Une fois le fichier PDF obtenu, vous pouvez le charger dans notre application pour une meilleure extraction des chapitres.

Note : Cette fonction nécessite que Calibre soit installé sur votre système. Si vous n'avez pas Calibre, vous pouvez le télécharger et l'installer depuis [le site officiel de Calibre](https://calibre-ebook.com/download).

Alternativement, si vous préférez utiliser Calibre directement :
1. Ouvrez Calibre
2. Ajoutez votre fichier ePub à la bibliothèque
3. Sélectionnez le livre et cliquez sur "Convertir les livres"
4. Choisissez "PDF" comme format de sortie
5. Cliquez sur "OK" pour lancer la conversion

## Dépannage

- Si la conversion s'arrête en cours de route, utilisez le bouton "Seconde passe" pour reprendre la conversion des chapitres qui ont échoué.
- En cas d'erreur de quota Microsoft, changez de serveur VPN et réessayez la conversion. Nous recommandons l'utilisation de ProtonVPN, qui est gratuit et fonctionne bien pour cet usage. Voici comment procéder :
  1. Téléchargez et installez ProtonVPN depuis leur site officiel.
  2. Créez un compte gratuit si vous n'en avez pas déjà un.
  3. Connectez-vous à un serveur VPN, de préférence dans un pays différent.
  4. Relancez la conversion dans notre application.
  5. Si l'erreur persiste, essayez de vous connecter à un autre serveur VPN et réessayez.

## Contributions

Les contributions à ce projet sont les bienvenues. N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
