# Built In
import json
import math
import os
import random
import sys

# External
import pygame
import pygame_menu

# Local
import vars

debug = True if "debug" in sys.argv else False

levelEdit = True if "levelEdit" in sys.argv else False

pygame.init()

size = (1280, 704) #playfield
screenSize = (size[0]+48,size[1]+48)
bg = 0, 0, 0

pygame.display.set_caption("Game.")

icon = pygame.image.load("assets/guy/lookRight2.png")

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
    def __init__(self,image,pos=[0,0],assetPath="assets/terrain/",scale=4,animation=[]):
        global levelEdit, editCoords
        self.image = pygame.image.load(assetPath+image)
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image,(self.rect.width*scale,self.rect.height*scale))
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        if animation:
            self.animation = [pygame.transform.scale(pygame.image.load(assetPath+im),(self.rect.width,self.rect.height)) for im in animation]
        else:
            self.animation = None
        self.animationFrame = 0
        self.animationFrames = 0
        terrainSurface.blit(self.image,self.rect)
        terrains.append(self)
        if levelEdit:
            editCoords[str(list(self.rect.topleft))][0] = self

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
        acceleration=0.25,update=None,
        spriteType="static",extraImages={},
        extraArgs={},animations=[],
        weight=0
        ):
        global levelEdit, editCoords
        self.image = pygame.image.load(assetPath+image) # Image & Rect
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image,(self.rect.width*scale,self.rect.height*scale))
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.speed = [0,0] # Speed
        self.fSpeed = 0
        self.sprite_update = update # Sprite
        self.direction = random.randint(0,3)
        self.projected_direction = self.direction
        self.type = spriteType
        self.images = {} # Animations
        self.animations = animations
        self.set_animation("reset")
        self.aliveFrames = 0
        self.extraArgs = {"dead":False,"player":False,"tangable":True,"kill":False,"killable":False,"movable":False,"goal":False,"won":False,"path":None,"pathSpeed":1,"pathStartup":1,"pushed":False} # Default Args
        self.extraArgs.update(extraArgs) # Add args to defaults
        if extraImages:
            self.images["idle"] = self.image
            for im in extraImages:
                if im != "idle":
                    self.images[im] = pygame.transform.scale(pygame.image.load(assetPath+extraImages[im]),(self.rect.width,self.rect.height))
        self.weight = weight
        if spriteType == "motion":
            self.acceleration = acceleration
            self.startup = 1
        if spriteType == "path":
            self.pathIndex = 0
            self.startup = self.extraArgs["pathStartup"]
            self.pathIndexDir = 0
            self.pathCooldown = self.extraArgs["pathCooldown"]
        sprites.append(self)
        if levelEdit:
            editCoords[str(list(self.rect.topleft))][0] = self

    def __lt__(self,other):
        return (self.weight < other.weight) and (vars.typeHierarchy[self.type] < vars.typeHierarchy[other.type])

    def update(self,tick):
        global frameN
        self.aliveFrames += 1
        if not ((self.extraArgs["dead"] and self.extraArgs["player"]) or (self.extraArgs["won"])):
            if self.sprite_update:
                self.sprite_update(self,tick)
            if self.type == "motion":
                self.motion_update(tick)
            elif self.type == "path":
                self.path_update(tick)
        self.do_animations()

    def motion_update(self,tick):
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
            binds = self.motion_collisions(binds)
            if any(binds):
                self.speed = [0,0]
                self.fSpeed = 0
                if not self.animation:
                    self.set_animation("collide")
            self.startup -= 0.5 if self.startup > 1 else 0

    def path_update(self,tick):
        if self.pathCooldown:
            self.pathCooldown -= 1
            return
        pathDifference = [self.extraArgs["path"][self.pathIndex][0]-list(self.rect.topleft)[0],self.extraArgs["path"][self.pathIndex][1]-list(self.rect.topleft)[1]]
        movement = self.extraArgs["pathSpeed"]/self.startup*tick
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
        if not move[0] and not move[1]:
            if self.pathIndex == 0 and self.pathIndexDir == 1:
                self.pathIndexDir = 0
            elif self.pathIndex == len(self.extraArgs["path"])-1 and self.pathIndexDir == 0:
                self.pathIndexDir = 1
            self.startup = self.extraArgs["pathStartup"]
            self.pathIndex = self.pathIndex + 1 if self.pathIndexDir == 0 else self.pathIndex - 1
            self.pathCooldown = self.extraArgs["pathCooldown"]
        self.startup -= 0.5 if self.startup > 1 else 0
        self.path_collision(move)

    def motion_collisions(self,binds):
        spritesNoMe = [sprite for sprite in sprites if sprite != self]
        rects = [sprite.rect for sprite in spritesNoMe if sprite.extraArgs["tangable"]]
        collides = self.rect.collidelistall(rects)
        if collides:
            for collision in collides:
                if spritesNoMe[collision].extraArgs["goal"] and self.extraArgs["player"]:
                    self.set_animation("celebrate")
                    self.extraArgs["won"] = True
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
            if self.extraArgs["pushed"]:
                self.kill()
                return [True]
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
        self.extraArgs["pushed"] = False
        return binds

    def path_collision(self,move):
        spritesNoMe = [sprite for sprite in sprites if sprite != self]
        rects = [sprite.rect for sprite in spritesNoMe if sprite.extraArgs["tangable"]]
        collides = self.rect.collidelistall(rects)
        if collides:
            for collision in collides:
                if self.extraArgs["kill"] and spritesNoMe[collision].extraArgs["killable"]:
                    spritesNoMe[collision].kill()
                    return
                if spritesNoMe[collision].type == "motion":
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
                    spritesNoMe[collision].extraArgs["pushed"] = True

    def do_animations(self):
        global goMainMenu
        if self.animationFrame >= len(self.animation):
            if self.extraArgs["dead"] and self.extraArgs["player"]:
                reset()
            if self.extraArgs["won"]:
                goMainMenu = True
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
                if self.extraArgs["player"]:
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
            rects = [s.rect for s in sprites if s != sprite] + [t.rect for t in terrains]
            collides = movedRect.collidelistall(rects)
            if (terrainSurface.get_rect().contains(movedRect)) and not collides:
                sprite.fSpeed = 40
                sprite.startup = 15
                sprite.set_animation("go",sprite.direction)
            else:
                sprite.image = sprite.images["idle"]
    if keyboard[player]["pause"]:
        pause()

