import pandas as pd
from collections import deque
from bench_parser import parse_bench
from graph_builder import build_graph
import networkx as nx


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


def build_dataset(bench_file):

    print("Opening:", bench_file)

    inputs, outputs, gates = parse_bench(bench_file)

    print("Inputs:", len(inputs))
    print("Outputs:", len(outputs))
    print("Gates:", len(gates))

    G = build_graph(inputs, outputs, gates)

    depth_map = compute_logic_depth(G)

    data = []

    for node in G.nodes:

        ntype  = G.nodes[node].get("type", "UNKNOWN")
        fanin  = G.in_degree(node)
        fanout = G.out_degree(node)
        depth  = depth_map[node]

        data.append({
            "node"  : node,
            "type"  : ntype,
            "fanin" : fanin,
            "fanout": fanout,
            "depth" : depth,
        })

    return pd.DataFrame(data)


def build_path_dataset(bench_file):

    from feature_extractor import get_all_paths, extract_features

    inputs, outputs, gates = parse_bench(bench_file)
    G = build_graph(inputs, outputs, gates)

    print("  Extracting paths...")
    paths = get_all_paths(G, inputs, outputs)
    print(f"  Found {len(paths)} paths")

    path_data = []
    for path in paths:
        features = extract_features(G, path)
        features["start"] = path[0]
        features["end"]   = path[-1]
        features["path"]  = " -> ".join(path)
        path_data.append(features)

    return pd.DataFrame(path_data)