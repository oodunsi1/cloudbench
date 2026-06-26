#!/usr/bin/env bash
# Verify the deployed static site serves the marker. The system-under-test provisions the hosting and
# sets SITE_URL to the public endpoint (S3 website URL or CloudFront domain).
set -euo pipefail
: "${SITE_URL:?Set SITE_URL to the provisioned static-site endpoint}"
echo "Checking $SITE_URL ..."
body="$(curl -fsSL "$SITE_URL")"
if echo "$body" | grep -q "CLOUDBENCH_STATIC_OK"; then
  echo "static site OK: marker served at $SITE_URL"
else
  echo "FAIL: marker not found at $SITE_URL" >&2
  exit 1
fi
