# Sounds With Silent

These sound files are identical to the ones in the parent directly but prefixed with silence.wav. They are used to play a silent sound before the actual sound as some amplifiers mute the audio when no sound is playing. This can cause the first few ms to be clipped off the beginning of the sound. By playing a silent sound first, the amplifier will not mute the audio and the sound will play as expected.

If the amplifier doesn't do this then the wav files in with_silent can be deleted and the ones in the parent directory can be used instead.