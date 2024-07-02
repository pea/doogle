import RPi.GPIO as GPIO
import time
import threading

class MotionSensor:
  def __init__(self, sensor_pin=27):
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(True)

    # Set up pins
    self.sensor_pin = sensor_pin
    GPIO.setup(self.sensor_pin, GPIO.IN)

    # Initialize count and motion_detected
    self.count = 0
    self.motion_detected = False

    # Attach interrupt
    GPIO.add_event_detect(self.sensor_pin, GPIO.FALLING, callback=self.sensor_callback)

  # Function to handle sensor signal
  def sensor_callback(self, channel):
    self.count += 1

  # Function to process the count
  def process_count(self):
    if self.count > 1:
      self.motion_detected = True
      self.count = 0
    else:
      self.motion_detected = False
      self.count = 0

  def start(self):
    self.thread = threading.Thread(target=self.run)
    self.thread.start()

  def run(self):
    try:
      while True:
        time.sleep(1)
        self.process_count()
    except KeyboardInterrupt:
      GPIO.cleanup()
