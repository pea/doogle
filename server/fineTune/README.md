# Train LLM on a new dataset

1. Build the Docker Image
```
docker build -t finetune .
```

2. Run the Docker Container
```
docker run --gpus all -e MODEL_BASE=llama-2-7b-chat.Q2_K.gguf -e CHECKPOINT_IN=chk-lora-open-llama-3b-v2-q8_0-test-LATEST.gguf -v ./data/:/workspace/data finetune
```
