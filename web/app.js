'use strict';

const $ = (s) => document.querySelector(s);
const el = (t, c, txt) => { const n = document.createElement(t); if (c) n.className = c; if (txt != null) n.textContent = txt; return n; };

const uang = (v, d = 2) => (v < 0 ? '-' : '') + '$' + Math.abs(v).toLocaleString('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (v, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d) + '%';
const harga = (v) => v == null ? '—' : (Math.abs(v) >= 100 ? v.toLocaleString('id-ID', { maximumFractionDigits: 2 })
  : Math.abs(v) >= 1 ? v.toFixed(4) : v.toPrecision(4));
const jam = (ms) => new Date(ms).toLocaleString('id-ID', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
const tanda = (v) => v > 0 ? 'pos' : v < 0 ? 'neg' : '';

async function ambil(url) {
  const r = await fetch(url);
  const j = await r.json();
  if (j && j.error) throw new Error(j.error);
  return j;
}

function tabel(node, kolom, baris, render) {
  node.innerHTML = '';
  if (!baris.length) { node.innerHTML = `<tr><td class="empty">Belum ada data.</td></tr>`; return; }
  const thead = el('thead'); const tr = el('tr');
  kolom.forEach(k => tr.appendChild(el('th', null, k)));
  thead.appendChild(tr); node.appendChild(thead);
  const tb = el('tbody');
  baris.forEach(b => tb.appendChild(render(b)));
  node.appendChild(tb);
}

function sel(cells) {
  const tr = el('tr');
  cells.forEach(c => {
    const td = el('td');
    if (typeof c === 'object' && c !== null) { td.className = c.c || ''; td.textContent = c.t; }
    else td.textContent = c;
    tr.appendChild(td);
  });
  return tr;
}

/* ================= kurva ekuitas ================= */
function gambarKurva(titik) {
  const svg = $('#equity-chart'), tip = $('#equity-tip');
  svg.innerHTML = '';
  if (titik.length < 2) return;

  const W = svg.clientWidth || 600, H = 210;
  const pad = { t: 14, r: 52, b: 22, l: 10 };
  const xs = titik.map(p => p.t), ys = titik.map(p => p.equity);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  let y0 = Math.min(...ys), y1 = Math.max(...ys);
  const bantal = (y1 - y0) * 0.15 || 1;
  y0 -= bantal; y1 += bantal;

  const X = (v) => pad.l + (v - x0) / ((x1 - x0) || 1) * (W - pad.l - pad.r);
  const Y = (v) => pad.t + (1 - (v - y0) / ((y1 - y0) || 1)) * (H - pad.t - pad.b);
  const NS = 'http://www.w3.org/2000/svg';
  const mk = (n, a) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); return e; };

  // gridline resesif + label sumbu
  for (let i = 0; i <= 3; i++) {
    const v = y0 + (y1 - y0) * i / 3, y = Y(v);
    svg.appendChild(mk('line', { x1: pad.l, x2: W - pad.r, y1: y, y2: y, stroke: '#2c2c2a', 'stroke-width': 1 }));
    const t = mk('text', { x: W - pad.r + 7, y: y + 4, fill: '#898781', 'font-size': 10 });
    t.textContent = '$' + v.toFixed(0);
    svg.appendChild(t);
  }

  const d = titik.map((p, i) => `${i ? 'L' : 'M'}${X(p.t).toFixed(1)},${Y(p.equity).toFixed(1)}`).join(' ');
  const area = `${d} L${X(x1).toFixed(1)},${Y(y0).toFixed(1)} L${X(x0).toFixed(1)},${Y(y0).toFixed(1)} Z`;

  const grad = mk('linearGradient', { id: 'g1', x1: '0', y1: '0', x2: '0', y2: '1' });
  grad.appendChild(mk('stop', { offset: '0%', 'stop-color': '#3987e5', 'stop-opacity': '0.28' }));
  grad.appendChild(mk('stop', { offset: '100%', 'stop-color': '#3987e5', 'stop-opacity': '0' }));
  const defs = mk('defs'); defs.appendChild(grad); svg.appendChild(defs);

  svg.appendChild(mk('path', { d: area, fill: 'url(#g1)' }));
  svg.appendChild(mk('path', { d, fill: 'none', stroke: '#3987e5', 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }));

  // titik akhir diberi cincin permukaan supaya tidak melebur ke garis
  const last = titik[titik.length - 1];
  svg.appendChild(mk('circle', { cx: X(last.t), cy: Y(last.equity), r: 4.5, fill: '#3987e5', stroke: '#1a1a19', 'stroke-width': 2 }));

  // lapisan hover: crosshair + tooltip
  const rule = mk('line', { y1: pad.t, y2: H - pad.b, stroke: '#898781', 'stroke-width': 1, 'stroke-dasharray': '3 3', opacity: 0 });
  const dot = mk('circle', { r: 4, fill: '#3987e5', stroke: '#1a1a19', 'stroke-width': 2, opacity: 0 });
  svg.appendChild(rule); svg.appendChild(dot);

  const hit = mk('rect', { x: 0, y: 0, width: W, height: H, fill: 'transparent' });
  svg.appendChild(hit);
  hit.addEventListener('mousemove', (e) => {
    const r = svg.getBoundingClientRect();
    const mx = e.clientX - r.left;
    let best = 0, bd = Infinity;
    titik.forEach((p, i) => { const dd = Math.abs(X(p.t) - mx); if (dd < bd) { bd = dd; best = i; } });
    const p = titik[best], px = X(p.t), py = Y(p.equity);
    rule.setAttribute('x1', px); rule.setAttribute('x2', px); rule.setAttribute('opacity', 1);
    dot.setAttribute('cx', px); dot.setAttribute('cy', py); dot.setAttribute('opacity', 1);
    tip.hidden = false;
    tip.style.left = px + 'px'; tip.style.top = py + 'px';
    tip.innerHTML = `<div><b>${uang(p.equity)}</b></div><div class="t-sub">${p.label} · ${jam(p.t)}</div>`;
  });
  hit.addEventListener('mouseleave', () => {
    rule.setAttribute('opacity', 0); dot.setAttribute('opacity', 0); tip.hidden = true;
  });

  tabel($('#equity-table'), ['Waktu', 'Ekuitas', 'Keterangan'], titik.slice().reverse(),
    (p) => sel([jam(p.t), uang(p.equity), p.label]));
}

