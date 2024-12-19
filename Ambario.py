"""
Note: There's no way you can use the pygame and opencv to record the frame with threading 
since the natrue of the different looping on the both methods (pygame loop vs opencv loop)
If there's some method to do this efficiently, I guess we can do that better
"""

import pygame
import cv2
import numpy as np
import pyaudio
import wave
import threading

class AudioRecorder(threading.Thread):
    def __init__(self, filename="output.wav", rate=44100, frames_per_buffer=1024):
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
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def save(self):
        with wave.open(self.filename, 'wb') as wavefile:
            wavefile.setnchannels(1)
            wavefile.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wavefile.setframerate(self.rate)
            wavefile.writeframes(b''.join(self.audio_frames))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("Jumping Game with Camera Background")
        self.clock = pygame.time.Clock()
        self.running = True

        self.platform = pygame.Rect(0, 430, 640, 50)
        self.sprite = pygame.Rect(200, 400, 50, 50)
        self.sprite_velocity = 10
        self.on_ground = False

        self.video_cap = cv2.VideoCapture(0)
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.out = cv2.VideoWriter("output.avi", self.fourcc, 15, (640, 480))

        self.audio_recorder = AudioRecorder()

    def detect_scream(self, volume, threshold=1000):
        return volume > threshold

    def apply_gravity(self):
        self.sprite.y += self.sprite_velocity
        self.sprite_velocity += 0.5
        if self.sprite.colliderect(self.platform):
            self.sprite.y = self.platform.y - self.sprite.height
            self.sprite_velocity = 0
            self.on_ground = True
        else:
            self.on_ground = False

    def run(self):
        self.audio_recorder.start()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            ret, frame = self.video_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                self.screen.fill([0, 0, 0])
                frame_surface = pygame.surfarray.make_surface(frame)
                self.screen.blit(frame_surface, (0, 0))

                current_volume = self.audio_recorder.volume
                if self.detect_scream(current_volume) and self.on_ground:
                    self.sprite_velocity = -10
                    self.on_ground = False

                self.apply_gravity()

                pygame.draw.rect(self.screen, (0, 255, 0), self.platform)
                pygame.draw.rect(self.screen, (255, 255, 255), self.sprite)

                pygame.display.update()

                # Convert Pygame surface to a format OpenCV understands (RGB -> BGR)
                frame_for_video = np.array(pygame.surfarray.pixels3d(self.screen))
                frame_for_video = np.transpose(frame_for_video, (1, 0, 2))
                frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)
                self.out.write(frame_for_video)

                self.clock.tick(15)

        self.audio_recorder.stop()
        self.audio_recorder.save()
        self.video_cap.release()
        self.out.release()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()