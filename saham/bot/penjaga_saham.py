#!/usr/bin/env python3
"""Penjaga saham — mengabari lewat Telegram saat level rencana disentuh.

KENAPA ADA. Bursa buka 09.00-16.15 WIB, dan menonton layar selama itu bukan
pekerjaan yang bisa dilakukan sambil hidup. Yang sebenarnya dibutuhkan bukan
pemantauan terus-menerus, melainkan kabar saat SATU DARI SEDIKIT level yang
sudah direncanakan tersentuh. Level-levelnya ditetapkan sekali, saat tenang,
dengan chart di depan mata — bukan saat harga sedang bergerak.

APA YANG TIDAK DILAKUKAN, dan ini disengaja:

  - TIDAK mengirim order. Tidak ada broker Indonesia yang punya API ritel, jadi
    memang tidak bisa. Tapi kalaupun bisa, jawabannya tetap tidak — alasan yang
    sama dengan `dasboard-trading`: satu-satunya jalur eksekusi adalah manusia
    yang sadar, setelah setup digambar.
  - TIDAK mengabari setiap harga bergerak. Alert yang terlalu sering berubah
    jadi latar belakang, lalu diabaikan justru saat ia penting.
  - TIDAK memakai feed TradingView. ToS-nya melarang non-display usage, dan bot
    ini persis itu. Chart TradingView tetap dipakai untuk menggambar dan
    melihat setup — itu penggunaan yang sah.

SEKALI PER KEJADIAN. Tiap level dilaporkan sekali per kunjungan. Level dibuka
kembali hanya kalau harga menjauh lebih dari BUKA_LAGI_PCT. Tanpa ini, satu
level yang disentuh berulang kali di sekitar batas akan mengirim puluhan pesan
dalam satu jam — pola yang sama sudah diselesaikan di penjaga_btc_70k.py.

Pemakaian:
    python3 penjaga_saham.py            # jalan terus, periksa tiap 5 menit
    python3 penjaga_saham.py --sekali   # satu siklus, untuk uji
    python3 penjaga_saham.py --dry      # jangan kirim, cuma tampilkan
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SINI = Path(__file__).resolve().parent
AKAR = SINI.parent
RENCANA = AKAR / "data" / "rencana.json"
KEADAAN = AKAR / "data" / ".keadaan_penjaga.json"
CATATAN = AKAR / "data" / "penjaga_saham.log"

sys.path.insert(0, str(SINI))
sys.path.insert(0, str(Path.home() / "trading-exec"))

import harga as sumber_harga  # noqa: E402
import telegram  # noqa: E402  — dipakai ulang dari ~/trading-exec

WIB = timezone(timedelta(hours=7))

# Data terbaik yang bisa diakses tanpa kontrak B2B tertunda 3-20 menit. Polling
# lebih rapat dari ini tidak menambah informasi apa pun, hanya menambah risiko
# kena rate limit.
JEDA_DETIK = 300

# Level dianggap "tersentuh" dalam radius ini. Nol akan membuat level nyaris
# tidak pernah kena persis, karena harga saham bergerak per tick (Rp1-25),
# bukan kontinu.
TOLERANSI_PCT = 0.3

# Level dibuka kembali setelah harga menjauh sejauh ini. Lebih longgar daripada
# toleransi supaya tidak berkedip di sekitar batas.
BUKA_LAGI_PCT = 1.5


def sekarang() -> datetime:
    return datetime.now(WIB)


def bursa_buka(t: datetime | None = None) -> bool:
    """Sesi BEI: Sen-Jum 09.00-16.15 WIB.

    Sengaja memakai satu rentang lebar, bukan dua sesi terpisah, karena bot ini
    hanya membandingkan harga terhadap level — jeda istirahat siang tidak
    mengubah apa pun kecuali harga tidak bergerak.
    """
    t = t or sekarang()
    if t.weekday() >= 5:
        return False
    menit = t.hour * 60 + t.minute
    return 9 * 60 <= menit <= 16 * 60 + 15


def catat(pesan: str) -> None:
    baris = f"[{sekarang():%d/%m %H:%M:%S}] {pesan}"
    print(baris, flush=True)
    try:
        with CATATAN.open("a") as f:
            f.write(baris + "\n")
    except OSError:
        pass


def muat_keadaan() -> dict:
    try:
        return json.loads(KEADAAN.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def simpan_keadaan(k: dict) -> None:
    try:
        KEADAAN.write_text(json.dumps(k, indent=2))
    except OSError:
        pass


def level_dipantau(r: dict) -> list[tuple[str, float, str]]:
    """(nama_level, harga, nada) untuk satu rencana."""
    out: list[tuple[str, float, str]] = []
    if r.get("status") == "menunggu" and r.get("entry"):
        out.append(("ENTRY", float(r["entry"]), "masuk"))
    if r.get("sl"):
        out.append(("SL", float(r["sl"]), "bahaya"))
    for i, tp in enumerate(r.get("tp") or [], start=1):
        out.append((f"TP{i}", float(tp), "untung"))
    return out


def periksa(dry: bool = False) -> int:
    try:
        data = json.loads(RENCANA.read_text())
    except (OSError, json.JSONDecodeError) as e:
        catat(f"rencana.json tidak terbaca: {e}")
        return 0

    rencana = [r for r in data.get("rencana", [])
               if r.get("status") in ("menunggu", "jalan")]
    if not rencana:
        return 0

    kode_kode = [r["kode"] for r in rencana]
    try:
        harga, sumber = sumber_harga.ambil(kode_kode)
    except sumber_harga.TidakAdaSumber as e:
        catat(f"TIDAK ADA HARGA — alert dilewati.\n{e}")
        return 0

    keadaan = muat_keadaan()
    terkirim = 0

    for r in rencana:
        kode = r["kode"]
        h = harga.get(kode)
        if h is None:
            catat(f"{kode}: harga tidak ada di balasan {sumber} — dilewati")
            continue

        for nama, level, nada in level_dipantau(r):
            kunci = f"{kode}:{nama}"
            jarak_pct = abs(h - level) / level * 100
            sudah = keadaan.get(kunci, {}).get("dilaporkan", False)

            if jarak_pct <= TOLERANSI_PCT and not sudah:
                arah = "▲" if h >= level else "▼"
                teks = (
                    f"{kode} {arah} {nama} tersentuh\n"
                    f"harga {h:,.0f} · level {level:,.0f}\n"
                    f"sumber {sumber} (tertunda, bukan real-time)"
                )
                if nada == "bahaya":
                    teks += "\n\nIni SL. Rencananya keluar — bukan menunggu balik."
                elif nada == "masuk":
                    teks += (f"\n\nSL {r.get('sl'):,.0f} · "
                             f"TP {' / '.join(f'{t:,.0f}' for t in r.get('tp', []))}"
                             "\nEksekusi manual di aplikasi broker.")
                catat(f"ALERT {kunci} @ {h:,.0f}")
                if not dry:
                    telegram.kirim(teks, judul="Saham")
                keadaan[kunci] = {"dilaporkan": True, "harga": h}
                terkirim += 1

            elif jarak_pct > BUKA_LAGI_PCT and sudah:
                keadaan[kunci] = {"dilaporkan": False, "harga": h}

    simpan_keadaan(keadaan)
    return terkirim


def main() -> int:
    dry = "--dry" in sys.argv
    sekali = "--sekali" in sys.argv

    if not telegram.terpasang():
        catat("Telegram belum dipasang — jalankan python3 ~/trading-exec/setup_telegram.py")
        return 1

    catat(f"Penjaga saham aktif — periksa tiap {JEDA_DETIK}s"
          f"{'  [DRY-RUN]' if dry else ''}")

    if sekali:
        n = periksa(dry)
        catat(f"selesai, {n} alert")
        return 0

    while True:
        try:
            if bursa_buka():
                periksa(dry)
            time.sleep(JEDA_DETIK)
        except KeyboardInterrupt:
            catat("dihentikan")
            return 0
        except Exception as e:  # jangan mati karena satu siklus gagal
            catat(f"galat siklus ({type(e).__name__}: {e}) — lanjut.")
            time.sleep(JEDA_DETIK)


if __name__ == "__main__":
    sys.exit(main())
