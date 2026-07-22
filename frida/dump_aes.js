'use strict';
// Frida 17 API. Dumps AES key material from OpenSSL init calls.
// The game statically links OpenSSL inside libTetrisBlitzApp.so (loaded late),
// so we wait for that module, then hook its internal EVP/AES inits.
// Also hook system libcrypto/libssl as a safety net.
const APP = 'libTetrisBlitzApp.so';

function hex(ptr, len) {
  try {
    return Array.from(new Uint8Array(ptr.readByteArray(len)))
      .map(b => ('0' + b.toString(16)).slice(-2)).join('');
  } catch (e) { return '<unreadable:' + e + '>'; }
}

function resolveIn(mod, name) {
  try { const a = mod.findExportByName(name); if (a) return a; } catch (e) {}
  try {
    const s = mod.enumerateSymbols().find(s => s.name === name && !s.address.isNull());
    if (s) return s.address;
  } catch (e) {}
  return null;
}

function hookEVPInit(mod) {
  const a = resolveIn(mod, 'EVP_DecryptInit_ex');
  if (!a) return false;
  Interceptor.attach(a, {
    onEnter(args) {                 // ctx, type, impl, key, iv
      if (!args[3].isNull()) console.log('[EVP.dec] key(32B)=' + hex(args[3], 32) + '  (' + mod.name + ')');
      if (!args[4].isNull()) console.log('[EVP.dec] iv(16B) =' + hex(args[4], 16));
    }
  });
  console.log('[+] hooked EVP_DecryptInit_ex @ ' + a + ' (' + mod.name + ')');
  return true;
}

function hookEVPCipher(mod) {
  const a = resolveIn(mod, 'EVP_CipherInit_ex');
  if (!a) return false;
  Interceptor.attach(a, {
    onEnter(args) {                 // ctx, type, impl, key, iv, enc
      const enc = args[6];
      if (!args[3].isNull()) console.log('[EVP.cip] enc=' + (enc && !enc.isNull() ? enc.toInt32() : '?') + ' key=' + hex(args[3], 32) + '  (' + mod.name + ')');
      if (!args[4].isNull()) console.log('[EVP.cip] iv =' + hex(args[4], 16));
    }
  });
  console.log('[+] hooked EVP_CipherInit_ex @ ' + a + ' (' + mod.name + ')');
  return true;
}

function hookAES(mod) {
  const a = resolveIn(mod, 'AES_set_decrypt_key');
  if (!a) return false;
  Interceptor.attach(a, {
    onEnter(args) {                 // userKey, bits, aeskey
      const bits = args[1].toInt32();
      console.log('[AES.dec] bits=' + bits + ' key=' + hex(args[0], bits / 8) + '  (' + mod.name + ')');
    }
  });
  console.log('[+] hooked AES_set_decrypt_key @ ' + a + ' (' + mod.name + ')');
  return true;
}

function hookAll(mod) {
  const a = hookEVPInit(mod), b = hookEVPCipher(mod), c = hookAES(mod);
  if (!(a || b || c)) console.log('[!] no crypto init symbols resolved in ' + mod.name);
}

function whenLoaded(name, cb) {
  const m = Process.findModuleByName(name);
  if (m) { cb(m); return; }
  const id = setInterval(() => {
    const mm = Process.findModuleByName(name);
    if (mm) { clearInterval(id); cb(mm); }
  }, 30);
}

// safety net: hook system crypto libs already present
Process.enumerateModules()
  .filter(m => /^libcrypto\.so$|^libssl\.so$/.test(m.name))
  .forEach(m => { console.log('[i] safety-net hook ' + m.name + ' @ ' + m.base); hookAll(m); });

// primary: wait for the app lib, report its symbol availability, hook internals
whenLoaded(APP, m => {
  console.log('[i] ' + APP + ' loaded base=' + m.base + ' size=' + m.size);
  let ex = -1, sy = -1;
  try { ex = m.enumerateExports().length; } catch (e) {}
  try { sy = m.enumerateSymbols().length; } catch (e) {}
  console.log('[i] ' + APP + ' exports=' + ex + ' symbols=' + sy);
  hookAll(m);
});
