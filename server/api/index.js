import express from 'express';
import multer from 'multer';
import axios from 'axios';
import { compile, serializeGrammar } from "@intrinsicai/gbnfgen";

const app = express()
const port = 4000

app.use(express.json());

const storage = multer.memoryStorage();
const upload = multer({ storage: storage }).fields([
  { name: 'audio', maxCount: 1 },
  { name: 'image', maxCount: 1 }
]);

app.get('/', (req, res) => {
  res.send('Hey')
})

app.post('/message', async (req, res) => {
  const history = req.body?.history;
  const text = req.body?.text;
  const grammarTypescript = req.body.grammar;

  const grammar = serializeGrammar(await compile(grammarTypescript, "Response"))

  try {
    const llamaText = await llamaRequest({text, history, grammar});

    res.writeHead(200, {
      'Content-Type': 'application/json'
    });

    res.end(JSON.stringify({
      llamaText: llamaText
    }));
  } catch (error) {
    console.error(error);
    res.status(500).send(error.message);
  }
})

app.post('/chat', upload, async (req, res) => {
  const audio = req.files?.['audio']?.[0]
  const image = req.files?.['image']?.[0]
  const history = req.body.history;
  const userText = req.body?.text;
  const grammarTypescript = req.body?.grammar;

  if (!history) {
    res.status(400).send('Missing history');
    return;
  }

  if (!userText && !audio) {
    res.status(400).send('Missing text or file');
    return;
  }

  const grammar = grammarTypescript ? serializeGrammar(await compile(grammarTypescript, "Response")) : ''

  try {
    let stt = null;
    if (audio) {
      stt = await sttRequest(audio.buffer);
    }

    const inputText = stt ?? userText;

    const maxRetries = 10;
    let retryCount = 0;

    const base64Image = image ? Buffer.from(image.buffer).toString('base64') : null;

    const getLlamaText = async () => {
      const text = await llamaRequest({text: inputText, history, grammar, image: base64Image ?? undefined})

      if (grammar && grammar !== '') {
        const parsedJson = () => {
          try {
            return JSON.parse(text)
          } catch (error) {
            return null
          }
        }

        if (retryCount >= maxRetries) {
          return null
        }

        const jsonResponse = parsedJson();

        if (!jsonResponse) {
          retryCount++;
          return getLlamaText()
        }

        if (jsonResponse?.function === undefined) {
          retryCount++;
          return getLlamaText()
        }

        return jsonResponse
      }

      return text;
    }

    const llamaText = await getLlamaText();

    const isJson = (value) => {
      try {
        JSON.parse(value);
        return true;
      } catch (error) {
        return false;
      }
    }

    const isLlamaTextJson = isJson(llamaText);
    
    if (!llamaText) {
      res.status(500).send('Invalid response from language model');
      return;
    }

    if (isLlamaTextJson && (llamaTextJson?.message === undefined || llamaTextJson?.message === '')) {
      res.status(500).send('Empty response from language model');
      return;
    }

    const emptyWavData = Buffer.from(new Uint8Array()).toString('base64');
    let tts = emptyWavData

    const llamaMessage = llamaText?.message ?? llamaText

    if (!!llamaMessage && llamaMessage !== "") {
      tts = await ttsRequest(llamaMessage)
    }

    res.writeHead(200, {
      'Content-Type': 'application/json'
    });

    res.end(JSON.stringify({
      sttText: inputText,
      llamaText: llamaText,
      wavData: Buffer.from(tts).toString('base64')
    }));
  } catch (error) {
    console.error(error);
    res.status(500).send(error.message);
  }
});

app.post('/tts', async (req, res) => {
  const text = req.body?.text;

  if (!text && text === '') {
    res.status(400).send('Missing text');
    return;
  }

  try {
    const tts = await ttsRequest(text ?? 'ok');

    res.writeHead(200, {
      'Content-Type': 'application/json'
    });

    res.end(JSON.stringify({
      wavData: Buffer.from(tts).toString('base64')
    }));
  } catch (error) {
    console.error(error);
    res.status(500).send(error.message);
  }
});

function sttRequest(fileBuffer) {
  const url = "http://whisper:6060/inference";
  
  const blob = new Blob([fileBuffer], { type: 'audio/wav' });

  const formData = new FormData();
  formData.append('file', blob);

  return axios.post(url, formData)
    .then(response => response.data.text)
    .catch(error => {
      console.error(error);
      return "";
    });
}

async function llamaRequest({text, image, history, grammar}) {
  const prompt = history + '\nUser: ' + text + '\nDoogle:';

  const data = {
    'stream': false,
    'n_predict': 400,
    'temperature': 0.7,
    'stop': ['</s>', 'Doogle:', 'User:'],
    'repeat_last_n': 256,
    'repeat_penalty': 1.18,
    'top_k': 40,
    'top_p': 0.95,
    'min_p': 0.05,
    'tfs_z': 1,
    'typical_p': 1,
    'presence_penalty': 0,
    'frequency_penalty': 0,
    'mirostat': 0,
    'mirostat_tau': 5,
    'mirostat_eta': 0.1,
    'grammar': grammar,
    'n_probs': 0,
    'image_data': image ? [{data: image, id: 10}] : [],
    'cache_prompt': true,
    'api_key': '',
    'slot_id': -1,
    'prompt': prompt
  };

  const response = await axios.post('http://llamacpp:7000/completion', data, {
    headers: {
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Content-Type': 'application/json',
    },
  })

  return response.data.content
}

function ttsRequest(text) {
  const url = 'http://tts:5002/api/tts';
  const params = {
    text: !!text && text !== '' ? text : 'No text provided to text-to-speech api',
    speaker_id: 'p226',
    style_wav: '',
    language_id: ''
  };

  return axios.get(url, {
    params: params,
    responseType: 'arraybuffer'
  })
  .then(response => response.data)
  .catch(error => {
    console.error('Error:', error);
    throw error;
  });
}


const tortoiseTtsRequest = async (text) => {
  const url = 'http://tortoise:6700/stream';
  const params = {
    text: text,
    voice: 'pat2'
  };

  const response = await axios.post(url, params, {
    responseType: 'stream'
  });

  return new Promise((resolve, reject) => {
    const chunks = []
    response.data.on('data', (chunk) => {
      chunks.push(chunk)
    })
    response.data.on('end', () => {
      resolve(Buffer.concat(chunks))
    })
    response.data.on('error', (error) => {
      reject(error)
    })
  })
}

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})
