# e-invoice-validators

Local validation of e-invoice formats used in CTC mandates, built on the **official publisher artefacts**
(no hand-written rules). Current scope:

| Format | Version | Source of artefacts | Engine |
|---|---|---|---|
| ZUGFeRD / Factur-X (CII) – MINIMUM, BASIC WL, BASIC, EN 16931, EXTENDED | ZUGFeRD 2.5.2 = Factur-X 1.09.2 (released 2026-08-04, effective 2026-09-01) | FeRD / FNFE-MPE release package | XSD (lxml) + compiled Schematron XSLT (Saxon) |
| UAE PINT AE Billing (Invoice, Credit Note; UBL 2.1) | 1.0.4 (Final, 2026-06-02) | Peppol UAE `resources.zip` | UBL 2.1 XSD + 2 compiled Schematron layers (PINT + AE) |
| XRechnung (UBL + CII) | 3.0.2 | KoSIT validator 1.6.3 + config release `v2026-08-31` (downloaded by `setup.sh`) | KoSIT validator (Java) |

## Use
```bash
./setup.sh                                   # once per fresh machine/session; installs deps, downloads KoSIT + UBL XSDs, verifies checksums
python3 src/validate.py invoice1.xml ...      # routes each file, prints JSON, exit code 1 if any file is invalid
python3 tests/run_tests.py                   # regression + negative tests
```
Routing is by document type and guideline/customization ID: CII → ZUGFeRD runner; UBL with
`urn:peppol:pint:billing-1@ae-1` → PINT AE; anything containing "xrechnung" → KoSIT.
**Anything else is reported as unsupported (valid=false), never passed silently.**

## Layout
- `artefacts/zugferd/<PROFILE>/` – profile XSD + 3 helper XSDs, compiled Schematron XSLT, `*_codedb.xml` (the XSLT loads it at runtime; keep it next to the XSLT). Original file names are kept because the XSDs import siblings by name.
- `artefacts/pint-ae/` – the two compiled XSLT files. The invoice and credit-note copies in the official zip are byte-identical, so one pair serves both.
- `MANIFEST.sha256` – checksums of every committed artefact (verified by `setup.sh`).
- `tests/` – official sample files (regression) and mutated files (negative tests).
- `.cache/` – created by `setup.sh`, not committed (KoSIT jar, XRechnung config incl. UBL 2.1 XSDs).

## Known findings (2026-10-22)
- 2 FeRD EXTENDED samples (X10, X15) raise warning `BR-FXEXT-E-08rev`; they still pass.
- Official PINT AE example `Volume-discount-credit-note.xml` fails the UBL XSD (`DiscrepancyResponse` placed before `OrderLineReference`); the Schematron does not catch it.
- 3 of FeRD's 4 XRechnung samples are rejected by KoSIT on `CII-SR-465`; the 4th targets XRechnung 2.1 and matches no 3.0.2 scenario.
- The PINT AE `resources.zip` the artefacts came from was named `…-dev.zip`; its release notes say 1.0.4 Final. Confirm against the published release.

## Not covered
PDF/A-3 conformance and embedded-XML checks for ZUGFeRD PDFs; PINT AE Self-Billing and Tax Data Document;
XRechnung extension/CVD scenarios beyond the KoSIT config defaults; registry lookups (TRN/TIN, Peppol
participant) and platform-side rules (FTA/ASP, SdI, DGFiP/PDP); France-specific flows and Italy FatturaPA (not yet added).

## Updating a spec version
Replace the files in `artefacts/<spec>/`, run `find artefacts -type f | sort | xargs sha256sum > MANIFEST.sha256`,
update the pins in `setup.sh` if KoSIT changes, rerun `tests/run_tests.py`, tag the commit.

## Licences
Artefacts and sample files are redistributed unchanged from FeRD/FNFE-MPE, OpenPeppol/UAE Peppol Authority.
Check their licence terms before publishing this repository publicly.
