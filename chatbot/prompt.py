from functions import functions_prompt
import json
import os

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

    sentences = []

    for function in matching_functions:
      sentences.append(function['prompt'] + " by setting function to " + str(function['name']))

    function_list = ', '.join(sentences)
    
    function_prompt = "Doogle can do the following: " + function_list + ", nothing other than chatting to the user by setting function to None."
  
  return "This is a chat between a user and an assistant called Doogle. " + function_prompt
