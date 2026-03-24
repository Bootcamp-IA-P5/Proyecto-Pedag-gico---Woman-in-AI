#!/bin/sh
set -eu

cat > /usr/share/nginx/html/env.js <<EOF
window.__VERTICE_ENV = {
  VITE_API_BASE_URL: "${VITE_API_BASE_URL:-}",
  VITE_SUPABASE_URL: "${VITE_SUPABASE_URL:-}",
  VITE_SUPABASE_ANON_KEY: "${VITE_SUPABASE_ANON_KEY:-}"
};
EOF
