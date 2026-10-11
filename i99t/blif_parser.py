"""
blif_parser.py
==============
Parses a Yosys/ABC-mapped BLIF file and infers gate types from truth tables.
Replaces bench_parser.py in the pipeline.

Returns same interface as bench_parser.py:
    inputs  : list of primary input signal names
    outputs : list of primary output signal names
    gates   : list of dicts {gate, type, inputs}
"""

import re


def infer_gate_type(n_inputs, cover_rows):
    input_pats = [row.split()[0] for row in cover_rows if row.strip()]

    if n_inputs == 0:
        return "CONST1" if input_pats else "CONST0"

    if n_inputs == 1:
        if input_pats == ["0"]:
            return "NOT"
        if input_pats == ["1"]:
            return "BUF"
        return "UNKNOWN_1IN"

    n_rows   = len(input_pats)
    max_rows = (2 ** n_inputs) - 1

    if n_rows == 1:
        pat = input_pats[0]
        if all(c == "1" for c in pat):
            return "AND"
        if all(c == "0" for c in pat):
            return "NOR"
        if n_inputs == 2:
            if set(input_pats) == {"01", "10"}:
                return "XOR"
            if set(input_pats) == {"00", "11"}:
                return "XNOR"
        return f"UNKNOWN_1ROW_{n_inputs}IN"

    if n_rows == max_rows:
        all_ones  = "1" * n_inputs
        all_zeros = "0" * n_inputs
        if all_ones not in input_pats:
            return "NAND"
        if all_zeros not in input_pats:
            return "OR"
        return f"UNKNOWN_{n_rows}ROWS_{n_inputs}IN"

    if n_inputs == 2:
        pat_set = set(input_pats)
        if pat_set == {"01", "10"}:
            return "XOR"
        if pat_set == {"00", "11"}:
            return "XNOR"

    return f"UNKNOWN_{n_rows}ROWS_{n_inputs}IN"


def parse_blif(blif_file):
    inputs  = []
    outputs = []
    gates   = []

    SKIP_SIGNALS = {"$false", "$true", "$undef"}

    with open(blif_file, "r") as fh:
        content = fh.read()

    content = re.sub(r"\\\s*\n\s*", " ", content)
    lines   = content.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or line.startswith("#"):
            i += 1
            continue

        if line.startswith(".inputs"):
            tokens = line.split()[1:]
            inputs.extend(t for t in tokens if t not in SKIP_SIGNALS)

        elif line.startswith(".outputs"):
            tokens = line.split()[1:]
            outputs.extend(t for t in tokens if t not in SKIP_SIGNALS)

        elif line.startswith(".latch"):
            parts = line.split()
            if len(parts) >= 3:
                d_input  = parts[1]
                q_output = parts[2]
                if q_output not in SKIP_SIGNALS:
                    gates.append({
                        "gate"  : q_output,
                        "type"  : "DFF",
                        "inputs": [d_input],
                    })

        elif line.startswith(".names"):
            tokens      = line.split()[1:]
            output_sig  = tokens[-1]
            gate_inputs = [t for t in tokens[:-1]
                           if t not in SKIP_SIGNALS]

            cover_rows = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt or nxt.startswith(".") or nxt.startswith("#"):
                    break
                cover_rows.append(nxt)
                j += 1

            if output_sig in SKIP_SIGNALS:
                i = j
                continue

            gate_type = infer_gate_type(len(gate_inputs), cover_rows)

            gates.append({
                "gate"  : output_sig,
                "type"  : gate_type,
                "inputs": gate_inputs,
            })

            i = j
            continue

        i += 1

    return inputs, outputs, gates


def verify_against_abc(gates, known_counts, circuit_name=""):
    from collections import Counter
    counts = Counter(g["type"] for g in gates)

    print(f"\n  Verification — {circuit_name}")
    print(f"  {'Gate':<12} {'Extracted':>10} {'Expected':>10} {'Match':>8}")
    print(f"  {'─'*44}")

    all_ok = True
    for gt, exp in sorted(known_counts.items()):
        ext   = counts.get(gt, 0)
        match = "✓" if ext == exp else "✗"
        if match == "✗":
            all_ok = False
        print(f"  {gt:<12} {ext:>10} {exp:>10} {match:>8}")

    unknown = {k: v for k, v in counts.items() if k.startswith("UNKNOWN")}
    if unknown:
        print(f"  ⚠ Unknown types: {unknown}")
        all_ok = False

    if all_ok:
        print(f"\n  ✓ All counts match ABC output.\n")
    else:
        print(f"\n  ✗ Mismatch. See above.\n")

    return all_ok


if __name__ == "__main__":
    import sys
    import os

    DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

    KNOWN = {
        "b01": {"AND": 8,  "NAND": 20, "NOT": 4,  "OR": 8,  "DFF": 5},
        "b10": {"AND": 42, "NAND": 90, "NOT": 10, "OR": 35, "DFF": 17},
    }

    circuits = sys.argv[1:] if len(sys.argv) > 1 else ["b01", "b10"]

    for circuit in circuits:
        blif = os.path.join(DATASET_PATH, circuit, f"{circuit}_mapped.blif")

        if not os.path.exists(blif):
            print(f"[SKIP] {blif} not found. Run generate_mapped_blifs.py first.")
            continue

        print(f"\n{'='*50}")
        print(f"  Parsing: {blif}")
        inputs, outputs, gates = parse_blif(blif)

        print(f"  Primary inputs : {len(inputs)}")
        print(f"  Primary outputs: {len(outputs)}")
        print(f"  Total gates    : {len(gates)}")

        from collections import Counter
        counts = Counter(g["type"] for g in gates)
        print(f"  Gate types:")
        for gt, cnt in sorted(counts.items()):
            print(f"    {gt:<12}: {cnt}")

        if circuit in KNOWN:
            verify_against_abc(gates, KNOWN[circuit], circuit)