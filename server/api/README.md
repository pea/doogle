# Doogle API

This is the API for Doogle. The language model (llamaCpp), speech-to-text (whisperCpp), text-to-speech (tts) are interacted with through this API. The API is written in Node.js and uses the Express.js framework.

# Example Request

## Sending wav recording of user

```
curl --location 'http://192.168.1.131:4000/chat' \
--form 'audio=@"test.wav"' \
--form 'history="This is a chat between a user and an assistant called Doogle."' \
--form 'grammar="enum Functions {
  None = \"None\"
}

interface Response {
  message: string;
  function: Functions;
}"'
```

## Sending text from user

```
curl --location 'http://192.168.1.131:4000/chat' \
--form 'text="hello"' \
--form 'history="This is a chat between a user and an assistant called Doogle."' \
--form 'grammar="enum Functions {
  None = \"None\"
}

interface Response {
  message: string;
  function: Functions;
}"'
```