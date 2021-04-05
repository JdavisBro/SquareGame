import math
import json

import pygame

import vars

class LevelEditor():
    def __init__(self,scr,siz):
        global screenSize, size
        screenSize = scr
        size = siz

    def update(self,levelData,sprites,terrains,terrainSurface,loadSpriteOrTerrain):
        if self.selected in self.levelEditAssets.keys():
            self.selectedIm[1].x = self.levelEditAssets[self.selected].x
            self.selectedIm[1].y = self.levelEditAssets[self.selected].y
        mouse = pygame.mouse.get_pressed(3)
        if any(mouse):
            mouseRect = pygame.Rect(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],1,1)
            clicked = mouseRect.collidelist(list(self.levelEditAssets.values()))
            if clicked != -1 and mouse[0]:
                if list(self.levelEditAssets.keys())[clicked] == "save":
                    if not self.previousMouse[0]:
                        with open("out.json","w+") as f:
                            json.dump(levelData,f,indent=4)
                    self.previousMouse = mouse
                    return self.selectedIm,False
                self.selected = list(self.levelEditAssets.keys())[clicked]
                self.prevGridPos = [-1,-1]
            else:
                mouseRect.topleft = (mouseRect.x-24,mouseRect.y-24)
                if (mouseRect.x <= size[0] and self.selected) and mouse[0]:
                    gridPos = []
                    gridPos.append(math.floor(mouseRect.x / 64))
                    gridPos.append(math.floor(mouseRect.y / 64))
                    if gridPos != self.prevGridPos:
                        self.prevGridPos = gridPos.copy()
                        gridPos[0] = gridPos[0]*64
                        gridPos[1] = gridPos[1]*64
                        if (str(gridPos) in self.editCoords):
                            if [terrain for terrain in terrains if [terrain.rect.x,terrain.rect.y] == gridPos]:
                                terrainSurface.fill((0,0,0,0),self.editCoords[str(gridPos)][0].rect)
                                terrains.remove([terrain for terrain in terrains if [terrain.rect.x,terrain.rect.y] == gridPos][0])
                            elif [sprite for sprite in sprites if [sprite.rect.x,sprite.rect.y] == gridPos]:
                                sprites.remove([sprite for sprite in sprites if [sprite.rect.x,sprite.rect.y] == gridPos][0])
                            if self.editCoords[str(gridPos)][1] in levelData["terrain"]:
                                levelData["terrain"].remove(self.editCoords[str(gridPos)][1])
                            elif self.editCoords[str(gridPos)][1] in levelData["sprites"]:
                                levelData["sprites"].remove(self.editCoords[str(gridPos)][1])
                            self.editCoords.pop(str(gridPos))
                        if self.selected == "eraser":
                            return self.selectedIm,False
                        if self.selected in vars.sprites:
                            levelData["sprites"].append({"image":vars.images[vars.sprites[self.selected]]["idle"],"extraImages": vars.sprites[self.selected],"assetPath":self.selected,"pos":gridPos})
                            self.editCoords[str(gridPos)] = [None,levelData["sprites"][-1]]
                            loadSpriteOrTerrain({"image":vars.images[vars.sprites[self.selected]]["idle"],"extraImages": vars.sprites[self.selected],"assetPath":self.selected,"pos":gridPos},"sprite")
                        if self.selected in vars.terrains:
                            levelData["terrain"].append({"image":vars.images[vars.terrains[self.selected]][0],"assetPath":self.selected,"pos":gridPos})
                            self.editCoords[str(gridPos)] = [None,levelData["terrain"][-1]]
                            loadSpriteOrTerrain({"image":vars.images[vars.terrains[self.selected]][0],"assetPath":self.selected,"pos":gridPos},"terrain")
        play = False
        if pygame.key.get_pressed()[pygame.K_p]:
            play = True
        self.previousMouse = mouse
        return self.selectedIm,play

    def level_reset(self):
        self.prevGridPos = [-1,-1]
        self.editCoords = {}
        self.editSurface = pygame.Surface((screenSize[0]+500,screenSize[1]))
        tiled = pygame.image.load("assets/tile.png")
        self.editSurface.blit(tiled,(24,24))
        self.selectedIm = []
        self.selectedIm.append(pygame.image.load("assets/selected.png"))
        self.selectedIm.append(self.selectedIm[0].get_rect())
        self.selected = None
        self.levelEditAssets = {}
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
            rect.x = screenSize[0]+32+numDone*32
            rect.y = line*32
            self.levelEditAssets[sprite] = rect
            self.editSurface.blit(im,rect)
            numDone += 1
        for terrain in vars.terrains.keys():
            if numDone == 31:
                numDone = 0
                line += 1
            im = pygame.image.load(terrain+(vars.images[vars.terrains[terrain]][0]))
            rect = im.get_rect()
            im = pygame.transform.scale(im,(rect.width*2,rect.height*2))
            rect = im.get_rect()
            rect.x = screenSize[0]+32+numDone*32
            rect.y = line*32
            self.levelEditAssets[terrain] = rect
            self.editSurface.blit(im,rect)
            numDone += 1
        if numDone == 31:
            numDone = 0
            line += 1
        im = pygame.image.load("assets/eraser.png")
        rect = im.get_rect()
        rect.x = screenSize[0]+32+numDone*32
        rect.y = line*32
        self.levelEditAssets["eraser"] = rect
        self.editSurface.blit(im,rect)
        im = pygame.image.load("assets/save.png")
        rect = im.get_rect()
        rect.topleft = [1516,672]
        self.levelEditAssets["save"] = rect
        self.previousMouse = pygame.mouse.get_pressed(3)
        self.editSurface.blit(im,rect)
