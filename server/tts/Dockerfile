ARG BASE=nvidia/cuda:12.3.1-base-ubuntu22.04
FROM ${BASE}

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends gcc g++ make python3 python3-dev python3-pip python3-venv python3-wheel espeak-ng libsndfile1-dev git && rm -rf /var/lib/apt/lists/*
RUN pip3 install llvmlite --ignore-installed

# Install Dependencies:
RUN pip3 install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu118
RUN rm -rf /root/.cache/pip

# Copy TTS repository contents:
WORKDIR /root

RUN mkdir /root/TTS
RUN git clone https://github.com/coqui-ai/TTS.git /root/TTS

RUN cd TTS && make install

EXPOSE 5002

ENV CUDA_VISIBLE_DEVICES="0"

ENTRYPOINT ["python3", "/root/TTS/TTS/server/server.py",  "--model_name", "tts_models/en/vctk/vits", "--use_cuda", "True"]
