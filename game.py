import math
import random
import sys
# External
import pygame
import pygame_menu
# Local
import vars

pygame.init()

size = (1280, 720)
bg = 0, 0, 0

pygame.display.set_caption("Game.")

icon = pygame.image.load("assets/guy/lookRight2.png")

pygame.display.set_icon(icon)

screen = pygame.display.set_mode(size)

frameN = 1

def bind(value,upper,lower):
    if value > upper:
        return upper, True
    if value < lower:
        return lower, True
    return value, False

class Terrain:
    def __init__(self,image,pos=[0,0],assetPath="assets/terrain/",scale=4,animation=[],weight=90):
        self.image = pygame.image.load(assetPath+image)
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image,(self.rect.width*scale,self.rect.height*scale))
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.weight = weight
        if animation:
            self.animation = [pygame.transform.scale(pygame.image.load(assetPath+im),(self.rect.width,self.rect.height)) for im in animation]
        else:
            self.animation = None
        self.animationFrame = 0
        self.animationFrames = 0
        terrains.append(self)

    def __lt__(self,other):
        return self.weight < other.weight

    def do_animation(self):
        if self.animationFrames % 10 == 0:
            self.image = self.images[self.animation[self.animationFrame]]
            self.animationFrame += 1
        self.animationFrames += 1
        if self.animationFrame >= len(self.animation):
            self.animationFrame = 0
            self.animationFrames = 1


