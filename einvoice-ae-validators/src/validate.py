#!/usr/bin/env python3
"""UAE: validate PINT AE Billing 1.0.4 documents and print one JSON report.

  UBL Invoice / CreditNote with CustomizationID starting 'urn:peppol:pint:billing-1@ae-1' -> PINT AE 1.0.4
Everything else (incl. PINT AE Self-Billing and the Tax Data Document, which this repo does not cover yet)
is reported as unsupported with valid=false, never silently passed.
Usage: python3 src/validate.py FILE [FILE ...]   (exit code 1 if any file is not valid)
"""
import sys, json
from pathlib import Path
from lxml import etree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pint_ae_validate


def sniff(path):
    try:
        root = etree.parse(str(path)).getroot()
    except Exception as e:
        return None, None, f"not well-formed: {e}"
    return etree.QName(root).localname, root.xpath("string(/*/*[local-name()='CustomizationID'])"), None


def main(paths):
    ok, results = [], {}
    for p in paths:
        name, gid, err = sniff(p)
        if not err and name in ("Invoice", "CreditNote") and gid.startswith("urn:peppol:pint:billing-1@ae-1"):
            ok.append(p)
        else:
            results[p] = {"file": Path(p).name, "validator": None, "valid": False, "schematron": [],
                          "xsd": [{"msg": err or f"unsupported document (root={name}, customization='{gid}')"}]}
    for p, res in zip(ok, pint_ae_validate.run(ok)):
        results[p] = res
    ordered = [results[p] for p in paths]
    print(json.dumps(ordered, indent=2, ensure_ascii=False))
    return 0 if all(r.get("valid") for r in ordered) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
