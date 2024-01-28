from flask import Flask, request
from diffusers import DiffusionPipeline
import torch
import io
from flask import Response
import argparse

app = Flask(__name__)

parser = argparse.ArgumentParser(description='Runs a server for text-to-image')
parser.add_argument('--model', dest='model', type=str, default="/models/stable-diffusion-2-base",
                    help="Model to use")
args = parser.parse_args()
model = args.model

@app.route('/text-to-image', methods=['POST'])
def text_to_image():
  text = request.json['text']

  pipe = DiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16, use_safetensors=True, variant="fp16")

  pipe = pipe.to("cuda")

  pipe.enable_xformers_memory_efficient_attention()

  image = pipe(text).images[0]  

  image_bytes = io.BytesIO()
  image.save(image_bytes, format='PNG')
  image_bytes = image_bytes.getvalue()

  return Response(image_bytes, content_type='image/png')

if __name__ == '__main__':
  app.run(port=3002, host='0.0.0.0')
