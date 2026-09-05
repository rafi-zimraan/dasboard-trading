# Sistem Trading Saham — untuk orang yang tidak bisa menonton layar

Bursa buka 09.00–16.15 WIB. Menontonnya selama itu bukan pekerjaan yang bisa
dilakukan sambil punya hidup. Sistem ini dirancang untuk **tidak perlu
ditonton** — bukan untuk mempercepat reaksi.

## Kenyataan yang membentuk desainnya

**Tidak ada broker Indonesia yang punya API ritel.** Dicek ke 15+ sekuritas
(September 2026): portal developer, subdomain `api.*`, sitemap, FAQ. Tidak satu
pun. Tidak ada MCP, tidak ada REST, tidak ada apa pun.

Artinya sistem ini **dipaksa** jadi baca-saja. Eksekusi selalu manual di
aplikasi broker. Itu bukan kekurangan yang perlu diakali — untuk saham, jalur
`order.py` seperti di Bybit memang tidak mungkin ada.

**Konsekuensi kedua yang lebih penting:** kalau eksekusi manual, maka
kecepatan bukan keunggulan Anda. Yang jadi keunggulan adalah **kualitas level
yang ditetapkan sebelum pasar buka**. Sistem ini dibangun di sekitar itu.

## Tiga lapis

### Lapis 1 — Stockbit Price Alert (pakai ini dulu)

Stockbit punya **Price Alert bawaan**. Jalan di server mereka, sampai ke HP,
**tidak butuh Mac menyala**. Gratis, sah, tanpa dibangun apa pun.

Untuk kebutuhan "kabari saya kalau DSNG menyentuh 1.640", ini sudah selesai.
**Pasang alert Anda di sini lebih dulu.** Lapis 2 hanya untuk yang tidak bisa
dilakukan Stockbit.

### Lapis 2 — `bot/penjaga_saham.py`

Yang tidak bisa dilakukan Price Alert: membaca **rencana** (entry + SL + 3 TP
sekaligus per saham), menjelaskan **apa artinya** saat level kena, dan mencatat
riwayatnya.

```bash
python3 ~/analisa-saham/bot/penjaga_saham.py --sekali --dry   # uji
python3 ~/analisa-saham/bot/penjaga_saham.py                  # jalan terus
```

Memakai `~/trading-exec/telegram.py` yang sudah terpasang — tidak membangun
jalur notifikasi baru.

**Status hari ini: BELUM BISA JALAN.** Sumber datanya belum ada (lihat bawah).
Botnya sendiri sudah diuji dan berperilaku benar: saat tidak ada harga, ia
**menolak mengirim alert** daripada mengirim yang salah.

### Lapis 3 — riset berkala, bukan harian

Isi `riset/` diperbarui saat ada **perubahan keadaan**, bukan tiap hari.
Pemicu yang layak: keluar laporan keuangan, revisi target price, perubahan
regulasi, atau berita hukum atas emiten yang dipegang.

## Yang masih menghalangi Lapis 2

Yahoo Finance `.JK` membalas **HTTP 429** — dari sandbox riset maupun dari
koneksi rumah Anda (diuji 5 Sep 2026, termasuk alur cookie+crumb lengkap).

Dua jalan keluar:

1. **Daftar GoAPI.io**, simpan kuncinya di `~/.goapi_key` (chmod 600).
   Delay 3–10 menit, kontrak sah, dukungan bahasa Indonesia.
   Sadari: spesifikasi OpenAPI mereka sendiri menyebut sumbernya
   *"YFinance + GoogleFinance + MSN Money"* — yang dibeli adalah **kepastian
   akses**, bukan data premium.

2. **Coba Yahoo lagi beberapa hari lagi.** Pemblokiran Yahoo bersifat sementara
   dan per-IP. `bot/harga.py` sudah mencoba GoAPI dulu, lalu Yahoo — begitu
   salah satunya hidup, bot langsung jalan tanpa diubah.

**Yang sengaja tidak dipakai:** endpoint scanner TradingView bekerja sempurna
(844 emiten, tanpa kunci, 1,6 detik). Tapi ToS-nya melarang *"non-display
usage"* secara eksplisit, dan bot alert adalah persis itu. Chart TradingView
tetap dipakai untuk **menggambar dan melihat** setup — itu penggunaan yang sah.

