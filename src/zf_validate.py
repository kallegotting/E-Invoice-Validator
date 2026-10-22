#!/usr/bin/env python3
"""ZUGFeRD 2.5.2 / Factur-X 1.09.2 CII validation: profile XSD (lxml) + profile Schematron XSLT (Saxon)."""
import sys, json
from pathlib import Path
from lxml import etree
from saxonche import PySaxonProcessor
from common import ARTEFACTS, svrl_findings, verdict

ROOT = ARTEFACTS / "zugferd"
NS = {"rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
      "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"}
# guideline-id (suffix) -> profile folder. Longest suffix wins so 'basicwl' is not matched as 'basic'.
PROFILES = {
    "urn:factur-x.eu:1p0:minimum": "MINIMUM",
    "urn:factur-x.eu:1p0:basicwl": "BASICWL",
    "urn:factur-x.eu:1p0:basic": "BASIC",
    "urn:cen.eu:en16931:2017": "EN16931",
    "urn:factur-x.eu:1p0:extended": "EXTENDED",
}
_xsd, _xslt = {}, {}


def pick_profile(gid):
    for key in sorted(PROFILES, key=len, reverse=True):
        if gid == key or gid.endswith(key):
            return key, PROFILES[key]
    return None, None


def validate(path, xp):
    out = {"file": str(path).split("/")[-1], "validator": "zugferd-2.5.2", "profile": None, "xsd": [], "schematron": []}
    try:
        doc = etree.parse(str(path))
    except Exception as e:
        out["xsd"].append({"msg": f"not well-formed: {e}"}); out["valid"] = False; return out
    gid = doc.xpath("string(//rsm:ExchangedDocumentContext/ram:GuidelineSpecifiedDocumentContextParameter/ram:ID)", namespaces=NS)
    key, prof = pick_profile(gid)
    out["profile"] = prof or f"UNKNOWN ({gid})"
    if not prof:
        out["xsd"].append({"msg": f"no profile mapping for guideline '{gid}'"}); out["valid"] = False; return out
    d = ROOT / prof
    if prof not in _xsd:
        _xsd[prof] = etree.XMLSchema(etree.parse(str(d / f"Factur-X_1.09.2_{prof}.xsd")))
    xs = _xsd[prof]; xs.validate(doc)
    out["xsd"] = [{"line": e.line, "msg": e.message} for e in xs.error_log]
    if prof not in _xslt:
        _xslt[prof] = xp.compile_stylesheet(stylesheet_file=str(d / f"FACTUR-X_{'BASIC-WL' if prof == 'BASICWL' else prof}.xslt"))
    svrl = _xslt[prof].transform_to_string(source_file=str(Path(path).resolve()))
    out["schematron"] = svrl_findings(svrl, etree)
    out["valid"] = verdict(out)
    return out


def run(paths):
    with PySaxonProcessor(license=False) as proc:
        xp = proc.new_xslt30_processor()
        return [validate(p, xp) for p in paths]


if __name__ == "__main__":
    from pathlib import Path
    print(json.dumps(run(sys.argv[1:]), indent=2, ensure_ascii=False))
