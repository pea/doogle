.PHONY: install-nginx setup-nginx restart-nginx setup-reverse-proxy

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
		location / { \
		proxy_pass http://localhost:8160; \
		add_header 'Access-Control-Allow-Origin' '*'; \
		add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS'; \
		add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range'; \
		add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range'; \
		add_header 'Content-Type' 'video/webm'; \
		add_header 'Cache-Control' 'no-cache, no-store, must-revalidate'; \
		add_header 'Pragma' 'no-cache'; \
		add_header 'Expires' '0'; \
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

install:
	/bin/bash -c "python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"

update:
	zip -r cam.zip . -x "*.git*" -x "*.DS_Store" -x "*.vscode*" -x "*.env*" && scp cam.zip dooglecam@dooglecam.local: && rm cam.zip && ssh dooglecam@dooglecam.local "unzip -o cam.zip && rm cam.zip && chmod +x cam.py run_cam.sh run_stream.sh && sudo reboot"
