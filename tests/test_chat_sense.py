"""Bug 16: ChatSense — неотвеченные сообщения."""
import time
from aura.agents import chat_sense as cs


def setup_function():
    cs.STATE_PATH.unlink(missing_ok=True)


def test_empty():
    assert cs.find_unanswered([]) == []


def test_my_message_skipped():
    items = cs.find_unanswered([{"chat": "Аня", "preview": "Вы: привет"}])
    assert items == []


def test_their_message_detected():
    items = cs.find_unanswered([{"chat": "Аня", "preview": "привет"}])
    assert len(items) == 1
    assert items[0]["chat"] == "Аня"
    assert items[0]["reason"] == "unanswered"


def test_system_chats_skipped():
    items = cs.find_unanswered([
        {"chat": "Коды подтверждения", "preview": "1234"},
        {"chat": "MAX на iPhone", "preview": "новости"},
    ])
    assert items == []


def test_ttl_filters_recent():
    items = [{"chat": "Аня", "preview": "привет", "reason": "unanswered"}]
    cs.mark_reminded(items)
    filtered = cs.filter_by_reminder_ttl(items)
    assert filtered == []


def test_ttl_after_timeout_passes():
    state = {"reminded": {"Аня": time.time() - cs.RE_MIND_TTL - 1}}
    items = [{"chat": "Аня", "preview": "привет", "reason": "unanswered"}]
    filtered = cs.filter_by_reminder_ttl(items, state=state)
    assert len(filtered) == 1


def test_summary_one():
    s = cs.summary([{"chat": "Аня", "preview": "x", "reason": "u"}])
    assert "Аня" in s


def test_summary_many():
    items = [
        {"chat": "Аня", "preview": "x", "reason": "u"},
        {"chat": "Борис", "preview": "y", "reason": "u"},
    ]
    s = cs.summary(items)
    assert "2" in s
    assert "Аня" in s


def test_summary_empty():
    assert cs.summary([]) == ""
