import threading
from array import array
import queue
import pyaudio
import wave
import requests
from openwakeword.model import Model
import numpy as np
import time
import json
import http.client
import subprocess
import os
import shutil

CHUNK_SIZE = 1024
MIN_VOLUME = 1000
# if the recording thread can't consume fast enough, the listener will start discarding
BUF_MAX_SIZE = CHUNK_SIZE * 10
RATE = 16000

prompt = ""
prompt_lock = threading.Lock()
is_playing = False

def main():

    stopped = threading.Event()
    q = queue.Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK_SIZE)))

    if os.path.exists('./recording2.tmp.wav'):
      os.remove('./recording2.tmp.wav')

    if os.path.exists('./recording2.wav'):
      os.remove('./recording2.wav')

    listen_t = threading.Thread(target=listen, args=(stopped, q))
    listen_t.start()
    record_t = threading.Thread(target=record, args=(stopped, q))
    record_t.start()
    process_recording_t = threading.Thread(target=process_recording, args=(stopped, q))
    process_recording_t.start()

    try:
        while True:
            listen_t.join(0.1)
            record_t.join(0.1)
            process_recording_t.join(0.1)
    except KeyboardInterrupt:
        stopped.set()

    listen_t.join()
    record_t.join()
    process_recording_t.join()

def process_recording(stopped, q):
    while True:
        if stopped.wait(timeout=0):
            break
        
        if not os.path.exists('./recording2.tmp.wav'):
          continue

        if is_playing:
          continue

        # print("Requesting speech to text")
        text = speech_to_text_request()

        text = text.strip()
        text = text.replace("\n", "")  # Remove all new lines
        text = text.replace("[BLANK_AUDIO]", "")  # Remove all occurrences of [BLANK_AUDIO]

        if text == "":
          continue

        llama_response = llama_request(text)
        llama_response_text = concat_llama_response_text(llama_response)
        print(llama_response_text)
        text_to_speech(llama_response_text)

        if os.path.exists('./recording2.tmp.wav'):
          os.remove('./recording2.tmp.wav')
        
        stream = wave.open('recording2.wav', 'wb')
        stream.setnchannels(1)
        stream.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
        stream.setframerate(RATE)
        stream.close()  

def record(stopped, q):
    global prompt

    audio = pyaudio.PyAudio()
    mic_stream = audio.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)

    owwModel = Model(wakeword_models=["../models/hey_doogle.tflite"], inference_framework="tflite")

    stream = wave.open('recording2.wav', 'wb')
    stream.setnchannels(1)
    stream.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    stream.setframerate(RATE)
    seconds_silent = 0
    seconds_non_silent = 0
    should_record = False
    activated = False

    while True:
        if stopped.wait(timeout=0):
            break
        prediction = owwModel.predict(np.frombuffer(mic_stream.read(CHUNK_SIZE), dtype=np.int16))
        model_name = list(owwModel.models.keys())[0]
        score = prediction[model_name]

        if (score >= 0.5 and not should_record):
            print("Wake word detected")
            should_record = True
            activated = True

        chunk = q.get()
        vol = max(chunk)
        
        if (activated and vol >= MIN_VOLUME):
          print("Started recording")
          should_record = True
          
        if should_record:
          try:
            stream.writeframes(chunk)
          except:
            pass

        if (vol < MIN_VOLUME):
          seconds_silent += CHUNK_SIZE / RATE
          seconds_non_silent = 0
        else:
          seconds_silent = 0
          seconds_non_silent += CHUNK_SIZE / RATE

        if (should_record and (seconds_silent > 2 or seconds_non_silent > 10)):
          print("Stopped recording")
          should_record = False
          seconds_silent = 0

          if os.path.exists('./recording2.wav'):
            shutil.copy2('./recording2.wav', './recording2.tmp.wav')

        if (seconds_silent > 60 and activated):
          print("Closing session")
          activated = False
          prompt = ""
          stream = wave.open('recording2.wav', 'wb')
          stream.setnchannels(1)
          stream.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
          stream.setframerate(RATE)
          stream.close() 
          if os.path.exists('./recording2.tmp.wav'):
            os.remove('./recording2.tmp.wav')

