from functions import functions_prompt
from functions import run_function
import json
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

base_prompt = (
    os.getenv("BASE_PROMPT")
    if os.getenv("BASE_PROMPT") is not None
    else "This is a chat between a user and Doogle."
)

base_dir = os.path.dirname(os.path.abspath(__file__))

functions_json_file = os.path.join(base_dir, "functions.json")


def trigger_words_detected(userText):
    detected = False
    with open(functions_json_file) as f:
        functions_json = json.load(f)

    for key, item in functions_json.items():
        function = item
        try:
            trigger_words_array = function["triggerWords"]
            if trigger_words_array is None:
                continue
            for trigger_word in trigger_words_array:
                if trigger_word in userText:
                    detected = True
                    break
        except:
            continue

    return detected


def prompt(userText=None, history=None):
    with open(functions_json_file) as f:
        functions_json = json.load(f)

    prompt = base_prompt

    if trigger_words_detected(userText):
        prompt = (
            prompt
            + "Doogle can use tools by using the function parameter. Doogle ALWAYS sets a function in the function parameter when using a tool."
        )

    if history is not None:
        prompt = prompt + history

    # Handle environment functions
    environment_functions = []
    for function in functions_json.values():
        if function["type"] == "environment":
            function_response = subprocess.run(
                function["command"], shell=True, capture_output=True, text=True
            )
            if function_response is not None:
                environment_functions.append(
                    function["prompt"].replace(
                        "[function_response]", str(function_response.stdout)
                    )
                )
    environment_functions = (
        ".".join(environment_functions) if len(
            environment_functions) > 0 else ""
    )
    environment_functions = (
        environment_functions if len(environment_functions) > 0 else ""
    )
    prompt = prompt + environment_functions

    # Add functions if trigger words are found
    if userText is not None:
        matching_functions = []
        for key, item in functions_json.items():
            function = item
            try:
                trigger_words_array = function["triggerWords"]
                if trigger_words_array is None:
                    continue
                for trigger_word in trigger_words_array:
                    if trigger_word in userText:
                        function["name"] = key
                        matching_functions.append(function)
                        break
            except:
                continue

        # Handle regular functions
        can_do_functions = []
        for function in matching_functions:
            if function["type"] == "command":
                can_do_functions.append(
                    "By setting the function to "
                    + function["name"]
                    + " Doogle can "
                    + function["prompt"]
                )
        can_do_functions = (
            ".".join(can_do_functions) if len(can_do_functions) > 0 else ""
        )
        can_do_functions = can_do_functions if len(
            can_do_functions) > 0 else ""
        prompt = prompt + can_do_functions
        if len(can_do_functions) > 0:
            prompt = prompt

    return prompt
