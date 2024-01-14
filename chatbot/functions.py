import json
import subprocess
import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
functions_json_file = os.path.join(base_dir, 'functions.json')

def run_functions(json_text):
  json_without_message = json_text.copy()
  del json_without_message['message']

  try:
    with open(functions_json_file) as f:
      data = json.load(f)

    for function, details in data.items():
      if function in json_text:
        if json_text[function] == True:
          subprocess.run(details['command'], shell=True)
          print(f'Running {function} function')
  except:
    return