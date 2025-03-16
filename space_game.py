import pygame
import random
import sys
import math
import os
import json
import wave
import struct
import numpy

# Initialize pygame and sound
pygame.mixer.quit()  # Reset the mixer
pygame.mixer.pre_init(44100, -16, 2, 1024)  # Smaller buffer size
pygame.mixer.init()
pygame.init()

# Test pygame mixer
print("Testing pygame mixer...")
try:
    test_array = numpy.array([[32767, 32767], [0, 0], [-32767, -32767]], dtype=numpy.int16)
    test_sound = pygame.sndarray.make_sound(test_array)
    test_sound.play()
    pygame.time.wait(100)
    print("Basic sound test successful")
except Exception as e:
    print(f"Error in basic sound test: {e}")

# Set up mixer settings
pygame.mixer.set_num_channels(32)  # Increase number of sound channels
pygame.mixer.music.set_volume(0.5)  # Set default volume

print("Pygame version:", pygame.version.ver)
print("Mixer initialized:", pygame.mixer.get_init())
print("Number of channels:", pygame.mixer.get_num_channels())

def create_simple_sound(frequency, duration, volume=0.5, sound_type='sine'):
    """Create a more interesting sound wave"""
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    sound_buffer = numpy.zeros((num_samples, 2), dtype=numpy.int16)
    max_sample = 2**(16 - 1) - 1
    
    for i in range(num_samples):
        t = float(i) / sample_rate
        
        if sound_type == 'laser':
            # Laser sound: frequency sweep from high to low with harmonics
            freq = frequency * (1.0 - t/duration * 0.5)  # Sweep down
            decay = 1.0 - t/duration
            # Add harmonics for richer sound
            sample = int(max_sample * volume * decay * (
                0.7 * math.sin(2.0 * math.pi * freq * t) +
                0.2 * math.sin(2.0 * math.pi * freq * 2 * t) +  # First harmonic
                0.1 * math.sin(2.0 * math.pi * freq * 3 * t)    # Second harmonic
            ))
        
        elif sound_type == 'explosion':
            # Massive explosion: multiple layers of noise, deep bass rumble, and shockwave effect
            
            # Initial blast wave (high frequency content with very sharp attack)
            blast = random.uniform(-1, 1) * math.exp(-30 * t/duration)
            
            # Multiple rumble frequencies for rich bass
            rumble_freqs = [20, 40, 60, 80]  # Very low frequencies for deep rumble
            rumble = sum(math.sin(2.0 * math.pi * freq * t) * math.exp(-3 * t/duration)
                        for freq in rumble_freqs) / len(rumble_freqs)
            
            # Debris sound (mid-high frequency noise)
            debris = sum(random.uniform(-1, 1) * math.sin(2.0 * math.pi * freq * t)
                        for freq in [500, 1000, 2000]) / 3.0
            
            # Shockwave effect (amplitude modulation)
            shockwave = math.exp(-5 * t/duration) * (1.0 + 0.5 * math.sin(2.0 * math.pi * 30 * t))
            
            # Complex decay envelope
            if t < duration * 0.1:  # Initial blast (10% of duration)
                decay = 1.0  # Full volume
            elif t < duration * 0.3:  # Quick decay (next 20%)
                decay = 1.0 - 0.5 * ((t - 0.1 * duration) / (0.2 * duration))
            else:  # Long tail (remaining 70%)
                decay = 0.5 * math.exp(-2 * (t - 0.3 * duration) / (0.7 * duration))
            
            # Mix all components with different weights
            sample = int(max_sample * volume * decay * (
                0.4 * blast +           # Sharp initial blast
                0.3 * rumble +          # Deep bass rumble
                0.2 * debris +          # Mid-high debris sounds
                0.1 * shockwave         # Amplitude modulation
            ))
        
        elif sound_type == 'collision':
            # Enhanced collision: metallic impact with resonance and debris
            
            # Multiple impact frequencies for metallic sound
            frequencies = [
                frequency,          # Base frequency
                frequency * 1.5,    # Perfect fifth
                frequency * 2.0,    # Octave
                frequency * 2.5,    # Octave + fifth
                frequency * 3.0     # Two octaves
            ]
            
            # Initial impact (very fast attack)
            attack = min(1.0, t * 200)  # Twice as fast attack
            
            # Complex decay with different rates for each frequency
            decay_base = math.exp(-15 * t/duration)
            decay_rates = [1.0, 1.2, 1.5, 2.0, 2.5]  # Different decay rates
            
            # Metallic ringing frequencies
            metallic = sum(
                amp * math.sin(2.0 * math.pi * freq * t) * math.exp(-rate * 15 * t/duration)
                for freq, rate, amp in zip(frequencies, decay_rates, [0.4, 0.25, 0.15, 0.1, 0.1])
            )
            
            # Add some noise for impact crunch
            impact_noise = random.uniform(-1, 1) * math.exp(-30 * t/duration)
            
            # Combine metallic ringing with impact noise
            sample = int(max_sample * volume * attack * (
                0.8 * metallic +     # Metallic ringing
                0.2 * impact_noise   # Impact crunch
            ))
        
        elif sound_type == 'powerup':
            # Power-up: ascending frequency with harmonics and shimmer
            base_freq = frequency * (1.0 + t/duration * 1.5)  # Bigger frequency sweep
            # Add shimmer effect
            shimmer = 1.0 + 0.3 * math.sin(2.0 * math.pi * 15 * t)  # Faster wobble
            sparkle = 0.2 * math.sin(2.0 * math.pi * 1000 * t)  # High frequency sparkle
            
            # Combine multiple frequency components
            sample = int(max_sample * volume * (
                0.6 * math.sin(2.0 * math.pi * base_freq * t * shimmer) +
                0.3 * math.sin(2.0 * math.pi * base_freq * 1.5 * t) +
                0.1 * sparkle
            ))
        
        else:  # Default sine wave
            sample = int(max_sample * volume * math.sin(2.0 * math.pi * frequency * t))
        
        # Enhanced stereo effect with more separation
        pan_amount = 0.2  # Increased stereo separation
        left_sample = int(sample * (1.0 + pan_amount * math.sin(2.0 * math.pi * 2 * t)))
        right_sample = int(sample * (1.0 + pan_amount * math.cos(2.0 * math.pi * 2 * t)))
        sound_buffer[i] = [left_sample, right_sample]
    
    return pygame.sndarray.make_sound(sound_buffer)