/* ================= meter risiko ================= */
function meter(label, nilai, plafon, warna, ket) {
  const row = el('div', 'meter-row');
  const top = el('div', 'meter-top');
  top.appendChild(el('span', null, label));
  const b = el('b', null, `${uang(nilai)} / ${uang(plafon)}`);
  top.appendChild(b);
  row.appendChild(top);
  const tr = el('div', 'meter-track');
  const fl = el('div', 'meter-fill');
  fl.style.width = Math.min(100, plafon ? nilai / plafon * 100 : 0) + '%';
  fl.style.background = warna;
  tr.appendChild(fl); row.appendChild(tr);
  if (ket) { const n = el('div', 'lvl'); n.style.cssText = 'background:none;border:0;padding:4px 0 0'; n.appendChild(el('div', 'd', ket)); row.appendChild(n); }
  return row;
}

/* ================= ringkasan ================= */
async function muatRingkasan() {
  const a = await ambil('/api/akun');
  const w = a.wallet, r = a.risiko;

  $('#equity').textContent = uang(w.equity);
  $('#equity-sub').innerHTML = `wallet ${uang(w.wallet)} · floating <span class="${tanda(w.unrealised)}">${uang(w.unrealised)}</span> · realized kumulatif <span class="${tanda(w.realised_kumulatif)}">${uang(w.realised_kumulatif)}</span>`;
  $('#goal-pct').textContent = w.progres_pct.toFixed(1) + '%';
  $('#goal-fill').style.width = Math.min(100, w.progres_pct) + '%';
  $('#goal-start').textContent = uang(w.modal_awal, 0);
  $('#goal-end').textContent = uang(w.target, 0);
  const sisa = w.target - w.equity;
  $('#goal-note').textContent = `Tumbuh ${pct(w.pertumbuhan_pct)} dari modal awal. Sisa ${uang(sisa)} lagi — pada +2,9% per trade itu sekitar ${Math.ceil(Math.log(w.target / w.equity) / Math.log(1.029))} trade menang berturut.`;

  const t = $('#tiles'); t.innerHTML = '';
  const tile = (label, val, sub, cls) => {
    const n = el('div', 'tile');
    n.appendChild(el('p', 'label', label));
    n.appendChild(el('p', 'v ' + (cls || ''), val));
    n.appendChild(el('p', 's', sub));
    return n;
  };
  t.appendChild(tile('Posisi terbuka', String(a.posisi.length), a.posisi.map(p => p.symbol.replace('USDT', '')).join(' · ') || '—'));
  // Plafon datang dari /api/akun, tidak ditulis ulang di sini. Angka yang
  // tertanam dua kali akan berbeda suatu hari, dan yang dipercaya biasanya
  // yang lebih longgar. Dua desimal karena pada plafon 1% "1,0%" bisa berarti
  // 0,96% atau 1,04% — dua hal berbeda tepat di garis yang sedang dijaga.
  t.appendChild(tile('Risiko berjalan', uang(r.terbuka_usd), `${r.terbuka_pct.toFixed(2)}% dari ekuitas (plafon ${r.plafon_pct}%)`, r.terbuka_pct > r.plafon_pct ? 'neg' : ''));
  t.appendChild(tile('Maks per trade', uang(r.maks_per_trade_usd), `${r.maks_per_trade_pct}% dari ekuitas hari ini`));
  t.appendChild(tile('Order aktif', String(a.orders.length), a.orders.filter(o => o.reduce_only).length + ' reduce-only'));
  const s = a.statistik;
  t.appendChild(tile('Winrate', s.total ? s.winrate.toFixed(0) + '%' : '—', `${s.menang}M / ${s.kalah}K dari ${s.total} trade`));
  t.appendChild(tile('Profit factor', s.total ? (isFinite(s.profit_factor) ? s.profit_factor.toFixed(2) : '∞') : '—', 'untung kotor ÷ rugi kotor'));

  // Modal awal datang dari panduan; jangan pernah menuliskannya sebagai
  // angka tetap di HTML — pernah salah $85 dan diam-diam bertahan lama.
  $('#kurva-sub').textContent =
    `Dari modal awal ${uang(w.modal_awal, 0)}, tiap titik satu trade yang ditutup. `
    + 'Titik terakhir termasuk floating.';

  gambarKurva(a.kurva);

  const rm = $('#risk-meter'); rm.innerHTML = '';
  // Ambang warna dihitung sebagai rasio terhadap plafon, bukan angka tetap.
  // Dulu kuning dipatok di 10%: begitu plafon turun ke 3%, meter tidak akan
  // pernah kuning lagi — ia melompat dari hijau langsung ke merah, dan
  // peringatan yang paling berguna justru yang hilang.
  $('#risk-plafon').textContent =
    `Plafon rumah: ${r.maks_per_trade_pct}% per trade, ${r.plafon_pct}% total. `
    + 'Dihitung dari ekuitas hari ini.';
  const rasio = r.plafon_pct ? r.terbuka_pct / r.plafon_pct : 0;
  rm.appendChild(meter('Total risiko terbuka', r.terbuka_usd, r.plafon_usd,
    rasio > 1 ? 'var(--critical)' : rasio > 0.67 ? 'var(--warning)' : 'var(--good)',
    `Plafon ${r.plafon_pct}% = ${uang(r.plafon_usd)}. Sisa ruang ${uang(r.sisa_slot_usd)}.`));
  a.posisi.forEach(p => rm.appendChild(meter(
    `${p.symbol} (${p.side})`, p.risiko_sisa, r.maks_per_trade_usd,
    p.risiko_sisa === 0 ? 'var(--good)' : 'var(--series-1)',
    p.risiko_sisa === 0 ? 'SL sudah di sisi profit — risiko nol.' : `SL ${harga(p.sl)}`)));
  $('#risk-note').textContent = r.terbuka_pct > r.plafon_pct
    ? 'LEWAT PLAFON. Tunggu satu posisi selesai sebelum membuka yang baru.'
    : `Masih ada ruang ${uang(r.sisa_slot_usd)} sebelum menyentuh plafon ${r.plafon_pct}%.`;

  tabel($('#pos-table'),
    ['Simbol', 'Arah', 'Ukuran', 'Entry', 'Mark', 'PnL', '%', 'SL', 'Risiko sisa', 'Likuidasi'],
    a.posisi, (p) => {
      const tr = el('tr');
      const c = [
        { t: p.symbol, c: 'sym' },
        { t: p.side, c: '' },
        { t: p.size.toLocaleString('id-ID'), c: '' },
        { t: harga(p.entry), c: '' },
        { t: harga(p.mark), c: '' },
        { t: uang(p.unrealised), c: tanda(p.unrealised) },
        { t: pct(p.pnl_pct), c: tanda(p.pnl_pct) },
        { t: harga(p.sl), c: '' },
        { t: p.risiko_sisa === 0 ? 'nol' : uang(p.risiko_sisa), c: p.risiko_sisa === 0 ? 'pos' : '' },
        { t: harga(p.liq), c: '' },
      ];
      c.forEach((x, i) => {
        const td = el('td', x.c);
        if (i === 1) { const s = el('span', 'pill ' + x.t.toLowerCase(), x.t); td.appendChild(s); }
        else td.textContent = x.t;
        tr.appendChild(td);
      });
      return tr;
    });

  tabel($('#order-table'), ['Simbol', 'Sisi', 'Jenis', 'Qty', 'Harga', 'Pemicu', 'Reduce-only', 'Status'],
    a.orders, (o) => sel([
      { t: o.symbol, c: 'sym' }, o.side, o.kind, o.qty.toLocaleString('id-ID'),
      harga(o.price), harga(o.trigger), o.reduce_only ? 'ya' : '—', o.status]));

  return a;
}

