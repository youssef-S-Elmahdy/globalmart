#!/usr/bin/env bash
# Recreate the Grafana PostgreSQL datasource and set it as default.
# Assumes Grafana reachable at http://localhost:3001 with admin/admin123 (docker-compose defaults).

set -euo pipefail

GRAFANA_URL=${GRAFANA_URL:-http://localhost:3001}
GRAFANA_USER=${GRAFANA_USER:-admin}
GRAFANA_PASS=${GRAFANA_PASS:-admin123}

payload=$(cat <<'JSON'
{
  "name": "PostgreSQL",
  "type": "postgres",
  "access": "proxy",
  "url": "globalmart-postgres:5432",
  "database": "globalmart",
  "user": "globalmart",
  "isDefault": true,
  "jsonData": {
    "sslmode": "disable",
    "postgresVersion": 1600
  },
  "secureJsonData": {
    "password": "globalmart123"
  }
}
JSON
)

echo "Creating/updating Grafana datasource 'PostgreSQL'..."
curl -sS -X POST "${GRAFANA_URL}/api/datasources" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -H "Content-Type: application/json" \
  -d "${payload}"
echo
