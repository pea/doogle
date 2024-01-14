# Doogle

## Description

AI home voice assistant designed to be run on a Raspberry Pi, with LlamaCpp, WhistperCpp and TTS running on a server with a GPU.

## Features
- Wake word ("Hey Doogle")
- Voice chat and text chat
- Functions

## Installation

### Server

#### Prerequisites

- Nvidia GPU and the necessary drivers installed, including Nvidia Container Toolkit
- Docker

1. Copy the contents of server to a server
2. Run `docker compose up -d`
3. Open port 4000 on your server

### Chatbot

#### Prerequisites

- Python 3
- Pip

1. In /chatbot Run `pip install -r requirements.txt`, `sudo apt-get install portaudio19-dev`
2. Run `python3 chat.py` for voice chat or `python3 cli.py` for text chat

### Functions

Functions are rudimentary as currently Llama.cpp doesn't support them. However they are somewhat reliable.

To add a function, add a new item to the functions.json file. The prompt tells Doogle when it should reply in json format with the given function name. It will be added to the prompt before chatting. The command is what's run if Doogle replies with the function name in the json format.