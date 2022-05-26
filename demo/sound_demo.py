"""
A sound demo for rubato

Requires rubato 2.1.0 or later.
"""
import rubato as rb

rb.init(
    name="Sound Test",
    window_size=rb.Vector(300, 0),
    res=rb.Vector(0, 0),
)

main_scene = rb.Scene()

rb.Sound.import_sound_folder("sounds")  # Import the sound folder

click = rb.Sound.get_sound("click")  # Get sound instance
music = rb.Sound.get_sound("music")


def update():
    print(f"click: {bin(click.channels)}   music: {bin(music.channels)}")  # Prints the active channels
    if rb.Input.key_pressed("space"):
        click.play(0)


def input_listener(keyinfo):
    if keyinfo["key"] == "m":
        music.play()
    if keyinfo["key"] == "a":
        click.play(20)
    if keyinfo["key"] == "s":
        click.stop()
        music.stop()
    if keyinfo["key"] == "p":
        if click.state == rb.Sound.PLAYING:
            click.pause()
        elif click.state == rb.Sound.PAUSED:
            click.resume()
        if music.state == rb.Sound.PLAYING:
            music.pause()
        elif music.state == rb.Sound.PAUSED:
            music.resume()


rb.Radio.listen("KEYDOWN", input_listener)

main_scene.update = update

rb.begin()
