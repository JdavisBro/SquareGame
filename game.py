# Built In
import json
import os
import sys
import random
import copy

import rich
from rich import print

# External
import pygame
import pygame.freetype
import pygame_menu

# Local
import vars

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)
prefsPath = os.path.join(application_path, "userPrefs.json")

os.chdir(getattr(sys,"_MEIPASS","."))
debug = True if "debug" in sys.argv else False

pygame.init()

size = (1280, 704) # default playfield
screenSize = (size[0]+48,size[1]+48)
bg = 0, 0, 0
scroll = [0,0]

pygame.display.set_caption("Game.")
icon = pygame.image.load("assets/icon.png")
pygame.display.set_icon(icon)

if 'levelEdit' in sys.argv:
    screen = pygame.display.set_mode([screenSize[0]+500,screenSize[1]])
    from levelEdit import LevelEditor
    levelEdit = LevelEditor(screenSize,size,screen)
else:
    levelEdit = None
    screen = pygame.display.set_mode(screenSize)

frameN = 1
clock = pygame.time.Clock()
playerSprite = []

def bind(value,upper,lower):
    if value > upper: return upper, True
    if value < lower: return lower, True
    return value, False

def bind_rect_to_screen(rect):
    binds = []
    rect.top,binded = bind(rect.top,size[1],0)
    binds.append(binded)
    rect.left,binded = bind(rect.left,size[0],0)
    binds.append(binded)
    rect.bottom,binded = bind(rect.bottom,size[1],0)
    binds.append(binded)
    rect.right,binded = bind(rect.right,size[0],0)
    binds.append(binded)
    return rect,binds

class Terrain:
    def __init__(self,image,pos=[0,0],assetPath="assets/terrain/",material="none",scale=4,animation=None,animations=None):
        global levelEdit
        index = image
        if not isinstance(vars.images[vars.terrains[assetPath]][index],pygame.Surface):
            vars.images[vars.terrains[assetPath]][index] = pygame.image.load(assetPath+vars.images[vars.terrains[assetPath]][index])
            self.rect = vars.images[vars.terrains[assetPath]][index].get_rect()
            vars.images[vars.terrains[assetPath]][index] = pygame.transform.scale(vars.images[vars.terrains[assetPath]][index],(self.rect.width*scale,self.rect.height*scale))
        self.image = vars.images[vars.terrains[assetPath]][index]
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        if animation:
            animation = vars.animations[animations][animation]
            self.animation = [pygame.transform.scale(pygame.image.load(assetPath+im),(self.rect.width,self.rect.height)) for im in animation]
        else:
            self.animation = None
        self.animationFrame = 0
        self.animationFrames = 0
        self.material = material
        terrainSurface.blit(self.image,self.rect)
        terrains.append(self)
        if levelEdit:
            levelEdit.editCoords[str(list(self.rect.topleft))][0] = self

    def do_animation(self):
        global terrainSurface
        if self.animationFrames % 10 == 0:
            self.image = self.images[self.animation[self.animationFrame]]
            self.animationFrame += 1
        self.animationFrames += 1
        if self.animationFrame >= len(self.animation):
            self.animationFrame = 0
            self.animationFrames = 1
        terrainSurface.blit(self.image,self.rect)

