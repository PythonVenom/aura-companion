"""#36 AgentCANBus — тесты pub/sub шины."""
from __future__ import annotations

import pytest

from aura.core.canbus import (
    AgentCANBus, Message, _matches, get_bus, reset_bus, HISTORY_SIZE,
)


@pytest.fixture
def bus():
    return AgentCANBus()


@pytest.fixture
def recorder():
    """Простой recorder для сбора сообщений."""
    msgs = []
    def _rec(m): msgs.append(m)
    return msgs, _rec


# === _matches (wildcard) ===

def test_matches_exact():
    assert _matches("meds.taken", "meds.taken") is True


def test_matches_exact_false():
    assert _matches("meds.taken", "meds.missed") is False


def test_matches_star_single_level():
    assert _matches("meds.*", "meds.taken") is True
    assert _matches("meds.*", "meds.missed") is True


def test_matches_star_not_deep():
    """meds.* НЕ матчит meds.a.b (только один уровень)."""
    assert _matches("meds.*", "meds.a.b") is False


def test_matches_global_star():
    assert _matches("*", "anything") is True


def test_matches_no_partial():
    """'med' НЕ матчит 'meds.taken' (нет префиксного матча без *)."""
    assert _matches("med", "meds.taken") is False


# === publish / subscribe ===

def test_publish_no_subscribers(bus):
    delivered = bus.publish("x", {"a": 1})
    assert delivered == 0


def test_publish_one_subscriber(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("x", rec)
    delivered = bus.publish("x", {"a": 1})
    assert delivered == 1
    assert len(msgs) == 1
    assert msgs[0].payload == {"a": 1}


def test_publish_multiple_subscribers(bus):
    count = [0, 0]
    bus.subscribe("x", lambda m: count.__setitem__(0, count[0] + 1))
    bus.subscribe("x", lambda m: count.__setitem__(1, count[1] + 1))
    delivered = bus.publish("x", {})
    assert delivered == 2
    assert count == [1, 1]


def test_publish_wildcard(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("meds.*", rec)
    bus.publish("meds.taken", {})
    bus.publish("meds.missed", {})
    bus.publish("fall.detected", {})
    assert len(msgs) == 2


def test_publish_empty_channel_raises(bus):
    with pytest.raises(ValueError):
        bus.publish("", {})


def test_publish_sender_recorded(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("x", rec)
    bus.publish("x", {}, sender="meds")
    assert msgs[0].sender == "meds"


def test_publish_timestamp_set(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("x", rec)
    bus.publish("x", {})
    assert msgs[0].ts > 0


# === subscribe ===

def test_subscribe_empty_raises(bus):
    with pytest.raises(ValueError):
        bus.subscribe("", lambda m: None)


def test_subscribe_non_callable_raises(bus):
    with pytest.raises(TypeError):
        bus.subscribe("x", "not_callable")


# === unsubscribe ===

def test_unsubscribe_existing(bus):
    rec = lambda m: None
    bus.subscribe("x", rec)
    assert bus.unsubscribe("x", rec) is True


def test_unsubscribe_unknown_channel(bus):
    assert bus.unsubscribe("nope", lambda m: None) is False


def test_unsubscribe_after_delivery(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("x", rec)
    bus.publish("x", {})
    bus.unsubscribe("x", rec)
    bus.publish("x", {})
    assert len(msgs) == 1


def test_unsubscribe_unknown_callback(bus):
    bus.subscribe("x", lambda m: None)
    assert bus.unsubscribe("x", lambda m: None) is False


# === broadcast ===

def test_broadcast_all_subscribers(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("*", rec)
    bus.broadcast({"msg": "all"})
    assert len(msgs) == 1


def test_broadcast_channel_is_star(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("*", rec)
    bus.broadcast({"x": 1})
    assert msgs[0].channel == "*"


# === history ===

def test_history_empty(bus):
    assert bus.history() == []


def test_history_all(bus):
    for i in range(5):
        bus.publish(f"ch{i}", {})
    assert len(bus.history()) == 5


def test_history_filtered(bus):
    bus.publish("meds.taken", {})
    bus.publish("fall.detected", {})
    bus.publish("meds.missed", {})
    assert len(bus.history("meds.*")) == 2


def test_history_limit(bus):
    for i in range(10):
        bus.publish("x", {"i": i})
    assert len(bus.history(limit=3)) == 3


def test_history_ring_buffer():
    """Ring-buffer не растёт выше HISTORY_SIZE."""
    bus = AgentCANBus(history_size=10)
    for i in range(50):
        bus.publish("x", {"i": i})
    assert len(bus.history(limit=1000)) == 10
    # Проверяем, что остались последние
    hist = bus.history(limit=1000)
    assert hist[-1].payload == {"i": 49}


# === stats ===

def test_stats_initial(bus):
    s = bus.stats()
    assert s["published"] == 0
    assert s["delivered"] == 0
    assert s["dropped"] == 0


def test_stats_after_publish(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("x", rec)
    bus.publish("x", {})
    bus.publish("x", {})
    s = bus.stats()
    assert s["published"] == 2
    assert s["delivered"] == 2


def test_stats_dropped_on_exception(bus):
    def bad(m): raise RuntimeError("boom")
    bus.subscribe("x", bad)
    bus.publish("x", {})
    assert bus.stats()["dropped"] == 1


def test_stats_channels_count(bus):
    bus.subscribe("a", lambda m: None)
    bus.subscribe("b", lambda m: None)
    assert bus.stats()["channels"] == 2


# === clear ===

def test_clear_resets_all(bus, recorder):
    msgs, rec = recorder
    bus.subscribe("x", rec)
    bus.publish("x", {})
    bus.clear()
    assert bus.stats()["published"] == 0
    assert bus.history() == []
    assert bus.stats()["channels"] == 0


# === singleton ===

def test_get_bus_singleton():
    reset_bus()
    b1 = get_bus()
    b2 = get_bus()
    assert b1 is b2


def test_reset_bus_creates_new():
    b1 = get_bus()
    reset_bus()
    b2 = get_bus()
    assert b1 is not b2


# === Message dataclass ===

def test_message_fields():
    m = Message(channel="x", payload={"a": 1}, sender="test")
    assert m.channel == "x"
    assert m.payload == {"a": 1}
    assert m.sender == "test"
    assert m.ts > 0
