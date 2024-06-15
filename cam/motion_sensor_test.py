#!/home/dooglecam/.venv/bin/python3

from motion_sensor import MotionSensor
import time

motion_sensor = MotionSensor()
motion_sensor.start()

while True:
  if motion_sensor.motion_detected:
    print('Motion detected')
  else:
    print('No motion detected')
  time.sleep(1)

