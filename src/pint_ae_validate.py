#!/usr/bin/env python3
"""PINT AE 1.0.4 (UBL 2.1) Invoice / CreditNote validation:
UBL 2.1 XSD (lxml) + PINT UBL rules + AE jurisdiction rules (Saxon)."""
import sys, json
from pathlib import Path
from lxml import etree
from saxonche import PySaxonProcessor
from common import ARTEFACTS, UBL_XSD, svrl_findings, verdict

ROOT = ARTEFACTS / "pint-ae"
DOCS = {"Invoice": "UBL-Invoice-2.1.xsd", "CreditNote": "UBL-CreditNote-2.1.xsd"}
LAYERS = [("PINT", "PINT-UBL-validation-preprocessed.xslt"), ("AE", "PINT-jurisdiction-aligned-rules.xslt")]
_xsd, _xslt = {}, {}


def validate(path, xp):
    out = {"file": Path(path).name, "validator": "pint-ae-1.0.4", "doctype": None, "customization": None, "xsd": [], "schematron": []}
    try:
        doc = etree.parse(str(path))
    except Exception as e:
        out["xsd"].append({"msg": f"not well-formed: {e}"}); out["valid"] = False; return out
    root = etree.QName(doc.getroot()).localname
    out["doctype"] = root
    out["customization"] = doc.xpath("string(/*/*[local-name()='CustomizationID'])")
    if root not in DOCS:
        out["xsd"].append({"msg": f"unsupported root element '{root}'"}); out["valid"] = False; return out
    name = DOCS[root]
    if name not in _xsd:
        _xsd[name] = etree.XMLSchema(etree.parse(str(UBL_XSD / name)))
    xs = _xsd[name]; xs.validate(doc)
    out["xsd"] = [{"line": e.line, "msg": e.message} for e in xs.error_log]
    for layer, fname in LAYERS:
        if fname not in _xslt:
            _xslt[fname] = xp.compile_stylesheet(stylesheet_file=str(ROOT / fname))
        svrl = _xslt[fname].transform_to_string(source_file=str(Path(path).resolve()))
        for f in svrl_findings(svrl, etree):
            f["layer"] = layer
            out["schematron"].append(f)
    out["valid"] = verdict(out)
    return out


def run(paths):
    with PySaxonProcessor(license=False) as proc:
        xp = proc.new_xslt30_processor()
        return [validate(p, xp) for p in paths]


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1:]), indent=2, ensure_ascii=False))