class Sprite:
    def __init__(
        self,image,pos=[0,0],assetPath="assets/",scale=4,
        acceleration=0.25,update=None,
        spriteType="motion",extraImages={},
        extraArgs={"dead":False,"player":False,"tangable":True,"killable":False},animations=[],
        weight=0
        ):
        self.image = pygame.image.load(assetPath+image) # Image & Rect
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image,(self.rect.width*scale,self.rect.height*scale))
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.speed = [0,0] # Speed
        self.fSpeed = 0
        if spriteType == "motion":
            self.acceleration = acceleration
            self.startup = 1
        self.sprite_update = update # Sprite
        self.direction = random.randint(0,3)
        self.projected_direction = self.direction
        self.type = spriteType
        self.images = {} # Animations
        self.animations = animations
        self.set_animation("reset")
        self.aliveFrames = 0
        self.extraArgs = extraArgs # Args
        if extraImages:
            self.images["idle"] = self.image
            for im in extraImages:
                if im != "idle":
                    self.images[im] = pygame.transform.scale(pygame.image.load(assetPath+extraImages[im]),(self.rect.width,self.rect.height))
        self.weight = weight
        sprites.append(self)

    def __lt__(self,other):
        return self.weight < other.weight

    def update(self,tick):
        global frameN
        self.aliveFrames += 1
        if not (self.extraArgs["dead"] and self.extraArgs["player"]):
            if self.sprite_update:
                self.sprite_update(self,tick)
            if self.type == "motion":
                accel = self.acceleration*tick
                if self.fSpeed:
                    if self.direction == 0: #up
                        self.speed[1] = round((self.speed[1] - accel/self.startup) if (self.speed[1]>self.fSpeed*-1) else self.fSpeed*-1,2)
                    elif self.direction == 1: #right
                        self.speed[0] = round((self.speed[0] + accel/self.startup) if (self.speed[0]<self.fSpeed) else self.fSpeed,2)
                    elif self.direction == 2: #down
                        self.speed[1] = round((self.speed[1] + accel/self.startup) if (self.speed[1]<self.fSpeed) else self.fSpeed,2)
                    elif self.direction == 3: #left
                        self.speed[0] = round((self.speed[0] - accel/self.startup) if (self.speed[0]>self.fSpeed*-1) else self.fSpeed*-1,2)
                self.rect = self.rect.move(self.speed)
                if self.extraArgs["tangable"]:
                    binds = []
                    self.rect.top,binded = bind(self.rect.top,size[1],0)
                    binds.append(binded)
                    self.rect.left,binded = bind(self.rect.left,size[0],0)
                    binds.append(binded)
                    self.rect.bottom,binded = bind(self.rect.bottom,size[1],0)
                    binds.append(binded)
                    self.rect.right,binded = bind(self.rect.right,size[0],0)
                    binds.append(binded)
                    binds = self.check_collisions(binds)
                    if any(binds):
                        self.speed = [0,0]
                        self.fSpeed = 0
                        if not self.animation:
                            self.set_animation("collide")
                    self.startup -= 0.5 if self.startup > 1 else 0
        if self.animation:
            self.do_animations()

    def check_collisions(self,binds):
        spritesNoMe = [sprite for sprite in sprites if sprite != self]
        rects = [sprite.rect for sprite in spritesNoMe if sprite.extraArgs["tangable"]]
        collides = self.rect.collidelistall(rects)
        if collides:
            for collision in collides:
                try:
                    if spritesNoMe[collision].extraArgs["kill"] and self.extraArgs["killable"]:
                        self.kill()
                except KeyError:
                    pass
                try:
                    if self.extraArgs["kill"] and spritesNoMe[collision].extraArgs["killable"]:
                        spritesNoMe[collision].kill(0)
                except KeyError:
                    pass
                binds.append(True)
                if self.direction == 0: #up
                    self.rect.top = spritesNoMe[collision].rect.bottom
                elif self.direction == 1: #right
                    self.rect.right = spritesNoMe[collision].rect.left
                elif self.direction == 2: #down
                    self.rect.bottom = spritesNoMe[collision].rect.top
                elif self.direction == 3: #left
                    self.rect.left = spritesNoMe[collision].rect.right
                spritesNoMe[collision].startup = 30
        rects = [terrain.rect for terrain in terrains]
        collides = self.rect.collidelistall(rects)
        for collision in collides:
            binds.append(True)
            if self.direction == 0: #up
                self.rect.top = terrains[collision].rect.bottom
            elif self.direction == 1: #right
                self.rect.right = terrains[collision].rect.left
            elif self.direction == 2: #down
                self.rect.bottom = terrains[collision].rect.top
            elif self.direction == 3: #left
                self.rect.left = terrains[collision].rect.right
        return binds


    def do_animations(self):
        if self.animationFrame >= len(self.animation):
            if self.extraArgs["dead"] and self.extraArgs["player"]:
                reset()
            self.animation = []
            self.animationFrame = 0
        else:
            if self.animationFrames % self.animationTime == 0:
                self.image = self.images[self.animation[self.animationFrame]]
                self.animationFrame += 1
            self.animationFrames += 1

    def set_animation(self,anim,args=None):
        if anim in self.animations:
            args = str(args)
            if args:
                self.animation = [frame.format(args) for frame in self.animations[anim]]
            else:
                self.animation = self.animations[anim]

        else:
            if anim != "reset":
                print(f"uuhh, animation '{anim}' asked for but not found (issue???)")
            self.animation = []
        self.animationFrame = 0
        self.animationFrames = 0
        self.animationTime = 10

    def kill(self):
        if not self.extraArgs["dead"]:
            self.extraArgs["dead"] = True
            self.set_animation("death")

def player_update(sprite,tick):
    player = sprite.extraArgs["player"]-1
    if keyboard[player]["up"]:
        sprite.projected_direction = 0
    elif keyboard[player]["down"]:
        sprite.projected_direction = 2
    elif keyboard[player]["left"]:
        sprite.projected_direction = 3
    elif keyboard[player]["right"]:
        sprite.projected_direction = 1
    if not sprite.fSpeed:
        if sprite.direction != sprite.projected_direction:
            sprite.direction = sprite.projected_direction
            sprite.set_animation("look",sprite.direction)
        if keyboard[player]["action"]:
            movedRect = sprite.rect.move([1 if sprite.direction == 1 else -1 if sprite.direction == 3 else 0,1 if sprite.direction == 2 else -1 if sprite.direction == 0 else 0])
            rects = [s.rect for s in sprites if s != sprite] + [t.rect for t in terrains    ]
            collides = movedRect.collidelistall(rects)
            if (screen.get_rect().contains(movedRect)) and not collides:
                sprite.fSpeed = 40
                sprite.startup = 15
                sprite.set_animation("go",sprite.direction)
            else:
                sprite.image = sprite.images["idle"]
    if keyboard[player]["pause"]:
        pause()

