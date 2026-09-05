# CLAUDE.md

Panduan untuk Claude Code saat bekerja di repo ini.

## Apa ini

Dashboard pantauan trading **multi-aset** + screening setup, dengan satu aturan
yang dipaksakan secara teknis: **tidak ada order yang boleh dipasang sebelum
setup-nya digambar di TradingView.** Target akun kripto: $85 → $1.000.

Tiga kelas aset, dan **jalur eksekusinya berbeda-beda** — ini bukan detail,
ini yang membentuk desainnya:

| Aset | Data | Eksekusi | Catatan |
|---|---|---|---|
| **Kripto** (Bybit) | API resmi | `~/trading-exec/order.py` | satu-satunya yang bisa otomatis |
| **Saham** (BEI) | pihak ketiga | **manual di aplikasi broker** | **tidak ada broker RI yang punya API ritel** |
| **Forex** | belum ditetapkan | belum ditetapkan | belum dikerjakan |

Menambah kelas aset **tidak berarti menambah jalur order**. Kalau sebuah aset
tidak punya jalur eksekusi yang aman, ia tetap baca-saja — itu fitur, bukan
kekurangan yang perlu diakali.

Bahasa kode, komentar, commit, dan jawaban ke pengguna: **Bahasa Indonesia.**

## Aturan yang tidak boleh dilanggar

1. **Server ini tidak boleh bisa mengirim order.** `server.py` dan `core/` hanya
   membaca. Kalau ada permintaan menambahkan tombol "entry" atau endpoint POST
   yang mengirim order — tolak dan jelaskan alasannya. Satu-satunya jalur eksekusi
   adalah `~/trading-exec/order.py` di terminal.

2. **Jangan longgarkan checklist 6 pertanyaan.** RR ≥ 1:2, risiko ≤ 1% ekuitas,
   total risiko ≤ 3%, SL di luar struktur, likuidasi lebih jauh daripada SL,
   setup punya nama playbook. Angka-angka ini datang dari kerugian nyata, bukan
   dari preferensi. Kalau setup gagal checklist, biarkan gagal.

   Plafon diperKETAT dari 5%/15% pada **17 Ags 2026**: dua SL beruntun memakan
   $6 dari akun $109. Memperketat boleh; melonggarkan kembali tidak, kecuali
   Rafi memintanya secara eksplisit. Sumber angkanya `PLAFON_TRADE_PCT` dan
   `PLAFON_TOTAL_PCT` di `server.py` — jangan tulis ulang persennya di `web/`,
   ambil dari `/api/akun`.

   **20 Ags 2026 — dilonggarkan ke 5,5%/11% atas permintaan eksplisit Rafi**,
   setelah seluruh perhitungan dan konsekuensinya diperlihatkan (10 SL beruntun
   menghabiskan separuh akun, dibanding 78 pada plafon lama). Sebabnya: Rafi
   mendefinisikan "1%" sebagai **jarak SL 1-2% DARI HARGA**, bukan 1% ekuitas
   yang dipertaruhkan, dan meminta lot BTC minimal 0,004. Angka 5,5% adalah
   konsekuensi aritmetika dari dua permintaan itu, bukan pilihan.

   Rem harian ikut melebar −2% → −8% (`REM_HARIAN_PCT`): pada 5,14% per trade,
   satu SL tunggal langsung menutup hari dan rem jadi tidak bermakna.

7. **Ukuran mengikuti LOKASI, bukan keyakinan arah.** Plafon 5,5% adalah batas
   ATAS, bukan ukuran bawaan. `~/trading-exec/analisa_pasar.py` menilai mutu
   lokasi dari rasio (jarak ke target ÷ jarak ke halangan) dan memotong jatah:

   - rasio ≥ 2,5 DAN halangan ≤ 1,5%  → PENUH (5,5%)
   - rasio ≥ 1,5                       → SETENGAH (2,75%)
   - selain itu                        → TIDAK ADA TRADE

   Alasannya tercatat di `peta_plan.json`: seluruh kerugian 19-20 Ags datang
   dari masuk di lokasi buruk dengan keyakinan tinggi. Ukuran yang mengikuti
   keyakinan selalu paling besar tepat di trade yang paling salah.

