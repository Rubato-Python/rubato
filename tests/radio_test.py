"""Test the radio module"""
import pytest, unittest.mock as mock
from rubato.utils.radio import Radio, Listener
from rubato.utils.events import EventResponse


def test_listener_init():
    l = Listener("test", lambda: "test")
    assert l.event == "test"
    assert l.callback() == "test"  # type: ignore
    assert l.registered is False


def test_listener_ping():
    callback = mock.Mock()
    res = EventResponse(1)
    l = Listener("test", callback)

    l.ping(res)
    callback.assert_called_with(res)

    def example_cb():
        pass

    callback = mock.create_autospec(example_cb)
    l = Listener("test", callback)
    l.ping(res)
    callback.assert_called_once()


def test_radio_register():
    Radio.listeners = {}
    l = Listener("test", lambda: None)
    l2 = Listener("test", lambda: None)
    l3 = Listener("test", lambda: None)
    l3.registered = True
    Radio.register(l)
    Radio.register(l2)
    assert l.registered is True
    assert l2.registered is True

    assert Radio.listeners["test"] == [l, l2]

    l.registered = False
    with pytest.raises(ValueError):
        Radio.register(l)

    with pytest.raises(ValueError):
        Radio.register(l3)


def test_radio_listen():
    Radio.listeners = {}
    l = Radio.listen("test", lambda: None)
    assert l.registered is True
    assert l.event == "test"
    assert l.callback() is None  # type: ignore
    assert Radio.listeners["test"] == [l]


def test_radio_broadcast():
    Radio.listeners = {}
    callback = mock.Mock()
    Radio.listen("test", callback)
    Radio.listen("test", callback)
    Radio.listen("test", callback)

    Radio.broadcast("test")
    assert isinstance(callback.call_args_list[0].args[0], EventResponse)
    assert callback.call_count == 3


def test_listener_remove():
    Radio.listeners = {}
    l = Listener("test", lambda: None)
    l2 = Listener("test", lambda: None)
    Radio.register(l)

    assert l.registered is True
    assert l in Radio.listeners["test"]

    l.remove()
    assert l.registered is False
    assert not Radio.listeners

    with pytest.raises(ValueError):
        l2.remove()