async function muatMonitor() {
  const box = $('#aksi-list'); box.innerHTML = '';
  try {
    const m = await ambil('/api/monitor');
    if (m.error) { box.innerHTML = `<p class="err">monitor.py gagal: ${m.error}</p>`; return; }
    if (!m.aksi || !m.aksi.length) {
      const d = el('div', 'aksi ok');
      d.appendChild(el('span', 'ic', '✓'));
      d.appendChild(el('span', null, 'Tidak ada aksi. Diamkan posisi.'));
      box.appendChild(d);
    } else {
      m.aksi.forEach(a => {
        const d = el('div', 'aksi warn');
        d.appendChild(el('span', 'ic', '⚠'));
        d.appendChild(el('span', null, a));
        box.appendChild(d);
      });
    }
    (m.posisi || []).concat(m.watchlist || []).forEach(b => {
      const p = el('p', 'card-sub'); p.style.whiteSpace = 'pre-wrap'; p.textContent = b;
      box.appendChild(p);
    });
  } catch (e) { box.innerHTML = `<p class="err">${e.message}</p>`; }
}

/* ================= rencana ================= */
function kartuSetup(s) {
  const c = el('div', 'card');
  const h = el('div', 'setup-head');
  const nm = el('h2', null, s.symbol);
  h.appendChild(nm);
  h.appendChild(el('span', 'pill ' + (s.side === 'long' ? 'long' : 'short'), s.side.toUpperCase()));
  h.appendChild(el('span', 'card-sub', `Playbook ${s.playbook} · TF ${s.tf} · turnover $${(s.turnover / 1e6).toFixed(0)}M`));
  const rr = el('span', 'rr'); rr.innerHTML = `RR <b>1:${s.rr.toFixed(2)}</b>`;
  h.appendChild(rr);
  c.appendChild(h);

  const lv = el('div', 'levels');
  const kotak = (kelas, k, p, d) => {
    const n = el('div', 'lvl ' + kelas);
    n.appendChild(el('div', 'k', k));
    n.appendChild(el('div', 'p', harga(p)));
    if (d) n.appendChild(el('div', 'd', d));
    return n;
  };
  lv.appendChild(kotak('entry', 'Entry limit', s.entry, pct(s.dist_pct, 2) + ' dari harga'));
  lv.appendChild(kotak('sl', 'Stop loss', s.sl, pct(Math.abs(s.sl - s.entry) / s.entry * 100, 2) + ' jarak'));
  s.tps.forEach((t, i) => lv.appendChild(kotak('tp', 'TP' + (i + 1), t,
    '1:' + (Math.abs(t - s.entry) / Math.abs(s.entry - s.sl)).toFixed(2))));
  c.appendChild(lv);

  const info = el('p', 'card-sub');
  info.textContent = `Harga ${harga(s.last)} (${pct(s.chg24)} 24j)` +
    (s.vol_x ? ` · tembusan ${s.bars_ago} bar lalu, volume ${s.vol_x.toFixed(2)}× MA12` : '') +
    ` · sizing risiko ${uang(s.sizing.risiko_usd)} → ${s.sizing.qty >= 100 ? s.sizing.qty.toFixed(0) : s.sizing.qty.toFixed(6)} koin (margin 15x ${uang(s.sizing.margin)})`;
  c.appendChild(info);

  const ul = el('ul', 'check');
  s.checklist.forEach(q => {
    const li = el('li');
    li.appendChild(el('span', 'm ' + (q.ok ? 'yes' : 'no'), q.ok ? '✓' : '✕'));
    const w = el('span');
    w.appendChild(document.createTextNode(q.q + ' '));
    w.appendChild(el('span', 'd', q.detail));
    li.appendChild(w);
    ul.appendChild(li);
  });
  c.appendChild(ul);

  // toPrecision membuang ekor floating point (77.90782999999999 -> 77.90783);
  // Number(...) lalu membuang nol berlebih supaya perintahnya enak dibaca.
  const rapi = (v) => Number(v.toPrecision(8)).toString();
  const qty = s.sizing.qty >= 100 ? Math.round(s.sizing.qty) : Number(s.sizing.qty.toPrecision(3));
  const perintah = `python3 ~/trading-exec/order.py ${s.symbol} ${s.side} ${qty} 15 `
    + `${rapi(s.entry)} ${rapi(s.sl)} ${s.tps.map(rapi).join(' ')} --tf ${s.tf}`;
  const cmd = el('div', 'cmd');
  cmd.appendChild(el('code', null, perintah));
  const btn = el('button', 'btn', 'Salin');
  btn.onclick = () => { navigator.clipboard.writeText(perintah); btn.textContent = 'Tersalin'; setTimeout(() => btn.textContent = 'Salin', 1400); };
  cmd.appendChild(btn);
  c.appendChild(cmd);

  if (!s.lolos) {
    const w = el('p', 'card-sub');
    w.style.color = 'var(--critical)';
    w.textContent = 'Ada pertanyaan checklist yang dijawab TIDAK — order.py akan menolak setup ini apa adanya.';
    c.appendChild(w);
  }
  return c;
}

