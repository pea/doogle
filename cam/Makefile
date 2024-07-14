.PHONY: install-nginx setup-nginx restart-nginx setup-reverse-proxy setup-mediamtx start-mediamtx install update configure-autologin configure-dooglecam-startup

configure-autologin:
	@echo "Configuring autologin timeout..."
	@sudo sed -i '/^\[Seat:\*\]/!b;n;c\autologin-user-timeout=0' /etc/lightdm/lightdm.conf
	@echo "Autologin timeout configured."

configure-dooglecam:
	@echo "Configuring Doogle Cam to start at login..."
	@sed -i '/run_cam.sh/d' ~/.bashrc 2>> error.log
	@{ echo "/home/$$(whoami)/run_cam.sh &"; } >> ~/.bashrc 2>> error.log
	@echo "Doogle Cam configured to start at login."
	@sudo chmod +x /home/$$(whoami)/run_cam.sh 2>> error.log
	@sudo chmod +x /home/$$(whoami)/cam.py 2>> error.log

install-nginx:
	@echo "Checking if Nginx is installed..."
	@which nginx || (echo "Installing Nginx..." && sudo apt-get update && sudo apt-get install -y nginx) 2>> error.log

setup-nginx:
	@echo "Setting up Nginx configuration..." 2>> error.log
	@sudo cp conf/nginx.conf /etc/nginx/nginx.conf 2>> error.log
	@sudo nginx -t 2>> error.log && sudo systemctl reload nginx 2>> error.log || echo "Error setting up Nginx. Check error.log for details." >&2
	@echo "Nginx setup complete. Access the stream on port 80 with CORS enabled."
	@sudo systemctl start nginx 2>> error.log

restart-nginx:
	@echo "Restarting Nginx..."
	@sudo systemctl restart nginx
	@echo "Nginx restarted."

setup-reverse-proxy: setup-nginx restart-nginx

setup-mediamtx:
	@sudo apt update 2>> error.log
	@sudo apt upgrade -y 2>> error.log
	@wget https://github.com/bluenviron/mediamtx/releases/download/v1.8.3/mediamtx_v1.8.3_linux_arm64v8.tar.gz 2>> error.log
	@tar -xzvf mediamtx_v1.8.3_linux_arm64v8.tar.gz 2>> error.log
	@sudo mv mediamtx /usr/local/bin/ 2>> error.log
	@sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good 2>> error.log
	@sudo rm mediamtx_v1.8.3_linux_arm64v8.tar.gz 2>> error.log
	@sudo cp conf/mediamtx.yml mediamtx.yml 2>> error.log

start-mediamtx:
	@nohup sudo /usr/local/bin/mediamtx mediamtx.yml &

restart-mediamtx:
	@sudo pkill mediamtx
	@make start-mediamtx

install-python:
	@echo "Creating and activating virtual environment..."
	@sudo rm -rf /home/$$(whoami)/.venv 2>> error.log
	@python3 -m venv /home/$$(whoami)/.venv 2>> error.log
	@sudo chown -R $$(whoami):$$(whoami) /home/$$(whoami)/.venv 2>> error.log
	@bash -c "source /home/$$(whoami)/.venv/bin/activate && pip install -r requirements.txt" 2>> error.log

install:
	make configure-autologin && make configure-dooglecam && make install-python && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y mediainfo python3-lgpio && make setup-mediamtx && make install-nginx && make setup-nginx
