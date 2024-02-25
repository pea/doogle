#!/bin/bash
if pgrep -x "chat.py" > /dev/null
then
    echo "Doogle is already running."
else
    cd /home/doogle/doogle/chatbot/
    until ./chat.py --debug true; do
        echo "Script crashed with exit code $?. Respawning.." >&2
        sleep 2
    done
fi