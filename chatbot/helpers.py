import json

def is_json(data):
    try:
        json.loads(data)
        return True
    except ValueError as e:
        return False