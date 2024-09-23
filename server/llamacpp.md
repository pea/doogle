
# Llama.cpp Docker Containers

## Base Images
- [llamacpp](#llamacpp-image)
- [llamacpp-server](llamaCppServer/Dockerfile)
- [minicpm-server](minicpmServer/Dockerfile)


## llamacpp Image
The llamacpp image should be built from the Dockerfile in the llamaCpp directory. This image builds the `main` executable and should be used as a base image for the server image.
Build it with:
```bash
docker build -t llamacpp ./llamaCpp
```

## llamacpp-server Image
The llamacpp-server image downloads the models and runs `./llama-server` on port 7000.
Built it with:
```bash
docker build -t llamacpp-server ./llamaCppServer
```

It can then be used in docker-compose.yaml like so:
```yaml
modelname:
  image: llamacpp-server
  build:
    context: './llamaCppServer'
    dockerfile: 'Dockerfile'
    args:
      MODEL_DOWNLOAD_URL: https://huggingface.co...
      MMPROJ_DOWNLOAD_URL: https://huggingface.co... # Optional
  ports:
    - '7000:7000'
  restart: 'always'
  networks:
    - network
  deploy:
    resources:
      reservations:
        devices:
          - driver: 'nvidia'
            count: 'all'
            capabilities:
              - 'gpu'   
```

## mobilevlm-server Image
The mobilevlm-server can be used in the same way as llamacpp-server but instead runs a Node.js server on port 7000 and the API is slightly different.