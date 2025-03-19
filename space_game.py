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

# Screen dimensions
WIDTH, HEIGHT = 1280, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Asteroid Shooter")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (100, 200, 255)

# Grey shades for asteroids and effects
GREY = (128, 128, 128)
DARK_GREY = (64, 64, 64)
MEDIUM_GREY = (96, 96, 96)
LIGHT_GREY = (192, 192, 192)
CRATER_GREY = (48, 48, 48)

# Initialize game control variables
ESC_QUIT_GAME = False
ESC_WELCOME_SCREEN = True
total_score = 0  # Initialize global total_score

# Add after the imports at the top
FULLSCREEN = False

def toggle_fullscreen():
    global FULLSCREEN, screen, WIDTH, HEIGHT
    FULLSCREEN = not FULLSCREEN
    if FULLSCREEN:
        # Store the current window size before going fullscreen
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        WIDTH, HEIGHT = screen.get_size()
    else:
        # Return to windowed mode with original size
        WIDTH, HEIGHT = 800, 600  # Original window size
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_particle(self, x, y, color, velocity_x, velocity_y, lifetime, size=2, fade=True, glow=False, z=1.0):
        particle = {
            'x': x,
            'y': y,
            'z': z,  # Depth factor (0.1 to 1.0)
            'color': color,
            'velocity_x': velocity_x * z,  # Particles closer move faster
            'velocity_y': velocity_y * z,
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'size': size * z,  # Larger particles appear closer
            'fade': fade,
            'glow': glow,
            'alpha': 255
        }
        self.particles.append(particle)

    def update(self):
        # Update all particles in a single list comprehension for better performance
        self.particles = [p for p in self.particles if p['lifetime'] > 0]
        
        for p in self.particles:
            p['x'] += p['velocity_x']
            p['y'] += p['velocity_y']
            p['lifetime'] -= 1
            
            if p['fade']:
                fade_ratio = p['lifetime'] / p['max_lifetime']
                p['alpha'] = int(255 * fade_ratio)

    def draw(self, surface):
        # Sort particles by depth for proper rendering
        sorted_particles = sorted(self.particles, key=lambda p: p['z'])
        
        # Create a surface for glowing particles
        if any(p['glow'] for p in sorted_particles):
            glow_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        for p in sorted_particles:
            pos = (int(p['x']), int(p['y']))
            
            # Calculate color with alpha
            color = list(p['color'])
            if len(color) < 4:
                color.append(p['alpha'])
            else:
                color[3] = p['alpha']
            
            # Draw particle shadow for depth effect
            if p['z'] > 0.5:  # Only draw shadows for closer particles
                shadow_offset = int(4 * p['z'])
                shadow_size = int(p['size'] * 1.5)
                shadow_alpha = int(100 * p['z'])
                shadow_surface = pygame.Surface((shadow_size * 2, shadow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(shadow_surface, (0, 0, 0, shadow_alpha), 
                                 (shadow_size, shadow_size), shadow_size)
                surface.blit(shadow_surface, 
                           (pos[0] - shadow_size + shadow_offset, 
                            pos[1] - shadow_size + shadow_offset))
            
            # Draw glowing effect
            if p['glow']:
                glow_size = int(p['size'] * 2)
                glow_color = (*p['color'][:3], int(p['alpha'] * 0.5))
                glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)
                surface.blit(glow_surface, (pos[0] - glow_size, pos[1] - glow_size))
            
            # Draw main particle
            pygame.draw.circle(surface, color, pos, int(p['size']))

class StarField:
    def __init__(self, num_stars=100):
        self.stars = []
        # Create multiple layers of stars for parallax effect
        for _ in range(num_stars):
            # z determines the star's depth (0.1 to 1.0)
            z = random.uniform(0.1, 1.0)
            self.stars.append({
                'x': random.randrange(0, WIDTH),
                'y': random.randrange(0, HEIGHT),
                'z': z,  # Depth factor
                'size': max(1, int(3 * z)),  # Larger stars appear closer
                'brightness': int(255 * z),  # Brighter stars appear closer
                'speed': 2 * z  # Stars closer to viewer move faster
            })
    
    def update(self, player_velocity_x=0, player_velocity_y=0):
        for star in self.stars:
            # Parallax movement based on star's depth
            move_x = -player_velocity_x * star['z']
            move_y = -player_velocity_y * star['z']
            
            star['x'] += move_x
            star['y'] += move_y
            
            # Wrap stars around screen
            if star['x'] < 0:
                star['x'] = WIDTH
            elif star['x'] > WIDTH:
                star['x'] = 0
            if star['y'] < 0:
                star['y'] = HEIGHT
            elif star['y'] > HEIGHT:
                star['y'] = 0
    
    def draw(self, surface):
        # Draw stars from back to front
        sorted_stars = sorted(self.stars, key=lambda x: x['z'])
        for star in sorted_stars:
            # Create a glowing effect for closer stars
            if star['z'] > 0.7:  # Only closest stars glow
                glow_size = int(star['size'] * 2)
                glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                glow_color = (255, 255, 255, int(100 * star['z']))
                pygame.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)
                surface.blit(glow_surface, (star['x'] - glow_size, star['y'] - glow_size))
            
            # Draw the star
            color = (star['brightness'], star['brightness'], star['brightness'])
            pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), star['size'])

# Initialize particle system and star field globally
particle_system = ParticleSystem()
star_field = StarField(150)  # Increased number of stars for more depth

def create_space_dust(x, y, count=1):
    for _ in range(count):
        z = random.uniform(0.1, 1.0)  # Random depth
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 3) * z  # Faster if closer
        velocity_x = math.cos(angle) * speed
        velocity_y = math.sin(angle) * speed
        particle_system.add_particle(
            x, y,
            (200, 200, 255),
            velocity_x, velocity_y,
            random.randint(20, 40),
            size=1,
            fade=True,
            glow=False,
            z=z
        )

def create_engine_trail(x, y, color=(255, 165, 0)):
    z = random.uniform(0.6, 1.0)  # Engine trails are always closer
    particle_system.add_particle(
        x, y,
        color,
        random.uniform(-0.5, 0.5),
        random.uniform(1, 2),
        random.randint(10, 20),
        size=2,
        fade=True,
        glow=True,
        z=z
    )