def start():
    global clock,frameN,goMainMenu,levelName
    if not levelName:
        return
    reset_level()
    reset()
    goMainMenu = False
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
    global levelEdit, staticSurface, levelData, editCoords, prevGridPos, levelEditAssets, selected, selectedIm, previousMouse, levelName, editSurface, bg

    with open(f"levels/{levelName}.json","r") as f:
        levelData = json.load(f)

    staticSurface = pygame.Surface(screenSize)

    x = 0
    y = 0
    tile = pygame.image.load(f"assets/background/{levelData['level']['background']}.png")
    tile = pygame.transform.scale(tile,(64,64))
    while y<levelData['level']['size'][1]*64:
        while x<levelData['level']['size'][0]*64:
            staticSurface.blit(tile,(x+24,y+24))
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
        prevGridPos = [-1,-1]
        editCoords = {}
        editSurface = pygame.Surface((screenSize[0]+500,screenSize[1]))
        tiled = pygame.image.load("assets/tile.png")
        editSurface.blit(tiled,(24,24))
        selectedIm = []
        selectedIm.append(pygame.image.load("assets/selected.png"))
        selectedIm.append(selectedIm[0].get_rect())
        selected = None
        levelEditAssets = {}
        numDone = 0
        line = 0
        for sprite in vars.sprites.keys():
            if numDone == 31:
                numDone = 0
                line += 1
            im = pygame.image.load(sprite+(vars.images[vars.sprites[sprite]]["idle"]))
            rect = im.get_rect()
            im = pygame.transform.scale(im,(rect.width*2,rect.height*2))
            rect = im.get_rect()
            rect.x = size[0]+numDone*32
            rect.y = line*32
            levelEditAssets[sprite] = rect
            editSurface.blit(im,rect)
            numDone += 1
        for terrain in vars.terrains.keys():
            if numDone == 31:
                numDone = 0
                line += 1
            im = pygame.image.load(terrain+(vars.images[vars.terrains[terrain]][0]))
            rect = im.get_rect()
            im = pygame.transform.scale(im,(rect.width*2,rect.height*2))
            rect = im.get_rect()
            rect.x = size[0]+numDone*32
            rect.y = line*32
            levelEditAssets[terrain] = rect
            editSurface.blit(im,rect)
            numDone += 1
        if numDone == 31:
            numDone = 0
            line += 1
        im = pygame.image.load("assets/eraser.png")
        rect = im.get_rect()
        rect.x = size[0]+numDone*32
        rect.y = line*32
        levelEditAssets["eraser"] = rect
        editSurface.blit(im,rect)
        im = pygame.image.load("assets/save.png")
        rect = im.get_rect()
        rect.topleft = [1516,672]
        levelEditAssets["save"] = rect
        previousMouse = pygame.mouse.get_pressed(3)
        editSurface.blit(im,rect)