async function muatRencana(horizon) {
  const body = $('#rencana-body');
  body.innerHTML = '<p class="empty">Memindai pasar… (screening pertama bisa 30–60 detik)</p>';
  try {
    const r = await ambil('/api/rencana?horizon=' + horizon);
    body.innerHTML = '';
    const info = el('p', 'card-sub');
    info.textContent = `Timeframe ${r.tf} · ekuitas ${uang(r.ekuitas)} · risiko berjalan ${uang(r.risiko_terbuka)} · ${r.setups.length} kandidat lolos syarat.`;
    body.appendChild(info);
    if (!r.setups.length) {
      body.appendChild(el('p', 'empty',
        'Tidak ada setup yang lolos semua syarat pada horizon ini. Tidak ada trade — trade yang terlewat tidak pernah menagih biaya.'));
      return;
    }
    r.setups.forEach(s => body.appendChild(kartuSetup(s)));
  } catch (e) { body.innerHTML = `<p class="err">${e.message}</p>`; }
}

/* ================= trending ================= */
async function muatTrending() {
  const box = $('#volspike'); box.innerHTML = '<p class="empty">Memuat…</p>';
  try {
    const t = await ambil('/api/trending');
    box.innerHTML = '';
    const maks = Math.max(...t.lonjakan_volume.map(r => r.vol_x), 1);
    t.lonjakan_volume.forEach(r => {
      const row = el('div', 'bar-row');
      row.appendChild(el('span', 'sym', r.symbol.replace('USDT', '')));
      const tr = el('div', 'bar-track');
      const fl = el('div', 'bar-fill');
      fl.style.width = (r.vol_x / maks * 100) + '%';
      tr.appendChild(fl); row.appendChild(tr);
      const v = el('span', 'bar-val', r.vol_x.toFixed(2) + '× · ' + pct(r.chg));
      v.title = `Hari terakhir yang sudah tutup: ${r.vol_x.toFixed(2)}× MA12. `
        + `Hari berjalan baru ${(r.vol_x_berjalan ?? 0).toFixed(2)}× (belum selesai).`;
      row.appendChild(v);
      box.appendChild(row);
    });
    const kol = ['Simbol', 'Harga', '24 jam', 'Turnover'];
    const baris = (r) => sel([{ t: r.symbol, c: 'sym' }, harga(r.last),
      { t: pct(r.chg), c: tanda(r.chg) }, '$' + (r.turnover / 1e6).toFixed(0) + 'M']);
    tabel($('#gainers'), kol, t.naik, baris);
    tabel($('#losers'), kol, t.turun, baris);
  } catch (e) { box.innerHTML = `<p class="err">${e.message}</p>`; }
}

