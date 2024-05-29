#!/bin/bash

cd /home/dooglecam

command="rpicam-vid --width 1024 --height 864 --framerate 15 --level 4.2 --bitrate 10000000 --denoise cdn_off --analoggain 0 force_turbo 1 --codec mjpeg -n -t 0 --inline -o - | cvlc -vvv stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8160}' :demux=mjpeg"

if pgrep -x "rpicam-vid" > /dev/null
then
  echo "Video stream started"
else 
  until eval $command; do
    echo "Script crashed with exit code $?. Respawning.." >&2
    sleep 2
  done
fi