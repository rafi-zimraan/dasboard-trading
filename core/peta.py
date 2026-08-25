"""Membaca peta jalan trader ($107 -> $1.000) untuk tab Peta.

Sama seperti panduan: isinya TIDAK disimpan di repo ini karena memuat angka
akun dan riwayat trade sungguhan, sedangkan repo ini publik. Berkasnya hidup
di `~/trading-exec/peta_plan.json`; di sini hanya penampilnya.

Ditulis 18 Agustus 2026 atas permintaan Rafi setelah sesi live XAU — peta ini
adalah kurikulum + aturan malam + tape review, pendamping panduan.json (yang
tetap menjadi konstitusi; peta tidak boleh melonggarkan satu pun angkanya).
"""

from __future__ import annotations

import json
from pathlib import Path

SUMBER = Path.home() / "trading-exec" / "peta_plan.json"


def muat() -> dict:
    try:
        return json.loads(SUMBER.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {
            "error": f"peta_plan.json tidak terbaca ({type(e).__name__}). "
                     f"Letakkan di {SUMBER}.",
            "bagian": [],
        }
