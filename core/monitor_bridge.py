"""Menjalankan ~/trading-exec/monitor.py otomatis dari dashboard.

monitor.py tetap satu sumber kebenaran untuk aturan "aksi apa yang perlu
dilakukan". Dashboard tidak menyalin logikanya — dia memanggil fungsi yang sama
(cek_posisi / cek_watchlist), lalu menampilkan hasilnya di web.

Notifikasi macOS tetap dikirim oleh launchd tiap pagi seperti biasa; dari
dashboard notifikasi hanya dikirim kalau muncul aksi BARU, supaya tidak
berdering tiap kali halaman di-refresh.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "trading-exec"))

_lock = threading.Lock()
_state: dict = {"at": 0, "posisi": [], "watchlist": [], "aksi": [], "error": None}
_aksi_terkirim: set[str] = set()
TTL = 120


def _monitor():
    import monitor  # noqa: PLC0415
    return monitor


def jalankan(force: bool = False, notifikasi: bool = True) -> dict:
    now = time.time()
    if not force and now - _state["at"] < TTL and not _state["error"]:
        return _state

    with _lock:
        if not force and time.time() - _state["at"] < TTL and not _state["error"]:
            return _state
        try:
            m = _monitor()
            m.sync_clock()
            p_baris, p_aksi = m.cek_posisi()
            w_baris, w_aksi = m.cek_watchlist()
            aksi = p_aksi + w_aksi

            # Hanya aksi yang belum pernah muncul yang berhak membunyikan notifikasi.
            baru = [a for a in aksi if a not in _aksi_terkirim]
            if notifikasi and baru:
                m.notifikasi(f"⚠️ Trading: {len(baru)} aksi baru", baru[0])
                _aksi_terkirim.update(baru)

            _state.update({"at": time.time(), "posisi": p_baris, "watchlist": w_baris,
                           "aksi": aksi, "aksi_baru": baru, "error": None})
        except Exception as e:  # noqa: BLE001
            _state.update({"at": time.time(), "error": f"{type(e).__name__}: {e}"})
    return _state


def mulai_otomatis(interval: int = 300) -> threading.Thread:
    """Thread latar: monitor jalan sendiri selama dashboard hidup."""
    def loop():
        while True:
            try:
                jalankan(force=True)
            except Exception:  # noqa: BLE001
                pass
            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True, name="monitor-otomatis")
    t.start()
    return t
