"""A Perlin Noise demo for Rubato"""
from random import randint
import rubato as rb

rb.init({
    "name": "Perlin Test",
    "res": rb.Vector(480, 270),
    "window_size": rb.Vector(960, 540),
})

main_scene = rb.Scene()

scale = 100
offset = rb.Vector(100, 100)
true_random = True

rb.Noise.seed = randint(-100, 100)

saved = []
for x in range(rb.Display.res.x):
    saved.append([])
    for y in range(rb.Display.res.y):
        if true_random:
            noise = random.random() * 2 - 1
        else:
            noise = rb.Noise.noise2((x + offset.x) / scale, (y + offset.y) / scale)
        gray = (noise + 1) / 2 * 255  # Note simplex perlin noise ranges from -1 to 1 and is being scaled to 0-255
        color = [gray for i in range(3)]
        color = rb.Color(*color)
        saved[x].append((rb.Vector(x, y), color))


def draw():
    for i in range(rb.Display.res.x):
        for j in range(rb.Display.res.y):
            rb.Draw.point(saved[i][j][0], color=saved[i][j][1])


main_scene.draw = draw

rb.begin()
