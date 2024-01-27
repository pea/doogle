from functions import functions_prompt

def prompt():
  return "This is a chat between a user and an assistant called Doogle. Doogle can do the following: " + functions_prompt() + ", nothing other than chatting to the user by setting function to None."
