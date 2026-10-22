import sounddevice as sd
import numpy as np

def callback(indata, frames, time, status):
    vol = np.abs(indata).max()
    if vol > 0.01:
        print(f'Громкость: {vol:.3f}')

with sd.InputStream(channels=1, callback=callback):
    import time; time.sleep(5)
