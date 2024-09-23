import express from 'express';
import multer from 'multer';
import { spawn } from 'child_process';
import fs from 'fs';

const app = express()
const port = 7000

app.use(express.json());

const storage = multer.memoryStorage();
const upload = multer({ storage: storage }).fields([
  { name: 'audio', maxCount: 1 },
  { name: 'image', maxCount: 1 }
]);

app.get('/', (req, res) => {
  res.send('Hey')
})

app.post('/message', upload, async (req, res) => {
  const image = req.files?.['image']?.[0]
  const userText = req.body?.text;


  try {
    if (image) {
      fs.writeFileSync('/app/image.jpg', image.buffer);
    }

    const getLlamaText = async () => {
      return new Promise((resolve, reject) => {
        const command = spawn(`./llama-minicpmv-cli`, [
          '-m', '/models/model.gguf',
          '--mmproj', '/models/mmproj.gguf',
          '-c', '4096',
          '--temp', '0.1',
          '--top-p', '0.8',
          '--top-k', '100',
          '--repeat-penalty', '1.05',
          '--image', '/app/image.jpg',
          '-p', 'What is in the image?'
        ]);

        let data = '';
        command.stdout.on('data', (chunk) => {
          data += chunk;
        });

        command.stderr.on('data', (chunk) => {
          console.error('stderr:', chunk.toString());
        });

        command.on('error', (error) => {
          console.error('Failed to start subprocess:', error);
          reject(error);
        });

        command.on('close', (code) => {
          if (code === 0) {
            resolve(data);
          } else {
            reject(new Error(`Failed with code ${code}`));
          }
        });

        command.on('exit', (code, signal) => {
          if (code !== null) {
            console.log(`Process exited with code: ${code}`);
          } else {
            console.log(`Process terminated with signal: ${signal}`);
          }
        });
      });
    }

    const llamaText = await getLlamaText();

    res.writeHead(200, {
      'Content-Type': 'application/json'
    });

    res.end(JSON.stringify({
      llamaText,
    }));
  } catch (error) {
    console.error(error);
    res.status(500).send(error.message);
  }
});

async function llamaRequest({text, image}) {
  return 'test response'
}

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})
