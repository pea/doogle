FROM nvidia/cuda:12.3.1-devel-ubuntu22.04

RUN apt-get update && apt-get install -y wget git && \
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
  bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda && \
  rm Miniconda3-latest-Linux-x86_64.sh

ENV PATH="/root/miniconda/bin:${PATH}"
ARG PATH="/root/miniconda/bin:${PATH}"

RUN conda create -y --name tortoise python=3.9 numba inflect
RUN echo "conda activate tortoise" >> ~/.bashrc
RUN /bin/bash -c "source ~/.bashrc"
RUN conda install -y pytorch torchvision torchaudio pytorch-cuda=12 -c pytorch -c nvidia
RUN conda install transformers=4.29.2
RUN git clone https://github.com/neonbjb/tortoise-tts.git
RUN cd tortoise-tts && python setup.py install

COPY ./server.py /tortoise-tts/tortoise/server.py
COPY ./requirements.txt /tortoise-tts/tortoise/requirements.txt
RUN pip install -r /tortoise-tts/tortoise/requirements.txt

CMD ["python3", "/tortoise-tts/tortoise/server.py"]