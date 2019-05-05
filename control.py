import RPi.GPIO as GPIO
import time
import random
import simpleaudio as sa
from magic import assist

from google.cloud import texttospeech

GPIO.setmode(GPIO.BCM)

PARTY_PIN = 16
ASSISTANT_PIN = 19
SORTING_PIN = 27  # TODO
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

was_sorting = False


def sorting_mode():
    team_name = random.choice(TEAM_NAMES)
    synthesis_input = texttospeech.types.SynthesisInput(text=team_name)
    response = clientT2S.synthesize_speech(synthesis_input, voice, audio_config)
    play_obj = sa.play_buffer(response.audio_content, 1, 2, 22050)
    play_obj.wait_done()

print("Starting the awesome hat control!")

while True:
    if GPIO.input(PARTY_PIN) == GPIO.HIGH:  # Upwards
        print("PARTY MODE")
        # TODO light up LEDs, play music while input is HIGH
        time.sleep(5)
    elif GPIO.input(ASSISTANT_PIN) == GPIO.HIGH:  # Upwards
        print("ASSISTANT MODE")
        # TODO one run of recording, sending, answering (blocking)
        assist()
        time.sleep(5)
    elif GPIO.input(SORTING_PIN) == GPIO.HIGH:  # Upwards
        print("SORTING MODE")
        if was_sorting:
            time.sleep(1)
            continue
        sorting_mode()
        was_sorting = True
        continue
    else:  # No mode is active
        print("No mode active")
        time.sleep(1)
    was_sorting = False

GPIO.cleanup()
