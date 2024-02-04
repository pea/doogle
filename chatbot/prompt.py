from functions import functions_prompt
from functions import run_function
import json
import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))

functions_json_file = os.path.join(base_dir, 'functions.json')

def prompt(userText = None):
  function_prompt = ""
  if userText is not None:
    with open(functions_json_file) as f:
      data = json.load(f)
    
    matching_functions = []
    for key, item in data.items():
      function = item
      trigger_words_array = function['triggerWords']
      if trigger_words_array is None:
        continue
      for trigger_word in trigger_words_array:
        if trigger_word in userText:
          function['name'] = key
          matching_functions.append(function)
          break

    function_array = []

    for function in matching_functions:
      if function['type'] == 'command':
        function_array.append("Doogle can " + function['prompt'] + " by setting function to " + str(function['name']) + " with option set to what the user asked for")
      elif function['type'] == 'environment':
        function_response = run_function(function['name'])
        if function_response is not None:
          function_array.append(function['prompt'].replace("[function_response]", function_response))

    function_list = '. '.join(function_array)
    
    if len(function_list) > 0:
      function_prompt = function_list
    else:
      function_prompt = ""
  
  return "This is a chat between a user and an assistant called Doogle. " + function_prompt + ". Doogle sets function to None if just chatting"
