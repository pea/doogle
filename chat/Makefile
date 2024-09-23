.PHONY: install install-python

configure-autologin:
	@echo "Configuring autologin timeout..."
	@sudo sed -i '/^\[Seat:\*\]/!b;n;c\autologin-user-timeout=0' /etc/lightdm/lightdm.conf
	@echo "Autologin timeout configured."

configure-dooglechat:
	@echo "Configuring Doogle Chat to start at login..."
	@sed -i '/run_chat.sh/d' ~/.bashrc 2>> error.log
	@{ echo "/home/$$(whoami)/run_chat.sh &"; } >> ~/.bashrc 2>> error.log
	@echo "Doogle Chat configured to start at login."
	@sudo chmod +x /home/$$(whoami)/run_chat.sh 2>> error.log
	@sudo chmod +x /home/$$(whoami)/chat.py 2>> error.log

install-python:
	@echo "Creating and activating virtual environment..."
	@sudo rm -rf /home/$$(whoami)/.venv 2>> error.log
	@python3 -m venv /home/$$(whoami)/.venv 2>> error.log
	@sudo chown -R $$(whoami):$$(whoami) /home/$$(whoami)/.venv 2>> error.log
	@bash -c "source /home/$$(whoami)/.venv/bin/activate && pip install -r requirements.txt" 2>> error.log

install-vlc:
	@sudo apt update 2>> error.log
	@sudo apt install -y vlc 2>> error.log	

install:
	make install-python && install-vlc && make configure-dooglechat && configure-autologin