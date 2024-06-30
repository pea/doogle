#!/bin/bash

cd /home/dooglecam

command="rpicam-vid --width 640 --height 480 --framerate 15 --level 4.2 --bitrate 2000000 --denoise cdn_off --analoggain 0 force_turbo 1 --codec mjpeg -n -t 0 --inline -o - | cvlc -vvv stream:///dev/stdin --sout '#transcode{vcodec=VP80,vb=8000,acodec=none}:standard{access=http,mux=webm,dst=:8160}' :demux=mjpeg &"

if pgrep -x "rpicam-vid" > /dev/null
then
  echo "Video stream already started"
else 
  until eval $command; do
    echo "Script crashed with exit code $?. Respawning.." >&2
    sleep 2
  done
fi

