"""Тесты для aura/core/recon.py — парсер .tasks формата."""
from __future__ import annotations

import pytest

from aura.core.recon import parse_tasks, TaskBlock


def test_parse_empty():
    assert parse_tasks("") == []


def test_parse_only_header():
    text = "# tag: base\n# description: test\n"
    assert parse_tasks(text) == []


def test_parse_one_block_one_cmd():
    text = """# tag: x
## id=01 name=git
cmd: git status
"""
    blocks = parse_tasks(text)
    assert len(blocks) == 1
    b = blocks[0]
    assert b.id == "01"
    assert b.name == "git"
    assert b.entries == [("cmd", "git status")]


def test_parse_multiple_cmds():
    text = """## id=02 name=multi
cmd: git status
cmd: git log --oneline -5
"""
    blocks = parse_tasks(text)
    assert len(blocks) == 1
    assert len(blocks[0].entries) == 2
    assert blocks[0].entries[0] == ("cmd", "git status")
    assert blocks[0].entries[1] == ("cmd", "git log --oneline -5")


def test_parse_file_entry():
    text = """## id=03 name=unit
file: ~/.config/systemd/user/aura.service
"""
    blocks = parse_tasks(text)
    assert blocks[0].entries[0] == ("file", "~/.config/systemd/user/aura.service")


def test_parse_multiple_blocks():
    text = """## id=01 name=a
cmd: echo a

## id=02 name=b
cmd: echo b
"""
    blocks = parse_tasks(text)
    assert len(blocks) == 2
    assert blocks[0].id == "01"
    assert blocks[1].id == "02"


def test_parse_skips_comments_and_blanks():
    text = """# tag: x

## id=01 name=a
# comment inside
cmd: echo a

# another comment
"""
    blocks = parse_tasks(text)
    assert len(blocks) == 1
    assert len(blocks[0].entries) == 1


def test_parse_bad_block_no_id():
    text = """## name=missing_id
cmd: echo x
"""
    blocks = parse_tasks(text)
    assert blocks == []
