#!/bin/bash

cd /home/dooglecam

command="./cam.py &"

if pgrep -x "cam.py" > /dev/null
then
  echo "Doogle Cam already started"
else 
  until eval $command; do
    echo "Script crashed with exit code $?. Respawning.." >&2
    sleep 2
  done
fi