#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-


import random, os.path

#import basic pygame modules
import pygame
from pygame.locals import *

#see if we can load more than standard BMP
if not pygame.image.get_extended():
    raise SystemExit, "Sorry, extended image module required"


#game constants
MAX_SHOTS      = 2      #most player bullets onscreen
ALIEN_ODDS     = 10     #chances a new alien appears
BOMB_ODDS      = 20    #chances a new bomb will drop
ALIEN_RELOAD   = 12     #frames between new aliens
SCREENRECT     = Rect(0, 0, 640, 480)
SCORE          = 0


def load_image(file):
    "loads an image, prepares it for play"
    file = os.path.join('data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit, 'Could not load image "%s" %s'%(file, pygame.get_error())
    return surface.convert()	

def load_images(*files):
    imgs = []
    for file in files:
        imgs.append(load_image(file))
    return imgs


class dummysound:
    def play(self): pass

def load_sound(file):
    if not pygame.mixer: return dummysound()
    file = os.path.join('data', file)
    try:
        sound = pygame.mixer.Sound(file)
        return sound
    except pygame.error:
        print 'Warning, unable to load,', file
    return dummysound()



# each type of game object gets an init and an
# update function. the update function is called
# once per frame, and it is when each object should
# change it's current position and state. the Player
# object actually gets a "move" function instead of
# update, since it is passed extra information about
# the keyboard


class Player(pygame.sprite.Sprite):
	speed = 10
	bounce = 24
	gun_offset = -11
	images = []
	def __init__(self):
		pygame.sprite.Sprite.__init__(self, self.containers)
		self.image = self.images[0]
		self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
		self.reloading = 0
		self.origtop = self.rect.top
		self.facing = -1

	def move(self, direction):
		if direction: self.facing = direction
		self.rect.move_ip(direction*self.speed, 0)
		self.rect = self.rect.clamp(SCREENRECT)
		if self.reloading:
			if self.facing < 0:
				self.image = self.images[2]
			elif self.facing > 0:
				self.image = self.images[3]
		else:
			if self.facing < 0:
				self.image = self.images[0]
			elif self.facing > 0:
				self.image = self.images[1]
		self.rect.top = self.origtop - (self.rect.left/self.bounce%2)

	def gunpos(self):
		pos = self.facing*self.gun_offset + self.rect.centerx
		return pos, self.rect.top

	def shoot(self):
		if self.facing < 0:
			self.image = self.images[2]
		elif self.facing > 0:
			self.image = self.images[3]
	
	def update(self):
		if self.reloading:
			if self.facing < 0:
				self.image = self.images[2]
			elif self.facing > 0:
				self.image = self.images[3]
		else:
			if self.facing < 0:
				self.image = self.images[0]
			elif self.facing > 0:
				self.image = self.images[1]
		
class Alien(pygame.sprite.Sprite):
    speed = 13
    animcycle = 12
    images = []
    direction = 1
    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.facing = random.choice((-1,1)) * Alien.speed
        self.frame = 0
        if self.facing < 0:
            self.rect.right = SCREENRECT.right

    def update(self):
        self.rect.move_ip(self.facing, 0)
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing;
            self.rect.top = self.rect.bottom + 1
            self.rect = self.rect.clamp(SCREENRECT)
        self.frame = self.frame + 1
        if self.facing < 0:
        	if self.direction:
        		self.image = pygame.transform.flip(self.image, 1, 0)
        		self.direction = 0
        if self.facing > 0:
        	if not self.direction:
        		self.image = pygame.transform.flip(self.image, 1, 0)
        		self.direction = 1


class Explosion(pygame.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife

    def update(self):
        self.life = self.life - 1
        self.image = self.images[self.life/self.animcycle%2]
        if self.life <= 0: self.kill()


class Shot(pygame.sprite.Sprite):
    speed = -11
    images = []
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top <= 0:
            self.kill()


class Bomb(pygame.sprite.Sprite):
    speed = 9
    images = []
    def __init__(self, alien):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=
                    alien.rect.move(0,5).midbottom)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom >= 470:
            Explosion(self)
            self.kill()


class Score(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 20)
        self.font.set_underline(1)
        self.color = Color('white')
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self):
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = "Score: %d" % SCORE
            if SCORE > current_highscore:
                self.color = Color('red')
            self.image = self.font.render(msg, 0, self.color)

