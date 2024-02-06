FROM nvidia/cuda:12.3.1-devel-ubuntu22.04

WORKDIR /app

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    wget

# Upgrade pip
RUN pip3 install --upgrade pip

# Install Jupyter and any other necessary packages defined in automatic_model_training.ipynb
RUN pip3 install jupyter mutagen==1.47.0 torchinfo==1.8.0 torchmetrics==1.2.0 speechbrain==0.5.14 audiomentations==0.33.0 torch-audiomentations==0.11.0 acoustics==0.2.6 tensorflow-cpu==2.8.1 tensorflow_probability==0.16.0 onnx_tf==1.10.0 pronouncing==0.2.0 datasets==2.14.6 deep-phonemizer==0.0.19 piper-phonemize webrtcvad protobuf==3.20.0
    
# Copy the .ipynb file into the Docker container
COPY automatic_model_training.ipynb .

# Expose the port Jupyter will run on
EXPOSE 8888

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Run Jupyter notebook on container startup
CMD ["jupyter", "notebook", "--ip='0.0.0.0'", "--port=8888", "--no-browser", "--allow-root"]