/* ================= jurnal ================= */
async function muatJurnal(a) {
  const s = a.statistik;
  const t = $('#stat-tiles'); t.innerHTML = '';
  const tile = (l, v, sub, cls) => {
    const n = el('div', 'tile');
    n.appendChild(el('p', 'label', l));
    n.appendChild(el('p', 'v ' + (cls || ''), v));
    n.appendChild(el('p', 's', sub));
    return n;
  };
  t.appendChild(tile('Trade selesai', String(s.total), 'dari closed-PnL Bybit'));
  t.appendChild(tile('Net realized', uang(s.net), 'setelah fee', tanda(s.net)));
  t.appendChild(tile('Rata-rata menang', uang(s.rata_menang), `${s.menang} trade`, 'pos'));
  t.appendChild(tile('Rata-rata kalah', uang(s.rata_kalah), `${s.kalah} trade`, s.kalah ? 'neg' : ''));

  tabel($('#closed-table'), ['Ditutup', 'Simbol', 'Arah', 'Qty', 'Masuk', 'Keluar', 'Hasil'],
    a.closed, (c) => sel([jam(c.closed_at), { t: c.symbol, c: 'sym' }, c.side,
      c.qty.toLocaleString('id-ID'), harga(c.entry), harga(c.exit),
      { t: uang(c.pnl), c: tanda(c.pnl) }]));

  try {
    const p = await ambil('/api/plans');
    tabel($('#plans-table'), ['Waktu', 'Simbol', 'Arah', 'Entry', 'SL', 'TP', 'Risiko', 'Digambar', 'Status'],
      p, (r) => sel([jam(r.waktu), { t: r.symbol, c: 'sym' }, r.side, harga(r.entry), harga(r.sl),
        (r.tps || []).map(harga).join(' / '), uang(r.risiko_usd || 0),
        { t: r.digambar ? 'ya' : 'TIDAK', c: r.digambar ? 'pos' : 'neg' }, r.status || '—']));
  } catch (e) { /* file rencana belum ada */ }
}

