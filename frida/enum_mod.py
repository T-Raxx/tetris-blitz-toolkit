import frida, sys, time
dev = frida.get_device("emulator-5554", timeout=10)
# attach to running game
try:
    session = dev.attach("Tetris Blitz")
except Exception as e:
    print("attach failed, spawning:", e)
    pid = dev.spawn(["com.ea.tetrisblitz_row"]); session = dev.attach(pid); dev.resume(pid); time.sleep(6)
js = """
const mods = Process.enumerateModules();
send('TOTAL ' + mods.length);
mods.filter(m => /tetris|app|game|blitz|unity|cocos|il2|libc\+\+|libjs/i.test(m.name))
    .forEach(m => send('MOD ' + m.name + ' | ' + m.path + ' | base=' + m.base + ' size=' + m.size));
const t = Process.findModuleByName('libTetrisBlitzApp.so');
send('findByName libTetrisBlitzApp.so => ' + (t ? ('FOUND base='+t.base) : 'NULL'));
// also list any module whose path mentions the package
mods.filter(m => /tetrisblitz_row/.test(m.path||'')).forEach(m => send('PKGPATH ' + m.name + ' | ' + m.path));
"""
out=[]
def on_msg(m,d):
    if m["type"]=="send": print(m["payload"])
    elif m["type"]=="error": print("ERR", m.get("stack"))
s = session.create_script(js); s.on("message", on_msg); s.load()
time.sleep(2)
