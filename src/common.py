"""Shared paths and helpers."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARTEFACTS = REPO / "artefacts"
CACHE = REPO / ".cache"                       # populated by setup.sh (not committed)
KOSIT_JAR = CACHE / "validator-1.6.3-standalone.jar"
KOSIT_CONFIG = CACHE / "xrechnung-config"      # XRechnung 3.0.2 config, release v2026-08-31
UBL_XSD = KOSIT_CONFIG / "resources" / "ubl" / "2.1" / "xsd" / "maindoc"

SVRL_NS = {"svrl": "http://purl.oclc.org/dsdl/svrl"}


def svrl_findings(svrl_text, etree):
    """Extract failed asserts / successful reports from an SVRL document."""
    sv = etree.fromstring(svrl_text.encode())
    out = []
    for el in sv.xpath("//svrl:failed-assert | //svrl:successful-report", namespaces=SVRL_NS):
        out.append({
            "rule": el.get("id"),
            "severity": el.get("flag") or "error",
            "location": el.get("location"),
            "msg": " ".join(el.xpath("string(svrl:text)", namespaces=SVRL_NS).split()),
        })
    return out


def verdict(result):
    """True if there are no XSD errors and no Schematron findings of severity error/fatal."""
    if result.get("xsd"):
        return False
    return not any(f.get("severity") in ("error", "fatal") for f in result.get("schematron", []))