# Sound effects
class SoundManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            try:
                # Create sound effects with enhanced sounds
                cls._instance.laser_sound = create_simple_sound(2000, 0.2, 0.3, 'laser')
                cls._instance.explosion_sound = create_simple_sound(60, 1.0, 0.8, 'explosion')  # Longer, louder, deeper
                cls._instance.collision_sound = create_simple_sound(200, 0.4, 0.7, 'collision')  # Longer, louder, deeper
                cls._instance.powerup_sound = create_simple_sound(600, 0.3, 0.4, 'powerup')
                
                cls._instance.enabled = True
                print("Sound manager initialized successfully")
                
                # Test sound
                cls._instance.explosion_sound.play()
                pygame.time.wait(100)
                print("Test sound played")
            except Exception as e:
                print(f"Warning: Could not initialize sound manager: {e}")
                cls._instance.enabled = False
        return cls._instance
    
    def play_laser(self):
        if self.enabled:
            try:
                self.laser_sound.stop()  # Stop any currently playing instance
                self.laser_sound.play()
                print("Playing laser sound")
            except Exception as e:
                print(f"Error playing laser sound: {e}")
    
    def play_explosion(self):
        if self.enabled:
            try:
                self.explosion_sound.stop()
                self.explosion_sound.play()
                print("Playing explosion sound")
            except Exception as e:
                print(f"Error playing explosion sound: {e}")
    
    def play_collision(self):
        if self.enabled:
            try:
                self.collision_sound.stop()
                self.collision_sound.play()
                print("Playing collision sound")
            except Exception as e:
                print(f"Error playing collision sound: {e}")
    
    def play_powerup(self):
        if self.enabled:
            try:
                self.powerup_sound.stop()
                self.powerup_sound.play()
                print("Playing powerup sound")
            except Exception as e:
                print(f"Error playing powerup sound: {e}")

# Initialize sound manager as a global singleton
pygame.mixer.set_num_channels(32)  # Increase number of sound channels
sound_manager = SoundManager()

# Test all sounds with delays
def test_sounds():
    print("\nTesting sound system...")
    sound_manager.play_laser()
    pygame.time.wait(200)  # Wait between sounds
    sound_manager.play_explosion()
    pygame.time.wait(400)
    sound_manager.play_collision()
    pygame.time.wait(200)
    sound_manager.play_powerup()
    pygame.time.wait(300)
    print("Sound test complete\n")

# Run sound test
test_sounds()

# Screen dimensions
WIDTH, HEIGHT = 1280, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Asteroid Shooter")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BROWN = (165, 42, 42)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Explosion class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center_x, center_y):
        super().__init__()
        self.radius = 250  # Explosion radius increased to 250
        self.current_radius = 0
        self.growth_rate = 25  # Increased to match larger radius
        self.max_frames = 10
        self.frame = 0
        self.center_x = center_x
        self.center_y = center_y
        
        # Create surface for explosion
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (center_x, center_y)
    
    def update(self):
        self.frame += 1
        if self.frame > self.max_frames:
            self.kill()
            return
        
        self.current_radius = int((self.frame / self.max_frames) * self.radius)
        self.image.fill((0, 0, 0, 0))  # Clear with transparent
        pygame.draw.circle(self.image, (*ORANGE, 128), (self.radius, self.radius), self.current_radius)