class Sprite:
    def __init__(
        self,image,pos=[0,0],assetPath="assets/",scale=4,
        extraImages="default",extraArgs={},
        animations=None,weight=0
        ):
        global levelEdit, triggers, playerSprite
        self.aliveFrames = 0
        self.extraArgs = vars.defaultExtraArgs.copy() # Default Args
        self.extraArgs.update(extraArgs) # Add args to defaults
        if animations:
            self.animations = vars.animations[animations]
            if "idle" in self.animations:
                self.set_animation("idle")
            else:
                self.set_animation("a")
        else:
            self.animations = []
        self.rect = None
        if isinstance(list(vars.images[extraImages].values())[0],str):
            for im in vars.images[extraImages]:
                img = pygame.image.load(assetPath+vars.images[extraImages][im])
                if not self.rect:
                    self.rect = img.get_rect()
                vars.images[extraImages][im] = pygame.transform.scale(img,(self.rect.width*scale,self.rect.height*scale))
        self.images = vars.images[extraImages]
        self.image = self.images[image]
        if self.extraArgs["addControl"]:
            self.image = self.image.copy()
            font_render("munro32",pygame.key.name(userPrefs["binds"][self.extraArgs["addControl"]]).upper(),(24,18),surface=self.image)
        if self.extraArgs["triggerId"]:
            triggers[self.extraArgs["triggerId"]] = False
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.weight = weight
        if self.extraArgs["player"] == 1:
            sprites.insert(0,self)
            playerSprite.append(self)
        else:
            sprites.append(self)
        if levelEdit:
            levelEdit.editCoords[str(list(self.rect.topleft))][0] = self

    def __lt__(self,other):
        return (self.weight < other.weight)

    def update(self,tick):
        global collectedKeys
        global frameN
        self.aliveFrames += 1
        if self.extraArgs["goal"] and self.extraArgs["locked"]:
            if collectedKeys >= levelData["level"]["keys"]:
                self.set_animation("unlock")
                self.extraArgs["locked"] = False
        self.do_animations()

    def collisions(self,binds):
        return binds

    def do_animations(self):
        global goMainMenu,levelChange,levelName
        if not self.animations or not self.animation:
            return
        animationChanged = False
        if not self.extraArgs["player"] and playerSprite:
            playerNear = pygame.Rect(self.rect.x-self.rect.width//2,self.rect.y-self.rect.height//2,self.rect.width*2,self.rect.height*2)
            display_rect(playerNear)
            if playerNear.collidelist(playerSprite):
                playerNear = True
                if "playerNear" in self.animations and self.animation == self.animations["idle"][1]:
                    self.animation = self.animations["playerNear"][1]
                    animationChanged = True
            else:
                playerNear = False
                if "playerNear" in self.animations:
                    if self.animation == self.animations["playerNear"][1]:
                        self.animation = self.animations["idle"][1]
                        animationChanged = True
        if self.animationFrame >= len(self.animation):
            if not self.animationTimeout[1] and self.animationTimeout[0] != -1:
                self.animationTimeout[1] = True
                self.animationTimeout[0] = self.aliveFrames + self.animationTimeout[0]
            if self.animationTimeout[1] and self.animationTimeout[0] > self.aliveFrames:
                return
            if self.extraArgs["dead"] and self.extraArgs["player"]:
                reset()
            if self.extraArgs["dead"] and self in sprites:
                sprites.remove(self)
            if self.extraArgs["won"]:
                timer.print_time()
                if levelEdit or userPrefs["levelCompleteAction"] == 2:
                    reset()
                elif levels.index(levelName) == len(levels)-1 or userPrefs["levelCompleteAction"] == 1:
                    goMainMenu = True
                else:
                    levelName = levels[levels.index(levelName)+1]
                    menu.get_widget("levelSelect").set_value(levelName)
                    levelChange = True
            if self.animationEnd:
                self.animation = self.animationEnd
                self.animationEnd = []
                self.animationFrame = 0
                self.animationFrames = 0
                self.animationTimeout = [-1,False]
                return
            self.animation = []
            self.animationFrame = 0
            if self.animationTimeout[1]:
                self.animationTimeout[1] = False
                if "playerNear" in self.animations and playerNear:
                    self.animation = self.animations["playerNear"]
                else:
                    self.set_animation("idle")
            if animationChanged:
                self.image = self.images[self.animation[self.animationFrame]]
        else:
            if animationChanged:
                self.image = self.images[self.animation[self.animationFrame]]
            if self.animationFrames % self.animationTime == 0:
                self.image = self.images[self.animation[self.animationFrame]]
                self.animationFrame += 1
            self.animationFrames += 1

    def set_animation(self,anim,args=None):
        if not self.animations:
            return
        self.animationFrame = 0
        self.animationFrames = 0
        self.animationTime = 10
        if anim == "idle" or anim == "playerNear":
            self.animationTime = 60
        self.animationTimeout = [0,False]
        self.animationEnd = []
        if anim in self.animations:
            args = str(args)
            self.animationTimeout = [self.animations[anim][0],False]
            if args:
                self.animation = [frame.format(args) for frame in self.animations[anim][1]]
            else:
                self.animation = self.animations[anim][1]
            if args:
                self.animationEnd = [frame.format(args) for frame in self.animations[anim][2]]
            else:
                self.animationEnd = self.animations[anim][2]
        else:
            self.animation = []

    def kill(self):
        if self.extraArgs["dead"]:
            return
        if self.animations:
            if "death" in self.animations:
                self.extraArgs["dead"] = True
                self.set_animation("death")
            else:
                sprites.remove(self)
        else:
            sprites.remove(self)

class PlayerSprite(Sprite):
    def __init__(
        self,image,pos=[0,0],assetPath="assets/",scale=4,
        acceleration=0.25,extraImages="default",extraArgs={},
        animations=None,weight=0
        ):
        super().__init__(image,pos,assetPath,scale,extraImages,extraArgs,animations,weight)
        self.speed = [0,0] # Speed
        self.fSpeed = 0
        self.acceleration = acceleration
        self.direction = None
        self.projected_direction = None
        self.startup = 1
        self.lookFrame = 0

    def update(self,tick):
        global newKeyboard, scroll, screenSize, playerSprite
        player = self.extraArgs["player"]-1
        if player == 1 and self not in playerSprite:
            playerSprite.append(self)
        if not self.extraArgs["dead"] and not self.extraArgs["won"]:
            if keyboard[player]["up"]:
                self.projected_direction = 0 if (0 != self.direction) else self.projected_direction
            elif keyboard[player]["down"]:
                self.projected_direction = 2 if 2 != self.direction else self.projected_direction
            elif keyboard[player]["left"]:
                self.projected_direction = 3 if 3 != self.direction else self.projected_direction
            elif keyboard[player]["right"]:
                self.projected_direction = 1 if 1 != self.direction else self.projected_direction
            if not self.fSpeed:
                if self.direction != self.projected_direction:
                    self.direction = self.projected_direction
                    if self.direction is not None:
                        self.set_animation("look",self.direction)
                        self.lookFrame = 0
                if (keyboard[player]["action"] or userPrefs["automaticMovement"] == 1) and (self.direction is not None and frameN != 0):
                    movedRect = self.rect.move([1 if self.direction == 1 else -1 if self.direction == 3 else 0,1 if self.direction == 2 else -1 if self.direction == 0 else 0])
                    def sprite_movement_check(s):
                        return not any((s == self, not s.extraArgs["tangable"], s.extraArgs["key"], (s.extraArgs["goal"] and not s.extraArgs["locked"]), s.extraArgs["movable"], s.extraArgs["playerThrough"]))
                    rects = [s.rect for s in sprites if sprite_movement_check(s)] + [t.rect for t in terrains]
                    collides = movedRect.collidelistall(rects)
                    if (terrainSurface.get_rect().contains(movedRect)) and not collides:
                        self.fSpeed = 40
                        self.startup = 15
                        self.set_animation("go",self.direction)
                        self.projected_direction = None
                    else:
                        self.image = self.images["idle"]
                        self.direction = None
                        self.projected_direction = None
            accel = self.acceleration*tick
            if self.direction is not None and not self.fSpeed:
                self.lookFrame += 1
            if self.fSpeed:
                if self.direction == 0: #up
                    self.speed[1] = round((self.speed[1] - accel/self.startup) if (self.speed[1]>self.fSpeed*-1) else self.fSpeed*-1,2)
                elif self.direction == 1: #right
                    self.speed[0] = round((self.speed[0] + accel/self.startup) if (self.speed[0]<self.fSpeed) else self.fSpeed,2)
                elif self.direction == 2: #down
                    self.speed[1] = round((self.speed[1] + accel/self.startup) if (self.speed[1]<self.fSpeed) else self.fSpeed,2)
                elif self.direction == 3: #left
                    self.speed[0] = round((self.speed[0] - accel/self.startup) if (self.speed[0]>self.fSpeed*-1) else self.fSpeed*-1,2)
            self.rect = self.rect.move([round(self.speed[0]),round(self.speed[1])])
            self.rect,binds = bind_rect_to_screen(self.rect) 
            binds = self.collisions(binds)
            if any(binds):
                self.speed = [0,0]
                self.fSpeed = 0
                self.direction = None
                if not self.animation:
                    self.set_animation("collide")
            self.startup -= 0.5 if self.startup > 1 else 0
        if self.rect.centerx - scroll[0] > screenSize[0]//2: # RIGHT
            if not (self.fSpeed and self.direction == 3): # this line is so that scroll doesn't snap back if going after the direction scroll happens
                scroll[0] += self.rect.centerx-scroll[0] - screenSize[0]//2
        elif self.rect.centerx - scroll[0] < screenSize[0]//2: # LEFT
            if not (self.fSpeed and self.direction == 1):
                scroll[0] += self.rect.centerx-scroll[0] - screenSize[0]//2
        if self.rect.centery - scroll[1] > screenSize[1]//2: # DOWN
            if not (self.fSpeed and self.direction == 0):
                scroll[1] += self.rect.centery - scroll[1] - screenSize[1]//2
        elif self.rect.centery - scroll[1] < screenSize[1]//2: # UP
            if not (self.fSpeed and self.direction == 2):
                scroll[1] += self.rect.centery - scroll[1] - screenSize[1]//2
        scroll[0] = bind(scroll[0],size[0]+48-screenSize[0],0)[0]
        scroll[1] = bind(scroll[1],size[1]+48-screenSize[1],0)[0]
        if (self.lookFrame > 180) and not self.fSpeed:
            if self.direction == 0:
                scroll[1] -= bind(self.lookFrame - 180,100,0)[0]
            elif self.direction == 2:
                scroll[1] += bind(self.lookFrame - 180,100,0)[0]
            elif self.direction == 1:
                scroll[0] += bind(self.lookFrame - 180,100,0)[0]
            elif self.direction == 3:
                scroll[0] -= bind(self.lookFrame - 180,100,0)[0]
        scroll[0] = bind(scroll[0],size[0]+48-screenSize[0],0)[0]
        scroll[1] = bind(scroll[1],size[1]+48-screenSize[1],0)[0]
        super().update(tick)

    def collisions(self,binds):
        global collectedKeys
        spritesNoMe = [sprite for sprite in sprites if sprite != self and ((sprite.extraArgs["tangable"] and not sprite.extraArgs["dead"]) or sprite.extraArgs["triggerId"]) and not sprite.extraArgs["playerThrough"]]
        rects = [sprite.rect for sprite in spritesNoMe]
        collides = self.rect.collidelistall(rects)
        if collides:
            for collision in collides:
                if spritesNoMe[collision].extraArgs["triggerId"]:
                    triggers[spritesNoMe[collision].extraArgs["triggerId"]] = True
                    continue
                if (spritesNoMe[collision].extraArgs["goal"] and not spritesNoMe[collision].extraArgs["locked"]):
                    self.set_animation("celebrate")
                    self.extraArgs["won"] = True
                if spritesNoMe[collision].extraArgs["key"]:
                    spritesNoMe[collision].kill()
                    collectedKeys += 1
                    continue
                if spritesNoMe[collision].extraArgs["kill"] and self.extraArgs["killable"]:
                    self.kill()
                if self.extraArgs["kill"] and spritesNoMe[collision].extraArgs["killable"]:
                    spritesNoMe[collision].kill()
                stop = None
                if spritesNoMe[collision].extraArgs["movable"]:
                    tempRect = spritesNoMe[collision].rect.copy()
                    if self.direction == 0: #up
                        tempRect.bottom = self.rect.top
                    elif self.direction == 1: #right
                        tempRect.left = self.rect.right
                    elif self.direction == 2: #down
                        tempRect.top = self.rect.bottom
                    elif self.direction == 3: #left
                        tempRect.right = self.rect.left
                    r = [terrain.rect for terrain in terrains] + [sprite.rect for sprite in sprites if sprite.extraArgs["tangable"] and (sprite != self and sprite != spritesNoMe[collision])]
                    col = tempRect.collidelist(r)
                    tempRect,moveBinds = bind_rect_to_screen(tempRect)
                    if any(moveBinds):
                        stop = True
                    elif col != -1:
                        stop = True
                        if self.direction == 0: #up
                            tempRect.top = r[col].bottom
                        elif self.direction == 1: #right
                            tempRect.right = r[col].left
                        elif self.direction == 2: #down
                            tempRect.bottom = r[col].top
                        elif self.direction == 3: #left
                            tempRect.left = r[col].right
                    else:
                        if self.fSpeed > 20:
                            self.fSpeed = self.fSpeed//8
                    spritesNoMe[collision].rect = tempRect
                if (self.fSpeed and not spritesNoMe[collision].extraArgs["movable"]) or stop:
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
                    if "collide" in spritesNoMe[collision].animations:
                        spritesNoMe[collision].set_animation("collide")
        rects = [terrain.rect for terrain in terrains]
        collides = self.rect.collidelistall(rects)
        if collides:
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

class PathSprite(Sprite):
    def __init__(self,image,pos=[0,0],assetPath="assets/",scale=4,
        acceleration=0.25,extraImages="default",extraArgs={},
        animations=None,weight=0
        ):
        super().__init__(image,pos,assetPath,scale,extraImages,extraArgs,animations,weight)
        self.pathIndex = 0
        self.startup = self.extraArgs["pathStartup"]
        self.startupImmunity = 0
        self.pathIndexDir = 0
        self.pathCooldown = self.extraArgs["pathCooldown"]
        self.moving = None
        self.done = False
        if self.extraArgs["path"] is None:
            self.extraArgs["path"] = [self.rect.topleft]

    def update(self,tick):
        if not self.extraArgs["dead"] and (((not self.extraArgs["pathRepeat"] and not self.done) or self.extraArgs["pathRepeat"])):
            if self.pathCooldown:
                self.pathCooldown -= 1
            else:
                if self.extraArgs["pathTrigger"]:
                    if not triggers[self.extraArgs["pathTrigger"]]:
                        super().update()
                        return
                pathDifference = [self.extraArgs["path"][self.pathIndex][0]-list(self.rect.topleft)[0],self.extraArgs["path"][self.pathIndex][1]-list(self.rect.topleft)[1]]
                if self.startupImmunity == 0:
                    movement = self.extraArgs["pathSpeed"]/self.startup*tick
                else:
                    movement = self.extraArgs["pathSpeed"]*tick
                move = [0,0]
                if pathDifference[0] > 0:
                    if pathDifference[0] <= movement:
                        move[0] = pathDifference[0]
                    else:
                        move[0] = movement
                elif pathDifference[0] < 0:
                    if pathDifference[0] >= movement * -1:
                        move[0] = pathDifference[0]
                    else:
                        move[0] = movement*-1
                if pathDifference[1] > 0:
                    if pathDifference[1] <= movement:
                        move[1] = pathDifference[1]
                    else:
                        move[1] = movement
                elif pathDifference[1] < 0:
                    if pathDifference[1] >= movement * -1:
                        move[1] = pathDifference[1]
                    else:
                        move[1] = movement*-1
                self.rect = self.rect.move(move)
                if ((move[0] if move[0] > 0 else move[0]*-1) > (move[1] if move[1] > 0 else move[1]*-1)):
                    if move[0] >= 0:
                        direction = 1
                    else:
                        direction = 3
                else:
                    if move[1] >= 0:
                        direction = 2
                    else:
                        direction = 0
                if (not move[0] and not move[1]):
                    direction = None
                if (self.moving != direction and 'go' in self.animations):
                    self.moving = direction
                    if self.moving is not None:
                        self.set_animation("go",self.moving)
                    else:
                        self.set_animation("reset")
                if not move[0] and not move[1]:
                    if self.pathIndex == 0 and self.pathIndexDir == 1:
                        self.pathIndexDir = 0
                    elif self.pathIndex == len(self.extraArgs["path"])-1 and self.pathIndexDir == 0:
                        self.done = True
                        self.pathIndexDir = 1
                    self.startup = self.extraArgs["pathStartup"]
                    self.pathIndex = self.pathIndex + 1 if self.pathIndexDir == 0 else self.pathIndex - 1
                    self.pathCooldown = self.extraArgs["pathCooldown"]
                    self.set_animation("idle")
                self.startupImmunity -= 1 if self.startupImmunity > 0 else 0
                if self.startup > 1:
                    self.startup -= 0.5
                    if self.startup <= 1:
                        self.startupImmunity = 90
                self.collisions(move)
        super().update(tick)

    def collisions(self,move):
        spritesNoMe = [sprite for sprite in sprites if sprite != self and (sprite.extraArgs["tangable"] and not sprite.extraArgs["dead"])]
        rects = [sprite.rect for sprite in spritesNoMe]
        collides = self.rect.collidelistall(rects)
        if collides:
            for collision in collides:
                if self.extraArgs["goal"] and spritesNoMe[collision].extraArgs["player"]:
                    return
                if self.extraArgs["kill"] and spritesNoMe[collision].extraArgs["killable"]:
                    spritesNoMe[collision].kill()
                    return
                if isinstance(spritesNoMe[collision],PlayerSprite) and not spritesNoMe[collision].extraArgs["dead"]:
                    if ((move[0] if move[0] > 0 else move[0]*-1) > (move[1] if move[1] > 0 else move[1]*-1)):
                        if move[0] >= 0:
                            rects[collision].left = self.rect.right
                        else:
                            rects[collision].right = self.rect.left
                    else:
                        if move[1] >= 0:
                            rects[collision].top = self.rect.bottom
                        else:
                            rects[collision].bottom = self.rect.top
                    binds = []
                    rects[collision].top,binded = bind(rects[collision].top,size[1],0)
                    binds.append(binded)
                    rects[collision].left,binded = bind(rects[collision].left,size[0],0)
                    binds.append(binded)
                    rects[collision].bottom,binded = bind(rects[collision].bottom,size[1],0)
                    binds.append(binded)
                    rects[collision].right,binded = bind(rects[collision].right,size[0],0)
                    binds.append(binded)
                    if rects[collision].collidelistall([t.rect for t in terrains] + [s.rect for s in sprites if all([not s.extraArgs["dead"],s.extraArgs["tangable"],not (s.extraArgs["goal"] and not s.extraArgs["locked"]),not s.extraArgs["key"], s != self, s != spritesNoMe[collision]])]):
                        binds.append(True)
                    if any(binds):
                        spritesNoMe[collision].kill()

class Timer():
    def __init__(self,level):
        self.levelTime = 0
        self.level = level
        self.time = 0
        self.started = 0

    def update(self,tick):
        """Updates the timer."""
        if (userPrefs["timerStart"] == 1 and self.started != 2):
            if self.started == 1:
                self.started = 2
            return
        if self.level != levelName:
            self.level = levelName
            self.level_reset()
        self.time += tick
        self.levelTime += tick

    def level_reset(self):
        if self.started > 0:
            self.started = 0
        self.levelTime = 0

    def start(self):
        """Starts the timer if it is on first input mode."""
        if self.started == 0:
            self.started = 1

    def print_time(self):
        print(f"Time on [bold cyan]Level {self.level}[/bold cyan]: {self.time_readable(self.levelTime)}")

    def time_readable(self,time,hours=True,milliseconds=True):
        """Returns time (ms) as a readable string of "HH:MM:SS.MS"."""
        if time >= 3600000:
            hour = time//3600000
            time -= 3600000*hour
            hour = ("0" if len(str(hour)) == 1 else "") + str(hour)
        else:
            hour = "00"
        if time >= 60000:
            minute = time//60000
            time -= 60000*minute
            minute = ("0" if len(str(minute)) == 1 else "") + str(minute)
        else:
            minute = "00"
        if time >= 1000:
            second = time//1000
            time -= 1000*second
            second = ("0" if len(str(second)) == 1 else "") + str(second)
        else:
            second = "00"
        time = str(time//10)
        if time:
            time = ("0" if len(time) == 1 else "") + time
        out = ""
        if hours:
            out += f"{hour}:"
        out += f"{minute}:{second}"
        if milliseconds:
            out += f".{time}"
        return out
        

def start():
    global clock,frameN,goMainMenu,levelName,levelChange,timer
    if not levelName:
        return
    timer = Timer(levelName)
    frameN = 0
    reset_level()
    reset()
    goMainMenu = False
    levelChange = False
    while 1:
        if pauseMenu.is_enabled():
            pauseMenu.update(pygame.event.get())
        if goMainMenu:
            levels = list(list(os.walk("levels"))[0][2])
            levels = [f[:-5] for f in levels if f.endswith(".json")]
            dropSelect.update_items([(level.replace("[q]","?"),level) for level in levels])
            dropSelect.make_selection_drop()
            return
        if pauseMenu.is_enabled():
            pauseMenu.draw(screen)
        else:
            tick = clock.tick(120)
            update(tick)
        if levelChange:
            reset_level()
            reset()
            levelChange = False
        frameN += 1
        pygame.display.flip()

def pause():
    pygame.mouse.set_visible(True)
    keyboard[0]["pause"] = False
    pauseMenu.get_current().select_widget(pauseMenu.get_widgets()[0])
    pauseMenu.get_current().enable()

def unpause():
    if not levelEdit:
        pygame.mouse.set_visible(False)
    pauseMenu.get_current().full_reset()
    pauseMenu.get_current().disable()

def returnToMainMenu():
    global goMainMenu
    pauseMenu.get_current().full_reset()
    pauseMenu.get_current().disable()
    goMainMenu = True

def reset_level():
    global staticSurface, levelData, prevGridPos, previousMouse, levelName, bg, spriteTypes, hudSurface, fonts, size

    with open(f"levels/{levelName}.json","r") as f:
        levelData = json.load(f)

    if levelEdit:
        levelEdit.levelData = levelData

    size = levelData['level']['size'].copy()
    size[0] = size[0]*64
    size[1] = size[1]*64

    spriteTypes = {"none": Sprite,"player": PlayerSprite,"path": PathSprite}

    staticSurface = pygame.Surface((size[0]+48,size[1]+48))

    hudSurface = pygame.Surface(screenSize,flags=pygame.SRCALPHA)

    x = 0
    y = 0
    tiles = []
    for tile in levelData['level']['background']:
        tile = pygame.image.load(f"assets/background/{tile}.png")
        tiles.append(pygame.transform.scale(tile,(64,64)))
    while y<size[1]:
        while x<size[0]:
            staticSurface.blit(random.choice(tiles),(x+24,y+24))
            x += 64
        x = 0
        y += 64

    im = pygame.image.load(f"assets/borders/{levelData['level']['border']}/corner.png") # Corner piece
    im = pygame.transform.scale(im,(6*4,6*4))
    staticSurface.blit(im,(0,0))
    staticSurface.blit(im,(levelData['level']['size'][0]*64+24,0))
    staticSurface.blit(im,(0,levelData['level']['size'][1]*64+24))
    staticSurface.blit(im,(levelData['level']['size'][0]*64+24,levelData['level']['size'][1]*64+24))
    im = pygame.image.load(f"assets/borders/{levelData['level']['border']}/left.png") # Left piece
    im = pygame.transform.scale(im,(24,64))
    oIm = None
    if os.path.exists(f"assets/borders/{levelData['level']['border']}/right.png"):
        oIm = pygame.image.load(f"assets/borders/{levelData['level']['border']}/right.png")
        oIm = pygame.transform.scale(oIm,(24,64))
    for i in range(levelData['level']['size'][1]):
        staticSurface.blit(im,(0,24+(i*64))) # Blit to left
        staticSurface.blit(oIm if oIm else im,(levelData['level']['size'][0]*64+24,24+(i*64))) # Blit to right
    im = pygame.image.load(f"assets/borders/{levelData['level']['border']}/top.png")
    im = pygame.transform.scale(im,(64,24))
    oIm = None
    if os.path.exists(f"assets/borders/{levelData['level']['border']}/bottom.png"):
        oIm = pygame.image.load(f"assets/borders/{levelData['level']['border']}/bottom.png")
        oIm = pygame.transform.scale(oIm,(64,24))
    for i in range(levelData['level']['size'][0]):
        staticSurface.blit(im,(24+(i*64),0))
        staticSurface.blit(oIm if oIm else im,(24+(i*64),levelData['level']['size'][1]*64+24))

    im = pygame.image.load("assets/timerBg.png")
    im = pygame.transform.scale(im,(128,64))
    hudSurface.blit(im,(screenSize[0]-128,0))

    if levelData["level"]["keys"]:
        im = pygame.image.load("assets/keyCountBg.png")
        im = pygame.transform.scale(im,(72,26))
        hudSurface.blit(im,(10,0))

    if not levelEdit:
        pygame.mouse.set_visible(False)
    else:
        levelEdit.size = size
        levelEdit.level_reset()

def reset():
    global terrains, sprites, keyboard, terrainSurface, play, levelEdit, collectedKeys, newKeyboard, debugTextBg, size, triggers

    if pauseMenu.is_enabled():
        pauseMenu.disable()

    collectedKeys = 0

    play = not levelEdit

    terrains = []

    sprites = []

    triggers = {}

    terrainSurface = pygame.Surface(size,flags=pygame.SRCALPHA) 

    for sprite in levelData["sprites"]:
        if levelEdit:
            levelEdit.editCoords[str(sprite["pos"])] = [None,sprite,"sprite"]
        loadSpriteOrTerrain(sprite,"sprite")

    for terrain in levelData["terrain"]:
        if levelEdit:
            levelEdit.editCoords[str(terrain["pos"])] = [None,terrain,"terrain"]
        loadSpriteOrTerrain(terrain,"terrain")

    if levelEdit:
        levelEdit.sprites = sprites
        levelEdit.terrains = terrains
        levelEdit.terrainSurface = terrainSurface

    keyboard = copy.deepcopy(blankKeyboard)
    newKeyboard = copy.deepcopy(blankKeyboard)

    if timer.level == levelName:
        timer.level_reset()

    if debug:
        debugTextBg = pygame.Surface(screenSize)

def close():
    print("\n\n")
    sys.exit()

def loadSpriteOrTerrain(data,stype):
    data = data.copy()
    if stype == "sprite":
        spritetype = spriteTypes[data.get("type","none")]
        if "type" in data.keys():
            data.pop("type")
        spritetype(**data)
    else:
        Terrain(**data)

if levelEdit:
    levelEdit.loadSpriteOrTerrain = loadSpriteOrTerrain

def font_render(font,text,pos,colour=(255,255,255),bg_colour=None,surface=screen,antialiasing=True):
    fonts[font].antialiased = antialiasing
    text = fonts[font].render_to(surface,pos,text,colour,bg_colour)

rectsToFill = []
def display_rect(rect,colour=(255,0,0,100)):
    rectsToFill.append((rect,colour))

def update(tick):
    global play, newKeyboard, rectsToFill, playerSprite

    [playerSprite.remove(sprite) for sprite in playerSprite if sprite not in sprites]

    rectsToFill = []

    newKeyboard = copy.deepcopy(blankKeyboard)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: close()
        if event.type == pygame.KEYDOWN: # KEY
            timer.start()
            if event.key == pygame.K_i and debug:
                mouserect = pygame.Rect((pygame.mouse.get_pos(),(1,1)))
                mouserect.topleft = (mouserect.x-24,mouserect.y-24)
                guys = sprites + terrains
                col = mouserect.collidelist(guys)
                if col != -1:
                    rich.inspect(guys[col])
            for i in range(len(binds)):
                if event.key in binds[i]:
                    newKeyboard[i][binds[i][event.key]] = True
                    keyboard[i][binds[i][event.key]] = True
        if event.type == pygame.KEYUP:
            for i in range(len(binds)):
                if event.key in binds[i]:
                    keyboard[i][binds[i][event.key]] = False
    
    if keyboard[0]["pause"]:
        pause()
    if newKeyboard[0]["reset"]:
        reset()
        return

    if levelEdit and not play:
        if newKeyboard[0]["reset"]:
            levelData["level"]["keys"] -= 1
        elif newKeyboard[0]["action"]:
            levelData["level"]["keys"] += 1

    screen.fill((0,0,0))

    if levelEdit and play:
        if pygame.key.get_pressed()[pygame.K_o]:
            play = False
            reset()

    if playerSprite:
        playerDead = any([(sprite.extraArgs["dead"] or sprite.extraArgs["won"]) for sprite in playerSprite])
    else:
        playerDead = True

    if not playerDead:
        [terrain.do_animation() for terrain in terrains if terrain.animation]

    for sprite in sprites: # SPRITES
        if sprite in playerSprite:
            continue
        if play and not playerSprite:
            sprite.update(tick)
        elif play and not playerDead:
            sprite.update(tick)
        scrollPos = (list(sprite.rect.topleft)[0]+24-scroll[0], list(sprite.rect.topleft)[1]+24-scroll[1])
        screen.blit(sprite.image,scrollPos)

    if play and not playerSprite:
        timer.update(tick)
    elif (play and not (playerDead and not frameN == 0)):
        timer.update(tick)

    if play and playerSprite:
        for sprite in playerSprite:
            sprite.update(tick)

    if levelEdit and not play:
        scroll[0] += 8 if keyboard[0]["right"] else -8 if keyboard[0]["left"] else 0
        scroll[1] += 8 if keyboard[0]["down"] else -8 if keyboard[0]["up"] else 0

    scroll[0] = bind(scroll[0],size[0]+48-screenSize[0],0)[0]
    scroll[1] = bind(scroll[1],size[1]+48-screenSize[1],0)[0]

    screen.blit(staticSurface,(0-scroll[0],0-scroll[1]))

    screen.blit(terrainSurface,(24-scroll[0],24-scroll[1]))

    for sprite in sorted(sprites):
        if sprite == playerSprite:
            continue
        scrollPos = (list(sprite.rect.topleft)[0]+24-scroll[0], list(sprite.rect.topleft)[1]+24-scroll[1])
        screen.blit(sprite.image,scrollPos)

    for sprite in playerSprite:
        scrollPos = (list(sprite.rect.topleft)[0]+24-scroll[0], list(sprite.rect.topleft)[1]+24-scroll[1])
        screen.blit(sprite.image,scrollPos)

    if levelEdit and not play:
        selectedIm,play = levelEdit.update(scroll)
        screen.blit(levelEdit.editStaticSurface,(24-scroll[0],24-scroll[1]))
        screen.blit(levelEdit.editSurface,(0,0))
        if selectedIm[1].topleft != (0,0):
            screen.blit(selectedIm[0],selectedIm[1])

    screen.blit(hudSurface,(0,0))

    if playerSprite:
        if any([sprite.extraArgs["won"] for sprite in playerSprite]):
            font_render("arial60","Congratulations!",(70,70),(255,255,255))

    if levelData['level']['keys']:
        font_render("munro18",f"{collectedKeys}/{levelData['level']['keys']}",(45,7),(25,25,25),antialiasing=False)

    if levelEdit:
        font_render("munro24",str(levelEdit.mousePos),(90,0))
    if debug:
        if not pygame.mouse.get_visible():
            pygame.mouse.set_visible(True)
        font_render("munro24",str(pygame.mouse.get_pos()),(400,0))
        if rectsToFill and pygame.key.get_pressed()[pygame.K_RETURN]:
            surface = pygame.Surface(size,pygame.SRCALPHA)
            for i in rectsToFill:
                surface.fill(i[1],i[0],pygame.BLEND_RGBA_ADD)
            screen.blit(surface,(24,24))
    t = timer.time_readable(timer.time)
    font_render("munro24",t,(1216,10),(8,8,200))
    font_render("munro24",t,(1214,8))
    t = timer.time_readable(timer.levelTime,False)
    font_render("munro24",t,(1245,40),(200,8,8))
    font_render("munro24",t,(1243,38))

    if debug and playerSprite:
        font_render("consolas10",f"F {add_zeros(frameN)} PS {clock.get_fps():.2f} T {add_zeros(tick,3)} x {add_zeros(playerSprite[0].rect.x)} y {add_zeros(playerSprite[0].rect.y)} dir {add_zeros(playerSprite[0].direction,0)} pro {add_zeros(playerSprite[0].projected_direction,0)} T {add_zeros(playerSprite[0].rect.top)} L {add_zeros(playerSprite[0].rect.left)} R {add_zeros(playerSprite[0].rect.right)} B {add_zeros(playerSprite[0].rect.bottom)} | s {add_zeros(playerSprite[0].fSpeed,1)} {add_zeros(playerSprite[0].speed[0],1)} {add_zeros(playerSprite[0].speed[1],1)} su {add_zeros(playerSprite[0].startup,1)} | Scroll: {scroll} | Ani: {add_zeros(playerSprite[0].animationFrame)} {playerSprite[0].animation}",(4,730),(255,255,255),bg_colour=(0,0,0)) # The speed values and negetive numbers are kinda fucked but i dont care.
        font_render("consolas10",f"{' '.join([arg+'='+(str(value) if not isinstance(value,bool) else ('T' if value else 'F')) for arg,value in playerSprite[0].extraArgs.items()])}",(4,740),(255,255,255),bg_colour=(0,0,0))

def add_zeros(text,zeros=4):
    if text is None:
        if zeros == 0:
            return "N"
        text = "NA"
    text = str(text)
    return '0'*bind((len(text)-4)*-1,zeros,0)[0] + text

fonts = {} # FONTS

for f in [("munro24","assets/fonts/munro/regular.ttf",24),("munro18","assets/fonts/munro/small.ttf",18),("munro32","assets/fonts/munro/regular.ttf",32)]:
    fonts[f[0]] = pygame.freetype.Font(f[1],f[2])

for f in [("arial60","arial",60),("consolas10","consolas",10)]: # May be exclusive to windows so perhaps check.
    fonts[f[0]] = pygame.freetype.SysFont(f[1],f[2])

pauseMenu = pygame_menu.Menu('Paused.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK) # PAUSE MENU
[pauseMenu.add.button(*i) for i in [('Continue',unpause),('Reset Level',reset),('Main Menu',returnToMainMenu),('Quit Game',close)]]
pauseMenu.disable()

levelName = None

def select_level(a, selectedLevel, *args, **kwargs):
    global levelName
    levelName = selectedLevel

if not os.path.exists(prefsPath): # userPrefs and preferences menu
    with open("defaultUserPrefs.json","r") as f2:
        userPrefs = json.load(f2)
    with open(prefsPath,"w+") as f:
        json.dump(userPrefs,f,indent=4)
else:
    with open(prefsPath,"r") as f:
        userPrefs = json.load(f)

def update_prefs():
    with open(prefsPath,"w+") as f:
        json.dump(userPrefs,f,indent=4)
    darken_apply()
    refresh_binds()

def disgard():
    global userPrefs
    with open(prefsPath,"r") as f:
        userPrefs = json.load(f)
    darken_apply()
    reset_selectors()
    reset_control_widgets()

def reset_selectors():
    [widget.set_value(userPrefs[widget.get_id()]) for widget in preferencesMenu.get_widgets() if isinstance(widget,pygame_menu.widgets.Selector)]

def light_apply():
    try:
        for w in applies + disgards:
            w.set_border(2,((20,150,25) if w in applies else (150,20,25)))
    except:
        pass #cry

def darken_apply():
    try:
        for w in applies + disgards:
            w.set_border(0,(0,0,0))
    except:
        pass #joy

blankKeyboard = [{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False,"reset":False},{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False,"reset":False}] # controls and controls menu

def refresh_binds():
    global binds
    binds = [{v: k for k, v in userPrefs["binds"].items()},vars.binds[1]]

refresh_binds()

def default_controls():
    userPrefs["binds"] = {v: k for k, v in vars.binds[0].items()}
    reset_control_widgets()
    light_apply()

def reset_control_widgets():
    for widget in controlsMenu.get_widgets():
        if widget.get_id().startswith("bind"):
            bind = widget.get_id()[4:]
            widget.set_title(f"{bind} | {pygame.key.name(userPrefs['binds'][bind])}")

def get_input():
    global inputMode
    inputMode[2] += 1
    if inputMode[2] > 600:
        button.set_title(f"{inputMode[0]} | {pygame.key.name(inputMode[1])}")
        button.set_border(0,(0,0,0))
        inputMode = []
        return
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            set_input(event.key)

def set_input(key):
    global inputMode
    button = controlsMenu.get_widget(f"bind{inputMode[0]}")
    button.set_title(f"{inputMode[0]} | {pygame.key.name(key)}")
    button.set_border(0,(0,0,0))
    userPrefs["binds"][inputMode[0]] = key
    inputMode = []
    light_apply()

def start_input_mode(bind,currentKey):
    global inputMode,button
    inputMode = [bind,currentKey,0]
    button = controlsMenu.get_widget(f"bind{bind}")
    button.set_title(f"{bind} | ...")
    button.set_border(2,(0,90,0))

inputMode = []
applies = []
disgards = []

controlsMenu = pygame_menu.Menu("Controls.",screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK) # Setting up controls menu
[controlsMenu.add.button(f"{bind} | {pygame.key.name(userPrefs['binds'][bind])}",start_input_mode,bind,userPrefs['binds'][bind],button_id=f"bind{bind}") for bind in blankKeyboard[0]]
controlsMenu.add.vertical_margin(40)
applies.append(controlsMenu.add.button("Apply", update_prefs))
disgards.append(controlsMenu.add.button("Disgard", disgard))
controlsMenu.add.button("Default", default_controls)
controlsMenu.add.button("Back", pygame_menu.events.BACK)

def set_preference(a,value,pref,*args,**kwargs):
    userPrefs[pref] = value
    light_apply()

preferencesMenu = pygame_menu.Menu('Preferences.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK) # Setting up preferences menu
prefs = [("On level complete ", [("Next level",0),("Main Menu",1),("Reset Level",2)], "levelCompleteAction"),("Timer start ", [("On Level Load",0),("On First Input",1)], "timerStart"),("Move on ", [("Action Button Press",0),("Direction Press",1)], "automaticMovement")]
[preferencesMenu.add.selector(pref[0],pref[1],selector_id=pref[2],onchange=set_preference,default=userPrefs[pref[2]],pref=pref[2]) for pref in prefs]
preferencesMenu.add.vertical_margin(20)
preferencesMenu.add.button("Controls",controlsMenu)
preferencesMenu.add.vertical_margin(40)
applies.append(preferencesMenu.add.button("Apply", update_prefs))
disgards.append(preferencesMenu.add.button("Disgard", disgard))
preferencesMenu.add.button("Back", pygame_menu.events.BACK)

darken_apply()

menu = pygame_menu.Menu('Game.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK) # Setting up main menu
menu.add.button('Play Game', start)
menu.add.vertical_margin(20)
levels = list(list(os.walk("levels"))[0][2])
levels = [f[:-5] for f in levels if f.endswith(".json")]
levelName = levels[0]
dropSelect = menu.add.dropselect("Level", [(f.replace("[q]","?"),f) for f in levels],onchange=select_level,dropselect_id="levelSelect",default=0,placeholder_add_to_selection_box=False,selection_box_width=350,selection_box_height=500,selection_box_bgcolor=(148, 148, 148),selection_option_selected_bgcolor=(120, 120, 120),selection_box_arrow_color=(255,255,255),selection_option_selected_font_color=(250,250,250),selection_option_font_color=(255,255,255))
for i in [('Preferences',preferencesMenu),('Quit Game', close)]:
    menu.add.vertical_margin(20)
    menu.add.button(*i)

def run():
    while 1: # Main menu loop (with control input features)
        if not inputMode:
            events = pygame.event.get()
            menu.update(events)
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if menu.get_current() in [preferencesMenu,controlsMenu]:
                            menu.get_current().get_widgets()[-1].apply()
        else:
            get_input()
        menu.draw(screen)
        pygame.display.flip()
run()
