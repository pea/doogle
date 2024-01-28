FROM nvidia/cuda:12.3.1-base-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip wget git git-lfs

RUN pip3 install diffusers accelerate scipy safetensors xformers torch flask transformers

RUN git-lfs install

RUN git clone https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 /models/stable-diffusion-xl-base-1.0

EXPOSE 3002

WORKDIR /app

COPY ./stableDiffusion /app

CMD ["python3", "server.py", "--model", "/models/stable-diffusion-xl-base-1.0"]