import pygame
import cv2
import numpy as np
import pyaudio
import wave
import threading
import random

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

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("Model/chicken.png").convert_alpha()
        self.imge = pygame.transform.scale(self.image, (10, 10))
        self.rect = self.image.get_rect(midbottom=(x, y))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.player_walk = [
            pygame.image.load('Model/Mario - Walk1.gif').convert_alpha(),
            pygame.image.load('Model/Mario - Walk2.gif').convert_alpha(),
            pygame.image.load('Model/Mario - Walk3.gif').convert_alpha()
        ]
        self.player_jump = pygame.image.load("Model/Mario - Jump.gif").convert_alpha()
        self.image = self.player_walk[0]
        self.rect = self.image.get_rect(midbottom=(80, 430))
        self.gravity = 0
        self.player_index = 0
        self.on_ground = True

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity

    def jump(self, jump_force):
        if self.on_ground:
            self.gravity = jump_force

    def update(self):
        self.apply_gravity()
        self.animation_state()

    def animation_state(self):
        if not self.on_ground:
            self.image = self.player_jump
        else:
            self.player_index += 0.1
            if self.player_index >= len(self.player_walk):
                self.player_index = 0
            self.image = self.player_walk[int(self.player_index)]
        self.rect.x += 1  # Move the player to the right
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("Jumping Game with Camera Background")
        self.clock = pygame.time.Clock()
        self.running = True

        # Load and resize the platform image
        self.platform_image = pygame.image.load("Model/ground.png").convert_alpha()
        self.platform_image = pygame.transform.scale(self.platform_image, (200, 50))  # Resize to (width, height)
        self.platform_rect = self.platform_image.get_rect(topleft=(0, 430))
        self.player = pygame.sprite.GroupSingle(Player())

        self.video_cap = cv2.VideoCapture(0)
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.out = cv2.VideoWriter("output.avi", self.fourcc, 15, (640, 480))

        self.audio_recorder = AudioRecorder()

        # Define platform layouts
        self.platform_layouts = [
            {
                "platforms": [(0, 430), (300, 430), (600, 430), (900, 430), (1200, 430), (1500, 430), (1800, 430)],
                "blocks": [(400, 380), (700, 300), (1000, 220)]  # Example block positions
            }
        ]

        # Randomly select a platform layout
        self.selected_layout = random.choice(self.platform_layouts)
        self.platforms = [pygame.Rect(x, y, self.platform_rect.width, self.platform_rect.height) for x, y in self.selected_layout["platforms"]]

        # Initialize blocks
        self.blocks = pygame.sprite.Group()
        for x, y in self.selected_layout["blocks"]:
            self.blocks.add(Block(x, y))

        # Define the finish line
        self.finish_line = pygame.Rect(self.platforms[-1].right, self.platforms[-1].top, 10, self.platforms[-1].height)

        # Speed at which platforms move to the left
        self.platform_speed = 5

    def detect_scream(self, volume, threshold=500):
        print(volume)
        if volume > threshold:
            # Calculate jump force based on volume
            jump_force = min(-5 - (volume - threshold) / 250, -15) # Cap the jump force to -15
            return jump_force
        return 0

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
                jump_force = self.detect_scream(current_volume)
                if jump_force:    
                    self.player.sprite.jump(jump_force)

                self.player.update()

                # Update platform positions
                for platform in self.platforms:
                    platform.x -= self.platform_speed

                # Update block positions
                for block in self.blocks:
                    block.rect.x -= self.platform_speed

                # Update finish line position
                self.finish_line.x -= self.platform_speed

                # Collision detection
                player_rect = self.player.sprite.rect
                self.player.sprite.on_ground = False  # Reset on_ground status
                for platform in self.platforms:
                    if player_rect.colliderect(platform):
                        # Adjust player's position based on collision
                        if player_rect.bottom > platform.top and player_rect.top < platform.top:
                            player_rect.bottom = platform.top
                            self.player.sprite.on_ground = True
                            self.player.sprite.gravity = 0  # Reset gravity when on platform
                        elif player_rect.top < platform.bottom and player_rect.bottom > platform.bottom:
                            player_rect.top = platform.bottom
                        elif player_rect.right > platform.left and player_rect.left < platform.left:
                            player_rect.right = platform.left
                        elif player_rect.left < platform.right and player_rect.right > platform.right:
                            player_rect.left = platform.right

                # Allow jumping only if the player is on the ground
                self.player.draw(self.screen)

                # Draw the platforms
                for platform in self.platforms:
                    self.screen.blit(self.platform_image, platform)

                # Draw the blocks
                self.blocks.draw(self.screen)

                pygame.display.update()

                # Convert Pygame surface to a format OpenCV understands (RGB -> BGR)
                frame_for_video = np.array(pygame.surfarray.pixels3d(self.screen))
                frame_for_video = np.transpose(frame_for_video, (1, 0, 2))
                frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)
                self.out.write(frame_for_video)

                self.clock.tick(15)

                # Check if player has reached the finish line
                if self.player.sprite.rect.colliderect(self.finish_line):
                    print("Congratulations! You've reached the finish line!")
                    self.running = False

        self.audio_recorder.stop()
        self.audio_recorder.save()
        self.video_cap.release()
        self.out.release()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
