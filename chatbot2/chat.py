#!/usr/bin/env python3

import pyaudio
import time
import numpy as np
from openwakeword.model import Model
from respeaker.tuning import Tuning
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
from prompt import prompt
import io

class ChatBot:
  def __init__(self):
    self.owwModel = Model(wakeword_models=['./hey_doogle.tflite'], inference_framework="tflite")
    self.CHUNK = 1024
    self.RATE = 16000
    self.p = pyaudio.PyAudio()
    self.stream = None
    self.recording = None
    self.time_last_voice_detected = 0
    self.mic_instance = usb.core.find(idVendor=0x2886, idProduct=0x0018)
    self.Mic_tuning = Tuning(self.mic_instance)
    self.should_record = False
    self.is_recording = False
    self.history = prompt()

  def stream_callback(self, in_data, frame_count, time_info, status):
    data = np.frombuffer(in_data, dtype=np.int16)
    prediction = self.owwModel.predict(np.frombuffer(data, dtype=np.int16))
    model_name = list(self.owwModel.models.keys())[0]
    score = prediction[model_name]

    voice_detected = self.Mic_tuning.is_voice()

    if voice_detected:
      self.time_last_voice_detected = time.time()
    else:
      if time.time() - self.time_last_voice_detected > 2:
        if self.recording is not None:
          self.play_audio("sound/close.wav")
          self.resume_media()
          self.handle_recording()
          self.should_record = False
          self.is_recording = False

    if score >= 0.5:
      self.should_record = True

    if self.should_record and not self.is_recording:
      self.play_audio("sound/open.wav")

    if self.should_record:
      self.is_recording = True
      self.pause_media()
      if self.recording is None:
        self.recording = data
      else:
        self.recording = np.concatenate((self.recording, data))

    return (in_data, pyaudio.paContinue)
  
  def play_audio(self, input):
    def run_subprocess():
      if os.path.exists(input):
        subprocess.run(["ffplay", "-nodisp", "-autoexit", input], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      else:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-"], input=input, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    thread = threading.Thread(target=run_subprocess)
    thread.start()

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

    if recording is not None:
      recording_wav = self.frames_to_wav(recording, pyaudio.get_sample_size(pyaudio.paInt16), 1, 16000)
      files = {
        'audio': recording_wav
      }

      data = {
        'history': self.history,
        'grammar': grammar_types()
      }

      response = requests.post(
        'http://192.168.1.131:4000/chat',
        headers=None,
        files=files,
        data=data
      )

      self.recording = None

    if text is not None:
      data = {
        'text': text,
        'history': self.history,
        'grammar': grammar_types()
      }

      response = requests.post(
        'http://192.168.1.131:4000/chat',
        headers=None,
        json=data
      )

    if response.status_code != 200:
      self.tts("There was an error with a request to the LLM server. " + response.text)

    response_json = json.loads(response.text)
    llamaText = response_json['llamaText']
    llamaText_json = llamaText
    message = llamaText_json['message']
    sttText = response_json['sttText']
    wavData = response_json['wavData']
    function = llamaText_json['function']
    wavDataBytes = base64.b64decode(wavData)
    
    return (message, sttText, wavDataBytes, function)
  
  def handle_function(self, function):
    function_response = run_function(function)

    llm_response = self.llm_request(
      text="The function response is: " + str(function_response) + ". Please inform me of it in plain English."
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
    
    message, sttText, wavDataBytes, function = llm_response

    self.history += "\n\nUser: " + sttText + "\nDoogle: " + message

    if function != "None" and function != "none":
      self.handle_function(function)
      return
    else:
      self.pause_media()
      self.play_audio(wavDataBytes)
      self.resume_media()

  def pause_media(self):
      subprocess.run("echo 'pause' > /dev/tcp/localhost/12345", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, executable="/bin/bash")
      subprocess.run("echo 'pause' | nc localhost 12345", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
      
  def resume_media(self):
      subprocess.run("echo 'play' > /dev/tcp/localhost/12345", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, executable="/bin/bash")
      subprocess.run("echo 'play' | nc localhost 12345", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

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
    self.play_audio("sound/start.wav")

  def stop(self):
    if self.stream is not None:
      self.stream.stop_stream()
      self.stream.close()
    self.p.terminate()

chatbot = ChatBot()
chatbot.start()

while chatbot.stream.is_active():
  time.sleep(0.1)

chatbot.stop()
