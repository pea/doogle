FROM llamacpp

WORKDIR /app

# Install node and packages
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

ARG MODEL_DOWNLOAD_URL
ARG MMPROJ_DOWNLOAD_URL

RUN [ ! -d /models ] && mkdir /models || echo "/models directory already exists"
RUN wget -O /models/model.gguf ${MODEL_DOWNLOAD_URL}
RUN wget -O /models/mmproj.gguf ${MMPROJ_DOWNLOAD_URL}

COPY . /app
RUN npm install

ENTRYPOINT ["npm", "start"]