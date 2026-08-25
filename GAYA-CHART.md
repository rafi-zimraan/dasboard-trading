# GAYA-CHART.md

Konvensi menggambar setup di TradingView. Berlaku untuk `~/trading-exec/plot_setup.py`,
untuk agen AI mana pun yang menggambar lewat TradingView MCP, dan untuk warna apa pun
yang dipakai menampilkan zona di dashboard.

Ditulis 23 Agustus 2026 atas permintaan Rafi setelah ia menunjukkan satu chart yang
gayanya ia sukai: zona supply magenta bertingkat, garis struktur putih tebal, dan
kotak proyeksi abu-abu yang jelas berbeda dari zona nyata.

**Diperbarui hari yang sama:** Rafi meminta tema **ungu**. Entry pindah dari biru
`#3987e5` ke ungu `#a855f7`, dan kotak zona hasil ikut ungu. Dua warna sengaja
TIDAK ikut berubah — alasannya di bawah.

## Dua warna yang tidak boleh diubah oleh selera

- **SL tetap merah `#d03b3b`.** Merah = salah adalah bawaan, bukan gaya. Kalau
  batas rugi sewarna dengan target, mata berhenti membedakan mana yang harus
  dihindari. Satu-satunya garis yang harus langsung terbaca saat panik adalah SL.
- **Proyeksi tetap abu-abu `#6b7280` dan putus-putus.** Begitu skenario digambar
  sewarna entry atau target, ia terbaca sebagai rencana yang sudah sah. Itu persis
  jebakan story BTC 23 Ags: panah ke 73.500 digambar setegas level nyata, padahal
  harga justru naik $1.500 dari situ.

## Kenapa gaya perlu diatur sama sekali

Chart bukan hiasan — dia alat pengambil keputusan. Dua kesalahan yang lahir dari
gambar yang tidak konsisten:

1. **Proyeksi yang terlihat seperti fakta.** Panah "harga akan ke sini" digambar
   dengan gaya yang sama seperti level yang benar-benar sudah teruji. Setelah
   beberapa jam menatapnya, otak berhenti membedakan mana yang sudah terjadi dan
   mana yang baru harapan. Karena itu **proyeksi WAJIB abu-abu dan putus-putus.**

2. **Zona yang tidak punya tingkat.** Supply yang sudah dijebol dan supply yang
   masih perawan digambar sama pekatnya, lalu keduanya dihormati sama besar.
   Zona yang sudah diuji dan jebol **wajib lebih pudar**.

## Palet

Semua warna dipilih untuk latar gelap. Jangan menambah warna di luar tabel ini;
kalau butuh peran baru, tambahkan barisnya di sini dulu.

| Peran | Warna | Hex | Bentuk | Transparansi |
|---|---|---|---|---|
| Entry | **ungu** | `#a855f7` | garis, tebal 2 | — |
| Stop loss | merah | `#d03b3b` | garis, tebal 2 | — |
| Take profit | hijau | `#0ca30c` | garis, tebal 2 | — |
| Zona risiko (entry→SL) | merah | `#d03b3b` | kotak | 85 |
| Zona hasil (entry→TP) | **ungu** | `rgba(168,85,247,0.14)` | kotak | — |
| Supply aktif (belum diuji) | magenta | `#e0409a` | kotak | 78 |
| Supply sudah diuji/jebol | maroon | `#7d2244` | kotak | 88 |
| Demand aktif (belum diuji) | toska | `#17a2b8` | kotak | 78 |
| Demand sudah diuji/jebol | biru tua | `#14506b` | kotak | 88 |
| Garis struktur (trendline, BOS) | putih | `#e8e8e8` | garis tren, tebal 2 | — |
| **Proyeksi / skenario** | **abu-abu** | `#6b7280` | kotak + panah, **putus-putus** | 90 |

## Aturan bentuk

- **Utuh = sudah terjadi. Putus-putus = belum terjadi.** Tidak ada pengecualian.
  Level yang ditembus, swing yang terbentuk, zona yang tercetak → garis utuh.
  Target, jalur harapan, skenario "kalau" → putus-putus abu-abu.
- **Tebal 2 untuk struktur, tebal 1 untuk level minor.** Kalau semua tebal, tidak
  ada yang menonjol.
- **Zona selalu kotak, level selalu garis.** Zona punya lebar (order block, range);
  level tidak. Menggambar order block sebagai garis tunggal membuang informasi
  lebar yang justru menentukan penempatan SL.
- **Label wajib berisi harga.** "Supply" saja tidak berguna saat di-screenshot;
  "Supply 78.073" berguna. `plot_setup.py` sudah menulis harga di tiap garis.
- **Pane indikator maksimal satu.** Chart yang penuh indikator menunda keputusan,
  bukan mempertajamnya.

## Sumber kebenaran

Palet ini hidup di `WARNA` pada `~/trading-exec/plot_setup.py`. Kalau berubah di
sana, perbarui tabel ini — jangan biarkan dua daftar warna berbeda.

Dashboard boleh memakai hex yang sama untuk zona di `web/style.css`, tapi tetap
lewat variabel `:root` (lihat aturan CSP dan mode gelap di `AGENTS.md`).

## Yang TIDAK boleh digambar

- **Garis dari chart orang lain tanpa konversi.** Feed berbeda punya harga
  berbeda: `BTCUSD` bukan `BYBIT:BTCUSDT.P`, dan wick XAU Bybit vs Pepperstone
  pernah beda $10. Level dari screenshot streamer wajib dicek ulang ke kline
  Bybit sebelum jadi garis.
- **Zona yang menyentuh harga sekarang.** Sudah disaring di `analisa_pasar.py`
  (`JEDA_MIN` 1%, `LEBAR_MAKS` 3%); jangan gambar manual apa yang sudah ditolak
  saringan itu.
