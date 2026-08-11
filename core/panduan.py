"""Membaca panduan trading + menilai angka akun terhadap ambang di dalamnya.

Isi panduan sengaja TIDAK disimpan di repo. Dokumen itu memuat riwayat trade
dan ukuran akun sungguhan, sedangkan repo ini publik. Yang ada di sini hanya
penampil dan penilainya; isinya dibaca dari `~/trading-exec/panduan.json`.

Kalau berkas itu tidak ada, dashboard tetap jalan dan tab Panduan menjelaskan
cara membuatnya, bukan menampilkan aturan karangan sendiri — aturan yang salah
lebih berbahaya daripada aturan yang absen.
"""

from __future__ import annotations

import json
from pathlib import Path

SUMBER = Path.home() / "trading-exec" / "panduan.json"

# Dipakai kalau berkas panduan belum ada, supaya modal_awal tidak diam-diam
# salah. Angka ini berasal dari panduan edisi 1 (9 Agustus 2026).
MODAL_AWAL_BAWAAN = 59.0
TARGET_BAWAAN = 1000.0


def muat() -> dict:
    try:
        return json.loads(SUMBER.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {"error": f"panduan.json tidak terbaca ({type(e).__name__}). "
                         f"Letakkan di {SUMBER}.", "playbook": [], "checklist": [],
                "perusak": [], "fase": [], "angka": [], "ritual": []}


def modal_awal() -> float:
    return float(muat().get("modal_awal") or MODAL_AWAL_BAWAAN)


def target() -> float:
    return float(muat().get("target") or TARGET_BAWAAN)


def _nilai(a: dict, v: float | None) -> tuple[str, str]:
    """Kembalikan (status, alasan) untuk satu ukuran.

    Status: 'sehat' | 'bahaya' | 'antara' | 'belum'. Sengaja tidak memaksa
    hitam-putih: nilai yang berada di antara sehat dan bahaya memang ada, dan
    memaksanya jadi 'sehat' akan menutupi masalah yang sedang tumbuh.
    """
    if v is None:
        return "belum", "belum ada data"
    if "bahaya_min" in a and v >= a["bahaya_min"]:
        return "bahaya", f"{a['bahaya']} — {a['arti']}"
    if "bahaya_maks" in a and v <= a["bahaya_maks"]:
        return "bahaya", f"{a['bahaya']} — {a['arti']}"
    if "sehat_maks" in a and "sehat_min" not in a:
        return ("sehat", "sesuai target") if v <= a["sehat_maks"] else ("antara", a["arti"])
    if "sehat_min" in a and "sehat_maks" in a:
        if a["sehat_min"] <= v <= a["sehat_maks"]:
            return "sehat", "di rentang sehat"
        return "antara", a["arti"]
    if "sehat_min" in a:
        return ("sehat", "di atas ambang sehat") if v >= a["sehat_min"] else ("antara", a["arti"])
    return "antara", a["arti"]


def rapor(statistik: dict, pelanggaran: int) -> dict:
    """Lima angka panduan, diisi dari statistik akun yang sungguhan."""
    p = muat()
    stat = dict(statistik)
    mk = abs(stat.get("rata_kalah") or 0)
    stat["menang_bagi_kalah"] = (stat.get("rata_menang", 0) / mk) if mk else None
    stat["pelanggaran"] = pelanggaran

    baris = []
    for a in p.get("angka", []):
        v = stat.get(a["kunci"])
        if v is not None and not isinstance(v, (int, float)):
            v = None
        if v is not None and v == float("inf"):
            v = None
        status, alasan = _nilai(a, v)
        baris.append({**a, "nilai": v, "status": status, "alasan": alasan})

    total = stat.get("total", 0)
    fase_kini = None
    for f in p.get("fase", []):
        if f["dari"] <= max(1, total) <= f["sampai"]:
            fase_kini = f["nama"]
            break

    return {
        "baris": baris,
        "total_trade": total,
        "fase_kini": fase_kini,
        "cukup_data": total >= 30,
        "catatan": p.get("angka_catatan", ""),
    }


def semua(statistik: dict, pelanggaran: int) -> dict:
    p = muat()
    return {**p, "rapor": rapor(statistik, pelanggaran)}
