ARG UBUNTU_VERSION=22.04

# This needs to generally match the container host's environment.
ARG CUDA_VERSION=12.3.1

# Target the CUDA build image
ARG BASE_CUDA_DEV_CONTAINER=nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}

FROM ${BASE_CUDA_DEV_CONTAINER} as build

EXPOSE 7000

# Unless otherwise specified, we make a fat build.
ARG CUDA_DOCKER_ARCH=all

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential python3 python3-pip git wget

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

# Download the models
RUN mkdir /models

RUN wget -O /models/ggml-mistral-q_4_k.gguf "https://huggingface.co/cmp-nct/llava-1.6-gguf/resolve/main/ggml-mistral-q_4_k.gguf?download=true"

RUN wget -O /models/mmproj-mistral7b-f16.gguf "https://huggingface.co/cmp-nct/llava-1.6-gguf/resolve/main/mmproj-mistral7b-f16.gguf?download=true"

ENTRYPOINT ["/app/.devops/tools.sh"]

