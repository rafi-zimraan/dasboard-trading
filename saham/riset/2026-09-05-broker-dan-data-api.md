# Sekuritas & Sumber Data Harga IDX

Riset per **5 September 2026**. Untuk memilih broker dan membangun bot alert.

## Temuan yang mengubah keputusan

1. **TIDAK SATU PUN dari 15+ sekuritas Indonesia punya API publik untuk ritel** —
   baik data harga maupun eksekusi order. Dicek lewat portal developer,
   subdomain `api.*`/`developer.*`, sitemap, FAQ, dan deskripsi aplikasi. Yang
   beredar hanya library *reverse-engineering* di GitHub (Stockbit, Ajaib):
   tidak resmi, tidak didukung, berpotensi melanggar ToS.

   **Konsekuensi: bot hanya bisa memberi sinyal. Eksekusi tetap manual.**
   Struktur yang sama dengan `dasboard-trading` — dashboard membaca,
   `order.py` yang mengeksekusi.

2. **MOST sudah MATI.** Aplikasi MOST Mandiri Sekuritas ditutup penuh
   **31 Desember 2025**; sejak 1 Januari 2026 pindah ke **Growin'**. Panduan
   mana pun yang masih menyebut MOST sudah usang.

3. **Fee bukan pembedanya untuk modal kecil** — lihat bagian tick di bawah.

## Tabel sekuritas (urut fee termurah)

| Sekuritas | Beli | Jual | Bolak-balik | Min. deposit | API |
|---|---|---|---|---|---|
| **Indo Premier — akun ODT** | 0,10% | 0,20% | **0,30%** | tanpa minimum | tidak ada |
| KISI (iKISI) | 0,13% | 0,23% | 0,36% | tidak terverifikasi | tidak ada |
| Sinarmas (SimInvest) | 0,1403% | 0,2403% | 0,3806% | tidak terverifikasi | tidak ada |
| **Stockbit Sekuritas** ⭐ | **0,15%** | **0,25%** | **0,40%** | **tanpa minimum** | tidak ada |
| **Philip (POEMS ID)** online ⭐ | 0,15% | 0,25% | 0,40% | Rp500.000 | tidak ada |
| RHB TradeSmart ID | 0,15% | 0,25% | 0,40% | ±Rp100rb | tidak ada |
| Sucor (SPOT) online | 0,15% | 0,25% | 0,40% | top-up Rp100rb | tidak ada |
| Mirae Asset (M-STOCK) | 0,15% | 0,25% | 0,40% | Rp0 (RDN Sinarmas) | tidak ada |
| Bibit Plus (via Stockbit Sek.) | 0,15% | 0,25% | 0,40% | wajib 1 lot | tidak ada |
| Ajaib Sekuritas | 0,1513% | 0,2513% | 0,4026% | tanpa minimum | tidak ada |
| BNI Sekuritas (BIONS) | 0,17% | 0,27% | 0,44% | Rp0 reguler | tidak ada |
| Mandiri Sekuritas — **Growin'** | 0,18% | 0,28% | 0,46% | tanpa minimum | tidak ada |
| Trimegah (Trima+) | 0,18%* | 0,28%* | 0,46%* | tanpa minimum | tidak ada |
| Indo Premier (IPOT) reguler | 0,19% | 0,29% | 0,48% | tanpa minimum | tidak ada |
| MNC (MotionTrade) | tidak dipublikasikan | — | — | Rp200rb (promo) | tidak ada |
| BRI Danareksa (BRIGHTS) | **tidak terverifikasi** | — | — | — | tidak ada |

⭐ = diverifikasi langsung dari halaman resmi · \* = sumber pihak ketiga tanpa tanggal

**Stockbit 0,15%/0,25%** diverifikasi di `help.stockbit.com` — sudah termasuk
levy 0,043%, PPN, dan PPh final jual 0,1%. ETF/right/waran: 0,15%/0,15%.
Tanpa minimum deposit; minimum beli 1 lot = 100 lembar.

**Philip 0,15%/0,25% online** diverifikasi di `poems.co.id/Support/Knowledgebase`.

### Nomor izin OJK — mana yang terverifikasi

**Terverifikasi langsung dari situs resmi masing-masing:**

| Sekuritas | Nomor izin |
|---|---|
| BNI Sekuritas | KEP-21/PM.2/2017 |
| Ajaib Sekuritas | KEP-171/PM/1992 |
| BRI Danareksa | KEP-291 & KEP-292/PM/1992 |

