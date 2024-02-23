# Doogle

## Description

Smart speaker designed to replace the big tech alternatives. The heavy lifting is designed to be done by a server with a GPU running Llama.cpp, Whisper.cpp and TTS, and a Raspberry Pi does the audio input and output, as well as control any peripherals like RF transceivers.

## Features
- Wake word ("Hey Doogle")
- Voice chat and text chat
- Functions

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

Install some optional packages to do with functions.

For the radio:

`sudo apt install vlc`

Reboot the Raspberry Pi.

`sudo reboot`

### Update chatbot dependencies

```
pip install --upgrade -r requirements.txt
```

### Functions

To add a function, create a new item in `functions.json`.

index: the text ID of the function
Type: "environment" or "command". `command` phrases the instruction as "Doogle can..", `environment` phrases the instruction as "the time is..". Add [function_response] to the prompt to have the response from the function inserted into the environment-type prompt.
triggerWords: When any of these words are spoken by the user, the function prompt will be added. This allows for many functions without bogging down the request with a long prompt.
command: The command to run when the function is triggered. The command can return a response in any format - Doogle will read it in plain English.

```
"time": {
  "type": "environment",
  "prompt": "the time is [function_response]",
  "triggerWords": ["time"],
  "command": "python3 functions/time.py"
}
```

## Volume

You might want to increase the mic gain and speaker volume on the Raspberry Pi. You can do this by running `alsamixer`.

## Respeaker

The Doogle chatbot can be used with a standard USB microphone, but it's designed to work with the ReSpeaker 4-Mic Array for Raspberry Pi. This is a 4-microphone array that can be used to detect the direction of sound and provides VAD capabilities. It's also a speaker, so it can be used to play audio.

### Give user permission to use the Repspeaker

- `lsusb` and find vendor ID and product ID (e.g. 2886:0018)
- `sudo nano /etc/udev/rules.d/99-com.rules`
- Add `SUBSYSTEM=="usb", ATTR{idVendor}=="2886", ATTR{idProduct}=="0018", MODE="0666"`
- `sudo udevadm control --reload-rules`
- `sudo udevadm trigger`

## Debugging

`cd ~/doogle/chatbot`
`pkill chat.py && .venv/bin/python3 chat.py debug`

## Wake Words

# Turn the lights on

Settings used
```
config["target_phrase"] = ["turn the lights on", "Doogle lights on", "lights on"]
config["custom_negative_phrases"] = ["turn the lights off", "Doogle lights off", "lights off"]
config["n_samples"] = 100000
config["n_samples_val"] = 2000
config["steps"] = 100000
config["target_accuracy"] = 0.7
config["target_recall"] = 0.5
config["target_false_positives_per_hour"] = 0.2
config["max_negative_weight"] = 1000
```

# Turn the lights off

```
config["target_phrase"] = ["turn the lights off", "Doogle lights off", "lights off"]
config["custom_negative_phrases"] = ["turn the lights on", "Doogle lights on", "lights on"]
config["n_samples"] = 100000
config["n_samples_val"] = 2000
config["steps"] = 100000
config["target_accuracy"] = 0.7
config["target_recall"] = 0.5
config["target_false_positives_per_hour"] = 0.2
config["max_negative_weight"] = 1000
```