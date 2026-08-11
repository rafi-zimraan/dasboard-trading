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

Halaman ini memuat isi akun sungguhan: ekuitas, posisi, SL, riwayat PnL. Semua
akses lewat login; tidak ada mode "tanpa kunci biar praktis", bahkan di
localhost.

### Pasang kredensial (wajib sebelum pakai)

```bash
python3 setup_auth.py            # tanya email & password, tidak ditampilkan
python3 setup_auth.py --status   # lihat sudah terpasang atau belum
```

Password **tidak pernah disimpan** — yang tersimpan hanya turunan scrypt
(N=2¹⁵, r=8, ±67 ms per percobaan) beserta garam acak di
`~/.trading-dashboard-auth`, chmod 600, di luar repo. Password juga tidak
diterima lewat argumen perintah, karena argumen terbaca oleh `ps` dan tersimpan
di riwayat shell.

### Lapisan pertahanan

| Lapisan | Isinya |
|---|---|
| Login | scrypt + garam acak; email dan password dibandingkan dengan `compare_digest` sehingga waktu jawab tidak membocorkan tebakan yang hampir benar |
| Sesi | ID acak 32 byte, **hanya di memori** — tidak ada berkas sesi yang bisa dicuri, restart server memutus semua sesi |
| Cookie | `HttpOnly` + `SameSite=Strict` + `Secure` otomatis saat lewat HTTPS |
| Anti brute-force | 5 kali salah → alamat dikunci, waktu kunci **berlipat dua** tiap ronde berikutnya (60 s → 1 jam). Selama terkunci, password benar pun ditolak |
| IP asli | Dibaca dari `CF-Connecting-IP`; tanpa ini seluruh dunia terhitung `127.0.0.1` di balik tunnel dan penguncian jadi tidak berarti |
| CSP | `default-src 'self'` penuh — tidak ada skrip/gaya inline di halaman ini, jadi skrip suntikan tidak akan dieksekusi dan data tidak bisa dikirim ke domain lain |
| Header | `X-Frame-Options: DENY`, `nosniff`, `no-referrer`, `noindex`, `Permissions-Policy` |
| Batas body | Permintaan login di atas 4 KB langsung ditolak |
| Metode | Hanya `GET` dan `POST`; `POST` hanya melayani `/login` dan `/logout` — **tidak pernah** order |

### Akses untuk skrip

`curl`/cron memakai token acak 32 byte, bukan password:

```bash
curl -H "Authorization: Bearer $(cat ~/.trading-dashboard-token)" \
     http://127.0.0.1:8787/api/akun
```

Ganti token kapan saja dengan `python3 setup_auth.py --reset-token`.

### Saat di-tunnel

Port tetap terikat ke `127.0.0.1`; `cloudflared` berjalan di mesin yang sama dan
menyambung keluar, jadi tidak ada port yang dibuka ke jaringan. URL
`trycloudflare.com` berganti tiap kali tunnel dijalankan ulang.

Yang **masih** perlu Anda jaga sendiri: password yang kuat (12+ karakter, ada
simbol, bukan pola "kata + angka"), dan jangan membuka dashboard di komputer
yang tidak Anda percayai.

## Isi halaman

| Tab | Isinya |
|---|---|
| **Ringkasan** | Ekuitas, progres ke $1.000, kurva ekuitas, meter risiko, posisi terbuka, order aktif, aksi dari `monitor.py` |
| **Rencana** | Screening harian (1H+4H), mingguan (Daily), bulanan (Weekly) — tiap kandidat lengkap dengan level, sizing, checklist 6 pertanyaan, dan perintah `order.py` siap salin |
| **Trending** | Koin dengan perhatian yang sedang datang (volume vs MA12 koin itu sendiri), plus naik/turun terbesar |
| **Jurnal** | Statistik trade selesai dari closed-PnL Bybit + riwayat rencana yang pernah dibuat |
| **Panduan** | Aturan dari panduan trading — tiga playbook, checklist enam pertanyaan, empat cara merusak akun, tiga fase — plus rapor lima angka yang **dinilai langsung atas data akun nyata** |

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

## Panduan (tab Aturan)

Tab Panduan membaca `~/trading-exec/panduan.json`. Berkas itu **sengaja di luar
repo**: isinya memuat riwayat trade dan ukuran akun sungguhan, sedangkan repo
ini publik. Yang ada di repo hanya penampil dan penilainya.

Kalau berkas itu tidak ada, tab Panduan menjelaskan cara membuatnya, bukan
menampilkan aturan karangan sendiri — aturan yang salah lebih berbahaya
daripada aturan yang absen.

`modal_awal` dan `target` juga dibaca dari sana, jadi hanya ada satu tempat yang
menentukannya. (Angka $85 yang sempat tertanam di kode keliru: wallet $77,22
dikurangi realized kumulatif $21,55 memberi setoran ~$55,7 — cocok dengan $59 di
panduan, bukan $85.)

Rapor lima angka menilai statistik akun terhadap ambang di panduan, termasuk
ambang yang tidak enak didengar: win rate **di atas 80% ditandai bahaya**, bukan
prestasi, karena biasanya berarti untung diambil terlalu cepat dan rugi ditahan
terlalu lama.

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
