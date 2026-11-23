// 署名（BIP340 Schnorr / secp256k1）と Nostr のイベント。外部の部品を使わずに書いている。
// 公式の試験ベクトル（tests/sig.test.js）で正しさを確かめている。
"use strict";
(function (root) {
  const P = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2fn;
  const N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141n;
  const GX = 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798n;
  const GY = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8n;
  const mod = (a, m = P) => { const r = a % m; return r >= 0n ? r : r + m; };
  const pow = (b, e, m = P) => { let r = 1n; b = mod(b, m); while (e > 0n) { if (e & 1n) r = r * b % m; b = b * b % m; e >>= 1n; } return r; };
  const inv = (a, m = P) => { let [x, y, u, v] = [mod(a, m), m, 1n, 0n]; while (x !== 0n) { const q = y / x; [x, y] = [y - q * x, x]; [u, v] = [v - q * u, u]; } return mod(v, m); };

  // ヤコビ座標の点 [X, Y, Z]（Z=0 は無限遠点）
  const O = [0n, 1n, 0n];
  function dbl([X, Y, Z]) {
    if (Z === 0n || Y === 0n) return O;
    const A = X * X % P, B = Y * Y % P, C = B * B % P;
    const D = mod(2n * (mod((X + B) ** 2n) - A - C)), E = 3n * A % P, F = E * E % P;
    const X3 = mod(F - 2n * D), Y3 = mod(E * (D - X3) - 8n * C), Z3 = 2n * Y * Z % P;
    return [X3, Y3, Z3];
  }
  function add(p1, p2) {
    if (p1[2] === 0n) return p2; if (p2[2] === 0n) return p1;
    const [X1, Y1, Z1] = p1, [X2, Y2, Z2] = p2;
    const Z1Z1 = Z1 * Z1 % P, Z2Z2 = Z2 * Z2 % P;
    const U1 = X1 * Z2Z2 % P, U2 = X2 * Z1Z1 % P, S1 = Y1 * Z2 % P * Z2Z2 % P, S2 = Y2 * Z1 % P * Z1Z1 % P;
    if (U1 === U2) return S1 === S2 ? dbl(p1) : O;
    const H = mod(U2 - U1), I = (2n * H) ** 2n % P, J = H * I % P, r = mod(2n * (S2 - S1)), V = U1 * I % P;
    const X3 = mod(r * r - J - 2n * V), Y3 = mod(r * (V - X3) - 2n * S1 * J), Z3 = mod(((Z1 + Z2) ** 2n - Z1Z1 - Z2Z2) * H);
    return [X3, Y3, Z3];
  }
  function mul(pt, k) { let R = O, Q = pt; while (k > 0n) { if (k & 1n) R = add(R, Q); Q = dbl(Q); k >>= 1n; } return R; }
  function affine([X, Y, Z]) { if (Z === 0n) return null; const zi = inv(Z), z2 = zi * zi % P; return [X * z2 % P, Y * z2 % P * zi % P]; }
  const G = [GX, GY, 1n];
  // G の倍数は表を作っておく（署名と確認を速くする）
  const GT = []; { let q = G; for (let i = 0; i < 256; i++) { GT.push(q); q = dbl(q); } }
  function mulG(k) { let R = O; for (let i = 0; k > 0n; i++, k >>= 1n) if (k & 1n) R = add(R, GT[i]); return R; }

  const hex = b => Array.from(b, x => x.toString(16).padStart(2, "0")).join("");
  const unhex = h => Uint8Array.from(h.match(/../g) || [], x => parseInt(x, 16));
  const num = b => BigInt("0x" + (hex(b) || "0"));
  const n32 = x => unhex(x.toString(16).padStart(64, "0"));
  const cat = (...a) => { const o = new Uint8Array(a.reduce((s, x) => s + x.length, 0)); let i = 0; for (const x of a) { o.set(x, i); i += x.length; } return o; };
  const enc = new TextEncoder();
  const subtle = (root.crypto && root.crypto.subtle) || require("crypto").webcrypto.subtle;
  const sha = async b => new Uint8Array(await subtle.digest("SHA-256", b));
  const tagged = async (tag, ...m) => { const t = await sha(enc.encode(tag)); return sha(cat(t, t, ...m)); };

  function liftX(x) {
    if (x >= P) return null;
    const c = mod(x ** 3n + 7n), y = pow(c, (P + 1n) / 4n);
    if (y * y % P !== c) return null;
    return [x, y & 1n ? P - y : y, 1n];
  }
  function pubkey(sk) { const d = num(sk); if (d <= 0n || d >= N) throw new Error("bad key"); return n32(affine(mulG(d))[0]); }
  async function sign(msg, sk, aux) {
    let d = num(sk); if (d <= 0n || d >= N) throw new Error("bad key");
    const Pa = affine(mulG(d)); if (Pa[1] & 1n) d = N - d;
    const px = n32(Pa[0]);
    const t = n32(d ^ num(await tagged("BIP0340/aux", aux)));
    const k0 = mod(num(await tagged("BIP0340/nonce", t, px, msg)), N); if (k0 === 0n) throw new Error("bad nonce");
    const R = affine(mulG(k0)); const k = R[1] & 1n ? N - k0 : k0;
    const rx = n32(R[0]);
    const e = mod(num(await tagged("BIP0340/challenge", rx, px, msg)), N);
    return cat(rx, n32(mod(k + e * d, N)));
  }
  async function verify(msg, pk, sig) {
    try {
      if (sig.length !== 64 || pk.length !== 32) return false;
      const Pp = liftX(num(pk)); if (!Pp) return false;
      const r = num(sig.slice(0, 32)), s = num(sig.slice(32)); if (r >= P || s >= N) return false;
      const e = mod(num(await tagged("BIP0340/challenge", sig.slice(0, 32), pk, msg)), N);
      const R = affine(add(mulG(s), mul(Pp, N - e)));
      return !!R && !(R[1] & 1n) && R[0] === r;
    } catch (e) { return false; }
  }

  // ---------- Nostr のイベント ----------
  async function eventId(ev) { return hex(await sha(enc.encode(JSON.stringify([0, ev.pubkey, ev.created_at, ev.kind, ev.tags, ev.content])))); }
  async function signEvent(tmpl, skHex) {
    const sk = unhex(skHex);
    const ev = {kind: tmpl.kind, created_at: tmpl.created_at || Math.floor(Date.now() / 1000), tags: tmpl.tags || [], content: tmpl.content || "", pubkey: hex(pubkey(sk))};
    ev.id = await eventId(ev);
    ev.sig = hex(await sign(unhex(ev.id), sk, (root.crypto || require("crypto").webcrypto).getRandomValues(new Uint8Array(32))));
    return ev;
  }
  async function verifyEvent(ev) {
    if (!ev || typeof ev.id !== "string" || ev.id !== await eventId(ev)) return false;
    return verify(unhex(ev.id), unhex(ev.pubkey), unhex(ev.sig));
  }
  function newKey() { for (;;) { const b = (root.crypto || require("crypto").webcrypto).getRandomValues(new Uint8Array(32)); const d = num(b); if (d > 0n && d < N) return hex(b); } }

  // 共有の秘密（ECDH）：自分のかぎ × 相手の番号。どちらの側から計算しても同じ32バイトになる（x座標だけを使う）
  function shared(skHex, pkHex) {
    const d = num(unhex(skHex)); if (d <= 0n || d >= N) throw new Error("bad key");
    const Pp = liftX(num(unhex(pkHex))); if (!Pp) throw new Error("bad pubkey");
    return n32(affine(mul(Pp, d))[0]);
  }
  // 公開鍵の点（x と y）。チェーン（Base など）のアドレスを作るときに使う
  function pubXY(skHex) { const d = num(unhex(skHex)); if (d <= 0n || d >= N) throw new Error("bad key"); const [x, y] = affine(mulG(d)); return cat(n32(x), n32(y)); }
  // 32バイトを、かぎとして使える数にする（0 と N 以上を避ける）
  function toKey(bytes) { const d = mod(num(bytes), N - 1n) + 1n; return hex(n32(d)); }
  const api = {sign, verify, pubkey, signEvent, verifyEvent, eventId, newKey, hex, unhex, shared, sha, pubXY, toKey};
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Sig = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
