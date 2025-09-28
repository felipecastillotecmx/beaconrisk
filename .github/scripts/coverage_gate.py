#!/usr/bin/env python3
import sys, xml.etree.ElementTree as ET, os
threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 80.0
path = sys.argv[2] if len(sys.argv) > 2 else "coverage.xml"
if not os.path.exists(path):
    print(f"[coverage-gate] Archivo no encontrado: {path}", file=sys.stderr); sys.exit(2)
tree = ET.parse(path); root = tree.getroot()
# Soportar formatos: coverage.py (root tag 'coverage' con attributes), cobertura (line-rate)
line_rate = None
if root.tag == "coverage" and "line-rate" in root.attrib:
    line_rate = float(root.attrib["line-rate"]) * 100.0
else:
    # Fallback: sumar totales
    covered = 0; valid = 0
    for pkg in root.findall(".//classes/class/lines/line"):
        valid += 1
        hits = int(pkg.attrib.get("hits", "0"))
        if hits > 0: covered += 1
    line_rate = (covered/valid * 100.0) if valid else 0.0
print(f"[coverage-gate] Cobertura = {line_rate:.2f}% (umbral {threshold:.2f}%)")
if line_rate + 1e-9 < threshold:
    print("[coverage-gate] Fallo: cobertura por debajo del umbral.", file=sys.stderr)
    sys.exit(1)
print("[coverage-gate] OK")
