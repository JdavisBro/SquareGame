import os
import math
import json
import sys
import copy

import pygame
import pygame_menu

import vars

def bind(value,upper,lower):
    if value > upper:
        return upper, True
    if value < lower:
        return lower, True
    return value, False

class LevelEditor():
    def __init__(self,screenSize,size,screen):
        self.loadSpriteOrTerrain = None
        self.sprites = None
        self.terrains = None
        self.terrainSurface = None
        self.screenSize = screenSize
        self.size = size
        self.screen = screen
        self.posMode = False
        self.posList = False
        self.mousePos = [0,0]
        self.currentlyEditing = None
        self.editMenu = None
        self.backupGuy = None
        self.levelData = None
        self.images = copy.deepcopy(vars.images)
        self.editMenu = pygame_menu.Menu("Edit Sprite.",self.screenSize[0],self.screenSize[1],theme=pygame_menu.themes.THEME_DARK)
        for arg,argType in vars.spriteArgs.items():
            self.add_widget(arg,argType,{"extraArgs":{},"pos":[0,0]},False,True)
        self.editMenu.add.vertical_margin(30)
        for arg,argType in vars.spriteExtraArgs.items():
            self.add_widget(arg,argType,{"extraArgs":{},"pos":[0,0]},True,True)
        self.editMenu.add.button("Apply",self.update_sprite)
        self.editMenu.add.button("Return",self.editMenu.disable)
        self.editMenu.disable()
        self.selectedN = 0

    def update(self,scroll):
        if self.editMenu:
            if self.editMenu.is_enabled():
                self.edit_menu()
        if pygame.key.get_pressed()[pygame.K_RETURN] and isinstance(self.posList,list):
            return self.end_pos_list()
        if self.selected in self.levelEditAssets.keys():
            self.selectedIm[1].x = self.levelEditAssets[self.selected].x
            self.selectedIm[1].y = self.levelEditAssets[self.selected].y+32
        mouse = pygame.mouse.get_pressed(3)
        self.mousePos = ((pygame.mouse.get_pos()[0]-24+scroll[0])//64*64,(pygame.mouse.get_pos()[1]-24+scroll[1])//64*64)
        if any(mouse):
            mouseRect = pygame.Rect(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],1,1)
            clicked = mouseRect.collidelist(list(self.levelEditAssets.values()))
            if clicked != -1 and not self.posMode: # Clicked an asset
                if mouse[0]:
                    oldSel = self.selectedN
                    self.selectedN = 0
                    if oldSel != self.selectedN:
                        self.editSurface.fill((0,0,0),self.levelEditAssets[self.selected])
                        self.editSurface.blit(self.images[vars.terrains[self.selected]][self.selectedN],self.levelEditAssets[self.selected])
                    if list(self.levelEditAssets.keys())[clicked] == "save":
                        if not self.previousMouse[0]:
                            outN = 0
                            while os.path.exists(f"levels/_out{str(outN)}.json"):
                                outN += 1
                            with open(f"levels/_out{str(outN)}.json","w+") as f:
                                json.dump(self.levelData,f,indent=4)
                        self.previousMouse = mouse
                        return self.selectedIm,False
                    self.selected = list(self.levelEditAssets.keys())[clicked]
                    self.prevGridPos = [-1,-1]
                elif (mouse[1] and not self.previousMouse[1]) or (mouse[2] and not self.previousMouse[2]):
                    self.update_asset(mouse)
            else: # Didn't click an asset, could've clicked a grid spot
                mouseRect.topleft = (mouseRect.x-24+scroll[0],mouseRect.y-24+scroll[1])
                if not (bind(mouseRect.x,self.size[0],0)[1] or bind(mouseRect.y,self.size[1],0)[1]): # WE ON DA GRID
                    gridPos = []
                    gridPos.append(mouseRect.x // 64)
                    gridPos.append(mouseRect.y // 64)
                    gridPos[0] = gridPos[0]*64
                    gridPos[1] = gridPos[1]*64
                    if mouse[0]: # Ayo we left clicked on the  grid
                        if gridPos != self.prevGridPos and self.posMode:
                            self.prevGridPos = gridPos.copy()
                            return self.set_pos(gridPos)
                        if gridPos != self.prevGridPos and self.selected:
                            self.prevGridPos = gridPos.copy()
                            if (str(gridPos) in self.editCoords):
                                if [terrain for terrain in self.terrains if [terrain.rect.x,terrain.rect.y] == gridPos]:
                                    self.terrainSurface.fill((0,0,0,0),self.editCoords[str(gridPos)][0].rect)
                                    self.terrains.remove([terrain for terrain in self.terrains if [terrain.rect.x,terrain.rect.y] == gridPos][0])
                                elif [sprite for sprite in self.sprites if [sprite.rect.x,sprite.rect.y] == gridPos]:
                                    self.sprites.remove([sprite for sprite in self.sprites if [sprite.rect.x,sprite.rect.y] == gridPos][0])
                                if self.editCoords[str(gridPos)][1] in self.levelData["terrain"]:
                                    self.levelData["terrain"].remove(self.editCoords[str(gridPos)][1])
                                elif self.editCoords[str(gridPos)][1] in self.levelData["sprites"]:
                                    self.levelData["sprites"].remove(self.editCoords[str(gridPos)][1])
                                self.editCoords.pop(str(gridPos))
                            if self.selected == "eraser":
                                return self.selectedIm,False
                            if self.selected in vars.sprites:
                                self.levelData["sprites"].append({"image":"idle","extraImages": vars.sprites[self.selected],"assetPath":self.selected,"pos":gridPos,"extraArgs": {}})
                                self.editCoords[str(gridPos)] = [None,self.levelData["sprites"][-1].copy(),"sprite"]
                                self.loadSpriteOrTerrain({"image":"idle","extraImages": vars.sprites[self.selected],"assetPath":self.selected,"pos":gridPos,"extraArgs": {}},"sprite")
                            if self.selected in vars.terrains:
                                self.levelData["terrain"].append({"image":self.selectedN,"assetPath":self.selected,"pos":gridPos})
                                self.editCoords[str(gridPos)] = [None,self.levelData["terrain"][-1].copy(),"terrain"]
                                self.loadSpriteOrTerrain({"image":self.selectedN,"assetPath":self.selected,"pos":gridPos},"terrain")
                    elif mouse[2] and not self.posMode: # hol on.. we right clickin
                        if (str(gridPos) in self.editCoords):
                            if self.editCoords[str(gridPos)][2] == "sprite":
                                self.currentlyEditingL = gridPos
                                self.currentlyEditing = str(gridPos)
                                guy = self.editCoords[self.currentlyEditing][1]
                                self.backupGuy = guy.copy()
                                for arg,argType in vars.spriteArgs.items():
                                    self.add_widget(arg,argType,guy)
                                for arg,argType in vars.spriteExtraArgs.items():
                                    self.add_widget(arg,argType,guy,True)
                                self.editMenu.enable()
                                return self.edit_menu()
                elif (mouse[1] and not self.previousMouse[1]) or (mouse[2] and not self.previousMouse[2]):
                    self.update_asset(mouse)
        self.previousMouse = mouse
        return self.selectedIm,(True if pygame.key.get_pressed()[pygame.K_p] else False)

    def update_asset(self,mouse):
        if self.selected in vars.terrains.keys():
            terrain = vars.terrains[self.selected]
            self.selectedN += -1 if mouse[1] and (0 <= self.selectedN-1) else 1 if len(vars.images[terrain])>self.selectedN+1 and mouse[2] else 0
            self.editSurface.fill((0,0,0),self.levelEditAssets[self.selected])
            if not self.check_for_image(terrain,self.selectedN,pygame.Surface):
                if not isinstance(vars.images[terrain][self.selectedN],pygame.Surface):
                    self.images[terrain][self.selectedN] = pygame.image.load(f"{self.selected}{vars.images[terrain][self.selectedN]}")
                else:
                    self.images[terrain][self.selectedN] = vars.images[terrain][self.selectedN]
                self.images[terrain][self.selectedN] = pygame.transform.scale(self.images[terrain][self.selectedN],(32,32))
            self.editSurface.blit(self.images[terrain][self.selectedN],self.levelEditAssets[self.selected])
            self.prevGridPos = [-1,-1]

    def check_for_image(self,thing,index,typeCheck="NOCHECK"):
        if self.images.get(thing):
            if index in self.images[thing]:
                if typeCheck != "NOCHECK": return isinstance(self.images[thing][index],typeCheck)
                else: return True
        else: self.images[thing] = {}
        return False

    def level_reset(self):
        self.prevGridPos = [-1,-1]
        self.editCoords = {}
        self.editSurface = pygame.Surface((self.screenSize[0]+500,self.screenSize[1]),pygame.SRCALPHA)
        self.editStaticSurface = pygame.Surface(self.size,pygame.SRCALPHA)
        self.editSurface.fill((0,0,0),rect=((self.screenSize[0],0),(500,self.screenSize[1])))
        tiled = pygame.image.load("assets/tile.png")
        for y in range(self.size[1]//64):
            for x in range(self.size[0]//64):
                self.editStaticSurface.blit(tiled,(x*64,y*64))
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
            if not isinstance(vars.images[vars.sprites[sprite]]["idle"],pygame.Surface):
                im = pygame.image.load(sprite+(vars.images[vars.sprites[sprite]]["idle"]))
            else:
                im = vars.images[vars.sprites[sprite]]["idle"]
            im = pygame.transform.scale(im,(32,32))
            rect = im.get_rect()
            rect.x = self.screenSize[0]+32+numDone*32
            rect.y = line*32
            self.levelEditAssets[sprite] = rect
            self.editSurface.blit(im,rect)
            numDone += 1
        for terrain in vars.terrains.keys():
            if numDone == 31:
                numDone = 0
                line += 1
            if not self.check_for_image(vars.terrains[terrain],0,pygame.Surface):
                self.images[vars.terrains[terrain]][0] = pygame.image.load(terrain+(vars.images[vars.terrains[terrain]][0]))
                self.images[vars.terrains[terrain]][0] = pygame.transform.scale(self.images[vars.terrains[terrain]][0],(32,32))
            im = self.images[vars.terrains[terrain]][0]
            rect = im.get_rect()
            rect.x = self.screenSize[0]+32+numDone*32
            rect.y = line*32
            self.levelEditAssets[terrain] = rect
            self.editSurface.blit(im,rect)
            numDone += 1
        if numDone == 31:
            numDone = 0
            line += 1
        im = pygame.image.load("assets/eraser.png")
        rect = im.get_rect()
        rect.x = self.screenSize[0]+32+numDone*32
        rect.y = line*32
        self.levelEditAssets["eraser"] = rect
        self.editSurface.blit(im,rect)
        im = pygame.image.load("assets/save.png")
        rect = im.get_rect()
        rect.topleft = [1516,672]
        self.levelEditAssets["save"] = rect
        self.previousMouse = pygame.mouse.get_pressed(3)
        self.editSurface.blit(im,rect)

    def onchange(self,a,b=None,widget=None,*args,**kwargs):
        if isinstance(a,pygame_menu.widgets.Widget):
            widget = a
        elif isinstance(b,pygame_menu.widgets.Widget):
            widget = b
        widget.set_border(2,(20,150,25))

    def add_widget(self,arg,argType,guy,extraArg=False,setup=False):
        wid = ("e!" if extraArg else "") + arg
        if not setup:
            widget = self.editMenu.get_widget(wid)
            if argType[0] == "text":
                value = argType[1] if argType[1] is not None else "N/A"
                value = guy.get(arg,value) if not extraArg else guy["extraArgs"].get(arg,value)
            elif argType[0] == "dropdown":
                value = argType[2] if argType[2] is not None else -1
                value = (guy.get(arg,value) if not extraArg else guy["extraArgs"].get(arg,value))
            elif argType[0] == "toggle":
                value = guy.get(arg,argType[1]) if not extraArg else guy["extraArgs"].get(arg,argType[1])
            elif argType[0] == "float":
                value = argType[1] if argType[1] is not None else 0
                value = guy.get(arg,value) if not extraArg else guy["extraArgs"].get(arg,value)
            else:
                if argType[0] == "pos":
                    value = guy.get(arg,argType[1]) if not extraArg else guy["extraArgs"].get(arg,argType[1])
                    widget.set_title(f"{arg}: {str(value)}")
                return # burn in hell!
            widget.set_value(value)
            return
        if argType[0] == "text":
            default = argType[1] if argType[1] is not None else "N/A"
            default = guy.get(arg,default) if not extraArg else guy["extraArgs"].get(arg,default)
            text_input = self.editMenu.add.text_input(f"{arg}: ",textinput_id=wid,onreturn=self.text_edit,input_underline='_',default=str(default))
            text_input.add_self_to_kwargs()
        elif argType[0] == "pos":
            button = self.editMenu.add.button(f"{arg}: {str(guy.get(arg,'None')) if not extraArg else guy['extraArgs'].get(arg,'None')}",self.pos_mode,argType[1],button_id=wid)
            button.add_self_to_kwargs()
        elif argType[0] == "dropdown":
            default = argType[2] if argType[2] is not None else "NO VALUE"
            index = (guy.get(arg,default) if not extraArg else guy["extraArgs"].get(arg,default))
            if index != "NO VALUE":
                index = argType[1].index(index)
            else:
                index = -1
            values = [(str(i),i) for i in argType[1]]
            dropselect = self.editMenu.add.dropselect(arg,values,dropselect_id=wid,onchange=self.drop_select,default=index)
            dropselect.add_self_to_kwargs()
        elif argType[0] == "toggle":
            default = guy.get(arg,argType[1]) if not extraArg else guy["extraArgs"].get(arg,argType[1])
            toggle_switch = self.editMenu.add.toggle_switch(arg,toggleswitch_id=wid,onchange=self.toggle,default=default)
            toggle_switch.add_self_to_kwargs()
        elif argType[0] == "flint":
            default = argType[1] if argType[1] is not None else 0
            default = guy.get(arg,default) if not extraArg else guy["extraArgs"].get(arg,default)
            text_input = self.editMenu.add.text_input(f"{arg}: ",textinput_id=wid,input_type=(pygame_menu.locals.INPUT_FLOAT if argType[2] == "float" else pygame_menu.locals.INPUT_INT),onreturn=self.text_edit,input_underline='_',default=int(default))
            text_input.add_self_to_kwargs()

    def toggle(self,state,widget):
        self.onchange(widget)
        arg = widget.get_id()
        ex = False
        if arg.startswith("e!"):
            arg = arg[2:]
            ex = True
        if ex:
            self.editCoords[self.currentlyEditing][1]["extraArgs"][arg] = state
        else:
            self.editCoords[self.currentlyEditing][1][arg] = state

    def drop_select(self,a,selected,widget):
        self.onchange(widget)
        arg = widget.get_id()
        ex = False
        if arg.startswith("e!"):
            arg = arg[2:]
            ex = True
        if ex:
            self.editCoords[self.currentlyEditing][1]["extraArgs"][arg] = selected
        else:  
            self.editCoords[self.currentlyEditing][1][arg] = selected

    def edit_menu(self):
        while 1:
            try:
                if pygame.key.get_pressed()[pygame.K_TAB]:
                    self.update_sprite()
                    self.editMenu.disable()
                if pygame.key.get_pressed()[pygame.K_ESCAPE]:
                    self.editMenu.disable()
                self.editMenu.update(pygame.event.get())
            except:
                self.update_sprite()
            if not self.editMenu.is_enabled():
                return self.selectedIm,False
            self.editMenu.draw(self.screen)
            pygame.display.flip()

    def pos_mode(self,listMode,widget):
        self.posMode = True
        self.posList = False
        if isinstance(listMode,list):
            self.posList = listMode.copy()
        self.editMenu.disable()
        self.button = widget
        self.prevGridPos = [-1,-1]

    def set_pos(self,newPos):
        newPosButAsAStr = str(newPos)
        if not isinstance(self.posList,list):
            if newPosButAsAStr == self.currentlyEditing:
                self.posMode = False
                self.editMenu.enable()
                return self.selectedIm,False
            if (newPosButAsAStr in self.editCoords):
                if [terrain for terrain in self.terrains if [terrain.rect.x,terrain.rect.y] == newPos]:
                    self.terrainSurface.fill((0,0,0,0),self.editCoords[newPosButAsAStr][0].rect)
                    self.terrains.remove([terrain for terrain in self.terrains if [terrain.rect.x,terrain.rect.y] == newPos][0])
                elif [sprite for sprite in self.sprites if [sprite.rect.x,sprite.rect.y] == newPos]:
                    self.sprites.remove([sprite for sprite in self.sprites if [sprite.rect.x,sprite.rect.y] == newPos][0])
                if self.editCoords[newPosButAsAStr][1] in self.levelData["terrain"]:
                    self.levelData["terrain"].remove(self.editCoords[newPosButAsAStr][1])
                elif self.editCoords[newPosButAsAStr][1] in self.levelData["sprites"]:
                    self.levelData["sprites"].remove(self.editCoords[newPosButAsAStr][1])
                self.editCoords.pop(newPosButAsAStr)
            self.editCoords[newPosButAsAStr] = self.editCoords[self.currentlyEditing]
            self.editCoords[newPosButAsAStr][1]["pos"] = newPos
            self.editCoords.pop(self.currentlyEditing)
            self.currentlyEditingL = newPos
            self.currentlyEditing = newPosButAsAStr
            self.update_sprite()
            self.posMode = False
            self.editMenu.enable()
            bid = self.button.get_id()
            guy = self.editCoords[newPosButAsAStr][1] if not bid.startswith("e!") else self.editCoords[newPosButAsAStr][1]["extraArgs"]
            bid = bid[2:] if bid.startswith("e!") else bid
            self.button.set_title(f"{bid}: {str(guy[bid])}")
            self.onchange(self.button)
            return self.selectedIm,False
        else:
            if newPos:
                print(newPos)
                self.posList.append(newPos)
                return self.selectedIm,False

    def end_pos_list(self):
        self.editCoords[self.currentlyEditing][1]["extraArgs"]["path"] = self.posList
        self.update_sprite()
        self.posMode = False
        self.editMenu.enable()
        self.button.set_title(f"{self.button.get_id()[2:]}: {str(self.posList)}")
        self.onchange(self.button)
        return self.selectedIm,False

    def update_sprite(self):
        self.sprites.remove(self.editCoords[self.currentlyEditing][0])
        try:
            self.loadSpriteOrTerrain(self.editCoords[self.currentlyEditing][1],"sprite")
        except:
            self.editCoords[self.currentlyEditing][1] = self.backupGuy
            self.loadSpriteOrTerrain(self.backupGuy,"sprite")
            print(f"ERROR: REVERTING TO BACKUP OF GUY\n{sys.exc_info()}")
            self.editMenu.disable()
        else:
            for i in range(len(self.levelData["sprites"])):
                if self.levelData["sprites"][i]["pos"] == self.currentlyEditingL:
                    self.levelData["sprites"].remove(self.levelData["sprites"][i])
                    self.levelData["sprites"].append(self.editCoords[self.currentlyEditing][1].copy())
            self.backupGuy = self.editCoords[self.currentlyEditing][1].copy()
            for widget in self.editMenu.get_widgets():
                widget.set_border(0,(0,0,0))

    def text_edit(self,current_text,widget):
        arg = widget.get_id()
        ex = False
        if arg.startswith("e!"):
            arg = arg[2:]
            ex = True
        if ex:
            self.editCoords[self.currentlyEditing][1]["extraArgs"][arg] = current_text
        else:
            self.editCoords[self.currentlyEditing][1][arg] = current_text
        self.onchange(widget)