**BELUM terverifikasi — masih dari artikel sekunder:** Stockbit, Mirae Asset,
Mandiri Sekuritas, Indo Premier. Termasuk **Stockbit**, yang direkomendasikan
di berkas ini — statusnya sebagai perusahaan efek berizin tidak diragukan, tapi
nomor SK-nya belum dibaca dari sumber primer.

Kenapa ini perlu ditandai: nomor **KEP-11/PM/PPE/1996** ditemukan dikutip untuk
**dua broker berbeda** (Mandiri Sekuritas dan Indo Premier) — tanda kuat artikel
SEO saling salin. `ojk.go.id` dan `idx.co.id` dua-duanya memblokir akses
otomatis, jadi keempat nomor sisanya **harus dicek manual** di ojk.go.id atau
idx.co.id sebelum dipakai untuk keputusan apa pun.

### Nama aplikasi yang sering keliru

Sucor = **SPOT** (bukan "Profits") · Trimegah = **Trima+** (bukan "iTrimegah") ·
brokernya **Korea Investment and Sekuritas Indonesia (iKISI)** — KISI Asset
Management adalah MI terpisah · **Bibit** sudah punya fitur saham (**Bibit Plus**)
yang berjalan di atas lisensi Stockbit Sekuritas.

## Kenapa mengejar fee termurah bukan optimasi yang berarti

Selisih broker termurah (0,30%) vs termahal wajar (0,48%) = **0,18%**.
Bandingkan dengan friksi **satu tick harga**:

| Kode | Harga | Tick | **1 tick =** | Modal/lot |
|---|---|---|---|---|
| NSSS | 875 | 5 | **0,57%** | Rp87.500 |
| TAPG | 2.230 | 10 | **0,45%** | Rp223.000 |
| ADRO | 2.720 | 10 | 0,37% | Rp272.000 |
| PTBA | 2.880 | 10 | 0,35% | Rp288.000 |
| PGAS | 1.520 | 5 | 0,33% | Rp152.000 |
| LSIP | 1.685 | 5 | 0,30% | Rp168.500 |
| AALI | 8.550 | 25 | 0,29% | Rp855.000 |

**Satu tick (0,29–0,57%) hampir setara seluruh biaya bolak-balik 0,40%, dan
lebih besar dari selisih antar-broker.** Ini kebalikan dari Bybit. Yang benar-benar
menghemat: **tidak menyeberang spread tanpa perlu** — pakai limit, bukan market.

## Sumber data harga IDX

| Sumber | IDX? | Harga | Delay | Status 2026 |
|---|---|---|---|---|
| **yfinance `.JK`** | ✅ | **gratis, tanpa API key** | ~15–20 mnt | ✅ **HIDUP** — v1.7.0, 26 Ags 2026 |
| GoAPI.io IDX | ✅ | trial, lalu tidak publik | **3–10 mnt** | ✅ hidup |
| Sectors API v2 | ✅ IDX+SGX+KLSE | plan Insider | **EOD/harian** | ✅ hidup (v1 → `410 Gone`) |
| Twelve Data | ✅ `XIDX` | **Pro $99/bln** | **EOD saja** | ✅ hidup |
| EODHD | ❓ | $19,99–99,99/bln | EOD / 15 mnt | IDX tidak terkonfirmasi |
| Alpha Vantage | ❌ | — | — | IDX tidak ada di daftar bursa |
| Finnhub | ❌ | — | — | IDX tidak terbukti |
| Marketstack / FMP | ❌ | — | — | Indonesia tidak disebut |
| Polygon.io | ❌ | — | — | redirect ke `massive.com`, **US-only** |
| API resmi IDX | — | kontrak B2B | — | `idx.co.id` balas **403** ke non-browser |
| investpy | — | — | — | ☠️ **MATI** (terakhir Jan 2022) |
| tradingview-ta | — | — | — | ☠️ **BASI** (terakhir Okt 2022) |
| Google Finance | — | — | — | tidak pernah punya API |
| Stockbit / RTI / IDNFinancials | — | — | — | tidak ada API publik |

### yfinance — hasil uji jujur

**Tidak berhasil ditarik dari sandbox riset.** Semua percobaan ke
`query1`/`query2.finance.yahoo.com` membalas `"Too Many Requests"`, termasuk
alur cookie+crumb lengkap.

**Tapi ini hampir pasti pemblokiran IP datacenter, bukan matinya layanan.**
Tiga bukti tak langsung:

1. **yfinance v1.7.0 dirilis 26 Agustus 2026** — dipelihara aktif, dan kini
   memakai `curl_cffi` yang justru dipakai untuk menembus deteksi bot Yahoo.
