import pygame

images = {
    "player": {
        "idle":"idle.png",
        "look0f0":"lookUp1.png","look0f1":"lookUp2.png","go0f0":"goUp1.png","go0f1":"goUp2.png","go0f2":"goUp3.png",
        "look1f0":"lookRight1.png","look1f1":"lookRight2.png","go1f0":"goRight1.png","go1f1":"goRight2.png","go1f2":"goRight3.png",
        "look2f0":"lookDown1.png","look2f1":"lookDown2.png","go2f0":"goDown1.png","go2f1":"goDown2.png","go2f2":"goDown3.png",
        "look3f0":"lookLeft1.png","look3f1":"lookLeft2.png","go3f0":"goLeft1.png","go3f1":"goLeft2.png","go3f2":"goLeft3.png",
        "confuzzled0":"confuzzled1.png","confuzzled1":"confuzzled2.png","confuzzled2":"confuzzled3.png","confuzzled3":"confuzzled4.png","confuzzled4":"confuzzled5.png",
        "death0":"death1.png","death1":"death2.png","death2":"death3.png","death3":"death4.png","death4":"death5.png","death5":"death6.png",
    },
    "grass": {
        0: "0.png"
    },
    "brick": {
        0: "0.png"
    }
}

animations = {
    "player": {
            "collide": ["confuzzled0","confuzzled1","confuzzled2","confuzzled3","confuzzled4","idle"],
            "death": ["death0","death1","death2","death3","death4","death5","death5","death5","death5","death5","death5","death5","death5"],
            "look": ["look{}f0","look{}f1"],
            "go": ["go{}f0","go{}f1","go{}f2"],
            "reset": [],
        },

}

binds = [
    {pygame.K_w:"up",pygame.K_s:"down",pygame.K_a:"left",pygame.K_d:"right",pygame.K_SPACE:"action",pygame.K_ESCAPE:"pause"},
    {pygame.K_UP:"up",pygame.K_DOWN:"down",pygame.K_LEFT:"left",pygame.K_RIGHT:"right",pygame.K_KP0:"action"}
    ]

sprites = {"assets/guy/": "player", "assets/guy2/": "player"}

terrains = {"assets/terrain/grass/": "grass","assets/terrain/brick/": "brick"}