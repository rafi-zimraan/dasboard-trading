#!/usr/bin/env python3
"""Dashboard trading harian — server lokal, hanya baca.

  python3 server.py                # buka http://127.0.0.1:8787
  python3 server.py --port 9000
  python3 server.py --no-monitor   # jangan jalankan monitor.py otomatis
  python3 setup_auth.py            # pasang / ganti email + password login

Server ini TIDAK BISA mengirim order. Satu-satunya jalur untuk membuka posisi
tetap `python3 ~/trading-exec/order.py`, yang mewajibkan setup digambar dulu di
TradingView dan lolos checklist 6 pertanyaan.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from core import auth, bybit, monitor_bridge, screening, trending  # noqa: E402

WEB = HERE / "web"
PLANS = Path.home() / "trading-exec" / "trade_plans.json"
TOKEN = auth.token()


def akun() -> dict:
    bybit.sync_clock()
    w = bybit.wallet()
    pos = bybit.positions()
    orders = bybit.open_orders()
    closed = bybit.closed_pnl()
    risiko_posisi = sum(p["risiko_sisa"] for p in pos)
    risiko_tertunda = sum(o["risiko_tertunda"] for o in orders)
    # Plafon dihitung atas keduanya — order menggantung sudah mengunci risiko.
    total = risiko_posisi + risiko_tertunda
    return {
        "wallet": w,
        "posisi": pos,
        "orders": orders,
        "closed": closed[::-1][:25],
        "kurva": bybit.kurva_ekuitas(closed, w["equity"]),
        "statistik": bybit.statistik(closed),
        "risiko": {
            "posisi_usd": risiko_posisi,
            "tertunda_usd": risiko_tertunda,
            "terbuka_usd": total,
            "terbuka_pct": total / w["equity"] * 100 if w["equity"] else 0,
            "plafon_pct": 15.0,
            "sisa_slot_usd": max(0.0, w["equity"] * 0.15 - total),
            "maks_per_trade_usd": w["equity"] * 0.05,
        },
    }


def rencana(horizon: str) -> dict:
    a = akun()
    eq = a["wallet"]["equity"]
    risiko_terbuka = a["risiko"]["terbuka_usd"]
    maks = a["risiko"]["maks_per_trade_usd"]
    s = screening.setups(horizon)

    keluar = []
    for st in s["setups"][:10]:
        z = screening.sizing(st, min(maks, 5.0))
        cl = screening.checklist(st, eq, z["risiko_usd"], risiko_terbuka)
        keluar.append({**st, "sizing": z, "checklist": cl,
                       "lolos": all(c["ok"] for c in cl)})
    return {"horizon": horizon, "tf": s["tf"], "at": s["at"], "setups": keluar,
            "ekuitas": eq, "risiko_terbuka": risiko_terbuka}


def rencana_tersimpan() -> list:
    if not PLANS.exists():
        return []
    try:
        d = json.loads(PLANS.read_text())
        return d[::-1][:20] if isinstance(d, list) else [d]
    except json.JSONDecodeError:
        return []


ROUTES = {
    "/api/akun": lambda q: akun(),
    "/api/monitor": lambda q: monitor_bridge.jalankan(force=q.get("force") == ["1"]),
    "/api/trending": lambda q: trending.snapshot(force=q.get("force") == ["1"]),
    "/api/rencana": lambda q: rencana(q.get("horizon", ["harian"])[0]),
    "/api/plans": lambda q: rencana_tersimpan(),
}

MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8", ".json": "application/json"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if "--verbose" in sys.argv:
            super().log_message(fmt, *args)

    def _kirim(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex, nofollow")
        self.send_header("Referrer-Policy", "no-referrer")
        # Tidak ada skrip/gaya inline di halaman ini, jadi CSP boleh seketat
        # mungkin: skrip pihak ketiga yang berhasil disuntikkan tetap tidak
        # akan dieksekusi, dan data tidak bisa dikirim ke domain lain.
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "img-src 'self' data:; connect-src 'self'; form-action 'self'; "
                         "frame-ancestors 'none'; base-uri 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    # --- identitas & sesi --------------------------------------------------

    def _ip(self) -> str:
        """IP asli. Di balik cloudflared, alamat soket selalu 127.0.0.1 —
        tanpa header ini seluruh dunia terhitung satu alamat dan penguncian
        brute-force jadi tidak ada artinya."""
        for h in ("CF-Connecting-IP", "X-Forwarded-For"):
            v = self.headers.get(h)
            if v:
                return v.split(",")[0].strip()
        return self.client_address[0]

    def _cookie(self, nama: str) -> str:
        for bagian in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = bagian.strip().partition("=")
            if k == nama:
                return v.strip()
        return ""

    def _https(self) -> bool:
        return (self.headers.get("X-Forwarded-Proto") or "").lower() == "https"

    def _set_sesi(self, sid: str) -> str:
        aman = "; Secure" if self._https() else ""
        return (f"sid={sid}; Path=/; Max-Age={auth.SESI_UMUR}; "
                f"HttpOnly; SameSite=Strict{aman}")

    def _terotorisasi(self) -> bool:
        if auth.sesi_sah(self._cookie("sid")):
            return True
        # Jalur skrip (curl/cron): token acak 32 byte, bukan password.
        bearer = (self.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
        return bool(bearer and secrets.compare_digest(bearer, TOKEN))

    def _halaman_login(self, pesan: str = "", code: int = 200):
        html = (WEB / "login.html").read_text()
        blok = ""
        if pesan:
            aman = (pesan.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace('"', "&quot;"))
            blok = f'<div class="login-alert"><span class="ic">!</span><span>{aman}</span></div>'
        html = html.replace("<!--PESAN-->", blok).replace("<!--CSRF-->", "")
        self._kirim(code, html.encode(), "text/html; charset=utf-8")

    # --- POST: hanya login & logout, tidak pernah order --------------------

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path

        if path == "/logout":
            auth.hapus_sesi(self._cookie("sid"))
            self._kirim(302, b"", "text/plain",
                        {"Location": "/login", "Set-Cookie": "sid=; Path=/; Max-Age=0"})
            return

        if path != "/login":
            self._kirim(404, b"tidak ada", "text/plain; charset=utf-8")
            return

        ip = self._ip()
        sisa = auth.sisa_kunci(ip)
        if sisa:
            self._halaman_login(
                f"Terlalu banyak percobaan gagal. Coba lagi dalam {sisa} detik.", 429)
            return

        panjang = int(self.headers.get("Content-Length") or 0)
        if panjang > 4096:                       # form login tidak pernah sebesar ini
            self._kirim(413, b"terlalu besar", "text/plain; charset=utf-8")
            return
        form = parse_qs(self.rfile.read(panjang).decode("utf-8", "replace"))
        email = (form.get("email") or [""])[0]
        password = (form.get("password") or [""])[0]

        if not auth.ada_kredensial():
            self._halaman_login(
                "Kredensial belum dipasang. Jalankan: python3 setup_auth.py", 503)
            return

        if auth.verifikasi(email, password):
            auth.bersihkan_gagal(ip)
            sid = auth.buat_sesi(email, ip)
            print(f"  login berhasil: {email} dari {ip}")
            self._kirim(302, b"", "text/plain",
                        {"Location": "/", "Set-Cookie": self._set_sesi(sid)})
            return

        dikunci = auth.catat_gagal(ip)
        print(f"  LOGIN GAGAL dari {ip}" + (f" — dikunci {dikunci}s" if dikunci else ""))
        pesan = ("Email atau password salah."
                 + (f" Alamat Anda dikunci {dikunci} detik." if dikunci else ""))
        self._halaman_login(pesan, 401)

    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        path = u.path
        q = parse_qs(u.query)

        if path == "/login":
            if self._terotorisasi():
                self._kirim(302, b"", "text/plain", {"Location": "/"})
                return
            self._halaman_login()
            return

        if path == "/logout":
            auth.hapus_sesi(self._cookie("sid"))
            self._kirim(302, b"", "text/plain",
                        {"Location": "/login", "Set-Cookie": "sid=; Path=/; Max-Age=0"})
            return

        # style.css dibutuhkan halaman login itu sendiri, jadi boleh tanpa sesi.
        # Isinya tidak mengandung data akun.
        if not self._terotorisasi() and path != "/style.css":
            if path.startswith("/api/"):
                self._kirim(401, json.dumps({"error": "belum masuk"}).encode(),
                            "application/json; charset=utf-8")
            else:
                self._kirim(302, b"", "text/plain", {"Location": "/login"})
            return

        if path in ROUTES:
            try:
                data = ROUTES[path](q)
                body = json.dumps(data, default=str).encode()
                self._kirim(200, body, "application/json; charset=utf-8")
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                body = json.dumps({"error": f"{type(e).__name__}: {e}"}).encode()
                self._kirim(500, body, "application/json; charset=utf-8")
            return

        if path == "/":
            path = "/index.html"
        f = (WEB / path.lstrip("/")).resolve()
        if not str(f).startswith(str(WEB)) or not f.is_file():
            self._kirim(404, b"tidak ada", "text/plain; charset=utf-8")
            return
        self._kirim(200, f.read_bytes(), MIME.get(f.suffix, "application/octet-stream"))


def main() -> int:
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8787

    if "--no-monitor" not in sys.argv:
        monitor_bridge.mulai_otomatis(300)
        print("monitor.py otomatis: aktif (tiap 5 menit, notifikasi hanya untuk aksi baru)")

    # Panaskan cache screener di latar supaya halaman pertama tidak menunggu.
    def panaskan():
        for h in ("harian", "mingguan", "bulanan"):
            try:
                screening.setups(h)
                print(f"  screener {h}: siap")
            except Exception as e:  # noqa: BLE001
                print(f"  screener {h}: gagal — {e}")
    threading.Thread(target=panaskan, daemon=True).start()

    # Tetap mengikat ke 127.0.0.1 walau sedang di-tunnel: cloudflared jalan di
    # mesin ini dan menyambung ke localhost, jadi port-nya tidak perlu terbuka
    # ke jaringan. Pakai --lan hanya kalau memang mau diakses dari HP satu wifi.
    host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"
    # Sapu sesi & catatan kegagalan yang sudah lewat, tiap 10 menit.
    def sapu():
        while True:
            time.sleep(600)
            auth.sapu_kadaluarsa()
    threading.Thread(target=sapu, daemon=True).start()

    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"\n  Dashboard trading  ->  http://127.0.0.1:{port}\n")
    if auth.ada_kredensial():
        print("  Masuk dengan email + password yang sudah dipasang.")
    else:
        print("  !! KREDENSIAL BELUM DIPASANG — jalankan dulu: python3 setup_auth.py")
    print(f"  Token skrip (curl/cron): Authorization: Bearer <isi {auth.TOKEN_FILE}>\n")
    print("  Server ini hanya membaca. Untuk membuka posisi:")
    print("  python3 ~/trading-exec/order.py SYMBOL side qty lev entry sl tp1 [tp2] --live\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
