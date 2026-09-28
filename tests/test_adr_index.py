"""ADR index consistency (doc-test)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
ADR_DIR = ROOT / "docs" / "adr"
README = ADR_DIR / "README.md"


def test_all_adr_files_in_index():
    readme = README.read_text(encoding="utf-8")
    files = sorted(ADR_DIR.glob("[0-9][0-9][0-9]-*.md"))
    missing = [f.stem[:3] for f in files if f"| {f.stem[:3]} |" not in readme]
    assert not missing, f"ADR не в индексе: {missing}"


def test_index_has_no_phantoms():
    readme = README.read_text(encoding="utf-8")
    codes = re.findall(r"^\| (\d{3}) \|", readme, re.MULTILINE)
    files = {f.stem[:3] for f in ADR_DIR.glob("[0-9][0-9][0-9]-*.md")}
    phantoms = [c for c in codes if c not in files]
    assert not phantoms, f"Phantom ADR в индексе: {phantoms}"


def test_new_adr_have_date_and_status():
    """ADR-024+ должны иметь **Дата:** и **Статус:**
    (старые 001-023 — другой формат, не трогаем — YAGNI)."""
    bad = []
    for f in ADR_DIR.glob("[0-9][0-9][0-9]-*.md"):
        num = int(f.stem[:3])
        if num < 24:
            continue
        text = f.read_text(encoding="utf-8")
        if "**Дата:**" not in text or "**Статус:**" not in text:
            bad.append(f.stem)
    assert not bad, f"ADR-024+ без Дата/Статус: {bad}"


def test_adr_count_minimum():
    files = list(ADR_DIR.glob("[0-9][0-9][0-9]-*.md"))
    assert len(files) >= 30, f"ADR только {len(files)}, ожидалось 30+"
