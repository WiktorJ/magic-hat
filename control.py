import RPi.GPIO as GPIO
import time
import random
import simpleaudio as sa
from magic import assist

from google.cloud import texttospeech

GPIO.setmode(GPIO.BCM)

PARTY_PIN = 16
ASSISTANT_PIN = 26
SORTING_PIN = 19
BUTTON_PIN = 20

TEAM_NAMES = ["Cognition", "Mechatronics", "Control", "Growth", "Middleware"]

GPIO.setup(PARTY_PIN, GPIO.IN)
GPIO.setup(ASSISTANT_PIN, GPIO.IN)
GPIO.setup(SORTING_PIN, GPIO.IN)

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
    wave_obj = sa.WaveObject(response.audio_content, 1, 2, 22050)
    play_obj = wave_obj.play()
    play_obj.wait_done()

def party_mode():
    # TODO light up LEDs
    wave_obj = sa.WaveObject.from_wave_file("/home/pi/party_audio.wav")
    play_obj = wave_obj.play()
    while GPIO.input(PARTY_PIN) == GPIO.LOW:
        time.sleep(0.2)
    play_obj.stop()

print("Starting the awesome hat control!")

while True:
    if GPIO.input(ASSISTANT_PIN) == GPIO.HIGH:  # Upwards
        print("ASSISTANT MODE")
        # one run of recording, sending, answering (blocking)
        assist()
    elif GPIO.input(SORTING_PIN) == GPIO.HIGH:  # Upwards
        print("SORTING MODE")
        if was_sorting:
            time.sleep(0.2)
            continue
        sorting_mode()
        was_sorting = True
        continue
    elif GPIO.input(PARTY_PIN) == GPIO.LOW:  # Upwards
        print("PARTY")
        party_mode()
    else:
        print("No mode active")
        time.sleep(1)
    was_sorting = False

GPIO.cleanup()