def main(winstyle = 0):
    # Initialize pygame
    pygame.init()
    if pygame.mixer and not pygame.mixer.get_init():
        print 'Warning, no sound'
        pygame.mixer = None

    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    global current_highscore
    if os.path.isfile("highscore.txt"):
        fil = open("highscore.txt", 'r+')
        current_highscore = fil.readline()
        if current_highscore[-2:] == '\n':
            current_highscore = int(current_highscore[:-2])
        else:
            current_highscore = int(current_highscore)

        fil.close()
    else:
        current_highscore = 0


    #Load images, assign to sprite classes
    #(do this before the classes are used, after screen setup)
    img = load_image('bubba.gif')
    img2 = load_image('bubba_shoot.gif')
    Player.images = [img, pygame.transform.flip(img, 1, 0), img2, pygame.transform.flip(img2, 1, 0)]
    img = load_image('explosion1.gif')
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]
    Alien.images = load_images('brady.gif')
    Bomb.images = [load_image('football.gif')]
    Shot.images = [load_image('laser_shot.gif')]

    #decorate the game window
    icon = pygame.transform.scale(pygame.transform.flip(Player.images[0], 1, 0), (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Bubbaspillet')
    pygame.mouse.set_visible(0)

    #create the background, tile the bgd image
    bgdtile = load_image('background.bmp')
    background = pygame.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    #load the sound effects
    boom_sound = load_sound('boom.wav')
    shoot_sound = load_sound('car_door.wav')
    if pygame.mixer:
        music = os.path.join('data', 'house_lo.wav')
        pygame.mixer.music.load(music)
        pygame.mixer.music.play(-1)

    # Initialize Game Groups
    aliens = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    all = pygame.sprite.RenderUpdates()
    lastalien = pygame.sprite.GroupSingle()

    #assign default groups to each sprite class
    Player.containers = all
    Alien.containers = aliens, all, lastalien
    Shot.containers = shots, all
    Bomb.containers = bombs, all
    Explosion.containers = all
    Score.containers = all

    #Create Some Starting Values
    global score
    alienreload = ALIEN_RELOAD
    kills = 0
    clock = pygame.time.Clock()
    global keypresses 
    keypresses = 0
    global total_shots
    total_shots = 0

    #initialize our starting sprites
    global SCORE
    player = Player()
    Alien() #note, this 'lives' because it goes into a sprite group
    if pygame.font:
        all.add(Score())

    while player.alive():

        #get input
        for event in pygame.event.get():
            if event.type == QUIT or \
                (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return "quit"
        keystate = pygame.key.get_pressed()

        # clear/erase the last drawn sprites
        all.clear(screen, background)

        #update all the sprites
        all.update()

        #handle player input
        direction = keystate[K_RIGHT] - keystate[K_LEFT]
        player.move(direction)
        firing = keystate[K_SPACE] or keystate[K_UP]
        if firing:
        	keypresses += 1
        if not player.reloading and firing and len(shots) < MAX_SHOTS:
            Shot(player.gunpos())
            shoot_sound.play()
            total_shots+= 1
            player.shoot()
        player.reloading = firing

        # Create new alien
        if alienreload:
            alienreload = alienreload - 1
        elif not int(random.random() * ALIEN_ODDS):
            Alien()
            alienreload = ALIEN_RELOAD

        # Drop bombs
        if lastalien and not int(random.random() * BOMB_ODDS):
            Bomb(lastalien.sprite)

        # Detect collisions
        for alien in pygame.sprite.spritecollide(player, aliens, 1):
            boom_sound.play()
            Explosion(alien)
            Explosion(player)
            SCORE = SCORE + 1
            player.kill()

        for alien in pygame.sprite.groupcollide(shots, aliens, 1, 1).keys():
            boom_sound.play()
            Explosion(alien)
            SCORE = SCORE + 1

        for bomb in pygame.sprite.spritecollide(player, bombs, 1):
            boom_sound.play()
            Explosion(player)
            Explosion(bomb)
            player.kill()

        #draw the scene
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        #cap the framerate
        clock.tick(40)

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)
    pygame.time.wait(1000)
	

#call the "main" function if running this script
if __name__ == '__main__': 
	foobar = 1	
	while foobar:
		feedback = main()
		print "Nyt spil:"
		print "Antal dræbte Brady'er: " + str(SCORE)
		print "Antal tastetryk: " + str(keypresses)
		print "Antal skud: " + str(total_shots)
		print "Præcisionen: " + str(100.*SCORE/total_shots)

                if int(current_highscore)<SCORE:
                        fil = open("highscore.txt", 'w')
                        fil.write(str(SCORE))
                        fil.close()
                        print "Du har sl�et rekorden! Den var p� " + str(current_highscore) + " og du fik: " + str(SCORE)


		if feedback != "quit":
			key = 0	
			while not key:
				for event in pygame.event.get():
					if event.type == KEYDOWN and event.key == K_RETURN:
						key = 1
					elif event.type == KEYDOWN and event.key == K_ESCAPE:
						foobar = 0
						key = 1
		else:
			foobar = 0
		SCORE = 0
                print
