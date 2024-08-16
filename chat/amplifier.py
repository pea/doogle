import RPi.GPIO as GPIO
from database import Database
import os

class Amplifier:
  def __init__(self, callback=None):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    self.database = Database(os.path.join(current_dir, 'chat.db'))
    self.pin = 6
    self.callback = callback
    try:
      GPIO.setmode(GPIO.BCM)
      GPIO.setup(self.pin, GPIO.OUT)
      GPIO.output(self.pin, GPIO.HIGH)
      self.database.update_muted(muted=True)
    except:
      pass

  def mute(self):
    try:
      is_muted = self.database.get_muted()
      if is_muted == False:
        GPIO.output(self.pin, GPIO.HIGH)
        self.database.update_muted(muted=True)
        if self.callback is not None:
          self.callback(muted=True, error=None)
    except Exception as e:
      if self.callback is not None:
        self.callback(muted=False, error=e)
      pass

  def unmute(self):
    try:
      is_muted = self.database.get_muted()
      if is_muted == True:
        GPIO.output(self.pin, GPIO.LOW)
        self.database.update_muted(muted=False)
        if self.callback is not None:
          self.callback(muted=False, error=None)
    except Exception as e:
      if self.callback is not None:
        self.callback(muted=False, error=e)
      pass