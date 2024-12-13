import threading
import pyaudio
import wave
import cv2
import pygame
import numpy as np
import ffmpeg

## Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
GRAVITY = 0.5
JUMP_STRENGTH = -10
FPS = 60
JUMP_THRESHOLD = 1000  # Adjust this based on your microphone sensitivity

# Set up screen and window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jumping Game with Camera Background")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Platform setup
platform = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)  # Platform at the bottom of the screen
platform_speed = 10  # Speed of platform movement

# Player setup (the jumping character)
sprite = pygame.Rect(200, 400, 50, 50)  # Starting position (centered on the platform)
sprite_velocity = 10
gravity = 0.5  # Gravity force
jump_strength = -15  # Jumping strength
on_ground = False # Flag to check if the sprite is on the ground

def detect_scream(volume, threshold=0.1):
    print(f"Volume: {volume:.2f}")
    return volume > threshold

class AudioRecorder(threading.Thread):
    def __init__(self, filename, rate=44100, fpb=2940, channels=1, audio_index=0):
        super().__init__()
        self.filename = filename
        self.rate = rate
        self.frames_per_buffer = fpb
        self.channels = channels
        self.format = pyaudio.paInt16
        self.audio_frames = []
        self.volume = 0  # Current volume level
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=audio_index,
            frames_per_buffer=self.frames_per_buffer,
        )
        self.running = False

    def run(self):
        """Continuously record audio and calculate volume."""
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
        """Stop the audio recording."""
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def save_audio(self):
        """Save the recorded audio to a file."""
        with wave.open(self.filename, 'wb') as wavefile:
            wavefile.setnchannels(self.channels)
            wavefile.setsampwidth(self.audio.get_sample_size(self.format))
            wavefile.setframerate(self.rate)
            wavefile.writeframes(b''.join(self.audio_frames))

if __name__ == "__main__":
    # File names for audio and video
    video_filename = "output.avi"
    audio_filename = "output.wav"
    final_filename = "final_output.mp4"

    # Initialize video capture
    video_cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    video_out = cv2.VideoWriter(video_filename, fourcc, 15, (640, 480))

    # Start audio recording in a thread
    audio_recorder = AudioRecorder(audio_filename)
    audio_recorder.start()

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Capture a video frame
        ret, frame = video_cap.read()
        if ret:

            # Convert the frame to RGB and rotate it for Pygame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)  # Rotate to match Pygame coordinates

            # Clear the screen with black before drawing
            screen.fill([0, 0, 0])

            # Get the current volume level
            current_volume = audio_recorder.volume

            # Jump logic based on volume
            if detect_scream(audio_recorder.volume, threshold=1000) and on_ground:
                sprite_velocity = JUMP_STRENGTH
                on_ground = False

            # Gravity and platform collision
            sprite.y += sprite_velocity
            sprite_velocity += GRAVITY
            if sprite.colliderect(platform):  # Collision with platform
                sprite.y = platform.y - sprite.height
                sprite_velocity = 0
                on_ground = True

            # Draw the camera feed
            frame_surface = pygame.surfarray.make_surface(frame)
            screen.blit(frame_surface, (0, 0))  # Draw the camera frame as background

            # Render the frame in Pygame
            screen.blit(frame_surface, (0, 0))

            # Draw the platform (on top of the camera feed)
            pygame.draw.rect(screen, GREEN, platform)

            # Draw the player (the jumping sprite)
            pygame.draw.rect(screen, WHITE, sprite)


            # Convert Pygame surface to a format OpenCV understands (RGB -> BGR)
            frame_for_video = np.array(pygame.surfarray.pixels3d(screen))  # Get the screen pixels
            frame_for_video = np.transpose(frame_for_video, (1, 0, 2))  # Transpose to correct orientation
            frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)  # Convert to BGR for OpenCV

            # Write the frame to the video output file
            # out.write(frame_for_video)

            # Write the frame to the video file
            video_out.write(frame_for_video)

            pygame.display.update()


        # Control frame rate
        clock.tick(15)

    # Cleanup
    video_cap.release()
    video_out.release()
    audio_recorder.stop()
    audio_recorder.save_audio()
    pygame.quit()

    # Merge audio and video using ffmpeg
    video_stream = ffmpeg.input(video_filename)
    audio_stream = ffmpeg.input(audio_filename)
    output = ffmpeg.output(video_stream, audio_stream, final_filename, vcodec='copy', acodec='aac', strict='experimental')
    ffmpeg.run(output)
