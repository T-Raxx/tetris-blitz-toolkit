import frida, time
dev = frida.get_device("emulator-5554", timeout=10)
session = dev.attach("Tetris Blitz")
js = r"""
const needles = ["formatVersion","Coefficient","coefficient","GameplayCoeff","PlayerData","\"coins\"","BonusBoards","matrixWidth"];
function scanAll(){
  const ranges = Process.enumerateRanges('r--');
  send('ranges='+ranges.length);
  let total=0;
  for (const n of needles){
    let found=0;
    const pat = Array.from(n).map(c=>('0'+c.charCodeAt(0).toString(16)).slice(-2)).join(' ');
    for (const r of ranges){
      try {
        const res = Memory.scanSync(r.base, r.size, pat);
        if (res.length){
          found += res.length;
          if (found<=2){
            const ctx = res[0].address.readUtf8String(120);
            send('HIT ['+n+'] @'+res[0].address+' ctx='+JSON.stringify(ctx));
          }
        }
      } catch(e){}
    }
    send('NEEDLE '+n+' total='+found);
    total+=found;
  }
  send('DONE total='+total);
}
scanAll();
"""
def on(m,d):
    if m["type"]=="send": print(m["payload"])
    elif m["type"]=="error": print("ERR", m.get("stack"))
s=session.create_script(js); s.on("message",on); s.load()
time.sleep(20)
