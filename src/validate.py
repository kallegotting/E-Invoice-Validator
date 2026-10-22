#!/usr/bin/env python3
"""Route each file to the right validator and print one JSON report.

  CII  + Factur-X/ZUGFeRD/EN16931 guideline  -> zf_validate   (ZUGFeRD 2.5.2 / Factur-X 1.09.2)
  UBL  + urn:peppol:pint:billing-1@ae-1      -> pint_ae_validate (PINT AE 1.0.4)
  CII/UBL + XRechnung guideline              -> KoSIT validator (XRechnung 3.0.2 config)
Everything else is reported as unsupported, never silently passed.
Usage: python3 src/validate.py FILE [FILE ...]   (exit code 1 if any file is not valid)
"""
import sys, json, subprocess, tempfile
from pathlib import Path
from lxml import etree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common, zf_validate, pint_ae_validate

REP = {"rep": "http://www.xoev.de/de/validator/varl/1"}


def sniff(path):
    try:
        root = etree.parse(str(path)).getroot()
    except Exception as e:
        return None, None, f"not well-formed: {e}"
    name = etree.QName(root).localname
    if name == "CrossIndustryInvoice":
        gid = root.xpath("string(//*[local-name()='GuidelineSpecifiedDocumentContextParameter']/*[local-name()='ID'])")
    else:
        gid = root.xpath("string(/*/*[local-name()='CustomizationID'])")
    return name, gid, None


def route(name, gid):
    g = gid.lower()
    if "xrechnung" in g:
        return "kosit"
    if name == "CrossIndustryInvoice":
        return "zf"
    if name in ("Invoice", "CreditNote") and gid.startswith("urn:peppol:pint:billing-1@ae-1"):
        return "pint-ae"
    return None


def kosit(path):
    out = {"file": Path(path).name, "validator": "kosit-xrechnung-3.0.2 (config v2026-08-31, validator 1.6.3)", "xsd": [], "schematron": []}
    if not common.KOSIT_JAR.exists():
        out.update(valid=False, error="KoSIT validator not installed; run ./setup.sh"); return out
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["java", "-jar", str(common.KOSIT_JAR), "-s", str(common.KOSIT_CONFIG / "scenarios.xml"),
                        "-r", str(common.KOSIT_CONFIG), "-o", td, str(path)], capture_output=True, text=True)
        reports = list(Path(td).glob("*-report.xml"))
        if not reports:
            out.update(valid=False, error="KoSIT produced no report (no matching scenario for this document?)"); return out
        rep = etree.parse(str(reports[0]))
    out["accepted"] = bool(rep.xpath("boolean(//rep:assessment/rep:accept)", namespaces=REP))
    out["scenario"] = rep.xpath("string(//rep:scenarioMatched/*[local-name()='scenario']/*[local-name()='name'])", namespaces=REP) or None
    for step in rep.xpath("//rep:validationStepResult", namespaces=REP):
        for m in step.xpath("rep:message", namespaces=REP):
            item = {"rule": m.get("code"), "severity": m.get("level"), "location": m.get("xpathLocation"), "msg": " ".join((m.text or "").split())}
            (out["xsd"] if step.get("id") == "val-xsd" else out["schematron"]).append(item)
    out["valid"] = out["accepted"]   # KoSIT's own accept/reject is authoritative (it applies custom severity levels)
    return out


def main(paths):
    results, groups = {}, {"zf": [], "pint-ae": []}
    for p in paths:
        name, gid, err = sniff(p)
        r = route(name, gid) if not err else None
        if err or r is None:
            results[p] = {"file": Path(p).name, "validator": None, "valid": False,
                          "xsd": [{"msg": err or f"unsupported document (root={name}, guideline='{gid}')"}], "schematron": []}
        elif r == "kosit":
            results[p] = kosit(p)
        else:
            groups[r].append(p)
    for p, res in zip(groups["zf"], zf_validate.run(groups["zf"])): results[p] = res
    for p, res in zip(groups["pint-ae"], pint_ae_validate.run(groups["pint-ae"])): results[p] = res
    ordered = [results[p] for p in paths]
    print(json.dumps(ordered, indent=2, ensure_ascii=False))
    return 0 if all(r.get("valid") for r in ordered) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
