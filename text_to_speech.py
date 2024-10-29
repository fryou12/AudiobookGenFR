# text_to_speech.py

import asyncio
import edge_tts
import os
import logging
# Définition des voix supportées
SUPPORTED_VOICES = {
    1: 'fr-FR-VivienneMultilingualNeural',
    2: 'fr-FR-DeniseNeural',
    3: 'fr-FR-EloiseNeural',
    4: 'fr-FR-RemyMultilingualNeural',
    5: 'fr-FR-HenriNeural'
}

async def text_to_speech(text, voice_index=4, rate=0, volume=0, output_file="output.mp3", max_retries=3, chapter_title=None):
    logging.info(f"Début de la conversion en audio pour le fichier : {output_file}")
    
    if voice_index not in SUPPORTED_VOICES:
        raise ValueError(f"Voice index '{voice_index}' is not supported. Choose from {list(SUPPORTED_VOICES.keys())}.")
    
    main_voice = SUPPORTED_VOICES[voice_index]
    title_voice = 'fr-FR-HenriNeural'
    rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
    volume_str = f"+{volume}%" if volume >= 0 else f"{volume}%"
    
    temp_title_file = "temp_title.mp3"
    temp_content_file = "temp_content.mp3"
    
    try:
        if chapter_title:
            communicate_title = edge_tts.Communicate(chapter_title, title_voice, rate=rate_str, volume=volume_str)
            await communicate_title.save(temp_title_file)
        
        communicate_content = edge_tts.Communicate(text, main_voice, rate=rate_str, volume=volume_str)
        await communicate_content.save(temp_content_file)
        
        if chapter_title:
            os.system(f"ffmpeg -y -i {temp_title_file} -i {temp_content_file} -filter_complex '[0:a][1:a]concat=n=2:v=0:a=1[out]' -map '[out]' '{output_file}'")
        else:
            os.replace(temp_content_file, output_file)
        
        print(f"Audio generated: {output_file}")
    except Exception as e:
        logging.error(f"Error during text-to-speech conversion: {str(e)}")
        raise e
    finally:
        if os.path.exists(temp_title_file):
            os.remove(temp_title_file)
        if os.path.exists(temp_content_file):
            os.remove(temp_content_file)
    
    logging.info(f"Fin de la conversion en audio pour le fichier : {output_file}")

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