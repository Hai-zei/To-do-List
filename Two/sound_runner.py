import pygame
import pyaudio
import numpy as np
import random
import sys
import os
import cv2

# 初始化 Pygame
pygame.init()
pygame.mixer.init()

# 游戏常量
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

# 设置游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("声音跑酷")
clock = pygame.time.Clock()

# 音频设置
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
THRESHOLD = 0.1


def load_image(path, scale=None):
    """
    加载图像并根据需要进行缩放
    :param path: 图像文件路径
    :param scale: 缩放比例，格式为 (width, height)
    :return: 加载并处理后的图像
    """
    try:
        image = pygame.image.load(path).convert_alpha()
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except pygame.error as e:
        print(f"加载图像 {path} 时出错: {e}")
        return None


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.run_frames = [
            load_image(f"assets/metest({i + 1}).png") for i in range(3)
        ]  # 非跳跃状态下的动画帧
        self.jump_frames = [
            load_image(f"assets/jump_{i + 1}.png") for i in range(2)
        ]  # 跳跃状态下的动画帧

        # 调整帧大小，放大 1.25 倍，并设置高度比大障碍物高 50px
        target_height = 70 + 50  # 大障碍物高度为 70
        scale_factor = target_height / self.run_frames[0].get_height()
        self.run_frames = [
            pygame.transform.scale(frame, (int(frame.get_width() * scale_factor), target_height))
            for frame in self.run_frames
        ]
        self.jump_frames = [
            pygame.transform.scale(frame, (int(frame.get_width() * scale_factor), target_height))
            for frame in self.jump_frames
        ]

        self.current_frame = 0
        self.image = self.run_frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - 100
        self.velocity_y = 0
        self.jumping = False
        self.gravity = 0.8
        self.double_jump_available = True
        self.animation_timer = 0
        self.sound_active = False

    def update(self):
        # 重力效果
        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y

        # 地面碰撞检测
        if self.rect.bottom > SCREEN_HEIGHT - 50:
            self.rect.bottom = SCREEN_HEIGHT - 50
            self.velocity_y = 0
            self.jumping = False

        if self.rect.bottom == SCREEN_HEIGHT - 50:  # 如果玩家在地面上，重置二连跳
            self.double_jump_available = True

        # 更新动画帧
        self.animation_timer += 1
        if self.animation_timer >= 10:  # 每 10 帧切换一次动画
            if self.jumping or self.velocity_y != 0:  # 跳跃状态
                self.current_frame = (self.current_frame + 1) % len(self.jump_frames)
                self.image = self.jump_frames[self.current_frame]
            else:  # 非跳跃状态
                self.current_frame = (self.current_frame + 1) % len(self.run_frames)
                self.image = self.run_frames[self.current_frame]
            self.animation_timer = 0

    def jump(self):
        if not self.jumping and self.rect.bottom >= SCREEN_HEIGHT - 50:
            self.velocity_y = -20
            self.jumping = True
        elif self.jumping and self.double_jump_available:  # 检查是否可以二连跳
            self.velocity_y = -14  # 二连跳的高度更高
            self.double_jump_available = False


class Ground(pygame.sprite.Sprite):
    def __init__(self, y):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH, 50))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = y

    def update(self):
        pass  # 地面不需要移动


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, obstacle_type):
        super().__init__()
        if obstacle_type == "enemy_one":
            self.image = load_image("assets/enemy_one.png", (30, 70))
        else:  # obstacle_type == "enemy_two"
            self.image = load_image("assets/enemy_two.png", (50, 100))

        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH
        self.rect.y = SCREEN_HEIGHT - 50 - self.rect.height  # 调整位置，使其在地面上
        self.speed = 5
        self.obstacle_type = obstacle_type

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()


