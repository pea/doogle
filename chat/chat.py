#!/home/doogle/doogle/chatbot/.venv/bin/python3

import pyaudio
import time
import numpy as np
import usb.core
import usb.util
import wave
import subprocess
import os
import threading
import requests
import json
import base64
from functions import run_function
from functions import grammar_types
from functions import get_function
from functions import get_functions_by_type
from functions import trigger_words_detected
from prompt import prompt
import io
import logging
import re
from dotenv import load_dotenv
from wakeword.openwakeword.openwakeword import OpenWakeWord
from wakeword.porcupine.porcupine import Porcupine
from amplifier import Amplifier
from rotary_encoder import RotaryEncoder
import threading
from pydub import AudioSegment

load_dotenv()

debug = os.getenv("DOOGLE_DEBUG")
doogle_server_host = os.getenv("DOOGLE_SERVER_HOST")
api_server_host = os.getenv("API_SERVER_HOST")
sst_server_host = os.getenv("STT_SERVER_HOST")
wakeword_library = os.getenv("WAKEWORD_LIBRARY")
porcupine_access_key = os.getenv("PORCUPINE_ACCESS_KEY")
conversation_mode = os.getenv("CONVERSATION_MODE")

try:
    import RPi.GPIO as GPIO
    from respeaker.pixel_ring.pixel_ring import pixel_ring
    from respeaker.tuning import Tuning
except ImportError:
    GPIO = None
    pixel_ring = None
    Tuning = None


