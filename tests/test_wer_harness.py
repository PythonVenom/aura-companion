"""T083 — тесты WER harness."""
from aura.core import wer_harness


def test_normalize():
    assert wer_harness.normalize("Привет, Мир!") == "привет мир"
    assert wer_harness.normalize("") == ""
    assert wer_harness.normalize("a  b   c") == "a b c"


def test_wer_identical():
    r = wer_harness.wer("привет мир", "привет мир")
    assert r["wer"] == 0.0
    assert r["S"] == 0 and r["D"] == 0 and r["I"] == 0
    assert r["pass"] is True


def test_wer_one_substitution():
    r = wer_harness.wer("привет мир", "привет море")
    assert r["S"] == 1 and r["D"] == 0 and r["I"] == 0
    assert r["N"] == 2
    assert r["wer"] == 0.5


def test_wer_one_deletion():
    r = wer_harness.wer("привет мир большой", "привет мир")
    assert r["S"] == 0 and r["D"] == 1 and r["I"] == 0
    assert r["N"] == 3
    assert r["wer"] == 1 / 3


def test_wer_one_insertion():
    r = wer_harness.wer("привет мир", "привет мой мир")
    assert r["S"] == 0 and r["D"] == 0 and r["I"] == 1
    assert r["N"] == 2
    assert r["wer"] == 0.5


def test_wer_empty_ref():
    r = wer_harness.wer("", "какие-то слова")
    assert r["I"] == 2
    assert r["wer"] == 1.0


def test_corpus_wer():
    pairs = [
        ("привет мир", "привет мир"),
        ("как дела", "как дела"),
        ("добрый день", "добрый вечер"),
    ]
    r = wer_harness.corpus_wer(pairs)
    assert r["samples"] == 3
    # 1 substitution, 6 words total
    assert r["S"] == 1
    assert r["N"] == 6
    assert r["wer"] == round(1 / 6, 4)


def test_record_and_report(tmp_path, monkeypatch):
    monkeypatch.setattr(wer_harness, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(wer_harness, "RESULTS_FILE", tmp_path / "wer.jsonl")
    wer_harness.record("asr", "привет мир", "привет мир")
    wer_harness.record("asr", "как дела", "как дела")
    report = wer_harness.wer_report()
    assert report["samples"] == 2
    assert report["wer"] == 0.0
    assert report["pass"] is True


def test_record_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(wer_harness, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(wer_harness, "RESULTS_FILE", tmp_path / "wer.jsonl")
    wer_harness.record("asr", "один два три четыре пять", "один три")
    report = wer_harness.wer_report()
    assert report["samples"] == 1
    assert report["pass"] is False
    assert report["wer"] > 0.05


def test_reset(tmp_path, monkeypatch):
    monkeypatch.setattr(wer_harness, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(wer_harness, "RESULTS_FILE", tmp_path / "wer.jsonl")
    wer_harness.record("asr", "привет", "привет")
    wer_harness.reset()
    assert wer_harness.load_history() == []
