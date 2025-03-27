import pygame
import random
import sys
import speech_recognition as sr
import threading
import queue
import time
import pygame_gui
import os
from pygame import mixer
import math

# 初始化Pygame
pygame.init()
pygame.mixer.init()

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
JUMP_FORCE = -15
SCROLL_SPEED = 5
OBSTACLE_SPAWN_RANGE = (2, 4)  # 障碍物生成间隔（秒）
INVINCIBILITY_DURATION = 1.0  # 无敌时间（秒）
DIFFICULTY_INTERVAL = 30  # 难度提升间隔（秒）
SPEED_INCREASE = 0.1  # 速度增加比例

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)

# 设置游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D跑酷游戏 - 语音控制版")
clock = pygame.time.Clock()

# 语音控制相关
class VoiceController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.command_queue = queue.Queue()
        self.running = True
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _listen_loop(self):
        with sr.Microphone() as source:
            print("正在调整麦克风...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)  # 增加环境噪音调整时间
            print("麦克风已就绪！")

            while self.running:
                try:
                    print("正在听...")
                    # 增加超时时间和语音时长限制
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    try:
                        text = self.recognizer.recognize_google(audio, language='zh-CN')
                        print(f"识别到: {text}")
                        self._process_command(text)
                    except sr.UnknownValueError:
                        print("无法识别语音")
                    except sr.RequestError as e:
                        print(f"无法连接到Google语音识别服务: {e}")
                except Exception as e:
                    print(f"语音识别错误: {e}")
                    time.sleep(0.5)  # 增加错误后的等待时间

    def _process_command(self, text):
        if "跳" in text:
            self.command_queue.put("jump")
        elif "蹲" in text:
            self.command_queue.put("slide")
        elif "开始" in text:
            self.command_queue.put("start")
        elif "二段跳" in text:
            self.command_queue.put("double_jump")

    def get_next_command(self):
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None

# 加载资源
def load_image(name, scale=1):
    try:
        image = pygame.image.load(os.path.join('assets', name)).convert_alpha()
        if scale != 1:
            new_size = (int(image.get_width() * scale), int(image.get_height() * scale))
            image = pygame.transform.scale(image, new_size)
        return image
    except:
        # 如果找不到图片，创建一个占位图
        surface = pygame.Surface((50, 50))
        surface.fill(BLUE)
        return surface

class SpriteSheet:
    def __init__(self, image, frame_width, frame_height, frames, duration):
        self.sheet = image
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frames = frames
        self.duration = duration
        self.current_frame = 0
        self.animation_timer = 0
        self.rect = pygame.Rect(0, 0, frame_width, frame_height)

    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.duration / self.frames:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % self.frames

    def get_current_frame(self):
        self.rect.x = self.current_frame * self.frame_width
        return self.sheet.subsurface(self.rect)

class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.emitters = []

    def create_dust(self, x, y):
        for _ in range(5):
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(0, 2),
                'life': 1.0,
                'color': (200, 200, 200)
            }
            self.particles.append(particle)

    def create_explosion(self, x, y):
        for _ in range(10):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(2, 5)
            particle = {
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.0,
                'color': (255, 100, 0)
            }
            self.particles.append(particle)

    def update(self, dt):
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= dt
            if particle['life'] <= 0:
                self.particles.remove(particle)

    def draw(self, surface):
        for particle in self.particles:
            alpha = int(particle['life'] * 255)
            color = (*particle['color'], alpha)
            pos = (int(particle['x']), int(particle['y']))
            pygame.draw.circle(surface, color, pos, 2)

class ParallaxBackground:
    def __init__(self):
        self.layers = []
        self.speeds = [0.2, 0.5, 1.0]  # 不同层的滚动速度
        for i, speed in enumerate(self.speeds):
            layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            layer.fill((200 - i * 50, 150 - i * 30, 100 - i * 20))  # 沙漠色调
            self.layers.append({
                'surface': layer,
                'speed': speed,
                'x': 0
            })

    def update(self):
        for layer in self.layers:
            layer['x'] -= layer['speed']
            if layer['x'] <= -SCREEN_WIDTH:
                layer['x'] = 0

    def draw(self, surface):
        for layer in self.layers:
            surface.blit(layer['surface'], (layer['x'], 0))
            surface.blit(layer['surface'], (layer['x'] + SCREEN_WIDTH, 0))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 加载角色精灵图
        self.sprite_sheet = SpriteSheet(load_image('player.png'), 50, 50, 6, 0.5)
        self.image = self.sprite_sheet.get_current_frame()
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - 100
        self.velocity_y = 0
        self.jumping = False
        self.double_jump_available = False
        self.sliding = False
        self.slide_timer = 0
        self.slide_duration = 0.5
        self.invincible = False
        self.invincibility_timer = 0
        self.original_height = 50
        self.facing_right = True

    def update(self, dt):
        # 更新动画
        self.sprite_sheet.update(dt)
        self.image = self.sprite_sheet.get_current_frame()
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

        # 重力效果
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        # 地面碰撞检测
        if self.rect.bottom > SCREEN_HEIGHT - 50:
            self.rect.bottom = SCREEN_HEIGHT - 50
            self.velocity_y = 0
            self.jumping = False
            self.double_jump_available = True
            self.sliding = False

        # 滑行状态更新
        if self.sliding:
            self.slide_timer += dt
            if self.slide_timer >= self.slide_duration:
                self.sliding = False
                self.slide_timer = 0
                self.rect.height = self.original_height

        # 无敌状态更新
        if self.invincible:
            self.invincibility_timer += dt
            if self.invincibility_timer >= INVINCIBILITY_DURATION:
                self.invincible = False
                self.invincibility_timer = 0

    def jump(self):
        if not self.jumping:
            self.velocity_y = JUMP_FORCE
            self.jumping = True
            self.facing_right = True
        elif self.double_jump_available:
            self.velocity_y = JUMP_FORCE * 0.8
            self.double_jump_available = False

    def slide(self):
        if not self.jumping and not self.sliding:
            self.sliding = True
            self.slide_timer = 0
            self.rect.height = 25
            self.invincible = True
            self.invincibility_timer = 0

