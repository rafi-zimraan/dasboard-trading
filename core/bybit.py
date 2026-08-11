"""Klien Bybit v5 baca-saja untuk dashboard.

Sengaja dipisah dari ~/trading-exec/bybit_trade.py: file ini TIDAK PERNAH
mengirim order. Dashboard hanya boleh membaca — satu-satunya jalur yang bisa
membuka posisi tetap eksekutor manual di terminal.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.request
from pathlib import Path

BASE = "https://api.bybit.com"
RECV = "15000"
_offset = 0

# Modal awal dan target dibaca dari panduan (satu sumber kebenaran), bukan
# ditulis ulang di sini. Angka $85 yang sempat dipakai keliru: rekonsiliasi
# wallet ($77,22) dikurangi realized kumulatif ($21,55) memberi setoran ~$55,7,
# yang cocok dengan $59 di panduan, bukan $85.
from . import panduan as _panduan

MODAL_AWAL = _panduan.modal_awal()
TARGET = _panduan.target()


def _keys() -> tuple[str, str]:
    kv = {}
    for line in (Path.home() / ".bybit_keys").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv["KEY"], kv["SECRET"]


def _fetch(req, tries: int = 3):
    last = None
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(0.4)
    raise RuntimeError(f"bybit fetch gagal: {last}")


def sync_clock() -> None:
    """Jam Mac bisa meleset belasan detik dari server Bybit -> error 10002 saat sign."""
    global _offset
    srv = int(_fetch(urllib.request.Request(BASE + "/v5/market/time"))["result"]["timeNano"])
    _offset = srv // 1_000_000 - int(time.time() * 1000)


def signed_get(path: str, qs: str):
    key, secret = _keys()
    ts = str(int(time.time() * 1000) + _offset)
    sign = hmac.new(secret.encode(), (ts + key + RECV + qs).encode(), hashlib.sha256).hexdigest()
    return _fetch(urllib.request.Request(
        f"{BASE}{path}?{qs}",
        headers={"X-BAPI-API-KEY": key, "X-BAPI-TIMESTAMP": ts,
                 "X-BAPI-RECV-WINDOW": RECV, "X-BAPI-SIGN": sign}))


def public(path: str):
    return _fetch(urllib.request.Request(BASE + path, headers={"User-Agent": "dashboard/1.0"}))


# --- pembacaan tingkat tinggi ---------------------------------------------

def wallet() -> dict:
    coins = signed_get("/v5/account/wallet-balance", "accountType=UNIFIED")["result"]["list"][0]["coin"]
    u = next((c for c in coins if c["coin"] == "USDT"), {})

    def f(k):
        try:
            return float(u.get(k) or 0)
        except ValueError:
            return 0.0

    equity = f("equity")
    return {
        "equity": equity,
        "wallet": f("walletBalance"),
        "unrealised": f("unrealisedPnl"),
        "realised_kumulatif": f("cumRealisedPnl"),
        "modal_awal": MODAL_AWAL,
        "target": TARGET,
        # Progres diukur dari modal awal, bukan dari nol — 0% berarti belum
        # menghasilkan apa pun, 100% berarti target tercapai.
        "progres_pct": max(0.0, (equity - MODAL_AWAL) / (TARGET - MODAL_AWAL) * 100),
        "pertumbuhan_pct": (equity / MODAL_AWAL - 1) * 100 if MODAL_AWAL else 0,
    }


def positions() -> list[dict]:
    raw = signed_get("/v5/position/list", "category=linear&settleCoin=USDT&limit=20")["result"]["list"]
    out = []
    for p in raw:
        if float(p["size"]) <= 0:
            continue
        entry, mark = float(p["avgPrice"]), float(p["markPrice"])
        long = p["side"] == "Buy"
        sl = float(p["stopLoss"]) if p["stopLoss"] else None
        # Risiko sisa: kalau SL sudah melewati entry ke sisi profit, risikonya nol.
        risiko = 0.0
        if sl:
            per_koin = (entry - sl) if long else (sl - entry)
            risiko = max(0.0, per_koin * float(p["size"]))
        out.append({
            "symbol": p["symbol"], "side": "LONG" if long else "SHORT",
            "size": float(p["size"]), "entry": entry, "mark": mark,
            "liq": float(p["liqPrice"]) if p["liqPrice"] else None,
            "leverage": float(p["leverage"]), "value": float(p["positionValue"]),
            "unrealised": float(p["unrealisedPnl"]),
            "realised": float(p.get("curRealisedPnl") or 0),
            "sl": sl, "margin": float(p.get("positionIM") or 0),
            "pnl_pct": ((mark / entry - 1) * 100) * (1 if long else -1),
            "risiko_sisa": risiko,
            "sl_aman": bool(sl and ((sl >= entry) if not long else (sl <= entry)) is False),
        })
    return out


def open_orders() -> list[dict]:
    raw = signed_get("/v5/order/realtime", "category=linear&settleCoin=USDT&limit=50")["result"]["list"]
    out = []
    for o in raw:
        harga = float(o["price"]) if o["price"] != "0" else None
        sl = float(o["stopLoss"]) if o.get("stopLoss") and o["stopLoss"] != "0" else None
        # Order entry yang masih menggantung TETAP membawa risiko: begitu terisi,
        # jarak ke SL langsung jadi uang. Tidak menghitungnya membuat plafon 15%
        # terlihat longgar padahal sudah terpakai.
        risiko = abs(harga - sl) * float(o["qty"]) if (harga and sl and not o["reduceOnly"]) else 0.0
        out.append({
            "symbol": o["symbol"], "side": o["side"], "type": o["orderType"],
            "qty": float(o["qty"]), "price": harga,
            "trigger": float(o["triggerPrice"]) if o.get("triggerPrice") else None,
            "reduce_only": o["reduceOnly"], "kind": o.get("stopOrderType") or "Limit",
            "status": o["orderStatus"], "created": int(o["createdTime"]),
            "sl": sl, "tp": float(o["takeProfit"]) if o.get("takeProfit") and o["takeProfit"] != "0" else None,
            "risiko_tertunda": risiko,
        })
    return out


def closed_pnl(limit: int = 100) -> list[dict]:
    raw = signed_get("/v5/position/closed-pnl", f"category=linear&limit={limit}")["result"]["list"]
    rows = [{
        "symbol": c["symbol"],
        # side pada closed-pnl = sisi order PENUTUP, jadi dibalik agar jadi arah posisi.
        "side": "SHORT" if c["side"] == "Buy" else "LONG",
        "qty": float(c["qty"]), "entry": float(c["avgEntryPrice"]),
        "exit": float(c["avgExitPrice"]), "pnl": float(c["closedPnl"]),
        "leverage": float(c["leverage"]), "closed_at": int(c["updatedTime"]),
    } for c in raw]
    rows.sort(key=lambda r: r["closed_at"])
    return rows


def kurva_ekuitas(rows: list[dict], equity_now: float) -> list[dict]:
    """Kurva ekuitas dari riwayat closed PnL, ditutup dengan ekuitas live."""
    saldo = MODAL_AWAL
    titik = [{"t": rows[0]["closed_at"] - 3600_000 if rows else int(time.time() * 1000),
              "equity": saldo, "label": "modal awal"}]
    for r in rows:
        saldo += r["pnl"]
        titik.append({"t": r["closed_at"], "equity": round(saldo, 4),
                      "label": f"{r['symbol']} {r['pnl']:+.2f}"})
    titik.append({"t": int(time.time() * 1000), "equity": round(equity_now, 4),
                  "label": "ekuitas sekarang (termasuk floating)"})
    return titik


def statistik(rows: list[dict]) -> dict:
    if not rows:
        return {"total": 0, "menang": 0, "kalah": 0, "winrate": 0.0,
                "profit_factor": 0.0, "rata_menang": 0.0, "rata_kalah": 0.0, "net": 0.0}
    menang = [r["pnl"] for r in rows if r["pnl"] > 0]
    kalah = [r["pnl"] for r in rows if r["pnl"] <= 0]
    gross_u = sum(menang)
    gross_r = abs(sum(kalah))
    return {
        "total": len(rows), "menang": len(menang), "kalah": len(kalah),
        "winrate": len(menang) / len(rows) * 100,
        "profit_factor": (gross_u / gross_r) if gross_r else float("inf") if gross_u else 0.0,
        "rata_menang": (gross_u / len(menang)) if menang else 0.0,
        "rata_kalah": (-gross_r / len(kalah)) if kalah else 0.0,
        "net": gross_u - gross_r,
    }
