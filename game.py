import math
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

size = (1280, 704)
bg = 0, 0, 0

pygame.display.set_caption("Game.")

icon = pygame.image.load("assets/guy/lookRight2.png")

pygame.display.set_icon(icon)

if levelEdit:
    screen = pygame.display.set_mode([size[0]+500,size[1]])
else:
    screen = pygame.display.set_mode(size)

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
        self.extraArgs = {"dead":False,"player":False,"tangable":True,"kill":False,"killable":False,"movable":False} # Default Args
        self.extraArgs.update(extraArgs) # Add args to defaults
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
                self.motion_update(tick)
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
            if (screen.get_rect().contains(movedRect)) and not collides:
                sprite.fSpeed = 40
                sprite.startup = 15
                sprite.set_animation("go",sprite.direction)
            else:
                sprite.image = sprite.images["idle"]
    if keyboard[player]["pause"]:
        pause()

def start():
    global clock,frameN,goMainMenu
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
    global levelEdit, staticSurface, levelData, editCoords, prevGridPos, levelEditAssets, selected, selectedIm
    defaultLevelData = {
        "sprites":[
            {"image":"idle.png","assetPath":"assets/guy/","update":"player","animations":"player","spriteType":"motion","extraImages":"player","extraArgs":{"player":1,"killable":True}},
            {"image":"confuzzled3.png","assetPath":"assets/guy2/","pos":[0,200],"extraArgs":{"kill":True}}
            ],
        "terrain":[
            {"image":"0.png","assetPath":"assets/terrain/grass/","pos":[0,448]},
            ],
        }

    if not levelEdit:
        pygame.mouse.set_visible(False)
        levelData = defaultLevelData # this is where i would load the data from file
        staticSurface = pygame.Surface(size)
    else:
        levelData = defaultLevelData
        prevGridPos = [-1,-1]
        editCoords = {}
        staticSurface = pygame.Surface((size[0]+500,size[1]))
        tiled = pygame.image.load("assets/tile.png")
        staticSurface.blit(tiled,(0,0))
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
            staticSurface.blit(im,rect)
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
            staticSurface.blit(im,rect)
            numDone += 1
        if numDone == 31:
            numDone = 0
            line += 1
        im = pygame.image.load("assets/eraser.png")
        rect = im.get_rect()
        rect.x = size[0]+numDone*32
        rect.y = line*32
        levelEditAssets["eraser"] = rect
        staticSurface.blit(im,rect)



def reset():
    global terrains, sprites, keyboard, terrainSurface, updates, play

    play = not levelEdit

    updates = {"player":player_update}

    terrains = []

    sprites = []

    terrainSurface = pygame.Surface(size) 

    for sprite in levelData["sprites"]:
        loadSpriteOrTerrain(sprite,"sprite")

    for terrain in levelData["terrain"]:
        loadSpriteOrTerrain(terrain,"terrain")

    keyboard = [{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False},{"up":False,"down":False,"left":False,"right":False,"action":False,"pause":False}]

def loadSpriteOrTerrain(data,stype):
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
    global selected, selectedIm, prevGridPos, editCoords, levelEditAssets, play
    if selected in levelEditAssets.keys():
        selectedIm[1].x = levelEditAssets[selected].x
        selectedIm[1].y = levelEditAssets[selected].y
        screen.blit(selectedIm[0],selectedIm[1])
    mouse = pygame.mouse.get_pressed(3)
    if any(mouse):
        mouseRect = pygame.Rect(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],1,1)
        clicked = mouseRect.collidelist(list(levelEditAssets.values()))
        if clicked != -1 and mouse[0]:
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
                        loadSpriteOrTerrain({"image":vars.images[vars.sprites[selected]]["idle"],"extraImages": vars.sprites[selected],"assetPath":selected,"pos":gridPos},"sprite")
                        editCoords[str(gridPos)] = [sprites[-1],levelData["sprites"][-1]]
                    if selected in vars.terrains:
                        levelData["terrain"].append({"image":vars.images[vars.terrains[selected]][0],"assetPath":selected,"pos":gridPos})
                        loadSpriteOrTerrain({"image":vars.images[vars.terrains[selected]][0],"assetPath":selected,"pos":gridPos},"terrain")
                        editCoords[str(gridPos)] = [terrains[-1],levelData["terrain"][-1]]
    if pygame.key.get_pressed()[pygame.K_p]:
        play = True

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
    
    screen.fill(bg)

    if levelEdit and not play:
        screen.blit(staticSurface,(0,0))
        levelEditor()

    if levelEdit and play:
        if pygame.key.get_pressed()[pygame.K_o]:
            play = False
            reset()

    [terrain.do_animation() for terrain in terrains if terrain.animation]

    screen.blit(terrainSurface,(0,0),special_flags=pygame.BLEND_RGBA_ADD) # THIS IS WHERE SCREEN SCROLL WOULD GO!

    for sprite in sorted(sprites): # SPRITES
        if play:
            sprite.update(tick)
        scrollPos = (list(sprite.rect.topleft)[0]-0, list(sprite.rect.topleft)[1]-0) # THIS IS ALSO WHERE SCREEN SCROLL WOULD GO!
        screen.blit(sprite.image,scrollPos)

    font = pygame.font.SysFont("Arial",20)

    if debug:
        text = font.render(f"Frame: {frameN} ps {clock.get_fps():.2f} | Pos: x {sprites[0].rect.x} y {sprites[0].rect.y} | Dir: {sprites[0].direction} pr {sprites[0].projected_direction} | Edges: T {sprites[0].rect.top} L {sprites[0].rect.left} R {sprites[0].rect.right} B {sprites[0].rect.bottom} | Speed: f {sprites[0].fSpeed} - {sprites[0].speed} su {sprites[0].startup} | Ani: {sprites[0].animationFrame} {sprites[0].animation} | {sprites[0].extraArgs}",True,(255,0,0))
        text_rect = text.get_rect()
        text_rect.left += 70
        text_rect.top += 70
        screen.blit(text,text_rect)

pauseMenu = pygame_menu.Menu('Paused.',size[0],size[1],theme=pygame_menu.themes.THEME_DARK)
pauseMenu.add.button('Continue', unpause)
pauseMenu.add.button('Main Menu',returnToMainMenu)
pauseMenu.add.button('Quit', pygame_menu.events.EXIT)
pauseMenu.disable()

menu = pygame_menu.Menu('Game.',size[0],size[1],theme=pygame_menu.themes.THEME_DARK)
menu.add.button('Play', start)
menu.add.button('Quit', pygame_menu.events.EXIT)
menu.mainloop(screen)
