import pyaudio
import threading
import numpy as np
import wave

class AudioRecorder(threading.Thread):
    """
    Sepearete thread for recording audio. since the Nature of Python that can't do recording and processing at the same time.
    filename: str, default="output/output.wav" - The name of the file to save the audio recording.
    rate: int, default=44100 - The sampling rate of the audio.
    frames_per_buffer: int, default=1024 - The number of frames per buffer.
    """
    def __init__(self, filename="output/output.wav", rate=44100, frames_per_buffer=1048):
        super(AudioRecorder, self).__init__()
        self.filename = filename
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.audio_frames = []
        self.volume = 0
        self.running = False

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.frames_per_buffer)

    def run(self):
        """
        Background thread to record audio. in this steps we do the calculation of the volume of the audio.
        using the formula: volume = np.linalg.norm(audio_data) / np.sqrt(len(audio_data))
        which is the RMS value of the audio data. 
        """
        self.running = True
        while self.running:
            try:
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                self.audio_frames.append(data)

                # Calculate volume
                audio_data = np.frombuffer(data, dtype=np.int16)
                if len(audio_data) == 0 or np.all(audio_data == 0):
                    self.volume = 0
                else:
                    self.volume = np.linalg.norm(audio_data) / np.sqrt(len(audio_data))

            except Exception as e:
                print("Audio recording error:", e)

    def stop(self):
        """
        Stops the audio recording.
        """
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def save(self):
        """
        Saves the recorded audio to a WAV file.
        """
        with wave.open(self.filename, 'wb') as wavefile:
            wavefile.setnchannels(1)
            wavefile.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wavefile.setframerate(self.rate)
            wavefile.writeframes(b''.join(self.audio_frames))

