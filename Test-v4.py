import pygame
import cv2
import numpy as np
import sounddevice as sd
import sys
import queue

# Initialize Pygame and camera
camera = cv2.VideoCapture(0)
pygame.init()

## Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
GRAVITY = 0.5
JUMP_STRENGTH = -10
FPS = 60

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
# y_velocity = 0

# Set up the clock
clock = pygame.time.Clock()

# Set up the audio queue for capturing screams
q = queue.Queue()

def callback(indata, frames, time, status):
    """Callback function to capture audio input"""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

# Start audio capture stream
stream = sd.InputStream(callback=callback, channels=1, samplerate=44100)
stream.start()

# Gravity-based movement
def apply_gravity():
    global sprite_velocity, on_ground
    sprite_velocity += GRAVITY
    sprite.y += sprite_velocity

    # Check if sprite hits the ground (platform)
    if sprite.colliderect(platform):
        sprite.y = platform.y - sprite.height
        sprite_velocity = 0  # Stop falling once on the platform
        on_ground = True  # Set the flag to true when sprite is on the ground
    else:
        on_ground = False  # If not on platform, reset flag

## Detect if the user is screaming
def detect_scream():
    volume = np.linalg.norm(q.get()) / np.sqrt(len(q.get()))
    print(f"Volume: {volume:.2f}")
    if volume > 0.1:  # Threshold for scream detection
        return True
    return False

## OpenCV Video writter setup
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_filename = 'output/screaming_sprite_output-demo.avi'
out = cv2.VideoWriter(video_filename, fourcc, FPS, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Game loop flag
running = True

while running:
    ret, frame = camera.read()

    if not ret:
        print("Failed to capture frame.")
        break

    # Convert the frame to RGB and rotate it for Pygame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)  # Rotate to match Pygame coordinates

    # Clear the screen with black before drawing
    screen.fill([0, 0, 0])

    ## Detect scream and trigger sprite jump if on the ground
    if detect_scream() and on_ground:
        sprite_velocity = JUMP_STRENGTH  # Set jump velocity

    ## Apply gravity to the sprite
    apply_gravity()

    # Draw the camera feed
    frame_surface = pygame.surfarray.make_surface(frame)
    screen.blit(frame_surface, (0, 0))  # Draw the camera frame as background

    # Draw the platform (on top of the camera feed)
    pygame.draw.rect(screen, GREEN, platform)

    # Handle jumping (only allow jumping if on the platform)
    # if is_jumping:
    #     y_velocity += gravity  # Apply gravity to velocity
    #     player.y += y_velocity  # Move the player according to the velocity

    #     # If player hits the ground (platform), stop falling and allow jumping again
    #     if player.colliderect(platform):
    #         player.y = platform.top - player.height
    #         is_jumping = False
    #         y_velocity = 0  # Reset velocity after landing

    # Draw the player (the jumping sprite)
    pygame.draw.rect(screen, WHITE, sprite)

    # Handle events (such as quit and jumping)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit(0)

    # Check for keypress to trigger jump (you can replace this with scream detection)
    # keys = pygame.key.get_pressed()
    # if keys[pygame.K_SPACE] and on_ground:  # Jump when spacebar is pressed
    #     is_jumping = True
    #     y_velocity = jump_strength  # Set jump velocity

    # Convert Pygame surface to a format OpenCV understands (RGB -> BGR)
    frame_for_video = np.array(pygame.surfarray.pixels3d(screen))  # Get the screen pixels
    frame_for_video = np.transpose(frame_for_video, (1, 0, 2))  # Transpose to correct orientation
    frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)  # Convert to BGR for OpenCV

    # Write the frame to the video output file
    out.write(frame_for_video)

    # Update the display
    pygame.display.update()

# Cleanup
pygame.quit()
out.release()  # Save and close the video file
cv2.destroyAllWindows()
