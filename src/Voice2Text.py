import whisper
import torch
import gc
import noisereduce as nr
import soundfile as sf
import numpy as np
import os

model_name = "medium"
#model_name = "large-v3"

model = None

def reload_model():
       
	global model
	gc.collect()
	torch.cuda.empty_cache()
	model = whisper.load_model(model_name)
     
options = {
    'verbose': False,
	#'language':'zh',
}

def denoise(path):
        data, rate = sf.read(path)
        denoised = None
        for i in range(data.shape[1]):
            mono = data.T[i].T
            result = nr.reduce_noise(y=mono, sr=rate)
            if denoised is None:
                denoised = result
            else:
                denoised = np.vstack((denoised, result))
            denoised = denoised.T
        return denoised, rate

def transcribe(path):
	text = {}
	global model
	global options
	if model is None:
		reload_model()
	target, rate = denoise(path)
	sf.write("temp.wav", target, rate)
	result = model.transcribe("temp.wav", **options)
	os.remove("temp.wav")
	for i in result["segments"]:
		text[i['start']] = i['text']
	return text

