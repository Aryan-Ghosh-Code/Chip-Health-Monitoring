import os
import subprocess

YOSYS_BAT    = r"E:\Projects\ChipHealthAnalysis\i99t\run_yosys.bat"
DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

CIRCUITS = [
    "b01", "b02", "b03", "b04", "b05", "b06", "b07", "b08",
    "b09", "b10", "b11", "b12", "b13", "b14", "b15",
    "b17", "b20", "b21", "b22"
]


def generate_mapped_verilog(circuit):
    blif_in     = os.path.join(DATASET_PATH, circuit, f"{circuit}.blif")
    verilog_out = os.path.join(DATASET_PATH, circuit, f"{circuit}_mapped.v")

    if not os.path.exists(blif_in):
        print(f"  [SKIP] {blif_in} not found")
        return False

    yosys_script = (
        f"read_blif {blif_in}; "
        f"synth -top {circuit}.blif; "
        f"abc -g AND,NAND,OR; "
        f"stat; "
        f"write_verilog {verilog_out}"
    )

    print(f"\n{'─'*50}")
    print(f"  Processing : {circuit}")
    print(f"  Output     : {verilog_out}")

    try:
        result = subprocess.run(
            ["cmd", "/c", YOSYS_BAT, yosys_script],
            capture_output=True,
            text=True,
            timeout=600
        )

        for line in result.stdout.splitlines():
            if "ABC RESULTS" in line or "cells" in line.lower():
                print(f"  {line.strip()}")

        if result.returncode != 0:
            print(f"  [ERROR] RC={result.returncode}")
            print(result.stderr[-300:] if result.stderr else "")
            return False

        if os.path.exists(verilog_out):
            size = os.path.getsize(verilog_out)
            print(f"  [OK] {size} bytes")
            return True
        else:
            print(f"  [ERROR] Output file not created")
            return False

    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {circuit}")
        return False


def main():
    print(f"Yosys bat : {YOSYS_BAT}")
    print(f"Dataset   : {DATASET_PATH}")
    print(f"Flow      : read_blif → synth → abc -g AND,NAND,OR → write_verilog\n")

    success = []
    failed  = []

    for circuit in CIRCUITS:
        ok = generate_mapped_verilog(circuit)
        if ok:
            success.append(circuit)
        else:
            failed.append(circuit)

    print(f"\n{'='*50}")
    print(f"  Success : {len(success)} — {success}")
    if failed:
        print(f"  Failed  : {len(failed)} — {failed}")
    print(f"\n  Next: python verilog_parser.py b01 b10")


if __name__ == "__main__":
    main()