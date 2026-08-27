# ATURAN-TRAILING.md

Kapan trailing stop dipakai, dan berapa jaraknya. Dipaksakan oleh
`~/trading-exec/pasang_trailing.py`.

## Perubahan 27 Agustus 2026 — trailing jadi BAWAAN, bukan pengecualian

Sampai 26 Ags dokumen ini berbunyi *"trailing hanya untuk wilayah tanpa level
acuan di atas harga"*, dan skripnya menolak secara bawaan. **Dibalik atas
permintaan eksplisit Rafi**, setelah EDENUSDT memperlihatkan harga dari aturan
lama.

### Bukti yang membalikkannya

EDENUSDT long, entry 0,05698, tranche terakhir ~287 unit.

| | Harga | Hasil |
|---|---|---|
| Puncak 27/08 00:00 | 0,07319 | +$4,65 mengambang |
| Keluar manual 27/08 10:17 | 0,06053 | **+$1,02 diterima** |
| **Yang menguap** | | **−$3,64** |

Kalau trailing dipasang saat untung menyentuh $2 (harga ~0,0640) dengan
`--kunci=1`, jaraknya $1 ÷ 287 = 0,00348. Stop mengikuti puncak:
0,07319 − 0,00348 = 0,06971 → **+$3,65**.

Satu perintah yang tidak dijalankan = **$2,63**.

### Kenapa ini TIDAK bertabrakan dengan pelajaran 19 Agustus

19 Ags: BTC long 67.956,8. TP2 rencana 69.700, tepat di bawah swing high harian
69.990. TP lalu dinaikkan ke 71.985 **dan** ditambah trailing $850. Hasil
+$0,08; TP tetap 69.700 akan membayar +$1,74.

Kesalahannya **bukan** trailing. Kesalahannya **memindahkan TP menjauh dari
struktur**. Kalau TP dibiarkan di 69.700 dan trailing tetap dipasang, urutannya:
high mencapai 70.053 → TP 69.700 kena LEBIH DULU → +$1,74. Trailing tidak pernah
menyala. Hasilnya identik dengan rencana awal.

Jadi aturan barunya bukan "trailing menggantikan TP" — itu tetap terlarang.
Aturan barunya: **TP tetap di struktur, trailing dipasang di sampingnya.**

- Harga lari ke target → **TP** yang bayar.
- Harga mentok lalu balik → **trailing** yang bayar.

Tidak ada jalur di mana pasangan ini lebih buruk daripada TP sendirian.

## Aturan yang berlaku sekarang

> **Begitu untung mengambang sebuah posisi menyentuh $2, pasang trailing
> dengan `--kunci=1`. Tanpa bertanya lagi, tanpa menunggu diminta.**

```bash
python3 ~/trading-exec/pasang_trailing.py <SIMBOL> --kunci=1 --tanpa-target --live
```

Tangga kuncinya:

| Untung mengambang | Kunci |
|---|---|
| < $2 | belum — biarkan SL awal yang bekerja |
| ≥ $2 | $1 |
| ≥ $4 | $2 |
| ≥ $6 | $3 |

Polanya: **kunci ≈ separuh untung mengambang.** Separuh, bukan seluruhnya —
stop yang mengunci hampir semua untung duduk terlalu dekat harga dan tersapu
napas normal pasar.

**Kenapa tidak dipasang tepat di +$1.** Aritmetika, bukan pilihan:

```
jarak = harga_sekarang − (entry + kunci / qty)
```

Pada untung tepat $1 dengan kunci $1, jaraknya **nol** — stop duduk persis di
harga sekarang dan kena seketika. Untung harus cukup jauh di atas target kunci
supaya ada ruang. $2 adalah ambang terkecil yang menyisakan ruang itu, dan
itulah `AMBANG_USD` di skrip.

## Empat syarat — status setelah 27 Ags

1. **Untung mengambang ≥ $2.** TETAP. Di bawah ini trailing tidak menyala dan
   SL awal yang bekerja.

2. ~~Tidak ada target struktur di depan harga.~~ **DICABUT sebagai penghalang.**
   Adanya swing high tidak lagi membatalkan trailing — TP dibiarkan di swing
   high itu dan trailing dipasang di sampingnya. Flag `--tanpa-target` sekarang
   dipakai rutin, bukan sebagai pengakuan istimewa.

3. **Jarak ≥ lebar konsolidasi terakhir**, diukur dari 24 bar M15 — **bukan
   ATR**. TETAP, dan setelah syarat 2 dicabut inilah penjaga utamanya. ATR selalu
   telat setelah ledakan volatilitas: 19 Ags ATR H1 masih 254 padahal bar M5
   bergerak $2.828.

4. **Wajib mengunci untung minimal $1.** TETAP. Kalau jarak hasil hitungan lebih
   **sempit** daripada lebar konsolidasi, trailing **ditolak** — harga belum
   cukup jauh dari entry. **Jawabannya menunggu, bukan mengecilkan target kunci.**

## Yang tetap terlarang

- **Menaikkan TP menjauh dari struktur supaya trailing punya ruang.** Ini
  kesalahan 19 Ags, dan pencabutan syarat 2 tidak menyentuhnya. TP duduk di
  swing high; trailing yang menyesuaikan diri, bukan sebaliknya.
- **Jarak trailing lebih sempit daripada lebar konsolidasi M15.** Stop seperti
  itu kena bukan karena trennya berakhir, tapi karena pasar bernapas.

## Pemakaian

```bash
python3 ~/trading-exec/pasang_trailing.py LTCUSDT                        # periksa saja
python3 ~/trading-exec/pasang_trailing.py LTCUSDT --kunci=1              # dry-run
python3 ~/trading-exec/pasang_trailing.py LTCUSDT --kunci=1 --tanpa-target --live
python3 ~/trading-exec/pasang_trailing.py BTCUSDT --jarak=850 --live     # jarak manual
```

Urutan wewenang jarak: `--jarak` manual > `--kunci` > lebar konsolidasi.

## Trailing TIDAK menghapus TP dan SL

Di Bybit v5, `trailingStop` hidup berdampingan dengan `stopLoss` dan
`takeProfit`. Contoh nyata BTCUSDT 27 Ags 2026, sesudah aturan baru:

```
avgPrice 77704 · trailingStop 1014 · stopLoss 76150 · takeProfit 82811
```

Stop mengikuti 1.014 di bawah harga tertinggi, SL 76.150 tetap jadi jaring
bawah, TP 82.811 tetap jadi atap. Inilah bentuk yang dimaksud aturan baru:
ketiganya sekaligus.
