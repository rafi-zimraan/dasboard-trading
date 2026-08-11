#!/usr/bin/env python3
"""Pasang atau ganti kredensial login dashboard.

  python3 setup_auth.py                      # tanya email & password (tidak tampil)
  python3 setup_auth.py --email a@b.com      # password tetap ditanya
  python3 setup_auth.py --status             # lihat kredensial terpasang atau belum
  python3 setup_auth.py --reset-token        # buat ulang token untuk skrip

Password TIDAK PERNAH disimpan dan tidak pernah muncul di argumen perintah —
argumen bisa terbaca lewat `ps` oleh proses lain di mesin yang sama, dan
tersimpan di riwayat shell. Yang tersimpan hanya turunan scrypt di
~/.trading-dashboard-auth (chmod 600), di luar repo.
"""

from __future__ import annotations

import getpass
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import auth  # noqa: E402

UMUM = {
    "password", "12345678", "qwerty123", "admin123", "trading123",
    "bismillah", "rahasia", "indonesia",
}


def nilai_password(p: str) -> list[str]:
    """Keluhkan yang lemah — tapi keputusan tetap di tangan pemilik akun."""
    catatan = []
    if len(p) < 12:
        catatan.append(f"panjangnya {len(p)} karakter; 12+ jauh lebih tahan tebakan")
    if p.lower() in UMUM:
        catatan.append("ada di daftar password paling sering dicoba")
    if not re.search(r"[^A-Za-z0-9]", p):
        catatan.append("tidak ada simbol")
    if re.fullmatch(r"[A-Za-z]+\d{1,4}", p):
        catatan.append("polanya 'kata + angka' — pola pertama yang dicoba alat pembobol")
    return catatan


def main(argv: list[str]) -> int:
    if "--status" in argv:
        print(f"kredensial : {'terpasang' if auth.ada_kredensial() else 'BELUM ADA'}"
              f"  ({auth.AUTH_FILE})")
        print(f"token skrip: {'ada' if auth.TOKEN_FILE.exists() else 'belum dibuat'}"
              f"  ({auth.TOKEN_FILE})")
        return 0

    if "--reset-token" in argv:
        if auth.TOKEN_FILE.exists():
            auth.TOKEN_FILE.unlink()
        print(f"Token baru dibuat: {auth.token()}")
        print("Token lama langsung tidak berlaku.")
        return 0

    email = argv[argv.index("--email") + 1] if "--email" in argv else ""
    if not email:
        email = input("Email login: ").strip()
    if "@" not in email:
        print("email tidak sah", file=sys.stderr)
        return 2

    p1 = getpass.getpass("Password baru (tidak ditampilkan): ")
    if not p1:
        print("password kosong", file=sys.stderr)
        return 2
    p2 = getpass.getpass("Ulangi password: ")
    if p1 != p2:
        print("password tidak sama", file=sys.stderr)
        return 1

    catatan = nilai_password(p1)
    if catatan:
        print("\nPeringatan kekuatan password:")
        for c in catatan:
            print(f"  - {c}")
        if input("\nTetap pakai password ini? (ya/tidak): ").strip().lower() not in ("ya", "y"):
            print("dibatalkan.")
            return 1

    auth.simpan_kredensial(email, p1)
    print(f"\nKredensial tersimpan di {auth.AUTH_FILE} (chmod 600).")
    print("Yang disimpan hanya turunan scrypt — password aslinya tidak ada di mana pun.")
    print("Sesi yang sedang berjalan tidak otomatis berakhir; restart server untuk memutus semuanya.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
