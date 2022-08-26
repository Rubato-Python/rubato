"""Test the Game class"""
import pytest
from unittest.mock import Mock
import rubato
from rubato.game import Game
from rubato.struct.scene import Scene
from rubato.utils.debug import Debug
from rubato.utils.display import Display
from rubato.utils.draw import Draw
from rubato.utils.error import Error, InitError, IdError, PrintError
from rubato.utils.radio import Radio
from rubato.utils.rb_input import Input
from rubato.utils.rb_time import Time
# pylint: disable=redefined-outer-name, unused-argument, protected-access


@pytest.fixture
def scene():
    return Scene()


def test_state():
    assert Game.state == Game.STOPPED
    Game.state = Game.RUNNING
    assert Game.state == Game.RUNNING
    Game.state = Game.STOPPED
    assert Game.state == Game.STOPPED


def test_camera():
    Scene()
    assert Game.camera == Game.current.camera  # type: ignore


def test_init():
    with pytest.raises(InitError):
        Game()


def test__add():
    with pytest.raises(IdError):
        Game._add(Scene(name="scene"))
        Game._add(Scene(name="scene"))


@pytest.mark.rub
def test_quit(rub):
    with pytest.raises(SystemExit):
        Game.quit()
    assert Game.state == Game.STOPPED


def test_start(monkeypatch: pytest.MonkeyPatch):
    loop = Mock()
    monkeypatch.setattr(Game, "loop", loop)
    Game.start()
    loop.assert_called_once()

    loop = Mock(side_effect=KeyboardInterrupt)
    quit_mock = Mock()
    monkeypatch.setattr(Game, "quit", quit_mock)
    monkeypatch.setattr(Game, "loop", loop)
    Game.start()
    quit_mock.assert_called_once()

    loop = Mock(side_effect=PrintError)
    monkeypatch.setattr(Game, "loop", loop)
    with pytest.raises(PrintError):
        Game.start()
    loop.assert_called_once()

    loop = Mock(side_effect=Error)
    monkeypatch.setattr(Game, "loop", loop)
    with pytest.raises(Error):
        Game.start()
    loop.assert_called_once()

    assert Game.state == Game.RUNNING
    Game.state = Game.STOPPED


@pytest.mark.rub
def test_loop(monkeypatch: pytest.MonkeyPatch, rub):
    time_now = Mock(side_effect=[0] + [x * 1000 for x in range(20)])
    monkeypatch.setattr(Time, "now", time_now)
    push = Mock(side_effect=Error)
    monkeypatch.setattr(rubato.game.sdl2, "SDL_PushEvent", push)
    pump = Mock()
    monkeypatch.setattr(rubato.game.sdl2, "SDL_PumpEvents", pump)
    handle = Mock(side_effect=[x == 0 for x in range(20)])
    monkeypatch.setattr(Radio, "handle", handle)
    quit_func = Mock()
    monkeypatch.setattr(Game, "quit", quit_func)
    update_controller = Mock()
    monkeypatch.setattr(Input, "update_controllers", update_controller)
    process = Mock()
    monkeypatch.setattr(Time, "process_calls", process)

    run_count = 0
    scene_mock = Mock()

    def update_override():
        nonlocal run_count
        if run_count == 0:
            Game._current = ""
        if run_count == 1:
            monkeypatch.setattr(Game, "current", scene_mock)
            Game.state = Game.PAUSED
        elif run_count == 2:
            Game.state = Game.STOPPED
        run_count += 1

    Game.update = update_override

    Time.fixed_delta = 1

    clear = Mock()
    monkeypatch.setattr(Draw, "clear", clear)
    dump = Mock()
    monkeypatch.setattr(Draw, "dump", dump)
    draw = Mock()
    monkeypatch.setattr(Debug, "draw_fps", draw)

    Game.show_fps = True

    present = Mock()
    monkeypatch.setattr(Display.renderer, "present", present)

    Time.capped = True
    Time.normal_delta = 50000

    delay = Mock()
    monkeypatch.setattr(rubato.game.sdl2, "SDL_Delay", delay)

    with pytest.raises(Error):
        Game.start()

    time_now.assert_called()
    assert time_now.call_count == 11
    push.assert_called_once()
    pump.assert_called()
    assert pump.call_count == 3
    handle.assert_called()
    assert handle.call_count == 3
    quit_func.assert_called_once()
    update_controller.assert_called()
    assert update_controller.call_count == 3
    process.assert_called()
    assert process.call_count == 3
    assert run_count == 3
    scene_mock._paused_update.assert_called_once()
    scene_mock._update.assert_called_once()
    scene_mock._fixed_update.assert_called()
    assert scene_mock._fixed_update.call_count == 2
    scene_mock._draw.assert_called()
    assert scene_mock._draw.call_count == 2
    clear.assert_called_once()
    dump.assert_called()
    assert dump.call_count == 3
    draw.assert_called()
    assert draw.call_count == 3
    present.assert_called()
    assert present.call_count == 3
    delay.assert_called()
    assert delay.call_count == 4
    assert Game.state == Game.STOPPED
