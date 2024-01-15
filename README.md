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

### Functions

Functions are rudimentary but still somewhat reliable. They use grammar to have Doogle return JSON. Doogle can return the name of a function being requested by the user, and then Doogle runs the matching command. Currently it's more of a binary switch, so can't return any other data with the function, but it would be possible to add.

To add a function, add a new item to the functions.json file. The prompt tells Doogle when it can do, e.g. "play music". The command is what's run.

```
"playNtsRadioOne": {
  "prompt": "Play NTS Radio One",
  "command": "python3 functions/radio.py 'NTS Radio 1'"
}
```

#### Radio

Llama 2 refuses to play radio stations due to "ethical reasons". So you'll have to use a different model to do it, such as [WizardLM-1.0-Uncensored-Llama2-13B-GGUF](https://huggingface.co/TheBloke/WizardLM-1.0-Uncensored-Llama2-13B-GGUF).

## Volume

You might want to increase the mic gain and speaker volume on the Raspberry Pi. You can do this by running `alsamixer`.