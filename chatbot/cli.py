#!/usr/bin/env python3

import requests
import time
from functions import run_function
from functions import functions_prompt
from functions import grammar_types
import json

history = "This is a chat between a user and an assistant called Doogle. Doogle can do the following: " + functions_prompt() + ", nothing other than chatting to the user by setting function to None."

print(history)

while True:
    userText = input("\033[32mYou:\033[0m ")

    data = {
        'history': history,
        'text': userText,
        'grammar': grammar_types()
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

      run_function(llamaText_json['function'])
      
      history += "\n\nUser: " + userText + "\nDoogle: " + llamaText
    except:
      continue


   
