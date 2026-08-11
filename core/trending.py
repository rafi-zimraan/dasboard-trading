"""Crypto apa yang sedang menarik — bukan sekadar yang paling naik.

Yang naik 40% dalam sehari biasanya sudah selesai bergeraknya. Yang berguna
untuk trading adalah koin dengan perhatian yang SEDANG datang: volume hari ini
jauh di atas kebiasaannya sendiri. Itu yang dihitung di sini.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from . import bybit

CACHE: dict[str, dict] = {}
TTL = 300


def _tickers() -> list[dict]:
    rows = []
    for t in bybit.public("/v5/market/tickers?category=linear")["result"]["list"]:
        if not t["symbol"].endswith("USDT"):
            continue
        try:
            turn = float(t["turnover24h"])
            if turn < 20e6:
                continue
            rows.append({
                "symbol": t["symbol"], "last": float(t["lastPrice"]),
                "chg": float(t["price24hPcnt"]) * 100, "turnover": turn,
                "high": float(t["highPrice24h"]), "low": float(t["lowPrice24h"]),
            })
        except (KeyError, ValueError):
            continue
    return rows


def _lonjakan_volume(row: dict) -> dict | None:
    """Volume candle harian yang BARU TUTUP vs rata-rata 12 hari sebelumnya.

    Candle hari ini sengaja tidak dipakai: candle berjalan baru terisi beberapa
    jam, jadi membandingkannya dengan hari-hari penuh selalu menghasilkan angka
    di bawah 1x dan membuat semua koin terlihat sepi. Konvensi ini sama dengan
    monitor.py, yang juga membaca rows[-2].
    """
    try:
        r = bybit.public(f"/v5/market/kline?category=linear&symbol={row['symbol']}"
                         f"&interval=D&limit=15")["result"]["list"]
        bars = [[float(v) for v in k[1:6]] for k in r][::-1]
        if len(bars) < 15:
            return None
        tutup = bars[-2][4]                        # volume hari yang sudah selesai
        rata = sum(b[4] for b in bars[-14:-2]) / 12
        if rata <= 0:
            return None
        # Candle berjalan tetap dilaporkan apa adanya, diberi label jelas.
        berjalan = bars[-1][4] / rata
        return {**row, "vol_x": tutup / rata, "vol_x_berjalan": berjalan}
    except Exception:  # noqa: BLE001
        return None


def snapshot(force: bool = False) -> dict:
    now = time.time()
    if not force and CACHE.get("at") and now - CACHE["at"] < TTL:
        return CACHE

    rows = _tickers()
    rows.sort(key=lambda r: -r["turnover"])
    kandidat = rows[:70]

    with ThreadPoolExecutor(max_workers=8) as ex:
        diperiksa = [x for x in ex.map(_lonjakan_volume, kandidat) if x]

    out = {
        "at": now,
        "naik": sorted(rows, key=lambda r: -r["chg"])[:8],
        "turun": sorted(rows, key=lambda r: r["chg"])[:8],
        "likuid": rows[:8],
        # Inilah bagian yang benar-benar berguna: perhatian yang sedang datang.
        "lonjakan_volume": sorted(diperiksa, key=lambda r: -r["vol_x"])[:8],
    }
    CACHE.clear()
    CACHE.update(out)
    return out
