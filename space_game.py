import pygame
import random
import sys
import math
import os
import json

# Initialize pygame
pygame.init()

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
    STRAY_BOMB = "stray_bomb"  # New power-up type
    
    def __init__(self, x, y):
        super().__init__()
        self.type = random.choice([PowerUp.RAPID_FIRE, PowerUp.DOUBLE_SHOT, PowerUp.STRAY_BOMB])
        self.size = 20
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        if self.type == PowerUp.RAPID_FIRE:
            color = YELLOW
            # Draw lightning bolt
            points = [(10, 0), (20, 8), (13, 12), (20, 20), (0, 12), (7, 8)]
            pygame.draw.polygon(self.image, color, points)
        elif self.type == PowerUp.DOUBLE_SHOT:
            color = PURPLE
            # Draw double circle
            pygame.draw.circle(self.image, color, (5, 10), 5)
            pygame.draw.circle(self.image, color, (15, 10), 5)
        else:  # STRAY_BOMB
            color = RED
            # Draw bomb icon
            pygame.draw.circle(self.image, color, (self.size//2, self.size//2), self.size//2 - 2)
            pygame.draw.line(self.image, YELLOW, (self.size//2, 0), (self.size//2, self.size//4), 2)
        
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
    def __init__(self, image, speed):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed = speed
        self.base_shoot_delay = 250  # milliseconds
        self.shoot_delay = self.base_shoot_delay
        self.last_shot = pygame.time.get_ticks()
        
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
    player = Ship(ship_img, ship_speed)
    all_sprites.add(player)
    
    # Level settings
    level = 1
    level_score_threshold_delta = 1000  # Score needed to advance to next level
    level_score_threshold = level_score_threshold_delta
    asteroid_count = 6
    enemy_count = 2
    
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
            
            # Make level progression more consistent by using a fixed increment
            level_score_threshold += level_score_threshold_delta
        
        # Handle level transition
        if level_transition:
            current_time = pygame.time.get_ticks()
            if current_time - transition_start_time > transition_duration:
                level_transition = False
                
                # Create new asteroids and enemies for the new level
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
            
            # Check for bullet/bomb collisions and create explosions
            hits = pygame.sprite.groupcollide(bombs, player_bullets, True, True)
            for bomb in hits:
                explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                all_sprites.add(explosion)
                explosions.add(explosion)
                
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
                
                # Check if player is caught in explosion
                player_distance = math.sqrt(
                    (player.rect.centerx - explosion.center_x) ** 2 +
                    (player.rect.centery - explosion.center_y) ** 2
                )
                if player_distance <= explosion.radius:
                    running = False
            
            # Check for bullet/asteroid collisions
            hits = pygame.sprite.groupcollide(asteroids, player_bullets, True, True)
            for hit in hits:
                score += 50
                
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
            if bomb_hits:
                for bomb in bomb_hits:
                    explosion = Explosion(bomb.rect.centerx, bomb.rect.centery)
                    all_sprites.add(explosion)
                    explosions.add(explosion)
                    
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
            
            # Check for player/power-up collisions
            hits = pygame.sprite.spritecollide(player, power_ups, True)
            for hit in hits:
                player.add_power_up(hit.type)
            
            # Check for player collisions with other hazards
            for hazard_group in [asteroids, enemy_ships, enemy_bullets]:
                hits = pygame.sprite.spritecollide(player, hazard_group, False)
                if hits:
                    running = False
        
        # Draw / render
        screen.fill(BLACK)
        
        if level_transition:
            # Draw level transition screen
            level_font = pygame.font.Font(None, 72)
            level_text = level_font.render(f"LEVEL {level}", True, YELLOW)
            screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 - 50))
            
            # Draw level description
            desc_font = pygame.font.Font(None, 36)
            desc_text = desc_font.render(f"Challenge Level {level}!", True, WHITE)
            screen.blit(desc_text, (WIDTH//2 - desc_text.get_width()//2, HEIGHT//2 + 20))
        else:
            # Draw game elements
            all_sprites.draw(screen)
            
            # Draw score
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
            
            # Draw level at top right
            level_text = font.render(f"Level {level}", True, WHITE)
            screen.blit(level_text, (WIDTH - level_text.get_width() - 10, 10))
            
            # Draw player name
            name_text = font.render(f"Player: {player_name}", True, WHITE)
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
                if PowerUp.STRAY_BOMB in player.power_ups:
                    power_up_text.append("STRAY BOMB")
                if power_up_text:
                    power_up_display = font.render(" + ".join(power_up_text), True, YELLOW)
                    screen.blit(power_up_display, (10, 90))
                    
                # Draw power-up timer
                remaining = (player.power_up_duration - (pygame.time.get_ticks() - player.power_up_start)) // 1000
                if remaining > 0:
                    timer_text = font.render(f"({remaining}s)", True, YELLOW)
                    screen.blit(timer_text, (10, 120))
        
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
