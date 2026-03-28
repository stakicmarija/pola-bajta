import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import tempfile

SAMPLE_RATE = 16000 
CHANNELS = 1         


class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []
        self._thread = None

    def start(self):
        self.recording = True
        self.frames = []
        self._thread = threading.Thread(target=self._record, daemon=True)
        self._thread.start()

    def stop(self):
        self.recording = False
        if self._thread:
            self._thread.join()

        if not self.frames:
            return None

        audio_data = np.concatenate(self.frames, axis=0)

        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        )
        sf.write(tmp.name, audio_data, SAMPLE_RATE)
        return tmp.name 

    def _record(self):
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32"
        ) as stream:
            while self.recording:
                frame, _ = stream.read(1024)
                self.frames.append(frame)