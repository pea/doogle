import subprocess
import argparse
import threading
import time

parser = argparse.ArgumentParser()
parser.add_argument('--url', type=str, default='')
parser.add_argument('--stop', type=bool, default=False)
args = parser.parse_args()

def play_media(url):
  subprocess.run(["pkill", "vlc"])
  subprocess.run(["pkill", "VLC"])
  time.sleep(1)
  subprocess.run(["vlc", "--intf", "rc", "--rc-host", "localhost:12345", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_media():
  subprocess.run(["pkill", "vlc"])
  subprocess.run(["pkill", "VLC"])

if args.url:
  thread = threading.Thread(target=play_media, args=(args.url,), name='vlc_thread')
  thread.start()

if args.stop:
  thread = threading.Thread(target=stop_media, name='vlc_thread')
  thread.start()