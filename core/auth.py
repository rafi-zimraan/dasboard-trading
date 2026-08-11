"""Login, sesi, dan penahan serangan tebak-password.

Prinsip yang dipegang di sini:

- Password TIDAK PERNAH disimpan. Yang disimpan hanya turunan scrypt beserta
  garamnya, di luar repo (`~/.trading-dashboard-auth`, chmod 600). Repo ini
  publik — apa pun yang masuk ke dalamnya dianggap sudah bocor.
- Semua perbandingan rahasia memakai compare_digest, supaya lama waktu
  perbandingan tidak membocorkan seberapa dekat tebakan penyerang.
- Sesi hidup di memori saja. Server restart = semua sesi mati. Itu disengaja:
  tidak ada berkas sesi yang bisa dicuri.
- Percobaan gagal dihitung per alamat IP dan dikunci makin lama. Password
  sekuat apa pun kalah kalau penyerang boleh menebak tanpa batas.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
from pathlib import Path

AUTH_FILE = Path.home() / ".trading-dashboard-auth"

# scrypt: mahal secara sengaja supaya menebak massal jadi tidak ekonomis.
# 128 * N * r = 32 MB per percobaan. OpenSSL menolak di atas batas maxmem
# bawaannya (juga 32 MB), jadi batasnya dinaikkan eksplisit — tanpa ini
# hashlib.scrypt melempar "memory limit exceeded".
N, R, P, DKLEN = 2 ** 15, 8, 1, 32
MAXMEM = 128 * N * R * 2

SESI_UMUR = 12 * 3600          # 12 jam
GAGAL_MAKS = 5                 # sebelum kunci pertama
KUNCI_DASAR = 60               # detik, dilipatduakan tiap ronde gagal berikutnya
KUNCI_MAKS = 3600

_lock = threading.Lock()
_sesi: dict[str, dict] = {}
_gagal: dict[str, dict] = {}


# --- kredensial ------------------------------------------------------------

def _turunkan(password: str, garam: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=garam, n=N, r=R, p=P,
                          dklen=DKLEN, maxmem=MAXMEM)


def simpan_kredensial(email: str, password: str) -> None:
    garam = secrets.token_bytes(16)
    AUTH_FILE.write_text(json.dumps({
        "email": email.strip().lower(),
        "garam": garam.hex(),
        "hash": _turunkan(password, garam).hex(),
        "params": {"n": N, "r": R, "p": P, "dklen": DKLEN},
        "dibuat": int(time.time()),
    }, indent=2))
    AUTH_FILE.chmod(0o600)


def ada_kredensial() -> bool:
    return AUTH_FILE.exists()


def _baca() -> dict | None:
    if not AUTH_FILE.exists():
        return None
    try:
        return json.loads(AUTH_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def verifikasi(email: str, password: str) -> bool:
    d = _baca()
    if not d:
        return False
    p = d.get("params", {})
    try:
        n, r = p.get("n", N), p.get("r", R)
        calon = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(d["garam"]),
            n=n, r=r, p=p.get("p", P), dklen=p.get("dklen", DKLEN),
            maxmem=128 * n * r * 2)
    except (ValueError, KeyError):
        return False
    # Kedua perbandingan dijalankan penuh: email yang salah tidak boleh
    # menghasilkan jawaban lebih cepat daripada password yang salah.
    email_ok = secrets.compare_digest(email.strip().lower(), d.get("email", ""))
    pass_ok = secrets.compare_digest(calon.hex(), d.get("hash", ""))
    return email_ok and pass_ok


# --- penahan tebakan -------------------------------------------------------

def sisa_kunci(ip: str) -> int:
    with _lock:
        g = _gagal.get(ip)
        if not g:
            return 0
        sisa = int(g.get("sampai", 0) - time.time())
        return max(0, sisa)


def catat_gagal(ip: str) -> int:
    """Kembalikan berapa detik IP ini terkunci setelah kegagalan barusan."""
    with _lock:
        g = _gagal.setdefault(ip, {"n": 0, "sampai": 0})
        g["n"] += 1
        if g["n"] >= GAGAL_MAKS:
            ronde = g["n"] - GAGAL_MAKS
            durasi = min(KUNCI_MAKS, KUNCI_DASAR * (2 ** ronde))
            g["sampai"] = time.time() + durasi
            return int(durasi)
        return 0


def bersihkan_gagal(ip: str) -> None:
    with _lock:
        _gagal.pop(ip, None)


# --- sesi ------------------------------------------------------------------

def buat_sesi(email: str, ip: str) -> str:
    sid = secrets.token_urlsafe(32)
    with _lock:
        _sesi[sid] = {"email": email, "ip": ip, "kadaluarsa": time.time() + SESI_UMUR}
    return sid


def sesi_sah(sid: str | None) -> bool:
    if not sid:
        return False
    with _lock:
        s = _sesi.get(sid)
        if not s:
            return False
        if s["kadaluarsa"] < time.time():
            _sesi.pop(sid, None)
            return False
        return True


def hapus_sesi(sid: str | None) -> None:
    if sid:
        with _lock:
            _sesi.pop(sid, None)


def sapu_kadaluarsa() -> None:
    now = time.time()
    with _lock:
        for sid in [k for k, v in _sesi.items() if v["kadaluarsa"] < now]:
            _sesi.pop(sid, None)
        for ip in [k for k, v in _gagal.items()
                   if v.get("sampai", 0) < now - 86400 and v.get("n", 0) < GAGAL_MAKS]:
            _gagal.pop(ip, None)


# --- token untuk skrip (curl, cron) ---------------------------------------

TOKEN_FILE = Path.home() / ".trading-dashboard-token"


def token() -> str:
    """Token panjang-acak untuk akses non-browser (Authorization: Bearer).

    Ini BUKAN pengganti login; dia ada supaya skrip tidak perlu menyimpan
    password. Nilainya 32 byte acak — jauh lebih kuat daripada password mana
    pun yang diketik manusia.
    """
    t = os.environ.get("DASH_TOKEN", "").strip()
    if t:
        return t
    if TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text().strip()
        if t:
            return t
    t = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(t)
    TOKEN_FILE.chmod(0o600)
    return t