/* ================= panduan ================= */
async function muatPanduan() {
  let d;
  try { d = await ambil('/api/aturan'); }
  catch (e) { $('#rapor').innerHTML = `<p class="err">${e.message}</p>`; return; }

  if (d.error) { $('#rapor').innerHTML = `<p class="err">${d.error}</p>`; return; }
  $('#panduan-sumber').textContent = d.sumber || '';

  // --- rapor lima angka ---
  const r = $('#rapor'); r.innerHTML = '';
  const fmtNilai = (b) => {
    if (b.nilai == null) return '—';
    if (b.kunci === 'winrate') return b.nilai.toFixed(0) + '%';
    if (b.kunci === 'pelanggaran') return String(b.nilai);
    return b.nilai.toFixed(2);
  };
  d.rapor.baris.forEach(b => {
    const row = el('div', 'rapor-row');
    row.appendChild(el('span', 'rapor-nama', b.nama));
    row.appendChild(el('span', 'rapor-nilai s-' + b.status, fmtNilai(b)));
    const ket = el('span', 'rapor-ket');
    ket.appendChild(el('b', null, `sehat ${b.sehat} · bahaya ${b.bahaya}. `));
    ket.appendChild(document.createTextNode(b.status === 'bahaya' ? b.alasan : b.arti));
    row.appendChild(ket);
    r.appendChild(row);
  });
  $('#rapor-catatan').textContent =
    (d.rapor.cukup_data ? '' : `Baru ${d.rapor.total_trade} trade selesai. `) + (d.rapor.catatan || '');

  // --- checklist ---
  const cl = $('#checklist-panduan'); cl.innerHTML = '';
  (d.checklist || []).forEach(([q, ket]) => {
    const li = el('li');
    li.appendChild(el('b', null, q));
    li.appendChild(el('span', null, ket));
    cl.appendChild(li);
  });

  // --- fase ---
  const fl = $('#fase-list'); fl.innerHTML = '';
  (d.fase || []).forEach(f => {
    const kini = f.nama === d.rapor.fase_kini;
    const n = el('div', 'fase-item' + (kini ? ' kini' : ''));
    const h = el('h3', null, f.nama);
    if (kini) h.appendChild(el('span', 'badge', `sedang di sini · ${d.rapor.total_trade} trade`));
    n.appendChild(h);
    n.appendChild(el('p', null, f.isi));
    const u = el('p', 'ukuran');
    u.appendChild(el('b', null, 'Ukuran berhasil: '));
    u.appendChild(document.createTextNode(f.ukuran));
    n.appendChild(u);
    fl.appendChild(n);
  });

  // --- playbook ---
  const pl = $('#playbook-list'); pl.innerHTML = '';
  (d.playbook || []).forEach(pb => {
    const c = el('div', 'card');
    const head = el('div', 'card-head');
    head.appendChild(el('h2', null, `Playbook ${pb.kode} — ${pb.nama}`));
    head.appendChild(el('p', 'card-sub', pb.catatan || ''));
    c.appendChild(head);
    const dl = el('dl');
    (pb.baris || []).forEach(([k, v]) => {
      const row = el('div', 'pb-baris');
      row.appendChild(el('dt', null, k));
      row.appendChild(el('dd', null, v));
      dl.appendChild(row);
    });
    c.appendChild(dl);
    if (pb.pelajaran) c.appendChild(el('div', 'pb-pelajaran', pb.pelajaran));
    pl.appendChild(c);
  });

  // --- perusak ---
  const ps = $('#perusak-list'); ps.innerHTML = '';
  (d.perusak || []).forEach((x, i) => {
    const n = el('div', 'perusak-item');
    const h = el('h3');
    h.appendChild(el('span', 'no', String(i + 1)));
    h.appendChild(document.createTextNode(x.judul));
    n.appendChild(h);
    n.appendChild(el('p', null, x.isi));
    if (x.kejadian) n.appendChild(el('p', 'kejadian', x.kejadian));
    ps.appendChild(n);
  });

  // --- ritual ---
  const rl = $('#ritual-list'); rl.innerHTML = '';
  (d.ritual || []).forEach(([judul, ket]) => {
    const li = el('li');
    li.appendChild(el('b', null, judul));
    const s = el('span');
    if (ket.startsWith('python3')) s.appendChild(el('code', null, ket));
    else s.textContent = ket;
    li.appendChild(s);
    rl.appendChild(li);
  });
  $('#ritual-penutup').textContent = d.ritual_penutup || '';
}

