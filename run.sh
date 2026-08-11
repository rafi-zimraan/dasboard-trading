#!/bin/bash
# Nyalakan TradingView (kalau mati), jalankan dashboard, opsional buka tunnel.
#
#   ./run.sh                 lokal saja
#   ./run.sh --tunnel        + URL publik lewat Cloudflare (butuh cloudflared)
#   ./run.sh --lan           + bisa diakses dari HP di wifi yang sama
#   ./run.sh --port 9000     ganti port

set -u
cd "$(dirname "$0")" || exit 1

PORT=8787
for i in "$@"; do
  [ "${PREV:-}" = "--port" ] && PORT="$i"
  PREV="$i"
done

TUNNEL=0
ARGS=()
for a in "$@"; do
  if [ "$a" = "--tunnel" ]; then TUNNEL=1; else ARGS+=("$a"); fi
done

if ! curl -s -m 2 http://127.0.0.1:9222/json/version > /dev/null; then
  echo "TradingView belum jalan dengan CDP — menyalakan..."
  python3 ~/trading-exec/tv_mcp.py call tv_launch '{"port":9222}' > /dev/null 2>&1
fi

if [ "$TUNNEL" = "1" ]; then
  command -v cloudflared > /dev/null || { echo "cloudflared belum terpasang: brew install cloudflared"; exit 1; }
  python3 server.py --port "$PORT" ${ARGS[@]+"${ARGS[@]}"} &
  SRV=$!
  # Tunnel menyambung ke localhost, jadi port tidak perlu terbuka ke jaringan.
  cloudflared tunnel --url "http://127.0.0.1:$PORT" --no-autoupdate > /tmp/cf-dashboard.log 2>&1 &
  CF=$!
  trap 'kill $SRV $CF 2>/dev/null' EXIT INT TERM
  sleep 12
  URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/cf-dashboard.log | head -1)
  TOKEN=$(cat ~/.trading-dashboard-token 2>/dev/null)
  echo
  echo "  URL publik : ${URL:-(gagal — lihat /tmp/cf-dashboard.log)}/?t=$TOKEN"
  echo "  Tanpa token halaman menolak dengan 401. Jangan bagikan tautan ini."
  echo
  wait $SRV
else
  exec python3 server.py --port "$PORT" ${ARGS[@]+"${ARGS[@]}"}
fi
