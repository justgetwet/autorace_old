# coding: UTF-8
import pygame
from pygame.locals import *
import sys
import datetime
from race import Race

def main():
    pygame.init()
    screen = pygame.display.set_mode((256, 256 + 128))
    font = pygame.font.Font("./fonts/RictyDiminished-Regular.ttf", 20)
    frog = pygame.image.load("frog.png").convert_alpha()
    ck = pygame.time.Clock()
    dt_start = datetime.datetime.now()
    races = Race().today()
    at_once = True
    while True:
        ck.tick(30) #1秒間で30フレームになるように33msecのwait
        dt_now = datetime.datetime.now()
        clock = dt_now.strftime('%m/%d %H:%M:%S')
        screen.fill((255,255,255)) 
        screen.blit(frog, (0, 64), (0, 0, 256, 256))
        # text = font.render(clock, True, (255,255,255), (0,255,0))
        text = font.render(races[0], True, (255,255,255), (0,255,0))
        screen.blit(text, (32, 16))
        if at_once and dt_now.second - dt_start.second > 3:
            pygame.mixer.music.load('hello.mp3')
            pygame.mixer.music.play()
            at_once = False
        
        pygame.display.update()                                         # 画面更新
        # イベント処理
        for event in pygame.event.get():  # イベントキューからキーボードやマウスの動きを取得
            if event.type == QUIT:        # 閉じるボタンが押されたら終了
                pygame.quit()             # Pygameの終了(ないと終われない)
                sys.exit()                # 終了（ないとエラーで終了することになる）

if __name__ == "__main__":
    main()
