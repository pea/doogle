import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--volume', type=int, default=100)
args = parser.parse_args()

def volume(volume):
  try:
    subprocess.call(["amixer", "set", "Master", "--", str(volume)+"%"])
    subprocess.run(["ffplay", "-nodisp", "-autoexit", "sound/volume_check.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("The volume has been set to " + str(volume) + "%")
    return "The volume has been set to " + str(volume) + "%"
  except:
    return "An error occurred while setting the volume"
  
if args.volume:
  volume(args.volume)