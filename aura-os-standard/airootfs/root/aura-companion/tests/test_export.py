"""ChatSense: export_dialogs_markdown."""
from aura.agents.chat_sense import export_dialogs_markdown


def test_export_creates_file(tmp_path):
    previews = [
        {"name": "Аня", "preview": "привет"},
        {"name": "Борис", "preview": "как дела"},
    ]
    out = tmp_path / "export.md"
    n = export_dialogs_markdown(previews, out)
    assert n == 2
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "Аня" in text
    assert "Борис" in text


def test_export_empty(tmp_path):
    out = tmp_path / "empty.md"
    n = export_dialogs_markdown([], out)
    assert n == 0
    assert out.exists()