def start():
    reset()
    while 1:
        if pauseMenu.is_enabled():
            pauseMenu.update(pygame.event.get())
        if pauseMenu.is_enabled():
            pauseMenu.draw(screen)
        else:
            tick = pygame.time.Clock().tick(120)
            update(tick)
        pygame.display.flip()

def pause():
    pygame.mouse.set_visible(True)
    keyboard[0]["pause"] = False
    pauseMenu.get_current().enable()

def unpause():
    pygame.mouse.set_visible(False)
    pauseMenu.get_current().full_reset()
    pauseMenu.get_current().disable()

def reset():
    global terrains, sprites, keyboard

    terrains = []

    sprites = []

    pygame.mouse.set_visible(False)

    Sprite("idle.png",assetPath="assets/guy/",update=player_update,extraImages=vars.images.player,animations=vars.animations.player,weight=100,extraArgs={"player":1,"dead":False,"tangable":True,"killable":True})

    Sprite("idle.png",assetPath="assets/guy2/",pos=[0,200],extraArgs={"player":None,"dead":False,"tangable":True,"killable":False,"kill":True})

    # Sprite("idle.png",pos=[90,90],assetPath="assets/guy2/",update=player_update,extraImages=vars.images.player,animations=vars.animations.player,extraArgs={"player":2,"dead":False,"kill":False,"tangable":True,"killable":True})

    Terrain("grass.png",pos=[128,0])

    keyboard = [{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False},{"up":False,"down":False,"left":False,"right":False,"action":False}]

def update(tick):
    global frameN
    frameN += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit() # SYS
        
        if event.type == pygame.KEYDOWN: # KEY
            for i in range(len(vars.binds)):
                if event.key in vars.binds[i]:
                    keyboard[i][vars.binds[i][event.key]] = True
        if event.type == pygame.KEYUP:
            for i in range(len(vars.binds)):
                if event.key in vars.binds[i]:
                    keyboard[i][vars.binds[i][event.key]] = False
    
    screen.fill(bg)

    for terrain in terrains:
        if terrain.animation:
            terrain.do_animation()
        screen.blit(terrain.image,terrain.rect)

    for sprite in sorted(sprites): # SPRITES
        sprite.update(tick)
        screen.blit(sprite.image,sprite.rect)
    
    font = pygame.font.SysFont("Arial",20)
    
    text = font.render(f"Frame: {frameN} | Pos: x {sprites[0].rect.x} y {sprites[0].rect.y} | Dir: {sprites[0].direction} pr {sprites[0].projected_direction} | Edges: T {sprites[0].rect.top} L {sprites[0].rect.left} R {sprites[0].rect.right} B {sprites[0].rect.bottom} | Speed: f {sprites[0].fSpeed} - {sprites[0].speed} su {sprites[0].startup} | Ani: {sprites[0].animationFrame} {sprites[0].animation} | {sprites[0].extraArgs}",True,(255,0,0))
    text_rect = text.get_rect()
    text_rect.left += 70
    text_rect.top += 70
    
    screen.blit(text,text_rect)

pauseMenu = pygame_menu.Menu('Paused.',size[0],size[1],theme=pygame_menu.themes.THEME_DARK)
pauseMenu.add.button('Continue', unpause)
pauseMenu.add.button('Quit', pygame_menu.events.EXIT)
pauseMenu.disable()

menu = pygame_menu.Menu('Game.',size[0],size[1],theme=pygame_menu.themes.THEME_DARK)
menu.add.button('Play', start)
menu.add.button('Quit', pygame_menu.events.EXIT)
menu.mainloop(screen)
