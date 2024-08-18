# Doogle Chat

## Install

1. Change `.env.example` to `.env` and configure `DOOGLE_SERVER_HOST` with the IP of your machine running the Doogle server
2. Copy the contents of ./chat to the Raspberry PI
3. Run `make install`
4. Restart the Raspberry PI `sudo reboot`

## Functions

To add a function, create a new item in `functions.json`.

### Command-type function

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

### Environment-type function

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

### Wakeword-type function

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

## Respeaker Setup

The Doogle chatbot can be used with a standard USB microphone, but it's designed to work with the ReSpeaker 4-Mic Array for Raspberry Pi. This is a 4-microphone array that can be used to detect the direction of sound and provides VAD capabilities. It's also a speaker, so it can be used to play audio.

### Give user permission to use the Repspeaker

- `lsusb` and find vendor ID and product ID (e.g. 2886:0018)
- `sudo nano /etc/udev/rules.d/99-com.rules`
- Add `SUBSYSTEM=="usb", ATTR{idVendor}=="2886", ATTR{idProduct}=="0018", MODE="0666"`
- `sudo udevadm control --reload-rules`
- `sudo udevadm trigger`

## Debugging

Update `DOOGLE_DEBUG` in .env to toggle debugging. Logs are stored in chat.log and cleared on each boot.

## Rotary Encoder + Button

A clickable rotary encoder can be used to control the volume of the speaker. The rotary encoder has 5 pins: GND, VCC, SW, CLK, and DT. VCC and GND are connected to the 5V and GND pins on the Raspberry PI. SW (button) is connected to GPIO pin 17, CLK is connected to GPIO pin 18, and DT is connected to GPIO pin 19. Clicking will wake Doogle (same as saying "Doogle") and rotating will adjust the volume. 