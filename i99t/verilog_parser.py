"""
verilog_parser.py
=================
Parses Yosys Verilog written with:  write_verilog -noexpr -noattr
Flow: read_blif -> synth -> abc -g AND,NAND,OR -> write_verilog

Handles:
  * cell instances  \\$_AND_ _12_ (.A(x), .B(y), .Y(z));
  * plain aliases   assign U34 = _027_;   (resolved so every signal has ONE name)

Returns: inputs, outputs, gates   (same interface as bench_parser.py)
"""

import os
import re
import sys
from collections import Counter

CELL_TYPE_MAP = {
    "$_AND_": "AND",   "$_NAND_": "NAND", "$_OR_": "OR",   "$_NOR_": "NOR",
    "$_NOT_": "NOT",   "$_BUF_": "BUF",   "$_XOR_": "XOR", "$_XNOR_": "XNOR",
    "$_ANDNOT_": "ANDNOT", "$_ORNOT_": "ORNOT", "$_MUX_": "MUX",
    "$_FF_": "DFF",    "$_DFF_P_": "DFF", "$_DFF_N_": "DFF",
}

KNOWN = {   # ground truth from Yosys stat (same flow)
    "b01": {"AND": 10, "NAND": 17, "NOT": 3,  "OR": 7,  "DFF": 5},
    "b10": {"AND": 38, "NAND": 89, "NOT": 13, "OR": 35, "DFF": 17},
}


def parse_verilog(verilog_file):
    with open(verilog_file, "r") as fh:
        text = fh.read()

    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    # ---- ports ---------------------------------------------------------
    inputs, outputs = [], []
    for m in re.finditer(r"\b(input|output)\b\s*(?:\[[^\]]*\]\s*)?([^;]+);", text):
        names = [n.strip() for n in m.group(2).split(",") if n.strip()]
        (inputs if m.group(1) == "input" else outputs).extend(names)

    # ---- aliases (assign a = b;) with union-find -----------------------
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    n_alias = 0
    for m in re.finditer(r"assign\s+(\S+)\s*=\s*([^;]+);", text):
        lhs, rhs = m.group(1), m.group(2).strip()
        if re.fullmatch(r"[A-Za-z_\\][\w$.\\\[\]]*", rhs):
            union(lhs, rhs)
            n_alias += 1
        elif rhs[0].isdigit():
            continue                      # constant tie-off, ignore
        else:
            raise ValueError(
                f"{verilog_file}: found expression 'assign {lhs} = {rhs}'. "
                "Regenerate with: write_verilog -noexpr -noattr")

    # ---- cell instances ------------------------------------------------
    cell_re = re.compile(r"\\?(\$_[A-Z0-9_]+_)\s+(\S+)\s*\(([^;]+)\)\s*;", re.DOTALL)
    raw = []
    for m in cell_re.finditer(text):
        gtype = CELL_TYPE_MAP.get(m.group(1), m.group(1))
        ports = {p.group(1): p.group(2)
                 for p in re.finditer(r"\.(\w+)\s*\(\s*(\S+?)\s*\)", m.group(3))}
        raw.append((gtype, ports))

    # ---- canonical names: each equivalence class keeps its DRIVER ------
    drivers = {}
    for name in inputs:
        drivers.setdefault(find(name), name)
    for gtype, ports in raw:
        out = ports.get("Q") if gtype == "DFF" else ports.get("Y")
        if out:
            drivers.setdefault(find(out), out)

    def canon(x):
        return drivers.get(find(x), x)

    # ---- build gate list -----------------------------------------------
    gates = []
    for gtype, ports in raw:
        if gtype == "DFF":
            gates.append({"gate": canon(ports["Q"]), "type": "DFF",
                          "inputs": [canon(ports["D"])]})
        else:
            ins = [canon(v) for k, v in sorted(ports.items()) if k != "Y"]
            gates.append({"gate": canon(ports["Y"]), "type": gtype, "inputs": ins})

    inputs  = [canon(n) for n in inputs]
    outputs = list(dict.fromkeys(canon(n) for n in outputs))
    return inputs, outputs, gates


def verify(gates, expected, name):
    counts = Counter(g["type"] for g in gates)
    print(f"\n  Verification - {name}")
    print(f"  {'Gate':<8}{'Parser':>8}{'Yosys':>8}  Match")
    ok = True
    for gt, exp in sorted(expected.items()):
        got = counts.get(gt, 0)
        good = got == exp
        ok &= good
        print(f"  {gt:<8}{got:>8}{exp:>8}  {'OK' if good else 'MISMATCH'}")
    extra = {k: v for k, v in counts.items() if k not in expected}
    if extra:
        print(f"  Extra types: {extra}")
        ok = False
    print(f"\n  {'PASS' if ok else 'FAIL'}\n")
    return ok


if __name__ == "__main__":
    DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"
    for c in (sys.argv[1:] or ["b01", "b10"]):
        path = os.path.join(DATASET_PATH, c, f"{c}_mapped.v")
        if not os.path.exists(path):
            print(f"[SKIP] {path} missing")
            continue
        ins, outs, gates = parse_verilog(path)
        print(f"\n{'='*50}\n  {c}: inputs={len(ins)} outputs={len(outs)} gates={len(gates)}")
        print(f"  outputs -> {outs}")
        if c in KNOWN:
            verify(gates, KNOWN[c], c)
        else:
            print(f"  {dict(Counter(g['type'] for g in gates))}")