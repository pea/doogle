# Doogle

## Description

Smart speaker designed to replace the big tech alternatives. The heavy lifting is designed to be done by a server with a GPU running Llama.cpp, Whisper.cpp and TTS, and a Raspberry Pi does the audio input and output, as well as control any peripherals like RF transceivers.

## Contents
- [Features](#features)
- [Installation](#installation)
  - [Server](#server)
  - [Chatbot](#chatbot)
  - [Cam](#cam)
- [Functions](#functions)
  - [Command-type function](#command-type-function)
  - [Environment-type function](#environment-type-function)
  - [Wakeword-type function](#wakeword-type-function)
- [Respeaker Setup](#respeaker-setup)
- [Debugging](#debugging)

## Features
- Wake words ("Hey Doogle")
- Voice chat and text chat
- Functions using LLM
  - Control 433 Mhz remote control sockets
  - Internet radio
  - Timer
  - Volume control
- Functions using wake words ("Lights on")
- Functions that populate the prompt (like the time)
- Designed for reSpeaker 4-Mic Array
- Easy server setup with Docker Compose

## Installation

### Server

#### Prerequisites

- Nvidia GPU and the necessary drivers installed, including Nvidia Container Toolkit
- Docker

1. Install [Nvidia drivers](https://www.nvidia.co.uk/Download/index.aspx?lang=en-uk)
2. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
3. Clone the repository to your server
4. Edit the dockerfiles as necessary (such as changing the models used, cuda versions, etc.)
5. Run `docker compose up -d`
6. Open port 4000 on your server

Tested with:
- Debain
- RTX 3080 Ti
- MSI X570-A PRO
- 16GB RAM

### Chatbot

#### Prerequisites

- Python 3
- Pip

#### Installation

It's assumed that the user of the Raspberry Pi is called `doogle`. If not, replace `doogle` with the username of the user. By default it's `pi`.

Clone the repository to `/home/doogle`.

Install Python 3 as a virtual environment and the necessary Python packages for Doogle.

`cd /home/doogle/doogle/chatbot`

`chmod +x chat.py`

`python3 -m venv .venv`

`source .venv/bin/activate`

`pip install -r requirements.txt`

Configure the Raspberry Pi to login automatically at boot.

`sudo nano /etc/lightdm/lightdm.conf`

In the [Seat:*] section of the file, add or modify the following lines:
```
[Seat:*]
autologin-user=doogle
autologin-user-timeout=0
```

Configure Doogle to start at login.

`echo "/home/doogle/doogle/chatbot/run_chatbot.sh" >> ~/.bashrc`
`chmod +x /home/dooglecam/run_stream.sh`

Install some optional packages to do with functions.

For the radio:

`sudo apt install vlc`

Reboot the Raspberry Pi.

`sudo reboot`

### Cam

Install dependencies

`sudo apt-get update` and `sudo apt-get install vlc`

In the [Seat:*] section of the file, add or modify the following lines:

```
[Seat:*]
autologin-user=dooglecam
autologin-user-timeout=0
```

Configure Doogle Cam to start at login.

`echo "/home/dooglecam/run_stream.sh &" >> ~/.bashrc`
`echo "/home/dooglecam/run_cam.sh &" >> ~/.bashrc`

Install BMP280 Barometric Pressure Sensor if added

Instructions: https://iotstarters.com/configuring-bmp280-sensor-with-raspberry-pi

#### Functions

To add a function, create a new item in `functions.json`.

#### Command-type function

```
"lightsOn": {
  "type": "command",
  "prompt": "force turn on the lights",
  "triggerWords": ["lights", "light"],
  "command": ".venv/bin/python3 functions/transmit.py 4543573 -p 433 && python3 functions/transmit.py 4527445 -p 433"
}
```

- `index`: the text ID of the function
- `prompt`: the prompt to be added to the chatbot when the function is triggered by the triggerWord
- `triggerWords`: When any of these words are spoken by the user, the function prompt will be added. This allows for many functions without bogging down the request with a long prompt.
- `command`: The command to run when the function is triggered.

#### Environment-type function

```
"time": {
  "type": "environment",
  "prompt": "The time is [function_response]",
  "command": "python3 functions/time.py"
}
```

- `index`: the text ID of the function
- `prompt`: the prompt to be added to the chatbot
- `command`: The command to run, `[function_response]` will be replaced with the output of the command

#### Wakeword-type function

```
"turnTheLightsOn": {
  "type": "wakeword",
  "model": "doogle_lights_on",
  "command": ".venv/bin/python3 functions/transmit.py 4543573 -p 433 && python3 functions/transmit.py 4527445 -p 433"
}
```

- `index`: the text ID of the function
- `model`: the name of the model to use for the wake word contained in the `models` directory
- `command`: The command to run when the function is triggered.

#### Respeaker Setup

The Doogle chatbot can be used with a standard USB microphone, but it's designed to work with the ReSpeaker 4-Mic Array for Raspberry Pi. This is a 4-microphone array that can be used to detect the direction of sound and provides VAD capabilities. It's also a speaker, so it can be used to play audio.

### Give user permission to use the Repspeaker

- `lsusb` and find vendor ID and product ID (e.g. 2886:0018)
- `sudo nano /etc/udev/rules.d/99-com.rules`
- Add `SUBSYSTEM=="usb", ATTR{idVendor}=="2886", ATTR{idProduct}=="0018", MODE="0666"`
- `sudo udevadm control --reload-rules`
- `sudo udevadm trigger`

#### Debugging

Update `DOOGLE_DEBUG` in .env to toggle debugging. Logs are stored in chat.log and cleared on each boot.

