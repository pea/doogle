ARG UBUNTU_VERSION=22.04

# This needs to generally match the container host's environment.
ARG CUDA_VERSION=12.3.1

# Target the CUDA build image
ARG BASE_CUDA_DEV_CONTAINER=nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}

FROM ${BASE_CUDA_DEV_CONTAINER} as build

# Unless otherwise specified, we make a fat build.
ARG CUDA_DOCKER_ARCH=all

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential python3 python3-pip git wget g++ cmake make

RUN git clone https://github.com/ggerganov/llama.cpp.git /app

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Set nvcc architecture
ENV CUDA_DOCKER_ARCH=${CUDA_DOCKER_ARCH}

# Enable cuBLAS
ENV LLAMA_CUBLAS=1

ENV PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

RUN make

# Download the model
RUN mkdir /models
RUN wget -O /models/open-llama-3b-v2-q8_0.gguf https://huggingface.co/SlyEcho/open_llama_3b_v2_gguf/resolve/main/open-llama-3b-v2-q8_0.gguf?download=true

# Download training data
RUN wget -O /app/shakespeare.txt https://raw.githubusercontent.com/brunoklein99/deep-learning-notes/master/shakespeare.txt

CMD ["/app/finetune --model-base /models/open-llama-3b-v2-q8_0.gguf --checkpoint-in  /models/chk-lora-open-llama-3b-v2-q8_0-shakespeare-LATEST.gguf --checkpoint-out /models/chk-lora-open-llama-3b-v2-q8_0-shakespeare-ITERATION.gguf --lora-out /models/lora-open-llama-3b-v2-q8_0-shakespeare-ITERATION.bin --train-data "/app/shakespeare.txt" --save-every 10 --threads 6 --adam-iter 30 --batch 4 --ctx 64 --use-checkpointing"]

