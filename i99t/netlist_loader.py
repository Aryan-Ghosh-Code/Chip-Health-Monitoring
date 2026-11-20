import os

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"


def load_netlist_file(path):
    if path.endswith(".v"):
        from verilog_parser import parse_verilog
        return parse_verilog(path)
    from bench_parser import parse_bench
    return parse_bench(path)


def find_netlist(circuit):
    v = os.path.join(DATASET_PATH, circuit, f"{circuit}_mapped.v")
    b = os.path.join(DATASET_PATH, circuit, f"{circuit}.bench")
    if os.path.exists(v):
        return v
    if os.path.exists(b):
        print(f"  [WARN] {circuit}: falling back to raw .bench")
        return b
    raise FileNotFoundError(f"No netlist found for {circuit}")


def load_circuit(circuit):
    path = find_netlist(circuit)
    inputs, outputs, gates = load_netlist_file(path)
    return path, inputs, outputs, gates