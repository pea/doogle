from flask import Flask, request, Response
from api_fast import TextToSpeech, MODELS_DIR
from api import TextToSpeech as TextToSpeech2
import queue
import threading
import os
from utils.audio import load_audio, load_voices
import torch
import gc
import io
import wave
import torchaudio

app = Flask(__name__)

@app.route('/stream', methods=['POST'])
def stream_text_to_speech():
  text = request.json['text']
  voice = request.json['voice']

  torch.cuda.empty_cache()
  gc.collect()

  selected_voice = voice
  
  tts = TextToSpeech(models_dir=MODELS_DIR, use_deepspeed=True, kv_cache=True, half=True, autoregressive_batch_size=1)

  voice_samples, conditioning_latents = load_voices([selected_voice])
  
  audio_generator = tts.tts_stream(text, voice_samples=voice_samples, use_deterministic_seed=True)

  def generate_audio():
      audio_buffer = []

      for wav_chunk in audio_generator:
          audio_buffer.append(torch.unsqueeze(torch.from_numpy(wav_chunk.cpu().numpy()), 0))

      audio_tensor = torch.cat(audio_buffer, dim=1)
      wav_io = io.BytesIO()
      torchaudio.save(wav_io, src=audio_tensor, sample_rate=24000, format="wav")

      wav_data = wav_io.getvalue()
      yield wav_data

  return Response(generate_audio(), mimetype='audio/wav')

@app.route('/tts', methods=['POST'])
def text_to_speech():
  text = request.json['text']
  voice = request.json['voice']

  torch.cuda.empty_cache()
  gc.collect()

  tts = TextToSpeech2(models_dir=MODELS_DIR, use_deepspeed=False, kv_cache=True,autoregressive_batch_size=1, half=True)

  selected_voice = voice

  voice_samples, conditioning_latents = load_voices([selected_voice])

  gen, dbg_state = tts.tts_with_preset(text, k=1, voice_samples=voice_samples, conditioning_latents=conditioning_latents,
                preset="fast", use_deterministic_seed=True, return_deterministic_state=True, cvvp_amount=.0)
  
  if isinstance(gen, list):
    audio_data = []
    for j, g in enumerate(gen):
      audio_data.append(g.squeeze(0).cpu())
  else:
    audio_data = gen.squeeze(0).cpu()

  audio_io = io.BytesIO()
  torchaudio.save(audio_io, audio_data, 24000, format="wav")

  return Response(audio_io.getvalue(), mimetype='audio/wav')

if __name__ == '__main__':
  app.run(port=6700, host='0.0.0.0')
