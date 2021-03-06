import pygame

images = {
    "player": {
        "idle":"idle.png",
        "look0f0":"lookUp1.png","look0f1":"lookUp2.png","go0f0":"goUp1.png","go0f1":"goUp2.png","go0f2":"goUp3.png",
        "look1f0":"lookRight1.png","look1f1":"lookRight2.png","go1f0":"goRight1.png","go1f1":"goRight2.png","go1f2":"goRight3.png",
        "look2f0":"lookDown1.png","look2f1":"lookDown2.png","go2f0":"goDown1.png","go2f1":"goDown2.png","go2f2":"goDown3.png",
        "look3f0":"lookLeft1.png","look3f1":"lookLeft2.png","go3f0":"goLeft1.png","go3f1":"goLeft2.png","go3f2":"goLeft3.png",
        "confuzzled0":"confuzzled1.png","confuzzled1":"confuzzled2.png","confuzzled2":"confuzzled3.png","confuzzled3":"confuzzled4.png","confuzzled4":"confuzzled5.png",
        "death0":"death1.png","death1":"death2.png","death2":"death3.png","death3":"death4.png","death4":"death5.png",
        "celebrate0":"celebrate1.png","celebrate1":"celebrate2.png","celebrate2":"celebrate3.png",
    },
    "redPlayer": {
        "idle":"idle.png",
        "look0f0":"lookUp1.png","look0f1":"lookUp2.png","go0f0":"goUp1.png","go0f1":"goUp2.png","go0f2":"goUp3.png",
        "look1f0":"lookRight1.png","look1f1":"lookRight2.png","go1f0":"goRight1.png","go1f1":"goRight2.png","go1f2":"goRight3.png",
        "look2f0":"lookDown1.png","look2f1":"lookDown2.png","go2f0":"goDown1.png","go2f1":"goDown2.png","go2f2":"goDown3.png",
        "look3f0":"lookLeft1.png","look3f1":"lookLeft2.png","go3f0":"goLeft1.png","go3f1":"goLeft2.png","go3f2":"goLeft3.png",
        "confuzzled0":"confuzzled1.png","confuzzled1":"confuzzled2.png","confuzzled2":"confuzzled3.png","confuzzled3":"confuzzled4.png","confuzzled4":"confuzzled5.png",
        "death0":"death1.png","death1":"death2.png","death2":"death3.png","death3":"death4.png","death4":"death5.png",
        "celebrate0":"celebrate1.png","celebrate1":"celebrate2.png","celebrate2":"celebrate3.png",
    },

    "goal": {
        "idle": "idle.png",
        "locked": "locked.png"
    },
    "key": {
        "idle": "idle.png"
    },
    "triangle": {
        "idle": "idle.png","idle1": "idle1.png","idle2": "idle2.png","idle3": "idle3.png",
        "mouthOpen": "mouthOpen.png","mouthOpen1": "mouthOpen1.png","mouthOpen2": "mouthOpen2.png","mouthOpen3": "mouthOpen3.png",
    },
    "buttons": {
        "idle": "idle.png",
        "space": "space.png"
    },
    "stone": {
        "idle": "idle.png",
        "death0": "death0.png","death1": "death1.png","death2":"death2.png","death3":"death3.png","death4":"death4.png"
    },
    "button": {
        "idle": "idle.png",
        "pressed": "pressed.png"
    },
    "default": {
        "idle": "idle.png"
    },
    "playerGate": {
        "idle": "horizontal.png",
        "vertical": "vertical.png"
    },
    "grass": {
        0: "0.png",
    },
    "brick": {
        0: "0.png"
    },
    "phantombrick": {
        0: "0.png"
    },
    "nada": {
        0: "0.png"
    },
}

for i in range(16):
    images["grass"][i] = f"{i}.png"

animations = {
    "player": {
        "collide": (0,["confuzzled0","confuzzled1","confuzzled2","confuzzled3","confuzzled4","idle"],[]),
        "death": (60,["death0","death1","death2","death3","death4"],[]),
        "look": (600,["look{}f0","look{}f1"],["look{}f0","idle"]),
        "go": (-1,["go{}f0","go{}f1","go{}f2"],[]),
        "celebrate": (150,["celebrate0","celebrate1","celebrate2"],[]),
        "idle": (-1,["idle"],[]),
    },
    "goal": {
        "unlock": (0,["idle"],[]),
        "reset": (-1,["idle"],[])
    },
    "triangle": {
        "idle": (60,["idle","idle1","idle2","idle3"],[]),
        "playerNear": (60,["mouthOpen","mouthOpen1","mouthOpen2","mouthOpen3"],[])
    },
    "stone": {
        "idle": (0,["idle"],[]),
        "death": (0,["death0","death1","death2","death3","death4"],[])
    },
    "button": {
        "press": (0,["pressed"],[])
    },

}

binds = [
    {pygame.K_w:"up",pygame.K_s:"down",pygame.K_a:"left",pygame.K_d:"right",pygame.K_SPACE:"action",pygame.K_ESCAPE:"pause",pygame.K_r:"reset"},
    {pygame.K_UP:"up",pygame.K_DOWN:"down",pygame.K_LEFT:"left",pygame.K_RIGHT:"right",pygame.K_KP0:"action"}
    ]

sprites = {"assets/guy/": "player", "assets/guy2/": "redPlayer", "assets/goal/":"goal","assets/key/":"key","assets/buttons/":"buttons","assets/triangle/":"triangle","assets/stone/":"stone","assets/playerGate/":"playerGate","assets/button/":"button"}

terrains = {"assets/terrain/grass/": "grass","assets/terrain/brick/": "brick","assets/terrain/phantombrick/": "phantombrick","assets/terrain/nada/":"nada"}

types = ["none","path","player"]

spriteArgs = {
    "image": ["text",None],
    "type": ["dropdown", types,"none"],
    "pos": ["pos",False],
    "assetPath": ["text","assets/"],
    "extraImages": ["dropdown",list(images.keys()),"default"],
    "animations": ["dropdown",list(animations.keys()),None],
    "weight": ["flint",0,"int"]
}

spriteExtraArgs = {
    "player": ["flint",0,"int"],
    "tangable": ["toggle",1],
    "kill": ["toggle",0],
    "killable": ["toggle",0],
    "movable": ["toggle",0],
    "key": ["toggle",0],
    "goal": ["toggle",0],
    "locked": ["toggle",0],
    "path": ["pos",[]],
    "pathSpeed": ["flint",1,"float"],
    "pathStartup": ["flint",1,"float"],
    "pathCooldown": ["flint",60,"float"],
    "pathRepeat": ["toggle",1],
    "pathTrigger": ["text",None],
    "addControl": ["text",None],
    "triggerId": ["text",None],
    "playerThrough": ["toggle",0]
}

defaultExtraArgs = {
    "dead":False,"player":False,"tangable":True,
    "kill":False,"killable":False,"movable":False,
    "key":False,"goal":False,"locked":False,
    "won":False,"path":None,"pathSpeed":1,
    "pathStartup":1,"pathCooldown": 60,"pathRepeat":True,
    "pathTrigger": None,"addControl": None,"triggerId": None,"playerThrough":False
} # Default Args
