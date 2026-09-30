"""Bug 66: тесты под симптом утечки потоков + CPU-дельты + аудио."""
import sys
sys.path.insert(0, "scripts")

def test_parse_thread_count_from_proc():
    from aura_health import parse_thread_count
    assert parse_thread_count(17194) >= 1

def test_detect_thread_leak_detects_growth():
    from aura_health import detect_thread_leak
    assert detect_thread_leak(47, 48) is True
    assert detect_thread_leak(47, 47) is False

def test_parse_cpu_delta_from_top():
    from aura_health import parse_cpu_from_top
    sample = "  17194 pythonv+  20   0 2554828 708664  91384 S  45,9   2,2\n"
    assert parse_cpu_from_top(sample) == 45.9

def test_parse_audio_state_running():
    from aura_health import parse_audio_sources
    sample = "39\techo-cancel-source\tPipeWire\tfloat32le 2ch 48000Hz\tRUNNING\n"
    assert parse_audio_sources(sample)["default_running"] is True