2. **GoAPI.io — produk komersial berbayar — menyandarkan data IDX-nya pada
   Yahoo.** Tertulis di spesifikasi OpenAPI resmi mereka sendiri:
   > *"delay harga antara 3-10 menit. sumber: **YFinance** + GoogleFinance +
   > MSN Money + MarketWatch"*

   Padahal halaman marketing mereka menulis "real-time". **Membayar GoAPI =
   membayar wrapper atas data Yahoo yang gratis.** Kalau ada bisnis komersial
   berdiri di atas Yahoo `.JK`, jalurnya hidup.
3. Format ticker `.JK` tetap konvensi Yahoo yang stabil.

**Yang harus dilakukan:** uji `yf.Ticker("AALI.JK").history(period="5d")`
**dari koneksi rumah di Indonesia.** Jangan asumsikan mati, jangan asumsikan
hidup. Rate limit Yahoo tidak pernah dipublikasikan resmi — praktik komunitas:
jeda ≥1–2 detik antar request, jangan polling di bawah 5 menit.

**ToS Yahoo:** *"intended for personal use only"*. Bot alert pribadi cocok;
produk komersial tidak.

### TradingView scanner — bekerja, tapi ToS melarang

Endpoint `POST https://scanner.tradingview.com/indonesia/scan` bekerja sempurna:
**844 emiten IDX**, tanpa API key, hanya stdlib Python, 5 request = 1,59 detik.
Menyajikan `SMA20`, `SMA50`, `RSI`, `ATR`, `minmov`, 52w high/low.
Delay 10 menit.

**Tapi ToS TradingView melarangnya eksplisit:**
> *"licensed for exclusive **display-only** use... prohibits any form of
> **non-display usage**... automated trading, automated order generation..."*

**Bot alert Telegram adalah persis "non-display use".** Dicatat di sini supaya
opsinya diketahui — bukan supaya dipakai diam-diam. Pembanding: data real-time
IDX di TradingView dijual **$13/bulan**, dan itu pun display-only.

### Real-time vs delayed

- **Real-time sejati:** tidak ada jalur self-serve. Hanya kontrak datafeed IDX
  (B2B) atau langganan bursa TradingView $13/bln (display-only).
- **3–10 menit:** GoAPI.io
- **10 menit:** TradingView (ToS melarang bot)
- **~15–20 menit:** Yahoo/yfinance ← **cukup untuk alert level**
- **EOD saja:** Twelve Data (IDX), Sectors.app — **tidak bisa memicu alert intraday**

## Rekomendasi untuk bot alert

1. **yfinance `.JK`** — gratis, tanpa API key, delay ~15 menit. **Uji dulu dari
   koneksi rumah.** Dok: `https://pypi.org/project/yfinance/`
2. **Kalau diblokir → GoAPI.io** — `api.goapi.io/stock/idx/prices?symbols=...`
   (maks **50 simbol per panggilan**), delay 3–10 mnt, kontrak sah, dukungan
   bahasa Indonesia. Sadari: membeli kenyamanan, bukan data premium.
   Dok: `goapi.io/docs/`
3. **Untuk riset mingguan (bukan alert) → Sectors API v2** — EOD, tapi punya
   **Broker Activity per Symbol**, **Daily Net Foreign Inflow**, dan ekstensi
   **Mining dengan riwayat harga batu bara**. Relevan langsung untuk tesis
   sawit/energi. Dok: `https://docs.sectors.app/`

**Jam polling:** 09.00–16.15 WIB Sen–Jum. Dengan delay 10–20 menit, polling
lebih rapat dari 5 menit **tidak menambah informasi**.

**Saring keluar Papan Pemantauan Khusus.** Dari 844 emiten, **51 berharga
≤ Rp50** (BTEK@10, TAXI@13, KREN@14) — mekanismenya lelang berkala 5 sesi/hari,
bukan continuous. Kalau ikut tersaring, alert menyesatkan.

## Aturan bursa yang berubah bulan ini

- **Batas harga minimum Rp50 → Rp1.** Semula 7 Sep, **ditunda ke minggu ke-3/4
  September** (8 dari 91 Anggota Bursa belum lulus uji sistem). Rentang Rp1–Rp10
  memakai **fraksi nominal Rp1**, bukan persentase.