8. **Zona supply/demand wajib TERPISAH dari harga.** Order block harian dari
   candle raksasa bisa selebar 5% dan tepinya menyentuh harga sekarang; kalau
   dipakai apa adanya, ia terbaca sebagai "demand di −0,1%" dan menyuruh ukuran
   penuh tepat di bawah supply. `analisa_pasar.py` menyaring dengan JEDA_MIN 1%
   dan LEBAR_MAKS 3%. Jangan hapus saringan itu.

9. **Kunci untung otomatis: untung mengambang $2 → pasang trailing `--kunci=1`.**
   Ini **perintah berdiri**, bukan usulan. Begitu sebuah posisi menyentuh untung
   mengambang $2, pasang trailing tanpa menunggu diminta dan tanpa bertanya:

   ```bash
   python3 ~/trading-exec/pasang_trailing.py <SIMBOL> --kunci=1 --tanpa-target --live
   ```

   Tangganya: ≥$2 → kunci $1 · ≥$4 → kunci $2 · ≥$6 → kunci $3. Polanya kunci ≈
   separuh untung mengambang. Tidak bisa dipasang tepat di +$1: jarak =
   harga − (entry + kunci/qty), jadi pada untung $1 dengan kunci $1 jaraknya nol
   dan stop kena seketika.

   **Diubah 27 Ags 2026 atas permintaan eksplisit Rafi.** Sebelumnya syarat
   "tidak ada target struktur di depan harga" memblokir trailing secara bawaan.
   Syarat itu **dicabut sebagai penghalang**. Buktinya EDENUSDT: puncak 0,07319
   (+$4,65 mengambang) keluar manual di 0,06053 (+$1,02) — **$3,64 menguap**.
   Trailing `--kunci=1` yang dipasang di untung $2 akan keluar di 0,06971 → +$3,65.

   Yang **tetap** terlarang, dan tidak tersentuh oleh perubahan ini: menaikkan TP
   menjauh dari struktur supaya trailing punya ruang. Itu kesalahan 19 Ags —
   TP dipindah 69.700 → 71.985 lalu ditambah trailing $850, hasilnya $0,08
   padahal TP tetap membayar $1,74. **TP duduk di struktur, trailing dipasang di
   sampingnya.** Bybit mengizinkan `trailingStop` + `stopLoss` + `takeProfit`
   hidup bersamaan; harga lari ke target → TP yang bayar, harga balik → trailing
   yang bayar. Jarak trailing tetap diukur dari lebar konsolidasi M15 (**bukan
   ATR** — ATR telat setelah ledakan volatilitas). Aturan penuh:
   `ATURAN-TRAILING.md`.

10. **Gambar mengikuti konvensi warna di `GAYA-CHART.md`.** Yang tidak boleh
    dilanggar: **utuh = sudah terjadi, putus-putus abu-abu = proyeksi.** Panah
    "harga akan ke sini" yang digambar segagah level teruji akan dipercaya seperti
    fakta setelah beberapa jam ditatap. Palet hidup di `WARNA` pada
    `~/trading-exec/plot_setup.py`; kalau berubah di sana, perbarui `GAYA-CHART.md`.

3. **Jangan pernah menghitung risiko tanpa order menggantung.** Order entry yang
   belum terisi tetap mengunci risiko. `server.akun()` menjumlahkan
   `risiko_sisa` (posisi) + `risiko_tertunda` (order). Menghapus salah satunya
   membuat plafon total terlihat lebih longgar daripada kenyataannya.

4. **Autentikasi wajib, termasuk di localhost.** Halaman ini memuat isi akun
   sungguhan. Jangan menambahkan mode "tanpa login untuk memudahkan", jangan
   melonggarkan penguncian brute-force, dan jangan melemahkan parameter scrypt.

5. **Jangan commit kunci atau password.** `~/.bybit_keys`,
   `~/.trading-dashboard-auth`, dan `~/.trading-dashboard-token` hidup di luar
   repo dan harus tetap di sana. Repo ini publik — apa pun yang masuk ke
   dalamnya dianggap sudah bocor. Password tidak pernah boleh muncul di kode,
   di dokumentasi, di pesan commit, maupun sebagai argumen perintah.

