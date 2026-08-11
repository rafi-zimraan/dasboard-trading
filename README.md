# Dashboard Trading — target $1.000

Pantauan harian akun Bybit + screening setup pakai Playbook A/B/C, dengan satu
aturan yang dipaksakan secara teknis: **tidak ada order yang boleh dipasang
sebelum setup-nya digambar di TradingView.**

```bash
cd ~/DevProjects/@Website/trading-dashboard
./run.sh                     # lokal — mencetak URL lengkap beserta token
./run.sh --tunnel            # + URL publik lewat Cloudflare
./run.sh --lan               # + bisa dibuka dari HP di wifi yang sama
```

Tanpa dependensi pip. Butuh Python 3.9+, Node.js (untuk TradingView MCP), dan
`~/.bybit_keys`.

## Akses & keamanan

Halaman ini memuat isi akun sungguhan: ekuitas, posisi, SL, riwayat PnL. Karena
itu **setiap permintaan wajib membawa token**, termasuk dari localhost — tidak
ada mode "tanpa kunci biar praktis".

- Token dibuat sekali dan disimpan di `~/.trading-dashboard-token` (chmod 600).
  Bisa ditimpa lewat `DASH_TOKEN=...`.
- Server mencetak tautan lengkap `http://127.0.0.1:8787/?t=<token>` saat start.
- Membuka tautan itu memindahkan token ke cookie `HttpOnly` lalu **membersihkan
  URL**, supaya token tidak menetap di riwayat browser dan tidak ikut tersalin
  saat alamatnya dibagikan.
- Tanpa token, semua endpoint membalas `401`. Header `X-Robots-Tag: noindex` dan
  `Referrer-Policy: no-referrer` selalu dikirim.

Saat `--tunnel`, port tetap terikat ke `127.0.0.1`; `cloudflared` berjalan di
mesin yang sama dan menyambung keluar, jadi tidak ada port yang dibuka ke
jaringan. URL `trycloudflare.com` berganti tiap kali tunnel dijalankan ulang.

**Jangan bagikan tautan yang mengandung `?t=`** — itu setara memberikan akses
baca penuh ke akun.

## Isi halaman

| Tab | Isinya |
|---|---|
| **Ringkasan** | Ekuitas, progres ke $1.000, kurva ekuitas, meter risiko, posisi terbuka, order aktif, aksi dari `monitor.py` |
| **Rencana** | Screening harian (1H+4H), mingguan (Daily), bulanan (Weekly) — tiap kandidat lengkap dengan level, sizing, checklist 6 pertanyaan, dan perintah `order.py` siap salin |
| **Trending** | Koin dengan perhatian yang sedang datang (volume vs MA12 koin itu sendiri), plus naik/turun terbesar |
| **Jurnal** | Statistik trade selesai dari closed-PnL Bybit + riwayat rencana yang pernah dibuat |

## Aturan yang dipaksakan mesin, bukan niat

Order **tidak bisa** dikirim lewat dashboard. Satu-satunya jalur:

```bash
python3 ~/trading-exec/order.py SYMBOL side qty lev entry sl tp1 [tp2 ...] --live
```

`order.py` menolak order kalau:

1. **Setup gagal digambar** di TradingView (mis. aplikasinya mati) — order ditolak, bukan ditunda.
2. **Salah satu dari 6 pertanyaan checklist dijawab TIDAK**: RR < 1:2, risiko ≥ 5% ekuitas,
   total risiko ≥ 15%, SL terlalu rapat, atau likuidasi lebih dekat daripada SL.

Tanpa `--live` ia hanya menggambar + menjalankan checklist. Setiap rencana
dicatat ke `~/trading-exec/trade_plans.json`, termasuk kolom `digambar` — kalau
suatu saat `--skip-plot` dipakai, pelanggarannya tercatat permanen dan muncul
merah di tab Jurnal.

## Risiko dihitung termasuk order menggantung

Order entry yang belum terisi tetap membawa risiko: begitu terisi, jarak ke SL
langsung jadi uang. Meter risiko menjumlahkan **posisi berjalan + order
menggantung**, jadi plafon 15% tidak pernah terlihat lebih longgar dari
kenyataannya.

## monitor.py otomatis

Server menjalankan `~/trading-exec/monitor.py` tiap 5 menit di thread latar dan
menampilkan aksinya di tab Ringkasan. Logikanya tidak disalin — fungsi
`cek_posisi()` dan `cek_watchlist()` yang sama yang dipanggil, jadi aturan di
notifikasi pagi dan di dashboard tidak akan pernah berbeda.

Notifikasi macOS dari dashboard hanya berbunyi untuk aksi **baru**, supaya tidak
berdering tiap refresh. Jadwal launchd pagi tetap jalan seperti biasa.

Matikan dengan `python3 server.py --no-monitor`.

## Susunan

```
trading-dashboard/
├── server.py              # HTTP lokal, hanya baca; API + file statis
├── core/
│   ├── bybit.py           # klien Bybit v5 baca-saja (wallet, posisi, order, closed-PnL)
│   ├── screening.py       # memanggil ~/trading-exec/screener.py per horizon + checklist
│   ├── trending.py        # lonjakan volume & pergerakan 24 jam
│   └── monitor_bridge.py  # menjalankan monitor.py otomatis
└── web/                   # index.html · style.css · app.js (tanpa framework)
```

## Ketergantungan di luar repo

Repo ini **tidak berdiri sendiri**. Kloning saja tidak cukup untuk menjalankan —
dibutuhkan berkas berikut di `~/trading-exec/`:

| File | Guna |
|---|---|
| `screener.py` | Screening Playbook A/B/C — satu-satunya sumber kebenaran, dipanggil dashboard |
| `monitor.py` | Aturan "aksi apa yang perlu dilakukan" + watchlist |
| `order.py` | Gerbang wajib: gambar → checklist → order |
| `plot_setup.py` | Menggambar entry/SL/TP + zona R:R ke TradingView |
| `tv_mcp.py` | Klien Python untuk TradingView MCP |
| `bybit_trade.py` | Eksekutor order, dipanggil oleh `order.py` |

Plus `~/.bybit_keys` berisi baris `KEY=` dan `SECRET=`, serta TradingView Desktop
yang berjalan dengan `--remote-debugging-port=9222`.

Logika screening sengaja **tidak** disalin ke dalam repo ini. Dua salinan aturan
yang bisa berbeda lebih berbahaya daripada satu ketergantungan path.

Panduan untuk agen AI yang mengerjakan repo ini ada di
[`AGENTS.md`](AGENTS.md) dan [`CLAUDE.md`](CLAUDE.md).

## Catatan

- Tampilan sengaja berkomitmen pada mode gelap; semua warna ditulis eksplisit.
- Angka progres diukur dari modal awal $85, bukan dari nol — 0% berarti belum
  menghasilkan apa pun, 100% berarti $1.000 tercapai.
- Screening pertama tiap horizon butuh 30–60 detik (memindai 60 simbol);
  hasilnya di-cache 10 menit dan dipanaskan otomatis saat server start.
