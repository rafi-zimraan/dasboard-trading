# ATURAN-TRAILING.md

Kapan trailing stop boleh dipakai, dan berapa jaraknya. Dipaksakan oleh
`~/trading-exec/pasang_trailing.py` — skrip itu **menolak** kalau syaratnya
tidak terpenuhi, dan penolakan itu memang tujuannya.

## Kejadian yang melahirkan aturan ini

19 Agustus 2026, long BTCUSDT 0,001 @ 67.956,8. Rencana awal TP2 69.700, tepat
di bawah swing high harian 69.990. Atas permintaan TP lebih tinggi, TP dinaikkan
ke 71.985 **dan** ditambahkan trailing $850 yang aktif seketika.

| Yang dijalankan | Hasil |
|---|---|
| Trailing $850 aktif seketika | **+$0,08** |
| Trailing dengan pemicu 68.850 | +$0,19 |
| **TP tetap 69.700 (rencana awal)** | **+$1,74** — high mencapai 70.053, TP2 KENA |

Bahkan konfigurasi trailing yang "benar" kalah telak. **Konsepnya yang salah,
bukan setelannya.** Trailing $850 duduk di dalam lebar konsolidasi normal
($700–900), jadi pasti kena pada pullback pertama berapa pun pemicunya.

## Empat syarat, semuanya wajib

1. **Untung mengambang ≥ $2.** Malam itu untung tertinggi selama posisi hidup
   hanya $0,93 — dengan ambang ini trailing tidak akan pernah menyala dan TP
   tetap yang berjalan.

2. **Tidak ada target struktur di depan harga.** Kalau ada swing high yang bisa
   ditunjuk, TP tetap di situ. Trailing hanya untuk wilayah tanpa acuan di atas
   harga. Butuh konfirmasi manual: `--tanpa-target`.

3. **Jarak ≥ lebar konsolidasi terakhir**, diukur dari 24 bar M15 — **bukan dari
   ATR**. ATR selalu telat memperbarui diri setelah ledakan volatilitas: malam itu
   ATR H1 masih 254 padahal bar M5 bergerak $2.828.

4. **Trailing wajib MENGUNCI untung minimal $1** *(ditambahkan 23 Ags 2026 atas
   permintaan Rafi)*. Jaraknya dihitung mundur dari target kunci, bukan ditebak:

   ```
   stop_kunci = entry + (kunci / qty)          # long
   jarak      = harga_sekarang − stop_kunci
   ```

   Kalau `jarak` hasil hitungan itu lebih **sempit** daripada lebar konsolidasi,
   trailing **ditolak** — artinya harga belum cukup jauh dari entry untuk bisa
   mengunci sebanyak itu tanpa langsung tersapu.
   **Jawabannya menunggu, bukan mengecilkan target kunci.**

## Pemakaian

```bash
python3 ~/trading-exec/pasang_trailing.py LTCUSDT                        # periksa saja
python3 ~/trading-exec/pasang_trailing.py LTCUSDT --kunci=1              # dry-run, jarak dari kunci $1
python3 ~/trading-exec/pasang_trailing.py LTCUSDT --kunci=1 --tanpa-target --live
python3 ~/trading-exec/pasang_trailing.py BTCUSDT --jarak=850 --live     # jarak manual
```

Urutan wewenang jarak: `--jarak` manual > `--kunci` > lebar konsolidasi.

## Trailing TIDAK menghapus TP dan SL

Di Bybit v5, `trailingStop` hidup berdampingan dengan `stopLoss` dan
`takeProfit`. Contoh nyata LTCUSDT 23 Ags 2026:

```
avgPrice 51.46 · trailingStop 0.79 · stopLoss 49.92 · takeProfit 56.20
```

Stop mengikuti 0,79 di bawah harga tertinggi, SL 49,92 tetap jadi jaring bawah,
TP 56,20 tetap jadi target atas. Yang perlu diwaspadai bukan TP hilang, tapi
**trailing kena lebih dulu daripada TP** — itulah yang terjadi pada BTC.

## Yang mengalahkan trailing, hampir selalu

TP bertingkat + geser SL ke BE setelah TP1. Lihat aturan TP1 ≥ 2R: dengan tiga
tingkat, "TP1 cair lalu harga balik" baru impas kalau TP1 berada di 2R. Trailing
dipakai ketika **tidak ada** level di atas yang bisa ditunjuk — bukan sebagai
pengganti target yang sudah jelas.