/* ================= peta ================= */
async function muatPeta() {
  let d;
  try { d = await ambil('/api/peta'); }
  catch (e) { $('#peta-bagian').innerHTML = `<p class="err">${e.message}</p>`; return; }
  if (d.error) { $('#peta-bagian').innerHTML = `<p class="err">${d.error}</p>`; return; }

  $('#peta-judul').textContent = d.judul || 'Peta Trader Profesional';
  $('#peta-diperbarui').textContent = d.diperbarui || '';
  $('#peta-tesis').textContent = d.tesis || '';

  const wrap = $('#peta-bagian'); wrap.innerHTML = '';
  (d.bagian || []).forEach(bg => {
    const c = el('div', 'card');
    const head = el('div', 'card-head');
    head.appendChild(el('h2', null, bg.judul));
    c.appendChild(head);
    const ol = el('ol', 'rules');
    (bg.baris || []).forEach(([k, v]) => {
      const li = el('li');
      li.appendChild(el('b', null, k));
      li.appendChild(el('span', null, v));
      ol.appendChild(li);
    });
    c.appendChild(ol);
    if (bg.catatan) c.appendChild(el('div', 'note', bg.catatan));
    wrap.appendChild(c);
  });
}

/* ================= kerangka ================= */
let akunCache = null;

