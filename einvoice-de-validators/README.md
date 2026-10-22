# einvoice-de-validators

Local validation of German e-invoice formats using the **official publisher artefacts** (no hand-written rules).

| Format | Version | Artefacts from | Engine |
|---|---|---|---|
| ZUGFeRD / Factur-X (CII) – MINIMUM, BASIC WL, BASIC, EN 16931, EXTENDED | ZUGFeRD 2.5.2 = Factur-X 1.09.2 (released 2026-08-04, effective 2026-09-01) | FeRD / FNFE-MPE release package (committed in `artefacts/`) | profile XSD (lxml) + compiled Schematron XSLT (Saxon) |
| XRechnung (UBL + CII) | 3.0.2 | KoSIT validator 1.6.3 + config release `v2026-08-31` (downloaded by `setup.sh`) | KoSIT validator (Java) |

## Use
```bash
./setup.sh                                   # once per fresh machine/session; needs python3, pip, java, curl, unzip
python3 src/validate.py invoice1.xml ...      # routes each file, prints JSON, exit code 1 if any file is invalid
python3 tests/run_tests.py                   # regression + negative tests
```
Routing: CII with an XRechnung guideline → KoSIT; other CII → ZUGFeRD runner by profile; UBL with an XRechnung
customization → KoSIT. **Anything else (e.g. UAE PINT AE) is reported as unsupported (valid=false), never passed silently.**

## Layout
- `artefacts/zugferd/<PROFILE>/` – profile XSD + 3 helper XSDs, compiled Schematron XSLT, `*_codedb.xml` (loaded by the XSLT at runtime; keep next to it). Original file names are kept because the XSDs import siblings by name.
- `MANIFEST.sha256` – checksums of every committed artefact (verified by `setup.sh`).
- `tests/` – official FeRD samples (regression), mutated files (negative tests), one XRechnung sample.
- `.cache/` – created by `setup.sh`, not committed (KoSIT jar, XRechnung config incl. UBL 2.1 XSDs).

## Known findings (2026-10-22)
- 2 FeRD EXTENDED samples (X10, X15) raise warning `BR-FXEXT-E-08rev`; they still pass.
- 3 of FeRD's 4 XRechnung samples are rejected by KoSIT on `CII-SR-465` (KoSIT labels the message "warning" but still rejects); the 4th targets XRechnung 2.1 and matches no 3.0.2 scenario.

## Not covered
PDF/A-3 conformance and embedded-XML checks for ZUGFeRD PDFs; XRechnung extension/CVD scenarios beyond the KoSIT config defaults;
platform-side rules and registry lookups; the unified spec's non-XML requirements.

## Updating a spec version
Replace files in `artefacts/zugferd/`, regenerate `MANIFEST.sha256` (`find artefacts -type f | sort | xargs sha256sum > MANIFEST.sha256`),
update pins in `setup.sh` if KoSIT changes, rerun `tests/run_tests.py`, tag the commit.

## Licences
Artefacts and samples are redistributed unchanged from FeRD / FNFE-MPE. Check their licence terms before publishing this repository publicly.
