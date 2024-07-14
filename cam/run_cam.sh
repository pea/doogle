#!/bin/bash

cd /home/dooglecam

command="./cam.py &"

while true; do
  if ! pgrep -x "cam.py" > /dev/null; then
    eval "$command"
  fi
  sleep 1
done