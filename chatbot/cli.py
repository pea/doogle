#!/usr/bin/env python3

import requests
import time
from functions import run_functions
import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
functions_json_file = os.path.join(base_dir, 'functions.json')

def functions_prompt():
  with open(functions_json_file) as f:
      data = json.load(f)

  sentences = []

  for function, details in data.items():
      function_json_string = '{"function": "' + function + '"}'
      sentence = f'{details["prompt"].replace("[function]", function_json_string)}'
      sentences.append(sentence)

  result = ', '.join(sentences)

  return result

def functions_defaults_prompt():
  with open(functions_json_file) as f:
      data = json.load(f)

  sentences = []

  for function, details in data.items():
      function_json_string = '{"function": "' + function + '"}'
      sentence = function + " is false by default"
      sentences.append(sentence)

  result = ', '.join(sentences)

  return result

def functions_types():
  with open(functions_json_file) as f:
    data = json.load(f)

  function_types = []

  for function, details in data.items():
    function_type = f'{function}: boolean'
    function_types.append(function_type)

  result = '; '.join(function_types)

  return result

history = "This is a chat between a user and a home assistant called Doogle. Doogle does not pretend. Doogle does not use emojis or emoticons. Doogle can do the following functions: " + functions_prompt() + ". " + functions_defaults_prompt()

print(history)

while True:
    userText = input("\033[32mYou:\033[0m ")

    data = {
        'history': history,
        'text': userText,
        'functions': functions_types()
    }

    response = requests.post('http://192.168.1.131:4000/message', headers=None, json=data)

    if response.status_code == 200:
        last_response_timestamp = time.time()
    else:
        continue

    try:
      response_json = response.json()
      llamaText = response_json['llamaText']
      llamaText_json = json.loads(llamaText)
      message = llamaText_json['message']
      print("\033[34mDoogle:\033[0m " + message)
      run_functions(llamaText_json)
      history += "\n\nUser: " + userText + "\nDoogle: " + message
    except:
      continue


   
