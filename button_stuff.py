import RPi.GPIO as GPIO
import time
import random
import simpleaudio as sa
from magic import assist

GPIO.setmode(GPIO.BCM)

BUTTON_PIN = 20

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

clientT2S = texttospeech.TextToSpeechClient()
voice = texttospeech.types.VoiceSelectionParams(
    language_code='en-US',
    ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)
audio_config = texttospeech.types.AudioConfig(
    audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)


while True:
    if GPIO.wait_for_edge(BUTTON_PIN, GPIO.FALLING, timeout=5000):
        print('say sth')
        synthesis_input = texttospeech.types.SynthesisInput(text="smart hat self destruct mode activated. please remove the hat or be fried in 10 9 8 7 6 5 4 3 2 1 boom")
        response = clientT2S.synthesize_speech(synthesis_input, voice, audio_config)
        wave_obj = sa.WaveObject(response.audio_content, 1, 2, 22050)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    else:
        print('no button pressed')
