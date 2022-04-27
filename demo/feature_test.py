"""A place to test new WIP features"""  # pylint: disable=all
from random import randint, choice
import sys, os

sys.path.insert(0, os.path.abspath("../"))

import rubato as rb

rb.init({
    "name": "Physics Test",
    "physics_fps": 60,
    "window_size": rb.Vector(600, 600),
    "res": rb.Vector(1200, 1200),
})

main = rb.Scene()
rb.Game.scenes.add(main, "main")

with open("sprites/tes.txt", "r") as f:
    tes = f.readlines()
    print(tes)

rb.begin()
