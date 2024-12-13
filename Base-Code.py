import pygame
import cv2
import numpy as np
import sounddevice as sd
import soundfile as sf
import sys
import queue
import argparse

# Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
GRAVITY = 0.5
JUMP_STRENGTH = -10
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Initialize Pygame and camera
def init_camera():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        sys.exit(1)
    return camera

def init_pygame():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Jumping Game with Camera Background")
    return screen

# Set up the audio queue for capturing screams
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

def start_audio_stream():
    try:
        stream = sd.InputStream(callback=callback, channels=1, samplerate=44100)
        stream.start()
        return stream
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def apply_gravity(sprite, platform):
    global sprite_velocity, on_ground
    sprite_velocity += GRAVITY
    sprite.y += sprite_velocity
    if sprite.colliderect(platform):
        sprite.y = platform.y - sprite.height
        sprite_velocity = 0
        on_ground = True
    else:
        on_ground = False

def detect_scream():
    volume = np.linalg.norm(q.get()) / np.sqrt(len(q.get()))
    print(f"Volume: {volume:.2f}")
    return volume > 0.1

def main():
    camera = init_camera()
    screen = init_pygame()
    stream = start_audio_stream()

    ## Recording the Audio
    with sf.SoundFile("test.wav", mode='x', samplerate=44100,
        channels=1, subtype="PCM_16") as file:
        with stream:
            print('#' * 80)
            print('press Ctrl+C to stop the recording')
            print('#' * 80)
            while True:
                file.write(q.get())

    platform = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)
    sprite = pygame.Rect(200, 400, 50, 50)
    global sprite_velocity, on_ground
    sprite_velocity = 10
    on_ground = False

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_filename = 'screaming_sprite_output-demo.avi'
    out = cv2.VideoWriter(video_filename, fourcc, FPS, (SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()
    running = True

    while running:
        ret, frame = camera.read()
        if not ret:
            print("Failed to capture frame.")
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        screen.fill(BLACK)

        if detect_scream() and on_ground:
            sprite_velocity = JUMP_STRENGTH

        apply_gravity(sprite, platform)

        frame_surface = pygame.surfarray.make_surface(frame)
        screen.blit(frame_surface, (0, 0))
        pygame.draw.rect(screen, GREEN, platform)
        pygame.draw.rect(screen, WHITE, sprite)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit(0)

        frame_for_video = np.array(pygame.surfarray.pixels3d(screen))
        frame_for_video = np.transpose(frame_for_video, (1, 0, 2))
        frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)
        out.write(frame_for_video)

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    out.release()
    cv2.destroyAllWindows()
    stream.stop()



if __name__ == "__main__":
    main()