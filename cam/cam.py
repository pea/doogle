#!/home/dooglecam/.venv/bin/python3

from motion_sensor import MotionSensor
import time
import subprocess
import requests
import json
from PIL import Image
import io
import datetime
import logging
import os

if os.path.isfile('cam.log'):
  os.remove('cam.log')

logging.basicConfig(filename='cam.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p')

class Cam:
  def __init__(self):
    self.motion_sensor = MotionSensor()
    self.motion_sensor.start()
    self.history = 'This is Doogle Cam who describes images sent to it via a video stream.'

  def capture_still(video_url):
    subprocess.call('cvlc http://192.168.0.150:8160 --video-filter=scene --vout=dummy --scene-format=jpg --scene-ratio=1000000 --scene-prefix=snap --scene-path=./stills --run-time=1 vlc://quit', shell=True)

    image = Image.open('./stills/snap00001.jpg')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()
    return image_bytes
  
  def llm_request(self, image):
    if image is None:
      return None
    
    files = {
      'image': image
    }
      
    data = {
        'history': 'This is Doogle Cam who describes images sent to it via a video stream.',
        'text': '[img-10]what do you see?',
        'grammar': ''
      }
    
    response = requests.post(
        'http://192.168.0.131:4000/chat',
        headers=None,
        files=files,
        data=data,
        timeout=15
      )

    if response.status_code == 200:
      response_json = json.loads(response.text)
      llamaText = response_json['llamaText']
      message = llamaText
      return message
    else:
      print('Error: ', response.status_code)

  def message_speaker(self, message):
    if message is None:
      return
    
    data = {
      'message': message
    }

    requests.post(
      'http://doogle.local/message',
      headers=None,
      data=data,
      timeout=15
    )

  def start(self):
    while True:
      if self.motion_sensor.motion_detected:
        image = self.capture_still()
        llm_message = self.llm_request(image)

        current_datetime = datetime.datetime.now()
        friendly_time = current_datetime.strftime("%I:%M:%S %p")
        friendly_date = current_datetime.strftime("%A, %B %d, %Y")
        friendly_datetime = f'{friendly_time} on {friendly_date}'

        if llm_message is not None:
          logging.info(llm_message)
          self.history = self.history + '\nUSER: [img-10]whats in this image?\nDOOGLE: At ' + friendly_datetime + ': ' + llm_message
      else:
        print("No motion detected")
      time.sleep(1)

cam = Cam()
cam.start()
