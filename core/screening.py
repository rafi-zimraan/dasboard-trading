"""Jembatan ke ~/trading-exec/screener.py + rencana harian/mingguan/bulanan.

Screener asli tetap satu sumber kebenaran — file ini tidak menyalin logikanya,
hanya memanggilnya pada beberapa timeframe lalu mengemas hasilnya untuk web.
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path.home() / "trading-exec"))
import screener as S  # noqa: E402

# Horizon -> timeframe Bybit. Rencana harian dibaca dari 1H+4H, mingguan dari
# daily, bulanan dari weekly — struktur yang dipakai memang beda per horizon.
HORIZON = {
    "harian": ["60", "240"],
    "mingguan": ["D"],
    "bulanan": ["W"],
}

_cache: dict[str, dict] = {}
TTL = 600  # detik


def _scan_tf(tf: str, top: int) -> list[dict]:
    uni = S.universe(top)
    hits: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(lambda r: S.scan(r, tf, ["A", "B", "C"]), uni):
            hits += res
    for h in hits:
        h["tf"] = tf
    return hits


def setups(horizon: str, top: int = 60, force: bool = False) -> dict:
    """Kandidat setup untuk satu horizon, dengan cache TTL."""
    key = f"{horizon}:{top}"
    now = time.time()
    if not force and key in _cache and now - _cache[key]["at"] < TTL:
        return _cache[key]

    hits: list[dict] = []
    for tf in HORIZON.get(horizon, ["240"]):
        try:
            hits += _scan_tf(tf, top)
        except Exception as e:  # noqa: BLE001
            hits.append({"error": f"{type(e).__name__}: {e}", "tf": tf})

    # Satu setup terbaik per simbol; RR tertinggi menang.
    best: dict[str, dict] = {}
    for h in hits:
        if "error" in h:
            continue
        s = h["symbol"]
        if s not in best or h["rr"] > best[s]["rr"]:
            best[s] = h
    ranked = sorted(best.values(), key=lambda h: (-h["rr"], abs(h["dist_pct"])))

    out = {"at": now, "horizon": horizon,
           "tf": ",".join(HORIZON.get(horizon, [])), "setups": ranked}
    _cache[key] = out
    return out


def sizing(setup: dict, risiko_usd: float, lev: int = 15) -> dict:
    """Ukuran posisi dari risiko USD — bukan dari 'berapa yang saya mau taruh'."""
    per_koin = abs(setup["entry"] - setup["sl"])
    qty = risiko_usd / per_koin if per_koin else 0
    notional = qty * setup["entry"]
    return {"qty": qty, "notional": notional, "margin": notional / lev,
            "risiko_usd": risiko_usd, "risiko_per_koin": per_koin}


def checklist(setup: dict, equity: float, risiko_usd: float,
              risiko_terbuka: float, lev: int = 15) -> list[dict]:
    """Enam pertanyaan dari panduan. Satu saja 'tidak' -> jangan masuk."""
    liq = S.liq_price(setup["entry"], setup["side"], lev)
    r_pct = risiko_usd / equity * 100 if equity else 100
    total_pct = (risiko_usd + risiko_terbuka) / equity * 100 if equity else 100
    jarak_sl = abs(setup["entry"] - setup["sl"])
    return [
        {"q": "Masuk playbook A, B, atau C?",
         "ok": setup["playbook"] in ("A", "B", "C"),
         "detail": f"Playbook {setup['playbook']}"},
        {"q": "Risk/reward minimal 1:2?",
         "ok": setup["rr"] >= 2.0,
         "detail": f"1:{setup['rr']:.2f} ke TP2"},
        {"q": "SL di luar struktur, bukan angka bulat?",
         "ok": True,
         "detail": f"SL {setup['sl']:.8g} — swing sebelum tembusan ({jarak_sl/setup['entry']*100:.2f}%)"},
        # 17 Ags 2026: plafon turun dari 5%/15% ke 1%/3%. Toleransi 0,05 pp dan
        # dua desimal mengikuti gerbang di ~/trading-exec/order.py — kalau dua
        # layar ini menjawab beda untuk setup yang sama, yang dipercaya bukan
        # yang benar melainkan yang lebih longgar.
        {"q": "Risiko trade ini maksimal 1% ekuitas?",
         "ok": r_pct <= 1.05,
         "detail": f"${risiko_usd:.2f} = {r_pct:.2f}% dari ${equity:.2f}"},
        {"q": "Total risiko semua posisi maksimal 3%?",
         "ok": total_pct <= 3.05,
         "detail": f"{total_pct:.2f}% (termasuk ${risiko_terbuka:.2f} yang sudah berjalan)"},
        {"q": "Harga likuidasi lebih jauh daripada SL?",
         "ok": abs(setup["entry"] - liq) > jarak_sl,
         "detail": f"likuidasi ~{liq:.8g} vs SL {setup['sl']:.8g}"},
    ]
