import RPi.GPIO as GPIO
import time
import threading

class LightSensor:
  def __init__(self, sensor_pin=6):
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Set up pins
    self.sensor_pin = sensor_pin
    GPIO.setup(self.sensor_pin, GPIO.IN)

    # Initialize light_detected
    self.light_detected = False

    # Attach interrupt for both rising and falling edges
    GPIO.add_event_detect(self.sensor_pin, GPIO.BOTH, callback=self.sensor_callback, bouncetime=200)

  def sensor_callback(self, channel):
    # Check the current state and set light_detected accordingly
    if GPIO.input(self.sensor_pin):
      self.light_detected = False
    else:
      self.light_detected = True

  def get_light_status(self):
    # Method to get the current light detection status
    return self.light_detected

  def start(self):
    self.thread = threading.Thread(target=self.run)
    self.thread.start()
  
  def run(self):
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      GPIO.cleanup()