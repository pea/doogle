import requests
import time

history = "This is a chat between a user and a home assistant called Doogle. Doogle does not pretend. Doogle does not use emojis or emoticons. Doogle keeps replies as short as possible."

while True:
    userText = input("\033[32mYou:\033[0m ")

    data = {
        'history': history,
        'text': userText
    }

    response = requests.post('http://192.168.1.131:4000/message', headers=None, json=data)

    if response.status_code == 200:
        last_response_timestamp = time.time()
    else:
        continue

    response_json = response.json()
    llamaText = response_json['llamaText']

    print("\033[34mDoogle:\033[0m " + llamaText)
    
    history += "\n\nUser: " + userText + "\nDoogle: " + llamaText
