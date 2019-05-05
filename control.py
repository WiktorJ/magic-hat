import RPi.GPIO as GPIO
import time

from google.cloud import texttospeech

GPIO.setmode(GPIO.BCM)

PARTY_PIN = 16
ASSISTANT_PIN = 19
SORTING_PIN = 27 # TODO
BUTTON_PIN = 20

TEAM_NAMES = ["Hardest Hat", "Dialog Revolution"]

GPIO.setup(PARTY_PIN, GPIO.IN)
GPIO.setup(ASSISTANT_PIN, GPIO.IN)
GPIO.setup(SORTING_PIN, GPIO.IN)
GPIO.setup(BUTTON_PIN, GPIO.IN)

clientT2S = texttospeech.TextToSpeechClient()
voice = texttospeech.types.VoiceSelectionParams(
                language_code='en-US',
                ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)
audio_config = texttospeech.types.AudioConfig(
                audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)




def sorting_mode():
    
    synthesis_input = texttospeech.types.SynthesisInput(text=)#TODO
    response = clientT2S.synthesize_speech(synthesis_input, voice, audio_config)
    

while True:
    if GPIO.input(PARTY_PIN) == GPIO.HIGH:  # Upwards
        print("PARTY MODE")
        # TODO light up LEDs, play music while input is HIGH
        time.sleep(5)
    elif GPIO.input(ASSISTANT_PIN) == GPIO.HIGH:  # Upwards
        print("ASSISTANT MODE")
        # TODO one run of recording, sending, answering (blocking)
        time.sleep(5)
    elif GPIO.input(SORTING_PIN) == GPIO.HIGH:  # Upwards
        print("SORTING MODE")
        # TODO say a team name (blocking)
        sorting_mode()
        time.sleep(5)
    else:  # No mode is active
        time.sleep(1)

GPIO.cleanup()