def create_explosion_particles(x, y, intensity=1.0):
    num_particles = int(20 * intensity)
    for _ in range(num_particles):
        z = random.uniform(0.3, 1.0)  # Varying depths for more realistic explosion
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 5) * intensity * z
        velocity_x = math.cos(angle) * speed
        velocity_y = math.sin(angle) * speed
        
        # Core explosion particles (orange/red)
        particle_system.add_particle(
            x, y,
            (255, random.randint(100, 165), 0),
            velocity_x, velocity_y,
            random.randint(20, 40),
            size=3 * intensity,
            fade=True,
            glow=True,
            z=z
        )
        
        # Smoke particles (grey)
        smoke_z = z * 0.8  # Smoke slightly further back
        particle_system.add_particle(
            x, y,
            (100, 100, 100),
            velocity_x * 0.5, velocity_y * 0.5,
            random.randint(30, 60),
            size=4 * intensity,
            fade=True,
            glow=False,
            z=smoke_z
        )
        
        # Spark particles
        if random.random() < 0.3:  # 30% chance for each spark
            spark_z = z * 1.2  # Sparks slightly closer
            particle_system.add_particle(
                x, y,
                (255, 255, 200),
                velocity_x * 1.5, velocity_y * 1.5,
                random.randint(10, 20),
                size=1,
                fade=True,
                glow=True,
                z=spark_z
            )

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

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        self.level = level
        
        # Size based on level
        base_size = random.randint(30, 60)
        size_multiplier = 1 + (level - 1) * 0.2  # Increase size with level
        self.size = int(base_size * size_multiplier)
        
        # Create surface with alpha for smooth edges
        self.original_image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.image = self.original_image
        self.rect = self.image.get_rect()
        
        # Random starting position
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        
        # Generate polygon points for irregular shape
        num_points = random.randint(12, 16)
        angles = [i * (2 * math.pi / num_points) for i in range(num_points)]
        self.points = []
        for angle in angles:
            # Add some noise to radius for irregularity
            radius = self.size * (0.8 + random.random() * 0.4)
            x = self.size + math.cos(angle) * radius
            y = self.size + math.sin(angle) * radius
            self.points.append((x, y))
        
        # Base color varies slightly with random grey tone
        base_grey = random.randint(-20, 20)  # Random variation
        self.color = (
            min(255, max(0, MEDIUM_GREY[0] + base_grey)),
            min(255, max(0, MEDIUM_GREY[1] + base_grey)),
            min(255, max(0, MEDIUM_GREY[2] + base_grey))
        )
        
        # Draw the asteroid
        pygame.draw.polygon(self.original_image, self.color, self.points)
        
        # Add craters
        num_craters = random.randint(3, 7)
        for _ in range(num_craters):
            crater_x = random.randint(self.size // 2, int(self.size * 1.5))
            crater_y = random.randint(self.size // 2, int(self.size * 1.5))
            crater_radius = random.randint(3, 8)
            pygame.draw.circle(self.original_image, CRATER_GREY, (crater_x, crater_y), crater_radius)
        
        # Add highlights for 3D effect
        for point in self.points:
            pygame.draw.circle(self.original_image, LIGHT_GREY, (int(point[0]), int(point[1])), 2)
        
        # Physics attributes
        self.velocity_x = random.uniform(-2, 2)
        self.velocity_y = random.uniform(2, 4) + level * 0.5
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-3, 3)
        
        # Debris system
        self.debris = []
        self.last_debris = 0
        self.debris_interval = 100  # Milliseconds between debris spawns
        
    def update(self):
        # Update position with velocity
        self.rect.y += self.velocity_y
        self.rect.x += self.velocity_x
        
        # Rotate asteroid
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center
        
        # Add occasional debris
        self.last_debris += 1
        if self.last_debris >= self.debris_interval:  # Every 100 frames
            self.last_debris = 0
            if random.random() < 0.3:  # 30% chance
                self.debris.append({
                    'x': self.rect.centerx,
                    'y': self.rect.centery,
                    'velocity_x': random.uniform(-1, 1),
                    'velocity_y': random.uniform(-1, 1),
                    'lifetime': 30,  # Frames the debris will exist
                    'color': self.color
                })
        
        # Update existing debris
        for debris in self.debris[:]:  # Copy list to safely remove items
            debris['x'] += debris['velocity_x']
            debris['y'] += debris['velocity_y']
            debris['lifetime'] -= 1
            if debris['lifetime'] <= 0:
                self.debris.remove(debris)
        
        # If asteroid goes off screen, respawn it
        if (self.rect.top > HEIGHT + 10 or 
            self.rect.left < -25 or 
            self.rect.right > WIDTH + 25):
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.velocity_y = random.uniform(2, 4) + self.level * 0.5
            self.velocity_x = random.uniform(-2, 2)
    
    def draw_debris(self, surface):
        for debris in self.debris:
            alpha = min(255, debris['lifetime'] * 8)  # Fade out as lifetime decreases
            color = debris['color'] + (alpha,)  # Add alpha value
            pygame.draw.circle(surface, color, (int(debris['x']), int(debris['y'])), 1)

class EnemyShip(pygame.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        size = 40
        self.base_size = size
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw the enemy ship
        points = [(size//2, 0), (0, size), (size//2, size*3//4), (size, size)]
        pygame.draw.polygon(self.image, RED, points)
        pygame.draw.polygon(self.image, (200, 0, 0), points, 2)
        
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        
        # Start near vanishing point
        angle = random.uniform(0, 2 * math.pi)
        distance = random.randint(20, 50)
        self.rect.centerx = self.vanishing_point[0] + math.cos(angle) * distance
        self.rect.centery = self.vanishing_point[1] + math.sin(angle) * distance
        
        self.z = random.uniform(0.1, 0.3)
        self.z_speed = 0.004 * level

    def update(self):
        self.update_perspective()
        if self.z >= 1.0:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    # Power-up types
    RAPID_FIRE = "rapid_fire"
    DOUBLE_SHOT = "double_shot"
    TRIPLE_SHOT = "triple_shot"
    SUPER_RAPID_FIRE = "super_rapid_fire"
    RAPID_MOVEMENT = "rapid_movement"
    
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        
        # Select power-up type with weighted probabilities
        self.type = random.choice([
            self.RAPID_FIRE,
            self.DOUBLE_SHOT, self.DOUBLE_SHOT, self.DOUBLE_SHOT,  # Higher chance for double shot
            self.TRIPLE_SHOT,
            self.SUPER_RAPID_FIRE,
            self.RAPID_MOVEMENT
        ])
        
        size = 30
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw power-up based on type
        if self.type == self.RAPID_FIRE:
            color = YELLOW
            # Draw lightning bolt
            points = [(size//2, 0), (size, size//2), (size*2//3, size*3//5), (size, size), 
                     (0, size*3//5), (size//3, size*2//5)]
            pygame.draw.polygon(self.image, color, points)
        elif self.type == self.DOUBLE_SHOT:
            color = PURPLE
            # Draw double circle
            pygame.draw.circle(self.image, color, (size//4, size//2), size//4)
            pygame.draw.circle(self.image, color, (size*3//4, size//2), size//4)
        elif self.type == self.TRIPLE_SHOT:
            color = RED
            # Draw triple circle
            pygame.draw.circle(self.image, color, (size//5, size//2), size//5)
            pygame.draw.circle(self.image, color, (size//2, size//4), size//5)
            pygame.draw.circle(self.image, color, (size*4//5, size//2), size//5)
        elif self.type == self.SUPER_RAPID_FIRE:
            color = ORANGE
            # Draw double lightning bolt
            points1 = [(size//4, 0), (size//2, size//2), (size//3, size*3//5), 
                      (size//2, size), (0, size*3//5), (size//6, size//2)]
            points2 = [(size*3//4, 0), (size, size//2), (size*5//6, size*3//5), 
                      (size, size), (size//2, size*3//5), (size*2//3, size//2)]
            pygame.draw.polygon(self.image, color, points1)
            pygame.draw.polygon(self.image, color, points2)
        else:  # RAPID_MOVEMENT
            color = LIGHT_BLUE
            # Draw speed arrows
            pygame.draw.polygon(self.image, color, [(0, size//2), (size//2, size//4), (size//2, size*3//4)])
            pygame.draw.polygon(self.image, color, [(size//2, size//2), (size, size//4), (size, size*3//4)])
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Movement attributes
        self.speedy = random.randrange(2, 5)
        self.speedx = random.randrange(-2, 2)

    def update(self):
        # Move the power-up
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        
        # Remove if it goes off screen
        if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 25:
            self.kill()

class StrayBomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        
        size = 20
        self.base_size = size
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw bomb
        pygame.draw.circle(self.image, RED, (size//2, size//2), size//2)
        pygame.draw.circle(self.image, (200, 0, 0), (size//2, size//2), size//2 - 2)
        
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        
        # Start near vanishing point
        angle = random.uniform(0, 2 * math.pi)
        distance = random.randint(20, 50)
        self.rect.centerx = self.vanishing_point[0] + math.cos(angle) * distance
        self.rect.centery = self.vanishing_point[1] + math.sin(angle) * distance
        
        self.z = random.uniform(0.1, 0.3)
        self.z_speed = 0.005

    def update(self):
        self.update_perspective()
        if self.z >= 1.0:
            self.kill()

# Ship class
class Ship(pygame.sprite.Sprite):
    def __init__(self, image, speed, player_name=""):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 100
        self.player_name = player_name  # Store player name
        
        # Apply speed boost from shop
        speed_boost = next((item.effect_value for item in SHOP_ITEMS 
                          if item.effect_type == "speed" and item.purchased), 0)
        self.base_speed = speed + speed_boost
        self.speed = self.base_speed
        
        # Apply fire rate boost from shop
        fire_rate_boost = next((item.effect_value for item in SHOP_ITEMS 
                              if item.effect_type == "fire_rate" and item.purchased), 1)
        self.base_shoot_delay = int(250 / fire_rate_boost)
        self.shoot_delay = self.base_shoot_delay
        
        self.last_shot = pygame.time.get_ticks()
        
        # Apply extra health from shop
        self.extra_health = next((item.effect_value for item in SHOP_ITEMS 
                                if item.effect_type == "health" and item.purchased), 0)
        
        # Apply shield from shop
        self.shield_time = next((item.effect_value for item in SHOP_ITEMS 
                               if item.effect_type == "shield_time" and item.purchased), 0)
        if self.shield_time > 0:
            self.is_invincible = True
            self.shield_start = pygame.time.get_ticks()
        else:
            self.is_invincible = player_name == "12345"  # Set initial invincibility
        
        # Apply starting power-ups from shop
        self.power_ups = set()
        start_powerup = next((item.effect_value for item in SHOP_ITEMS 
                            if item.effect_type == "start_powerup" and item.purchased), None)
        if start_powerup:
            self.power_ups.add(start_powerup)
        
        self.power_up_start = 0
        self.power_up_duration = 50000
        
        # Movement boundaries
        self.min_y = 50
        self.max_y = HEIGHT - 50
        
        # Physics attributes - adjusted for better control
        self.velocity_x = 0
        self.velocity_y = 0
        self.max_velocity = 8  # Reduced from 15
        self.thrust = 1.0  # Increased from 0.5
        self.friction = 0.85  # Increased from 0.98 (more friction)
        self.rotation = 0
        self.rotation_speed = 3
        
        # Add deceleration when no keys are pressed
        self.deceleration = 0.92  # New attribute for quick stopping
    
    def update(self):
        # Update shield timer
        if self.shield_time > 0:
            now = pygame.time.get_ticks()
            if now - self.shield_start > self.shield_time * 1000:  # Convert to milliseconds
                self.shield_time = 0
                # Only disable invincibility if not using the special name
                if self.player_name != "12345":
                    self.is_invincible = False
        
        # Get keyboard input
        keys = pygame.key.get_pressed()
        movement_speed = self.speed * 2 if PowerUp.RAPID_MOVEMENT in self.power_ups else self.speed
        
        # Track if any movement keys are pressed
        moving = False
        
        # Apply thrust based on key presses with improved control
        if keys[pygame.K_LEFT]:
            self.velocity_x -= self.thrust * movement_speed * 0.5
            self.rotation = min(self.rotation + self.rotation_speed, 20)
            moving = True
        if keys[pygame.K_RIGHT]:
            self.velocity_x += self.thrust * movement_speed * 0.5
            self.rotation = max(self.rotation - self.rotation_speed, -20)
            moving = True
        if keys[pygame.K_UP]:
            self.velocity_y -= self.thrust * movement_speed * 0.5
            moving = True
        if keys[pygame.K_DOWN]:
            self.velocity_y += self.thrust * movement_speed * 0.5
            moving = True
        
        # Apply stronger deceleration when no movement keys are pressed
        if not moving:
            self.velocity_x *= self.deceleration
            self.velocity_y *= self.deceleration
            if abs(self.velocity_x) < 0.1: self.velocity_x = 0
            if abs(self.velocity_y) < 0.1: self.velocity_y = 0
        
        # Reset rotation when not turning
        if not (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]):
            self.rotation = self.rotation * 0.8  # Faster rotation reset
        
        # Apply friction
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        
        # Limit maximum velocity
        velocity_magnitude = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if velocity_magnitude > self.max_velocity:
            scale = self.max_velocity / velocity_magnitude
            self.velocity_x *= scale
            self.velocity_y *= scale
        
        # Update position
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
        # Keep ship on screen with bounce effect
        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity_x = abs(self.velocity_x) * 0.2  # Reduced bounce
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.velocity_x = -abs(self.velocity_x) * 0.2  # Reduced bounce
            
        if self.rect.top < self.min_y:
            self.rect.top = self.min_y
            self.velocity_y = abs(self.velocity_y) * 0.2  # Reduced bounce
        if self.rect.bottom > self.max_y:
            self.rect.bottom = self.max_y
            self.velocity_y = -abs(self.velocity_y) * 0.2  # Reduced bounce
            
        # Check power-up duration
        now = pygame.time.get_ticks()
        if self.power_ups and now - self.power_up_start > self.power_up_duration:
            self.power_ups.clear()
            self.shoot_delay = self.base_shoot_delay
            self.speed = self.base_speed
        
        # Maintain invincibility for special name
        if self.player_name == "12345":
            self.is_invincible = True
        
        # Rest of the update code...
        super().update()

    def add_power_up(self, power_up_type):
        self.power_ups.add(power_up_type)
        self.power_up_start = pygame.time.get_ticks()
        
        # Handle shooting power-ups
        if power_up_type == PowerUp.RAPID_FIRE:
            self.shoot_delay = self.base_shoot_delay // 2  # Twice as fast
        elif power_up_type == PowerUp.SUPER_RAPID_FIRE:
            self.shoot_delay = self.base_shoot_delay // 4  # Four times as fast
        elif power_up_type == PowerUp.RAPID_MOVEMENT:
            self.speed = self.base_speed * 2  # Twice as fast movement
        
        # Triple shot and double shot don't need special handling here
        # as they are handled in the shoot() method
        
        # Play power-up sound
        sound_manager.play_powerup()
        
        # Print debug info
        print(f"Power-up collected: {power_up_type}")
        print(f"Active power-ups: {self.power_ups}")
        print(f"Current shoot delay: {self.shoot_delay}")
        print(f"Current speed: {self.speed}")

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            sound_manager.play_laser()  # Play laser sound
            
            bullets = []
            # Count number of double shot power-ups for multiplicative effect
            double_shot_count = sum(1 for pu in self.power_ups if pu == PowerUp.DOUBLE_SHOT)
            shot_multiplier = 2 ** double_shot_count  # 1 double shot = 2x, 2 double shots = 4x, etc.
            
            if PowerUp.TRIPLE_SHOT in self.power_ups:
                # Base triple shot pattern
                base_pattern = [
                    (self.rect.centerx, self.rect.top, -1, 0),  # Center
                    (self.rect.centerx - 20, self.rect.top, -1, -15),  # Left
                    (self.rect.centerx + 20, self.rect.top, -1, 15)   # Right
                ]
                # Multiply pattern based on double shot count
                for _ in range(shot_multiplier):
                    offset = _ * 10  # Slight offset for each multiplication
                    for x, y, dir, angle in base_pattern:
                        bullets.append(Bullet(x + offset, y, dir, angle=angle))
                        bullets.append(Bullet(x - offset, y, dir, angle=angle))
            else:
                # Regular shot with multiplier
                base_x = self.rect.centerx
                spacing = 15  # Space between bullet pairs
                for i in range(shot_multiplier):
                    offset = (i - (shot_multiplier - 1) / 2) * spacing
                    bullets.append(Bullet(base_x + offset, self.rect.top, -1))
            
            return bullets
        return []

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
    def __init__(self, x, y, direction, color=GREEN, angle=0):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 10
        self.direction = direction  # 1 for down (enemy), -1 for up (player)
        
        # Add angle for spread shots
        self.angle = math.radians(angle)  # Convert to radians
        self.speedx = math.sin(self.angle) * self.speed
        self.speedy = math.cos(self.angle) * self.speed * direction
        self.x = float(x)  # Store exact position
        self.y = float(y)

    def update(self):
        # Update position using floating point coordinates
        self.x += self.speedx
        self.y += self.speedy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        # Kill if it moves off the screen
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

# Boss class
class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.boss_level = level // 5  # Regular boss level calculation
        
        # Check if this is a mega-boss (every 50 levels)
        self.is_mega_boss = level % 50 == 0
        self.mega_boss_tier = level // 50  # 1 for level 50, 2 for level 100, etc.
        
        # Size scales with level, mega-bosses are even larger
        if self.is_mega_boss:
            self.size = 400 + (self.mega_boss_tier * 50)  # Bigger for each tier
        else:
            self.size = 180 + (self.boss_level * 20)
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Set health based on boss type
        if self.is_mega_boss:
            if level == 50:  # Omega Boss has exactly 5000 health
                self.max_health = 5000
            else:
                # Scale mega-boss health exponentially for higher levels
                base_health = 5000
                level_multiplier = (self.mega_boss_tier - 1) * 2  # Double health every 50 levels
                self.max_health = base_health * (2 ** level_multiplier)
        else:
            # Regular boss health scales linearly
            self.max_health = 800 * self.boss_level
        
        self.health = self.max_health
        
        # Initialize movement pattern variables
        self.movement_pattern = 0
        self.movement_timer = pygame.time.get_ticks()
        self.movement_duration = 3000  # Switch movement every 3 seconds
        self.original_x = WIDTH // 2
        self.original_y = HEIGHT // 4
        self.target_x = self.original_x
        self.target_y = self.original_y
        self.move_speed = 2
        
        # Initialize boss position at the top of the screen
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.top = -self.size  # Start above the screen
        
        # Initialize shooting variables
        self.shoot_delay = 300 if self.is_mega_boss else max(300, 1500 - (self.boss_level * 100))
        self.last_shot = pygame.time.get_ticks()
        self.pattern_time = pygame.time.get_ticks()
        self.pattern_duration = 2000 if self.is_mega_boss else 3000
        self.current_pattern = 0
        self.movement_offset = 0
        
        # Draw boss appearance based on type
        if self.is_mega_boss:  # Mega-boss design
            # Core color gets more intense with level
            core_hue = (self.mega_boss_tier * 30) % 360
            core_color = pygame.Color(0)
            core_color.hsva = (core_hue, 100, 100, 100)
            
            # Draw core
            pygame.draw.circle(self.image, core_color, (self.size//2, self.size//2), self.size//3)
            
            # Draw rotating rings with color based on level
            ring_count = min(3 + self.mega_boss_tier, 8)  # More rings at higher levels
            for i in range(ring_count):
                radius = self.size//3 + i * (self.size//8)
                ring_hue = (core_hue + i * 30) % 360
                ring_color = pygame.Color(0)
                ring_color.hsva = (ring_hue, 100, 100, 100)
                pygame.draw.circle(self.image, ring_color, (self.size//2, self.size//2), radius, 4)
            
            # Add energy crystals that increase with level
            crystal_count = min(4 + self.mega_boss_tier, 8)
            for i in range(crystal_count):
                angle = 2 * math.pi * i / crystal_count
                x = self.size//2 + math.cos(angle) * (self.size//2 - 40)
                y = self.size//2 + math.sin(angle) * (self.size//2 - 40)
                crystal_color = pygame.Color(0)
                crystal_color.hsva = ((core_hue + 180) % 360, 100, 100, 100)
                
                # Draw crystal
                points = []
                for j in range(3):
                    crystal_angle = angle + 2 * math.pi * j / 3
                    points.append((
                        x + math.cos(crystal_angle) * 40,
                        y + math.sin(crystal_angle) * 40
                    ))
                pygame.draw.polygon(self.image, crystal_color, points)
            
            # Add glowing eyes that get more intense with level
            eye_size = 30 + self.mega_boss_tier * 5
            eye_color = pygame.Color(0)
            eye_color.hsva = ((core_hue + 120) % 360, 100, 100, 100)
            pygame.draw.circle(self.image, eye_color, (self.size//3, self.size//3), eye_size)
            pygame.draw.circle(self.image, eye_color, (2*self.size//3, self.size//3), eye_size)
            
            # Add energy beams that increase with level
            beam_count = min(8 + self.mega_boss_tier * 2, 16)
            beam_color = pygame.Color(0)
            beam_color.hsva = ((core_hue + 60) % 360, 100, 100, 100)
            for i in range(beam_count):
                angle = 2 * math.pi * i / beam_count
                start = (self.size//2, self.size//2)
                end = (
                    self.size//2 + math.cos(angle) * self.size//2,
                    self.size//2 + math.sin(angle) * self.size//2
                )
                pygame.draw.line(self.image, beam_color, start, end, 6)
        
        else:  # Regular boss designs
            if self.boss_level == 1:  # Level 5 boss
                # Draw large red pentagon with glowing core
                points = []
                for i in range(5):
                    angle = 2 * math.pi * i / 5 - math.pi / 2
                    points.append((
                        self.size/2 + math.cos(angle) * self.size/2,
                        self.size/2 + math.sin(angle) * self.size/2
                    ))
                pygame.draw.polygon(self.image, RED, points)
                pygame.draw.circle(self.image, ORANGE, (self.size//2, self.size//2), self.size//4)
            
            elif self.boss_level == 2:  # Level 10 boss
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
                pygame.draw.circle(self.image, (255, 0, 255), (self.size//3, self.size//3), 15)
                pygame.draw.circle(self.image, (255, 0, 255), (2*self.size//3, self.size//3), 15)
            
            else:  # Higher level regular bosses
                # Draw a more intimidating boss with level-based colors
                hue = (self.boss_level * 30) % 360
                main_color = pygame.Color(0)
                main_color.hsva = (hue, 100, 100, 100)
                
                # Main core
                pygame.draw.circle(self.image, main_color, (self.size//2, self.size//2), self.size//2)
                
                # Pulsing rings with complementary colors
                for i in range(4):
                    radius = self.size//2 - (i * 15)
                    ring_color = pygame.Color(0)
                    ring_color.hsva = ((hue + i * 30) % 360, 100, 100, 100)
                    pygame.draw.circle(self.image, ring_color, (self.size//2, self.size//2), radius, 5)

    def update(self):
        # Boss entrance movement
        if self.rect.top < 50:  # Initial descent
            self.rect.y += 2
            return
        
        now = pygame.time.get_ticks()
        
        # Switch movement patterns periodically
        if now - self.movement_timer > self.movement_duration:
            self.movement_pattern = (self.movement_pattern + 1) % 4
            self.movement_timer = now
            self.movement_offset = 0
        
        # Different movement patterns
        if self.is_mega_boss:
            if self.mega_boss_tier == 1:  # Omega Boss
                if self.movement_pattern == 0:  # Figure-8 pattern
                    self.movement_offset += 0.02
                    self.rect.centerx = self.original_x + math.sin(self.movement_offset * 2) * 200
                    self.rect.centery = self.original_y + math.sin(self.movement_offset) * 100
                
                elif self.movement_pattern == 1:  # Circle pattern
                    self.movement_offset += 0.03
                    radius = 150
                    self.rect.centerx = self.original_x + math.cos(self.movement_offset) * radius
                    self.rect.centery = self.original_y + math.sin(self.movement_offset) * radius
                
                elif self.movement_pattern == 2:  # Dash pattern
                    if self.movement_offset == 0:
                        self.target_x = random.randint(100, WIDTH - 100)
                        self.target_y = random.randint(100, HEIGHT//2)
                    
                    dx = self.target_x - self.rect.centerx
                    dy = self.target_y - self.rect.centery
                    dist = math.sqrt(dx * dx + dy * dy)
                    
                    if dist > 5:
                        self.rect.centerx += dx / dist * 5
                        self.rect.centery += dy / dist * 5
                    self.movement_offset += 0.1
                
                else:  # Zigzag pattern
                    self.movement_offset += 0.05
                    self.rect.centerx = self.original_x + math.sin(self.movement_offset * 4) * 200
                    self.rect.centery = self.original_y + math.sin(self.movement_offset * 2) * 50
        
        else:  # Regular boss movements
            if self.movement_pattern == 0:  # Side to side
                self.rect.centerx = self.original_x + math.sin(self.movement_offset) * 150
                self.movement_offset += 0.03
            
            elif self.movement_pattern == 1:  # Small circles
                radius = 75
                self.rect.centerx = self.original_x + math.cos(self.movement_offset) * radius
                self.rect.centery = self.original_y + math.sin(self.movement_offset) * radius
                self.movement_offset += 0.04
            
            elif self.movement_pattern == 2:  # Random position
                if self.movement_offset == 0:
                    self.target_x = random.randint(100, WIDTH - 100)
                    self.target_y = random.randint(100, HEIGHT//3)
                
                dx = self.target_x - self.rect.centerx
                dy = self.target_y - self.rect.centery
                dist = math.sqrt(dx * dx + dy * dy)
                
                if dist > 5:
                    self.rect.centerx += dx / dist * 3
                    self.rect.centery += dy / dist * 3
                self.movement_offset += 0.1
            
            else:  # Up and down
                self.rect.centery = self.original_y + math.sin(self.movement_offset) * 50
                self.movement_offset += 0.02
        
        # Keep boss within screen bounds
        self.rect.clamp_ip(pygame.Rect(0, 50, WIDTH, HEIGHT//2))

    def shoot(self, player=None):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullets = []
            
            if self.is_mega_boss:
                # Check if enough time has passed to switch patterns
                if now - self.pattern_time > self.pattern_duration:
                    self.current_pattern = (self.current_pattern + 1) % 4
                    self.pattern_time = now
                
                if self.mega_boss_tier == 1:  # Level 50 - Omega Boss
                    if self.current_pattern == 0:  # Spiral pattern
                        for i in range(8):
                            angle = 2 * math.pi * i / 8 + self.movement_offset
                            speed = 8
                            speed_x = math.cos(angle) * speed
                            speed_y = math.sin(angle) * speed
                            bullet = BossBullet(self.rect.centerx, self.rect.centery, 
                                              speed_x, speed_y, (255, 0, 0))  # Red bullets
                            bullets.append(bullet)
                        self.movement_offset += 0.2  # Rotate the pattern
                    
                    elif self.current_pattern == 1:  # Cross beam pattern
                        angles = [0, math.pi/2, math.pi, 3*math.pi/2]
                        for angle in angles:
                            for speed in range(4, 12, 2):  # Multiple bullets along each beam
                                speed_x = math.cos(angle) * speed
                                speed_y = math.sin(angle) * speed
                                bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                                  speed_x, speed_y, (255, 0, 255))  # Purple bullets
                                bullets.append(bullet)
                    
                    elif self.current_pattern == 2:  # Homing missiles
                        if player:
                            for i in range(3):  # Launch 3 homing missiles
                                dx = player.rect.centerx - self.rect.centerx
                                dy = player.rect.centery - self.rect.centery
                                dist = math.sqrt(dx * dx + dy * dy)
                                if dist > 0:
                                    speed = 6
                                    speed_x = dx / dist * speed
                                    speed_y = dy / dist * speed
                                    # Add slight spread to the missiles
                                    spread = (i - 1) * math.pi / 6
                                    new_speed_x = speed_x * math.cos(spread) - speed_y * math.sin(spread)
                                    new_speed_y = speed_x * math.sin(spread) + speed_y * math.cos(spread)
                                    bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                                      new_speed_x, new_speed_y, (0, 255, 255))  # Cyan bullets
                                    bullets.append(bullet)
                    
                    else:  # Scatter shot
                        for _ in range(12):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(3, 8)
                            speed_x = math.cos(angle) * speed
                            speed_y = math.sin(angle) * speed
                            bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                              speed_x, speed_y, (255, 255, 0))  # Yellow bullets
                            bullets.append(bullet)
                
                # ... rest of mega-boss patterns ...
            
            else:  # Regular boss patterns
                if self.current_pattern == 0:  # Basic spread shot
                    for i in range(-2, 3):
                        angle = math.pi/6 * i
                        speed = 6
                        speed_x = math.sin(angle) * speed
                        speed_y = math.cos(angle) * speed
                        bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                          speed_x, speed_y, RED)
                        bullets.append(bullet)
                
                elif self.current_pattern == 1:  # Circle shot
                    for i in range(8):
                        angle = 2 * math.pi * i / 8
                        speed = 5
                        speed_x = math.cos(angle) * speed
                        speed_y = math.sin(angle) * speed
                        bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                          speed_x, speed_y, PURPLE)
                        bullets.append(bullet)
                
                elif self.current_pattern == 2:  # Aimed shot
                    if player:
                        dx = player.rect.centerx - self.rect.centerx
                        dy = player.rect.centery - self.rect.centery
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist > 0:
                            speed = 7
                            speed_x = dx / dist * speed
                            speed_y = dy / dist * speed
                            bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                              speed_x, speed_y, ORANGE)
                            bullets.append(bullet)
                
                else:  # Random spray
                    for _ in range(5):
                        angle = random.uniform(math.pi/4, 3*math.pi/4)
                        speed = random.uniform(4, 7)
                        speed_x = math.cos(angle) * speed
                        speed_y = math.sin(angle) * speed
                        bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                          speed_x, speed_y, RED)
                        bullets.append(bullet)
                
                # Switch patterns periodically
                if now - self.pattern_time > self.pattern_duration:
                    self.current_pattern = (self.current_pattern + 1) % 4
                    self.pattern_time = now
            
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
PLAYER_NAME = None  # Global variable to store player name

def get_player_name():
    global PLAYER_NAME
    if PLAYER_NAME:  # If we already have a name, return it
        return PLAYER_NAME
        
    font = pygame.font.Font(None, 36)
    input_box = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 32)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False
    
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
                    if event.key == pygame.K_RETURN and text.strip():
                        PLAYER_NAME = text  # Store the name globally
                        return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode
        
        screen.fill(BLACK)
        txt_surface = font.render("Enter your name:", True, WHITE)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        screen.blit(txt_surface, (WIDTH//2 - txt_surface.get_width()//2, HEIGHT//2 - 50))
        txt_surface = font.render(text, True, color)
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(screen, color, input_box, 2)
        pygame.display.flip()

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
    # Create detailed ship designs
    def create_fighter_ship():
        ship = pygame.Surface((60, 60), pygame.SRCALPHA)
        # Main body
        pygame.draw.polygon(ship, (100, 100, 255), [
            (30, 0),   # Nose
            (40, 20),  # Right hull
            (45, 40),  # Right wing
            (35, 45),  # Right engine
            (25, 45),  # Left engine
            (15, 40),  # Left wing
            (20, 20)   # Left hull
        ])
        # Cockpit
        pygame.draw.polygon(ship, (200, 200, 255), [
            (30, 10),  # Top
            (35, 25),  # Right
            (25, 25)   # Left
        ])
        # Engine glow
        pygame.draw.circle(ship, (255, 165, 0), (30, 45), 5)
        pygame.draw.circle(ship, (255, 69, 0), (30, 45), 3)
        return ship, 5  # Balanced speed

    def create_interceptor_ship():
        ship = pygame.Surface((60, 60), pygame.SRCALPHA)
        # Main body
        pygame.draw.polygon(ship, (100, 255, 100), [
            (30, 0),   # Nose
            (45, 30),  # Right hull
            (40, 45),  # Right engine
            (20, 45),  # Left engine
            (15, 30)   # Left hull
        ])
        # Wings
        pygame.draw.polygon(ship, (50, 200, 50), [
            (45, 30),  # Right top
            (55, 40),  # Right tip
            (40, 45)   # Right bottom
        ])
        pygame.draw.polygon(ship, (50, 200, 50), [
            (15, 30),  # Left top
            (5, 40),   # Left tip
            (20, 45)   # Left bottom
        ])
        # Cockpit
        pygame.draw.ellipse(ship, (200, 255, 200), (25, 15, 10, 15))
        # Engine glow
        pygame.draw.circle(ship, (255, 165, 0), (30, 45), 6)
        pygame.draw.circle(ship, (255, 69, 0), (30, 45), 4)
        return ship, 7  # Fast speed

    def create_assault_ship():
        ship = pygame.Surface((60, 60), pygame.SRCALPHA)
        # Main body
        pygame.draw.polygon(ship, (255, 100, 100), [
            (30, 0),   # Nose
            (50, 25),  # Right hull
            (45, 45),  # Right engine
            (15, 45),  # Left engine
            (10, 25)   # Left hull
        ])
        # Heavy armor plates
        pygame.draw.polygon(ship, (200, 50, 50), [
            (40, 15),  # Right top
            (50, 25),  # Right middle
            (45, 35)   # Right bottom
        ])
        pygame.draw.polygon(ship, (200, 50, 50), [
            (20, 15),  # Left top
            (10, 25),  # Left middle
            (15, 35)   # Left bottom
        ])
        # Cockpit
        pygame.draw.polygon(ship, (255, 200, 200), [
            (30, 10),  # Top
            (35, 20),  # Right
            (25, 20)   # Left
        ])
        # Triple engine glow
        pygame.draw.circle(ship, (255, 165, 0), (22, 45), 4)
        pygame.draw.circle(ship, (255, 165, 0), (30, 45), 4)
        pygame.draw.circle(ship, (255, 165, 0), (38, 45), 4)
        pygame.draw.circle(ship, (255, 69, 0), (22, 45), 2)
        pygame.draw.circle(ship, (255, 69, 0), (30, 45), 2)
        pygame.draw.circle(ship, (255, 69, 0), (38, 45), 2)
        return ship, 3  # Heavy but slow

    ships = [
        (create_fighter_ship(), "Fighter", "Balanced speed and maneuverability"),
        (create_interceptor_ship(), "Interceptor", "Fast but fragile"),
        (create_assault_ship(), "Assault", "Heavy armor, powerful weapons")
    ]
    
    font = pygame.font.Font(None, 36)
    title = font.render("Select Your Ship", True, WHITE)
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        screen.fill(BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        # Handle events first
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    index = event.key - pygame.K_1
                    if 0 <= index < len(ships):
                        return ships[index][0]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    # Check each ship's click area
                    for i, ((ship_img, speed), name, desc) in enumerate(ships):
                        x = WIDTH // 4 * (i + 1)
                        y = HEIGHT // 2
                        # Create a larger click area
                        click_rect = pygame.Rect(x - 70, y - 70, 140, 140)
                        if click_rect.collidepoint(mouse_pos):
                            return (ship_img, speed)
        
        # Display ship options
        for i, ((ship_img, speed), name, desc) in enumerate(ships):
            x = WIDTH // 4 * (i + 1)
            y = HEIGHT // 2
            
            # Draw ship
            ship_rect = ship_img.get_rect(center=(x, y))
            screen.blit(ship_img, ship_rect)
            
            # Draw ship info
            name_text = font.render(name, True, WHITE)
            speed_text = font.render(f"Speed: {speed}", True, WHITE)
            desc_text = font.render(desc, True, WHITE)
            
            screen.blit(name_text, (x - name_text.get_width()//2, y + 40))
            screen.blit(speed_text, (x - speed_text.get_width()//2, y + 70))
            screen.blit(desc_text, (x - desc_text.get_width()//2, y + 100))
            
            # Draw selection box with engine glow effect
            box_color = (100 + int(abs(math.sin(pygame.time.get_ticks() * 0.003)) * 155),
                        100 + int(abs(math.sin(pygame.time.get_ticks() * 0.003)) * 155),
                        255)
            pygame.draw.rect(screen, box_color, (x - 70, y - 70, 140, 140), 2)
        
        pygame.display.flip()
        clock.tick(60)
    
    return None

# Welcome screen function
def welcome_screen():
    global ESC_QUIT_GAME
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        screen.fill(BLACK)
        
        # Draw title with glow effect
        title_font = pygame.font.Font(None, 74)
        title = title_font.render("SPACE SHOOTER", True, WHITE)
        # Create glow effect
        glow_color = (100 + int(abs(math.sin(pygame.time.get_ticks() * 0.003)) * 155),
                     100 + int(abs(math.sin(pygame.time.get_ticks() * 0.003)) * 155),
                     255)
        glow_title = title_font.render("SPACE SHOOTER", True, glow_color)
        
        # Draw glow and main title
        screen.blit(glow_title, (WIDTH//2 - title.get_width()//2 + 2, HEIGHT//4 + 2))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        
        # Draw player name
        name_font = pygame.font.Font(None, 36)
        name_text = name_font.render(f"Player: {PLAYER_NAME}", True, WHITE)
        screen.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT//2))
        
        # Draw menu options with glow effect
        menu_font = pygame.font.Font(None, 48)
        options = [
            ("Press SPACE to Play", pygame.K_SPACE),
            ("Press S for Shop", pygame.K_s),
            ("Press H for High Scores", pygame.K_h),
            ("Press ESC to Quit", pygame.K_ESCAPE)
        ]
        
        for i, (text, key) in enumerate(options):
            text_surface = menu_font.render(text, True, WHITE)
            y_pos = HEIGHT * 2//3 + i * 50
            screen.blit(text_surface, (WIDTH//2 - text_surface.get_width()//2, y_pos))
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ESC_QUIT_GAME = True
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    ESC_QUIT_GAME = True
                    return
                elif event.key == pygame.K_SPACE:
                    # Start game flow
                    ship_info = select_ship()
                    if ship_info:
                        game()
                        # Don't return here, let the welcome screen continue
                elif event.key == pygame.K_s:
                    shop_screen()
                elif event.key == pygame.K_h:
                    high_scores = load_high_scores()
                    display_high_scores(high_scores)

def display_rating_screen():
    font_title = pygame.font.Font(None, 72)
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    title = font_title.render("Rate The Game", True, YELLOW)
    stars = 0  # Current rating
    max_stars = 5
    submitted = False
    skip_levels = 0  # Number of levels to skip
    choosing_levels = False  # Whether we're in level selection mode
    
    # Create star surfaces
    empty_star = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(empty_star, WHITE, [(20, 0), (25, 15), (40, 15), (28, 25),
                                          (33, 40), (20, 30), (7, 40), (12, 25),
                                          (0, 15), (15, 15)], 2)
    
    filled_star = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(filled_star, YELLOW, [(20, 0), (25, 15), (40, 15), (28, 25),
                                            (33, 40), (20, 30), (7, 40), (12, 25),
                                            (0, 15), (15, 15)])
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        clock.tick(60)
        screen.fill(BLACK)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not submitted and not choosing_levels:
                    # Star rating area
                    star_x = WIDTH//2 - (max_stars * 50)//2
                    star_y = HEIGHT//2 - 50
                    for i in range(max_stars):
                        star_rect = pygame.Rect(star_x + i * 50, star_y, 40, 40)
                        if star_rect.collidepoint(mouse_x, mouse_y):
                            stars = i + 1
                            sound_manager.play_powerup()  # Play sound when selecting stars
                
                # Submit button
                submit_text = font.render("Submit", True, GREEN)
                submit_rect = submit_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
                if submit_rect.collidepoint(mouse_x, mouse_y) and not submitted and not choosing_levels:
                    submitted = True
                    sound_manager.play_powerup()
                    if stars == 5:
                        choosing_levels = True
                
                # Level skip buttons when choosing levels
                if choosing_levels:
                    # Increase/decrease level skip buttons
                    if HEIGHT//2 - 50 <= mouse_y <= HEIGHT//2 + 50:
                        if WIDTH//2 - 100 <= mouse_x <= WIDTH//2 - 20:  # Left button
                            skip_levels = max(0, skip_levels - 1)
                            sound_manager.play_powerup()
                        elif WIDTH//2 + 20 <= mouse_x <= WIDTH//2 + 100:  # Right button
                            skip_levels += 1
                            sound_manager.play_powerup()
                    
                    # Confirm button
                    confirm_text = font.render("Confirm", True, GREEN)
                    confirm_rect = confirm_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
                    if confirm_rect.collidepoint(mouse_x, mouse_y):
                        # Save the level skip value to a file
                        try:
                            with open('level_skip.json', 'w') as f:
                                json.dump({'skip_levels': skip_levels}, f)
                            game()  # Start the game immediately
                            return  # Exit the rating screen
                        except Exception as e:
                            print(f"Error saving level skip: {e}")
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if choosing_levels:
                        choosing_levels = False
                        submitted = False
                    else:
                        running = False
                elif event.key == pygame.K_RETURN and choosing_levels:
                    # Save the level skip value to a file
                    try:
                        with open('level_skip.json', 'w') as f:
                            json.dump({'skip_levels': skip_levels}, f)
                        game()  # Start the game immediately
                        return  # Exit the rating screen
                    except Exception as e:
                        print(f"Error saving level skip: {e}")
        
        # Draw title
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        
        if not choosing_levels:
            # Draw stars
            star_x = WIDTH//2 - (max_stars * 50)//2
            star_y = HEIGHT//2 - 50
            for i in range(max_stars):
                if i < stars:
                    screen.blit(filled_star, (star_x + i * 50, star_y))
                else:
                    screen.blit(empty_star, (star_x + i * 50, star_y))
            
            if not submitted:
                # Draw submit button
                submit_text = font.render("Submit", True, GREEN)
                screen.blit(submit_text, submit_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))
            else:
                # Draw thank you message
                thank_you = font.render("Thank you for rating!", True, WHITE)
                screen.blit(thank_you, thank_you.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))
        else:
            # Draw level skip selection
            skip_title = font.render("Choose Levels to Skip", True, YELLOW)
            screen.blit(skip_title, skip_title.get_rect(center=(WIDTH//2, HEIGHT//2 - 100)))
            
            # Draw decrease/increase buttons and level count
            pygame.draw.polygon(screen, WHITE, [(WIDTH//2 - 100, HEIGHT//2), 
                                             (WIDTH//2 - 20, HEIGHT//2 - 50),
                                             (WIDTH//2 - 20, HEIGHT//2 + 50)], 2)  # Left arrow
            pygame.draw.polygon(screen, WHITE, [(WIDTH//2 + 100, HEIGHT//2),
                                             (WIDTH//2 + 20, HEIGHT//2 - 50),
                                             (WIDTH//2 + 20, HEIGHT//2 + 50)], 2)  # Right arrow
            
            level_text = font.render(str(skip_levels), True, WHITE)
            screen.blit(level_text, level_text.get_rect(center=(WIDTH//2, HEIGHT//2)))
            
            # Draw confirm button
            confirm_text = font.render("Confirm", True, GREEN)
            screen.blit(confirm_text, confirm_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100)))
            
            # Draw instruction
            instruction = small_font.render("Press ESC to go back or ENTER to confirm", True, WHITE)
            screen.blit(instruction, instruction.get_rect(center=(WIDTH//2, HEIGHT - 50)))
        
        pygame.display.flip()

def load_level_skip():
    """Load the number of levels to skip"""
    try:
        if os.path.exists('level_skip.json'):
            with open('level_skip.json', 'r') as f:
                data = json.load(f)
                return data.get('skip_levels', 0)
    except Exception as e:
        print(f"Error loading level skip: {e}")
    return 0

# Update game function to handle level skipping
def game():
    # Import math here for asteroid polygon generation
    import math
    import random
    
    # Load level skip value at game start
    skip_levels = load_level_skip()
    
    # Initialize game objects and variables
    star_field = StarField()
    particle_system = ParticleSystem()
    all_sprites = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    boss_group = pygame.sprite.Group()
    boss_bullets = pygame.sprite.Group()
    
    # Get player name and select ship
    player_name = get_player_name()
    ship_img, ship_speed = select_ship()
    
    # Create player
    player = Ship(ship_img, ship_speed, player_name)
    all_sprites.add(player)
    
    # Initialize game state
    score = 0
    level = 1 + skip_levels  # Start at skipped level
    game_over = False
    game_paused = False
    level_transition = True  # Start with transition to show skipped level
    transition_start_time = pygame.time.get_ticks()
    transition_duration = 1000  # 1 second
    just_defeated_boss = False
    
    # Level settings
    level_score_threshold = 1000 * level  # Scale threshold with skipped levels
    asteroid_count = 6 + level  # Scale with level
    enemy_count = 2 + level // 2  # Add enemy every 2 levels
    
    # Clear the level skip after using it
    try:
        with open('level_skip.json', 'w') as f:
            json.dump({'skip_levels': 0}, f)
    except Exception as e:
        print(f"Error clearing level skip: {e}")
    
    # Create off-screen buffer for better performance
    buffer_surface = pygame.Surface((WIDTH, HEIGHT))
    
    # Set up double buffering
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
    
    # Initialize clock
    clock = pygame.time.Clock()
    
    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Kill player when ESC is pressed
                    running = False
                    # Create explosion effect
                    explosion = Explosion(player.rect.centerx, player.rect.centery)
                    explosion.radius = 400
                    explosion.growth_rate = 40
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    sound_manager.play_explosion()
                    # Wait for explosion animation
                    pygame.time.wait(500)
                elif event.key == pygame.K_SPACE and not game_paused and not level_transition:
                    # Player shooting
                    new_bullets = player.shoot()
                    for bullet in new_bullets:
                        all_sprites.add(bullet)
                        bullets.add(bullet)
                elif event.key == pygame.K_F11:
                    toggle_fullscreen()
        
        if game_paused:
            # Draw pause menu
            pause_font = pygame.font.Font(None, 74)
            pause_text = pause_font.render("PAUSED", True, WHITE)
            screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2))
            pygame.display.flip()
            continue
        
        # Handle level transition
        if level_transition:
            current_time = pygame.time.get_ticks()
            if current_time - transition_start_time > transition_duration:
                level_transition = False
                
                # Spawn boss if it's a boss level
                if level % 5 == 0 and not boss_group and not just_defeated_boss:
                    # Clear all enemies and asteroids
                    for sprite in [asteroids, enemies, power_ups, bombs]:
                        for obj in sprite:
                            obj.kill()
                    
                    # Create boss
                    boss = Boss(level)
                    all_sprites.add(boss)
                    boss_group.add(boss)
                    
                    # Special effects for boss entrance
                    if level == 50:  # Omega Boss entrance
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
                        sound_manager.play_explosion()
                else:
                    # Spawn regular enemies and asteroids
                    for i in range(asteroid_count):
                        asteroid = Asteroid(level)
                        all_sprites.add(asteroid)
                        asteroids.add(asteroid)
                    
                    for i in range(enemy_count):
                        enemy = EnemyShip(level)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
        
        # Update game state
        all_sprites.update()
        
        # Enemy shooting
        for enemy in enemies:
            bullet = enemy.shoot()
            if bullet:
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
        
        # Boss shooting and updates
        if boss_group:
            # Boss shooting
            for boss in boss_group:
                new_bullets = boss.shoot(player)
                for bullet in new_bullets:
                    all_sprites.add(bullet)
                    boss_bullets.add(bullet)
            
            # Check for player bullet hits on boss
            hits = pygame.sprite.groupcollide(boss_group, bullets, False, True)
            for boss, bullets_hit in hits.items():
                boss.health -= 10 * len(bullets_hit)
                sound_manager.play_collision()
                
                # Create explosion effect for each hit
                for bullet in bullets_hit:
                    explosion = Explosion(bullet.rect.centerx, bullet.rect.centery)
                    explosion.radius = 30
                    explosion.growth_rate = 5
                    explosion.max_frames = 5
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                
                # Check if boss is defeated
                if boss.health <= 0:
                    boss.kill()
                    # Create massive explosion
                    explosion = Explosion(boss.rect.centerx, boss.rect.centery)
                    explosion.radius = 400
                    explosion.growth_rate = 40
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    sound_manager.play_explosion()
                    
                    # Check if this was the Omega Boss (Level 50)
                    if level == 50 and player_name != "0987654321hq":
                        # Create multiple explosions for epic effect
                        for _ in range(10):
                            x = random.randint(0, WIDTH)
                            y = random.randint(0, HEIGHT)
                            explosion = Explosion(x, y)
                            explosion.radius = 300
                            explosion.growth_rate = 35
                            all_sprites.add(explosion)
                            explosions.add(explosion)
                            sound_manager.play_explosion()
                            pygame.time.wait(100)
                        
                        # Show congratulations message
                        font_big = pygame.font.Font(None, 74)
                        font = pygame.font.Font(None, 36)
                        congrats_text = font_big.render("CONGRATULATIONS!", True, YELLOW)
                        omega_text = font.render("You have defeated the Omega Boss!", True, WHITE)
                        reset_text = font.render("The universe will now reset...", True, RED)
                        
                        screen.blit(congrats_text, (WIDTH//2 - congrats_text.get_width()//2, HEIGHT//2 - 100))
                        screen.blit(omega_text, (WIDTH//2 - omega_text.get_width()//2, HEIGHT//2))
                        screen.blit(reset_text, (WIDTH//2 - reset_text.get_width()//2, HEIGHT//2 + 100))
                        pygame.display.flip()
                        pygame.time.wait(5000)  # Wait 5 seconds
                        
                        # Reset everything
                        try:
                            # Reset total score
                            with open('total_score.json', 'w') as f:
                                json.dump({'total_score': 0}, f)
                            
                            # Reset shop state
                            for item in SHOP_ITEMS:
                                item.purchased = False
                            
                            # Reset level skip
                            with open('level_skip.json', 'w') as f:
                                json.dump({'skip_levels': 0}, f)
                            
                            # Reset high scores
                            with open('high_scores.json', 'w') as f:
                                json.dump([], f)
                            
                            # Return to main menu
                            running = False
                            return score
                            
                        except Exception as e:
                            print(f"Error resetting game state: {e}")
                    
                    # Regular boss defeat rewards
                    boss_bonus = 5000 * (level // 5)
                    score += boss_bonus
                    
                    # Special message for secret name player passing level 50
                    if level >= 50 and player_name == "0987654321hq":
                        font = pygame.font.Font(None, 48)
                        secret_text = font.render("Secret Mode: Beyond Level 50!", True, PURPLE)
                        screen.blit(secret_text, (WIDTH//2 - secret_text.get_width()//2, HEIGHT//2))
                        pygame.display.flip()
                        pygame.time.wait(2000)
                    
                    # Spawn power-ups
                    for _ in range(3):
                        x = boss.rect.centerx + random.randint(-100, 100)
                        y = boss.rect.centery + random.randint(-100, 100)
                        power_up = PowerUp(x, y)
                        all_sprites.add(power_up)
                        power_ups.add(power_up)
                    
                    # Set next level threshold and flag
                    level_score_threshold = score + 1000
                    just_defeated_boss = True
                    
                    # Move to next level
                    level += 1
                    level_transition = True
                    transition_start_time = pygame.time.get_ticks()
        
        # Check for collisions in regular levels
        if not boss_group:
            # Player bullet hits asteroid
            hits = pygame.sprite.groupcollide(asteroids, bullets, True, True)
            for hit in hits:
                score += 50
                # Create new asteroid
                asteroid = Asteroid(level)
                all_sprites.add(asteroid)
                asteroids.add(asteroid)
                
                # Small chance to spawn power-up from asteroid
                if random.random() < 0.1:  # 10% chance
                    power_up = PowerUp(hit.rect.centerx, hit.rect.centery)
                    all_sprites.add(power_up)
                    power_ups.add(power_up)
            
            # Player bullet hits enemy
            hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
            for hit in hits:
                score += 100
                # Create new enemy
                enemy = EnemyShip(level)
                all_sprites.add(enemy)
                enemies.add(enemy)
                
                # Higher chance to spawn power-up from enemy
                if random.random() < 0.3:  # 30% chance
                    power_up = PowerUp(hit.rect.centerx, hit.rect.centery)
                    all_sprites.add(power_up)
                    power_ups.add(power_up)
        
        # Check if player collects power-up
        power_up_hits = pygame.sprite.spritecollide(player, power_ups, True)
        for power_up in power_up_hits:
            player.add_power_up(power_up.type)
            score += 25  # Bonus points for collecting power-up
        
        # Check if player is hit
        if not player.is_invincible:
            # Check collisions with all hazards
            for hazard_group in [asteroids, enemies, enemy_bullets, boss_bullets]:
                if pygame.sprite.spritecollide(player, hazard_group, True):
                    running = False
        
        # Check for level advancement in regular levels
        if not boss_group and score >= level_score_threshold and not level_transition:
            level += 1
            level_transition = True
            transition_start_time = pygame.time.get_ticks()
            
            # Update level settings
            level_score_threshold = score + 1000
            asteroid_count = 6 + level
            enemy_count = 2 + level // 2
            
            # Clear existing enemies and asteroids
            for sprite in asteroids:
                sprite.kill()
            for sprite in enemies:
                sprite.kill()
        
        # Clear screen and draw
        screen.fill(BLACK)
        
        # Draw starfield first (background)
        star_field.update(player.velocity_x, player.velocity_y)
        star_field.draw(screen)
        
        # Draw particles
        particle_system.update()
        particle_system.draw(screen)
        
        # Draw all sprites
        all_sprites.draw(screen)
        
        # Draw UI
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, WHITE)
        level_text = font.render(f"Level: {level}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 50))
        
        # Draw active power-up icons
        icon_size = 30
        icon_spacing = 40
        icon_y = 90
        for i, power_up_type in enumerate(player.power_ups):
            icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
            
            if power_up_type == PowerUp.RAPID_FIRE:
                color = YELLOW
                # Draw lightning bolt
                points = [(icon_size//2, 0), (icon_size, icon_size//2), 
                         (icon_size*2//3, icon_size*3//5), (icon_size, icon_size), 
                         (0, icon_size*3//5), (icon_size//3, icon_size*2//5)]
                pygame.draw.polygon(icon, color, points)
            elif power_up_type == PowerUp.DOUBLE_SHOT:
                color = PURPLE
                # Draw double circle
                pygame.draw.circle(icon, color, (icon_size//4, icon_size//2), icon_size//4)
                pygame.draw.circle(icon, color, (icon_size*3//4, icon_size//2), icon_size//4)
            elif power_up_type == PowerUp.TRIPLE_SHOT:
                color = RED
                # Draw triple circle
                pygame.draw.circle(icon, color, (icon_size//5, icon_size//2), icon_size//5)
                pygame.draw.circle(icon, color, (icon_size//2, icon_size//4), icon_size//5)
                pygame.draw.circle(icon, color, (icon_size*4//5, icon_size//2), icon_size//5)
            elif power_up_type == PowerUp.SUPER_RAPID_FIRE:
                color = ORANGE
                # Draw double lightning bolt
                points1 = [(icon_size//4, 0), (icon_size//2, icon_size//2), 
                          (icon_size//3, icon_size*3//5), (icon_size//2, icon_size), 
                          (0, icon_size*3//5), (icon_size//6, icon_size//2)]
                points2 = [(icon_size*3//4, 0), (icon_size, icon_size//2), 
                          (icon_size*5//6, icon_size*3//5), (icon_size, icon_size), 
                          (icon_size//2, icon_size*3//5), (icon_size*2//3, icon_size//2)]
                pygame.draw.polygon(icon, color, points1)
                pygame.draw.polygon(icon, color, points2)
            elif power_up_type == PowerUp.RAPID_MOVEMENT:
                color = LIGHT_BLUE
                # Draw speed arrows
                pygame.draw.polygon(icon, color, [(0, icon_size//2), (icon_size//2, icon_size//4), 
                                                (icon_size//2, icon_size*3//4)])
                pygame.draw.polygon(icon, color, [(icon_size//2, icon_size//2), (icon_size, icon_size//4), 
                                                (icon_size, icon_size*3//4)])
            
            screen.blit(icon, (10 + i * icon_spacing, icon_y))
            
            # Draw remaining time bar
            time_remaining = (player.power_up_duration - (pygame.time.get_ticks() - player.power_up_start)) / player.power_up_duration
            if time_remaining > 0:
                bar_width = icon_size
                bar_height = 4
                pygame.draw.rect(screen, (64, 64, 64), (10 + i * icon_spacing, icon_y + icon_size + 2, bar_width, bar_height))
                pygame.draw.rect(screen, color, (10 + i * icon_spacing, icon_y + icon_size + 2, 
                                               int(bar_width * time_remaining), bar_height))
        
        # Draw boss health bar if boss exists
        for boss in boss_group:
            # Draw boss health bar
            health_width = 800
            health_height = 20
            health_x = WIDTH//2 - health_width//2
            health_y = 50
            
            # Draw background (empty health)
            pygame.draw.rect(screen, (64, 64, 64), 
                           (health_x, health_y, health_width, health_height))
            
            # Draw current health
            current_width = int((boss.health / boss.max_health) * health_width)
            if boss.is_mega_boss:
                # Special health bar for mega bosses
                health_colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0)]
                segment_width = current_width // len(health_colors)
                for i, color in enumerate(health_colors):
                    pygame.draw.rect(screen, color,
                                   (health_x + i * segment_width, health_y,
                                    segment_width, health_height))
            else:
                pygame.draw.rect(screen, RED,
                               (health_x, health_y, current_width, health_height))
        
        # Draw level transition
        if level_transition:
            alpha = min(255, int(255 * (pygame.time.get_ticks() - transition_start_time) / transition_duration))
            transition_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            transition_surface.fill((0, 0, 0, alpha))
            
            # Draw level text
            level_font = pygame.font.Font(None, 74)
            if level % 5 == 0:
                level_text = level_font.render(f"BOSS LEVEL {level}", True, RED)
            else:
                level_text = level_font.render(f"LEVEL {level}", True, WHITE)
            
            text_rect = level_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(transition_surface, (0, 0))
            screen.blit(level_text, text_rect)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Game over - Show rating screen
    display_rating_screen()
    return score

# After the high scores functions, add persistent score management
def load_total_score():
    """Load the total accumulated score from a file"""
    try:
        with open('total_score.json', 'r') as f:
            data = json.load(f)
            return data.get('total_score', 0)
    except:
        return 0

def save_total_score(score):
    """Save the total accumulated score to a file"""
    try:
        with open('total_score.json', 'w') as f:
            json.dump({'total_score': score}, f)
    except Exception as e:
        print(f"Error saving total score: {e}")

# Add shop items and shop function after the high scores functions
class ShopItem:
    def __init__(self, name, description, cost, effect_type, effect_value):
        self.name = name
        self.description = description
        self.cost = cost
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.purchased = False

# Define available shop items
SHOP_ITEMS = [
    ShopItem("Speed Boost", "Permanent +2 ship speed", 1000, "speed", 2),
    ShopItem("Double Points", "Score 2x points from kills", 2000, "score_multiplier", 2),
    ShopItem("Extra Health", "Take one extra hit before dying", 3000, "health", 1),
    ShopItem("Rapid Fire", "Shoot faster permanently", 2500, "fire_rate", 1.5),
    ShopItem("Triple Shot", "Start with triple shot power-up", 5000, "start_powerup", "triple_shot"),
    ShopItem("Shield", "Start with temporary invincibility", 4000, "shield_time", 5),
]

def shop_screen():
    font_title = pygame.font.Font(None, 72)
    font = pygame.font.Font(None, 36)
    
    # Reset all items to unpurchased state
    for item in SHOP_ITEMS:
        item.purchased = False
    
    title = font_title.render("SHOP", True, YELLOW)
    total_coins = load_total_score()
    
    selected_item = 0
    clock = pygame.time.Clock()
    running = True
    
    while running:
        clock.tick(60)
        screen.fill(BLACK)
        
        # Draw title and total coins
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        coins_text = font.render(f"Your Coins: {total_coins}", True, YELLOW)
        screen.blit(coins_text, (WIDTH//2 - coins_text.get_width()//2, 100))
        
        # Draw items
        for i, item in enumerate(SHOP_ITEMS):
            y_pos = 200 + i * 60
            color = YELLOW if i == selected_item else WHITE
            
            # Draw selection box
            if i == selected_item:
                pygame.draw.rect(screen, color, (WIDTH//4 - 10, y_pos - 5, WIDTH//2 + 20, 50), 2)
            
            # Draw item name and cost
            name_text = font.render(item.name, True, color)
            cost_text = font.render(f"{item.cost} coins", True, color)
            status_text = font.render("PURCHASED" if item.purchased else "", True, GREEN)
            
            screen.blit(name_text, (WIDTH//4, y_pos))
            screen.blit(cost_text, (WIDTH//2, y_pos))
            screen.blit(status_text, (3*WIDTH//4, y_pos))
            
            # Draw description
            if i == selected_item:
                desc_text = font.render(item.description, True, WHITE)
                screen.blit(desc_text, (WIDTH//2 - desc_text.get_width()//2, y_pos + 25))
        
        # Draw instructions
        instructions = font.render("↑/↓: Select   ENTER: Buy   ESC: Return", True, WHITE)
        screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT - 50))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_item = (selected_item - 1) % len(SHOP_ITEMS)
                elif event.key == pygame.K_DOWN:
                    selected_item = (selected_item + 1) % len(SHOP_ITEMS)
                elif event.key == pygame.K_RETURN:
                    # Try to purchase selected item
                    item = SHOP_ITEMS[selected_item]
                    if not item.purchased and total_coins >= item.cost:
                        item.purchased = True
                        total_coins -= item.cost
                        save_total_score(total_coins)
                        # Play power-up sound for purchase
                        sound_manager.play_powerup()
                elif event.key == pygame.K_ESCAPE:
                    running = False

# Main game loop
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Shooter")
    
    ESC_QUIT_GAME = False
    PLAYER_NAME = None  # Always start with no player name
    
    # Main game loop
    running = True
    while running:
        try:
            if ESC_QUIT_GAME:
                break
            
            # Always get the name at the start of each game session
            PLAYER_NAME = get_player_name()
            if not PLAYER_NAME:
                break  # Exit if no name provided
            
            # Show welcome screen
            welcome_screen()
            
            # Check if user wants to quit
            if ESC_QUIT_GAME:
                break
                
        except SystemExit:
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            break
    
    pygame.quit()
    sys.exit()