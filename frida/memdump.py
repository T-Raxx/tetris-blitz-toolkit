import frida, time
dev = frida.get_device("emulator-5554", timeout=10)
session = dev.attach("Tetris Blitz")
js = r"""
function dumpAround(needle, before, after){
  const pat = Array.from(needle).map(c=>('0'+c.charCodeAt(0).toString(16)).slice(-2)).join(' ');
  const ranges = Process.enumerateRanges('r--');
  let shown=0;
  for (const r of ranges){
    let res=[]; try{res=Memory.scanSync(r.base, r.size, pat);}catch(e){continue;}
    for (const m of res){
      const start = m.address.sub(before);
      let bytes; try{bytes=start.readByteArray(before+after);}catch(e){continue;}
      const u8=new Uint8Array(bytes);
      let s=''; for(let i=0;i<u8.length;i++){const c=u8[i]; s+=(c>=32&&c<127)?String.fromCharCode(c):'.';}
      send('=== ['+needle+'] @'+m.address+' ===\n'+s);
      if(++shown>=2) return;
    }
  }
}
dumpAround("formatVersion", 40, 400);
dumpAround("\"coins\"", 60, 200);
send('__END__');
"""
def on(m,d):
    if m["type"]=="send": print(m["payload"])
    elif m["type"]=="error": print("ERR", m.get("stack"))
s=session.create_script(js); s.on("message",on); s.load()
time.sleep(15)
