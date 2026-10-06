from aura.agents.obd_scanner import AgentOBDScanner, DTC_HINTS

def test_init():
    a = AgentOBDScanner()
    assert a.name == "obd_scanner"

def test_hints():
    assert "P0301" in DTC_HINTS

def test_decode():
    a = AgentOBDScanner()
    assert "пропуск" in a.decode("P0301").lower()

def test_decode_unknown():
    a = AgentOBDScanner()
    assert "не найдена" in a.decode("Z9999")

def test_scan_no_adapter():
    a = AgentOBDScanner("/dev/nonexistent")
    assert "не подключён" in a.scan()
