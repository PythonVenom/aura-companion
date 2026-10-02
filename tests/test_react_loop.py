"""Тесты ReAct Loop."""
from __future__ import annotations
from aura.core.react_loop import ReActLoop, Step, Episode, format_episode
from aura.core.htn_planner import Operator


def _exec_ok(cap, args):
    return True, f"did {cap}"

def _exec_fail(cap, args):
    return False, "nope"

def _exec_mixed(cap, args):
    return ("ok" in cap), f"result of {cap}"


def test_single_step_success():
    loop = ReActLoop(executor=_exec_ok)
    ops = [Operator("x.y", {}, "test")]
    ep = loop.run("test", ops)
    assert ep.done is True
    assert len(ep.steps) == 1
    assert ep.steps[0].ok is True


def test_single_step_fail():
    loop = ReActLoop(executor=_exec_fail)
    ops = [Operator("x.y", {}, "test")]
    ep = loop.run("test", ops)
    assert ep.done is False
    assert ep.steps[0].ok is False


def test_max_iterations_cap():
    loop = ReActLoop(executor=_exec_ok)
    ops = [Operator(f"x.{i}", {}, "") for i in range(10)]
    ep = loop.run("test", ops)
    assert len(ep.steps) == ReActLoop.MAX_ITERATIONS


def test_executor_exception():
    def boom(cap, args):
        raise RuntimeError("boom")
    loop = ReActLoop(executor=boom)
    ops = [Operator("x.y", {}, "test")]
    ep = loop.run("test", ops)
    assert ep.done is False
    assert "boom" in ep.steps[0].error


def test_custom_reflector():
    def always_done(goal, steps):
        return True, "custom"
    loop = ReActLoop(executor=_exec_fail, reflector=always_done)
    ops = [Operator("x.y", {}, "")]
    ep = loop.run("test", ops)
    assert ep.done is True
    assert ep.reason == "custom"


def test_empty_operators():
    loop = ReActLoop(executor=_exec_ok)
    ep = loop.run("test", [])
    assert ep.done is False
    assert ep.steps == []


def test_format_episode():
    loop = ReActLoop(executor=_exec_ok)
    ops = [Operator("x.y", {}, "")]
    ep = loop.run("test", ops)
    s = format_episode(ep)
    assert "test" in s
    assert "DONE" in s
    assert "OK" in s
