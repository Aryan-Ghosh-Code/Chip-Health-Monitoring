from bench_parser import parse_bench
from graph_builder import build_graph
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Use b01 — small enough to be readable
inputs, outputs, gates = parse_bench(
    r"E:\Projects\ChipHealthAnalysis\i99t\b01\b01.bench"
)
G = build_graph(inputs, outputs, gates)

# Use a hierarchical layout based on logic depth
from dataset_builder import compute_logic_depth
depth_map = compute_logic_depth(G)

# Position nodes by depth (x = depth, y = spread within depth)
from collections import defaultdict
depth_to_nodes = defaultdict(list)
for node, d in depth_map.items():
    depth_to_nodes[d].append(node)

pos = {}
for depth, nodes in depth_to_nodes.items():
    for i, node in enumerate(sorted(nodes)):
        pos[node] = (depth, -i * 1.2)

# Colour by node type
color_map = []
for node in G.nodes():
    t = G.nodes[node].get("type", "")
    if t == "INPUT":
        color_map.append("lightgreen")
    elif t == "DFF_D":
        color_map.append("salmon")
    elif t == "DFF_Q":
        color_map.append("lightyellow")
    else:
        color_map.append("lightblue")

plt.figure(figsize=(18, 10))
nx.draw(G, pos=pos,
        labels={n: G.nodes[n].get("type","")[:4] + "\n" + n[:4]
                for n in G.nodes()},
        node_color=color_map,
        node_size=800,
        font_size=5,
        arrows=True,
        arrowsize=10,
        edge_color="gray",
        with_labels=True)

plt.title("b01 Circuit DAG -- Logic Depth Layout\n"
          "Green=INPUT  Blue=Gate  Yellow=DFF_Q  Red=DFF_D")
plt.tight_layout()
plt.savefig("b01_dag.png", dpi=150, bbox_inches="tight")
print("Saved: b01_dag.png")