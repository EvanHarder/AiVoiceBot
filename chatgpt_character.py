import time
import keyboard
from rich import print
from assemblyAi_speech_to_text import SpeechToTextManager
from openai_chat import GroqAiManager
from eleven_labs import ElevenLabsManager
from audio_player import AudioManager

A_API_KEY = "7a21f3b6263e48f997ed85961e350216"
ELEVENLABS_VOICE = "Callum" # Replace this with the name of whatever voice you have created on Elevenlabs

# BACKUP_FILE = "ChatHistoryBackup.txt"

elevenlabs_manager = ElevenLabsManager()
speechtotext_manager = SpeechToTextManager(A_API_KEY)
openai_manager = GroqAiManager()
audio_manager = AudioManager()

FIRST_SYSTEM_MESSAGE = {"role": "system", "content": '''
Testing bot for ai chat. be simple and direct
'''}
openai_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)

print("[green]Starting the loop, press F4 to begin")
while True:
    # Wait until user presses "f4" key
    if keyboard.read_key() != "f4":
        time.sleep(0.1)
        continue

    print("[green]User pressed F4 key! Now listening to your microphone:")
    
    # Get question from mic
    mic_result = speechtotext_manager.speechtotext_from_mic()
    
    if mic_result == '':
        print("[red]Did not receive any input from your microphone!")
        continue

    # Send question to groq
    openai_result = openai_manager.chat_with_history(mic_result)

    #11Labs for audio
    elevenlabs_output = elevenlabs_manager.text_to_audio(openai_result, ELEVENLABS_VOICE, False)

    # Play the mp3 file
    audio_manager.play_audio(elevenlabs_output, True, True, True)

    print("[green]\n!!!!!!!\nFINISHED PROCESSING DIALOGUE.\nREADY FOR NEXT INPUT\n!!!!!!!\n")
    
