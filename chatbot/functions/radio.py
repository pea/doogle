#!/usr/bin/env python3

import vlc
import time
import argparse
from pyradios import RadioBrowser
import json

parser = argparse.ArgumentParser(description='Plays a radio station')

parser.add_argument('search', metavar='SEARCH', type=str,
                    help="Search term")

args = parser.parse_args()

search_query = args.search

rb = RadioBrowser()

search_results = rb.search(name=search_query, limit=1, order="clickcount", reverse=True, hidebroken=True)

station = json.loads(json.dumps(search_results[0]))

# URL of the audio stream
url = station['url']

print("Playing " + station['name'])

# Create a VLC instance
instance = vlc.Instance()

# Create a media player
player = instance.media_player_new()

# Create a Media instance
media = instance.media_new(url)

# Set the media to the player
player.set_media(media)

# Play the media
player.play()

# Let it play for some time. Adjust as needed.
time.sleep(60)

# Stop the player
player.stop()