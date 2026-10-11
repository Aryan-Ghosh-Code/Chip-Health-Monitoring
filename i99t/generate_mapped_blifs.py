import os
import subprocess

YOSYS_BAT    = r"E:\Projects\ChipHealthAnalysis\i99t\run_yosys.bat"
DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

CIRCUITS = [
    "b01", "b02", "b03", "b04", "b05", "b06", "b07", "b08",
    "b09", "b10", "b11", "b12", "b13", "b14", "b15",
    "b17", "b18", "b19", "b20", "b21", "b22"
]


def generate_mapped_blif(circuit):
    blif_in  = os.path.join(DATASET_PATH, circuit, f"{circuit}.blif")
    blif_out = os.path.join(DATASET_PATH, circuit, f"{circuit}_mapped.blif")

    if not os.path.exists(blif_in):
        print(f"  [SKIP] {blif_in} not found")
        return False

    yosys_script = (
        f"read_blif {blif_in}; "
        f"proc; opt; "
        f"abc -g AND,NAND,OR; "
        f"opt; stat; "
        f"write_blif {blif_out}"
    )

    print(f"\n{'─'*50}")
    print(f"  Processing : {circuit}")
    print(f"  Output     : {blif_out}")

    try:
        result = subprocess.run(
            ["cmd", "/c", YOSYS_BAT, yosys_script],
            capture_output=True,
            text=True,
            timeout=300
        )

        for line in result.stdout.splitlines():
            if "ABC RESULTS" in line:
                print(f"  {line.strip()}")

        if result.returncode != 0:
            print(f"  [ERROR] RC={result.returncode}")
            print(result.stderr[-500:] if result.stderr else "(no stderr)")
            return False

        if os.path.exists(blif_out):
            size = os.path.getsize(blif_out)
            print(f"  [OK] {size} bytes written")
            return True
        else:
            print(f"  [ERROR] Output file not created")
            return False

    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {circuit} exceeded 300 seconds")
        return False


def main():
    print(f"Bat file  : {YOSYS_BAT}")
    print(f"Dataset   : {DATASET_PATH}")

    # Sanity check
    print(f"\nSanity check...")
    test = subprocess.run(
        ["cmd", "/c", YOSYS_BAT, "help"],
        capture_output=True, text=True, timeout=30
    )
    if "Yosys" in test.stdout or test.returncode == 0:
        print(f"  Yosys reachable via bat file ✓")
    else:
        print(f"  [FAIL] RC={test.returncode}")
        print(test.stderr[:300])
        return

    success = []
    failed  = []

    for circuit in CIRCUITS:
        ok = generate_mapped_blif(circuit)
        if ok:
            success.append(circuit)
        else:
            failed.append(circuit)

    print(f"\n{'='*50}")
    print(f"  Success : {len(success)} — {success}")
    if failed:
        print(f"  Failed  : {len(failed)} — {failed}")
    print(f"\n  Next: python blif_parser.py b01 b10")


if __name__ == "__main__":
    main()