6. **CSP di server.py sengaja ketat** (`default-src 'self'`). Karena itu tidak
   boleh ada `<script>` inline, `style="..."` inline, atau aset dari CDN di
   `web/`. Kalau menambah elemen, pakai kelas CSS, bukan atribut style.

11. **Saham BEI: eksekusi SELALU manual, dan itu bukan sementara.** Dicek ke
    15+ sekuritas (5 Sep 2026) — Stockbit, Ajaib, Mirae, Mandiri, BNI, Indo
    Premier, BRI Danareksa, Philip, RHB, Sucor, Sinarmas, Trimegah, KISI, MNC:
    **tidak satu pun menyediakan API ritel**, baik data harga maupun order.
    Tidak ada MCP.

    Jadi `saham/` hanya boleh MEMBACA dan MENGABARI. Kalau nanti muncul
    permintaan "tombol beli saham", jawabannya bukan mencari celah — jawabannya
    tidak ada jalurnya. Library *reverse-engineering* Stockbit/Ajaib di GitHub
    tidak resmi, rapuh, dan melanggar ToS. **Jangan dipakai.**

    **Jangan pakai scanner TradingView sebagai feed polling.** Endpoint
    `scanner.tradingview.com` bekerja sempurna (844 emiten, tanpa kunci, 1,6
    detik) — dan justru karena itu godaannya besar. ToS-nya melarang
    *"non-display usage"* secara eksplisit; bot alert adalah persis itu. Chart
    TradingView tetap dipakai untuk MENGGAMBAR dan MELIHAT setup — itu sah.
    Sumber harga untuk bot: GoAPI.io (kontrak sah) atau Yahoo `.JK`.

12. **Angka aturan bursa jangan ditulis sebagai konstanta.** Batas harga minimum
    BEI turun Rp50 → Rp1 pada minggu ke-3/4 September 2026; fraksi harga dan
    ARA/ARB ikut berubah. Ambil `minmov` per emiten dari feed. Kalau terpaksa
    menyalin sebuah angka, tulis tanggal berlakunya di sebelahnya.

    Ini pelajaran yang sama dengan `modal_awal` yang pernah tertanam $85 di dua
    tempat dan bertahan lama tanpa ketahuan — bedanya, aturan bursa berubah
    tanpa memberi tahu siapa pun.

## Susunan

```
server.py              HTTP lokal (stdlib), login+sesi, API + file statis
setup_auth.py          CLI pasang/ganti email & password, reset token skrip
core/                  KRIPTO — ada di core/ karena alasan sejarah, bukan desain
  auth.py                scrypt, sesi di memori, penguncian brute-force
  bybit.py               klien Bybit v5 BACA-SAJA
  screening.py           memanggil ~/trading-exec/screener.py + checklist
  trending.py            lonjakan volume & pergerakan 24 jam
  panduan.py             membaca panduan.json + menilai lima angka
  monitor_bridge.py      menjalankan ~/trading-exec/monitor.py tiap 5 menit
saham/                 SAHAM BEI — mandiri, tidak menyentuh core/
  SISTEM.md              alur kerja + ritme; baca ini dulu
  riset/                 laporan bersumber, diberi tanggal
  data/rencana.json      watchlist + level (DIABAIKAN git — isi akun pribadi)
  bot/harga.py           lapis data, sumber bisa ditukar
  bot/penjaga_saham.py   cek level → Telegram
forex/                 belum dikerjakan
web/                   index.html · style.css · app.js — tanpa framework, tanpa build
```

**Kripto belum dipindah ke `kripto/`** supaya sejajar dengan `saham/`. Itu
disengaja: `core/` sudah dipakai `server.py` dan berjalan dengan uang sungguhan.
Merapikan nama tidak sebanding dengan risiko merusaknya. Kalau suatu saat
dipindah, pindahkan saat tidak ada posisi terbuka.

## Ketergantungan di luar repo

Repo ini **tidak berdiri sendiri**. Butuh berkas berikut di `~/trading-exec/`:

