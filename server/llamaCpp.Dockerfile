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

# Download the model
RUN mkdir /models
RUN wget -O /models/wizardlm-1.0-uncensored-llama2-13b.Q4_K_M.gguf "https://huggingface.co/TheBloke/WizardLM-1.0-Uncensored-Llama2-13B-GGUF/resolve/main/wizardlm-1.0-uncensored-llama2-13b.Q4_K_M.gguf?download=true"

ENTRYPOINT ["/app/.devops/tools.sh"]

