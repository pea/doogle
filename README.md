# Doogle

## Description

AI home voice assistant designed to be run on a Raspberry Pi, with LlamaCpp, WhistperCpp and TTS running on a server with a GPU.

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

1. In /chatbot Run `pip install -r requirements.txt`
2. Run `python3 chat.py` for voice chat or `python3 cli.py` for text chat