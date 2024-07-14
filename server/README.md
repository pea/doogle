# Doogle Server

## Install

#### Prerequisites

- Nvidia GPU and the necessary drivers installed, including Nvidia Container Toolkit
- Docker

1. Install [Nvidia drivers](https://www.nvidia.co.uk/Download/index.aspx?lang=en-uk)
2. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
3. Clone the repository to your server
4. Edit the dockerfiles as necessary (such as changing the models used, cuda versions, etc.)
5. Run `docker compose up -d`
6. Open port 4000 on your server