def listen(stopped, q):
    stream = pyaudio.PyAudio().open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=1024,
    )

    while True:
        if stopped.wait(timeout=0):
            break
        try:
            q.put(array('h', stream.read(CHUNK_SIZE)))
        except queue.Full:
            pass  # discard


def speech_to_text_request(): 
  url = "http://192.168.1.131:6060/inference"
  files = {"file": open("./recording2.tmp.wav", "rb")}
  data = {
    "temperature": "0.2",
    "response-format": "json"
  }

  response = requests.post(url, files=files, data=data)
  response_json = response.json()
  if 'text' not in response_json:
    return ""
  
  text = response_json['text']
  
  text = text.strip()
  text = text.replace("\n", "")  # Remove all new lines
  text = text.replace("[BLANK_AUDIO]", "")  # Remove all occurrences of [BLANK_AUDIO]

  return text

def display_llama_response(r1):
  data1 = r1.read()  # This will return entire content.
      
  data1_str = data1.decode('utf-8')  # Convert bytes to string
  data_items = data1_str.split('\n\n')  # Split string into items

  for item in data_items:
    if item.startswith('data: '):  # Check if item starts with 'data: '
        json_str = item[6:]  # Remove 'data: ' prefix
        try:
            data = json.loads(json_str)  # Parse JSON
            print(data.get('content'), end='')  # Print content on the same line
        except json.JSONDecodeError:
            print("\nInvalid JSON: ", json_str)
  print()

def concat_llama_response_text(r1):
  global prompt
  data1 = r1.read()  # This will return entire content.
      
  data1_str = data1.decode('utf-8')  # Convert bytes to string
  data_items = data1_str.split('\n\n')  # Split string into items

  text = ""

  for item in data_items:
    if item.startswith('data: '):  # Check if item starts with 'data: '
        json_str = item[6:]  # Remove 'data: ' prefix
        try:
            data = json.loads(json_str)  # Parse JSON
            text += data.get('content')
        except json.JSONDecodeError:
            print("\nInvalid JSON: ", json_str)

  with prompt_lock:
    prompt = prompt + ' Doogle:' + text
  
  return text

def llama_request(text):
  global prompt

  if prompt == '':
    with prompt_lock:
      prompt = 'This is a chat between a user and a home assistant called Doogle. Doogle does not pretend. Doogle does not use emojis or emoticons. User: ' + text + '\nDoogle:'
  else:
    with prompt_lock:
      prompt = prompt + ' User: ' + text + '\nDoogle:'

  print(prompt)

  llama_url = '192.168.1.131:7000'
  llama_headers = {'Accept': 'text/event-stream'}
  llama_data = {
    'stream': True,
    'n_predict': 400,
    'temperature': 0.7,
    'stop': ['</s>', 'Doogle:', 'User:'],
    'repeat_last_n': 256,
    'repeat_penalty': 1.18,
    'top_k': 40,
    'top_p': 0.95,
    'min_p': 0.05,
    'tfs_z': 1,
    'typical_p': 1,
    'presence_penalty': 0,
    'frequency_penalty': 0,
    'mirostat': 0,
    'mirostat_tau': 5,
    'mirostat_eta': 0.1,
    'grammar': '',
    'n_probs': 0,
    'image_data': [],
    'cache_prompt': True,
    'api_key': '',
    'slot_id': -1,
    'prompt': prompt
  }

  llama_data_bytes = json.dumps(llama_data).encode('utf-8')

  conn = http.client.HTTPConnection(llama_url)
  conn.request("POST", "/completion", body=llama_data_bytes, headers=llama_headers)
  return conn.getresponse()

def text_to_speech(text):
  global is_playing
  is_playing = True
  url = 'http://192.168.1.131:5002/api/tts'
  params = {
    'text': text,
    'speaker_id': 'p298',
    'style_wav': '',
    'language_id': ''
  }
  response = requests.get(url, params=params, headers=None, verify=False)

  subprocess.run(["ffplay", "-nodisp", "-autoexit", "-"], input=response.content, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  is_playing = False

if __name__ == '__main__':
    main()
