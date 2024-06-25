# Base image with CUDA 12.3.1 and Ubuntu 22.04
FROM nvidia/cuda:12.3.1-devel-ubuntu22.04

# Set the working directory
WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    wget \
    build-essential \
    cmake \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --upgrade pip
RUN pip3 install torch transformers

# Clone llama.cpp repository and build the tool
RUN git clone https://github.com/ggerganov/llama.cpp.git /workspace/llama.cpp
RUN cd /workspace/llama.cpp && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make

# Set environment variables for llama.cpp
ENV PATH="/workspace/llama.cpp/build/bin:${PATH}"

RUN wget -P /workspace https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q2_K.gguf

# Copy the entrypoint script
COPY entrypoint.sh /workspace/entrypoint.sh
RUN chmod +x /workspace/entrypoint.sh

# Entrypoint
ENTRYPOINT ["/workspace/entrypoint.sh"]