class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = random.randint(SCREEN_HEIGHT - 200, SCREEN_HEIGHT - 100)
        self.speed = SCROLL_SPEED

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = pygame.Surface((30, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = SCREEN_HEIGHT - 50
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

class Game:
    def __init__(self):
        self.background = ParallaxBackground()
        self.player = Player()
        self.all_sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        self.score = 0
        self.game_over = False
        self.font = pygame.font.Font(None, 36)
        self.last_obstacle_time = 0
        self.last_coin_time = 0
        self.voice_controller = VoiceController()
        self.game_started = False
        self.voice_controller.start()
        self.current_speed = SCROLL_SPEED
        self.last_difficulty_increase = 0
        self.game_time = 0
        
        # 初始化粒子系统
        self.particles = ParticleSystem()
        
        # 初始化GUI
        self.gui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.score_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (200, 30)),
            text='Score: 0',
            manager=self.gui_manager
        )
        self.command_feedback = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 50), (200, 30)),
            text='',
            manager=self.gui_manager
        )

    def handle_events(self):
        time_delta = clock.tick(FPS)/1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                    self.particles.create_dust(self.player.rect.centerx, self.player.rect.bottom)
                if event.key == pygame.K_DOWN:
                    self.player.slide()
            
            self.gui_manager.process_events(event)
        
        self.gui_manager.update(time_delta)
        return True

    def handle_voice_commands(self):
        command = self.voice_controller.get_next_command()
        if command:
            if command == "jump":
                self.player.jump()
                self.particles.create_dust(self.player.rect.centerx, self.player.rect.bottom)
                self.command_feedback.set_text("跳跃!")
            elif command == "slide":
                self.player.slide()
                self.command_feedback.set_text("滑行!")
            elif command == "start" and not self.game_started:
                self.game_started = True
                self.game_over = False
                self.score = 0
                self.obstacles.empty()
                self.coins.empty()
                self.last_obstacle_time = 0
                self.last_coin_time = 0
                self.current_speed = SCROLL_SPEED
                self.last_difficulty_increase = 0
                self.game_time = 0
                self.command_feedback.set_text("游戏开始!")
            elif command == "double_jump":
                self.player.jump()
                self.command_feedback.set_text("二段跳!")

    def spawn_obstacle(self):
        current_time = pygame.time.get_ticks() / 1000
        if current_time - self.last_obstacle_time >= random.uniform(*OBSTACLE_SPAWN_RANGE):
            obstacle = Obstacle(self.current_speed)
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)
            self.last_obstacle_time = current_time

    def spawn_coin(self):
        current_time = pygame.time.get_ticks() / 1000
        if current_time - self.last_coin_time >= 3:  # 每3秒生成一个金币
            coin = Coin()
            self.coins.add(coin)
            self.all_sprites.add(coin)
            self.last_coin_time = current_time

    def update_difficulty(self):
        current_time = pygame.time.get_ticks() / 1000
        if current_time - self.last_difficulty_increase >= DIFFICULTY_INTERVAL:
            self.current_speed *= (1 + SPEED_INCREASE)
            self.last_difficulty_increase = current_time

    def update(self, dt):
        self.background.update()
        self.all_sprites.update(dt)
        self.obstacles.update()
        self.coins.update()
        self.particles.update(dt)

        # 处理语音命令
        self.handle_voice_commands()

        if not self.game_over and self.game_started:
            # 更新游戏时间
            self.game_time += dt
            # 每1秒加10分
            self.score = int(self.game_time * 10)
            self.score_label.set_text(f'Score: {self.score}')

            # 生成障碍物和金币
            self.spawn_obstacle()
            self.spawn_coin()

            # 更新难度
            self.update_difficulty()

            # 收集金币
            coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True)
            for coin in coin_hits:
                self.score += 50
                self.particles.create_explosion(coin.rect.centerx, coin.rect.centery)

            # 碰撞检测（考虑无敌状态）
            if not self.player.invincible:
                hits = pygame.sprite.spritecollide(self.player, self.obstacles, False)
                if hits:
                    self.game_over = True
                    self.particles.create_explosion(self.player.rect.centerx, self.player.rect.centery)

    def draw(self):
        self.background.draw(screen)
        self.all_sprites.draw(screen)
        self.particles.draw(screen)
        
        # 绘制GUI
        self.gui_manager.draw_ui(screen)

        if not self.game_started:
            start_text = self.font.render('说"开始"来开始游戏', True, RED)
            screen.blit(start_text, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2))
        elif self.game_over:
            game_over_text = self.font.render('游戏结束！说"开始"重新开始', True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2))

        pygame.display.flip()

    def cleanup(self):
        self.voice_controller.stop()

def main():
    game = Game()
    running = True

    try:
        while running:
            dt = clock.tick(FPS)/1000.0
            running = game.handle_events()
            game.update(dt)
            game.draw()
    finally:
        game.cleanup()
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()