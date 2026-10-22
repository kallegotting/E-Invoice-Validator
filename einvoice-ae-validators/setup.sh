#!/usr/bin/env bash
# Installs everything that is NOT committed in this repo. Idempotent. Needs: python3, pip, curl, unzip. (No Java.)
set -euo pipefail
cd "$(dirname "$0")"
CACHE=.cache; mkdir -p "$CACHE"

# PINT AE needs the OASIS UBL 2.1 XSDs, which the Peppol resources zip does not contain.
# They are taken from the (pinned) KoSIT XRechnung config release.
CFG_URL=https://github.com/itplr-kosit/validator-configuration-xrechnung/releases/download/v2026-08-31/xrechnung-3.0.2-validator-configuration-2026-08-31.zip
CFG_SHA=2530cd107c414511c5d0462ec10f886910395abfca820db82e83d70bf01221a8

if ! { [ -f "$CACHE/ubl-source.zip" ] && echo "$CFG_SHA  $CACHE/ubl-source.zip" | sha256sum -c --status; }; then
  curl -fsSL --retry 3 -o "$CACHE/ubl-source.zip" "$CFG_URL"
  echo "$CFG_SHA  $CACHE/ubl-source.zip" | sha256sum -c --status || { echo "CHECKSUM MISMATCH for ubl-source.zip" >&2; exit 1; }
fi
[ -d "$CACHE/ubl/resources/ubl/2.1/xsd/maindoc" ] || { mkdir -p "$CACHE/ubl"; unzip -q -o "$CACHE/ubl-source.zip" 'resources/ubl/2.1/xsd/*' -d "$CACHE/ubl"; }
python3 -c "import saxonche, lxml" 2>/dev/null || pip install --break-system-packages -q "saxonche==13.1.0" lxml
sha256sum -c --quiet MANIFEST.sha256 && echo "Artefact checksums OK"
echo "Setup complete. Try: python3 src/validate.py tests/negative/base.xml"
