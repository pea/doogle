import subprocess
import argparse
import threading
import time
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from amplifier import Amplifier

parser = argparse.ArgumentParser()
parser.add_argument('--url', type=str, default='')
parser.add_argument('--stop', type=bool, default=False)
parser.add_argument('--volume', type=int, default=20)
args = parser.parse_args()

gain = 8 / 100 * args.volume

def play_media(url):
  amplifier = Amplifier()
  amplifier.unmute()
  subprocess.run(["pkill", "vlc"])
  subprocess.run(["pkill", "VLC"])
  time.sleep(1)
  subprocess.run(["vlc", "--intf", "rc", "--no-video", "--gain", str(gain), "--rc-host", "localhost:12345", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_media():
  amplifier = Amplifier()
  amplifier.mute()
  subprocess.run(["pkill", "vlc"])
  subprocess.run(["pkill", "VLC"])

if args.url:
  thread = threading.Thread(target=play_media, args=(args.url,), name='vlc_thread')
  thread.start()

if args.stop:
  thread = threading.Thread(target=stop_media, name='vlc_thread')
  thread.start()