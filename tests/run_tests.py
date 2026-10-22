#!/usr/bin/env python3
"""Regression tests. Exit code 0 = all pass. Run after ./setup.sh:  python3 tests/run_tests.py"""
import sys, io, json, contextlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import zf_validate, pint_ae_validate, validate as router

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

# 1. FeRD ZUGFeRD/Factur-X sample XMLs: all must validate (two EXTENDED samples carry a known warning)
zf = sorted((HERE / "zugferd").rglob("*.xml"))
res = zf_validate.run(zf)
bad = [r["file"] for r in res if not r["valid"]]
check(not bad, f"ZUGFeRD/Factur-X samples valid: {len(res) - len(bad)}/{len(res)} {bad}")
warn = sorted(r["file"] for r in res if r["schematron"] and r["valid"])
check(warn == ["X10_01_Kleinunternehmer_ohneUStId.xml", "X15_01_steuerfreie_Innergemeinschaftliche_Lieferung.xml"],
      f"known BR-FXEXT-E-08rev warnings unchanged: {warn}")

# 2. Official PINT AE examples: 29 valid; one official credit-note example has a known XSD element-order defect
pa = sorted((HERE / "pint-ae").glob("*.xml"))
res = pint_ae_validate.run(pa)
bad = sorted(r["file"] for r in res if not r["valid"])
check(bad == ["Volume-discount-credit-note.xml"], f"PINT AE examples: only known-defective example fails: {bad}")

# 3. Negative tests: each mutation must be rejected with the expected rule
exp = {"base.xml": None, "m1_badcustomization.xml": "aligned-ibrp-001-ae", "m2_badpayable.xml": "ibr-co-16",
       "m3_badtaxrate.xml": "ibr-190-ae", "m4_badtypecode.xml": "ibr-cl-01"}
res = {r["file"]: r for r in pint_ae_validate.run([HERE / "negative" / n for n in exp])}
for name, rule in exp.items():
    r = res[name]
    if rule is None: check(r["valid"], f"{name} is valid")
    else: check((not r["valid"]) and any(f["rule"] == rule for f in r["schematron"]), f"{name} rejected with {rule}")

# 3b. Negative tests for ZUGFeRD/Factur-X (EN 16931 profile)
zexp = {"zf_base.xml": None, "zf_m1_badgrand.xml": "BR-CO-15", "zf_m2_badunit.xml": "FX-SCH-A-000613", "zf_m3_badguideline.xml": "XSD"}
zres = {r["file"]: r for r in zf_validate.run([HERE / "negative" / n for n in zexp])}
for name, rule in zexp.items():
    r = zres[name]
    if rule is None: check(r["valid"], f"{name} is valid")
    elif rule == "XSD": check((not r["valid"]) and r["xsd"], f"{name} rejected (unknown guideline)")
    else: check((not r["valid"]) and any(f["rule"] == rule for f in r["schematron"]), f"{name} rejected with {rule}")

# 4. Router: unsupported documents must be flagged, never silently passed
tmp = HERE / "negative" / "_unsupported.xml"
tmp.write_text('<?xml version="1.0"?><Foo xmlns="urn:x"/>')
try:
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        code = router.main([str(tmp)])
    check(code == 1 and json.loads(buf.getvalue())[0]["valid"] is False, "router flags unsupported document")
finally:
    tmp.unlink()

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
