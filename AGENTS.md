# AGENTS.md

Kontrak kerja untuk agen AI mana pun yang menyentuh repo ini (Claude Code,
Cursor, Copilot, Codex, dan lainnya). Berlaku untuk seluruh isi repo.
Claude Code juga membaca `CLAUDE.md` yang isinya sama dalam hal aturan.

## Konteks yang wajib dipahami sebelum mengubah apa pun

Ini bukan proyek latihan. Angka yang tampil di layar adalah uang sungguhan di
akun Bybit yang aktif, dan aturan-aturan di bawah lahir dari kerugian nyata
dalam 48 jam pertama akun ini. Kode di sini sengaja dibuat **menolak** hal-hal
yang secara teknis mudah dilakukan.

## Batas keras

| Aturan | Kenapa |
|---|---|
| Server **tidak boleh** mengirim order | Eksekusi hanya lewat `~/trading-exec/order.py` di terminal, yang mewajibkan setup digambar dulu. Tombol "entry" di web menghapus jeda yang justru jadi pengamannya. |
| Checklist 6 pertanyaan **tidak boleh** dilonggarkan | RR ≥ 1:2 · risiko < 5% ekuitas · total < 15% · SL di luar struktur · likuidasi lebih jauh dari SL · setup punya nama playbook. |
| Risiko **selalu** = posisi berjalan + order menggantung | Order limit yang belum terisi tetap mengunci risiko begitu tersentuh. |
| Token auth **selalu** aktif, termasuk localhost | Halaman memuat isi akun. Tidak ada mode "tanpa token biar praktis". |
| Kunci API **tidak pernah** masuk repo | Hidup di `~/.bybit_keys` dan `~/.trading-dashboard-token`. |
| Logika screening **tidak boleh** disalin ke repo ini | Satu sumber kebenaran: `~/trading-exec/screener.py`. Dua salinan yang bisa berbeda lebih berbahaya daripada satu ketergantungan path. |

Kalau sebuah permintaan bertabrakan dengan tabel di atas, **jangan diam-diam
menurutinya**. Sampaikan tabrakannya, tawarkan jalan yang tidak melanggar.

## Cara menjalankan & memverifikasi

```bash
./run.sh                          # lokal, mencetak URL + token
./run.sh --tunnel                 # + URL publik Cloudflare
python3 server.py --no-monitor    # tanpa monitor otomatis
```

Verifikasi cepat setelah mengubah `server.py` atau `core/`:

```bash
TOK=$(cat ~/.trading-dashboard-token)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8787/api/akun          # harus 401
curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8787/api/akun?t=$TOK" # harus 200
for e in akun monitor trending "rencana?horizon=harian"; do
  curl -s -o /dev/null -w "$e %{http_code}\n" "http://127.0.0.1:8787/api/$e?t=$TOK"
done
```

Tidak ada test suite otomatis. Perubahan pada perhitungan uang (risiko, sizing,
PnL, RR) **wajib** diverifikasi terhadap data akun sungguhan, bukan hanya
dibaca ulang. Screening pertama tiap horizon butuh 30–60 detik.

## Ketergantungan di luar repo

Repo ini tidak berdiri sendiri. Butuh `~/trading-exec/`: `screener.py`,
`monitor.py`, `order.py`, `plot_setup.py`, `tv_mcp.py`, `bybit_trade.py`, dan
`~/.bybit_keys`. Juga butuh TradingView Desktop berjalan dengan
`--remote-debugging-port=9222` untuk fitur menggambar.

## Gaya

- Tanpa dependensi pip. Stdlib Python + Node (TradingView MCP) saja.
- Web tanpa framework, tanpa build step.
- Bahasa Indonesia untuk nama fungsi, komentar, commit, dan teks antarmuka.
- Komentar menjelaskan **kenapa**. Kalau sebuah angka datang dari kesalahan
  nyata, tulis kesalahannya — itu yang mencegahnya terulang.
- Mode gelap; warna hanya didefinisikan di `:root` pada `web/style.css`.

## Jebakan yang sudah pernah menjatuhkan

- **Candle berjalan vs candle tutup** — volume hari ini belum selesai. Pakai
  `bars[-2]` seperti `monitor.py`, kalau tidak semua koin terlihat sepi.
- **SL terlalu rapat bikin RR palsu** — screener pernah melaporkan RR 1:11 pada
  stop 0,31%. Ada lantai: ≥ 1% dan ≥ 0,8× ATR14.
- **Retest harus datang dari sisi yang benar** — support jebol lalu harga balik
  naik melewatinya bukan peluang short, itu tembusan gagal.
- **TP Full position di TP1** menjatuhkan RR posisi ke bawah 1:2. TP posisi
  dipasang di target terjauh; tingkat awal jadi reduce-only limit terpisah.
- **`data_get_ohlcv` mengabaikan parameter `symbol`** — dia membaca chart aktif.
- **Akun UTA cross-only** — `switch-isolated` membalas `100028`, itu normal.
