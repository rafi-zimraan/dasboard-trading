#!/usr/bin/env python3
"""Dashboard trading harian — server lokal, hanya baca.

  python3 server.py                # buka http://127.0.0.1:8787
  python3 server.py --port 9000
  python3 server.py --no-monitor   # jangan jalankan monitor.py otomatis

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

from core import bybit, monitor_bridge, screening, trending  # noqa: E402

WEB = HERE / "web"
PLANS = Path.home() / "trading-exec" / "trade_plans.json"
TOKEN_FILE = Path.home() / ".trading-dashboard-token"


def token() -> str:
    """Token wajib untuk SEMUA permintaan.

    Halaman ini memuat isi akun sungguhan — ekuitas, posisi, SL, riwayat PnL.
    Begitu diekspos lewat tunnel, URL saja bukan pengaman: alamat tunnel bocor
    lewat riwayat browser, header referer, dan pemindai otomatis. Token dipakai
    selalu, bahkan di localhost, supaya tidak ada mode "kebetulan tanpa kunci".
    """
    t = os.environ.get("DASH_TOKEN", "").strip()
    if t:
        return t
    if TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text().strip()
        if t:
            return t
    t = secrets.token_urlsafe(24)
    TOKEN_FILE.write_text(t)
    TOKEN_FILE.chmod(0o600)
    return t


TOKEN = token()


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
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _terotorisasi(self, q: dict) -> bool:
        """Token boleh datang dari cookie, query ?t=, atau header Authorization.

        compare_digest dipakai supaya waktu perbandingan tidak membocorkan
        tebakan yang hampir benar.
        """
        for kandidat in (
            (self.headers.get("Cookie") or "").split("dash_token=")[-1].split(";")[0].strip(),
            (q.get("t") or [""])[0],
            (self.headers.get("Authorization") or "").removeprefix("Bearer ").strip(),
        ):
            if kandidat and secrets.compare_digest(kandidat, TOKEN):
                return True
        return False

    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        path = u.path
        q = parse_qs(u.query)

        if not self._terotorisasi(q):
            body = b"401 - token tidak sah. Buka lewat tautan lengkap yang dicetak server."
            self._kirim(401, body, "text/plain; charset=utf-8")
            return

        # Token yang datang lewat URL langsung dipindahkan ke cookie, lalu URL
        # dibersihkan — supaya token tidak menetap di riwayat browser dan tidak
        # ikut tersalin saat alamat dibagikan.
        if q.get("t") and path == "/":
            self._kirim(302, b"", "text/plain", {
                "Location": "/",
                "Set-Cookie": f"dash_token={TOKEN}; Path=/; Max-Age=2592000; "
                              f"HttpOnly; SameSite=Lax",
            })
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
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"\n  Dashboard trading  ->  http://127.0.0.1:{port}/?t={TOKEN}\n")
    print(f"  Token tersimpan di {TOKEN_FILE} (chmod 600).")
    print("  Semua permintaan wajib membawa token — termasuk dari localhost.\n")
    print("  Server ini hanya membaca. Untuk membuka posisi:")
    print("  python3 ~/trading-exec/order.py SYMBOL side qty lev entry sl tp1 [tp2] --live\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
