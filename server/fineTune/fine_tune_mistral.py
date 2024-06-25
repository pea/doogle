import torch
from transformers import MistralForCausalLM, MistralTokenizer
import sys

# Load the pre-trained model and tokenizer
model_name = "path_to_pretrained_model"  # Update with actual model path or name
tokenizer = MistralTokenizer.from_pretrained(model_name)
model = MistralForCausalLM.from_pretrained(model_name)

# Load the training data
train_data_path = sys.argv[1]
train_texts = open(train_data_path, "r").readlines()

# Tokenize the data
inputs = tokenizer(train_texts, return_tensors="pt", max_length=512, truncation=True, padding="max_length")

# Fine-tuning settings
epochs = 3
learning_rate = 5e-5

# Prepare the optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

# Fine-tune the model
model.train()
for epoch in range(epochs):
    for batch in inputs['input_ids']:
        outputs = model(input_ids=batch, labels=batch)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    print(f"Epoch {epoch+1} completed. Loss: {loss.item()}")

# Save the fine-tuned model
fine_tuned_model_path = "fine_tuned_model"
model.save_pretrained(fine_tuned_model_path)
tokenizer.save_pretrained(fine_tuned_model_path)

# Convert the model to ONNX format
dummy_input = torch.zeros(1, 512, dtype=torch.long)
onnx_model_path = "mistral_model.onnx"
torch.onnx.export(model, dummy_input, onnx_model_path)

# Convert ONNX model to GGUF format
import onnx_to_gguf
gguf_model_path = "mistral_model.gguf"
onnx_to_gguf.convert(onnx_model_path, gguf_model_path)