## Ritme kerja

**Mingguan (akhir pekan, 30–60 menit)** — ini inti sistemnya:
1. Baca ulang `data/rencana.json`
2. Untuk kandidat baru: gambar setupnya di TradingView, tetapkan entry/SL/TP
3. Pasang level di Stockbit Price Alert
4. Perbarui status rencana yang sudah kena

**Harian (5 menit, opsional):** baca notifikasi. Tidak membuka aplikasi kalau
tidak ada notifikasi.

**Saat alert masuk:** buka chart, periksa apakah alasannya masih berlaku, baru
eksekusi manual. **Alert adalah undangan untuk melihat, bukan perintah untuk
membeli.**

## Aturan yang dibawa dari Bybit — dan kenapa

Aturan ini lahir dari kerugian nyata di akun kripto, dan berlaku sama di saham.

1. **Level ditetapkan sebelum pasar buka, bukan saat harga bergerak.** Setiap
   angka di `rencana.json` punya kolom `dasar` yang menjelaskan dari mana ia
   datang. Angka tanpa dasar tidak masuk.

2. **Ukuran mengikuti LOKASI, bukan keyakinan.** Saham yang sudah naik 40%
   karena sebuah peristiwa sudah memuat peristiwa itu di harganya.

3. **Jangan mengejar harga yang lari.** Ini yang paling mahal. Pada 5 September
   2026, ASTER dimasuki di 99% rentang 30 hari; harga lari 1,5% selama
   persiapan, ukuran menyusut 42%, dan posisinya ditutup di harga yang tidak
   menghasilkan apa-apa. Di saham, ARB −15% membuat kesalahan yang sama jauh
   lebih mahal — tidak ada stop-loss otomatis yang bisa menyelamatkan Anda dari
   *auto rejection bawah*.

4. **Fee bukan tempat mencari penghematan.** Selisih antar-broker 0,10–0,18%,
   sementara **satu tick harga bernilai 0,29–0,57%**. Yang benar-benar
   menghemat: pakai limit, jangan menyeberang spread.

5. **Jangan tulis angka aturan bursa sebagai konstanta.** Batas harga minimum
   turun Rp50 → Rp1 bulan ini; fraksi harga dan ARA/ARB ikut berubah. Ambil
   `minmov` dari feed per emiten. Ini pola yang sudah tercatat di `CLAUDE.md`
   repo trading: `modal_awal` yang pernah tertanam $85 di dua tempat dan
   bertahan lama tanpa ketahuan.

6. **Saring keluar Papan Pemantauan Khusus.** 51 emiten berharga ≤ Rp50 memakai
   lelang berkala 5 sesi/hari, bukan continuous. Kalau ikut tersaring, alertnya
   menyesatkan.

## Susunan berkas

```
~/analisa-saham/
├── README.md                    aturan kerja
├── SISTEM.md                    berkas ini
├── RINGKASAN-2026-09-05.md      rekap seluruh riset
├── riset/                       5 laporan bersumber, diberi tanggal
├── data/
│   ├── rencana.json             watchlist + level + dasarnya
│   └── .keadaan_penjaga.json    anti-spam alert (dibuat otomatis)
├── bot/
│   ├── harga.py                 lapis data, sumber bisa ditukar
│   └── penjaga_saham.py         cek level → Telegram
└── catatan/                     keputusan sendiri + hasilnya
```

`catatan/` ada supaya keputusan yang meleset bisa dibaca ulang. Itu satu-satunya
cara aturan di atas lahir.

## Broker

**Stockbit** — fee 0,15%/0,25%, tanpa minimum deposit, Price Alert bawaan,
dan dokumentasi biaya paling jujur di antara semuanya (satu-satunya yang
terbuka soal bea meterai Rp10.000 dan biaya datafeed Rp16.650/bulan).

Yang lebih murah ada: **Indo Premier akun ODT 0,10%/0,20%**. Tapi selisihnya
0,10% — lebih kecil daripada satu tick. Bukan alasan untuk memilih.

**Tidak satu pun punya API.** Termasuk Stockbit.
