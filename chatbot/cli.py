#!/usr/bin/env python3

import requests
import time
from functions import run_function
from functions import functions_prompt
from functions import grammar_types
import json
from prompt import prompt
import subprocess
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--apihost', type=str, default='192.168.0.131')
parser.add_argument('--debug', type=bool, default=False)
args = parser.parse_args()

debug = args.debug
apihost = args.apihost

def message_request(history, userText, grammar):
  data = {
      'history': history,
      'text': userText,
      'grammar': grammar
  }

  if debug:
    print(data)

  return requests.post(f'http://{apihost}:4000/chat', headers=None, json=data)

while True:
  userText = input("\033[32mYou:\033[0m ")

  history = prompt(userText)

  response = message_request(history, userText, grammar_types())

  if response.status_code != 200:
    print("\033[31mError:\033[0m " + "Something went wrong")
    continue

  try:
    response_json = response.json()
  
    if debug:
      debug_response = response_json.copy()
      debug_response['wavData'] = "WAV DATA"
      print(debug_response)

    llamaText = response_json['llamaText']
    llamaText_json = json.loads(llamaText)
    message = llamaText_json['message']

    if llamaText_json['function'] == "none" or llamaText_json['function'] == "None":
      print("\033[34mDoogle:\033[0m " + message)
      history += "\n\nUser: " + userText + "\nDoogle: " + llamaText

    function_response = run_function(llamaText_json['function'], llamaText_json['option'])

    if function_response != None:
      response = message_request(history, "The function response is: " + str(function_response) + ". Please inform me of it in plain English.", grammar_types())

      response_json = response.json()
      llamaText = response_json['llamaText']
      llamaText_json = json.loads(llamaText)
      message = llamaText_json['message']

      print("\033[34mDoogle:\033[0m " + message)

      history += "\n\nsDoogle: " + llamaText
  
  except:
    continue
