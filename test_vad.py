import sounddevice as sd
import numpy as np
import webrtcvad
import time

vad = webrtcvad.Vad(0)  # 0 = максимальная чувствительность
count = 0

def callback(indata, frames, time_info, status):
    global count
    audio = (indata * 32767).astype(np.int16).tobytes()
    if vad.is_speech(audio, 16000):
        print(f'[{count}] VAD: ГОЛОС ОБНАРУЖЕН!')
    else:
        if count % 5 == 0: print(f'[{count}] тишина')
    count += 1

print('--- Говори 5 секунд ---')
with sd.InputStream(samplerate=16000, channels=1, dtype='float32', blocksize=320, callback=callback):
    time.sleep(5)
