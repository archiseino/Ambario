import pygame
import cv2
import numpy as np
import pyaudio
import wave
import threading
import time

class AudioRecorder(threading.Thread):
    def __init__(self, filename="output.wav", rate=44100, frames_per_buffer=1048):
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
        self.rect = self.image.get_rect(midbottom=(100, 350))
        self.gravity = 0
        self.player_index = 0
        self.on_ground = True
        self.dead = False
        self.invincible = False
        self.invincible_duration = 2  # seconds
        self.last_hit_time = 0

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity

    def jump(self, jump_force):
        if self.on_ground:
            self.gravity = jump_force

    def die(self):
        self.dead = True
        self.gravity = -15  # Initial jump force for death animation

    def hit(self):
        self.invincible = True
        self.last_hit_time = time.time()

    def update(self):
        if not self.dead:
            self.apply_gravity()
            self.animation_state()
            if self.invincible and (time.time() - self.last_hit_time) > self.invincible_duration:
                self.invincible = False
        else:
            self.apply_gravity()
            self.image = self.player_death

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
        self.show_congratulations = False
        self.show_game_over = False
        self.message_start_time = 0
        self.message_duration = 3  # seconds
        self.score = 0
        self.lives = 3

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
        self.ocean_rect = self.ocean.get_rect(topleft=(0, 165))

        ## Castle Image
        self.castle_image = pygame.image.load("Model/Castle.png").convert_alpha()
        self.castle_image = pygame.transform.scale(self.castle_image, (100, 100))


        self.video_cap = cv2.VideoCapture(0)
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.out = cv2.VideoWriter("output.avi", self.fourcc, 15, (640, 480))

        self.audio_recorder = AudioRecorder()

        ## Bottom Limit for the Platforms is aroudn 400 since we have Wave that will block the view of the platforms
        self.platform_layouts = [
            {
                "platforms": [(100, 350), (400, 300), (700, 250), (1000, 300), (1300, 250)],
                "blocks": [(450, 300), (780, 250), (1010, 300)]  # Example block positions
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

    def overlay_text(self, text, size, color, position):
        """Overlay text on the screen."""
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)
        self.screen.blit(text_surface, text_rect)

    def update_hud(self, volume = 0):
        """Update the HUD with the current volume, score, and lives."""
        font = pygame.font.Font(None, 36)
        volume_text = font.render(f"Volume: {int(volume)}", True, (255, 255, 255))
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        lives_text = font.render(f"Lives: {self.lives}", True, (255, 255, 255))

        self.screen.blit(volume_text, (10, 10))
        self.screen.blit(score_text, (10, 50))
        self.screen.blit(lives_text, (10, 90))

    def run(self):
        self.audio_recorder.start()

        countdown_seconds = 3
        countdown_start_time = time.time()
        current_volume = 0  # Initialize current_volume

        while self.running:
            current_time = time.time()
            elapsed_time = current_time - countdown_start_time

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

                if elapsed_time < countdown_seconds:
                    self.overlay_text(str(countdown_seconds - int(elapsed_time)), 74, (255, 255, 255), (320, 240))
                else:
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
                            if not self.player.sprite.invincible:
                                self.player.sprite.hit()
                                self.lives -= 1
                                if self.lives <= 0:
                                    self.player.sprite.die()
                                    self.show_game_over = True
                                    self.message_start_time = time.time()
                                    self.running = False

                    # Check if player falls off the screen
                    if player_rect.top > self.screen.get_height():
                        print("Player fell off the screen!")
                        self.player.sprite.die()
                        self.lives -= 1
                        self.show_game_over = True
                        self.message_start_time = time.time()
                        self.running = False

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

                    # Check collision with castle
                    if player_rect.colliderect(self.castle_rect):
                        print("Congratulations! You've reached the castle!")
                        self.show_congratulations = True
                        self.message_start_time = time.time()
                        self.running = False

                    # Update the score based on distance traveled
                    self.score += 1

                if self.show_congratulations:
                    self.overlay_text("Congratulations!", 74, (255, 255, 255), (320, 240))
                    if (current_time - self.message_start_time) > self.message_duration:
                        self.show_congratulations = False

                if self.show_game_over:
                    self.overlay_text("Game Over", 74, (255, 0, 0), (320, 240))
                    if (current_time - self.message_start_time) > self.message_duration:
                        self.show_game_over = False

                # Update the HUD
                self.update_hud(current_volume)

                pygame.display.update()

                frame_for_video = np.array(pygame.surfarray.pixels3d(self.screen))
                frame_for_video = np.transpose(frame_for_video, (1, 0, 2))
                frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)
                self.out.write(frame_for_video)

                self.clock.tick(15)

        # Ensure the final message is displayed for the specified duration
        end_time = time.time()
        while (time.time() - end_time) < self.message_duration:
            if self.show_congratulations:
                self.overlay_text("Congratulations!", 74, (255, 255, 255), (320, 240))
            if self.show_game_over:
                self.overlay_text("Game Over", 74, (255, 0, 0), (320, 240))
            pygame.display.update()
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