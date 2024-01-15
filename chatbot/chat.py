#!/home/doogle/doogle/chatbot/.venv/bin/python3

import threading
from array import array
import queue
import pyaudio
import wave
import requests
from openwakeword.model import Model
import numpy as np
import time
import subprocess
import os
import shutil
import requests
import base64
import time
from functions import run_function
from functions import functions_prompt
from functions import grammar_types
import threading
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
functions_json_file = os.path.join(base_dir, 'functions.json')

CHUNK_SIZE = 1024
BUF_MAX_SIZE = CHUNK_SIZE * 10
RATE = 16000
INPUT_DEVICE_INDEX = 3

is_playing = False
last_response_timestamp = 0
volume_history = np.array([])
is_processing = False

history = "This is a chat between a user and a home assistant called Doogle. Doogle does not pretend. Doogle does not use emojis or emoticons. Doogle can do the following functions: " + functions_prompt() + ". function is none by default"

print(history)

def main():
    stopped = threading.Event()
    q = queue.Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK_SIZE)))

    if os.path.exists('./recording.tmp.wav'):
      os.remove('./recording.tmp.wav')

    if os.path.exists('./recording.wav'):
      os.remove('./recording.wav')

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

def play_audio(input):
  def play():
    if os.path.exists(input):
      subprocess.run(["ffplay", "-nodisp", "-autoexit", input], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
       subprocess.run(["ffplay", "-nodisp", "-autoexit", "-"], input=input, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      
  threading.Thread(target=play).start()

def process_recording(stopped, q):
    global last_response_timestamp
    global history
    global is_playing
    global is_processing

    while True:
        if stopped.wait(timeout=0):
            break
        
        if not os.path.exists('./recording.tmp.wav'):
          continue

        if is_playing:
          continue

        is_processing = True

        files = {
          'audio': open('recording.tmp.wav', 'rb')
        }

        data = {
          'history': history,
          'grammar': grammar_types()
        }

        response = requests.post('http://192.168.1.131:4000/chat', headers=None, files=files, data=data)

        if response.status_code == 200:
          last_response_timestamp = time.time()
        else:
          print('\r' + "\033[31mError:\033[0m " + "Something went wrong")
          if os.path.exists('./recording.tmp.wav'):
            os.remove('./recording.tmp.wav')
          continue

        try:
          response_json = json.loads(response.text)
          llamaText = response_json['llamaText']
          llamaText_json = llamaText
          message = llamaText_json['message']
          sttText = response_json['sttText']
          wavData = response_json['wavData']
          wavDataBytes = base64.b64decode(wavData)

          run_function(llamaText_json['function'])
          
          print('\r' + "\033[32mUser:\033[0m " + sttText)
          print('\r' + "\033[34mDoogle:\033[0m " + message)

          history += "\n\nUser: " + sttText + "\nDoogle: " + message

          is_playing = True
          is_processing = False

          play_audio(wavDataBytes)

          is_playing = False

          if os.path.exists('./recording.tmp.wav'):
            os.remove('./recording.tmp.wav')
          
          stream = wave.open('recording.wav', 'wb')
          stream.setnchannels(1)
          stream.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
          stream.setframerate(RATE)
          stream.close()  
        except:
          print('\r' + "\033[31mError:\033[0m " + "Something went wrong")
          if os.path.exists('./recording.tmp.wav'):
            os.remove('./recording.tmp.wav')
          is_processing = False
          is_playing = False
          continue

def record(stopped, q):
    global last_response_timestamp
    global volume_history
    global is_processing
    global is_playing

    audio = pyaudio.PyAudio()
    mic_stream = audio.open(
      format=pyaudio.paInt16, 
      channels=1, 
      rate=RATE, 
      input=True, 
      frames_per_buffer=CHUNK_SIZE,
      input_device_index=INPUT_DEVICE_INDEX
    )
    
    owwModel = Model(wakeword_models=[os.path.join(base_dir, 'models/hey_doogle.tflite')], inference_framework="tflite")

    stream = wave.open('recording.wav', 'wb')
    stream.setnchannels(1)
    stream.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    stream.setframerate(RATE)
    seconds_silent = 0
    should_record = False
    activated = False
    time_started_recording = 0
    max_volume = 0

    play_audio('start.wav')

    while True:
        if stopped.wait(timeout=0):
            break

        prediction = owwModel.predict(np.frombuffer(mic_stream.read(CHUNK_SIZE), dtype=np.int16))
        model_name = list(owwModel.models.keys())[0]
        score = prediction[model_name]

        chunk = q.get()
        vol = max(chunk)

        volume_history = np.append(volume_history, vol)
        if len(volume_history) > 100:
          volume_history = volume_history[1:]     

        max_volume = max(max_volume, vol)
        base_volume = get_baseline_volume()
        sound_bars = volume_to_bars(vol * 0.7 / max_volume)

        # Check for wake word if not already recording
        if (score >= 0.5 and not should_record):
            # print("Wake word detected")
            play_audio('open.wav')
            activated = True
            should_record = True
    
        # Start recording
        if should_record:
          try:
            stream.writeframes(chunk)
          except:
            pass

        # Set time recording started
        if (should_record):
          if (time_started_recording == 0):
            time_started_recording = time.time()

        # Measure seconds of silence
        if (vol * 0.7 < base_volume):
          seconds_silent += CHUNK_SIZE / RATE
        else:
          seconds_silent = 0

        # Stop recording if silent for 2 seconds
        if (should_record and seconds_silent > 2):
          # print("Stopped recording")
          play_audio('close.wav')
          should_record = False
          seconds_silent = 0
          activated = False
          time_started_recording = 0

          if os.path.exists('./recording.wav'):
            shutil.copy2('./recording.wav', './recording.tmp.wav')

        # Stop recording if 10 seconds have passed since started recording
        if (activated and (time_started_recording + 10 < time.time() and time_started_recording != 0)):
          play_audio('close.wav')
          should_record = False
          seconds_silent = 0
          activated = False
          time_started_recording = 0

          if os.path.exists('./recording.wav'):
            shutil.copy2('./recording.wav', './recording.tmp.wav')

        status = ''

        if should_record:
            status = 'Listening' + ' ' + sound_bars
        else:
          if is_processing:
            status = 'Waiting for reply...'

        print(f'\r{"".ljust(40)}', end='')
        print(f'\r{status}', end='')

def volume_to_bars(vol_percent_increase, scale=30):
  # Convert the volume percentage increase to an integer
  vol_int = int(vol_percent_increase * scale)

  # Create a string of ▓ and ░ characters
  bars = '▓' * vol_int + '░' * (scale - vol_int)

  return bars

def listen(stopped, q):
    stream = pyaudio.PyAudio().open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=1024,
        input_device_index=INPUT_DEVICE_INDEX
    )

    while True:
        if stopped.wait(timeout=0):
            break
        try:
            q.put(array('h', stream.read(CHUNK_SIZE)))
        except queue.Full:
            pass

def get_baseline_volume():
  global volume_history

  data = volume_history
  # Calculate Q1, Q3 and IQR
  Q1 = np.percentile(data, 25)
  Q3 = np.percentile(data, 75)
  IQR = Q3 - Q1

  # Define upper and lower limits for outliers
  upper_limit = Q3 + 1.5 * IQR
  lower_limit = Q1 - 1.5 * IQR

  # Remove outliers
  filtered_data = data[(data >= lower_limit) & (data <= upper_limit)]

  # Calculate mean and standard deviation
  mean = np.mean(filtered_data)

  rounded_mean = round(mean)

  return rounded_mean

if __name__ == '__main__':
    main()