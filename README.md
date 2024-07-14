# Doogle

Doogle is a collection of AI smart devices that aim to replace Google's smart speakers and cameras with open source, privacy focused, and repairable alternatives.

# Doogle Server
The server is an AI language model, speech to text engine and test to speech engine. It uses Llama.cpp, Whisper.cpp and Coqui TTS.

# Doogle Chat
Doogle Chat is a Raspberry Pi 4B, reSpeaker 4-Mic Array, a speaker, and a 443 Mhz transmitter housed in a 3D printed case. Users can interact with it like any other smart speaker, but instead of "Hey Google", it's "Hey Doogle". You can ask him to control RF plug sockets, play internet radio, set timers. These functions are simple python scripts that can Doogle can be configured to handle.

# Doogle Cam
Doogle Cam is a Raspberry Pi 4B, infrared camera and microwave sensor. It activates on movement and translates what it sees into text, then publishes it on an API. It will also record video and allow video streaming. The idea of Doogle cam is to provide Doogle Chat with environmental context. For example, you might want Doogle Chat to wait until someone is in the room before telling them their timer has finished. The case is mostly 3D printed with some parts, such as acryllic disks, being easy to come across on eBay.

# Installation and Usage
- Server: [README.md](server/README.md)
- Chat: [README.md](chat/README.md)
- Cam: [README.md](cam/README.md)