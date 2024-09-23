FROM llamacpp

ARG MODEL_DOWNLOAD_URL
ARG MMPROJ_DOWNLOAD_URL

RUN apt-get update && apt-get install -y wget

RUN [ ! -d /models ] && mkdir /models || echo "/models directory already exists"
RUN wget -O /models/model.gguf ${MODEL_DOWNLOAD_URL}
RUN if [ -n "${MMPROJ_DOWNLOAD_URL}" ]; then wget -O /models/mmproj.gguf ${MMPROJ_DOWNLOAD_URL}; fi

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]