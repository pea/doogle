#!/home/doogle/doogle/chatbot/.venv/bin/python3

import pyaudio
import time
import numpy as np
from openwakeword.model import Model
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
from prompt import prompt
import io
import threading
import queue
import sys

debug = sys.argv[1] == "debug" if len(sys.argv) > 1 else False

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
    self.CHUNK = 1024
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

    wakeword_function_models = []
    for wakeword_function in self.wakeword_functions:
      wakeword_function_models.append(f'./models/{self.wakeword_functions[wakeword_function]["model"]}.tflite')

    wakeword_function_models.append('./models/hey_doogle.tflite')

    self.owwModel = Model(wakeword_models=wakeword_function_models, inference_framework="tflite")

    try:
      self.mic_instance = usb.core.find(idVendor=0x2886, idProduct=0x0018)
      self.Mic_tuning = Tuning(self.mic_instance)
    except Exception as e:
      self.Mic_tuning = None

    self.setup_leds()

    self.change_media_volume(200)

  def stream_callback(self, in_data, frame_count, time_info, status):
    data = np.frombuffer(in_data, dtype=np.int16)
    prediction = self.owwModel.predict(np.frombuffer(data, dtype=np.int16))
    heyDoogleScore = prediction['hey_doogle']

    detected_function_wakeword = False

    function_wakeword_scores = {}

    for wakeword_function in self.wakeword_functions:
      if prediction[self.wakeword_functions[wakeword_function]['model']] > 0.1:
        function_wakeword_scores[wakeword_function] = prediction[self.wakeword_functions[wakeword_function]['model']]
        detected_function_wakeword = True

    if detected_function_wakeword:
      function_wakeword = max(function_wakeword_scores, key=function_wakeword_scores.get)
      run_function(function_wakeword)

    if self.Mic_tuning is not None:
      voice_detected = self.Mic_tuning.is_voice()
    else:
      voice_detected = heyDoogleScore >= 0.5

    if voice_detected:
      self.time_last_voice_detected = time.time()
    else:
      if time.time() - self.time_last_voice_detected > 2:
        if self.recording is not None:
          self.play_audio("sound/close.wav", 100)
          self.handle_recording()
          self.resume_media()
          self.should_record = False
          self.is_recording = False
          self.time_started_recording = 0

    if heyDoogleScore >= 0.1 and not detected_function_wakeword:
      self.should_record = True
      self.time_last_voice_detected = time.time()

    if self.should_record and not self.is_recording:
      self.play_audio("sound/open.wav", 100)
      try:
        pixel_ring.listen()
      except:
        pass

    if self.should_record:
      self.is_recording = True
      
      if self.time_started_recording == 0:
        self.time_started_recording = time.time()

      self.pause_media()
      if self.recording is None:
          self.recording = data
      else:
        self.recording = np.concatenate((self.recording, data))
        try:
          pixel_ring.trace()
        except:
          pass

    if self.is_recording and time.time() - self.time_started_recording > 10:
      self.play_audio("sound/close.wav", 100)
      self.handle_recording()
      self.resume_media()
      self.should_record = False
      self.is_recording = False
      self.time_started_recording = 0

    if self.time_last_response != 0 and time.time() - self.time_last_response > 20 and self.recording is None:
      self.time_last_response = 0
      self.history = prompt()
      self.play_audio("sound/reset.wav", 100)

    return (in_data, pyaudio.paContinue)
  
  def play_audio(self, input, volume=256):
    if os.path.exists(input):
      subprocess.run(["ffplay", "-volume", str(volume), "-nodisp", "-autoexit", input], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
       subprocess.run(["ffplay", "-volume", str(volume), "-nodisp", "-autoexit", "-"], input=input, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
      pixel_ring.set_brightness(1)
      pixel_ring.set_color_palette(self.colour('cyan'), self.colour('black'))
      pixel_ring.trace()

      # def vad_direction():
      #   while self.Mic_tuning is not None:
      #     if self.Mic_tuning.is_voice():
      #       pixel_ring.listen()
      #       pixel_ring.set_color_palette(green, black)
      #     else:
      #       pixel_ring.set_color_palette(teal, black)
      #     time.sleep(0.1)
      
      # threading.Thread(target=vad_direction).start()

  def start_pulse_leds(self):
    if self.Mic_tuning is None:
      return

    def pulse_leds():
      while not self.should_stop_pulsing:
        for i in range(0, 31):
          pixel_ring.mono(0xff9600)
          pixel_ring.set_brightness(i)
          time.sleep(0.01)

        for i in range(31, 0, -1):
          pixel_ring.mono(0xff9600)
          pixel_ring.set_brightness(i)
          time.sleep(0.01)

    self.should_stop_pulsing = False
    self.pulse_leds_thread = threading.Thread(target=pulse_leds)
    self.pulse_leds_thread.start()

  def stop_pulse_leds(self):
    if self.Mic_tuning is None:
      return
    
    self.should_stop_pulsing = True
    if self.pulse_leds_thread is not None:
        self.pulse_leds_thread.join()  # Wait for the thread to finish
    self.setup_leds()
  
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
  
  def llm_request(self, recording=None, text=None):
    if recording is not None and text is not None:
      return

    # self.start_pulse_leds()
    try:
      pixel_ring.spin()
    except:
      pass

    if recording is not None:
      recording_wav = self.frames_to_wav(recording, pyaudio.get_sample_size(pyaudio.paInt16), 1, 16000)
      files = {
        'audio': recording_wav
      }

      userStt = self.sst(recording_wav)
      new_prompt = prompt(userText=userStt)

      data = {
        'history': new_prompt,
        'grammar': grammar_types()
      }

      if debug:
        print(data)

      response = requests.post(
        'http://192.168.1.131:4000/chat',
        headers=None,
        files=files,
        data=data
      )

      self.recording = None
      self.time_last_response = time.time()

    if text is not None:
      data = {
        'text': text,
        'history': prompt(),
        'grammar': grammar_types()
      }

      if debug:
        print(data)

      response = requests.post(
        'http://192.168.1.131:4000/chat',
        headers=None,
        json=data
      )

    # self.stop_pulse_leds()
    try:
      pixel_ring.trace()
    except:
      pass
    
    if response.status_code != 200:
      self.tts("There was an error with a request. " + response.text)

    try:
      response_json = json.loads(response.text)

      if debug:
        debug_response = response_json
        debug_response['wavData'] = "WAV DATA"
        print(debug_response)

      llamaText = response_json['llamaText']
      llamaText_json = llamaText
      message = llamaText_json['message']
      sttText = response_json['sttText']
      wavData = response_json['wavData']
      function = llamaText_json['function']
      option = llamaText_json['option']
      wavDataBytes = base64.b64decode(wavData)
    except Exception as e:
      self.tts("There was an error with a request. " + str(e))
      print(e)
      return
    
    return (message, sttText, wavDataBytes, function, option)
  
  def handle_function(self, function, option):
    run_function(function, option)

    function_response = None

    if function_response is None:
      return

    llm_response = self.llm_request(
      text="The response from the " + function + " function is: " + str(function_response) + ". Please inform me of it in plain English."
    )

    message, sttText, wavDataBytes, function = llm_response

    self.history += "\n\nUser: " + sttText + "\nDoogle: " + message
    self.pause_media()
    self.play_audio(wavDataBytes)
    self.resume_media()
  
  def handle_recording(self):
    if self.recording is None:
      return
  
    llm_response = self.llm_request(recording=self.recording)

    if llm_response is None:
      return
    
    message, sttText, wavDataBytes, function, option = llm_response

    self.history += "\n\nUser: " + sttText + "\nDoogle: " + message


    if function != "None" and function != "none":
      functionObj = get_function(function)
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
      self.resume_media()
  
  def change_media_volume(self, volume):
    subprocess.run("echo 'volume " + str(volume) + "' > /dev/tcp/localhost/12345", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, executable="/bin/bash")
    subprocess.run("echo 'volume " + str(volume) + "' | nc localhost 12345", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

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
    
    response = requests.post('http://192.168.1.131:4000/tts', headers=None, json=data)
    
    if response.status_code != 200:
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

    response = requests.post('http://192.168.1.131:6060/inference', headers=None, files=files)

    if response.status_code != 200:
      self.tts(response.text)
      return
    
    return response.text

  def start(self):
    self.stream = self.p.open(
      format=pyaudio.paInt16,
      channels=1,
      rate=self.RATE,
      input=True,
      input_device_index=self.find_microphone_index("ReSpeaker"),
      frames_per_buffer=self.CHUNK,
      stream_callback=self.stream_callback
    )
    self.stream.start_stream()
    self.play_audio("sound/start.wav", 100)

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

chatbot = ChatBot()
chatbot.start()

while chatbot.stream.is_active():
  time.sleep(0.1)

chatbot.stop()
