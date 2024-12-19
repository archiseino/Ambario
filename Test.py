import threading
import queue
import pygame
import numpy as np
import cv2
import pyaudio

class VideoRecorder(threading.Thread):
    def __init__(self, name, camindex=0, frameSize=(640, 480), fps=15):
        super(VideoRecorder, self).__init__()
        self.daemon = True
        self.device_index = camindex
        self.fps = fps
        self.frameSize = frameSize
        self.video_cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
        self.latest_frame = None
        self.lock = threading.Lock()
        self.running = False

    def run(self):
        """Background thread to capture frames."""
        self.running = True
        while self.running:
            ret, frame = self.video_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)  # Match Pygame's coordinate system
                with self.lock:
                    self.latest_frame = frame

    def get_frame(self):
        """Fetch the latest frame."""
        with self.lock:
            return self.latest_frame

    def stop(self):
        """Stop video capturing."""
        self.running = False
        self.video_cap.release()

class AudioRecorder(threading.Thread):
    def __init__(self, rate=44100, fpb=1024, channels=1, audio_index=0):
        super(AudioRecorder, self).__init__()
        self.daemon = True
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.latest_volume = 0.0
        self.running = False
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      input_device_index=audio_index,
                                      frames_per_buffer=self.frames_per_buffer)

    def run(self):
        """Background thread to process audio."""
        self.running = True
        while self.running:
            try:
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                self.latest_volume = self.calculate_volume(data)
            except Exception as e:
                print("Audio processing error:", e)

    def calculate_volume(self, data):
        """Calculate RMS volume from audio data."""
        audio_data = np.frombuffer(data, dtype=np.uint8)
        mean_square = np.mean(np.square(audio_data))
        if mean_square == 0:
            return 0.0
        rms = np.sqrt(mean_square)
        return rms / 32768.0  # Normalize to 0-1 range

    def stop(self):
        """Stop audio capturing."""
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()

    # Start audio and video threads
    video_recorder = VideoRecorder("test_video")
    audio_recorder = AudioRecorder()

    video_recorder.start()
    audio_recorder.start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fetch the latest video frame and audio volume
        frame = video_recorder.get_frame()
        volume = audio_recorder.latest_volume

        if frame is not None:
            # Convert the frame to a Pygame surface and render
            frame_surface = pygame.surfarray.make_surface(frame)
            screen.blit(frame_surface, (0, 0))

        # Render volume-based game logic or visual indicators
        # Example: Change background color based on volume
        if volume > 0.5:
            screen.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            screen.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_SUB)

        pygame.display.update()
        clock.tick(30)  # Target 30 FPS

    # Stop the threads
    video_recorder.stop()
    audio_recorder.stop()
    pygame.quit()
