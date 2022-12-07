import pygame
from pygame.locals import *

import sys
import random

sys.path.append('../')

import assets.utility_funcs as util

pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.music.load('assets/musics/Blues.ogg')
pygame.mixer.music.set_volume(0.5)

# Colors.
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (152, 152, 152)
MEDIUM_GREY = (170, 170, 170)
LIGHT_GREY = (220, 220, 220)
RED = (255, 0, 0)
BLUE = (65, 105, 255)
YELLOW = (224, 208, 31)

# Images.
head_img = pygame.transform.scale(pygame.image.load('assets/images/head.png'), (20, 20))
body_img = pygame.transform.scale(pygame.image.load('assets/images/body.png'), (20, 20))
food_img = pygame.transform.scale(pygame.image.load('assets/images/food.png'), (20, 20))
boost_img = [pygame.transform.scale(pygame.image.load('assets/images/score_boost.png'), (20, 20)),
			pygame.transform.scale(pygame.image.load('assets/images/speed_boost.png'), (20, 20))]

# Sounds and music.
eating_sound = pygame.mixer.Sound('assets/sounds/eating.wav')
boost_sound = pygame.mixer.Sound('assets/sounds/boost.wav')
boost_sound.set_volume(0.5)
game_over_sound = pygame.mixer.Sound('assets/sounds/game_over.wav')
game_over_sound.set_volume(0.6)

# Set allowed events to be placed on the queue.
pygame.event.set_blocked(None)  # Block all the events.
pygame.event.set_allowed([QUIT, MOUSEBUTTONDOWN, KEYDOWN, VIDEORESIZE])  # Allow these specific events.

class Effect:

	def __init__(self, surf, color = BLACK):
		self.sw_list = []
		self.particles_list = []
		self.surf = surf
		self.color = color
		self.delay = 0

	# Shockwaves effect.
	def shockwaves_generate(self, x, y, click_flag=False, auto=False, duration=5):
		# Append [[x, y], radius, duration] of the shockwave.		
		if click_flag:
			self.delay = 3
			self.sw_list.append([[x, y], 1, duration])
		
		if auto:
			self.delay -= 0.2
			if (self.delay <= 0):
				self.delay = 3
				self.sw_list.append([[x, y], 1, 3])

		# Loop through the shockwave list.
		for sw in self.sw_list:
			if int(sw[2]) == 0:
				sw[2] = -1  # Set the width to -1, so it'll draw nothing.

			pygame.draw.circle(self.surf, self.color, [sw[0][0], sw[0][1]], sw[1], int(sw[2]))
			sw[2] -= 0.07  # Decrease the line width of the circle over time, equivalent to decrease its duration.
			sw[1] += 1  # Increase the radius of the circle over time.

		# Remove those if their duration runs out.
		for index, value in sorted(enumerate(self.sw_list), reverse=True):
			if value[2] <= 0:
				self.sw_list.pop(index)

	# Particles effect:
	def particles_generate(self, x, y):
		#for i in range(10):
		# Append [[x, y], move_speed, duration]
		random_x_vel = random.randint(0,40) / 10 - 2
		random_y_vel = random.randint(0,40) / 10 - 2
		self.particles_list.append([[x, y], [random_x_vel, random_y_vel], random.randint(2,3)])

		for particle in self.particles_list:
			# typically moves around by the random velocity.
			particle[0][0] += particle[1][0]
			particle[0][1] += particle[1][1]
			# typically changes over time:
			particle[2] -= 0.05
			#particle[1][1] += 0.1 # gravity of these particle
			pygame.draw.circle(self.surf, self.color, [int(particle[0][0]), int(particle[0][1])], int(particle[2]))

			radius = particle[2] * 2 #Bán kính xung quanh particle
			self.surf.blit(util.circle_to_surf(radius, (30,30,30)), (int(particle[0][0] - radius), int(particle[0][1] - radius)), special_flags=BLEND_RGB_ADD)
		
		# typically disappears after a certain amount of time:
		for index, value in sorted(enumerate(self.particles_list), reverse = True):
			if value[2] <= 0:
				self.particles_list.pop(index)

	def clear(self):
		self.particles_list.clear()
		self.sw_list.clear()

