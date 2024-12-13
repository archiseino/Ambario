import cv2
import pyaudio
import wave
import threading
import time
import soundfile as sf
import os
import ffmpeg
import pygame
import cv2
import numpy as np
import sounddevice as sd
import sys
import queue

## Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
GRAVITY = 0.5
JUMP_STRENGTH = -10
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

REC_FOLDER = "recordings/"

# Base Recorder class
class BaseRecorder:
    def __init__(self, recorder):
        self.recorder = recorder
        self.open = True
        self.thread = None
        self.running = False  # Initialize the running attribute to control the thread

    def start(self):
        """Launches the recording function using a thread."""
        ## Both threading success running
        print(f"{self.__class__.__name__} thread started with ID: {self.thread.ident}")
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.record)
            self.thread.start()
            self.running = True


    def stop(self):
        """Stops the recording and its thread."""
        self.open = False
        self.running = False
        if self.thread is not None:
            self.thread.join()

# Video Recorder
class VideoRecorder(BaseRecorder):
    def __init__(self, recorder, video_filename):
        super().__init__(recorder)
        self.video_filename = video_filename
        self.recorder = recorder
        self.game = Game(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera = cv2.VideoCapture(0)
        self.out = cv2.VideoWriter(video_filename, cv2.VideoWriter_fourcc(*'XVID'), 30, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.running = True

    def start(self):
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                print("Failed to capture frame.")
                break

            # Convert the frame to RGB for Pygame and rotate it
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)  # Rotate to match Pygame coordinates

            # Update game logic (detect scream, apply gravity, update sprite)
            self.game.update()

            # Draw game elements and camera feed
            self.game.draw(frame)

            # Write the frame to the output video
            frame_for_video = np.array(self.game.get_screen())
            frame_for_video = np.transpose(frame_for_video, (1, 0, 2))  # Correct orientation
            frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)
            self.out.write(frame_for_video)
            self.game.clock.tick(self.game.FPS)  # Frame rate control

    def stop(self):
        self.running = False
        self.camera.release()
        pygame.quit() ## Clean up video

    def save(self):
        self.out.release()  # Finalize and save the video
        cv2.destroyAllWindows()

class AudioRecorder(BaseRecorder):
    def __init__(self, recorder, audio_filename, rate=44100, channels=1, frames_per_buffer=1024):
        super().__init__(recorder)
        self.audio_filename = audio_filename
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.channels = channels
        self.audio_frames = queue.Queue()
        self.sampling_duration = 0  # Duration for saving to file
        self.scream_threshold = 0.1  # Volume threshold to detect scream
        self.stream = sd.InputStream(callback=self.audio_callback, channels=self.channels, 
                                     samplerate=self.rate, blocksize=self.frames_per_buffer)
    
    def audio_callback(self, indata, frames, time, status):
        """Callback function to process audio frames."""
        if status:
            print(status, file=sys.stderr)
        self.audio_frames.put(indata.copy())
        
    def detect_scream(self):
        """Detect scream based on volume threshold."""
        if len(self.audio_frames) > 0:
            indata = np.concatenate(self.audio_frames, axis=0)
            volume_norm = np.linalg.norm(indata) / np.sqrt(len(indata))
            if volume_norm > self.scream_threshold:
                print("Scream detected!")
                return True
        return False

    def start(self):
        """Start audio recording."""
        self.stream.start()

    def stop(self):
        """Stop audio recording."""
        self.stream.stop()

    def save_audio(self):
        """Save audio data to a WAV file."""
        """Start recording audio."""
        with sf.SoundFile(self.audio_filename, mode='x', samplerate=self.rate,
                          channels=self.channels, subtype='PCM_16') as file:
            # with sd.InputStream(samplerate=self.rate, channels=self.channels,
            #                     callback=self.audio_callback):
            with self.stream:
                print("Recording audio...")
                while self.open:
                    file.write(self.audio_frames.get())

class Recorder:
    def __init__(self, filename):
        os.makedirs(REC_FOLDER, exist_ok=True)
        self.filename = filename
        self.video_filename = REC_FOLDER + "test_video.avi"
        self.audio_filename = REC_FOLDER + "test_audio.wav"

        self.video_thread = VideoRecorder(self, self.video_filename)  # Correct initialization
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



class Game:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.platform = pygame.Rect(0, screen_height - 50, screen_width, 50)
        self.sprite = pygame.Rect(200, 400, 50, 50)
        self.sprite_velocity = 0
        self.on_ground = False
        self.gravity = 0.5
        self.jump_strength = -10
        self.FPS = 60
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Jumping Game with Camera Background")
        self.clock = pygame.time.Clock()

        self.q = queue.Queue()  # Audio capture queue
        self.stream = sd.InputStream(callback=self.audio_callback, channels=1, samplerate=44100)
        self.stream.start()

    def audio_callback(self, indata, frames, time, status):
        """Callback function to capture audio input"""
        if status:
            print(status, file=sys.stderr)
        self.q.put(indata.copy())

    def detect_scream(self):
        """Detects if the user is screaming based on audio volume"""
        volume = np.linalg.norm(self.q.get()) / np.sqrt(len(self.q.get()))
        if volume > 0.1:
            return True
        return False

    def apply_gravity(self):
        """Applies gravity to the sprite"""
        self.sprite_velocity += self.gravity
        self.sprite.y += self.sprite_velocity

        if self.sprite.colliderect(self.platform):
            self.sprite.y = self.platform.y - self.sprite.height
            self.sprite_velocity = 0
            self.on_ground = True
        else:
            self.on_ground = False

    def update(self):
        """Main update function to handle jump and gravity"""
        if self.detect_scream() and self.on_ground:
            self.sprite_velocity = self.jump_strength  # Make the sprite jump
        self.apply_gravity()

    def draw(self, frame):
        """Draws the game elements (sprite, platform, camera feed)"""
        frame_surface = pygame.surfarray.make_surface(frame)
        self.screen.blit(frame_surface, (0, 0))  # Background as the camera frame
        pygame.draw.rect(self.screen, (0, 255, 0), self.platform)  # Draw platform
        pygame.draw.rect(self.screen, (255, 255, 255), self.sprite)  # Draw sprite
        pygame.display.update()

    def get_screen(self):
        """Returns the current Pygame screen surface for video output"""
        return pygame.surfarray.pixels3d(self.screen)

# Assuming we have all the necessary classes (Recorder, VideoRecorder, AudioRecorder, Game)
# Initialize the Recorder instance with a filename
recorder = Recorder("test1")

# Start the recording process (video and audio)
recorder.startRecording()

# Run the recording for a set duration (e.g., 10 seconds)
# Alternatively, you can replace this with a manual stop based on some condition or event
time.sleep(10)

# Stop the recording after 10 seconds (or other conditions)
recorder.stopRecording()

# Save the final recording, merging video and audio
recorder.saveRecording()