# StrayBomb class
class StrayBomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 40  # Increased size to accommodate larger radius
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Draw bomb as red circle with fuse
        pygame.draw.circle(self.image, RED, (self.size//2, self.size//2), 20)  # Radius increased to 20
        pygame.draw.line(self.image, YELLOW, (self.size//2, 0), (self.size//2, self.size//4), 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speedy = random.randint(1, 3)
        self.speedx = random.randint(-2, 2)
    
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        
        # Bounce off screen edges
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.speedx = -self.speedx
        
        # Kill if moves off bottom of screen
        if self.rect.top > HEIGHT:
            self.kill()

# PowerUp class
class PowerUp(pygame.sprite.Sprite):
    RAPID_FIRE = "rapid_fire"
    DOUBLE_SHOT = "double_shot"
    
    def __init__(self, x, y):
        super().__init__()
        self.type = random.choice([PowerUp.RAPID_FIRE, PowerUp.DOUBLE_SHOT])
        self.size = 20
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        if self.type == PowerUp.RAPID_FIRE:
            color = YELLOW
            # Draw lightning bolt
            points = [(10, 0), (20, 8), (13, 12), (20, 20), (0, 12), (7, 8)]
            pygame.draw.polygon(self.image, color, points)
        else:  # DOUBLE_SHOT
            color = PURPLE
            # Draw double circle
            pygame.draw.circle(self.image, color, (5, 10), 5)
            pygame.draw.circle(self.image, color, (15, 10), 5)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speedy = 3
    
    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

# Ship class
class Ship(pygame.sprite.Sprite):
    def __init__(self, image, speed, player_name=""):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed = speed
        self.base_shoot_delay = 250  # milliseconds
        self.shoot_delay = self.base_shoot_delay
        self.last_shot = pygame.time.get_ticks()
        
        # Special mode check
        self.is_invincible = player_name == "12345"
        
        # Power-up attributes
        self.power_ups = set()
        self.power_up_start = 0
        self.power_up_duration = 50000  # 50 seconds
        
        # Bomb attributes
        self.has_bomb = False

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        
        # Keep ship on screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            
        # Check power-up duration
        now = pygame.time.get_ticks()
        if self.power_ups and now - self.power_up_start > self.power_up_duration:
            self.power_ups.clear()
            self.shoot_delay = self.base_shoot_delay
    
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            sound_manager.play_laser()  # Play laser sound
            if PowerUp.DOUBLE_SHOT in self.power_ups:
                # Return list of two bullets side by side
                return [
                    Bullet(self.rect.left + 10, self.rect.top, -1),
                    Bullet(self.rect.right - 10, self.rect.top, -1)
                ]
            else:
                # Return single bullet as a list for consistency
                return [Bullet(self.rect.centerx, self.rect.top, -1)]
        return []
    
    def add_power_up(self, power_up_type):
        self.power_ups.add(power_up_type)
        self.power_up_start = pygame.time.get_ticks()
        
        if power_up_type == PowerUp.RAPID_FIRE:
            self.shoot_delay = self.base_shoot_delay // 2  # Twice as fast

# Enemy ship class
class EnemyShip(pygame.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        size = 40
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        # Draw enemy ship as red inverted triangle
        pygame.draw.polygon(self.image, RED, [(size//2, size), (0, 0), (size, 0)])
        
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        
        # Base speed increased by 25% per level
        base_speed = random.randrange(1, 3)
        level_multiplier = 1 + (0.25 * (level - 1))
        self.speedy = base_speed * level_multiplier
        self.speedx = random.randrange(-2, 2) * level_multiplier
        
        self.shoot_delay = max(300, 1500 - (level * 50))  # Shoot faster at higher levels
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        
        # If enemy goes off screen, respawn it
        if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 25:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 3)
            self.speedx = random.randrange(-2, 2)
    
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            return Bullet(self.rect.centerx, self.rect.bottom, 1, RED)
        return None

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 10
        self.direction = direction  # 1 for down (enemy), -1 for up (player)

    def update(self):
        self.rect.y += self.speed * self.direction
        # Kill if it moves off the screen
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

# Asteroid class
class Asteroid(pygame.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        # Create asteroid as a polygon
        size = random.randint(20, 50)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Generate random polygon points for the asteroid
        points = []
        for i in range(8):  # 8-sided polygon
            angle = 2 * math.pi * i / 8
            radius = random.uniform(size/3, size/2)
            x = size/2 + radius * math.cos(angle)
            y = size/2 + radius * math.sin(angle)
            points.append((x, y))
        
        # Draw the asteroid with color based on level
        if level <= 3:
            color = BROWN
        elif level <= 6:
            color = ORANGE
        elif level <= 9:
            color = PURPLE
        else:
            color = RED
            
        pygame.draw.polygon(self.image, color, points)
        
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        
        # Base speed increased by 25% per level
        base_speed = random.randrange(1, 4)
        level_multiplier = 1 + (0.25 * (level - 1))
        self.speedy = base_speed * level_multiplier
        self.speedx = random.randrange(-2, 2) * level_multiplier

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        # If asteroid goes off screen, respawn it
        if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 25:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 4)
            self.speedx = random.randrange(-2, 2)

# Boss class
class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.boss_level = level // 5  # 1 for level 5, 2 for level 10, etc.
        
        # Special handling for level 50 boss
        self.is_omega_boss = level == 50
        
        # Size scales with level, but Omega Boss is massive
        self.size = 400 if self.is_omega_boss else 180 + (self.boss_level * 20)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        if self.is_omega_boss:  # Level 50 - "THE OMEGA BOSS"
            # Create a massive, intimidating boss
            # Main core - pulsing dark matter core
            core_color = (100, 0, 150)  # Dark purple
            pygame.draw.circle(self.image, core_color, (self.size//2, self.size//2), self.size//3)
            
            # Multiple rotating rings
            for i in range(5):
                radius = self.size//3 + i * 30
                color = (255, i * 50, 255 - i * 30)  # Color gradient
                pygame.draw.circle(self.image, color, (self.size//2, self.size//2), radius, 4)
            
            # Energy crystals at cardinal points
            crystal_positions = [(self.size//2, 0), (self.size, self.size//2),
                               (self.size//2, self.size), (0, self.size//2)]
            for pos in crystal_positions:
                crystal_color = (255, 0, 100)  # Bright pink
                points = []
                for j in range(3):  # Triangle crystals
                    angle = 2 * math.pi * j / 3
                    points.append((
                        pos[0] + math.cos(angle) * 40,
                        pos[1] + math.sin(angle) * 40
                    ))
                pygame.draw.polygon(self.image, crystal_color, points)
            
            # Add glowing eyes
            eye_color = (255, 0, 0)  # Bright red
            eye_size = 30
            pygame.draw.circle(self.image, eye_color, (self.size//3, self.size//3), eye_size)
            pygame.draw.circle(self.image, eye_color, (2*self.size//3, self.size//3), eye_size)
            
            # Add energy beams
            beam_color = (255, 255, 0)  # Yellow
            for i in range(8):
                angle = 2 * math.pi * i / 8
                start = (self.size//2, self.size//2)
                end = (
                    self.size//2 + math.cos(angle) * self.size//2,
                    self.size//2 + math.sin(angle) * self.size//2
                )
                pygame.draw.line(self.image, beam_color, start, end, 6)
        
        elif self.boss_level == 1:  # Level 5 boss - "The Crimson Titan"
            # Draw large red pentagon with glowing core
            points = []
            for i in range(5):
                angle = 2 * math.pi * i / 5 - math.pi / 2
                points.append((
                    self.size/2 + math.cos(angle) * self.size/2,
                    self.size/2 + math.sin(angle) * self.size/2
                ))
            pygame.draw.polygon(self.image, RED, points)
            # Draw core
            pygame.draw.circle(self.image, ORANGE, (self.size//2, self.size//2), self.size//4)
            
        elif self.boss_level == 2:  # Level 10 boss - "The Void Reaper"
            # Draw dark purple crystal-like shape
            points = []
            for i in range(8):
                angle = 2 * math.pi * i / 8
                r = self.size/2 if i % 2 == 0 else self.size/3
                points.append((
                    self.size/2 + math.cos(angle) * r,
                    self.size/2 + math.sin(angle) * r
                ))
            pygame.draw.polygon(self.image, PURPLE, points)
            # Add glowing eyes
            eye_color = (255, 0, 255)  # Bright purple
            pygame.draw.circle(self.image, eye_color, (self.size//3, self.size//3), 15)
            pygame.draw.circle(self.image, eye_color, (2*self.size//3, self.size//3), 15)
            
        elif self.boss_level == 3:  # Level 15 boss - "The Omega Destroyer"
            # Draw massive technological horror
            # Main body
            pygame.draw.rect(self.image, RED, (self.size//4, self.size//4, self.size//2, self.size//2))
            # Outer ring
            pygame.draw.circle(self.image, ORANGE, (self.size//2, self.size//2), self.size//2, 5)
            # Energy nodes
            for i in range(4):
                angle = 2 * math.pi * i / 4
                x = self.size//2 + math.cos(angle) * self.size//3
                y = self.size//2 + math.sin(angle) * self.size//3
                pygame.draw.circle(self.image, YELLOW, (int(x), int(y)), 20)
                
        elif self.boss_level == 4:  # Level 20 boss - "The Quantum Harbinger"
            # Draw quantum-themed boss with multiple layers
            # Outer quantum field
            pygame.draw.circle(self.image, (0, 255, 255), (self.size//2, self.size//2), self.size//2)
            # Inner rings
            for i in range(3):
                radius = self.size//2 - (i * 20)
                pygame.draw.circle(self.image, (0, 150, 255), (self.size//2, self.size//2), radius, 3)
            # Energy beams
            for i in range(6):
                angle = 2 * math.pi * i / 6
                start = (self.size//2, self.size//2)
                end = (
                    self.size//2 + math.cos(angle) * self.size//2,
                    self.size//2 + math.sin(angle) * self.size//2
                )
                pygame.draw.line(self.image, (0, 255, 255), start, end, 4)
                
        else:  # Level 25+ boss - "The Cosmic Overlord"
            # Draw an even more intimidating boss
            # Main core
            pygame.draw.circle(self.image, (255, 0, 0), (self.size//2, self.size//2), self.size//2)
            # Pulsing rings
            for i in range(4):
                radius = self.size//2 - (i * 15)
                pygame.draw.circle(self.image, (255, i * 60, 0), (self.size//2, self.size//2), radius, 5)
            # Energy crystals
            for i in range(8):
                angle = 2 * math.pi * i / 8
                distance = self.size//3
                x = self.size//2 + math.cos(angle) * distance
                y = self.size//2 + math.sin(angle) * distance
                # Draw diamond-shaped crystals
                points = []
                for j in range(4):
                    crystal_angle = 2 * math.pi * j / 4 + angle
                    points.append((
                        x + math.cos(crystal_angle) * 15,
                        y + math.sin(crystal_angle) * 15
                    ))
                pygame.draw.polygon(self.image, (255, 255, 0), points)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.top = -self.size
        
        # Boss attributes scaled by level
        self.max_health = 800 * self.boss_level  # Reduced base health for more frequent bosses
        self.health = self.max_health
        self.speed = 2 + self.boss_level
        self.shoot_delay = max(100, 400 - (self.boss_level * 40))  # Faster shooting at higher levels
        self.last_shot = pygame.time.get_ticks()
        self.pattern_time = pygame.time.get_ticks()
        self.pattern_duration = 3000  # Switch patterns every 3 seconds
        self.current_pattern = 0
        self.movement_offset = 0
        
    def update(self):
        now = pygame.time.get_ticks()
        
        # Move into screen at start
        if self.rect.top < 50:
            self.rect.y += 2
            return
        
        # Special patterns for Omega Boss
        if self.is_omega_boss:
            # Switch patterns more frequently
            if now - self.pattern_time > 2000:  # Every 2 seconds
                self.pattern_time = now
                self.current_pattern = (self.current_pattern + 1) % 4
                self.movement_offset = 0
            
            # More complex movement patterns
            if self.current_pattern == 0:  # Double sine wave
                self.movement_offset += 0.08
                self.rect.centerx = WIDTH//2 + math.sin(self.movement_offset) * (WIDTH//3)
                self.rect.centery = HEIGHT//4 + math.sin(2 * self.movement_offset) * (HEIGHT//6)
            elif self.current_pattern == 1:  # Infinity pattern
                self.movement_offset += 0.05
                scale_x = WIDTH//3
                scale_y = HEIGHT//6
                self.rect.centerx = WIDTH//2 + math.sin(2 * self.movement_offset) * scale_x
                self.rect.centery = HEIGHT//4 + math.sin(self.movement_offset) * scale_y
            elif self.current_pattern == 2:  # Diamond pattern
                self.movement_offset += 0.04
                angle = self.movement_offset % (2 * math.pi)
                radius = 200
                self.rect.centerx = WIDTH//2 + math.cos(angle) * radius
                self.rect.centery = HEIGHT//4 + math.sin(angle) * radius
            else:  # Aggressive teleport
                if random.random() < 0.05:  # 5% chance to teleport each frame
                    self.rect.centerx = random.randint(self.size//2, WIDTH - self.size//2)
                    self.rect.centery = random.randint(50, HEIGHT//3)
        else:
            # Regular boss patterns
            # Switch patterns periodically
            if now - self.pattern_time > self.pattern_duration:
                self.pattern_time = now
                self.current_pattern = (self.current_pattern + 1) % 3
                self.movement_offset = 0
            
            # Movement patterns
            if self.current_pattern == 0:  # Sine wave
                self.movement_offset += 0.05
                self.rect.centerx = WIDTH//2 + math.sin(self.movement_offset) * (WIDTH//3)
            elif self.current_pattern == 1:  # Figure 8
                self.movement_offset += 0.03
                scale = 100
                self.rect.centerx = WIDTH//2 + math.sin(2 * self.movement_offset) * scale
                self.rect.centery = 150 + math.sin(self.movement_offset) * scale
            else:  # Random teleports
                if random.random() < 0.02:  # 2% chance to teleport each frame
                    self.rect.centerx = random.randint(self.size//2, WIDTH - self.size//2)
                    self.rect.centery = random.randint(50, HEIGHT//3)
        
        # Keep boss on screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT//2:
            self.rect.bottom = HEIGHT//2
    
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullets = []
            
            if self.is_omega_boss:
                # Multiple attack patterns
                pattern = (now // 2000) % 4  # Change pattern every 2 seconds
                
                if pattern == 0:  # Spiral barrage
                    for i in range(16):
                        angle = 2 * math.pi * i / 16 + self.movement_offset
                        speed = 7
                        speed_x = math.cos(angle) * speed
                        speed_y = math.sin(angle) * speed
                        bullet = BossBullet(self.rect.centerx, self.rect.centery, 
                                          speed_x, speed_y, (255, 0, 0))
                        bullets.append(bullet)
                
                elif pattern == 1:  # Cross beam
                    speeds = [(8, 0), (-8, 0), (0, 8), (0, -8),
                             (5.6, 5.6), (-5.6, 5.6), (5.6, -5.6), (-5.6, -5.6)]
                    for speed_x, speed_y in speeds:
                        bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                          speed_x, speed_y, (255, 255, 0))
                        bullets.append(bullet)
                
                elif pattern == 2:  # Homing missiles
                    for _ in range(4):
                        # Target player's position
                        from game import player  # Get player reference
                        dx = player.rect.centerx - self.rect.centerx
                        dy = player.rect.centery - self.rect.centery
                        dist = math.sqrt(dx * dx + dy * dy)
                        speed = 6
                        speed_x = dx / dist * speed
                        speed_y = dy / dist * speed
                        bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                          speed_x, speed_y, (0, 255, 255))
                        bullets.append(bullet)
                
                else:  # Random scatter shot
                    for _ in range(20):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(4, 10)
                        speed_x = math.cos(angle) * speed
                        speed_y = math.sin(angle) * speed
                        bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                          speed_x, speed_y, (255, 0, 255))
                        bullets.append(bullet)
            else:
                # Regular boss patterns
                if self.boss_level == 1:  # Pentagram shot pattern
                    for i in range(5):
                        angle = 2 * math.pi * i / 5 + self.movement_offset
                        speed_x = math.cos(angle) * 5
                        speed_y = math.sin(angle) * 5
                        bullet = BossBullet(self.rect.centerx, self.rect.centery, speed_x, speed_y, RED)
                        bullets.append(bullet)
                
                elif self.boss_level == 2:  # Spiral pattern
                    for i in range(8):
                        angle = 2 * math.pi * i / 8 + self.movement_offset
                        speed_x = math.cos(angle) * 6
                        speed_y = math.sin(angle) * 6
                        bullet = BossBullet(self.rect.centerx, self.rect.centery, speed_x, speed_y, PURPLE)
                        bullets.append(bullet)
                
                else:  # Chaos pattern
                    for _ in range(12):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(3, 8)
                        speed_x = math.cos(angle) * speed
                        speed_y = math.sin(angle) * speed
                        bullet = BossBullet(self.rect.centerx, self.rect.centery, speed_x, speed_y, ORANGE)
                        bullets.append(bullet)
            
            return bullets
        return []

# Boss Bullet class
class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed_x, speed_y, color):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (5, 5), 5)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        
    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        # Kill if off screen
        if (self.rect.left < -100 or self.rect.right > WIDTH + 100 or
            self.rect.top < -100 or self.rect.bottom > HEIGHT + 100):
            self.kill()

# Function to get player name
def get_player_name():
    font = pygame.font.Font(None, 36)
    input_box = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2, 400, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False
    
    title = font.render("Enter Your Name:", True, WHITE)
    
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                active = input_box.collidepoint(event.pos)
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        # Limit name length to 15 characters
                        if len(text) < 15:
                            text += event.unicode
        
        screen.fill(BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 80))
        
        # Render the current text
        txt_surface = font.render(text, True, color)
        # Resize the box if the text is too long
        width = max(400, txt_surface.get_width() + 10)
        input_box.w = width
        input_box.centerx = WIDTH // 2
        
        # Blit the text
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        # Blit the input_box rect
        pygame.draw.rect(screen, color, input_box, 2)
        
        pygame.display.flip()
    
    return text if text else "Anonymous"

# Function to load high scores
def load_high_scores():
    if not os.path.exists('high_scores.json'):
        return []
    
    try:
        with open('high_scores.json', 'r') as f:
            return json.load(f)
    except:
        return []

# Function to save high scores
def save_high_scores(scores):
    with open('high_scores.json', 'w') as f:
        json.dump(scores, f)

# Function to update high scores
def update_high_scores(player_name, score, level):
    high_scores = load_high_scores()
    high_scores.append({"name": player_name, "score": score, "level": level})
    # Sort by score (highest first) and keep only top 10
    high_scores = sorted(high_scores, key=lambda x: x["score"], reverse=True)[:10]
    save_high_scores(high_scores)
    return high_scores

# Function to display high scores
def display_high_scores(high_scores):
    font_title = pygame.font.Font(None, 48)
    font = pygame.font.Font(None, 36)
    
    title = font_title.render("HIGH SCORES", True, YELLOW)
    
    # Clear screen
    screen.fill(BLACK)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    
    # Display each high score
    y_pos = 180
    for i, entry in enumerate(high_scores):
        rank_text = font.render(f"{i+1}.", True, WHITE)
        name_text = font.render(entry["name"], True, WHITE)
        score_text = font.render(str(entry["score"]), True, WHITE)
        level_text = font.render(f"Level {entry.get('level', 1)}", True, WHITE)
        
        screen.blit(rank_text, (WIDTH // 2 - 250, y_pos))
        screen.blit(name_text, (WIDTH // 2 - 200, y_pos))
        screen.blit(score_text, (WIDTH // 2 + 50, y_pos))
        screen.blit(level_text, (WIDTH // 2 + 150, y_pos))
        
        y_pos += 40
    
    continue_text = font.render("Press any key to continue", True, WHITE)
    screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT - 100))
    
    pygame.display.flip()
    
    # Wait for key press
    # Create a clock outside the loop
    clock = pygame.time.Clock()
    waiting = True
    while waiting:
        clock.tick(60)  # Limit the loop to 60 FPS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        
        # No need to call pygame.event.pump() as pygame.event.get() already processes the event queue
        pygame.display.update()  # Make sure the display updates
    
    # Return to welcome screen after viewing high scores
    welcome_screen()

# Ship selection screen
def select_ship():
    # Create ship options as polygons instead of images
    ship1 = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.polygon(ship1, BLUE, [(25, 0), (0, 50), (50, 50)])
    
    ship2 = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.polygon(ship2, GREEN, [(25, 0), (0, 50), (25, 35), (50, 50)])
    
    ship3 = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.polygon(ship3, RED, [(25, 0), (10, 30), (0, 50), (50, 50), (40, 30)])
    ships = [(ship1, 5), (ship2, 7), (ship3, 3)]  # (image, speed)
    
    font = pygame.font.Font(None, 36)
    title = font.render("Select Your Ship", True, WHITE)
    
    selected = None
    
    while selected is None:
        screen.fill(BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        # Display ship options
        for i, (ship_img, speed) in enumerate(ships):
            x = WIDTH // 4 * (i + 1)
            y = HEIGHT // 2
            
            # Draw ship
            ship_rect = ship_img.get_rect(center=(x, y))
            screen.blit(ship_img, ship_rect)
            
            # Draw ship info
            speed_text = font.render(f"Speed: {speed}", True, WHITE)
            screen.blit(speed_text, (x - speed_text.get_width()//2, y + 60))
            
            # Draw selection box
            pygame.draw.rect(screen, WHITE, (x - 60, y - 60, 120, 120), 2)
            
            # Check for mouse click
            mouse_pos = pygame.mouse.get_pos()
            if pygame.mouse.get_pressed()[0] and ship_rect.collidepoint(mouse_pos):
                selected = ships[i]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                # Number keys for quick selection
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    index = event.key - pygame.K_1
                    if 0 <= index < len(ships):
                        selected = ships[index]
        
        pygame.display.flip()
    
    return selected

# Welcome screen function
def welcome_screen():
    font_title = pygame.font.Font(None, 72)
    font = pygame.font.Font(None, 36)
    
    title = font_title.render("SPACE ASTEROID SHOOTER", True, YELLOW)
    start_text = font.render("Press ENTER to Start", True, WHITE)
    high_scores_text = font.render("Press H to View High Scores", True, WHITE)
    quit_text = font.render("Press ESC to Quit", True, WHITE)
    
    # Create a simple animated asteroid for the welcome screen
    asteroid_img = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.circle(asteroid_img, BROWN, (25, 25), 20)
    asteroid_rect = asteroid_img.get_rect(center=(WIDTH//2, 300))
    asteroid_speed = [2, 1]
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    running = False
                    game()
                elif event.key == pygame.K_h:
                    display_high_scores(load_high_scores())
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Move the asteroid
        asteroid_rect.x += asteroid_speed[0]
        asteroid_rect.y += asteroid_speed[1]
        
        # Bounce the asteroid off the edges
        if asteroid_rect.left < 0 or asteroid_rect.right > WIDTH:
            asteroid_speed[0] = -asteroid_speed[0]
        if asteroid_rect.top < 0 or asteroid_rect.bottom > HEIGHT:
            asteroid_speed[1] = -asteroid_speed[1]
        
        # Draw everything
        screen.fill(BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT//2))
        screen.blit(high_scores_text, (WIDTH//2 - high_scores_text.get_width()//2, HEIGHT//2 + 50))
        screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, HEIGHT//2 + 100))
        screen.blit(asteroid_img, asteroid_rect)
        
        pygame.display.flip()

# Main game function
def game():
    # Import math here for asteroid polygon generation
    import math
    
    # Level names
    LEVEL_NAMES = [
        "Solar Beginnings",        # Level 1
        "Asteroid Belt",          # Level 2
        "Nebula Storm",           # Level 3
        "Cosmic Chaos",           # Level 4
        "Galactic Gateway",       # Level 5
        "Supernova Surge",        # Level 6
        "Black Hole's Edge",      # Level 7
        "Quantum Quandary",       # Level 8
        "Dark Matter Domain",     # Level 9
        "Celestial Citadel",      # Level 10
        "Pulsar Paradise",        # Level 11
        "Starborn Sanctuary",     # Level 12
        "Void Vanguard",          # Level 13
        "Cosmic Cataclysm",       # Level 14
        "Universal Ultima",       # Level 15
        "Neutron Nexus",          # Level 16
        "Stellar Siege",          # Level 17
        "Wormhole Warriors",      # Level 18
        "Plasma Pandemonium",     # Level 19
        "Meteor Maelstrom",       # Level 20
        "Quasar Quest",           # Level 21
        "Gamma Ray Glory",        # Level 22
        "Cosmic Ray Chaos",       # Level 23
        "Starship Graveyard",     # Level 24
        "Temporal Tempest",       # Level 25
        "Dimensional Drift",      # Level 26
        "Binary Star Battle",     # Level 27
        "Magnetar Mayhem",        # Level 28
        "Cosmic Web Weaver",      # Level 29
        "Event Horizon",          # Level 30
        "Galactic Core",          # Level 31
        "Antimatter Assault",     # Level 32
        "Hyperspace Haven",       # Level 33
        "Singularity Storm",      # Level 34
        "Celestial Symphony",     # Level 35
        "Quantum Realm",          # Level 36
        "Cosmic String Theory",   # Level 37
        "Parallel Universe",      # Level 38
        "Time Wave Zero",         # Level 39
        "Multiverse Mayhem",      # Level 40
        "Cosmic Consciousness",   # Level 41
        "Infinity's Edge",        # Level 42
        "Reality Rift",           # Level 43
        "Dimensional Apex",       # Level 44
        "Quantum Supremacy",      # Level 45
        "Universal Nexus",        # Level 46
        "Cosmic Transcendence",   # Level 47
        "Eternal Equilibrium",    # Level 48
        "Ultimate Universe",      # Level 49
        "Omega Omnipotence"       # Level 50
    ]
    
    # Get player name
    player_name = get_player_name()
    
    # Select ship
    ship_img, ship_speed = select_ship()
    
    # Create sprite groups
    all_sprites = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    enemy_ships = pygame.sprite.Group()
    player_bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    bombs = pygame.sprite.Group()  # New group for bombs
    explosions = pygame.sprite.Group()  # New group for explosions
    
    # Create player ship
    player = Ship(ship_img, ship_speed, player_name)
    all_sprites.add(player)
    
    # Level settings
    level = 1
    level_score_threshold_delta = 1000  # Score needed to advance to next level
    level_score_threshold = level_score_threshold_delta
    asteroid_count = 6
    enemy_count = 2
    
    # Track if we just completed a boss level
    just_defeated_boss = False
    
    # Power-up settings
    power_up_chance = 0.25  # 25% chance per destroyed object
    last_power_up_time = pygame.time.get_ticks()
    power_up_min_delay = 5000  # Minimum 5 seconds between power-ups
    
    # Bomb spawn settings
    bomb_spawn_delay = 5000  # 5 seconds between bomb spawns
    last_bomb_time = pygame.time.get_ticks()
    
    # Create asteroids for initial level
    for i in range(asteroid_count):
        a = Asteroid(level)
        all_sprites.add(a)
        asteroids.add(a)

    # Create enemy ships for initial level
    for i in range(enemy_count):
        e = EnemyShip(level)
        all_sprites.add(e)
        enemy_ships.add(e)
    
    # Score
    score = 0
    font = pygame.font.Font(None, 36)
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    # Level transition variables
    level_transition = False
    transition_start_time = 0
    transition_duration = 1000  # 1 second
    
    # Add boss sprite group
    boss_group = pygame.sprite.Group()
    boss_bullets = pygame.sprite.Group()
    
    while running:
        # Keep loop running at the right speed
        clock.tick(60)
        
        # Process input (events)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and not level_transition:
                    bullets = player.shoot()
                    for bullet in bullets:
                        all_sprites.add(bullet)
                        player_bullets.add(bullet)
        
        # Spawn new bomb periodically
        now = pygame.time.get_ticks()
        if now - last_bomb_time > bomb_spawn_delay:
            bomb = StrayBomb(random.randint(0, WIDTH-20), -20)
            all_sprites.add(bomb)
            bombs.add(bomb)
            last_bomb_time = now
        
        # Check if we need to advance to the next level
        if score >= level_score_threshold and not level_transition:
            level += 1
            level_transition = True
            transition_start_time = pygame.time.get_ticks()
            
            # Clear existing objects
            for sprite in [asteroids, enemy_ships, power_ups, bombs]:
                for obj in sprite:
                    obj.kill()
            
            # Add more asteroids and enemies for the new level
            asteroid_count = 6 + level  # Scale with level
            enemy_count = 2 + level // 2  # Add enemy every 2 levels
            
            # Update score threshold for next level
            level_score_threshold = score + level_score_threshold_delta
            
            # Reset boss defeat flag when moving to a new level
            just_defeated_boss = False
        
        # Handle level transition
        if level_transition:
            current_time = pygame.time.get_ticks()
            if current_time - transition_start_time > transition_duration:
                level_transition = False
                
                # Only spawn regular enemies if it's not a boss level
                if level % 5 != 0:
                    # Create new asteroids and enemies for the new level
                    for i in range(asteroid_count):
                        a = Asteroid(level)
                        all_sprites.add(a)
                        asteroids.add(a)
                    
                    for i in range(enemy_count):
                        e = EnemyShip(level)
                        all_sprites.add(e)
                        enemy_ships.add(e)
        
        # Check if it's a boss level (every 5 levels)
        if level % 5 == 0 and not boss_group and not level_transition and not just_defeated_boss:
            # Clear all enemies and asteroids
            for sprite in [asteroids, enemy_ships, power_ups, bombs]:
                for obj in sprite:
                    obj.kill()
            # Spawn boss
            boss = Boss(level)
            all_sprites.add(boss)
            boss_group.add(boss)
            
            # Special effects for Omega Boss entrance
            if level == 50:
                # Create multiple explosion effects
                for _ in range(5):
                    x = random.randint(0, WIDTH)
                    y = random.randint(0, HEIGHT//2)
                    explosion = Explosion(x, y)
                    explosion.radius = 200
                    explosion.growth_rate = 30
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                sound_manager.play_explosion()
                pygame.time.wait(100)
                sound_manager.play_explosion()
            else:
                sound_manager.play_explosion()  # Normal entrance sound
            
            # Modify boss attributes for level 50
            if level == 50:
                boss.max_health = 5000  # Much more health
                boss.health = boss.max_health
                boss.shoot_delay = 300  # Faster shooting
                boss.pattern_duration = 2000  # Faster pattern changes
        
        # Update boss and handle boss bullets
        if boss_group:
            # Boss shooting
            for boss in boss_group:
                new_bullets = boss.shoot()
                for bullet in new_bullets:
                    all_sprites.add(bullet)
                    boss_bullets.add(bullet)
            
            # Check for player bullet hits on boss
            hits = pygame.sprite.groupcollide(boss_group, player_bullets, False, True)
            for boss, bullets in hits.items():
                boss.health -= 10 * len(bullets)
                sound_manager.play_collision()  # Hit sound
                
                # Create small explosion effect for each hit
                for bullet in bullets:
                    explosion = Explosion(bullet.rect.centerx, bullet.rect.centery)
                    explosion.radius = 30  # Smaller explosion for hits
                    explosion.growth_rate = 5
                    explosion.max_frames = 5
                    all_sprites.add(explosion)
                
                # Check if boss is defeated
                if boss.health <= 0:
                    boss.kill()
                    # Create massive explosion
                    explosion = Explosion(boss.rect.centerx, boss.rect.centery)
                    explosion.radius = 400  # Massive explosion
                    explosion.growth_rate = 40
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    sound_manager.play_explosion()
                    boss_bonus = 5000 * (level // 5)  # Big score bonus for defeating boss
                    score += boss_bonus
                    # Set next level threshold right after boss bonus
                    level_score_threshold = score + level_score_threshold_delta
                    # Set flag to prevent immediate boss respawn
                    just_defeated_boss = True
                    
                    # Spawn regular enemies for the next level
                    for i in range(asteroid_count):
                        a = Asteroid(level)
                        all_sprites.add(a)
                        asteroids.add(a)
                    
                    for i in range(enemy_count):
                        e = EnemyShip(level)
                        all_sprites.add(e)
                        enemy_ships.add(e)
        
        # Update sprites if not in level transition
        if not level_transition:
            all_sprites.update()
            
            # Enemy ships shoot
            for enemy in enemy_ships:
                bullet = enemy.shoot()
                if bullet:
                    all_sprites.add(bullet)
                    enemy_bullets.add(bullet)
            
            # Check for bomb collisions with all objects and create explosions
            # Bomb collision with asteroids
            hits = pygame.sprite.groupcollide(bombs, asteroids, True, True)
            for bomb in hits:
                explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                all_sprites.add(explosion)
                explosions.add(explosion)
                sound_manager.play_explosion()  # Play explosion sound
                score += 25  # Bonus points for explosion kills
                a = Asteroid(level)  # Respawn asteroid
                all_sprites.add(a)
                asteroids.add(a)
            
            # Bomb collision with enemy ships
            hits = pygame.sprite.groupcollide(bombs, enemy_ships, True, True)
            for bomb in hits:
                explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                all_sprites.add(explosion)
                explosions.add(explosion)
                sound_manager.play_explosion()  # Play explosion sound
                score += 25  # Bonus points for explosion kills
                e = EnemyShip(level)  # Respawn enemy ship
                all_sprites.add(e)
                enemy_ships.add(e)
            
            # Bomb collision with enemy bullets
            hits = pygame.sprite.groupcollide(bombs, enemy_bullets, True, True)
            for bomb in hits:
                explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                all_sprites.add(explosion)
                explosions.add(explosion)
                sound_manager.play_explosion()  # Play explosion sound
            
            # Check for bullet/bomb collisions and create explosions
            hits = pygame.sprite.groupcollide(bombs, player_bullets, True, True)
            for bomb in hits:
                explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                all_sprites.add(explosion)
                explosions.add(explosion)
                sound_manager.play_explosion()  # Play explosion sound
                
                # Check what's caught in explosion radius
                for sprite_group in [asteroids, enemy_ships, enemy_bullets, power_ups, bombs]:
                    for sprite in sprite_group:
                        distance = math.sqrt(
                            (sprite.rect.centerx - explosion.center_x) ** 2 +
                            (sprite.rect.centery - explosion.center_y) ** 2
                        )
                        if distance <= explosion.radius:
                            if sprite_group == asteroids or sprite_group == enemy_ships:
                                score += 25  # Bonus points for explosion kills
                            sprite.kill()
            
            # Check for bullet/asteroid collisions
            hits = pygame.sprite.groupcollide(asteroids, player_bullets, True, True)
            for hit in hits:
                score += 50
                sound_manager.play_collision()  # Play collision sound
                
                # Chance to spawn power-up
                if (random.random() < power_up_chance and 
                    now - last_power_up_time > power_up_min_delay):
                    power_up = PowerUp(hit.rect.centerx, hit.rect.centery)
                    all_sprites.add(power_up)
                    power_ups.add(power_up)
                    last_power_up_time = now
                
                a = Asteroid(level)
                all_sprites.add(a)
                asteroids.add(a)
            
            # Check for bullet/enemy ship collisions
            hits = pygame.sprite.groupcollide(enemy_ships, player_bullets, True, True)
            for hit in hits:
                score += 100
                sound_manager.play_collision()  # Play collision sound
                
                # Chance to spawn power-up
                if (random.random() < 0.30 and  # 30% chance from enemy ships
                    now - last_power_up_time > power_up_min_delay):
                    power_up = PowerUp(hit.rect.centerx, hit.rect.centery)
                    all_sprites.add(power_up)
                    power_ups.add(power_up)
                    last_power_up_time = now
                
                e = EnemyShip(level)
                all_sprites.add(e)
                enemy_ships.add(e)
            
            # Check for player collisions with bombs first
            bomb_hits = pygame.sprite.spritecollide(player, bombs, True)
            if bomb_hits and not player.is_invincible:
                for bomb in bomb_hits:
                    explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    sound_manager.play_explosion()  # Play explosion sound
                    
                    # Check what's caught in explosion radius
                    for sprite_group in [asteroids, enemy_ships, enemy_bullets, power_ups, bombs]:
                        for sprite in sprite_group:
                            distance = math.sqrt(
                                (sprite.rect.centerx - explosion.center_x) ** 2 +
                                (sprite.rect.centery - explosion.center_y) ** 2
                            )
                            if distance <= explosion.radius:
                                if sprite_group == asteroids or sprite_group == enemy_ships:
                                    score += 25  # Bonus points for explosion kills
                                sprite.kill()
                running = False
            elif bomb_hits and player.is_invincible:
                # Still create explosion but don't end game
                for bomb in bomb_hits:
                    explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    
                    # Check what's caught in explosion radius (excluding player)
                    for sprite_group in [asteroids, enemy_ships, enemy_bullets, power_ups, bombs]:
                        for sprite in sprite_group:
                            distance = math.sqrt(
                                (sprite.rect.centerx - explosion.center_x) ** 2 +
                                (sprite.rect.centery - explosion.center_y) ** 2
                            )
                            if distance <= explosion.radius:
                                if sprite_group == asteroids or sprite_group == enemy_ships:
                                    score += 25  # Bonus points for explosion kills
                                sprite.kill()
            
            # Check for player/power-up collisions
            hits = pygame.sprite.spritecollide(player, power_ups, True)
            for hit in hits:
                player.add_power_up(hit.type)
                sound_manager.play_powerup()  # Play power-up collection sound
            
            # Check for player collisions with other hazards
            for hazard_group in [asteroids, enemy_ships, enemy_bullets]:
                hits = pygame.sprite.spritecollide(player, hazard_group, False)
                if hits and not player.is_invincible:
                    sound_manager.play_collision()  # Play collision sound
                    running = False
        
        # Draw / render
        screen.fill(BLACK)
        
        if level_transition:
            # Draw level transition screen
            level_font = pygame.font.Font(None, 72)
            level_text = level_font.render(f"LEVEL {level}", True, YELLOW)
            screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 - 100))
            
            # Draw level name
            level_name = LEVEL_NAMES[min(level - 1, len(LEVEL_NAMES) - 1)]  # Use last name for levels beyond the list
            name_font = pygame.font.Font(None, 48)
            name_text = name_font.render(level_name, True, ORANGE)
            screen.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT//2 - 20))
            
            # Draw level description
            desc_font = pygame.font.Font(None, 36)
            desc_text = desc_font.render("Prepare for the next challenge!", True, WHITE)
            screen.blit(desc_text, (WIDTH//2 - desc_text.get_width()//2, HEIGHT//2 + 40))
        else:
            # Draw game elements
            all_sprites.draw(screen)
            
            # Draw score at top left
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
            
            # Draw level name centered at top
            current_level_name = LEVEL_NAMES[min(level - 1, len(LEVEL_NAMES) - 1)]
            level_name_text = font.render(current_level_name, True, ORANGE)
            screen.blit(level_name_text, (WIDTH//2 - level_name_text.get_width()//2, 10))
            
            # Draw level number at top right
            level_text = font.render(f"Level {level}", True, WHITE)
            screen.blit(level_text, (WIDTH - level_text.get_width() - 10, 10))
            
            # Draw player name and invincible status if active
            name_color = YELLOW if player.is_invincible else WHITE
            name_text = font.render(f"Player: {player_name}", True, name_color)
            screen.blit(name_text, (10, 50))
            
            # Draw progress to next level
            next_level_score = level_score_threshold
            progress_text = font.render(f"Next level: {score}/{next_level_score}", True, WHITE)
            screen.blit(progress_text, (WIDTH - progress_text.get_width() - 10, 50))
            
            # Draw active power-ups
            if player.power_ups:
                power_up_text = []
                if PowerUp.RAPID_FIRE in player.power_ups:
                    power_up_text.append("RAPID FIRE")
                if PowerUp.DOUBLE_SHOT in player.power_ups:
                    power_up_text.append("DOUBLE SHOT")
                if power_up_text:
                    power_up_display = font.render(" + ".join(power_up_text), True, YELLOW)
                    screen.blit(power_up_display, (10, 90))
                    
                # Draw power-up timer
                remaining = (player.power_up_duration - (pygame.time.get_ticks() - player.power_up_start)) // 1000
                if remaining > 0:
                    timer_text = font.render(f"({remaining}s)", True, YELLOW)
                    screen.blit(timer_text, (10, 120))
        
        # Draw boss health bar if boss exists
        if boss_group:
            boss = boss_group.sprites()[0]
            bar_width = WIDTH - 100
            bar_height = 20
            health_percent = boss.health / boss.max_health
            
            if level == 50:  # Special health bar for Omega Boss
                # Draw multiple health bars with different colors
                colors = [(255, 0, 0), (255, 0, 255), (0, 255, 255)]  # Red, Purple, Cyan
                for i, color in enumerate(colors):
                    y_offset = i * 15
                    pygame.draw.rect(screen, color, (50, 20 + y_offset, bar_width, 5))
                    pygame.draw.rect(screen, (255, 255, 255), 
                                   (50, 20 + y_offset, bar_width * health_percent, 5))
                
                # Draw boss name with special effects
                boss_name = "THE OMEGA BOSS - DESTROYER OF WORLDS"
                boss_text = font.render(boss_name, True, (255, 0, 0))
                shadow_text = font.render(boss_name, True, (255, 255, 0))
                screen.blit(shadow_text, (WIDTH//2 - boss_text.get_width()//2 + 2, 47))
                screen.blit(boss_text, (WIDTH//2 - boss_text.get_width()//2, 45))
            else:
                # Regular boss health bar
                pygame.draw.rect(screen, RED, (50, 20, bar_width, bar_height))
                pygame.draw.rect(screen, GREEN, (50, 20, bar_width * health_percent, bar_height))
        
        # Flip the display
        pygame.display.flip()
    
    # Update high scores
    high_scores = update_high_scores(player_name, score, level)
    
    # Game over screen
    game_over_font = pygame.font.Font(None, 72)
    game_over_text = game_over_font.render("GAME OVER", True, RED)
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 150))
    
    final_score = font.render(f"Final Score: {score}", True, WHITE)
    screen.blit(final_score, (WIDTH//2 - final_score.get_width()//2, HEIGHT//2 - 80))
    
    level_reached = font.render(f"Level Reached: {level}", True, WHITE)
    screen.blit(level_reached, (WIDTH//2 - level_reached.get_width()//2, HEIGHT//2 - 40))
    
    player_name_text = font.render(f"Player: {player_name}", True, WHITE)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, HEIGHT//2))
    
    high_score_text = font.render("Press H to view high scores", True, WHITE)
    screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, HEIGHT//2 + 40))
    
    restart_text = font.render("Press R to restart or ESC to quit", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 80))
    
    pygame.display.flip()
    
    # Wait for restart or quit
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                    game()  # Restart game
                elif event.key == pygame.K_h:
                    display_high_scores(high_scores)
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

# Start the game
if __name__ == "__main__":
    welcome_screen()
    pygame.quit()
