ARG UBUNTU_VERSION=22.04
# This needs to generally match the container host's environment.
ARG CUDA_VERSION=12.3.1
# Target the CUDA build image
ARG BASE_CUDA_DEV_CONTAINER=nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}
# Target the CUDA runtime image
ARG BASE_CUDA_RUN_CONTAINER=nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu${UBUNTU_VERSION}

FROM ${BASE_CUDA_DEV_CONTAINER} AS build
WORKDIR /app

# Unless otherwise specified, we make a fat build.
ARG CUDA_DOCKER_ARCH=all
# Set nvcc architecture
ENV CUDA_DOCKER_ARCH=${CUDA_DOCKER_ARCH}
# Enable cuBLAS
ENV WHISPER_CUBLAS=1

RUN apt-get update && \
    apt-get install -y build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Ref: https://stackoverflow.com/a/53464012
ENV CUDA_MAIN_VERSION=12.3
ENV LD_LIBRARY_PATH /usr/local/cuda-${CUDA_MAIN_VERSION}/compat:$LD_LIBRARY_PATH

# Install Whisper codebase
RUN git clone --branch v1.5.3 https://github.com/ggerganov/whisper.cpp.git .

# Download the model
RUN bash ./models/download-ggml-model.sh small.en

# Build Whisper
RUN make

FROM ${BASE_CUDA_RUN_CONTAINER} AS runtime
WORKDIR /app

RUN apt-get update && \
  apt-get install -y curl ffmpeg \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY --from=build /app /app

CMD ["/app/server", "--host", "0.0.0.0", "--model", "models/ggml-small.en.bin"]

