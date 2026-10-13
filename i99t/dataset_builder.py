"""
dataset_builder.py
==================
Builds node-level and path-level feature DataFrames.
Priority: Verilog mapped > BLIF mapped > raw BENCH
"""

import pandas as pd
from collections import deque
from graph_builder import build_graph


def compute_logic_depth(G):
    in_deg = {n: G.in_degree(n) for n in G.nodes}
    depth  = {n: 0 for n in G.nodes}
    queue  = deque(n for n, d in in_deg.items() if d == 0)

    while queue:
        node = queue.popleft()
        for succ in G.successors(node):
            if depth[node] + 1 > depth[succ]:
                depth[succ] = depth[node] + 1
            in_deg[succ] -= 1
            if in_deg[succ] == 0:
                queue.append(succ)

    return depth


def _parse(input_file, file_type):
    if file_type == "verilog":
        from verilog_parser import parse_verilog
        return parse_verilog(input_file)
    elif file_type == "blif":
        from blif_parser import parse_blif
        return parse_blif(input_file)
    else:
        from bench_parser import parse_bench
        return parse_bench(input_file)


def build_dataset(input_file, file_type=None):
    if file_type is None:
        if input_file.endswith(".v"):
            file_type = "verilog"
        elif input_file.endswith(".blif"):
            file_type = "blif"
        else:
            file_type = "bench"

    print(f"  Opening ({file_type}): {input_file}")
    inputs, outputs, gates = _parse(input_file, file_type)

    print(f"  Inputs : {len(inputs)}")
    print(f"  Outputs: {len(outputs)}")
    print(f"  Gates  : {len(gates)}")

    G         = build_graph(inputs, outputs, gates)
    depth_map = compute_logic_depth(G)

    data = []
    for node in G.nodes:
        data.append({
            "node"  : node,
            "type"  : G.nodes[node].get("type", "UNKNOWN"),
            "fanin" : G.in_degree(node),
            "fanout": G.out_degree(node),
            "depth" : depth_map[node],
        })

    return pd.DataFrame(data)


def build_path_dataset(input_file, file_type=None):
    from feature_extractor import get_all_paths, extract_features

    if file_type is None:
        if input_file.endswith(".v"):
            file_type = "verilog"
        elif input_file.endswith(".blif"):
            file_type = "blif"
        else:
            file_type = "bench"

    inputs, outputs, gates = _parse(input_file, file_type)
    G = build_graph(inputs, outputs, gates)

    print("  Extracting paths...")
    paths = get_all_paths(G, inputs, outputs)
    print(f"  Found {len(paths)} paths")

    path_data = []
    for path in paths:
        features          = extract_features(G, path)
        features["start"] = path[0]
        features["end"]   = path[-1]
        features["path"]  = " -> ".join(path)
        path_data.append(features)

    return pd.DataFrame(path_data)