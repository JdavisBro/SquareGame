# Built In
import json
import os
import sys
import random

# External
import pygame
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

print("\n\n")

size = (1280, 704) #playfield
screenSize = (size[0]+48,size[1]+48)
bg = 0, 0, 0

if 'levelEdit' in sys.argv:
    from levelEdit import LevelEditor
    levelEdit = LevelEditor(screenSize,size)
else:
    levelEdit = None

pygame.display.set_caption("Game.")

icon = pygame.image.load("assets/icon.png")

pygame.display.set_icon(icon)

if levelEdit:
    screen = pygame.display.set_mode([screenSize[0]+500,screenSize[1]])
else:
    screen = pygame.display.set_mode(screenSize)

frameN = 1

clock = pygame.time.Clock()

def bind(value,upper,lower):
    if value > upper:
        return upper, True
    if value < lower:
        return lower, True
    return value, False

class Terrain:
    def __init__(self,image,pos=[0,0],assetPath="assets/terrain/",scale=4,animation=None,animations=None):
        global levelEdit
        self.image = pygame.image.load(assetPath+image)
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image,(self.rect.width*scale,self.rect.height*scale))
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
        global levelEdit
        self.aliveFrames = 0
        self.extraArgs = {"dead":False,"player":False,"tangable":True,"kill":False,"killable":False,"movable":False,"key":False,"goal":False,"locked":False,"won":False,"path":None,"pathSpeed":1,"pathStartup":1,"pushed":False,"blitImage":None} # Default Args
        self.extraArgs.update(extraArgs) # Add args to defaults
        if animations:
            self.animations = vars.animations[animations]
            if "idle" in self.animations:
                self.set_animation("idle")
            else:
                self.set_animation("a")
        else:
            self.animations = None
        self.rect = None
        if isinstance(list(vars.images[extraImages].values())[0],str):
            for im in vars.images[extraImages]:
                img = pygame.image.load(assetPath+vars.images[extraImages][im])
                if not self.rect:
                    self.rect = img.get_rect()
                vars.images[extraImages][im] = pygame.transform.scale(img,(self.rect.width*scale,self.rect.height*scale))
        self.images = vars.images[extraImages]
        self.image = self.images[image]
        if self.extraArgs["blitImage"]:
            self.image = self.image.copy()
            self.image.blit(self.images[self.extraArgs["blitImage"]],(0,0))
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.weight = weight
        sprites.append(self)
        if levelEdit:
            levelEdit.editCoords[str(list(self.rect.topleft))][0] = self

    def __lt__(self,other):
        return (self.weight < other.weight) and (vars.typeHierarchy[self.type] < vars.typeHierarchy[other.type])

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
        if not self.extraArgs["player"]:
            playerNear = self.rect.copy()
            playerNear.x -= 64
            playerNear.y -= 64
            playerNear.width += 64*2
            playerNear.height += 64*2
            if playerNear.colliderect(sprites[0].rect):
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
                    self.set_animation("playerNear")
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


    def update(self,tick):
        player = self.extraArgs["player"]-1
        if keyboard[player]["pause"]:
            pause()
        if newKeyboard[player]["reset"]:
            reset()
            return
        if not self.extraArgs["dead"] and not self.extraArgs["won"]:
            if keyboard[player]["up"]:
                self.projected_direction = 0
            elif keyboard[player]["down"]:
                self.projected_direction = 2
            elif keyboard[player]["left"]:
                self.projected_direction = 3
            elif keyboard[player]["right"]:
                self.projected_direction = 1
            if not self.fSpeed:
                if self.direction != self.projected_direction:
                    self.direction = self.projected_direction
                    self.set_animation("look",self.direction)
                if (keyboard[player]["action"] or userPrefs["automaticMovement"] == 1) and (self.direction is not None and frameN != 0):
                    movedRect = self.rect.move([1 if self.direction == 1 else -1 if self.direction == 3 else 0,1 if self.direction == 2 else -1 if self.direction == 0 else 0])
                    rects = [s.rect for s in sprites if not any((s == self,not s.extraArgs["tangable"],s.extraArgs["key"],(s.extraArgs["goal"] and not s.extraArgs["locked"])))] + [t.rect for t in terrains]
                    collides = movedRect.collidelistall(rects)
                    if (terrainSurface.get_rect().contains(movedRect)) and not collides:
                        self.fSpeed = 40
                        self.startup = 15
                        self.set_animation("go",self.direction)
                    else:
                        self.image = self.images["idle"]
                        self.direction = None
                        self.projected_direction = None
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
            self.rect = self.rect.move([round(self.speed[0]),round(self.speed[1])])
            binds = []
            self.rect.top,binded = bind(self.rect.top,size[1],0)
            binds.append(binded)
            self.rect.left,binded = bind(self.rect.left,size[0],0)
            binds.append(binded)
            self.rect.bottom,binded = bind(self.rect.bottom,size[1],0)
            binds.append(binded)
            self.rect.right,binded = bind(self.rect.right,size[0],0)
            binds.append(binded)
            binds = self.collisions(binds)
            if any(binds):
                self.speed = [0,0]
                self.fSpeed = 0
                if not self.animation:
                    self.set_animation("collide")
            self.startup -= 0.5 if self.startup > 1 else 0
            self.extraArgs["pushed"] = None
        super().update(tick)

    def collisions(self,binds):
        global collectedKeys
        spritesNoMe = [sprite for sprite in sprites if sprite != self and (sprite.extraArgs["tangable"] and not sprite.extraArgs["dead"])]
        rects = [sprite.rect for sprite in spritesNoMe]
        collides = self.rect.collidelistall(rects)
        if collides:
            for collision in collides:
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
                if self.fSpeed:
                    binds.append(True)
                    if self.direction == 0: #up
                        self.rect.top = rects[collision].bottom
                    elif self.direction == 1: #right
                        self.rect.right = rects[collision].left
                    elif self.direction == 2: #down
                        self.rect.bottom = rects[collision].top
                    elif self.direction == 3: #left
                        self.rect.left = rects[collision].right
                    spritesNoMe[collision].startup = 30
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

    def update(self,tick):
        if not self.extraArgs["dead"]:
            if self.pathCooldown:
                self.pathCooldown -= 1
            else:
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
                        self.pathIndexDir = 1
                    self.startup = self.extraArgs["pathStartup"]
                    self.pathIndex = self.pathIndex + 1 if self.pathIndexDir == 0 else self.pathIndex - 1
                    self.pathCooldown = self.extraArgs["pathCooldown"]
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
        print(f"Time on level {self.level}: {self.time_readable(self.levelTime)}")

    def time_readable(self,time):
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
        return f"{hour}:{minute}:{second}.{time}"
        

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
    global staticSurface, levelData, prevGridPos, previousMouse, levelName, bg, spriteTypes

    with open(f"levels/{levelName}.json","r") as f:
        levelData = json.load(f)

    spriteTypes = {"none": Sprite,"player": PlayerSprite,"path": PathSprite}

    staticSurface = pygame.Surface(screenSize)

    x = 0
    y = 0
    tiles = []
    for tile in levelData['level']['background']:
        tile = pygame.image.load(f"assets/background/{tile}.png")
        tiles.append(pygame.transform.scale(tile,(64,64)))
    while y<levelData['level']['size'][1]*64:
        while x<levelData['level']['size'][0]*64:
            staticSurface.blit(random.choice(tiles),(x+24,y+24))
            x += 64
        x = 0
        y += 64

    im = pygame.image.load(f"assets/borders/{levelData['level']['border']}/corner.png")
    im = pygame.transform.scale(im,(6*4,6*4))
    staticSurface.blit(im,(0,0))
    staticSurface.blit(im,(levelData['level']['size'][0]*64+24,0))
    staticSurface.blit(im,(0,levelData['level']['size'][1]*64+24))
    staticSurface.blit(im,(levelData['level']['size'][0]*64+24,levelData['level']['size'][1]*64+24))
    im = pygame.image.load(f"assets/borders/{levelData['level']['border']}/side.png")
    im = pygame.transform.scale(im,(24,64))
    for i in range(levelData['level']['size'][1]):
        staticSurface.blit(im,(0,24+(i*64)))
        staticSurface.blit(im,(levelData['level']['size'][0]*64+24,24+(i*64)))
    im = pygame.image.load(f"assets/borders/{levelData['level']['border']}/top.png")
    im = pygame.transform.scale(im,(64,24))
    for i in range(levelData['level']['size'][0]):
        staticSurface.blit(im,(24+(i*64),0))
        staticSurface.blit(im,(24+(i*64),levelData['level']['size'][1]*64+24))

    if not levelEdit:
        pygame.mouse.set_visible(False)
    else:
        levelEdit.level_reset()

