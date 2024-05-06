import pvporcupine
import numpy as np

class Porcupine:
    def __init__(self, ACCESS_KEY):
      self.wakewords = ["./wakeword/porcupine/hey-dougal_en_raspberry-pi_v3_0_0.ppn"]
      self.porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=self.wakewords
      )

    # @self: Porcupine
    # @data: audio bytes
    # @return: list of wakewords detected sorted by score
    def detected(self, data):
      keyword_index = self.porcupine.process(np.frombuffer(data, dtype=np.int16))

      if keyword_index == 0:
        return ["hey_doogle"]
      else:
        return []