- **ARA/ARB asimetris** (sejak 8 April 2025):

  | Rentang | ARA | ARB |
  |---|---|---|
  | Rp50–Rp200 | +35% | **−15%** |
  | Rp200–Rp5.000 | +25% | **−15%** |
  | > Rp5.000 | +20% | **−15%** |

  Direktur Perdagangan BEI: *"belum menentukan kapan kembali simetris."*
  Saham IPO: batas bisa 2× lipat di hari pertama.

- **Trading halt IHSG:** −8% halt 30 mnt · −15% halt 30 mnt lagi · −20% suspend
  sampai akhir sesi.

- **PPN efektif 11%**, bukan 12%. Tarif nominal 12% (UU HPP) dikenakan atas
  **DPP Nilai Lain 11/12** → beban efektif 11%. Diformalkan lewat PER-1/PJ/2025.
  Tarif 12% penuh hanya barang mewah; jasa broker efek tidak termasuk.

- **PPh final jual 0,1%** (PP 41/1994 jo. PP 14/1997) · **pajak dividen 10%**
  dengan pembebasan bila diinvestasikan kembali (UU HPP).

- **Sedang dikaji, BELUM berlaku:** perluasan jam dagang 08.00–17.00 dan
  1 lot 100 → 50 lembar. Jangan diasumsikan berlaku.

**Konsekuensi desain yang paling penting: tabel fraksi harga, ARA, dan ARB
JANGAN ditulis sebagai konstanta.** Aturannya berubah bulan ini. Ambil `minmov`
dari feed per emiten; simpan tanggal berlaku di samping angka mana pun yang
terpaksa disalin.

Ini pola yang sudah tercatat di `CLAUDE.md` repo trading: `modal_awal` yang
pernah tertanam $85 di dua tempat dan bertahan lama tanpa ketahuan.

## Yang tetap kosong

- **BRI Danareksa (BRIGHTS)** — `brights.id` mati dari sisi riset. Tidak terisi.
- **MNC MotionTrade** — fee tidak dipublikasikan. Telepon 021-2980-3111.
- **Trimegah** — angka hanya dari pihak ketiga tanpa tanggal.
- **Rincian levy BEI/KPEI/KSEI** — angka 0,043% berasal dari Stockbit dan
  Philip, **bukan dari IDX**.
- **Harga Sectors Insider & GoAPI pasca-trial** — di balik login.
- **Nomor izin OJK Stockbit, Mirae, Mandiri, Indo Premier** — OJK dan IDX
  memblokir akses otomatis. Tiga lainnya (BNI, Ajaib, BRI Danareksa) sudah
  terverifikasi dari situs resmi.
- **Biaya admin RDN & idle** — bervariasi per bank, tidak ada angka nasional.

## Sumber

- [detikFinance — alasan BEI tunda harga minimum Rp1](https://finance.detik.com/bursa-dan-valas/d-8645658/alasan-bei-tunda-harga-minimum-saham-rp-1)
- [Kompas Money — BEI siapkan harga minimum Rp1](https://money.kompas.com/read/2026/09/03/181925826/bei-siapkan-harga-minimum-saham-rp-1-jp-morgan-sentimen-bisa-lebih-positif) · 3 Sep 2026
- [Bisnis.com — 149 saham sentuh Rp50 pada 2026](https://market.bisnis.com/read/20260824/7/1998451/149-saham-sentuh-rp50-pada-2026-intip-efek-pembukaan-batas-bawah-rp1) · 24 Ags 2026
- [Kontan — auto rejection asimetris](https://investasi.kontan.co.id/news/bei-putuskan-auto-rejection-asimetris-hingga-revisi-batas-trading-halt)
- [detikFinance — reviu Papan Pemantauan Khusus](https://finance.detik.com/bursa-dan-valas/d-8566032/bei-reviu-papan-pemantauan-khusus-wujud-continuous-improvement-dan-penguatan-pasar) · 8 Jul 2026
- [BCA Sekuritas — jam perdagangan](https://www.bcasekuritas.co.id/help/faq/exchange-trading-hours)
- [CNBC Indonesia — kebijakan PPN](https://www.cnbcindonesia.com/news/20250106144809-4-601101/sri-mulyani-ungkap-alasan-ubah-kebijakan-ppn-usai-didatangi-prabowo)
- [PP 14/1997](https://peraturan.bpk.go.id/Details/56237/pp-no-14-tahun-1997) · [PwC Tax Summaries Indonesia](https://taxsummaries.pwc.com/indonesia/individual/other-taxes)
- Halaman resmi: `help.stockbit.com` · `poems.co.id/Support/Knowledgebase` · `goapi.io/v1.0.1.yaml` · `docs.sectors.app`