def reset():
    global terrains, sprites, keyboard, terrainSurface, play, levelEdit, collectedKeys, blankKeyboard, newKeyboard

    if pauseMenu.is_enabled():
        pauseMenu.disable()

    collectedKeys = 0

    play = not levelEdit

    terrains = []

    sprites = []

    terrainSurface = pygame.Surface(size,flags=pygame.SRCALPHA) 

    for sprite in levelData["sprites"]:
        if levelEdit:
            levelEdit.editCoords[str(sprite["pos"])] = [None,sprite]
        loadSpriteOrTerrain(sprite,"sprite")

    for terrain in levelData["terrain"]:
        if levelEdit:
            levelEdit.editCoords[str(terrain["pos"])] = [None,terrain]
        loadSpriteOrTerrain(terrain,"terrain")

    blankKeyboard = [{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False,"reset":False},{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False}]
    keyboard = blankKeyboard
    newKeyboard = blankKeyboard

    if timer.level == levelName:
        timer.level_reset()

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

def update(tick):
    global clock, play, levelData, sprites, terrains, terrainSurface, collectedKeys

    newKeyboard = blankKeyboard

    for event in pygame.event.get():
        if event.type == pygame.QUIT: close()
        if event.type == pygame.KEYDOWN: # KEY
            timer.start()
            for i in range(len(vars.binds)):
                if event.key in vars.binds[i]:
                    keyboard[i][vars.binds[i][event.key]] = True
                    newKeyboard[i][vars.binds[i][event.key]] = True
        if event.type == pygame.KEYUP:
            for i in range(len(vars.binds)):
                if event.key in vars.binds[i]:
                    keyboard[i][vars.binds[i][event.key]] = False
                    newKeyboard[i][vars.binds[i][event.key]] = False
    
    screen.fill((0,0,0))

    if levelEdit and play:
        if pygame.key.get_pressed()[pygame.K_o]:
            play = False
            reset()

    if not sprites[0].extraArgs["dead"]:
        [terrain.do_animation() for terrain in terrains if terrain.animation]
    
    screen.blit(staticSurface,(0,0))

    screen.blit(terrainSurface,(24,24)) # THIS IS WHERE SCREEN SCROLL WOULD GO!

    if levelEdit and not play:
        screen.blit(levelEdit.editSurface,(0,0),special_flags=pygame.BLEND_ADD)
        selectedIm,play = levelEdit.update(levelData,sprites,terrains,terrainSurface,loadSpriteOrTerrain)
        if selectedIm:
            screen.blit(selectedIm[0],selectedIm[1])

    for sprite in sorted(sprites[1:]): # SPRITES
        if play and not (sprites[0].extraArgs["dead"] or sprites[0].extraArgs["won"]):
            sprite.update(tick)
        scrollPos = (list(sprite.rect.topleft)[0]+24-0, list(sprite.rect.topleft)[1]+24-0) # THIS IS ALSO WHERE SCREEN SCROLL WOULD GO!
        screen.blit(sprite.image,scrollPos)

    if (play and not (sprites[0].extraArgs["dead"] or sprites[0].extraArgs["won"]) and not frameN == 0):
        timer.update(tick)

    if play:
        sprites[0].update(tick)
    scrollPos = (list(sprites[0].rect.topleft)[0]+24-0, list(sprites[0].rect.topleft)[1]+24-0) # THIS IS ALSO WHERE SCREEN SCROLL WOULD GO!
    screen.blit(sprites[0].image,scrollPos)

    font = pygame.font.SysFont("Arial",200)

    if sprites[0].extraArgs["won"]:
        text = font.render("Congratulations!",True,(255,255,255))
        text_rect = text.get_rect()
        screen.blit(text,(70,70))

    font = pygame.font.SysFont("Arial",30)

    if levelData['level']['keys']:
        text = font.render(f"Keys: {collectedKeys}/{levelData['level']['keys']}",True,(255,255,255))
        screen.blit(text,(0,0))

    if levelEdit:
        text = font.render(str(levelEdit.mousePos),True,(255,255,255))
        screen.blit(text,(0,0))

    text = font.render(f"L: {timer.time_readable(timer.levelTime)} - O: {timer.time_readable(timer.time)}",True,(255,255,255))
    screen.blit(text,(0,700))

    if debug and sprites[0].extraArgs["player"]:
        text = font.render(f"Frame: {frameN} ps {clock.get_fps():.2f} | Pos: x {sprites[0].rect.x} y {sprites[0].rect.y} | Dir: {sprites[0].direction} pr {sprites[0].projected_direction} | Edges: T {sprites[0].rect.top} L {sprites[0].rect.left} R {sprites[0].rect.right} B {sprites[0].rect.bottom} | Speed: f {sprites[0].fSpeed} - {sprites[0].speed} su {sprites[0].startup} | Ani: {sprites[0].animationFrame} {sprites[0].animation} | {sprites[0].extraArgs}",True,(255,0,0))
        screen.blit(text,(0,40))

