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
import psutil
from ir_leds import ir_leds
from mediamtx_yml_updater import MediaMatrixUpdater

load_dotenv()

prompt = os.getenv('PROMPT')
query = os.getenv('QUERY')
description_frequency = os.getenv('DESCRIPTION_FREQUENCY')
debug = os.getenv('DEBUG')
doogle_server_host = os.getenv('DOOGLE_SERVER_HOST')

class Cam:
  def __init__(self):
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
    self.vlc_recording_process = None
    self.currently_recording_video_filename = None
    self.video_recording_start_time = None
    self.time_of_last_temperature_save = datetime.datetime.now() - datetime.timedelta(seconds=999)
    self.time_of_last_system_info_save = datetime.datetime.now() - datetime.timedelta(seconds=999)
    self.recording_process = None
    self.uptime = datetime.datetime.now()
    self.is_recording_video = False
    self.is_capture_still = False

    self.start_streaming_server()

    self.ir_leds = ir_leds()
    self.ir_leds.test_leds()

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
    if self.is_recording_video:
      return

    self.is_recording_video = True
    filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    self.currently_recording_video_filename = f'{filename}.webm'
    rtsp_url = 'rtsp://localhost:8554/stream'
    output_filename = f"./videos/{self.currently_recording_video_filename}"
    
    self.log(f'Starting video recording to {output_filename}')
    self.video_recording_start_time = datetime.datetime.now()

    command = f'ffmpeg -rtsp_transport tcp -i {rtsp_url} -c:v libvpx-vp9 -s:v 640x480 -r 15 -b:v 1500k -g 30 -c:a libvorbis -bufsize 3000k -preset ultrafast -crf 30 -fflags +discardcorrupt -reconnect 1 {output_filename}'

    def record_video():
        self.recording_process = subprocess.Popen(command, shell=True)

    self.recording_thread = threading.Thread(target=record_video)
    self.recording_thread.start()

  def stop_recording_video(self):
    if self.recording_process:
        self.recording_process.terminate()
        self.recording_thread.join()

    if self.currently_recording_video_filename is None:
      return

    self.log(f'Saving video {self.currently_recording_video_filename} with duration 0.0 seconds')

    self.db.add_video(self.video_recording_start_time, f'{self.currently_recording_video_filename}', 0.0)

    self.currently_recording_video_filename = None

    self.is_recording_video = False

  def capture_still(video_url, self):
    if self.is_capture_still:
      return None

    self.is_capture_still = True

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

    self.is_capture_still = False
    
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
          f'http://{doogle_server_host}:4000/chat',
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
    if self.ir_led_behavior() == 'auto':
      self.ir_leds.turn_off_leds()

    self.stop_recording_video()

  def log(self, message):
    if debug:
      self.logger.info(message)

  def ir_led_behavior(self):
    settings = self.db.get_settings()
    if settings is None:
        return 'auto'
    
    if isinstance(settings, str):
        try:
            settings = json.loads(settings)
        except json.JSONDecodeError:
            return 'auto'
    
    if isinstance(settings, list):
        if not settings:
            return 'auto'
        settings = settings[0]
    
    return settings.get('ir_led_behavior', 'auto')

  def stop_streaming_server(self):
    subprocess.run('sudo pkill -f mediamtx', shell=True)

  def start_streaming_server(self):
    presets = {
      'daytime': {
        'brightness': 0.1,
        'contrast': 1.0
      },
      'nighttime': {
        'brightness': 0.6,
        'contrast': 1.9
      }
    }

    preset = 'daytime'

    brightness = str(presets[preset]['brightness'])
    contrast = str(presets[preset]['contrast'])

    command = f'sudo BRIGHTNESS="{brightness}" CONTRAST="{contrast}" /usr/local/bin/mediamtx mediamtx.yml &'

    self.stop_streaming_server()
    threading.Thread(target=lambda: subprocess.run(command, shell=True)).start()

  def handle_overheating(self):
    if self.get_pi_temperature() >= 65:
      self.log('Raspberry Pi is overheating. Stopping streaming server.')
      self.stop_streaming_server()
      
      self.log('Waiting for Raspberry Pi to cool down...')
      while self.get_pi_temperature() > 60:
          time.sleep(30)
      
      self.log('Raspberry Pi has cooled down. Starting streaming server.')
      self.start_streaming_server()
      
  def start(self):
    while True:
      time.sleep(1)
      self.handle_overheating()
      self.log_system_info()

      secs_since_last_motion = (datetime.datetime.now() - self.time_of_last_motion).total_seconds()

      if self.ir_led_behavior() == 'on':
        self.ir_leds.turn_on_leds()

      if self.ir_led_behavior() == 'off':
        self.ir_leds.turn_off_leds()

      if secs_since_last_motion > 10:
        self.handle_motion_end()

      if self.motion_sensor.motion_detected:
        if self.ir_led_behavior() == 'auto':
          self.ir_leds.turn_on_leds()

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