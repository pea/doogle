#!/home/doogle/doogle/chatbot/.venv/bin/python3

import subprocess

def volume(volume):
  try:
    subprocess.call(["amixer", "set", "Master", "--", str(volume)+"%"])
    subprocess.run(["ffplay", "-nodisp", "-autoexit", "sound/volume_check.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "The volume has been set to " + str(volume) + "%"
  except:
    return "An error occurred while setting the volume"