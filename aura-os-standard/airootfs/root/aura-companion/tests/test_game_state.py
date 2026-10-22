"""Тесты GameState и StateStore."""

import json

import pytest

from aura.game.state import (
    RANKS,
    SCHEMA_VERSION,
    GameState,
    StateStore,
    level_for_xp,
    rank_for_xp,
)


# ── rank_for_xp ────────────────────────────────────────────
def test_rank_cadet_at_zero():
    assert rank_for_xp(0) == "Кадет"

def test_rank_lieutenant_at_100():
    assert rank_for_xp(100) == "Лейтенант"

def test_rank_commander_at_300():
    assert rank_for_xp(300) == "Коммандер"

def test_rank_captain_at_600():
    assert rank_for_xp(600) == "Капитан"

def test_rank_legend_at_1000():
    assert rank_for_xp(1000) == "Легенда"

def test_rank_stays_legend_above():
    assert rank_for_xp(99999) == "Легенда"


# ── level_for_xp ───────────────────────────────────────────
def test_level_one_at_zero():
    assert level_for_xp(0) == 1

def test_level_two_at_100():
    assert level_for_xp(100) == 2

def test_level_five_at_1000():
    assert level_for_xp(1000) == 5


# ── GameState ──────────────────────────────────────────────
def test_default_state():
    s = GameState()
    assert s.xp == 0
    assert s.rank == "Кадет"
    assert s.level == 1
    assert s.sector == "STABILIZE"
    assert s.shields == 100
    assert s.hull == 1570

def test_add_xp_changes_rank():
    s = GameState()
    s.add_xp(150)
    assert s.xp == 150
    assert s.rank == "Лейтенант"
    assert s.level == 2

def test_add_xp_ignores_negative():
    s = GameState()
    s.add_xp(-50)
    assert s.xp == 0

def test_days_on_planet_minimum_one():
    s = GameState()
    assert s.days_on_planet() >= 1

def test_to_dict_roundtrip():
    s = GameState(xp=200, sector="FORMALIZE")
    s2 = GameState(**s.to_dict())
    assert s2.xp == 200
    assert s2.sector == "FORMALIZE"


# ── StateStore ─────────────────────────────────────────────
@pytest.fixture
def store(tmp_path):
    return StateStore(db_path=tmp_path / "state.db", key="test-key")

def test_store_load_default_when_empty(store):
    s = store.load()
    assert s.xp == 0
    assert s.sector == "STABILIZE"

def test_store_save_and_load(store):
    s = GameState(xp=450, sector="FORMALIZE", quests_done=["F-038"])
    store.save(s)
    s2 = store.load()
    assert s2.xp == 450
    assert s2.sector == "FORMALIZE"
    assert s2.quests_done == ["F-038"]

def test_store_save_idempotent(store):
    s = GameState(xp=100)
    store.save(s)
    store.save(s)
    assert store.load().xp == 100

def test_store_ignores_unknown_fields(store):
    store.save(GameState(xp=42))
    conn = store._connect()
    row = conn.execute("SELECT v FROM meta WHERE k='state'").fetchone()
    data = json.loads(row[0])
    data["unknown_field"] = "trash"
    conn.execute("UPDATE meta SET v=? WHERE k='state'", (json.dumps(data),))
    conn.commit()
    assert store.load().xp == 42

def test_store_persists_between_instances(tmp_path):
    db = tmp_path / "state.db"
    st1 = StateStore(db_path=db, key="k1")
    st1.save(GameState(xp=777))
    st1.close()
    st2 = StateStore(db_path=db, key="k1")
    assert st2.load().xp == 777

def test_store_writes_schema_version(store):
    store.save(GameState())
    conn = store._connect()
    row = conn.execute(
        "SELECT v FROM meta WHERE k='schema_version'"
    ).fetchone()
    assert row[0] == str(SCHEMA_VERSION)

def test_ranks_are_sorted():
    thresholds = [t for t, _ in RANKS]
    assert thresholds == sorted(thresholds)