async function muatSemua() {
  const dot = $('#status-dot');
  try {
    akunCache = await muatRingkasan();
    dot.className = 'dot ok';
    $('#last-update').textContent = 'diperbarui ' + new Date().toLocaleTimeString('id-ID');
  } catch (e) {
    dot.className = 'dot err';
    $('#last-update').textContent = 'gagal: ' + e.message;
  }
  muatMonitor();
  if (akunCache) muatJurnal(akunCache);
}

$('#tabs').addEventListener('click', (e) => {
  const b = e.target.closest('.tab'); if (!b) return;
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('is-active', x === b));
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('is-active', v.id === 'view-' + b.dataset.view));
  if (b.dataset.view === 'rencana' && !$('#rencana-body').dataset.loaded) {
    $('#rencana-body').dataset.loaded = '1';
    muatRencana('harian');
  }
  if (b.dataset.view === 'trending' && !$('#volspike').dataset.loaded) {
    $('#volspike').dataset.loaded = '1';
    muatTrending();
  }
  if (b.dataset.view === 'panduan' && !$('#rapor').dataset.loaded) {
    $('#rapor').dataset.loaded = '1';
    muatPanduan();
  }
  if (b.dataset.view === 'peta' && !$('#peta-bagian').dataset.loaded) {
    $('#peta-bagian').dataset.loaded = '1';
    muatPeta();
  }
});

$('#horizon-seg').addEventListener('click', (e) => {
  const b = e.target.closest('.seg-btn'); if (!b) return;
  document.querySelectorAll('.seg-btn').forEach(x => x.classList.toggle('is-active', x === b));
  muatRencana(b.dataset.h);
});

$('#refresh').addEventListener('click', muatSemua);
window.addEventListener('resize', () => { if (akunCache) gambarKurva(akunCache.kurva); });

muatSemua();
setInterval(muatSemua, 60000);
