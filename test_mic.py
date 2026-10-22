import sounddevice as sd
import numpy as np
import time

print('--- Говори в микрофон 15 секунд! ---')
devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f'Проверяю устройство {i}: {dev["name"]}')
        try:
            def cb(indata, frames, t, status):
                vol = np.abs(indata).max()
                if vol > 0.01:
                    print(f'  -> Устройство {i}: ГОЛОС! Громкость {vol:.3f}')
            with sd.InputStream(device=i, channels=1, callback=cb):
                time.sleep(1.5)
        except Exception as e:
            pass
