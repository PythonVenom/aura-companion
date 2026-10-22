"""CLI: agents + professions."""
from argparse import Namespace
from aura import cli


def test_cmd_agents(capsys):
    rc = cli.cmd_agents(Namespace())
    assert rc == 0
    out = capsys.readouterr().out
    assert "Всего агентов" in out
    # Должно быть >= 30
    import re
    m = re.search(r"Всего агентов: (\d+)", out)
    assert m, "нет строки с count"
    n = int(m.group(1))
    assert n >= 30, f"агентов только {n}"


def test_cmd_professions(capsys):
    rc = cli.cmd_professions(Namespace())
    assert rc == 0
    out = capsys.readouterr().out
    assert "профессий" in out.lower()
