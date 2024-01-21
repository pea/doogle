import json
import subprocess
import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
functions_json_file = os.path.join(base_dir, 'functions.json')

def run_function(function_name):
  if function_name == "none":
    return

  with open(functions_json_file) as f:
      data = json.load(f)

  if function_name in data:
    function = data[function_name]
    command = function['command']
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout
    
  
def functions_prompt():
  with open(functions_json_file) as f:
      data = json.load(f)

  sentences = []

  for function, details in data.items():
      function_json_string = '{"function": "' + function + '"}'
      sentence = f'{details["prompt"].replace("[function]", function_json_string)}'
      sentences.append(sentence + " by setting function to " + function)

  result = ', '.join(sentences)

  return result

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
}
"""

    return enum_string + interface_string