#!/bin/bash
cd /home/doogle/doogle/chatbot/
until ./chat.py > "chat.$(date +%Y%m%d%H%M%S)".log 2>&1; do
    echo "Script crashed with exit code $?. Respawning.." >&2
    sleep 2
done