class ChatBot:
    def __init__(self):
        logging.basicConfig(
            filename="chat.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

        self.CHUNK = 1020
        self.RATE = 16000
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recording = None
        self.time_last_voice_detected = 0
        self.time_started_recording = 0
        self.should_record = False
        self.is_recording = False
        self.history = prompt()
        self.media_paused = False
        self.should_pulse_leds = False
        self.time_last_response = 0
        self.should_stop_pulsing = False
        self.pulse_leds_thread = None
        self.wakeword_functions = get_functions_by_type("wakeword")
        self.is_playing_audio = False
        self.is_playing_audio_lock = threading.Lock()
        self.led_mode = None
        self.seconds_wait_speak = 2
        self.current_volume = 0
        self.prev_volume = 80
        self.is_button_pressed = False

        self.rotary_encoder = RotaryEncoder(
            button_callback=lambda: self.handle_button_press(),
            long_press_callback=lambda: self.stop_media(),
            rotation_callback=lambda rotation: self.set_volume(
                self.current_volume + (rotation * 5)
            ),
        )

        if GPIO is not None:
            GPIO.setmode(GPIO.BCM)

        if wakeword_library == "porcupine":
            self.wakeword = Porcupine(porcupine_access_key)
        else:
            self.wakeword = OpenWakeWord()

        self.set_volume(80, False)

        try:
            self.mic_instance = usb.core.find(idVendor=0x2886, idProduct=0x0018)
            self.Mic_tuning = Tuning(self.mic_instance)
            # self.Mic_tuning.write('GAMMAVAD_SR', 30.0)
            # self.Mic_tuning.write('AGCONOFF', 0)
            # self.Mic_tuning.write('AGCMAXGAIN', 51.600000381469727)
            # self.Mic_tuning.write('AGCGAIN', 4.125182945281267)
            # self.Mic_tuning.write('AGCTIME', 0.1)
            # self.Mic_tuning.write('AGCDESIREDLEVEL', 10)

            self.log(
                f"""
      GAMMAVAD_SR: {self.Mic_tuning.read("GAMMAVAD_SR")}
      AGCONOFF: {self.Mic_tuning.read("AGCONOFF")}
      AGCMAXGAIN: {self.Mic_tuning.read("AGCMAXGAIN")}
      AGCGAIN: {self.Mic_tuning.read("AGCGAIN")}
      AGCTIME: {self.Mic_tuning.read("AGCTIME")}
      AGCDESIREDLEVEL: {self.Mic_tuning.read("AGCDESIREDLEVEL")}
      AGCMAXGAIN: {self.Mic_tuning.read("AGCMAXGAIN")}
      """
            )

        except ImportError:
            self.Mic_tuning = None

        self.setup_leds()

    # Channel 0: processed audio for ASR
    # Channel 1: mic1 raw data
    # Channel 2: mic2 raw data
    # Channel 3: mic3 raw data
    # Channel 4: mic4 raw data
    # Channel 5: merged playback data
    def extract_channel(self, data, channel):
        new_data = np.frombuffer(data, dtype=np.int16)
        data_np = np.reshape(new_data, (-1, 6))  # Corrected line
        # data_channel_0/1/2/3/4/5 = np.ascontiguousarray(data_np[:, 0/1/2/3/4/5])
        data_channel = np.ascontiguousarray(data_np[:, channel])
        return data_channel

    def stream_callback(self, in_data, frame_count, time_info, status):
        """
        Callback function for audio stream processing.

        Args:
            in_data (bytes): The input audio data.
            frame_count (int): The number of frames.
            time_info (dict): A dictionary containing timing information.
            status (int): The status flag.

        Returns:
            tuple: A tuple containing the output data and a flag indicating whether to continue streaming.
        """
        data = self.extract_channel(in_data, 1)

        # If Doogle is speaking or some other audio is playing, don't record audio
        if self.is_audio_playing():
            self.log("Audio is playing, not recording")
            return (None, pyaudio.paContinue)

        detected_wakewords = self.wakeword.detected(data)

        detected_function_wakewords = (
            filter(lambda wakeword: wakeword != "hey_doogle", detected_wakewords)
            if len(detected_wakewords) > 1
            else []
        )
        is_detected_function_wakeword = len(detected_function_wakewords) > 0
        is_detected_heydoogle_wakeword = (
            "hey_doogle" in detected_wakewords and len(detected_wakewords) == 1
        )

        if self.is_button_pressed == True:
            self.prev_volume = self.current_volume
            detected_wakewords = ["hey_doogle"]
            is_detected_heydoogle_wakeword = True
            self.is_button_pressed = False

        if is_detected_function_wakeword:
            function_wakeword = detected_function_wakewords[0]
            run_function(function_wakeword)

        if self.voice_detected():
            voice_detected = True
        else:
            voice_detected = False

        if voice_detected:
            self.time_last_voice_detected = time.time()
            self.log(f"Voice detected")
        else:
            if time.time() - self.time_last_voice_detected > self.seconds_wait_speak:
                if self.recording is not None and self.is_recording:
                    self.log(
                        f"Voice not detected for {self.seconds_wait_speak} seconds while recording, stopping recording"
                    )
                    self.play_audio("sound/close.wav", 70)
                    self.reset_leds()
                    threading.Thread(target=self.handle_recording).start()
                    self.resume_media()
                    self.should_record = False
                    self.is_recording = False
                    self.time_started_recording = 0

        if is_detected_heydoogle_wakeword:
            self.should_record = True
            self.time_last_voice_detected = time.time()
            self.seconds_wait_speak = 3
            self.log(f"Hey Doogle wakeword detected")

        if self.should_record:
            if not self.is_recording:
                self.pause_media()
                self.play_audio("sound/open.wav", 70)
                self.listen_leds()

            self.is_recording = True
            self.log(f"Recording in progress")

            if self.time_started_recording == 0:
                self.time_started_recording = time.time()

            if self.recording is None:
                self.recording = data
            else:
                self.recording = np.concatenate((self.recording, data))

        if self.is_recording and time.time() - self.time_started_recording > 10:
            self.log(f"User spoke for over 10 seconds, stopping recording")
            self.play_audio("sound/close.wav", 70)
            threading.Thread(target=self.handle_recording).start()
            self.resume_media()
            self.should_record = False
            self.is_recording = False
            self.time_started_recording = 0
            self.reset_leds()

        if (
            self.time_last_response != 0
            and time.time() - self.time_last_response > 20
            and not self.is_recording
        ):
            self.log(f"No response for 20 seconds, resetting history")
            self.time_last_response = 0
            self.history = prompt()
            self.play_audio("sound/reset.wav", 70)
            self.reset_leds()

        return (in_data, pyaudio.paContinue)

    def set_volume(self, volume, audio_confirmation=True):
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100

        if volume != self.current_volume:
            subprocess.call(["amixer", "set", "Master", "--", str(volume) + "%"])
            if audio_confirmation:
                self.play_audio("sound/volume_check.wav", 50)
            self.current_volume = volume

    def get_audio_file_duration(self, input_abs_path):
        """
        Get the duration of an audio file.

        Args:
            input_abs_path (str): The absolute path to the audio file.

        Returns:
            float: The duration of the audio file in seconds.
        """
        audio = AudioSegment.from_file(input_abs_path)
        return len(audio) / 1000.0  # Duration in seconds

    def get_audio_bytes_duration(self, data):
        with wave.open(io.BytesIO(data), "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate)
            return duration

    def set_playing_audio_for_duration(self, duration):
        with self.is_playing_audio_lock:
            self.is_playing_audio = True
        threading.Thread(
            target=self._reset_playing_audio_after_delay, args=(duration,)
        ).start()

    def _reset_playing_audio_after_delay(self, duration):
        time.sleep(duration)
        with self.is_playing_audio_lock:
            self.is_playing_audio = False

    def is_audio_playing(self):
        with self.is_playing_audio_lock:
            return self.is_playing_audio

    def play_audio(self, input, volume=100):
        if os.path.exists(input):
            input_abs_path = os.path.abspath(input)
            duration = self.get_audio_file_duration(input_abs_path)

            input_with_silent = os.path.join(
                "sound/with_silent", os.path.basename(input)
            )


            if os.path.exists(input_with_silent):
                input_with_silent_abs_path = os.path.abspath(input_with_silent)
                input = input_with_silent
                duration = self.get_audio_file_duration(input_with_silent_abs_path)

            threading.Thread(
                target=lambda: subprocess.run(
                    ["ffplay", "-volume", str(volume), "-nodisp", "-autoexit", input],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ).start()
        else:
            duration = self.get_audio_bytes_duration(input)
            threading.Thread(
                target=lambda: subprocess.run(
                    ["ffplay", "-volume", str(volume), "-nodisp", "-autoexit", "-"],
                    input=input,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ).start()

        self.log(f"Playing audio for {duration} seconds")
        self.set_playing_audio_for_duration(duration)

    def find_microphone_index(self, partial_name):
        pi = pyaudio.PyAudio()
        info = pi.get_host_api_info_by_index(0)
        numdevices = info.get("deviceCount")
        for i in range(0, numdevices):
            if (
                pi.get_device_info_by_host_api_device_index(0, i).get(
                    "maxInputChannels"
                )
            ) > 0:
                device_name = pi.get_device_info_by_host_api_device_index(0, i).get(
                    "name"
                )
                if partial_name in device_name:
                    return i
        return None

    def voice_direction(self):
        return self.Mic_tuning.direction

    def voice_detected(self):
        return self.Mic_tuning.is_voice()

    def setup_leds(self):
        if self.Mic_tuning is not None:
            en_pin = 12
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(en_pin, GPIO.OUT)
            GPIO.output(en_pin, GPIO.LOW)
            pixel_ring.set_brightness(2)
            pixel_ring.set_color_palette(self.colour("cyan"), self.colour("black"))
            pixel_ring.trace()
            self.led_mode = "trace"

    def colour_leds(self, colour):
        try:
            pixel_ring.set_color_palette(self.colour(colour), self.colour("black"))
        except:
            pass

    def reset_leds(self):
        try:
            if self.led_mode is not "trace":
                threading.Thread(target=pixel_ring.trace).start()
                self.led_mode = "trace"
                self.colour_leds("cyan")
        except:
            pass

    def listen_leds(self):
        try:
            if self.led_mode is not "listen":
                threading.Thread(target=pixel_ring.spin).start()
                self.led_mode = "listen"
        except:
            pass

    def loading_leds(self):
        try:
            if self.led_mode is not "speak":
                threading.Thread(target=pixel_ring.speak).start()
                self.led_mode = "speak"
        except:
            pass

    def stop_leds(self):
        try:
            if self.led_mode is not "off":
                threading.Thread(target=pixel_ring.off).start()
                self.led_mode = "off"
        except:
            pass

    def frames_to_wav(self, frames, sample_width, channels, sample_rate):
        wav_io = io.BytesIO()

        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setsampwidth(sample_width)
            wav_file.setnchannels(channels)
            wav_file.setframerate(sample_rate)

            for frame in frames:
                wav_file.writeframes(frame)

        wav_data = wav_io.getvalue()

        return wav_data

    def trim_stt(self, text):
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\(.+?\)", "", text)
        text = text.replace("\n", "")
        text = text.strip()
        return text

    def llm_request(self, recording=None, text=None):
        if recording is not None and text is not None:
            self.log("No audio or text provided")
            self.reset_leds()
            self.time_last_response = time.time()
            return

        if recording is not None:
            self.loading_leds()

            recording_wav = self.frames_to_wav(
                recording, pyaudio.get_sample_size(pyaudio.paInt16), 1, 16000
            )
            files = {"audio": recording_wav}

            self.colour_leds("yellow")

            userStt = self.sst(recording_wav)

            self.colour_leds("cyan")

            if userStt is None or self.trim_stt(userStt) == "":
                self.stop_leds()
                self.reset_leds()
                self.play_audio("sound/error.wav", 50)
                return

            new_prompt = prompt(userText=userStt, history=self.history)

            self.log(f"History: {self.history}")

            self.log(f"User STT: {userStt}")

            numTriggerWordsDetected = len(trigger_words_detected(userStt))

            self.log(
                f"Trigger words detected: {str(numTriggerWordsDetected)} from text {userStt}"
            )

            if numTriggerWordsDetected > 0:
                grammar = grammar_types()
            else:
                grammar = ""

            data = {"text": userStt, "history": new_prompt, "grammar": grammar}

            self.log(data)

            self.colour_leds("green")

            try:
                response = requests.post(
                    f"http://{api_server_host}/chat",
                    headers=None,
                    json=data,
                    timeout=15,
                )
            except:
                self.log(
                    f"""
        Headers: {response.headers}
        Status code: {response.status_code}
        Body: {response.text}
        Request: {response.request.body}
        """
                )
                self.play_audio("sound/error.wav", 50)

            self.colour_leds("cyan")

            self.recording = None

        if text is not None:
            data = {"text": text, "history": prompt(), "grammar": ""}

            self.log(data)

            self.loading_leds()

            self.colour_leds("purple")

            try:
                response = requests.post(
                    f"http://{api_server_host}/chat",
                    headers=None,
                    json=data,
                    timeout=15,
                )
            except:
                self.log(
                    f"""
        Headers: {response.headers}
        Status code: {response.status_code}
        Body: {response.text}
        Request: {response.request.body}
        """
                )
                self.play_audio("sound/error.wav", 50)

            self.colour_leds("cyan")

        self.reset_leds()

        if response.status_code != 200:
            self.tts("There was an error with a request. " + response.text)
            self.reset_leds()
            self.log(
                f"""
      Headers: {response.headers}
      Status code: {response.status_code}
      Body: {response.text}
      Request: {response.request.body}
      """
            )

        response_json = json.loads(response.text)

        if self.trim_stt(response_json["sttText"]) == "":
            self.stop_leds()
            self.reset_leds()
            self.play_audio("sound/error.wav", 50)
            return

        if debug:
            debug_response = response_json.copy()
            debug_response["wavData"] = "WAV DATA"
            self.log(debug_response)

        llamaText = response_json["llamaText"]

        message = llamaText
        function = "None"
        option = "None"

        try:
            if not isinstance(llamaText, str):
                llamaText_json = llamaText
                message = llamaText_json["message"]
                function = llamaText_json["function"]
                option = llamaText_json["option"]

            sttText = response_json["sttText"]
            wavData = response_json["wavData"]
            wavDataBytes = base64.b64decode(wavData)
        except:
            self.tts("There was an error with a request. " + response.text)
            self.reset_leds()
            self.log(
                f"""
      Headers: {response.headers}
      Status code: {response.status_code}
      Body: {response.text}
      Request: {response.request.body}
      """
            )
            return None

        return (message, sttText, wavDataBytes, function, option)

    def handle_function(self, function, option):
        self.log(f"Running function {function} with option {option}")

        run_function(function, option)

        function_response = None

        if function_response is None:
            return

        llm_response = self.llm_request(
            text="The response from the "
            + function
            + " function is: "
            + str(function_response)
            + ". Please inform me of it in plain English."
        )

        if llm_response is None:
            self.reset_leds()
            return

        message, sttText, wavDataBytes, function = llm_response

        if self.trim_stt(sttText) is not "":
            self.history += "\n\nUser: " + sttText + "\nDoogle: " + message
            self.pause_media()
            self.play_audio(wavDataBytes)
            self.resume_media()

    def start_listening(self):
        if conversation_mode == "true":
            self.should_record = True
            self.seconds_wait_speak = 3
            self.time_last_voice_detected = time.time()
            self.listen_leds()

    def handle_recording(self):
        if self.recording is None:
            self.log("Recording is empty")
            self.time_last_response = time.time()
            self.reset_leds()
            return

        self.time_last_response = 0

        llm_response = self.llm_request(recording=self.recording)

        if llm_response is None:
            self.reset_leds()
            self.log("LLM response is missing")
            self.time_last_response = time.time()
            return

        message, sttText, wavDataBytes, function, option = llm_response

        self.history += "\n\nUser: " + sttText + "\nDoogle: " + message

        if function != "None" and function != "none":
            functionObj = get_function(function)
            self.log(f"Function object: {functionObj}")
            if functionObj["type"] == "command":
                self.handle_function(function, option)
                return
            elif functionObj["type"] == "environment":
                self.pause_media()
                self.play_audio(wavDataBytes)
                self.resume_media()
                return
        else:
            self.pause_media()
            self.play_audio(wavDataBytes)
            self.time_last_response = time.time()
            self.reset_leds()
            self.start_listening()
            self.resume_media()

    def pause_media(self):
        if self.media_paused:
            return

        def pause_media_thread():
            try:
                subprocess.run(
                    "echo 'pause' > /dev/tcp/localhost/12345",
                    shell=True,
                    executable="/bin/bash",
                )
            except:
                pass

        threading.Thread(target=pause_media_thread).start()

        self.media_paused = True

    def resume_media(self):
        if not self.media_paused:
            return

        def resume_media_thread():
            try:
                subprocess.run(
                    "echo 'play' > /dev/tcp/localhost/12345",
                    shell=True,
                    executable="/bin/bash",
                )
            except:
                pass

        threading.Thread(target=resume_media_thread).start()

        self.media_paused = False

    def stop_media(self):
        subprocess.run(["pkill", "vlc"])
        subprocess.run(["pkill", "VLC"])

    def tts(self, text):
        data = {"text": text}

        try:
            response = requests.post(
                f"http://{api_server_host}/tts", headers=None, json=data, timeout=15
            )
        except:
            self.reset_leds()
            self.play_audio("sound/error.wav", 50)
            return

        response_json = response.json()
        wavData = response_json["wavData"]
        wavDataBytes = base64.b64decode(wavData)

        self.pause_media()
        self.play_audio(wavDataBytes)
        self.resume_media()

    def sst(self, wavDataBytes):
        files = {"file": wavDataBytes}

        try:
            response = requests.post(
                f"http://{sst_server_host}/inference",
                headers=None,
                files=files,
                timeout=15,
            )
        except:
            self.reset_leds()
            self.play_audio("sound/error.wav", 50)
            if response.text is not None:
                self.tts(response.text)
            self.log(
                f"""
      Headers: {response.headers}
      Status code: {response.status_code}
      Body: {response.text}
      Request: {response.request.body}
      """
            )
            return

        responseJson = json.loads(response.text)
        text = responseJson["text"]
        return text

    def start(self):
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=6,
            rate=self.RATE,
            input=True,
            input_device_index=self.find_microphone_index("ReSpeaker"),
            frames_per_buffer=self.CHUNK,
            stream_callback=self.stream_callback,
        )
        self.stream.start_stream()
        self.play_audio("sound/start.wav", 70)

    def stop(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def colour(self, name):
        if name == "red":
            return 0xFF0000
        elif name == "green":
            return 0x00FF00
        elif name == "blue":
            return 0x0000FF
        elif name == "yellow":
            return 0xFFFF00
        elif name == "purple":
            return 0xFF00FF
        elif name == "cyan":
            return 0x00FFFF
        elif name == "white":
            return 0xFFFFFF
        else:
            return 0x000000

    def log(self, message):
        if debug:
            logging.info(f"{message}")

            with open("openwakeword.log", "r") as log:
                lines = log.readlines()

            if len(lines) > 1000:
                with open("openwakeword.log", "w") as log:
                    log.writelines(lines[1:])

    def handle_button_press(self):
        self.log(f"Button pressed")
        self.is_button_pressed = True


chatbot = ChatBot()
chatbot.start()

while chatbot.stream.is_active():
    time.sleep(0)

chatbot.stop()
