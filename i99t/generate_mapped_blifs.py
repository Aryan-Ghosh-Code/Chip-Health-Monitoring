import os
import sys
import subprocess

YOSYS_BAT    = r"E:\Projects\ChipHealthAnalysis\i99t\run_yosys.bat"
DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

ALL_CIRCUITS = [
    "b01", "b02", "b03", "b04", "b05", "b06", "b07", "b08",
    "b09", "b10", "b11", "b12", "b13", "b14", "b15",
    "b17", "b20", "b21", "b22"
]

# Same flow everywhere: read_blif -> synth -> abc -> write_verilog (cells, no expressions)
WRITE_CMD = "write_verilog -noexpr -noattr"


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
        f"{WRITE_CMD} {verilog_out}"
    )

    print(f"\n{'-'*50}\n  Processing : {circuit}")

    try:
        result = subprocess.run(
            ["cmd", "/c", YOSYS_BAT, yosys_script],
            capture_output=True, text=True, timeout=900
        )
        for line in result.stdout.splitlines():
            if "ABC RESULTS" in line:
                print(f"  {line.strip()}")

        if result.returncode != 0:
            print(f"  [ERROR] RC={result.returncode}")
            print(result.stderr[-300:] if result.stderr else "")
            return False

        if os.path.exists(verilog_out):
            print(f"  [OK] {os.path.getsize(verilog_out)} bytes")
            return True
        print("  [ERROR] Output file not created")
        return False

    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {circuit}")
        return False


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