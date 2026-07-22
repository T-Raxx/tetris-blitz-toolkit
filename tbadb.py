import subprocess, tempfile, os, time, pathlib

DEV = "emulator-5554"
PKG = "com.ea.tetrisblitz_row"
FILES_DIR = f"/sdcard/Android/data/{PKG}/files"
KNOWN_FILES = [f"{FILES_DIR}/PlayerData.json", f"{FILES_DIR}/NarcSave.json"]

def _run(args):
    p = subprocess.run(["adb", *args], capture_output=True)
    return p.returncode, p.stdout

def device(run=_run):
    _, out = run(["devices"])
    for line in out.decode("utf-8", "replace").splitlines()[1:]:
        s = line.strip()
        if s.endswith("\tdevice") or s.endswith(" device"):
            return s.split()[0]
    return None

def pull(remote, run=_run):
    tmp = f"/sdcard/_tbpull_{int(time.time()*1000)}.bin"
    run(["-s", DEV, "shell", "su", "-c", f"cp '{remote}' {tmp} && chmod 666 {tmp}"])
    fd, local = tempfile.mkstemp(suffix=".bin"); os.close(fd)
    run(["-s", DEV, "pull", tmp, local])
    run(["-s", DEV, "shell", "rm", "-f", tmp])
    data = open(local, "rb").read(); os.remove(local)
    return data

def push(remote, data, backup_dir="backups", run=_run):
    pathlib.Path(backup_dir).mkdir(exist_ok=True)
    bak = os.path.join(backup_dir, f"{os.path.basename(remote)}.{int(time.time())}.bak")
    try:
        open(bak, "wb").write(pull(remote, run=run))    # backup current remote first
    except Exception:
        bak = ""
    fd, local = tempfile.mkstemp(suffix=".bin"); os.close(fd)
    open(local, "wb").write(data)
    tmp = f"/sdcard/_tbpush_{int(time.time()*1000)}.bin"
    run(["-s", DEV, "push", local, tmp])
    run(["-s", DEV, "shell", "su", "-c", f"cp {tmp} '{remote}' && rm -f {tmp}"])
    os.remove(local)
    return bak
