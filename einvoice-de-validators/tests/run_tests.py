#!/usr/bin/env python3
"""Regression tests. Exit code 0 = all pass. Run after ./setup.sh:  python3 tests/run_tests.py"""
import sys, io, json, contextlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import zf_validate, validate as router

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

# 1. FeRD ZUGFeRD/Factur-X sample XMLs: all must validate (two EXTENDED samples carry a known warning)
res = zf_validate.run(sorted((HERE / "zugferd").rglob("*.xml")))
bad = [r["file"] for r in res if not r["valid"]]
check(not bad, f"ZUGFeRD/Factur-X samples valid: {len(res) - len(bad)}/{len(res)} {bad}")
warn = sorted(r["file"] for r in res if r["schematron"] and r["valid"])
check(warn == ["X10_01_Kleinunternehmer_ohneUStId.xml", "X15_01_steuerfreie_Innergemeinschaftliche_Lieferung.xml"],
      f"known BR-FXEXT-E-08rev warnings unchanged: {warn}")

# 2. Negative tests (EN 16931 profile)
zexp = {"zf_base.xml": None, "zf_m1_badgrand.xml": "BR-CO-15", "zf_m2_badunit.xml": "FX-SCH-A-000613", "zf_m3_badguideline.xml": "XSD"}
zres = {r["file"]: r for r in zf_validate.run([HERE / "negative" / n for n in zexp])}
for name, rule in zexp.items():
    r = zres[name]
    if rule is None: check(r["valid"], f"{name} is valid")
    elif rule == "XSD": check((not r["valid"]) and r["xsd"], f"{name} rejected (unknown guideline)")
    else: check((not r["valid"]) and any(f["rule"] == rule for f in r["schematron"]), f"{name} rejected with {rule}")

# 3. XRechnung via KoSIT. KNOWN FINDING: FeRD's own XRechnung 3.0 sample is rejected on CII-SR-465.
with contextlib.redirect_stdout(io.StringIO()) as buf:
    code = router.main([str(HERE / "xrechnung" / "XRECHNUNG_Einfach.xml")])
r = json.loads(buf.getvalue())[0]
check(r["validator"].startswith("kosit") and r["valid"] is False and any(f["rule"] == "CII-SR-465" for f in r["schematron"]),
      "XRechnung sample routed to KoSIT and rejected on CII-SR-465 (known finding)")

# 4. Router: unsupported documents (incl. UAE PINT AE, which lives in the UAE repo) must be flagged, never passed
tmp = HERE / "negative" / "_unsupported.xml"
tmp.write_text('<?xml version="1.0"?><Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
               'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
               '<cbc:CustomizationID>urn:peppol:pint:billing-1@ae-1</cbc:CustomizationID></Invoice>')
try:
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        code = router.main([str(tmp)])
    check(code == 1 and json.loads(buf.getvalue())[0]["valid"] is False, "router flags PINT AE document as unsupported here")
finally:
    tmp.unlink()

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
