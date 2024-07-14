#!/bin/bash

cd /home/doogle/doogle/chatbot/
source .env

if [ -z "$DOOGLE_DEBUG" ]
then
    DOOGLE_DEBUG="false"
fi

if pgrep -x "chat.py" > /dev/null
then
  if [ "$DOOGLE_DEBUG" = "false" ]
  then
    echo "Doogle started"
  else
    echo "Doogle started in debug mode"
  fi
else 
  until ./chat.py; do
    echo "Script crashed with exit code $?. Respawning.." >&2
    sleep 2
  done
fi