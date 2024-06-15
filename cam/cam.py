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
import subprocess
from dotenv import load_dotenv
from database import Database
from api import Api
import threading

try:
  from smbus2 import SMBus
  from bmp280 import BMP280
  is_temp_sensor_installed = True
except ImportError:
  is_temp_sensor_installed = False

load_dotenv()

prompt = os.getenv('PROMPT')
query = os.getenv('QUERY')
description_frequency = os.getenv('DESCRIPTION_FREQUENCY')
debug = os.getenv('DEBUG')

class Cam:
  def __init__(self):
    # Set up logging
    self.logger = logging.getLogger('Cam')
    self.logger.setLevel(logging.INFO)
    handler = logging.FileHandler('cam.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)
    self.logger.propagate = False

    self.motion_sensor = MotionSensor()
    self.motion_sensor.start()
    self.time_of_last_motion = datetime.datetime.now() - datetime.timedelta(seconds=999)
    self.is_awaiting_response = False
    self.last_temperature = 0
    self.db = Database('activity.db')

    if is_temp_sensor_installed:
      self.bus = SMBus(1)
      self.bmp280 = BMP280(i2c_dev=self.bus)
      self.log('Temperature sensor initialized')
    else:
      self.log('Temperature sensor not found')

  def capture_still(video_url, self):
    try:
      subprocess.call('cvlc http://192.168.0.150:8160 --video-filter=scene --vout=dummy --scene-format=jpg --scene-ratio=1000000 --scene-prefix=snap --scene-path=./stills --run-time=1 vlc://quit', shell=True)

      image = Image.open('./stills/snap00001.jpg')
      buffer = io.BytesIO()
      image.save(buffer, format='JPEG')
      image_bytes = buffer.getvalue()
      return image_bytes
    except Exception as e:
      self.log(e)
    
  def llm_request(self, image, imageId):
    if image is None:
      return None
    
    files = {
      'image': image
    }
      
    data = {
        'history': prompt,
        'text': f'[img-{imageId}]{query}',
        'grammar': '',
        'imageId': imageId
      }
    
    try:
      self.is_awaiting_response
      self.log('Sending image to LLM')
      response = requests.post(
          'http://192.168.0.131:4000/chat',
          headers=None,
          files=files,
          data=data,
          timeout=15
        )
      self.is_awaiting_response = False
    except requests.exceptions.RequestException as e:
      self.log(e)
      self.is_awaiting_response = False
      return None

    if response.status_code == 200:
      response_json = json.loads(response.text)
      llamaText = response_json['llamaText']
      message = llamaText
      return message
    else:
      self.log(response.text)

  def handle_motion(self):
    self.time_of_last_motion = datetime.datetime.now()

    image = self.capture_still(self)
    imageId = int(datetime.datetime.now().timestamp())
    llm_message = self.llm_request(image, imageId)
    self.db.add_item(datetime.datetime.now(), llm_message)

    if llm_message is not None:
      self.log(llm_message)

  def handle_temperature(self):
    if is_temp_sensor_installed and self.last_temperature != round(self.bmp280.get_temperature()):
      temperature = round(self.bmp280.get_temperature())
      self.log(f'Temperature changed from {self.last_temperature}°C to {temperature}°C')
      self.last_temperature = temperature

  def log(self, message):
    if debug:
      self.logger.info(message)
      
  def start(self):
    while True:
      time.sleep(1)
      self.handle_temperature()
      if self.motion_sensor.motion_detected:
        time_since_last_motion = datetime.datetime.now() - self.time_of_last_motion

        self.log('Motion detected')

        if time_since_last_motion.total_seconds() < int(description_frequency):
          continue

        if self.is_awaiting_response:
          continue

        self.handle_motion()


api = Api()
api_thread = threading.Thread(target=api.start_server)
api_thread.start()

cam = Cam()
cam.start()
