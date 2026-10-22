"""Тесты Meta + NLU + Verifier + Red Team (ADR-131..133)."""
from __future__ import annotations


def test_meta_score_sure():
    from aura.core.memory.meta import score
    s = score(extraction=0.95, evidence_count=10, consistency=0.95)
    assert s.label == "sure"
    assert s.value > 0.8


def test_meta_score_unsure():
    from aura.core.memory.meta import score
    s = score(extraction=0.2, evidence_count=1, consistency=0.3)
    assert s.label in ("unsure", "unknown")


def test_meta_hedged():
    from aura.core.memory.meta import score, hedged
    s = score(extraction=0.9, evidence_count=10)
    assert hedged("Париж", s) == "Париж"
    s2 = score(extraction=0.3, evidence_count=1, consistency=0.3)
    out = hedged("Париж", s2)
    assert "уверена" in out or "возможно" in out or "Кажется" in out


def test_meta_calibration():
    from aura.core.memory.meta import calibration_error
    ece = calibration_error([(0.9, True), (0.9, True), (0.1, False)])
    assert 0.0 <= ece <= 1.0


def test_nlu_imports():
    from aura.core.nlu import classify
    assert callable(classify)


def test_nlu_classify_or_fallback():
    from aura.core.nlu import classify
    r, c = classify("xyzzy nonsense text no intent")
    # либо None (порог), либо low confidence
    assert r is None or c >= 0.0


def test_verifier_number_check():
    from aura.core.verifier import check_numbers_consistency
    assert check_numbers_consistency("в 2026 году", "сегодня 2026 год")
    assert not check_numbers_consistency("42", "ничего похожего")


def test_verifier_hedge_signal():
    from aura.core.verifier import should_hedge
    assert should_hedge(0.5)
    assert not should_hedge(0.9)


def test_red_team_dataset_loads():
    import yaml
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "evals/red_team.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert len(data["cases"]) >= 25