def reset():
    global terrains, sprites, keyboard, terrainSurface, updates, play, editCoords, levelEdit

    play = not levelEdit

    updates = {"player":player_update}

    terrains = []

    sprites = []

    terrainSurface = pygame.Surface(size) 

    for sprite in levelData["sprites"]:
        if levelEdit:
            editCoords[str(sprite["pos"])] = [None,sprite]
        loadSpriteOrTerrain(sprite,"sprite")

    for terrain in levelData["terrain"]:
        if levelEdit:
            editCoords[str(terrain["pos"])] = [None,terrain]
        loadSpriteOrTerrain(terrain,"terrain")

    keyboard = [{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False},{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False}]

def loadSpriteOrTerrain(data,stype):
    data = data.copy()
    if stype == "sprite":
        if "update" in data.keys():
            if type(data["update"]) == str:
                data["update"] = updates[data["update"]]
        if "extraImages" in data.keys():
            if type(data["extraImages"]) == str:
                data["extraImages"] = vars.images[data["extraImages"]]
        if "animations" in data.keys():
            if type(data["animations"]) == str:
                data["animations"] = vars.animations[data["animations"]]
        Sprite(**data)
    else:
        if "animation" in data.keys():
            data["animations"] = vars.animations[data["animation"]]
        Terrain(**data)

def levelEditor():
    global selected, selectedIm, prevGridPos, editCoords, levelEditAssets, play, previousMouse
    if selected in levelEditAssets.keys():
        selectedIm[1].x = levelEditAssets[selected].x
        selectedIm[1].y = levelEditAssets[selected].y
        screen.blit(selectedIm[0],selectedIm[1])
    mouse = pygame.mouse.get_pressed(3)
    if any(mouse):
        mouseRect = pygame.Rect(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],1,1)
        clicked = mouseRect.collidelist(list(levelEditAssets.values()))
        if clicked != -1 and mouse[0]:
            if list(levelEditAssets.keys())[clicked] == "save":
                if not previousMouse[0]:
                    with open("out.json","w+") as f:
                        json.dump(levelData,f,indent=4)
                previousMouse = mouse
                return
            selected = list(levelEditAssets.keys())[clicked]
            prevGridPos = [-1,-1]
        else:
            if (mouseRect.x <= size[0] and selected) and mouse[0]:
                gridPos = []
                gridPos.append(math.floor(mouseRect.x / 64))
                gridPos.append(math.floor(mouseRect.y / 64))
                if gridPos != prevGridPos:
                    prevGridPos = gridPos.copy()
                    gridPos[0] = gridPos[0]*64
                    gridPos[1] = gridPos[1]*64
                    if (str(gridPos) in editCoords):
                        if [terrain for terrain in terrains if [terrain.rect.x,terrain.rect.y] == gridPos]:
                            terrainSurface.fill((0,0,0,0),editCoords[str(gridPos)][0].rect)
                            terrains.remove([terrain for terrain in terrains if [terrain.rect.x,terrain.rect.y] == gridPos][0])
                        elif [sprite for sprite in sprites if [sprite.rect.x,sprite.rect.y] == gridPos]:
                            sprites.remove([sprite for sprite in sprites if [sprite.rect.x,sprite.rect.y] == gridPos][0])
                        if editCoords[str(gridPos)][1] in levelData["terrain"]:
                            levelData["terrain"].remove(editCoords[str(gridPos)][1])
                        elif editCoords[str(gridPos)][1] in levelData["sprites"]:
                            levelData["sprites"].remove(editCoords[str(gridPos)][1])
                        editCoords.pop(str(gridPos))
                    if selected == "eraser":
                        return
                    if selected in vars.sprites:
                        levelData["sprites"].append({"image":vars.images[vars.sprites[selected]]["idle"],"extraImages": vars.sprites[selected],"assetPath":selected,"pos":gridPos})
                        editCoords[str(gridPos)] = [None,levelData["sprites"][-1]]
                        loadSpriteOrTerrain({"image":vars.images[vars.sprites[selected]]["idle"],"extraImages": vars.sprites[selected],"assetPath":selected,"pos":gridPos},"sprite")
                    if selected in vars.terrains:
                        levelData["terrain"].append({"image":vars.images[vars.terrains[selected]][0],"assetPath":selected,"pos":gridPos})
                        editCoords[str(gridPos)] = [None,levelData["terrain"][-1]]
                        loadSpriteOrTerrain({"image":vars.images[vars.terrains[selected]][0],"assetPath":selected,"pos":gridPos},"terrain")
    if pygame.key.get_pressed()[pygame.K_p]:
        play = True
    previousMouse = mouse

