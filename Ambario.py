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
        self.images = [
            pygame.image.load("Model/piranha_frame_1.png").convert_alpha(),
            pygame.image.load("Model/piranha_frame_2.png").convert_alpha()
        ]
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.index = 0
    
    def update(self):
        self.index += 0.1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[int(self.index)]

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
        self.rect = self.image.get_rect(midbottom=(0, 300))
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
        self.player = pygame.sprite.GroupSingle(Player())

        ## Pipe Image
        self.pipe_image = pygame.image.load("Model/pipe.gif").convert_alpha()
        self.pipe_image = pygame.transform.scale(self.pipe_image, (120, 400))

        ## Ocean image  
        self.ocean = pygame.image.load("Model/ocean-1.png").convert_alpha()
        self.ocean = pygame.transform.scale(self.ocean, (640, 480))
        self.ocean_rect = self.ocean.get_rect(midbottom=(0, 0))

        ## Castle Image
        self.castle_image = pygame.image.load("Model/Castle.png").convert_alpha()
        self.castle_image = pygame.transform.scale(self.castle_image, (100, 100))


        self.video_cap = cv2.VideoCapture(0)
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.out = cv2.VideoWriter("output.avi", self.fourcc, 15, (640, 480))

        self.audio_recorder = AudioRecorder()

        ## Bottom Limit for the Platforms is aroudn 400 since we have Wave
        self.platform_layouts = [
            {
                "platforms": [(0, 350), (300, 350), (600, 350), (900, 350), (1200, 350)],
                "blocks": [(400, 350), (700, 350), (1000, 350)]  # Example block positions
            }
        ]

        self.platforms = []
        self.pipes = []
        for layout in self.platform_layouts:
            for pos in layout["platforms"]:
                platform_rect = self.platform_image.get_rect(topleft=pos)
                self.platforms.append(platform_rect)
                pipe_rect = self.pipe_image.get_rect(midtop=(pos[0] + platform_rect.width // 2, pos[1] + platform_rect.height))
                self.pipes.append(pipe_rect)

        self.blocks = pygame.sprite.Group()
        for layout in self.platform_layouts:
            for pos in layout["blocks"]:
                self.blocks.add(Block(pos[0], pos[1]))

        # Place the castle at the end of the last platform
        last_platform = self.platforms[-1]
        self.castle_rect = self.castle_image.get_rect(midbottom=(last_platform.left + last_platform.width // 2, last_platform.top + 5))
        self.platform_speed = 5

    def detect_scream(self, volume, threshold=500):
        if volume > threshold:
            jump_force = min(-5 - (volume - threshold) / 250, -15)
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
                self.blocks.update()

                for platform in self.platforms:
                    platform.x -= self.platform_speed

                for pipe in self.pipes:
                    pipe.x -= self.platform_speed

                for block in self.blocks:
                    block.rect.x -= self.platform_speed

                self.castle_rect.x -= self.platform_speed


                player_rect = self.player.sprite.rect
                self.player.sprite.on_ground = False
                for platform in self.platforms:
                    if player_rect.colliderect(platform):
                        if player_rect.bottom > platform.top and player_rect.top < platform.top:
                            player_rect.bottom = platform.top
                            self.player.sprite.on_ground = True
                            self.player.sprite.gravity = 0
                        elif player_rect.top < platform.bottom and player_rect.bottom > platform.bottom:
                            player_rect.top = platform.bottom
                        elif player_rect.right > platform.left and player_rect.left < platform.left:
                            player_rect.right = platform.left
                        elif player_rect.left < platform.right and player_rect.right > platform.right:
                            player_rect.left = platform.right

                # Check collision with blocks
                for block in self.blocks:
                    if player_rect.colliderect(block.rect):
                        print("Collision with block!")
                        # Handle collision (e.g., end game, reduce health, etc.)

                self.player.draw(self.screen)
                for platform in self.platforms:
                    self.screen.blit(self.platform_image, platform)
                for pipe in self.pipes:
                    self.screen.blit(self.pipe_image, pipe)
                self.blocks.draw(self.screen)

                # Draw the castle
                self.screen.blit(self.castle_image, self.castle_rect)

                # Draw the ocean
                self.screen.blit(self.ocean, self.ocean_rect)



                pygame.display.update()

                frame_for_video = np.array(pygame.surfarray.pixels3d(self.screen))
                frame_for_video = np.transpose(frame_for_video, (1, 0, 2))
                frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)
                self.out.write(frame_for_video)

                self.clock.tick(15)

                # Check collision with castle
                if player_rect.colliderect(self.castle_rect):
                    print("Congratulations! You've reached the castle!")
                    self.running = False

        self.audio_recorder.stop()
        self.audio_recorder.save()
        self.video_cap.release()
        self.out.release()
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()