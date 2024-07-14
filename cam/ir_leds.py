import RPi.GPIO as GPIO
import time

class ir_leds:
  def __init__(self):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)

  def turn_on_leds(self):
    GPIO.output(23, GPIO.HIGH)

  def turn_off_leds(self):
    GPIO.output(23, GPIO.LOW)

  def test_leds(self):
    self.turn_on_leds()
    time.sleep(1)
    self.turn_off_leds()