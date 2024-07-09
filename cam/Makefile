.PHONY: install-nginx setup-nginx restart-nginx setup-reverse-proxy setup-mediamtx start-mediamtx install update

# Define the path to your Nginx configuration for the stream
NGINX_CONF=/etc/nginx/sites-available/mjpeg_stream

install-nginx:
	@echo "Checking if Nginx is installed..."
	@which nginx || (echo "Installing Nginx..." && sudo apt-get update && sudo apt-get install -y nginx)

setup-nginx: install-nginx
	@echo "Setting up Nginx configuration..."
	@sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
	# Remove the default Nginx site to prevent conflicts
	@sudo rm -f /etc/nginx/sites-enabled/default
	# Define the stream configuration with the correct port and add CORS headers
	@echo "server { \
		listen 80; \
		server_name localhost; \
		location /stream/ { \
			proxy_pass http://localhost:8889/stream/; \
			proxy_http_version 1.1; \
			proxy_set_header Host \$host; \
			proxy_set_header X-Real-IP \$remote_addr; \
			proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; \
			proxy_set_header X-Forwarded-Proto \$scheme; \
		} \
		}" | sudo tee $(NGINX_CONF)
	# Ensure the mjpeg_stream configuration is enabled
	@sudo ln -sf $(NGINX_CONF) /etc/nginx/sites-enabled/mjpeg_stream
	# Reload Nginx to apply changes
	@sudo nginx -t && sudo systemctl reload nginx
	@echo "Nginx setup complete. Access the stream on port 80 with CORS enabled."

restart-nginx:
	@echo "Restarting Nginx..."
	@sudo systemctl restart nginx
	@echo "Nginx restarted."

setup-reverse-proxy: setup-nginx restart-nginx

setup-mediamtx:
	sudo apt update
	sudo apt upgrade -y
	wget https://github.com/bluenviron/mediamtx/releases/download/v1.8.3/mediamtx_v1.8.3_linux_arm64v8.tar.gz
	tar -xzvf mediamtx_v1.8.3_linux_arm64v8.tar.gz
	sudo mv mediamtx /usr/local/bin/
	sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good
	sudo rm mediamtx_v1.8.3_linux_arm64v8.tar.gz

start-mediamtx:
	@nohup sudo /usr/local/bin/mediamtx mediamtx.yml &

restart-mediamtx:
	@sudo pkill mediamtx
	@make start-mediamtx

install:
	/bin/bash -c "python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y mediainfo python3-lgpio && make setup-mediamtx

update:
	zip -r cam.zip . -x "*.git*" -x "*.DS_Store" -x "*.vscode*" -x "*.env*" && scp cam.zip dooglecam@dooglecam.local: && rm cam.zip && ssh dooglecam@dooglecam.local "unzip -o cam.zip && rm cam.zip && chmod +x cam.py run_cam.sh run_stream.sh && sudo reboot"