class Main_System:

	def __init__(self, main_screen, windows_size, monitor_size, fps_clock, framerate = 60):
		self.music_flag = False
		self.fllscrn_flag = False
		self.return_menu_flag = False
		self.retry_flag = False
		self.res_w = 800
		self.res_h = 600
		self.old_high_score = 0
		self.current_high_score = 0
		self.game_mode = 0
		self.move_speed = 20
		self.segment_size = 20
		self.monitor_size = monitor_size
		self.screen = main_screen
		self.ws = windows_size
		self.clock = fps_clock
		self.framerate = framerate
		self.visual_fx = Effect(self.screen)

	# Read from file.
	def read_data(self, file_name):
		try:
			f = open(file_name, 'r')
			print("Opened file:\n" + f.name)
			content = f.readlines()
		
			for line in content:
				line = line.strip().lower()
				if "music" in line:
					self.music_flag = line.split()[-1] == "true"
			
				elif "resolution" in line:
					splited_line = line.split()
					self.res_w = int(splited_line[2])
					self.res_h = int(splited_line[4])
			
				elif "fullscreen" in line:
					self.fllscrn_flag = line.split()[-1] == "true"

				elif "high score" in line:
					self.current_high_score = int(line.split()[-1])
					self.old_high_score = self.current_high_score

			print("\nRead file successfully.")
	
		except IOError:
			print('An error occurred while reading the file.')
	
		finally:
			f.close()

	# Write to file.
	def save_data(self, file_name):
		try:
			f = open(file_name, 'w')
			f.write(f'Music = {self.music_flag}\n')
			f.write(f'Resolution = {self.res_w} x {self.res_h}\n')
			f.write(f'Fullscreen = {self.fllscrn_flag}\n')
			f.write(f'High Score = {self.current_high_score}')
	
		except IOError:
			print('An error occurred while writing to the file.')
	
		finally:
			f.close()

	# Game.
	def start_game(self):
		# Fields:
		snake_pos = [100, 60]  # Head position.
		snake_body = [[100, 60], [80, 60], [60, 60]] # Position of each segments.


		# Food raw position.
		food_x = random.randrange(2, int(self.ws[0] / 10 - 3))
		food_y = random.randrange(3, int(self.ws[1] / 10 - 3))
		if food_x % 2 != 0:
			food_x += 1  # If it's odd, then increment by 1.
		
		if food_y % 2 != 0:
			food_y += 1
		
		food_pos = [food_x * 10, food_y * 10]  # Food actual position.
		food_available = True


		# Boost raw position.
		boost_x = random.randrange(2, int(self.ws[0] / 10 - 3))
		boost_y = random.randrange(3, int(self.ws[1] / 10 - 3))
		if boost_x % 2 != 0:
			boost_x += 1  # If it's odd, then increment by 1.
		
		if boost_y % 2 != 0:
			boost_y += 1
		
		# If the boost overlap the food, then move the boost over.
		if boost_x == food_x and boost_y == food_y:
			boost_x += 20
			if boost_x == self.ws[0] - 30:
				boost_x -= 20
		
		boost_pos = [boost_x * 10, boost_y * 10]  # Boost actual position.
		boost_available = True

		# Index for the type of boost: 0 for score x5, 1 for speed x1.5
		index = random.randint(0, 1)
		if index == 0:
			boost_duration = 75
		elif index == 1:
			boost_duration = 113


		direction = 'RIGHT'  # Starting direction.
		change_to = direction  # New direction.
		score = 0
		apple_count = 0  # Checking when the boost will respawn.	

		self.retry_flag = self.return_menu_flag = False
		self.visual_fx.clear()


		# Restart game nested function.
		def restart_game():
			nonlocal snake_pos, snake_body, score, apple_count, direction, change_to, boost_available, boost_duration
			
			self.visual_fx.clear()
			
			snake_pos = [100, 60]
			snake_body = [[100, 60], [80, 60], [60, 60]]
			score = 0
			apple_count = 0
			direction = 'RIGHT'
			change_to = direction
			boost_available = True
			index = random.randint(0, 1)
			
			if index == 0:
				boost_duration = 75
			else:
				boost_duration = 113


			nonlocal food_x, food_y, food_pos, boost_x, boost_y, boost_pos
			

			# Make a new boost position.
			food_x = random.randrange(2, int(self.ws[0] / 10 - 3))
			food_y = random.randrange(3, int(self.ws[1] / 10 - 3))
			if food_x % 2 != 0:
				food_x += 1  # If it's odd, then increment by 1.
		
			if food_y % 2 != 0:
				food_y += 1
		
			food_pos = [food_x * 10, food_y * 10]  # Food actual position.
			

			# Make a new boost position.
			boost_x = random.randrange(2, int(self.ws[0] / 10 - 3))
			boost_y = random.randrange(3, int(self.ws[1] / 10 - 3))
			if boost_x % 2 != 0:
				boost_x += 1  # If it's odd, then increment by 1.
		
			if boost_y % 2 != 0:
				boost_y += 1
		
			# If the boost overlap the food, then move the boost over.
			if boost_x == food_x and boost_y == food_y:
				boost_x += 20
				if boost_x == self.ws[0] - 30:
					boost_x -= 20

			boost_pos = [boost_x * 10, boost_y * 10]  # Boost actual position.
		

		
		running = True
		# Update loop:
		while running:
			# Return to menu if an exit flag is raised.
			if self.return_menu_flag:
				running = False
				util.fade_out(tuple(self.ws), self.screen)
			
			# If contact with the boost.
			if snake_pos[0] == boost_pos[0] and snake_pos[1] == boost_pos[1]:
				self.visual_fx.clear()
				if boost_available:
					boost_sound.play()
					boost_available = False

			# If the boost is active, then decrease its duration
			if not boost_available:
				boost_duration -= 1

			# Events Handling.
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()
				if event.type == KEYDOWN:
					if event.key == K_ESCAPE or event.key == K_p:
						self.pause_menu()
						# running = False  # Ấn escape sẽ trở về menu
					if event.key == K_d or event.key == K_RIGHT:
						change_to = 'RIGHT'
					if event.key == K_a or event.key == K_LEFT:
						change_to = 'LEFT'
					if event.key == K_w or event.key == K_UP:
						change_to = 'UP'
					if event.key == K_s or event.key == K_DOWN:
						change_to = 'DOWN'
				if event.type == VIDEORESIZE:
					if not self.fllscrn_flag:
						self.screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]

			# Change direction, avoid reversing movement.
			if change_to == 'RIGHT' and direction != 'LEFT':
				direction = 'RIGHT'
			if change_to == 'LEFT' and direction != 'RIGHT':
				direction = 'LEFT'
			if change_to == 'UP' and direction != 'DOWN':
				direction = 'UP'
			if change_to == 'DOWN' and direction != 'UP':
				direction = 'DOWN'

			# Head rotate angle, position number is counter-clockwise, negative number is clockwise.
			# Default direction facing right horizontally.
			angle = 0
			# Update snake position overtime.
			if direction == 'RIGHT':
				snake_pos[0] += self.move_speed
			elif direction == 'LEFT':
				snake_pos[0] -= self.move_speed
				angle = 180
			elif direction == 'UP':
				snake_pos[1] -= self.move_speed
				angle = 90
			elif direction == 'DOWN':
				snake_pos[1] += self.move_speed
				angle = -90

			# Add segment when eating food.
			snake_body.insert(0, list(snake_pos))
			if snake_pos[0] == food_pos[0] and snake_pos[1] == food_pos[1]:
				eating_sound.play()
				
				# If the boost is consumed, then count the number of foods.
				if not boost_available:
					apple_count += 1
				
				# Calculate score based on if the boost's been consumed or not.
				if not boost_available and boost_duration > 0:
					if index == 0:
						score += 5
					elif index == 1:
						score += 1
				else:
					score += 1
				food_available = False
			else:
				snake_body.pop()

			# If the current score is higher than the previous best, then update it.
			if score > self.current_high_score:
				self.current_high_score = score
				self.save_data('user_data/user_config.txt')

			# Regenerate new food if eaten:
			if not food_available:
				food_x = random.randrange(2, int(self.ws[0] / 10 - 3))
				food_y = random.randrange(3, int(self.ws[1] / 10 - 3))
				
				if food_x % 2 != 0:
					food_x += 1
				
				if food_y % 2 != 0:
					food_y += 1
				
				food_pos = [food_x * 10, food_y * 10]
				food_available = True

			# Set new boost position if eaten:
			if not boost_available:
				boost_x = random.randrange(2, int(self.ws[0] / 10 - 3))
				boost_y = random.randrange(3, int(self.ws[1] / 10 - 3))
				
				if boost_x % 2 != 0:
					boost_x += 1
				
				if boost_y % 2 != 0:
					boost_y += 1
				
				if boost_x == food_x and boost_y == food_y:
					boost_x += 20
					if boost_x == self.ws[0] - 30:
						boost_x -= 20
				
				boost_pos = [boost_x * 10, boost_y * 10]

			# Regenerate new boost if eating enough foods.
			if apple_count == 10:
				boost_available = True
				index = random.randint(0, 1)
				
				if index == 0:
					boost_duration = 75
				
				else:
					boost_duration = 113
				apple_count = 0

			# Only draw on screen if running:
			if running:
				self.screen.fill(WHITE)

				# Particles effect if achieving certain scores.
				if score >= 30:
					x = snake_pos[0] + head_img.get_width() / 2
					y = snake_pos[1] + head_img.get_height() / 2
					self.visual_fx.particles_generate(x, y)

				# Draw the body segment.
				for pos in snake_body[1:]:
					self.screen.blit(body_img, (pos[0], pos[1]))

				# Draw the head, applying rotation angle.
				head_img_copy = pygame.transform.rotate(head_img, angle)
				self.screen.blit(head_img_copy, (snake_body[0][0], snake_body[0][1]))
				
				# Draw the food.
				self.screen.blit(food_img, (food_pos[0], food_pos[1]))

				# Draw the corresponding boost.
				if boost_available:
					if index == 0:  # Score boost
						self.visual_fx.shockwaves_generate(boost_pos[0] + boost_img[0].get_width() / 2, boost_pos[1] + boost_img[0].get_height() / 2, auto=True)
						self.screen.blit(boost_img[0], (boost_pos[0], boost_pos[1]))
					else:  # Speed boost
						self.visual_fx.shockwaves_generate(boost_pos[0] + boost_img[1].get_width() / 2, boost_pos[1] + boost_img[1].get_height() / 2, auto=True)
						self.screen.blit(boost_img[1], (boost_pos[0], boost_pos[1]))

				# Draw boost duration bar.
				if not boost_available and boost_duration > 0:
					if index == 0:
						util.draw_text('x5 Score ', self.ws[0] / 20 * 7, 20, 15, self.screen, color=RED)
						duration_bar = pygame.Rect(self.ws[0] / 12 * 5, 18, round(boost_duration * 1.5), 20)
					else:
						util.draw_text('x1.5 Speed ', self.ws[0] / 20 * 7, 20, 15, self.screen, color=RED)
						duration_bar = pygame.Rect(self.ws[0] / 12 * 5, 18, boost_duration, 20)
					pygame.draw.rect(self.screen, RED, duration_bar)

				# Casual Mode:
				if self.game_mode == 0:
					# Draw the border.
					pygame.draw.rect(self.screen, BLACK, (10, 10, self.ws[0] - 20, self.ws[1] - 20), 2)
					
					# X axis collision checking.
					if snake_pos[0] > self.ws[0] - 30 or snake_pos[0] < 20:
						self.game_over(score)
						
						# Restart if needed.
						if self.retry_flag:
							restart_game()
						
						else:
							running = False
							util.fade_out(tuple(self.ws), self.screen)
							break
					
					# Y Axis collision checking.
					if snake_pos[1] > self.ws[1] - 30 or snake_pos[1] < 20:
						self.game_over(score)
					
						if self.retry_flag:
							restart_game()
						
						else:
							running = False;
							util.fade_out(tuple(self.ws), self.screen)
							break
				
				# Borderless Mode
				else:
					# Reset position when running pass the windows border.
					if snake_pos[0] > self.ws[0]:
						snake_pos[0] = -20
					elif snake_pos[0] < 0:
						snake_pos[0] = self.ws[0]
					elif snake_pos[1] > self.ws[1]:
						snake_pos[1] = -20
					elif snake_pos[1] < 0:
						snake_pos[1] = self.ws[1]
			
			# Break if not running.
			else:
				break

			# If the snake eats its own segment.
			for segment in snake_body[1:]:
				if snake_pos[0] == segment[0] and snake_pos[1] == segment[1]:
					self.game_over(score)
					
					# Restart if needed.
					if self.retry_flag:
						restart_game()
					
					else:
						running = False
						util.fade_out(tuple(self.ws), self.screen)
						break

			self.show_score(1, score)
			pygame.display.update()
			if not boost_available and boost_duration > 0:
				if index == 1:
					self.clock.tick(15)
				else:
					self.clock.tick(10)
			else:
				self.clock.tick(10)

	# Main Menu:
	def main_menu(self):
		self.read_data("user_data/user_config.txt")
		print("\nFullscreen: ", self.fllscrn_flag)
		print("Music: ", self.music_flag)
		print("Saved high score: ", self.old_high_score)

		if self.fllscrn_flag:
			self.screen = pygame.display.set_mode(self.monitor_size, FULLSCREEN)
			self.ws = [self.screen.get_width(), self.screen.get_height()]
		else:
			self.screen = pygame.display.set_mode((self.res_w, self.res_h), RESIZABLE)
			self.ws = [self.screen.get_width(), self.screen.get_height()]

		if self.music_flag:
			pygame.mixer.music.play(-1)

		click = False  # Click flag
		alpha = 0  # Alpha value for transparent effect

		while True:
			# Lắp đầy màn hình bằng màu trằng
			self.screen.fill(WHITE)

			# Lấy vị trí của chuột:
			mx, my = pygame.mouse.get_pos()

			# Tiêu đề:
			util.draw_text('SNAK3 CLASSIQUE', self.ws[0] / 2, self.ws[1] / 6, 70, self.screen, bold=True, font_name="calibri")
			util.draw_text('--------------------', self.ws[0] / 2, self.ws[1] / 4, 30, self.screen, bold=True, font_name="calibri")

			# Nút bấm:
			button_1 = pygame.Rect(300, 240, 270, 50)
			util.draw_rect(button_1, self.screen, GREY, self.ws[0] / 2, self.ws[1] / 5 * 2)
			util.draw_text('Casual Mode', self.ws[0] / 2, self.ws[1] / 12 * 5, 30, self.screen)
		
			if button_1.collidepoint((mx, my)):  # Khi dí trỏ chuột vào
				util.draw_rect(button_1, self.screen, MEDIUM_GREY, self.ws[0] / 2, self.ws[1] / 5 * 2)
				util.draw_text('Casual Mode', self.ws[0] / 2, self.ws[1] / 12 * 5, 30, self.screen, color=YELLOW)
				if click:  # Khi bấm chuột vào
					util.fade_out(tuple(self.ws), self.screen)
					self.game_mode = 0
					self.start_game()
					alpha = 255


			button_2 = pygame.Rect(165, 300, 270, 50)
			util.draw_rect(button_2, self.screen, GREY, self.ws[0] / 2, self.ws[1] / 2)
			util.draw_text('Borderless Mode', self.ws[0] / 2, self.ws[1] / 60 * 31, 30, self.screen)
		
			if button_2.collidepoint((mx, my)):
				util.draw_rect(button_2, self.screen, MEDIUM_GREY, self.ws[0] / 2, self.ws[1] / 2)
				util.draw_text('Borderless Mode', self.ws[0] / 2, self.ws[1] / 60 * 31, 30, self.screen, color=YELLOW)
				if click:
					util.fade_out(tuple(self.ws), self.screen)
					self.game_mode = 1
					self.start_game()
					alpha = 255


			button_3 = pygame.Rect(165, 300, 270, 50)
			util.draw_rect(button_3, self.screen, GREY, self.ws[0] / 2, self.ws[1] / 5 * 3)
			util.draw_text('Settings', self.ws[0] / 2, self.ws[1] / 60 * 37, 30, self.screen)
		
			if button_3.collidepoint((mx, my)):  # Khi dí trỏ chuột vào
				util.draw_rect(button_3, self.screen, MEDIUM_GREY, self.ws[0] / 2, self.ws[1] / 5 * 3)
				util.draw_text('Settings', self.ws[0] / 2, self.ws[1] / 60 * 37, 30, self.screen, color=YELLOW)
				if click:  # Khi bấm chuột vào
					util.fade_out(tuple(self.ws), self.screen)
					self.show_settings()
					alpha = 255


			button_4 = pygame.Rect(165, 300, 270, 50)
			util.draw_rect(button_4, self.screen, GREY, self.ws[0] / 2, self.ws[1] / 10 * 7)
			util.draw_text('Quit', self.ws[0] / 2, self.ws[1] / 60 * 43, 30, self.screen)
		
			if button_4.collidepoint((mx, my)):  # Khi dí trỏ chuột vào
				util.draw_rect(button_4, self.screen, MEDIUM_GREY, self.ws[0] / 2, self.ws[1] / 10 * 7)
				util.draw_text('Quit', self.ws[0] / 2, self.ws[1] / 60 * 43, 30, self.screen, color=YELLOW)
				if click:  # Khi bấm chuột vào
					pygame.quit()
					sys.exit()


			util.draw_text('© 2022 Constance, v1.2', self.ws[0] / 2, self.ws[1] - 15, 15, self.screen)

			self.visual_fx.shockwaves_generate(mx, my, click_flag=click)

			if alpha > 0:
				if alpha == 255:
					fade_in = pygame.Surface(tuple(self.ws))
					fade_in.fill(WHITE)
					self.visual_fx.clear()  # Reset the shockwaves list

				fade_in.set_alpha(alpha)
				self.screen.blit(fade_in, (0, 0))
				alpha -= 15

			click = False
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()
				if event.type == MOUSEBUTTONDOWN:
					if event.button == 1:  # Khi bấm chuột trái
						click = True
				if event.type == VIDEORESIZE:
					if not self.fllscrn_flag:
						self.screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]

			pygame.display.update()
			self.clock.tick(self.framerate)

	#Hàm settings:
	def show_settings(self):
		running = True
		click = False

		alpha = 255
		while running:
			self.screen.fill(WHITE)

			mx ,my = pygame.mouse.get_pos()

			util.draw_text('SETTINGS', self.ws[0]/2, self.ws[1]/6, 70, self.screen, bold=True, font_name="calibri")

			button_1 = pygame.Rect(200,340,200,50)
			util.draw_rect(button_1, self.screen, GREY, self.ws[0]/2, self.ws[1]/5*2)
			util.draw_text('Resolution', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen)
			if button_1.collidepoint((mx,my)):
				util.draw_rect(button_1, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/5*2)
				util.draw_text('Resolution', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen, color=YELLOW)
				if click:
					util.fade_out(tuple(self.ws), self.screen)
					self.show_resolution()
					alpha = 255


			button_2 = pygame.Rect(200,340,200,50)
			util.draw_rect(button_2, self.screen, GREY, self.ws[0]/2, self.ws[1]/2)
			util.draw_text('Controls', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen)
			if button_2.collidepoint((mx,my)):
				util.draw_rect(button_2, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/2)
				util.draw_text('Controls', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen, color=YELLOW)
				if click:
					util.fade_out(tuple(self.ws), self.screen)
					self.show_controls()
					alpha = 255


			button_3 = pygame.Rect(200,340,200,50)
			util.draw_rect(button_3, self.screen, GREY, self.ws[0]/2, self.ws[1]/5*3)
			if self.music_flag:
				util.draw_text('Music:[ON]', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen)
			else:
				util.draw_text('Music:[OFF]', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen)
			if button_3.collidepoint((mx,my)):
				if self.music_flag:
					util.draw_rect(button_3, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/5*3)
					util.draw_text('Music:[ON]', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen, color=YELLOW)
				else:
					util.draw_rect(button_3, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/5*3)
					util.draw_text('Music:[OFF]', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen, color=YELLOW)
				if click:
					self.music_flag = not self.music_flag
					self.save_data('user_data/user_config.txt')
					if self.music_flag:
						pygame.mixer.music.play(-1)
					else:
						pygame.mixer.music.stop()


			button_4 = pygame.Rect(200,400,200,50)
			util.draw_rect(button_4, self.screen, GREY, self.ws[0]/2, self.ws[1]/10*7)
			util.draw_text('Back', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen)
			if button_4.collidepoint((mx,my)):
				util.draw_rect(button_4, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/10*7)
				util.draw_text('Back', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen, color=YELLOW)
				if click:
					running = False
					util.fade_out(tuple(self.ws), self.screen)
					break

			util.draw_text('© 2022 Constance, v1.2', self.ws[0]/2, self.ws[1]-15, 15, self.screen)

			self.visual_fx.shockwaves_generate(mx, my, click_flag=click)
		
			if alpha > 0:
				if alpha == 255:
					fade_in = pygame.Surface(tuple(self.ws))
					fade_in.fill(WHITE)
					self.visual_fx.clear()

				fade_in.set_alpha(alpha)
				self.screen.blit(fade_in, (0,0))
				alpha -= 15

			click = False
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()
				if event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						running = False
						util.fade_out(tuple(self.ws), self.screen)
				if event.type == MOUSEBUTTONDOWN:
					if event.button == 1:
						click = True
				if event.type == VIDEORESIZE:
					if not self.fllscrn_flag:
						self.screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]
		
			pygame.display.update()
			self.clock.tick(self.framerate)
		
		return self.screen, self.ws

	#Hàm submenu controls:
	def show_controls(self):
		running = True 
		click = False
		alpha = 255

		while running:
			self.screen.fill(WHITE)
			mx, my = pygame.mouse.get_pos()

			util.draw_text('CONTROLS', self.ws[0]/2, self.ws[1]/6, 70, self.screen, bold=True, font_name="calibri")

			util.draw_text('W: Up', self.ws[0]/2, self.ws[1]/60*17, 30, self.screen)
			util.draw_text('S: Down', self.ws[0]/2, self.ws[1]/20*7, 30, self.screen)
			util.draw_text('A: Left', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen)
			util.draw_text('D: Right', self.ws[0]/2, self.ws[1]/60*29, 30, self.screen)
			util.draw_text('ESC: Pause Game', self.ws[0]/2, self.ws[1]/20*11, 30, self.screen)

		
			button_1 = pygame.Rect(200,400,100,50)
			util.draw_rect(button_1, self.screen, GREY, self.ws[0]/2, self.ws[1]/10*7)
			util.draw_text('Back', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen)
			if button_1.collidepoint((mx,my)):
				util.draw_rect(button_1, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/10*7)
				util.draw_text('Back', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen, color=YELLOW)
				if click:
					running = False
					util.fade_out(tuple(self.ws), self.screen)
					break

			util.draw_text('© 2022 Constance, v1.2', self.ws[0]/2, self.ws[1]-15, 15, self.screen)

			self.visual_fx.shockwaves_generate(mx, my, click_flag=click)

			if alpha > 0:
				if alpha == 255:
					fade_in = pygame.Surface(tuple(self.ws))
					fade_in.fill(WHITE)
					self.visual_fx.clear()

				fade_in.set_alpha(alpha)
				self.screen.blit(fade_in, (0,0))
				alpha -= 15

			click = False
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()
				if event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						running = False
						util.fade_out(tuple(self.ws), self.screen)
				if event.type == MOUSEBUTTONDOWN:
					if event.button == 1:
						click = True
				if event.type == VIDEORESIZE:
					if not self.fllscrn_flag:
						self.screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]

			pygame.display.update()
			self.clock.tick(self.framerate)

	#Hàm submenu resolution
	def show_resolution(self):
		running = True 
		click = False
		alpha = 255

		while running:
			self.screen.fill(WHITE)
			mx,my = pygame.mouse.get_pos()

			util.draw_text('RESOLUTION', self.ws[0]/2, self.ws[1]/6, 70, self.screen, bold=True, font_name="calibri")

			if not self.fllscrn_flag:
				button_1 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_1, self.screen, GREY, self.ws[0]/2, self.ws[1]/10*3)
				
				if self.res_w == 800 and self.res_h == 600:
					util.draw_rect(button_1, self.screen, YELLOW, self.ws[0]/2, self.ws[1]/10*3)
					util.draw_text('800 x 600', self.ws[0]/2, self.ws[1]/60*19, 30, self.screen)
				
				else:
					util.draw_text('800 x 600', self.ws[0]/2, self.ws[1]/60*19, 30, self.screen)
				
				if button_1.collidepoint((mx,my)):					
					if self.res_w != 800 and self.res_h != 600:
						util.draw_rect(button_1, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/10*3)
						util.draw_text('800 x 600', self.ws[0]/2, self.ws[1]/60*19, 30, self.screen, color=YELLOW)
					
					if click:
						self.res_w = 800
						self.res_h = 600
						self.screen = pygame.display.set_mode((self.res_w, self.res_h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]
						self.save_data('user_data/user_config.txt')

			
				button_2 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_2, self.screen, GREY, self.ws[0]/2, self.ws[1]/5*2)
				
				if self.res_w == 1152 and self.res_h == 864:
					util.draw_rect(button_2, self.screen, YELLOW, self.ws[0]/2, self.ws[1]/5*2)
					util.draw_text('1152 x 864', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen)
				
				else:
					util.draw_text('1152 x 864', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen)
				
				if button_2.collidepoint((mx,my)):
					if self.res_w != 1152 and self.res_h != 864:
						util.draw_rect(button_2, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/5*2)
						util.draw_text('1152 x 864', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen, color=YELLOW)
					
					if click:
						self.res_w = 1152
						self.res_h = 864
						self.screen = pygame.display.set_mode((self.res_w, self.res_h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]
						self.save_data('user_data/user_config.txt')


				button_3 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_3, self.screen, GREY, self.ws[0]/2, self.ws[1]/2)
				
				if self.res_w == 1366 and self.res_h == 768:
					util.draw_rect(button_3, self.screen, YELLOW, self.ws[0]/2, self.ws[1]/2)
					util.draw_text('1366 x 768', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen)
				
				else:
					util.draw_text('1366 x 768', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen)
				
				if button_3.collidepoint((mx,my)):
					if self.res_w != 1366 and self.res_h != 768:
						util.draw_rect(button_3, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/2)
						util.draw_text('1366 x 768', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen, color=YELLOW)
					
					if click:
						self.res_w = 1366
						self.res_h = 768
						self.screen = pygame.display.set_mode((self.res_w, self.res_h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]
						self.save_data('user_data/user_config.txt')


				button_4 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_4, self.screen, GREY, self.ws[0]/2, self.ws[1]/5*3)
				
				if self.res_w == 1600 and self.res_h == 900:
					util.draw_rect(button_4, self.screen, YELLOW, self.ws[0]/2, self.ws[1]/5*3)
					util.draw_text('1600 x 900', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen)
				
				else:
					util.draw_text('1600 x 900', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen)
				
				if button_4.collidepoint((mx,my)):
					if self.res_w != 1600 and self.res_h != 900:
						util.draw_rect(button_4, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/5*3)
						util.draw_text('1600 x 900', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen, color=YELLOW)
					
					if click:
						self.res_w = 1600
						self.res_h = 900
						self.screen = pygame.display.set_mode((self.res_w, self.res_h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]
						self.save_data('user_data/user_config.txt')

		
			else:
				button_1 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_1, self.screen, LIGHT_GREY, self.ws[0]/2, self.ws[1]/10*3)
				util.draw_text('800 x 600', self.ws[0]/2, self.ws[1]/60*19, 30, self.screen, color=GREY)

				button_2 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_2, self.screen, LIGHT_GREY, self.ws[0]/2, self.ws[1]/5*2)
				util.draw_text('1152 x 864', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen, color=GREY)

				button_3 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_3, self.screen, LIGHT_GREY, self.ws[0]/2, self.ws[1]/2)
				util.draw_text('1366 x 768', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen, color=GREY)

				button_4 = pygame.Rect(200,340,200,50)
				util.draw_rect(button_4, self.screen, LIGHT_GREY, self.ws[0]/2, self.ws[1]/5*3)
				util.draw_text('1600 x 900', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen, color=GREY)


			button_5 = pygame.Rect(200,340,200,50)
			util.draw_rect(button_5, self.screen, GREY, self.ws[0]/2, self.ws[1]/10*7)
			
			if self.fllscrn_flag:
				util.draw_rect(button_5, self.screen, YELLOW, self.ws[0]/2, self.ws[1]/10*7)
				util.draw_text('Fullsreen', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen)

			else:
				util.draw_text('Fullsreen', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen)

			if button_5.collidepoint((mx,my)):
				if self.fllscrn_flag:
					util.draw_rect(button_5, self.screen, BLACK, self.ws[0]/2, self.ws[1]/10*7)
					util.draw_text('Fullsreen', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen, color=YELLOW)

				else:
					util.draw_rect(button_5, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/10*7)
					util.draw_text('Fullsreen', self.ws[0]/2, self.ws[1]/60*43, 30, self.screen, color=YELLOW)

				if click:
					self.fllscrn_flag = not self.fllscrn_flag
				
					if self.fllscrn_flag:
						self.screen = pygame.display.set_mode(self.monitor_size, FULLSCREEN)
						self.ws = [self.screen.get_width(), self.screen.get_height()]

					else:
						self.screen = pygame.display.set_mode((self.res_w, self.res_h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]
				
					self.save_data('user_data/user_config.txt')


			button_6 = pygame.Rect(200,400,200,50)
			util.draw_rect(button_6, self.screen, GREY, self.ws[0]/2, self.ws[1]/5*4)
			util.draw_text('Back', self.ws[0]/2, self.ws[1]/60*49, 30, self.screen)

			if button_6.collidepoint((mx,my)):
				util.draw_rect(button_6, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/5*4)
				util.draw_text('Back', self.ws[0]/2, self.ws[1]/60*49, 30, self.screen, color=YELLOW)

				if click:
					running = False
					util.fade_out(tuple(self.ws), self.screen)
					break

			util.draw_text('© 2022 Constance, v1.2', self.ws[0]/2, self.ws[1]-15, 15, self.screen)

			self.visual_fx.shockwaves_generate(mx, my, click_flag=click)

			if alpha > 0:
				if alpha == 255:
					fade_in = pygame.Surface(tuple(self.ws))
					fade_in.fill(WHITE)
					self.visual_fx.clear()

				fade_in.set_alpha(alpha)
				self.screen.blit(fade_in, (0,0))
				alpha -= 15

			click = False
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()
				if event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						running = False
						util.fade_out(tuple(self.ws), self.screen)
				if event.type == MOUSEBUTTONDOWN:
					if event.button == 1:
						click = True
				if event.type == VIDEORESIZE:
					if not self.fllscrn_flag:
						self.screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]

			pygame.display.update()
			self.clock.tick(self.framerate)

	#Hàm pause game:
	def pause_menu(self):
		running = True
		click = False
		self.return_menu_flag = False

		surf = pygame.Surface(tuple(self.ws))
		surf.fill(GREY)
		surf.set_alpha(150)
		self.screen.blit(surf, (0,0))
		while running:
			mx, my = pygame.mouse.get_pos()

			util.draw_text('PAUSED', self.ws[0]/2, self.ws[1]/10*3, 70, self.screen, color=RED, bold=True, font_name="calibri")

			button_1 = pygame.Rect(0,0,250,50)
			util.draw_rect(button_1, self.screen, GREY, self.ws[0]/2, self.ws[1]/2)
			util.draw_text('Resume', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen)
			if button_1.collidepoint((mx,my)):
				util.draw_rect(button_1, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/2)
				util.draw_text('Resume', self.ws[0]/2, self.ws[1]/60*31, 30, self.screen, color=YELLOW)
				if click:
					running = False


			button_2 = pygame.Rect(0,0,250,50)
			util.draw_rect(button_2, self.screen, GREY, self.ws[0]/2, self.ws[1]/5*3)
			util.draw_text('Return to Menu', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen)
			if button_2.collidepoint((mx, my)):
				util.draw_rect(button_2, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/5*3)
				util.draw_text('Return to Menu', self.ws[0]/2, self.ws[1]/60*37, 30, self.screen, color=YELLOW)
				if click:
					self.return_menu_flag = True
					running = False

			click = False
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()

				# Unpause.
				if event.type == KEYDOWN:
					if event.key == K_ESCAPE or event.key == K_p:
						running = False
				
				if event.type == MOUSEBUTTONDOWN:
					if event.button == 1:
						click = True
				
				if event.type == VIDEORESIZE:
					if not self.fllscrn_flag:
						self.screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]
						surf = pygame.Surface(tuple(self.ws))
						surf.fill(GREY)
						surf.set_alpha(150)
						self.screen.blit(surf, (0,0))

			pygame.display.update()
			self.clock.tick(self.framerate)

	#Hàm game over:
	def game_over(self, score):
		running = True
		click = False
		self.return_menu_flag = self.retry_flag = False
		self.visual_fx.clear()
		game_over_sound.play()

		while running:
		
			mx, my = pygame.mouse.get_pos()

			self.screen.fill(WHITE)
			util.draw_text('GAME OVER', self.ws[0]/2, self.ws[1]/6, 70, self.screen, color=RED, bold=True, font_name="calibri")
			self.show_score(0, score) #Hiển thị điểm

			button_1 = pygame.Rect(0,0,250,50)
			util.draw_rect(button_1, self.screen, GREY, self.ws[0]/2, self.ws[1]/3*2)
			util.draw_text('Retry', self.ws[0]/2, self.ws[1]/60*41, 30, self.screen)
			if button_1.collidepoint((mx,my)):
				util.draw_rect(button_1, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/3*2)
				util.draw_text('Retry', self.ws[0]/2, self.ws[1]/60*41, 30, self.screen, color=YELLOW)
				if click:
					self.retry_flag = True
					running = False


			button_2 = pygame.Rect(0,0,250,50)
			util.draw_rect(button_2, self.screen, GREY, self.ws[0]/2, self.ws[1]/30*23)
			util.draw_text('Return to Menu', self.ws[0]/2, self.ws[1]/60*47, 30, self.screen)
			if button_2.collidepoint((mx, my)):
				util.draw_rect(button_2, self.screen, MEDIUM_GREY, self.ws[0]/2, self.ws[1]/30*23)
				util.draw_text('Return to Menu', self.ws[0]/2, self.ws[1]/60*47, 30, self.screen, color=YELLOW)
				if click:
					self.return_menu_flag = True
					running = False

			self.visual_fx.shockwaves_generate(mx, my, click_flag=click)

			click = False
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()
				if event.type == MOUSEBUTTONDOWN:
					if event.button == 1:
						click = True
				if event.type == VIDEORESIZE:
					if not self.fllscrn_flag:
						self.screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
						self.ws = [self.screen.get_width(), self.screen.get_height()]

			pygame.display.update()
			self.clock.tick(self.framerate)


	# Show score:
	def show_score(self, choice, score):
		# In game.
		if choice == 1:
			util.draw_text(f'Score: {score}', 70, 20, 15, self.screen)
			if score > self.old_high_score:
				util.draw_text(f'New High Score: {self.current_high_score}', self.ws[0]-100, 20, 15, self.screen, color=RED)
			else:
				util.draw_text(f'High Score: {self.current_high_score}', self.ws[0]-100, 20, 15, self.screen)
		
		# In game over screen.
		else:
			if score > self.old_high_score:
				text_rect = util.draw_text(f'New High Score: {self.current_high_score}', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen, color=RED)
				self.visual_fx.particles_generate(text_rect.midleft[0], text_rect.midleft[1])
				self.visual_fx.particles_generate(text_rect.midright[0], text_rect.midright[1])
			else:
				util.draw_text(f'High Score: {self.current_high_score}', self.ws[0]/2, self.ws[1]/12*5, 30, self.screen)
			util.draw_text(f'Current Score: {score}', self.ws[0]/2, self.ws[1]/100*48, 23, self.screen)