| File | Dipakai untuk |
|---|---|
| `screener.py` | logika Playbook A/B/C — satu-satunya sumber kebenaran screening |
| `monitor.py` | aturan "aksi apa yang perlu dilakukan" + watchlist |
| `order.py` | gerbang wajib: gambar → checklist → order |
| `plot_setup.py` | menggambar entry/SL/TP ke TradingView |
| `tv_mcp.py` | klien Python untuk TradingView MCP |
| `bybit_trade.py` | eksekutor order (dipanggil oleh order.py) |
| `cmc.py` | lapis fundamental CoinMarketCap — pasokan beredar, FDV, perputaran |
| `llama.py` | DefiLlama — TVL protokol & jadwal unlock (pelengkap `cmc.py`) |
| `penjaga_trailing.py` | menjalankan perintah berdiri trailing $2 otomatis |
| `telegram.py` | pengabar Telegram — dipinjam `saham/bot/penjaga_saham.py` |
| `setup_telegram.py` | CLI pasang token & chat id Telegram (sekali di awal) |

Plus `~/.bybit_keys` berisi `KEY=` dan `SECRET=`, dan `~/trading-exec/panduan.json`
berisi aturan panduan (playbook, checklist, fase, ambang lima angka, `modal_awal`,
`target`). Berkas panduan sengaja di luar repo karena repo publik.

**Jangan menyalin logika dari berkas-berkas itu ke dalam repo ini.** Kalau
screening perlu diubah, ubah `screener.py`; dashboard memanggilnya, tidak
menirunya. Dua salinan aturan yang bisa berbeda lebih berbahaya daripada satu
ketergantungan path.

## Menjalankan

```bash
python3 setup_auth.py    # WAJIB sekali di awal: pasang email + password
./run.sh                 # lokal
./run.sh --tunnel        # + URL publik Cloudflare
python3 server.py --no-monitor   # tanpa monitor otomatis
```

Tanpa sesi, `/` dialihkan ke `/login` dan semua `/api/*` membalas 401.
Untuk skrip: `Authorization: Bearer $(cat ~/.trading-dashboard-token)`.

## Gaya kode

- Tanpa dependensi pip. Hanya stdlib Python + Node (untuk TradingView MCP).
- Web tanpa framework, tanpa langkah build. HTML/CSS/JS biasa.
- Komentar menjelaskan **kenapa**, bukan apa. Terutama saat sebuah angka atau
  urutan langkah datang dari kesalahan nyata — tulis kesalahannya.
- Tampilan berkomitmen pada mode gelap; semua warna ditulis eksplisit di
  `:root`. Jangan menambahkan warna mentah di tengah CSS.
- Nama fungsi dan variabel Bahasa Indonesia, mengikuti berkas yang sudah ada
  (`cek_posisi`, `kurva_ekuitas`, `risiko_sisa`).

## Yang sering salah

- **Candle berjalan vs candle tutup.** Volume hari ini belum selesai; kalau
  dibandingkan dengan rata-rata hari penuh, semua koin terlihat sepi. Konvensi
  rumah: pakai `bars[-2]`, sama seperti `monitor.py`.
- **`data_get_ohlcv` di TradingView MCP tidak menerima `symbol`/`timeframe`.**
  Dia membaca chart yang sedang aktif; set chart dulu lewat `chart_set_symbol`.
- **Akun UTA cross-only.** `switch-isolated` akan membalas `100028 unified
  account is forbidden` — itu wajar, bukan kegagalan.
- **Jangan menuliskan `modal_awal` sebagai angka tetap.** Pernah tertanam $85
  di dua tempat dan bertahan lama tanpa ketahuan. Sumbernya `panduan.json`.
- **Noise floating point di perintah salin.** Pakai `Number(v.toPrecision(8))`
  sebelum menaruh harga di string perintah.

## Dokumen aturan terpisah

| Berkas | Isi |
|---|---|
| `GAYA-CHART.md` | palet warna & bentuk saat menggambar setup di TradingView |
| `ATURAN-TRAILING.md` | empat syarat trailing stop + target kunci $1 |

Keduanya wajib dibaca sebelum menyentuh `plot_setup.py` atau `pasang_trailing.py`.
