"""
verilog_parser.py
=================
Parses Yosys/ABC-mapped Verilog output.
Flow: read_blif → synth → abc -g AND,NAND,OR → write_verilog

Cell names $_AND_, $_NAND_, $_NOT_, $_OR_, $_FF_ map to gate types.

Returns same interface as bench_parser.py:
    inputs, outputs, gates
"""

import re
import os


CELL_TYPE_MAP = {
    "$_AND_"   : "AND",
    "$_NAND_"  : "NAND",
    "$_OR_"    : "OR",
    "$_NOR_"   : "NOR",
    "$_NOT_"   : "NOT",
    "$_BUF_"   : "BUF",
    "$_XOR_"   : "XOR",
    "$_XNOR_"  : "XNOR",
    "$_FF_"    : "DFF",
    "$_DFF_P_" : "DFF",
    "$_DFF_N_" : "DFF",
    "$_ANDNOT_": "ANDNOT",
    "$_ORNOT_" : "ORNOT",
    "$_MUX_"   : "MUX",
}


def parse_verilog(verilog_file):
    """
    Parse Yosys/ABC-mapped Verilog file.

    Returns:
        inputs  : list of primary input signal names
        outputs : list of primary output signal names
        gates   : list of {gate, type, inputs}
    """
    inputs  = []
    outputs = []
    gates   = []

    with open(verilog_file, "r") as fh:
        content = fh.read()

    # Remove single-line and block comments
    content = re.sub(r'//[^\n]*', '', content)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    # Extract input/output declarations
    for m in re.finditer(
        r'\b(input|output)\b\s*(?:\[[^\]]*\]\s*)?([^;]+);',
        content
    ):
        direction = m.group(1)
        names = [n.strip() for n in m.group(2).split(',')]
        for name in names:
            name = name.strip()
            if name:
                if direction == "input":
                    inputs.append(name)
                else:
                    outputs.append(name)

    # Extract cell instantiations
    # Pattern: $_CELLTYPE_ instance_name (.PORT(sig), ...);
    cell_pattern = re.compile(
        r'(\$_[A-Z0-9_]+_)\s+'
        r'(\w+)\s*'
        r'\(([^;]+)\)\s*;',
        re.DOTALL
    )

    for m in cell_pattern.finditer(content):
        cell_type_raw = m.group(1)
        instance_name = m.group(2)
        port_str      = m.group(3)

        gate_type = CELL_TYPE_MAP.get(cell_type_raw, cell_type_raw)

        # Parse .PORT(signal) connections
        port_map = {}
        for pm in re.finditer(r'\.(\w+)\s*\(\s*(\S+?)\s*\)', port_str):
            port_map[pm.group(1)] = pm.group(2)

        # Output signal
        if gate_type == "DFF":
            output_sig  = port_map.get("Q", instance_name)
            gate_inputs = [port_map["D"]] if "D" in port_map else []
        elif gate_type == "MUX":
            output_sig  = port_map.get("Y", instance_name)
            gate_inputs = [port_map.get("A",""),
                           port_map.get("B",""),
                           port_map.get("S","")]
        else:
            output_sig  = port_map.get("Y", instance_name)
            gate_inputs = [v for k, v in sorted(port_map.items())
                           if k != "Y"]

        gates.append({
            "gate"  : output_sig,
            "type"  : gate_type,
            "inputs": [g for g in gate_inputs if g],
        })

    return inputs, outputs, gates


def verify_against_yosys(gates, known_counts, circuit_name=""):
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

    unexpected = {k: v for k, v in counts.items()
                  if k not in known_counts}
    if unexpected:
        print(f"\n  Extra types found: {unexpected}")

    print(f"\n  {'✓ All counts match Yosys stat output.' if all_ok else '✗ Mismatch.'}\n")
    return all_ok


if __name__ == "__main__":
    import sys

    DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

    # Ground truth from Yosys stat after:
    # read_blif → synth -top <circuit>.blif → abc -g AND,NAND,OR
    KNOWN = {
        "b01": {"AND": 10, "NAND": 17, "NOT": 3,  "OR": 7,  "DFF": 5},
        "b10": {"AND": 38, "NAND": 89, "NOT": 13, "OR": 35, "DFF": 17},
    }

    circuits = sys.argv[1:] if len(sys.argv) > 1 else ["b01", "b10"]

    for circuit in circuits:
        verilog = os.path.join(
            DATASET_PATH, circuit, f"{circuit}_mapped.v"
        )

        if not os.path.exists(verilog):
            print(f"[SKIP] {verilog} not found. Run generate_mapped_blifs.py first.")
            continue

        print(f"\n{'='*50}")
        print(f"  Parsing: {verilog}")
        inputs, outputs, gates = parse_verilog(verilog)

        from collections import Counter
        counts = Counter(g["type"] for g in gates)

        print(f"  Inputs : {len(inputs)}")
        print(f"  Outputs: {len(outputs)}")
        print(f"  Gates  : {len(gates)}")
        print(f"  Types  :")
        for gt, cnt in sorted(counts.items()):
            print(f"    {gt:<12}: {cnt}")

        if circuit in KNOWN:
            verify_against_yosys(gates, KNOWN[circuit], circuit)