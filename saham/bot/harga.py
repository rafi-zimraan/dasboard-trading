#!/usr/bin/env python3
"""Lapis pengambil harga saham IDX — satu pintu, sumber bisa ditukar.

KENAPA MODUL SENDIRI. Tidak ada satu pun broker Indonesia yang menyediakan API
ritel (dicek ke 15+ sekuritas, September 2026). Jadi harga harus diambil dari
penyedia pihak ketiga, dan penyedia itu bisa mati kapan saja — investpy mati
Januari 2022, tradingview-ta basi Oktober 2022. Modul ini memisahkan "dari mana
harga datang" dari "apa yang dilakukan dengan harga", supaya penjaga_saham.py
tidak perlu diubah saat sumbernya berganti.

URUTAN SUMBER, dan alasannya:

  1. GoAPI.io   — kontrak sah, delay 3-10 menit, dukungan bahasa Indonesia.
                  Butuh kunci di ~/.goapi_key. Sadari: spesifikasi OpenAPI
                  mereka sendiri menyebut sumbernya "YFinance + GoogleFinance +
                  MSN Money", jadi yang dibeli adalah kenyamanan dan kepastian
                  akses, bukan data premium.
  2. Yahoo .JK  — gratis, tanpa kunci, delay ~15 menit. Per 5 Sep 2026 membalas
                  HTTP 429 dari koneksi ini DAN dari sandbox riset. Tetap
                  dicoba karena pemblokiran Yahoo bersifat sementara dan
                  per-IP; kalau nanti lolos, ia jadi jalur gratis.

YANG SENGAJA TIDAK DIPAKAI. Endpoint scanner TradingView bekerja sempurna —
844 emiten, tanpa kunci, 5 request 1,6 detik, lengkap dengan SMA/RSI/ATR/minmov.
Tapi ToS TradingView melarang "non-display usage" secara eksplisit, dan bot
alert adalah persis itu. Chart TradingView tetap dipakai untuk MENGGAMBAR dan
MELIHAT setup (itu display use yang sah); ia tidak dipakai sebagai feed polling.

BATAS YANG DISENGAJA. Modul ini hanya MEMBACA. Tidak ada jalur order di sini,
dan memang tidak bisa ada — tidak ada broker yang menyediakannya. Eksekusi
selalu manual di aplikasi broker.
"""
from __future__ import annotations

import http.cookiejar
import json
import urllib.error
import urllib.request
from pathlib import Path

KUNCI_GOAPI = Path.home() / ".goapi_key"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")

# Yahoo tidak pernah mempublikasikan rate limit resminya. Praktik komunitas:
# jeda >=1-2 detik antar request. Dengan delay data 15 menit, polling lebih
# rapat dari 5 menit tidak menambah informasi apa pun.
JEDA_MIN_DETIK = 2


class TidakAdaSumber(RuntimeError):
    """Semua sumber harga gagal. Sengaja gagal keras, bukan mengembalikan None.

    Harga None yang lolos diam-diam ke pembanding level akan menghasilkan
    perbandingan yang salah, dan alert yang salah lebih berbahaya daripada
    tidak ada alert.
    """


def _kunci_goapi() -> str | None:
    try:
        return KUNCI_GOAPI.read_text().strip() or None
    except OSError:
        return None


def _dari_goapi(kode_kode: list[str]) -> dict[str, float]:
    """GoAPI menerima banyak simbol sekaligus — maksimum 50 per panggilan."""
    kunci = _kunci_goapi()
    if not kunci:
        return {}
    hasil: dict[str, float] = {}
    for i in range(0, len(kode_kode), 50):
        potongan = kode_kode[i:i + 50]
        url = ("https://api.goapi.io/stock/idx/prices"
               f"?symbols={','.join(potongan)}&api_key={kunci}")
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers={"User-Agent": UA}),
                    timeout=20) as r:
                data = json.load(r)
        except (urllib.error.URLError, json.JSONDecodeError, OSError):
            continue
        for baris in data.get("data", {}).get("results", []) or []:
            kode = str(baris.get("symbol", "")).upper()
            harga = baris.get("close") or baris.get("price")
            if kode and harga:
                hasil[kode] = float(harga)
    return hasil


def _dari_yahoo(kode_kode: list[str]) -> dict[str, float]:
    """Yahoo satu simbol per panggilan. Butuh cookie+crumb sejak pertengahan 2025."""
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA), ("Accept-Language", "en-US,en;q=0.9")]
    try:
        op.open("https://fc.yahoo.com/", timeout=15).read()
    except Exception:
        pass  # 404 di sini wajar; yang dibutuhkan cuma cookie-nya
    try:
        crumb = op.open("https://query1.finance.yahoo.com/v1/test/getcrumb",
                        timeout=15).read().decode()
    except Exception:
        return {}

    import time
    hasil: dict[str, float] = {}
    for kode in kode_kode:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{kode}.JK"
               f"?range=1d&interval=1d&crumb={crumb}")
        try:
            with op.open(url, timeout=20) as r:
                meta = json.load(r)["chart"]["result"][0]["meta"]
            harga = meta.get("regularMarketPrice")
            if harga:
                hasil[kode.upper()] = float(harga)
        except Exception:
            pass
        time.sleep(JEDA_MIN_DETIK)
    return hasil


def ambil(kode_kode: list[str]) -> tuple[dict[str, float], str]:
    """Harga terakhir untuk daftar kode IDX. Kembalikan (harga, nama_sumber).

    Mencoba sumber berurutan sampai ada yang membalas. Kalau semua gagal,
    melempar TidakAdaSumber — jangan pernah diam-diam mengembalikan kosong.
    """
    kode_kode = [k.upper().strip() for k in kode_kode if k.strip()]
    if not kode_kode:
        return {}, "kosong"

    for nama, fungsi in (("GoAPI", _dari_goapi), ("Yahoo", _dari_yahoo)):
        harga = fungsi(kode_kode)
        if harga:
            return harga, nama

    raise TidakAdaSumber(
        "Semua sumber harga gagal.\n"
        "  - GoAPI  : butuh kunci di ~/.goapi_key (daftar di goapi.io)\n"
        "  - Yahoo  : membalas 429 sejak 5 Sep 2026 dari koneksi ini\n"
        "Alert TIDAK dikirim daripada mengirim yang salah."
    )


if __name__ == "__main__":
    import sys
    kode = sys.argv[1:] or ["DSNG", "LSIP", "TAPG", "PTBA"]
    try:
        harga, sumber = ambil(kode)
        print(f"sumber: {sumber}")
        for k, v in harga.items():
            print(f"  {k:6} {v:>10,.0f}")
    except TidakAdaSumber as e:
        print(e)
        sys.exit(1)
