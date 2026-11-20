import os
import re
import sys
import json
import subprocess

YOSYS_BAT    = r"E:\Projects\ChipHealthAnalysis\i99t\run_yosys.bat"
DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

ALL_CIRCUITS = [
    "b01", "b02", "b03", "b04", "b05", "b06", "b07", "b08",
    "b09", "b10", "b11", "b12", "b13", "b14", "b15",
    "b17", "b20", "b21", "b22"
]

WRITE_CMD = "write_verilog -noexpr -noattr"

NAME_MAP = {
    "$_AND_": "AND", "$_NAND_": "NAND", "$_OR_": "OR", "$_NOR_": "NOR",
    "$_NOT_": "NOT", "$_XOR_": "XOR", "$_XNOR_": "XNOR",
    "$_ANDNOT_": "ANDNOT", "$_ORNOT_": "ORNOT", "$_MUX_": "MUX",
    "$_FF_": "DFF",
}


def parse_last_stat(stdout):
    """Counts from the LAST 'Printing statistics' block (after abc)."""
    parts = stdout.split("Printing statistics")
    if len(parts) < 2:
        return None, None
    block = parts[-1]
    counts = {}
    for m in re.finditer(r"^\s*(\d+)\s+(\$_[A-Z0-9_]+_)\s*$", block, re.MULTILINE):
        counts[NAME_MAP.get(m.group(2), m.group(2))] = int(m.group(1))
    total = re.search(r"^\s*(\d+)\s+cells\s*$", block, re.MULTILINE)
    return counts, (int(total.group(1)) if total else None)


def generate_mapped_verilog(circuit):
    folder      = os.path.join(DATASET_PATH, circuit)
    blif_in     = os.path.join(folder, f"{circuit}.blif")
    verilog_out = os.path.join(folder, f"{circuit}_mapped.v")
    log_out     = os.path.join(folder, f"{circuit}_yosys.log")
    json_out    = os.path.join(folder, f"{circuit}_yosys_stat.json")

    if not os.path.exists(blif_in):
        print(f"  [SKIP] {blif_in} not found")
        return False

    yosys_script = (
        f"read_blif {blif_in}; "
        f"synth -top {circuit}.blif; "
        f"abc -g AND,NAND,OR; "
        f"stat; "
        f"{WRITE_CMD} {verilog_out}"
    )

    print(f"\n{'-'*50}\n  Processing : {circuit}")

    try:
        result = subprocess.run(
            ["cmd", "/c", YOSYS_BAT, yosys_script],
            capture_output=True, text=True, timeout=900
        )
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {circuit}")
        return False

    with open(log_out, "w") as fh:
        fh.write(result.stdout)

    if result.returncode != 0:
        print(f"  [ERROR] RC={result.returncode}")
        print(result.stderr[-300:] if result.stderr else "")
        return False

    counts, total = parse_last_stat(result.stdout)
    if not counts:
        print("  [WARN] could not read stat block, check the log file")
        return False

    with open(json_out, "w") as fh:
        json.dump({"counts": counts, "total_cells": total}, fh, indent=2)

    print(f"  Yosys stat : {counts}  total={total}")
    return os.path.exists(verilog_out)


def main():
    circuits = sys.argv[1:] if len(sys.argv) > 1 else ALL_CIRCUITS
    print(f"Flow     : read_blif -> synth -> abc -g AND,NAND,OR -> {WRITE_CMD}")
    print(f"Circuits : {circuits}")

    ok  = [c for c in circuits if generate_mapped_verilog(c)]
    bad = [c for c in circuits if c not in ok]

    print(f"\n{'='*50}\n  Success: {ok}")
    if bad:
        print(f"  Failed : {bad}")


if __name__ == "__main__":
    main()