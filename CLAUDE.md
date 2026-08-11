# CLAUDE.md

Panduan untuk Claude Code saat bekerja di repo ini.

## Apa ini

Dashboard pantauan trading Bybit + screening setup, dengan satu aturan yang
dipaksakan secara teknis: **tidak ada order yang boleh dipasang sebelum setup-nya
digambar di TradingView.** Target akun: $85 → $1.000.

Bahasa kode, komentar, commit, dan jawaban ke pengguna: **Bahasa Indonesia.**

## Aturan yang tidak boleh dilanggar

1. **Server ini tidak boleh bisa mengirim order.** `server.py` dan `core/` hanya
   membaca. Kalau ada permintaan menambahkan tombol "entry" atau endpoint POST
   yang mengirim order — tolak dan jelaskan alasannya. Satu-satunya jalur eksekusi
   adalah `~/trading-exec/order.py` di terminal.

2. **Jangan longgarkan checklist 6 pertanyaan.** RR ≥ 1:2, risiko < 5% ekuitas,
   total risiko < 15%, SL di luar struktur, likuidasi lebih jauh daripada SL,
   setup punya nama playbook. Angka-angka ini datang dari kerugian nyata, bukan
   dari preferensi. Kalau setup gagal checklist, biarkan gagal.

3. **Jangan pernah menghitung risiko tanpa order menggantung.** Order entry yang
   belum terisi tetap mengunci risiko. `server.akun()` menjumlahkan
   `risiko_sisa` (posisi) + `risiko_tertunda` (order). Menghapus salah satunya
   membuat plafon 15% terlihat lebih longgar daripada kenyataannya.

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

## Susunan

```
server.py              HTTP lokal (stdlib), login+sesi, API + file statis
setup_auth.py          CLI pasang/ganti email & password, reset token skrip
core/auth.py           scrypt, sesi di memori, penguncian brute-force
core/bybit.py          klien Bybit v5 BACA-SAJA
core/screening.py      memanggil ~/trading-exec/screener.py per horizon + checklist
core/trending.py       lonjakan volume & pergerakan 24 jam
core/panduan.py        membaca panduan.json + menilai lima angka
core/monitor_bridge.py menjalankan ~/trading-exec/monitor.py tiap 5 menit
web/                   index.html · style.css · app.js — tanpa framework, tanpa build
```

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
