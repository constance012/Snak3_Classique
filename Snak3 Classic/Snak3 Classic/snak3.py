import pygame

import assets.framework as frwk

# Initialize Pygame.
pygame.init()

# FPS clock.
mainClock = pygame.time.Clock()
framerate = 60

monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h]

# Create windows.
pygame.display.set_caption('Snak3 Classique')
pygame.display.set_icon(pygame.image.load('assets/images/snak3.png'))
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
ws = [screen.get_width(), screen.get_height()]  # Window Size.

# Create instance.
main_sys = frwk.Main_System(screen, ws, monitor_size, mainClock, framerate)

# Gọi main menu để chạy cả chương trình khi và chỉ khi snak3.py là chương trình chính.
if __name__ == '__main__':
	main_sys.main_menu()
