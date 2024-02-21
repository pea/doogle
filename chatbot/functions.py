import json
import subprocess
import json
import os
import threading

base_dir = os.path.dirname(os.path.abspath(__file__))
functions_json_file = os.path.join(base_dir, 'functions.json')
stop_thread = threading.Event()
function_thread = None

def run_function(function_name, option=None):
    global function_thread

    # If function_thread exists and is alive, stop it
    if function_thread is not None and function_thread.is_alive():
        stop_thread.set()
        function_thread.join()

    # Reset the stop_thread event
    stop_thread.clear()

    # Start a new function_thread
    function_thread = threading.Thread(target=execute_function, args=(function_name, option), name='function_thread')
    function_thread.start()

def execute_function(function_name, option):
    if function_name == "none":
      return

    with open(functions_json_file) as f:
      data = json.load(f)

    if function_name in data:
      function = data[function_name]
      command = function['command']
      if option:
        command = command.replace("[option]", str(option))
      result = subprocess.run(command, shell=True, capture_output=True, text=True)
      return result.stdout

    if stop_thread.is_set():
        return
  
def functions_prompt():
  with open(functions_json_file) as f:
      data = json.load(f)

  sentences = []

  for function, details in data.items():
      function_json_string = '{"function": "' + function + '"}'
      sentence = f'{details["prompt"].replace("[function]", function_json_string)}'
      sentences.append(sentence + " by setting function to '" + function + "'")

  result = ', '.join(sentences)

  return result

def trigger_words_detected(userText):
  with open(functions_json_file) as f:
    data = json.load(f)

  matching_functions = []
  for key, item in data.items():
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

  return matching_functions

def grammar_types():
  with open(functions_json_file) as f:
    data = json.load(f)

    enum_string = "enum Functions {\n"
    enum_string += "  None = \"None\",\n"
    for function in data.keys():
        enum_string += f"  {function} = \"{function}\",\n"
    enum_string += "}\n"

    interface_string = """
interface Response {
  message: string;
  function: Functions;
  option: string;
}
"""

    return enum_string + interface_string

def get_function(function_name):
  with open(functions_json_file) as f:
    data = json.load(f)

  if function_name in data:
    return data[function_name]

  return None

def get_functions_by_type(function_type):
  with open(functions_json_file) as f:
    data = json.load(f)

  function_dict = {}
  for function_name, function in data.items():
    if function['type'] == function_type:
      function_dict[function_name] = function

  return function_dict