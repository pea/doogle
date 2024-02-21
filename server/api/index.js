import express from 'express';
import multer from 'multer';
import axios from 'axios';
import { compile, serializeGrammar } from "@intrinsicai/gbnfgen";

const app = express()
const port = 4000

app.use(express.json());

const storage = multer.memoryStorage();
const upload = multer({ storage: storage }).single('audio');

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
  const file = req?.file;
  const history = req.body.history;
  const userText = req.body?.text;
  const grammarTypescript = req.body?.grammar;

  if (!history) {
    res.status(400).send('Missing history');
    return;
  }

  if (!userText && !file) {
    res.status(400).send('Missing text or file');
    return;
  }

  const grammar = grammarTypescript ? serializeGrammar(await compile(grammarTypescript, "Response")) : ''

  try {
    let stt = null;
    if (file) {
      stt = await sttRequest(file.buffer);
    }

    const inputText = stt ?? userText;

    const retries = 3;
    let numRetries = 0;

    const getLlamaText = async () => {
      const text = await llamaRequest({text: inputText, history, grammar})

      if (grammar && grammar !== '') {
        const parsedJson = () => {
          try {
            return JSON.parse(text);
          } catch (error) {
            return null;
          }
        }

        if (numRetries >= retries) {
          console.error('Retries exceeded');
          return null;
        }

        if (!parsedJson() && numRetries < retries) {
          numRetries++;
          console.log('Retrying...');
          return getLlamaText();
        } else {
          return parsedJson();
        }
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
      res.status(500).send('Invalid response from LLM');
      return;
    }

    if (isLlamaTextJson && (llamaTextJson?.message === undefined || llamaTextJson?.message === '')) {
      res.status(500).send('Empty response from LLM');
      return;
    }

    const tts = await ttsRequest(llamaText?.message ?? llamaText);

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

  if (!text) {
    res.status(400).send('Missing text');
    return;
  }

  try {
    const tts = await ttsRequest(text);

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
  const url = "http://192.168.1.131:6060/inference";
  
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

async function llamaRequest({text, history, grammar}) {
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
    'image_data': [],
    'cache_prompt': true,
    'api_key': '',
    'slot_id': -1,
    'prompt': prompt
  };

  const response = await axios.post('http://192.168.1.131:7000/completion', data, {
    headers: {
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Content-Type': 'application/json',
    },
  })

  return response.data.content
}

function ttsRequest(text) {
  const url = 'http://192.168.1.131:5002/api/tts';
  const params = {
    text: text,
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
  const url = 'http://192.168.1.131:6700/stream';
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
