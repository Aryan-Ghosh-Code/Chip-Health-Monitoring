import re

def parse_bench(bench_file):

    inputs = []
    outputs = []
    gates = []

    with open(bench_file, "r") as f:
        lines = f.readlines()

    print("Total lines:", len(lines))

    for i, line in enumerate(lines):

        line = line.strip()

        if not line or line.startswith("#"):
            continue

        # INPUT
        if line.startswith("INPUT"):
            node = re.findall(r'\((.*?)\)', line)[0]
            inputs.append(node)

        # OUTPUT
        elif line.startswith("OUTPUT"):
            node = re.findall(r'\((.*?)\)', line)[0]
            outputs.append(node)

        # GATE
        elif "=" in line:

            left, right = line.split("=")
            gate_name = left.strip()

            gate_type = right.split("(")[0].strip()

            gate_inputs = re.findall(r'\((.*?)\)', right)[0].split(",")

            gate_inputs = [x.strip() for x in gate_inputs]

            gates.append({
                "gate": gate_name,
                "type": gate_type,
                "inputs": gate_inputs
            })

    return inputs, outputs, gates