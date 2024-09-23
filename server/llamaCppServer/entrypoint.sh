#!/bin/sh

if [ -n "$MMPROJ_DOWNLOAD_URL" ]; then
  exec ./llama-server -m /models/model.gguf --mmproj /models/mmproj.gguf -n 512 --n-gpu-layers 32 --port 7000 --host 0.0.0.0 --batch-size 2048 --ubatch-size 256 --ctx-size 256
else
  exec ./llama-server -m /models/model.gguf -n 512 --n-gpu-layers 32 --port 7000 --host 0.0.0.0 --batch-size 2048 --ubatch-size 256 --ctx-size 256
fi