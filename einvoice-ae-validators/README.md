# einvoice-ae-validators

Local validation of UAE e-invoices (PINT AE) using the **official Peppol UAE artefacts** (no hand-written rules).

| Format | Version | Artefacts from | Engine |
|---|---|---|---|
| PINT AE Billing – Invoice and Credit Note (UBL 2.1) | 1.0.4 (Final, 2026-06-02) | Peppol UAE `resources.zip` (compiled Schematron committed in `artefacts/`) | UBL 2.1 XSD (lxml) + 2 Schematron layers: PINT rules and AE jurisdiction rules (Saxon) |

## Use
```bash
./setup.sh                                   # once per fresh machine/session; needs python3, pip, curl, unzip (no Java)
python3 src/validate.py invoice1.xml ...      # prints JSON, exit code 1 if any file is invalid
python3 tests/run_tests.py                   # regression + negative tests
```
Only UBL Invoice/CreditNote with CustomizationID starting `urn:peppol:pint:billing-1@ae-1` is validated.
**Anything else (incl. Self-Billing and the Tax Data Document) is reported as unsupported (valid=false), never passed silently.**

## Layout
- `artefacts/pint-ae/` – `PINT-UBL-validation-preprocessed.xslt` and `PINT-jurisdiction-aligned-rules.xslt`. The invoice and credit-note copies in the official zip are byte-identical, so one pair serves both.
- `MANIFEST.sha256` – checksums of the committed artefacts (verified by `setup.sh`).
- `tests/official/` – the 30 official Peppol UAE example documents; `tests/negative/` – one valid base file and four mutated copies.
- `.cache/` – created by `setup.sh`, not committed: the OASIS UBL 2.1 XSDs, which the Peppol zip does not contain. They are extracted from the pinned KoSIT XRechnung config release (checksum-verified).

## Known findings (2026-10-22)
- Official example `Volume-discount-credit-note.xml` fails the UBL XSD (`DiscrepancyResponse` placed before `OrderLineReference`); the Schematron does not catch it.
- The `resources.zip` these artefacts came from was named `…-dev.zip`; its release notes say 1.0.4 Final. Confirm against the published release.

## Not covered
PINT AE Self-Billing and Tax Data Document (separate 1.0.4 specs, resources not yet added); TRN/TIN and Peppol participant registry lookups;
FTA / accredited-service-provider checks beyond the published specification.

## Updating a spec version
Replace the XSLT files, regenerate `MANIFEST.sha256`, rerun `tests/run_tests.py`, tag the commit.

## Licences
Artefacts and examples are redistributed unchanged from OpenPeppol / the UAE Peppol Authority. Check their licence terms before publishing this repository publicly.
