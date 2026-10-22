#!/usr/bin/env python3
"""Regression tests. Exit code 0 = all pass. Run after ./setup.sh:  python3 tests/run_tests.py"""
import sys, io, json, contextlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import pint_ae_validate, validate as router

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

# 1. Official PINT AE examples: all valid except one known XSD defect in an official credit-note example
res = pint_ae_validate.run(sorted((HERE / "official").glob("*.xml")))
bad = sorted(r["file"] for r in res if not r["valid"])
check(bad == ["Volume-discount-credit-note.xml"], f"{len(res) - len(bad)}/{len(res)} official examples valid; only known-defective one fails: {bad}")

# 2. Negative tests: each mutation must be rejected with the expected rule
exp = {"base.xml": None, "m1_badcustomization.xml": "aligned-ibrp-001-ae", "m2_badpayable.xml": "ibr-co-16",
       "m3_badtaxrate.xml": "ibr-190-ae", "m4_badtypecode.xml": "ibr-cl-01"}
res = {r["file"]: r for r in pint_ae_validate.run([HERE / "negative" / n for n in exp])}
for name, rule in exp.items():
    r = res[name]
    if rule is None: check(r["valid"], f"{name} is valid")
    else: check((not r["valid"]) and any(f["rule"] == rule for f in r["schematron"]), f"{name} rejected with {rule}")

# 3. Router: unsupported documents (e.g. PINT AE Self-Billing, not covered yet) are flagged, never passed
tmp = HERE / "negative" / "_unsupported.xml"
tmp.write_text('<?xml version="1.0"?><Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
               'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
               '<cbc:CustomizationID>urn:peppol:pint:selfbilling-1@ae-1</cbc:CustomizationID></Invoice>')
try:
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        code = router.main([str(tmp)])
    check(code == 1 and json.loads(buf.getvalue())[0]["valid"] is False, "router flags Self-Billing document as unsupported")
finally:
    tmp.unlink()

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
