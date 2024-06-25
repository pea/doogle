#!/bin/bash

# Ensure the script stops on errors
set -e

# Check if model base, input checkpoint, and training data file are provided
if [ -z "$MODEL_BASE" ] || [ -z "$CHECKPOINT_IN" ]; then
  echo "Error: MODEL_BASE and CHECKPOINT_IN must be provided."
  echo "Usage: docker run -e MODEL_BASE=<model_base> -e CHECKPOINT_IN=<checkpoint_in> -v /path/to/data:/workspace/data <image>"
  exit 1
fi

# Check if the training data file exists
if [ ! -f /workspace/data/input_data.txt ]; then
  echo "Error: Training data file /workspace/data/input_data.txt not found."
  exit 1
fi

# Fine-tune the model using llama.cpp
/workspace/llama.cpp/build/bin/llama-finetune \
    --model-base $MODEL_BASE \
    --checkpoint-in $CHECKPOINT_IN \
    --checkpoint-out /workspace/data/chk-lora-output.gguf \
    --lora-out /workspace/data/lora-output.bin \
    --train-data /workspace/data/input_data.txt \
    --save-every 10 \
    --threads 6 --adam-iter 30 --batch 4 --ctx 64 \
    --use-checkpointing

# Notify completion
echo "Fine-tuning completed. Check /workspace for the output files."
