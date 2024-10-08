from openwakeword.model import Model
import numpy as np
import os

openwakeword_sensitivity = float(os.getenv('OPENWAKEWORD_SENSITIVITY', 0.5))

class OpenWakeWord:
    def __init__(self): 
      model_paths = self.get_model_files("./wakeword/openwakeword/models")

      self.model = Model(
        wakeword_models=model_paths,
        inference_framework="tflite"
      )

    # @self: OpenWakeWord
    # @data: audio bytes
    # @return: list of wakewords detected sorted by score
    def detected(self, data):
      predictions = self.model.predict(np.frombuffer(data, dtype=np.int16))

      predictions_as_array = []
      for key, prediction in predictions.items():
        predictions_as_array.append((key, prediction))

      predictions_sorted_by_score = sorted(predictions_as_array, key=lambda x: x[1], reverse=True)

      detected = []

      for prediction in predictions_sorted_by_score:
        if prediction[1] > openwakeword_sensitivity:
          detected.append(prediction[0])

      # Alternative spelling of Doogle
      if len(detected) > 0 and detected[0] == "hey_dougal":
        return ["hey_doogle"]

      return detected

    def get_model_files(self, directory):
        filenames = ["hey_dougal"]
        model_files = []

        for dirpath, dirnames, files in os.walk(directory):
            for filename in files:
                if any(name in filename for name in filenames) and filename.endswith('.tflite'):
                    model_files.append(os.path.join(dirpath, filename))

        return model_files
    