import pygame
import time

class Block(pygame.sprite.Sprite):
    """
    Clsss for the blocks in the game.
    """
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
    """
    Class for the player character. Mario in this case. The properties of this class are:
    - player_walk: List of images for the walking animation.
    - player_jump: Image for the jumping animation.
    - image: The current image of the player.
    - rect: The rectangle of the player image.
    - gravity: The gravity acting on the player.
    - player_index: The index of the player image.
    - on_ground: Boolean to check if the player is on the ground.
    - dead: Boolean to check if the player is dead.
    - invincible: Boolean to check if the player is invincible.
    - invincible_duration: The duration of invincibility.
    - last_hit_time: The time of the last hit.
    """
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
        """
        Methods to update the player state. 
        This includes applying gravity, changing the player image, and checking for invincibility.
        """
        if not self.dead:
            self.apply_gravity()
            self.animation_state()
            if self.invincible and (time.time() - self.last_hit_time) > self.invincible_duration:
                self.invincible = False
        else:
            self.apply_gravity()
            self.image = self.player_death

    def animation_state(self):
        """
        Methods to change the player image based on the state of the player.
        """
        if not self.on_ground:
            self.image = self.player_jump
        else:
            self.player_index += 0.1
            if self.player_index >= len(self.player_walk):
                self.player_index = 0
            self.image = self.player_walk[int(self.player_index)]
        self.rect.x += 1  # Move the player to the right
