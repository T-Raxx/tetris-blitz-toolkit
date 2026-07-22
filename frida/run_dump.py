import frida, sys, time

DEVICE = "emulator-5554"
PKG = "com.ea.tetrisblitz_row"
DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0

dev = frida.get_device(DEVICE, timeout=10)
print(f"[*] device: {dev}")
pid = dev.spawn([PKG])
print(f"[*] spawned pid={pid}")
session = dev.attach(pid)
script = session.create_script(open("frida/dump_aes.js", encoding="utf-8").read())

def on_message(msg, data):
    if msg["type"] == "log":
        print(msg["payload"])
    elif msg["type"] == "error":
        print("[SCRIPT ERROR]", msg.get("stack", msg))

script.on("message", on_message)
script.load()
dev.resume(pid)
print(f"[*] resumed; collecting for {DURATION}s ...")
time.sleep(DURATION)
print("[*] done")
try:
    session.detach()
except Exception:
    pass
