import subprocess
import requests
import base64
import argparse
import threading
import time

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from amplifier import Amplifier

parser = argparse.ArgumentParser()
parser.add_argument('--time', type=int, default=10)
args = parser.parse_args()

time_in_minutes = args.time
time_in_seconds = round(time_in_minutes * 60)

def tts(text):
  data = {
    'text': text
  }
  
  response = requests.post('http://192.168.0.131:4000/tts', headers=None, json=data, timeout=10)
  
  if response.status_code != 200:
    return
  
  response_json = response.json()
  wavData = response_json['wavData']
  wavDataBytes = base64.b64decode(wavData)

  subprocess.run(["ffplay", "-volume", "256", "-nodisp", "-autoexit", "-"], input=wavDataBytes, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_pause_media():
  amplifier = Amplifier()
  amplifier.unmute()
  try:
    subprocess.run("echo 'pause' > /dev/tcp/localhost/12345", shell=True, executable="/bin/bash")
  except:
    pass
  amplifier.mute()

def play_alert():
  amplifier = Amplifier()
  amplifier.unmute()
  subprocess.run(["ffplay", "-volume", "256", "-nodisp", "-autoexit", 'sound/alarm.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  amplifier.mute()


time_readable = ''
if time_in_minutes >= 1:
  time_readable = f'{time_in_minutes} minute'
  if time_in_minutes > 1:
    time_readable += 's'
else:
  time_readable = f'{time_in_seconds} seconds'

def timer_thread():
  play_pause_media()

  print(f'Starting timer for {time_readable}')
  tts(f'Starting timer for {time_readable}')

  play_pause_media()

  subprocess.run(["sleep", str(time_in_seconds)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  play_pause_media()
  
  play_alert()

  print(f'The {time_readable} timer has finished')
  tts(f'The {time_readable} timer has finished')

  for _ in range(3):
    play_alert()
    time.sleep(1)

  play_pause_media()

thread = threading.Thread(target=timer_thread)
thread.start()
