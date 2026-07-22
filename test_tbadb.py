import tbadb

class FakeRun:
    def __init__(self, script): self.script, self.calls = script, []
    def __call__(self, args):
        self.calls.append(args)
        return self.script(args)

def test_device_detects_emulator():
    run = FakeRun(lambda a: (0, b"List of devices attached\nemulator-5554\tdevice\n"))
    assert tbadb.device(run=run) == "emulator-5554"

def test_device_none_when_offline():
    run = FakeRun(lambda a: (0, b"List of devices attached\n"))
    assert tbadb.device(run=run) is None

def test_pull_reads_bytes(tmp_path, monkeypatch):
    payload = b"\x01\x02\x03\x04"
    def script(a):
        if a[:2] == ["-s", "emulator-5554"] and "pull" in a:
            open(a[-1], "wb").write(payload); return (0, b"1 file pulled")
        return (0, b"")
    got = tbadb.pull("/sdcard/x.bin", run=FakeRun(script))
    assert got == payload

def test_push_writes_backup_first(tmp_path):
    remote = "/sdcard/Android/data/com.ea.tetrisblitz_row/files/PlayerData.json"
    pulled = b"OLDSAVE"
    order = []
    def script(a):
        if "pull" in a:
            open(a[-1], "wb").write(pulled); order.append("pull"); return (0, b"")
        if "push" in a: order.append("push"); return (0, b"")
        order.append("shell"); return (0, b"")
    bak = tbadb.push(remote, b"NEWSAVE", backup_dir=str(tmp_path), run=FakeRun(script))
    assert order.index("pull") < order.index("push")   # backup before push
    assert open(bak, "rb").read() == pulled
