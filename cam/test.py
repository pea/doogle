import subprocess

is_running = subprocess.run('pgrep -f mediamtx', shell=True).returncode == 0

print('running' if is_running else 'not running')