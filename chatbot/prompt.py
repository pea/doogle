from functions import functions_prompt
from functions import run_function
import json
import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))

functions_json_file = os.path.join(base_dir, 'functions.json')

def prompt(userText = None):
  with open(functions_json_file) as f:
      functions_json = json.load(f)

  prompt = "This is a chat between a user and Doogle.\n"

  # Handle environment functions
  environment_functions = []
  for function in functions_json.values():
    if function['type'] == 'environment':
      function_response = subprocess.run(function['command'], shell=True, capture_output=True, text=True)
      if function_response is not None:
        environment_functions.append(function['prompt'].replace("[function_response]", str(function_response.stdout)))
  environment_functions = '.\n'.join(environment_functions) if len(environment_functions) > 0 else ""
  environment_functions = environment_functions if len(environment_functions) > 0 else ""
  prompt = prompt + environment_functions
  
  # Add functions if trigger words are found
  if userText is not None:    
    matching_functions = []
    for key, item in functions_json.items():
      function = item
      try:
        trigger_words_array = function['triggerWords']
        if trigger_words_array is None:
          continue
        for trigger_word in trigger_words_array:
          if trigger_word in userText:
            function['name'] = key
            matching_functions.append(function)
            break
      except:
        continue

    # Handle regular functions
    can_do_functions = []
    for function in matching_functions:
      if function['type'] == 'command':
        can_do_functions.append("Doogle can " + function['prompt'])
    can_do_functions = '.\n'.join(can_do_functions) if len(can_do_functions) > 0 else ""
    can_do_functions = can_do_functions if len(can_do_functions) > 0 else ""
    prompt = prompt + can_do_functions
    if len(can_do_functions) > 0:
      prompt = prompt + "\n"

    # Handle function examples
    function_examples = []
    for function in matching_functions:
      if function['type'] == 'command':
        optionExample = function['optionExample'] if 'optionExample' in function else "None"
        function_examples.append("User: " + function['prompt'] + ". \nDoogle: {'message': '', 'function': '" + function["name"] + "', 'options': '" + optionExample + "'}\n")
    function_examples = ''.join(function_examples)
    function_examples = function_examples + "\n" if len(function_examples) > 0 else ""
    if len(function_examples) > 0:
      prompt = prompt + function_examples

  return prompt
