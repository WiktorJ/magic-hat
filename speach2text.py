from __future__ import division

import json
import re
import sys

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
import requests

import simpleaudio as sa
from google.cloud import texttospeech

# from pygame import mixer  # Load the required library

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
clientT2S = texttospeech.TextToSpeechClient()


class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed + 10 - len(transcript))

        if not result.is_final:
            sys.stdout.write("Question: {}".format(transcript + overwrite_chars + '\r'))
            # print("Question: {}".format(transcript + overwrite_chars + '\r'))
            # link = "http://35.246.158.89:5000/?question={}".format(transcript.replace(' ', '+'))
            # response = requests.get(link).text
            # sys.stdout.write("\n")
            # sys.stdout.write("Answer: {}".format(response + '\r'))
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            message = transcript.replace(' ', '+')
            while message[0] == '+':
                message = message[1:]
            link = "http://35.246.158.89:5000/?question={}".format(transcript.replace(' ', '+'))
            try:
                res = requests.get(link)
                response = res.json()
                print("Question: {}, Answer: {}".format(transcript, response['answers'][0]['span']))
                synthesis_input = texttospeech.types.SynthesisInput(text=response['answers'][0]['span'])

                # Build the voice request, select the language code ("en-US") and the ssml
                # voice gender ("neutral")
                voice = texttospeech.types.VoiceSelectionParams(
                    language_code='en-US',
                    ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)

                # Select the type of audio file you want returned
                audio_config = texttospeech.types.AudioConfig(
                    audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)

                # Perform the text-to-speech request on the text input with the selected
                # voice parameters and audio file type
                response = clientT2S.synthesize_speech(synthesis_input, voice, audio_config)
                with open('output.wav', 'wb') as out:
                    # Write the response to the output file.
                    out.write(response.audio_content)
                    print('Audio content written to file "output.wav"')

                wave_obj = sa.WaveObject.from_wave_file("output.wav")
                play_obj = wave_obj.play()
                play_obj.wait_done()

                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.
                # if re.search(r'\b(exit|quit)\b', transcript, re.I):
                #     print('Exiting..')
                #     break
            except Exception as e:
                print("error {}".format(e))
                print("result {}".format(response.results))
                num_chars_printed = 0


def run(streaming_config, client):
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)
        print("MIC loop")
        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)


def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    while True:
        try:
            run(streaming_config, client)
        except Exception as e:
            print("Main loop exception, restarting... {}".format(e))


if __name__ == '__main__':
    main()
