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

debug = True if "debug" in sys.argv else False

pygame.init()

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
    def __init__(self,image,pos=[0,0],assetPath="assets/terrain/",scale=4,animation=None):
        global levelEdit
        self.image = pygame.image.load(assetPath+image)
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image,(self.rect.width*scale,self.rect.height*scale))
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        if animation:
            animation = vars.animations[animation]
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
        if animations:
            self.animations = vars.animations[animations]
            self.set_animation("idle")
        else:
            self.animations = None
        self.aliveFrames = 0
        self.extraArgs = {"dead":False,"player":False,"tangable":True,"kill":False,"killable":False,"movable":False,"key":False,"goal":False,"locked":False,"won":False,"path":None,"pathSpeed":1,"pathStartup":1,"pushed":False,"blitImage":None} # Default Args
        self.extraArgs.update(extraArgs) # Add args to defaults
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
        if self.animationFrame >= len(self.animation):
            if not self.animationTimeout[1] and self.animationTimeout[0] != -1:
                self.animationTimeout[1] = True
                self.animationTimeout[0] = self.aliveFrames + self.animationTimeout[0]
            if self.animationTimeout[1] and self.animationTimeout[0] > self.aliveFrames:
                return
            if self.extraArgs["dead"] and self.extraArgs["player"]:
                reset()
            if self.extraArgs["won"]:
                if levelEdit:
                    reset()
                elif levels.index(levelName) == len(levels)-1:
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
                self.animation = self.animations["idle"]
        else:
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
            if anim != "reset":
                if self.extraArgs["goal"]:
                    print(f"uuhh, animation '{anim}' asked for but not found (issue???)")
            self.animation = []

    def kill(self):
        if not self.extraArgs["dead"] and self.extraArgs["player"]:
            self.extraArgs["dead"] = True
            self.set_animation("death")
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
                if keyboard[player]["action"] and (self.direction is not None):
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
        spritesNoMe = [sprite for sprite in sprites if sprite != self]
        rects = [sprite.rect for sprite in spritesNoMe if sprite.extraArgs["tangable"]]
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
        if self.pathCooldown:
            self.pathCooldown -= 1
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
        if self.moving != direction:
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
        spritesNoMe = [sprite for sprite in sprites if sprite != self]
        rects = [sprite.rect for sprite in spritesNoMe if sprite.extraArgs["tangable"]]
        collides = self.rect.collidelistall(rects)
        if collides:
            for collision in collides:
                if self.extraArgs["kill"] and spritesNoMe[collision].extraArgs["killable"]:
                    spritesNoMe[collision].kill()
                    return
                if isinstance(spritesNoMe[collision],PlayerSprite) and not spritesNoMe[collision].extraArgs["dead"]:
                    if ((move[0] if move[0] > 0 else move[0]*-1) > (move[1] if move[1] > 0 else move[1]*-1)):
                        if move[0] >= 0:
                            spritesNoMe[collision].rect.left = self.rect.right
                        else:
                            spritesNoMe[collision].rect.right = self.rect.left
                    else:
                        if move[1] >= 0:
                            spritesNoMe[collision].rect.top = self.rect.bottom
                        else:
                            spritesNoMe[collision].rect.bottom = self.rect.top
                    binds = []
                    spritesNoMe[collision].rect.top,binded = bind(spritesNoMe[collision].rect.top,size[1],0)
                    binds.append(binded)
                    spritesNoMe[collision].rect.left,binded = bind(spritesNoMe[collision].rect.left,size[0],0)
                    binds.append(binded)
                    spritesNoMe[collision].rect.bottom,binded = bind(spritesNoMe[collision].rect.bottom,size[1],0)
                    binds.append(binded)
                    spritesNoMe[collision].rect.right,binded = bind(spritesNoMe[collision].rect.right,size[0],0)
                    binds.append(binded)
                    if spritesNoMe[collision].rect.collidelistall([t.rect for t in terrains] + [s.rect for s in sprites if all([s.extraArgs["tangable"],not (s.extraArgs["goal"] and not s.extraArgs["locked"]),not s.extraArgs["key"], s != self, s != spritesNoMe[collision]])]):
                        binds.append(True)
                    if any(binds):
                        spritesNoMe[collision].kill()

def start():
    global clock,frameN,goMainMenu,levelName,levelChange
    if not levelName:
        return
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

    terrainSurface = pygame.Surface(size) 

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
        if event.type == pygame.QUIT: sys.exit() # SYS
        
        if event.type == pygame.KEYDOWN: # KEY
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

    screen.blit(terrainSurface,(24,24),special_flags=pygame.BLEND_RGBA_MAX) # THIS IS WHERE SCREEN SCROLL WOULD GO!

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

def select_level(selectedlevel, *args, **kwargs):
    global levelName
    levelName = selectedlevel[0][0]

menu = pygame_menu.Menu('Game.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK)
menu.add.button('Play Game', start)
levels = list(list(os.walk("levels"))[0][2])
levels = [f[:-5] for f in levels]
levelName = levels[0]
menu.add.dropselect("Level", [(f,f) for f in levels],onchange=select_level,dropselect_id="levelSelect",default=0,placeholder_add_to_selection_box=False,selection_box_width=350,selection_box_height=500,selection_box_bgcolor=(148, 148, 148),selection_option_selected_bgcolor=(120, 120, 120),selection_box_arrow_color=(255,255,255),selection_option_selected_font_color=(250,250,250),selection_option_font_color=(255,255,255))
menu.add.button('Quit Game', pygame_menu.events.EXIT)
menu.mainloop(screen)
