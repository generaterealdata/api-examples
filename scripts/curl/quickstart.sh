#!/usr/bin/env bash
# Generate a dataset with curl: start it, wait for it, download it.
#
#   export GRD_API_KEY=grd_live_...
#   bash quickstart.sh
#
# Needs curl and jq. API reference: https://generaterealdata.com/docs/api/
set -euo pipefail

API="https://generaterealdata.com/api/v1"
AUTH="Authorization: Bearer ${GRD_API_KEY:?Set GRD_API_KEY to your API key first}"

# 1. Start the dataset. The response has its id and a status.
response=$(curl -sS -X POST "$API/datasets" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "mode": "prompt",
    "description": "A veterinary clinic with owners, pets, appointments and invoices",
    "rows": 2000,
    "format": "csv",
    "seed": 7
  }')
id=$(echo "$response" | jq -r '.id // empty')
if [ -z "$id" ]; then
  echo "$response" | jq -r '.error | "\(.code): \(.message)"' >&2
  exit 1
fi

# 2. Check the status every few seconds until it is ready.
status=$(echo "$response" | jq -r '.status')
while [ "$status" != "ready" ] && [ "$status" != "failed" ]; do
  sleep 5
  response=$(curl -sS "$API/datasets/$id" -H "$AUTH")
  status=$(echo "$response" | jq -r '.status')
  echo "  $status" >&2
done
if [ "$status" = "failed" ]; then
  echo "$response" | jq -r '.error.message' >&2
  exit 1
fi

# 3. Download the file. -L follows the redirect to the file itself.
curl -sS -L -o vet_clinic.zip -H "$AUTH" "$API/datasets/$id/download"
echo "$response" | jq '{rows_generated, rows_per_table, schema_id, seed}'
echo "Saved vet_clinic.zip"
