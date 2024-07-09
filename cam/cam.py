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
import RPi.GPIO as GPIO
import psutil

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
    self.is_fan_on = False
    self.vlc_recording_process = None
    self.currently_recording_video_filename = None
    self.video_recording_start_time = None
    self.time_of_last_temperature_save = datetime.datetime.now() - datetime.timedelta(seconds=999)
    self.time_of_last_system_info_save = datetime.datetime.now() - datetime.timedelta(seconds=999)
    self.recording_process = None

    self.setup_fan()
    self.setup_leds()

    self.test_fan()
    self.test_leds()

    if is_temp_sensor_installed:
      self.bus = SMBus(1)
      self.bmp280 = BMP280(i2c_dev=self.bus)
      self.log('Temperature sensor initialized')
    else:
      self.log('Temperature sensor not found')

  def setup_fan(self):
    GPIO.setup(22, GPIO.OUT)

  def turn_on_fan(self):
    GPIO.output(22, GPIO.HIGH)
    self.is_fan_on = True

  def turn_off_fan(self):
    GPIO.output(22, GPIO.LOW)
    self.is_fan_on = False

  def test_fan(self):
    self.turn_on_fan()
    time.sleep(3)
    self.turn_off_fan()

  def setup_leds(self):
    GPIO.setup(23, GPIO.OUT)

  def turn_on_leds(self):
    GPIO.output(23, GPIO.HIGH)

  def turn_off_leds(self):
    GPIO.output(23, GPIO.LOW)

  def test_leds(self):
    self.turn_on_leds()
    time.sleep(1)
    self.turn_off_leds()

  def log_system_info(self):
    if (datetime.datetime.now() - self.time_of_last_system_info_save).total_seconds() < 60:
      return

    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    raspberry_pi_temperature = self.get_pi_temperature()

    self.db.add_system_info(
      datetime.datetime.now(), 
      cpu_usage,
      ram_usage,
      disk_usage,
      raspberry_pi_temperature
    )

    self.time_of_last_system_info_save = datetime.datetime.now()

  def get_pi_temperature(self):
    process = subprocess.Popen(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    temperature = output.decode()
    temperature = temperature.replace('temp=', '').replace('\'C\n', '')
    return float(temperature)

  def start_recording_video(self):
    # Generate filename based on current datetime
    filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    self.currently_recording_video_filename = f'{filename}.webm'
    rtsp_url = 'rtsp://localhost:8554/stream'
    output_filename = f"./videos/{self.currently_recording_video_filename}"
    
    # Log start of recording
    self.log(f'Starting video recording to {output_filename}')
    self.video_recording_start_time = datetime.datetime.now()

    # Define the recording command with detailed ffmpeg options
    command = f'ffmpeg -rtsp_transport tcp -i {rtsp_url} -c:v libvpx-vp9 -s:v 640x480 -r 25 -b:v 1500k -g 30 -c:a libvorbis -bufsize 3000k -fflags +discardcorrupt -reconnect 1 {output_filename}'

    # Define a function to run the recording command in a subprocess
    def record_video():
        self.recording_process = subprocess.Popen(command, shell=True)

    # Start the recording in a new thread
    self.recording_thread = threading.Thread(target=record_video)
    self.recording_thread.start()

  def stop_recording_video(self):
    if self.recording_process:
        self.recording_process.terminate()
        self.recording_thread.join()
        self.log("Video recording stopped.")

    if self.currently_recording_video_filename is None:
      return

    self.log(f'Saving video {self.currently_recording_video_filename} with duration 0.0 seconds')

    self.db.add_video(self.video_recording_start_time, f'{self.currently_recording_video_filename}', 0.0)

    self.currently_recording_video_filename = None

  def capture_still(video_url, self):
    try:
      if os.path.exists('./stills/snapshot.jpg'):
        os.remove('./stills/snapshot.jpg')

      subprocess.call('ffmpeg -i rtsp://localhost:8554/stream -vframes 1 -q:v 2 ./stills/snapshot.jpg', shell=True)

      image = Image.open('./stills/snapshot.jpg')
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
    self.start_recording_video()
    imageId = int(datetime.datetime.now().timestamp())
    llm_message = self.llm_request(image, imageId)
    if llm_message is not None:
      self.db.add_activity(datetime.datetime.now(), llm_message)

    if llm_message is not None:
      self.log(llm_message)

  def handle_motion_end(self):
    self.turn_off_leds()
    self.stop_recording_video()
    self.log('Motion ended')

  def handle_temperature(self):
    if (datetime.datetime.now() - self.time_of_last_temperature_save).total_seconds() > 60:
      self.db.add_temperature(
        datetime.datetime.now(),
        round(self.bmp280.get_temperature(), 2),
        'on' if self.is_fan_on else 'off'
      )
      self.time_of_last_temperature_save = datetime.datetime.now()

    if is_temp_sensor_installed and self.last_temperature != round(self.bmp280.get_temperature()):
      temperature = round(self.bmp280.get_temperature())

      if self.get_pi_temperature() >= 70:
        self.turn_on_fan()

      if self.get_pi_temperature() < 60:
        self.turn_off_fan()

      self.log(f'Temperature changed from {self.last_temperature}°C to {temperature}°C')
      self.last_temperature = temperature

  def log(self, message):
    if debug:
      self.logger.info(message)
      
  def start(self):
    while True:
      time.sleep(1)
      self.handle_temperature()
      self.log_system_info()

      secs_since_last_motion = (datetime.datetime.now() - self.time_of_last_motion).total_seconds()

      if secs_since_last_motion > 10:
        self.handle_motion_end()

      if self.motion_sensor.motion_detected:
        self.turn_on_leds()
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