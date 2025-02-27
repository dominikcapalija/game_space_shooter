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

# Ship class
class Ship(pygame.sprite.Sprite):
    def __init__(self, image, speed):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed = speed
        self.shoot_delay = 250  # milliseconds
        self.last_shot = pygame.time.get_ticks()

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
    
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            return Bullet(self.rect.centerx, self.rect.top)
        return None

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 10

    def update(self):
        self.rect.y -= self.speed
        # Kill if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()

# Asteroid class
class Asteroid(pygame.sprite.Sprite):
    def __init__(self):
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
        
        # Draw the asteroid
        pygame.draw.polygon(self.image, BROWN, points)
        
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(1, 4)
        self.speedx = random.randrange(-2, 2)

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
def update_high_scores(player_name, score):
    high_scores = load_high_scores()
    high_scores.append({"name": player_name, "score": score})
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
        
        screen.blit(rank_text, (WIDTH // 2 - 200, y_pos))
        screen.blit(name_text, (WIDTH // 2 - 150, y_pos))
        screen.blit(score_text, (WIDTH // 2 + 150, y_pos))
        
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
        print("tick")

        for event in pygame.event.get():
            print("got event")
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
    bullets = pygame.sprite.Group()
    
    # Create player ship
    player = Ship(ship_img, ship_speed)
    all_sprites.add(player)
    
    # Create asteroids
    for i in range(8):
        a = Asteroid()
        all_sprites.add(a)
        asteroids.add(a)
    
    # Score
    score = 0
    font = pygame.font.Font(None, 36)
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
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
                elif event.key == pygame.K_SPACE:
                    bullet = player.shoot()
                    if bullet:
                        all_sprites.add(bullet)
                        bullets.add(bullet)
        
        # Update
        all_sprites.update()
        
        # Check for bullet/asteroid collisions
        hits = pygame.sprite.groupcollide(asteroids, bullets, True, True)
        for hit in hits:
            score += 50
            a = Asteroid()
            all_sprites.add(a)
            asteroids.add(a)
        
        # Check for player/asteroid collisions
        hits = pygame.sprite.spritecollide(player, asteroids, False)
        if hits:
            running = False
        
        # Draw / render
        screen.fill(BLACK)
        all_sprites.draw(screen)
        
        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Draw player name
        name_text = font.render(f"Player: {player_name}", True, WHITE)
        screen.blit(name_text, (10, 50))
        
        # Flip the display
        pygame.display.flip()
    
    # Update high scores
    high_scores = update_high_scores(player_name, score)
    
    # Game over screen
    game_over_font = pygame.font.Font(None, 72)
    game_over_text = game_over_font.render("GAME OVER", True, RED)
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 150))
    
    final_score = font.render(f"Final Score: {score}", True, WHITE)
    screen.blit(final_score, (WIDTH//2 - final_score.get_width()//2, HEIGHT//2 - 80))
    
    player_name_text = font.render(f"Player: {player_name}", True, WHITE)
    screen.blit(player_name_text, (WIDTH//2 - player_name_text.get_width()//2, HEIGHT//2 - 40))
    
    high_score_text = font.render("Press H to view high scores", True, WHITE)
    screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, HEIGHT//2 + 20))
    
    restart_text = font.render("Press R to restart or ESC to quit", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 70))
    
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
