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



load_dotenv()

debug = os.getenv('DOOGLE_DEBUG')
apihost = os.getenv('API_HOST')
wakeword_library = os.getenv('WAKEWORD_LIBRARY')
porcupine_access_key = os.getenv('PORCUPINE_ACCESS_KEY')
conversation_mode = os.getenv('CONVERSATION_MODE')

if os.path.isfile('chat.log'):
  os.remove('chat.log')

logging.basicConfig(filename='chat.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p')

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
    self.wakeword_functions = get_functions_by_type('wakeword')
    self.should_enable_voice_detection = True
    self.led_mode = None
    self.seconds_wait_speak = 2
    self.current_volume = 0
    self.prev_volume = 80

    if GPIO is not None:
      GPIO.setmode(GPIO.BCM)
      GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    if wakeword_library == 'porcupine':
      self.wakeword = Porcupine(porcupine_access_key)
    else:
      self.wakeword = OpenWakeWord()

    self.set_volume(80)

    try:
      self.mic_instance = usb.core.find(idVendor=0x2886, idProduct=0x0018)
      self.Mic_tuning = Tuning(self.mic_instance)
      # self.Mic_tuning.write('GAMMAVAD_SR', 30.0)
      #self.Mic_tuning.write('AGCONOFF', 0)
      # self.Mic_tuning.write('AGCMAXGAIN', 51.600000381469727)
      #self.Mic_tuning.write('AGCGAIN', 4.125182945281267)
      # self.Mic_tuning.write('AGCTIME', 0.1)
      # self.Mic_tuning.write('AGCDESIREDLEVEL', 10)

      self.log(f"""
      GAMMAVAD_SR: {self.Mic_tuning.read("GAMMAVAD_SR")}
      AGCONOFF: {self.Mic_tuning.read("AGCONOFF")}
      AGCMAXGAIN: {self.Mic_tuning.read("AGCMAXGAIN")}
      AGCGAIN: {self.Mic_tuning.read("AGCGAIN")}
      AGCTIME: {self.Mic_tuning.read("AGCTIME")}
      AGCDESIREDLEVEL: {self.Mic_tuning.read("AGCDESIREDLEVEL")}
      AGCMAXGAIN: {self.Mic_tuning.read("AGCMAXGAIN")}
      """)

    except Exception as e:
      self.Mic_tuning = None

    self.setup_leds()

  def is_button_pressed(self):
        if GPIO is not None:
            return GPIO.input(27)

  def voice_detected(self):
    if (self.should_enable_voice_detection == True):
      return self.Mic_tuning.is_voice()
    else:
      return False

  def stream_callback(self, in_data, frame_count, time_info, status):
    new_data = np.frombuffer(in_data, dtype=np.int16)
    data_np = np.reshape(new_data, (-1, 6))  # Corrected line
    data_channel_0 = np.ascontiguousarray(data_np[:, 0])
    data_channel_1 = np.ascontiguousarray(data_np[:, 1])
    data_channel_2 = np.ascontiguousarray(data_np[:, 2])
    data_channel_3 = np.ascontiguousarray(data_np[:, 3])
    data_channel_4 = np.ascontiguousarray(data_np[:, 4])
    data_channel_5 = np.ascontiguousarray(data_np[:, 5])

    data = data_channel_1

    detected_wakewords = self.wakeword.detected(data)

    detected_function_wakewords = filter(lambda wakeword: wakeword != "hey_doogle", detected_wakewords) if len(detected_wakewords) > 1 else []
    is_detected_function_wakeword = len(detected_function_wakewords) > 0
    is_detected_heydoogle_wakeword = "hey_doogle" in detected_wakewords and len(detected_wakewords) == 1

    if self.is_button_pressed():
      self.prev_volume = self.current_volume
      detected_wakewords = ["hey_doogle"]
      is_detected_heydoogle_wakeword = True

    if is_detected_function_wakeword:
      function_wakeword = detected_function_wakewords[0]
      run_function(function_wakeword)

    # Base voice detection on wakewords rather than VAD
    if detected_wakewords is not None and (len(detected_wakewords) > 0 or is_detected_function_wakeword):
      voice_detected = True
    else:
      voice_detected = False

    # if self.Mic_tuning is not None:
    #   voice_detected = self.voice_detected()
    # else:
    #   if self.should_enable_voice_detection:
    #     voice_detected = is_detected_heydoogle_wakeword
    #   else:
    #     voice_detected = False

    if voice_detected:
      self.time_last_voice_detected = time.time()
      self.log(f'Voice detected')
    else:
      if time.time() - self.time_last_voice_detected > self.seconds_wait_speak:
        if self.recording is not None and self.is_recording:
          self.log(f'Voice not detected for {self.seconds_wait_speak} seconds while recording, stopping recording')
          self.play_audio("sound/close.wav", 70)
          self.reset_leds()
          threading.Thread(target=self.handle_recording).start()
          threading.Thread(target=self.resume_media).start()
          self.should_record = False
          self.is_recording = False
          self.time_started_recording = 0

    if is_detected_heydoogle_wakeword:
      self.should_record = True
      self.time_last_voice_detected = time.time()
      self.seconds_wait_speak = 1.5
      self.log(f'Hey Doogle wakeword detected')

    if self.should_record and not self.is_recording:
      self.play_audio("sound/open.wav", 70)

    if self.should_record:
      self.is_recording = True
      self.log(f'Recording in progress')
      self.listen_leds()
      
      if self.time_started_recording == 0:
        self.time_started_recording = time.time()

      threading.Thread(target=self.pause_media).start()
      if self.recording is None:
          self.recording = data_channel_0
      else:
        self.recording = np.concatenate((self.recording, data_channel_0))

    if self.is_recording and time.time() - self.time_started_recording > 10:
      self.log(f'User spoke for over 10 seconds, stopping recording')
      self.play_audio("sound/close.wav", 70)
      threading.Thread(target=self.handle_recording).start()
      threading.Thread(target=self.resume_media).start()
      self.should_record = False
      self.is_recording = False
      self.time_started_recording = 0
      self.reset_leds()

    if self.time_last_response != 0 and time.time() - self.time_last_response > 20 and not self.is_recording:
      self.log(f'No response for 20 seconds, resetting history')
      self.time_last_response = 0
      self.history = prompt()
      self.play_audio("sound/reset.wav", 70)
      self.reset_leds()

    return (in_data, pyaudio.paContinue)
  
  def set_volume(self, volume):
    if volume != self.current_volume:
      subprocess.call(["amixer", "set", "Master", "--", str(volume)+"%"])
      self.current_volume = volume
  
  def play_audio(self, input, volume=100):
    self.should_enable_voice_detection = False
    if os.path.exists(input):
      subprocess.run(["ffplay", "-volume", str(volume), "-nodisp", "-autoexit", input], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
       subprocess.run(["ffplay", "-volume", str(volume), "-nodisp", "-autoexit", "-"], input=input, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    self.should_enable_voice_detection = True

  def find_microphone_index(self, partial_name):
    pi = pyaudio.PyAudio()
    info = pi.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (pi.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            device_name = pi.get_device_info_by_host_api_device_index(0, i).get('name')
            if partial_name in device_name:
                return i
    return None
  
  def voice_direction(self):
    return self.Mic_tuning.direction
  
  def setup_leds(self):
    if self.Mic_tuning is not None:
      en_pin = 12
      GPIO.setmode(GPIO.BCM)
      GPIO.setup(en_pin, GPIO.OUT)
      GPIO.output(en_pin, GPIO.LOW)
      pixel_ring.set_brightness(2)
      pixel_ring.set_color_palette(self.colour('cyan'), self.colour('black'))
      pixel_ring.trace()
      self.led_mode = "trace"

  def colour_leds(self, colour):
    try:
      pixel_ring.set_color_palette(self.colour(colour), self.colour('black'))
    except:
      pass

  def reset_leds(self):
    try:
      if self.led_mode is not "trace":
        pixel_ring.trace()
        self.led_mode = "trace"
        self.colour_leds("cyan")
    except:
      pass

  def listen_leds(self):
    try:
      if self.led_mode is not "listen":
        pixel_ring.spin()
        self.led_mode = "listen"
    except:
      pass
  
  def loading_leds(self):
    try:
      if self.led_mode is not "speak":
        pixel_ring.speak()
        self.led_mode = "speak"
    except:
      pass

  def stop_leds(self):
    try:
      if self.led_mode is not "off":
        pixel_ring.off()
        self.led_mode = "off"
    except:
      pass

  def frames_to_wav(self, frames, sample_width, channels, sample_rate):
    wav_io = io.BytesIO()

    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setsampwidth(sample_width)
        wav_file.setnchannels(channels)
        wav_file.setframerate(sample_rate)

        for frame in frames:
            wav_file.writeframes(frame)

    wav_data = wav_io.getvalue()

    return wav_data

  def trim_stt(self, text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.+?\)', '', text)
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

      recording_wav = self.frames_to_wav(recording, pyaudio.get_sample_size(pyaudio.paInt16), 1, 16000)
      files = {
        'audio': recording_wav
      }

      self.colour_leds("yellow")

      userStt = self.sst(recording_wav)

      self.colour_leds("cyan")

      if userStt is None or self.trim_stt(userStt) == "":
        self.stop_leds()
        self.reset_leds()
        self.play_audio("sound/error.wav", 50)
        return

      new_prompt = prompt(userText=userStt, history=self.history)

      self.log(f'History: {self.history}')
      
      self.log(f'User STT: {userStt}')

      numTriggerWordsDetected = len(trigger_words_detected(userStt))
      
      self.log(f'Trigger words detected: {str(numTriggerWordsDetected)} from text {userStt}')

      if numTriggerWordsDetected > 0:
        grammar = grammar_types()
      else:
        grammar = ""

      data = {
        'text': userStt,
        'history': new_prompt,
        'grammar': grammar
      }

      self.log(data)

      self.colour_leds("green")

      try:
        response = requests.post(
          f'http://{apihost}:4000/chat',
          headers=None,
          json=data,
          timeout=15
        )
      except:
        self.log(f"""
        Headers: {response.headers}
        Status code: {response.status_code}
        Body: {response.text}
        Request: {response.request.body}
        """)
        self.play_audio("sound/error.wav", 50)

      self.colour_leds("cyan")

      self.recording = None

    if text is not None:
      data = {
        'text': text,
        'history': prompt(),
        'grammar': ''
      }

      self.log(data)

      self.loading_leds()

      self.colour_leds("purple")

      try:
        response = requests.post(
          f'http://{apihost}:4000/chat',
          headers=None,
          json=data,
          timeout=15
        )
      except:
        self.log(f"""
        Headers: {response.headers}
        Status code: {response.status_code}
        Body: {response.text}
        Request: {response.request.body}
        """)
        self.play_audio("sound/error.wav", 50)

      self.colour_leds("cyan")

    self.reset_leds()

    if response.status_code != 200:
      self.tts("There was an error with a request. " + response.text)
      self.reset_leds()
      self.log(f"""
      Headers: {response.headers}
      Status code: {response.status_code}
      Body: {response.text}
      Request: {response.request.body}
      """)

    response_json = json.loads(response.text)

    if (self.trim_stt(response_json['sttText']) == ""):
      self.stop_leds()
      self.reset_leds()
      self.play_audio("sound/error.wav", 50)
      return

    if debug:
      debug_response = response_json.copy()
      debug_response['wavData'] = "WAV DATA"
      self.log(debug_response)

    llamaText = response_json['llamaText']

    message = llamaText
    function = "None"
    option = "None"

    try:
      if not isinstance(llamaText, str):
        llamaText_json = llamaText
        message = llamaText_json['message']
        function = llamaText_json['function']
        option = llamaText_json['option']

      sttText = response_json['sttText']
      wavData = response_json['wavData']
      wavDataBytes = base64.b64decode(wavData)
    except:
      self.tts("There was an error with a request. " + response.text)
      self.reset_leds()
      self.log(f"""
      Headers: {response.headers}
      Status code: {response.status_code}
      Body: {response.text}
      Request: {response.request.body}
      """)
      return None
    
    return (message, sttText, wavDataBytes, function, option)
  
  def handle_function(self, function, option):
    self.log(f'Running function {function} with option {option}')

    run_function(function, option)

    function_response = None

    if function_response is None:
      return

    llm_response = self.llm_request(
      text="The response from the " + function + " function is: " + str(function_response) + ". Please inform me of it in plain English."
    )

    if llm_response is None:
      self.reset_leds()
      return

    message, sttText, wavDataBytes, function = llm_response

    if (self.trim_stt(sttText) is not ""):
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
      self.log(f'Function object: {functionObj}')
      if functionObj['type'] == 'command':
        self.handle_function(function, option)
        return
      elif functionObj['type'] == 'environment':
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

      try:
        subprocess.run("echo 'pause' > /dev/tcp/localhost/12345", shell=True, executable="/bin/bash")
      except:
        pass

      self.media_paused = True
      
  def resume_media(self):
      if not self.media_paused:
        return

      try:
        subprocess.run("echo 'play' > /dev/tcp/localhost/12345", shell=True, executable="/bin/bash")
      except:
        pass
      
      self.media_paused = False

  def tts(self, text):
    data = {
      'text': text
    }
    
    try:
      response = requests.post(
        f'http://{apihost}:4000/tts',
        headers=None,
        json=data,
        timeout=15
      )
    except:
      self.reset_leds()
      self.play_audio("sound/error.wav", 50)
      return
    
    response_json = response.json()
    wavData = response_json['wavData']
    wavDataBytes = base64.b64decode(wavData)

    self.pause_media()
    self.play_audio(wavDataBytes)
    self.resume_media()

  def sst(self, wavDataBytes):
    files = {
      'file': wavDataBytes
    }

    try:
      response = requests.post(
        f'http://{apihost}:6060/inference',
        headers=None,
        files=files,
        timeout=15
      )
    except:
      self.reset_leds()
      self.play_audio("sound/error.wav", 50)
      if response.text is not None:
        self.tts(response.text)
      self.log(f"""
      Headers: {response.headers}
      Status code: {response.status_code}
      Body: {response.text}
      Request: {response.request.body}
      """)
      return

    responseJson = json.loads(response.text)
    text = responseJson['text']
    return text

  def start(self):
    self.stream = self.p.open(
      format=pyaudio.paInt16,
      channels=6,
      rate=self.RATE,
      input=True,
      input_device_index=self.find_microphone_index("ReSpeaker"),
      frames_per_buffer=self.CHUNK,
      stream_callback=self.stream_callback
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
      return 0xff0000
    elif name == "green":
      return 0x00ff00
    elif name == "blue":
      return 0x0000ff
    elif name == "yellow":
      return 0xffff00
    elif name == "purple":
      return 0xff00ff
    elif name == "cyan":
      return 0x00ffff
    elif name == "white":
      return 0xffffff
    else:
      return 0x000000
    
  def log(self, message):
    if debug:
      logging.info(f'{message}')

chatbot = ChatBot()
chatbot.start()

while chatbot.stream.is_active():
  time.sleep(0)

chatbot.stop()
