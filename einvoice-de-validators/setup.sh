#!/usr/bin/env bash
# Installs everything that is NOT committed in this repo. Idempotent. Needs: python3, pip, java, curl, unzip.
set -euo pipefail
cd "$(dirname "$0")"
CACHE=.cache; mkdir -p "$CACHE"

KOSIT_URL=https://github.com/itplr-kosit/validator/releases/download/v1.6.3/validator-1.6.3-standalone.jar
KOSIT_SHA=799e64befca97d4080e03608c80b85dd5a5ecc5f4ae4f35d1116ec2855b9a7c9
CFG_URL=https://github.com/itplr-kosit/validator-configuration-xrechnung/releases/download/v2026-08-31/xrechnung-3.0.2-validator-configuration-2026-08-31.zip
CFG_SHA=2530cd107c414511c5d0462ec10f886910395abfca820db82e83d70bf01221a8

fetch() { # url sha256 dest
  if [ -f "$3" ] && echo "$2  $3" | sha256sum -c --status; then return; fi
  curl -fsSL --retry 3 -o "$3" "$1"
  echo "$2  $3" | sha256sum -c --status || { echo "CHECKSUM MISMATCH for $3" >&2; exit 1; }
}

python3 -c "import saxonche, lxml" 2>/dev/null || pip install --break-system-packages -q "saxonche==13.1.0" lxml
fetch "$KOSIT_URL" "$KOSIT_SHA" "$CACHE/validator-1.6.3-standalone.jar"
fetch "$CFG_URL" "$CFG_SHA" "$CACHE/xrechnung-config.zip"
[ -d "$CACHE/xrechnung-config" ] || { mkdir -p "$CACHE/xrechnung-config"; unzip -q "$CACHE/xrechnung-config.zip" -d "$CACHE/xrechnung-config"; }
sha256sum -c --quiet MANIFEST.sha256 && echo "Artefact checksums OK"
echo "Setup complete. Try: python3 src/validate.py tests/negative/zf_base.xml"
