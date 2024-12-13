import cv2
import pyaudio
import wave
import threading
import time
import os
import ffmpeg

REC_FOLDER = "recordings/"

# Base Recorder class
class BaseRecorder:
    def __init__(self, recorder):
        self.recorder = recorder
        self.open = True
        self.thread = None

    def start(self):
        """Launches the recording function using a thread."""
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.record)
            self.thread.start()

    def stop(self):
        """Stops the recording and its thread."""
        self.open = False
        if self.thread is not None:
            self.thread.join()

# Video Recorder
class VideoRecorder(BaseRecorder):
    def __init__(self, recorder, video_filename, fourcc="MJPG", frameSize=(640, 480), camindex=0, fps=30):
        super().__init__(recorder)
        self.video_filename = video_filename
        self.device_index = camindex
        self.fps = fps
        self.fourcc = fourcc
        self.video_cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        self.video_writer = cv2.VideoWriter_fourcc(*fourcc)
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, frameSize)

    def record(self):
        """Records video frames."""
        while self.open:
            ret, video_frame = self.video_cap.read()
            if ret:
                self.video_out.write(video_frame)
                cv2.imshow('video_frame', video_frame)

            else:
                break
        self.video_out.release()
        self.video_cap.release()

class AudioRecorder(BaseRecorder):
    def __init__(self, recorder, audio_filename, rate=44100, fpb=1024, channels=1, audio_index=0):
        super().__init__(recorder)
        self.audio_filename = audio_filename
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=audio_index,
            frames_per_buffer=self.frames_per_buffer,
        )
        self.audio_frames = []

    def record(self):
        """Records audio frames."""
        while self.open:
            data = self.stream.read(self.frames_per_buffer)
            self.audio_frames.append(data)
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def saveAudio(self):
        """Saves the recorded audio to a file."""
        waveFile = wave.open(self.audio_filename, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(self.format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(self.audio_frames))
        waveFile.close()

# Main Recorder class
class Recorder:
    def __init__(self, filename):
        os.makedirs(REC_FOLDER, exist_ok=True)
        self.filename = filename
        self.video_filename = REC_FOLDER + filename + "_video.avi"
        self.audio_filename = REC_FOLDER + filename + "_audio.wav"

        self.video_thread = VideoRecorder(self, self.video_filename)
        self.audio_thread = AudioRecorder(self, self.audio_filename)

        if not os.path.exists(self.video_thread.video_filename):
            print("Video file not found!")
        else:
            print(f"Video file exists: {self.video_thread.video_filename}")

        if not os.path.exists(self.audio_thread.audio_filename):
            print("Audio file not found!")
        else:
            print(f"Audio file exists: {self.audio_thread.audio_filename}")


    def startRecording(self):
        self.video_thread.start()
        self.audio_thread.start()

    def stopRecording(self):
        self.video_thread.stop()
        self.audio_thread.stop()

    def saveRecording(self):
        self.audio_thread.saveAudio()
        video_stream = ffmpeg.input(self.video_thread.video_filename)
        audio_stream = ffmpeg.input(self.audio_thread.audio_filename)

        while not os.path.exists(self.audio_thread.audio_filename):
            print("Waiting for audio file to exist...")
            time.sleep(0.1)

        output_file = REC_FOLDER + self.filename + ".mp4"
        ffmpeg.output(video_stream, audio_stream, output_file).run(overwrite_output=True)
        print(f"Recording saved as: {output_file}")

recorder = Recorder("test1")
recorder.startRecording()
time.sleep(10)
recorder.stopRecording()
recorder.saveRecording()
