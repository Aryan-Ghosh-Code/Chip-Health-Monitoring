import sys
import networkx as nx
from collections import Counter
from netlist_loader import load_circuit
from graph_builder import build_graph
from dataset_builder import compute_logic_depth


def check(circuit):
    path, inputs, outputs, gates = load_circuit(circuit)
    G = build_graph(inputs, outputs, gates)
    depth = compute_logic_depth(G)

    n_dff  = sum(1 for g in gates if g["type"] == "DFF")
    n_comb = len(gates) - n_dff
    names  = [g["gate"] for g in gates]
    expected_nodes = len(set(inputs)) + n_comb + 2 * n_dff
    types = Counter(a.get("type") for _, a in G.nodes(data=True))

    checks = {
        "is DAG"                    : nx.is_directed_acyclic_graph(G),
        "gate names unique"         : len(set(names)) == len(names),
        "node count = in+comb+2*FF" : G.number_of_nodes() == expected_nodes,
        "no dangling signals"       : types.get("IMPLICIT_INPUT", 0) == 0,
        "all PI depth = 0"          : all(depth[i] == 0 for i in set(inputs)),
        "all DFF_Q depth = 0"       : all(depth[n] == 0 for n, a in G.nodes(data=True)
                                          if a.get("type") == "DFF_Q"),
    }

    print(f"\n{'='*52}\n  {circuit}   ({path})")
    print(f"  nodes={G.number_of_nodes()} (expected {expected_nodes})  "
          f"edges={G.number_of_edges()}  max depth={max(depth.values())}")
    print(f"  node types: {dict(types)}")
    for k, v in checks.items():
        print(f"  {'OK  ' if v else 'FAIL'}  {k}")
    return all(checks.values())


if __name__ == "__main__":
    results = {c: check(c) for c in (sys.argv[1:] or ["b01", "b10"])}
    print(f"\n  {'ALL PASS' if all(results.values()) else 'FAILURES: ' + str([c for c, v in results.items() if not v])}")