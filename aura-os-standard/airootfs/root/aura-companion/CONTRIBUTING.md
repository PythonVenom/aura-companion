# Contributing to AURA

## Quick start

    git clone https://github.com/PythonVenom/aura-companion.git
    cd aura-companion
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    export PYTHONPATH=$PWD
    ./venv/bin/python -m aura.cli doctor

## Standards

- Python 3.12+
- mypy 0 errors: `mypy aura/ --ignore-missing-imports`
- Ruff 0 errors: `ruff check aura/`
- Tests required for new agents (pytest)
- ADR for architecture decisions (docs/adr/)

## Adding a new agent

1. Create `aura/agents/my_agent.py` (inherit `BaseAgent`)
2. Implement `can_handle()` and `handle()`
3. Register in `aura/bootstrap.py` (`_try_register`)
4. Add test in `tests/test_my_agent.py`
5. Run mypy + ruff + pytest
6. Commit with prefix `feat(agent): ...`

## Commit convention

- `feat(scope): ...` — new feature
- `fix(scope): ...` — bugfix
- `docs: ...` — documentation
- `chore: ...` — routine
- `test: ...` — tests

## WIP=1, Batch=1

- One task at a time
- Patch → test → commit
- git status before each step

## Contact

Captain: Voronin Ivan (PythonVenom)