class Game:
    def __init__(self):
        self.player = Player()
        self.all_sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        self.ground = Ground(SCREEN_HEIGHT)  # 初始化地面
        self.all_sprites.add(self.ground)

        self.background = load_image("assets/background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.score = 0  # 初始化得分
        self.game_over = False
        self.font = pygame.font.Font(None, 48)  # 调整字体大小
        self.obstacle_spawn_rate = 0.01  # 降低障碍物生成率

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True

    def check_sound(self, stream):
        try:
            data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.float32)
            if np.max(np.abs(data)) > THRESHOLD:
                self.player.sound_active = True  # 声音检测到时设置标志
                self.player.jump()
            else:
                self.player.sound_active = False  # 没有声音时重置标志
        except Exception as e:
            print(f"音频读取错误: {e}")

    def update(self):
        self.all_sprites.update()
        self.obstacles.update()

        # 更新得分：检测玩家是否跨过障碍物
        for obstacle in self.obstacles:
            if obstacle.rect.right < self.player.rect.left:  # 玩家已跨过障碍物
                if obstacle.obstacle_type == "enemy_one":
                    self.score += 1  # 跨过小障碍物加 1 分
                elif obstacle.obstacle_type == "enemy_two":
                    self.score += 2  # 跨过大障碍物加 2 分
                obstacle.kill()  # 移除障碍物

        # 生成障碍物
        if random.random() < self.obstacle_spawn_rate and not self.game_over:
            if random.random() < 0.75:  # 75% 概率生成 enemy_one
                obstacle = Obstacle("enemy_one")
            else:  # 25% 概率生成 enemy_two
                obstacle = Obstacle("enemy_two")
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)

        # 碰撞检测
        hits = pygame.sprite.spritecollide(self.player, self.obstacles, False)
        if hits:
            self.game_over = True

    def draw(self):
        # 绘制背景图
        if self.background:
            screen.blit(self.background, (0, 0))

        self.all_sprites.draw(screen)

        # 显示得分
        score_text = self.font.render(f'Score: {self.score}', True, GREEN)  # 使用绿色字体
        text_rect = score_text.get_rect(topleft=(10, 10))  # 显示在屏幕左上角
        screen.blit(score_text, text_rect)

        if self.game_over:
            game_over_text = self.font.render('Game Over! Press SPACE to restart', True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2))

        pygame.display.flip()


def play_video(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"无法打开视频文件: {video_path}")
            return

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("视频读取结束或发生错误")
                break

            try:
                frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                screen.blit(frame_surface, (0, 0))
                pygame.display.update()
            except Exception as e:
                print(f"处理视频帧时出错: {e}")
                break

            # 检查用户是否按下 "Enter" 键
            if any(event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN for event in pygame.event.get()):
                break
    except Exception as e:
        print(f"播放视频时出错: {e}")
    finally:
        if 'cap' in locals():
            cap.release()
    print("视频播放结束")


def start_screen():
    # 显示开始页面图片
    start_image = load_image("assets/start.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    if start_image:
        screen.blit(start_image, (0, 0))
        pygame.display.update()

    # 播放开始音频
    try:
        pygame.mixer.music.load("source/start.mp3")  # 加载音频文件
        pygame.mixer.music.play(-1)  # 循环播放音频
    except pygame.error as e:
        print(f"加载开始音频时出错: {e}")

    # 等待用户按下 "Enter" 键
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False
                pygame.mixer.music.stop()  # 停止播放音频
                # 清空屏幕，停止显示开始页面
                screen.fill(BLACK)
                pygame.display.update()


def main():
    start_screen()  # 显示开始页面并播放视频

    try:
        pygame.mixer.music.load("source/stand.mp3")  # 加载新的背景音乐
        pygame.mixer.music.play(-1)  # 循环播放背景音乐
    except pygame.error as e:
        print(f"加载背景音乐时出错: {e}")

    game = Game()
    running = True

    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        while running:
            running = game.handle_events()
            if not game.game_over:
                game.check_sound(stream)
                game.update()
            else:
                pygame.mixer.music.stop()  # 游戏结束后停止音乐
            game.draw()
            clock.tick(FPS)
    except Exception as e:
        print(f"游戏运行错误: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    main()
    