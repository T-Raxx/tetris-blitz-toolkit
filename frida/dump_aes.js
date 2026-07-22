'use strict';
// Dumps AES key material the moment the game inits a decrypt context.
// Hooks both the high-level EVP init and the low-level AES key schedule.
// MuMu runs the arm64 lib via x86 translation; symbols may live in the app
// lib (static OpenSSL) or a separate libcrypto — resolve() covers both.
const LIB = 'libTetrisBlitzApp.so';

function hex(ptr, len) {
  try {
    return Array.from(new Uint8Array(ptr.readByteArray(len)))
      .map(b => ('0' + b.toString(16)).slice(-2)).join('');
  } catch (e) { return '<unreadable ' + e + '>'; }
}

function resolve(name) {
  let a = Module.findExportByName(LIB, name);
  if (a) return a;
  try {
    const s = Module.enumerateSymbols(LIB).find(s => s.name === name && !s.address.isNull());
    if (s) return s.address;
  } catch (e) {}
  return Module.findExportByName(null, name); // any module (separate libcrypto)
}

function diag() {
  console.log('[i] modules of interest:');
  Process.enumerateModules()
    .filter(m => /Tetris|crypto|ssl|js/i.test(m.name))
    .forEach(m => console.log('    ' + m.name + '  base=' + m.base + ' size=' + m.size));
}

function hookEVP() {
  const a = resolve('EVP_DecryptInit_ex');
  if (!a) { console.log('[!] EVP_DecryptInit_ex not found'); return; }
  Interceptor.attach(a, {
    onEnter(args) {
      // int EVP_DecryptInit_ex(ctx, type, impl, key, iv)
      const key = args[3], iv = args[4];
      if (!key.isNull()) console.log('[EVP] key(32B)=' + hex(key, 32));
      if (!iv.isNull())  console.log('[EVP] iv(16B) =' + hex(iv, 16));
    }
  });
  console.log('[+] hooked EVP_DecryptInit_ex @ ' + a);
}

function hookEVPCipher() {
  const a = resolve('EVP_CipherInit_ex');
  if (!a) return;
  Interceptor.attach(a, {
    onEnter(args) {
      const key = args[3], iv = args[4], enc = args[6];
      if (!key.isNull()) console.log('[EVPc] enc=' + (enc && !enc.isNull() ? enc.toInt32() : '?') + ' key=' + hex(key, 32));
      if (!iv.isNull())  console.log('[EVPc] iv =' + hex(iv, 16));
    }
  });
  console.log('[+] hooked EVP_CipherInit_ex @ ' + a);
}

function hookAES() {
  const a = resolve('AES_set_decrypt_key');
  if (!a) { console.log('[!] AES_set_decrypt_key not found'); return; }
  Interceptor.attach(a, {
    onEnter(args) {
      // int AES_set_decrypt_key(userKey, bits, aeskey)
      const bits = args[1].toInt32();
      console.log('[AES] bits=' + bits + ' key=' + hex(args[0], bits / 8));
    }
  });
  console.log('[+] hooked AES_set_decrypt_key @ ' + a);
}

setTimeout(() => { diag(); hookEVP(); hookEVPCipher(); hookAES(); }, 0);
