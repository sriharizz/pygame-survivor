from random import randint,choice
from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites
class Game:
    def __init__(self):
        #setup
        pygame.init()
        self.display_surface=pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
        pygame.display.set_caption("SURVIVOR")
        self.clock=pygame.time.Clock()
        self.running=True
        

        #groups
        self.all_sprites= AllSprites()
        self.collision_sprites=pygame.sprite.Group()
        self.bullet_sprites=pygame.sprite.Group()
        self.enemy_sprites=pygame.sprite.Group()

        #gun timer
        self.can_shoot=True
        self.shoot_time=0
        self.gun_cooldown=100

        #enemy timer
        self.enemy_event=pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event,300)
        self.spawn_positions=[]

        #sound
        self.shoot_sound=pygame.mixer.Sound(join('audio','shoot.wav'))
        self.shoot_sound.set_volume(0.4)
        self.impact_sound=pygame.mixer.Sound(join('audio','impact.ogg'))
        self.music=pygame.mixer.Sound(join('audio','music.wav'))
        self.music.set_volume(0.3)
        self.music.play(loops=-1)
        self.heart_image = pygame.image.load(join('images', 'heart','heart.png')).convert_alpha()
        self.heart_image = pygame.transform.scale(self.heart_image, (32, 32))  # Resize if needed
        self.load_images()
        self.setup()
    def load_images(self):
        self.surf=pygame.image.load(join('images','gun','bullet.png')).convert_alpha()

        folders=list((walk(join('images','enemies'))))[0][1]
        self.enemy_frames={}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images','enemies',folder)):
                self.enemy_frames[folder]=[]
                for file_name in sorted(file_names,key=lambda name: int(name.split('.')[0])):
                    full_path=join(folder_path,file_name)
                    surf=pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)
    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos=self.gun.rect.center+self.gun.player_direction*50
            bullet(self.surf,pos,self.gun.player_direction,(self.all_sprites,self.bullet_sprites))
            self.can_shoot=False
            self.shoot_time=pygame.time.get_ticks()
    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True
    def setup(self):
        map=load_pygame(join('data','maps','world.tmx'))
        for x,y,image in map.get_layer_by_name('Ground').tiles():
            Sprite((x*TILE_SIZE,y*TILE_SIZE),image,(self.all_sprites))
        for obj in map.get_layer_by_name('Objects'):
            collisionSprite((obj.x,obj.y),obj.image,(self.all_sprites,self.collision_sprites))
        for obj in map.get_layer_by_name('Collisions'):
            collisionSprite((obj.x,obj.y),pygame.Surface((obj.width,obj.height)),self.collision_sprites)
        for obj in map.get_layer_by_name('Entities'):
            if obj.name=='Player':
                self.player=Player((obj.x,obj.y),self.all_sprites,self.collision_sprites)
                self.gun=Gun(self.player,self.all_sprites)
            else:
                self.spawn_positions.append((obj.x,obj.y))
    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites=pygame.sprite.spritecollide(bullet,self.enemy_sprites,False,pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        sprite.destroy()
                    bullet.kill()
    def player_collision(self):
        current_time = pygame.time.get_ticks()
        
        if current_time - self.player.last_hit_time > self.player.hit_cooldown:
            if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
                self.player.health -= 1
                self.player.last_hit_time = current_time
                
                # Visual feedback - flash red
                flash_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                flash_surface.fill((255, 0, 0))
                flash_surface.set_alpha(100)
                self.display_surface.blit(flash_surface, (0, 0))
                pygame.display.update()
                pygame.time.delay(50)  # Brief flash
                
                if self.player.health <= 0:
                    self.show_game_over()
                    self.running = False
    def show_game_over(self):
        # Pause all sounds
        pygame.mixer.stop()

        # Create semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)  # transparency level (0-255)
        overlay.fill((0, 0, 0))  # black overlay
        self.display_surface.blit(overlay, (0, 0))

        # Game Over Text (Glow effect)
        font = pygame.font.SysFont("arialblack", 100)
        text = font.render('GAME OVER', True, (255, 0, 0))
        glow = font.render('GAME OVER', True, (255, 100, 100))

        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        glow_rect = glow.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 5))

        self.display_surface.blit(glow, glow_rect)  # soft glow
        self.display_surface.blit(text, text_rect)  # solid red

        # Smaller hint below
        small_font = pygame.font.SysFont("arial", 40)
        restart_text = small_font.render("Press R to Restart or Q to Quit", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100))
        self.display_surface.blit(restart_text, restart_rect)

        pygame.display.update()

        # Wait for player to choose (loop until R or Q is pressed)
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Restart the game
                        self.__init__()
                        self.run()
                        waiting = False
                    if event.key == pygame.K_q:
                        pygame.quit()
                        exit()


    def draw_health_bar(self):
        heart_width = self.heart_image.get_width()
        spacing = 5  # Space between hearts
        x, y = 10, 10  # Top-left position
        
        # Draw only the current hearts (no empty hearts)
        for i in range(self.player.health):
            self.display_surface.blit(self.heart_image, (x + i * (heart_width + spacing), y))
    def run(self):
        while self.running:
            #dt
            dt=self.clock.tick()/1000
            #event loop
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    self.running=False
                if event.type==self.enemy_event:
                    enemy(choice(self.spawn_positions),choice(list(self.enemy_frames.values())),(self.all_sprites,self.enemy_sprites),self.player,self.collision_sprites)
            #update
            self.gun_timer()
            self.input()
            self.all_sprites.update(dt)
            self.bullet_collision()
            self.player_collision()
            #draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            self.draw_health_bar()
            pygame.display.update()

        pygame.quit()
if __name__=='__main__':
    game=Game()
    game.run()
         


   