def update(tick):
    global clock, play

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
    
    screen.fill((0,0,0))

    if levelEdit and play:
        if pygame.key.get_pressed()[pygame.K_o]:
            play = False
            reset()

    [terrain.do_animation() for terrain in terrains if terrain.animation]
    
    screen.blit(staticSurface,(0,0))

    screen.blit(terrainSurface,(24,24),special_flags=pygame.BLEND_MAX) # THIS IS WHERE SCREEN SCROLL WOULD GO!

    if levelEdit and not play:
        screen.blit(editSurface,(0,0),special_flags=pygame.BLEND_ADD)
        levelEditor()

    for sprite in sorted(sprites[1:]): # SPRITES
        if play:
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
        text_rect.left += 70
        text_rect.top += 70
        screen.blit(text,text_rect)

    font = pygame.font.SysFont("Arial",20)

    if debug and sprites[0].extraArgs["player"]:
        text = font.render(f"Frame: {frameN} ps {clock.get_fps():.2f} | Pos: x {sprites[0].rect.x} y {sprites[0].rect.y} | Dir: {sprites[0].direction} pr {sprites[0].projected_direction} | Edges: T {sprites[0].rect.top} L {sprites[0].rect.left} R {sprites[0].rect.right} B {sprites[0].rect.bottom} | Speed: f {sprites[0].fSpeed} - {sprites[0].speed} su {sprites[0].startup} | Ani: {sprites[0].animationFrame} {sprites[0].animation} | {sprites[0].extraArgs}",True,(255,0,0))
        text_rect = text.get_rect()
        text_rect.left += 70
        text_rect.top += 70
        screen.blit(text,text_rect)

pauseMenu = pygame_menu.Menu('Paused.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK)
pauseMenu.add.button('Continue', unpause)
pauseMenu.add.button('Main Menu',returnToMainMenu)
pauseMenu.add.button('Quit', pygame_menu.events.EXIT)
pauseMenu.disable()

levelName = None

def select_level(selectedlevel, *args, **kwargs):
    global levelName
    levelName = selectedlevel[0][0]

menu = pygame_menu.Menu('Game.',screenSize[0],screenSize[1],theme=pygame_menu.themes.THEME_DARK)
menu.add.button('Play', start)
levels = list(list(os.walk("levels"))[0][2])
levels = [(f[:-5],f[:-5]) for f in levels]
menu.add.dropselect("Level", levels,onchange=select_level)
menu.add.button('Quit', pygame_menu.events.EXIT)
menu.mainloop(screen)