pauseMenu = pygame_menu.Menu('Paused.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK)
pauseMenu.add.button('Continue', unpause)
pauseMenu.add.button('Reset Level', reset)
pauseMenu.add.button('Main Menu',returnToMainMenu)
pauseMenu.add.button('Quit Game', pygame_menu.events.EXIT)
pauseMenu.disable()

levelName = None
if not os.path.exists(prefsPath):
    with open("defaultUserPrefs.json","r") as f2:
        userPrefs = json.load(f2)
    with open(prefsPath,"w+") as f:
        json.dump(userPrefs,f,indent=4)
else:
    with open(prefsPath,"r") as f:
        userPrefs = json.load(f)

def select_level(selectedlevel, *args, **kwargs):
    global levelName
    levelName = selectedlevel[0][0]

def update_prefs():
    with open(prefsPath,"w+") as f:
        json.dump(userPrefs,f,indent=4)
    apply.set_border(0,(20,150,25))

def light_apply():
    try:
        apply.set_border(2,(20,150,25))
    except:
        pass #cry

def set_level_complete_action(levelCompleteAction, *args, **kwargs):
    userPrefs["levelCompleteAction"] = levelCompleteAction[1]
    light_apply()

def set_timer_start(timerStart, *args, **kwargs):
    userPrefs["timerStart"] = timerStart[1]
    light_apply()

def set_automatic_movement(automaticMovement, *args, **kwargs):
    userPrefs["automaticMovement"] = automaticMovement[1]
    light_apply()

preferencesMenu = pygame_menu.Menu('Preferences.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK)
preferencesMenu.add.selector("On level complete ", [("Next level",0),("Main Menu",1),("Reset Level",2)],onchange=set_level_complete_action,default=userPrefs["levelCompleteAction"])
preferencesMenu.add.selector("Timer start ",[("On Level Load",0),("On First Input",1)],onchange=set_timer_start,default=userPrefs["timerStart"])
preferencesMenu.add.selector("Movement ",[("Require Action Button",0),("On Direction Press",1)],onchange=set_automatic_movement,default=userPrefs["automaticMovement"])
apply = preferencesMenu.add.button("Apply", update_prefs)
preferencesMenu.add.button("Back", pygame_menu.events.BACK)

menu = pygame_menu.Menu('Game.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK)
menu.add.button('Play Game', start)
levels = list(list(os.walk("levels"))[0][2])
levels = [f[:-5] for f in levels]
levelName = levels[0]
menu.add.dropselect("Level", [(f,f) for f in levels],onchange=select_level,dropselect_id="levelSelect",default=0,placeholder_add_to_selection_box=False,selection_box_width=350,selection_box_height=500,selection_box_bgcolor=(148, 148, 148),selection_option_selected_bgcolor=(120, 120, 120),selection_box_arrow_color=(255,255,255),selection_option_selected_font_color=(250,250,250),selection_option_font_color=(255,255,255))
menu.add.button('Preferences',preferencesMenu)
menu.add.button('Quit Game', close)
menu.mainloop(screen)
