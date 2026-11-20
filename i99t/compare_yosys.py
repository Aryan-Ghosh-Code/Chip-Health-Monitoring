import os
import sys
import json
from collections import Counter
from verilog_parser import parse_verilog

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"


def compare(circuit):
    folder    = os.path.join(DATASET_PATH, circuit)
    json_path = os.path.join(folder, f"{circuit}_yosys_stat.json")
    v_path    = os.path.join(folder, f"{circuit}_mapped.v")

    if not (os.path.exists(json_path) and os.path.exists(v_path)):
        print(f"\n  {circuit}: files missing, run generate_mapped_blifs.py first")
        return False

    with open(json_path) as fh:
        ref = json.load(fh)

    _, _, gates = parse_verilog(v_path)
    got = Counter(g["type"] for g in gates)

    print(f"\n{'='*46}\n  {circuit}")
    print(f"  {'Gate':<8}{'Parser':>8}{'Yosys':>8}  Match")
    ok = True
    for gt in sorted(set(ref["counts"]) | set(got)):
        a, b = got.get(gt, 0), ref["counts"].get(gt, 0)
        good = a == b
        ok &= good
        print(f"  {gt:<8}{a:>8}{b:>8}  {'OK' if good else 'MISMATCH'}")

    total_ok = sum(got.values()) == ref["total_cells"]
    ok &= total_ok
    print(f"  {'TOTAL':<8}{sum(got.values()):>8}{ref['total_cells']:>8}  "
          f"{'OK' if total_ok else 'MISMATCH'}")
    return ok


if __name__ == "__main__":
    circuits = sys.argv[1:] or ["b01", "b10"]
    results = {c: compare(c) for c in circuits}
    bad = [c for c, v in results.items() if not v]
    print(f"\n  {'ALL PASS' if not bad else 'FAILURES: ' + str(bad)}")