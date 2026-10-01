import networkx as nx


def get_all_paths(G, inputs, outputs):

    paths = []

    # Startpoints = primary inputs + DFF_Q nodes
    startpoints = inputs + [n for n, a in G.nodes(data=True)
                            if a.get("type") == "DFF_Q"]

    # Endpoints = DFF_D nodes + output-marked nodes
    endpoints = [n for n, a in G.nodes(data=True)
                 if a.get("type") == "DFF_D" or a.get("output") == True]

    for i in startpoints:
        for o in endpoints:
            if i in G and o in G:
                try:
                    for path in nx.all_simple_paths(G, i, o, cutoff=40):
                        paths.append(path)
                        if len(paths) >= 100000:
                            return paths
                except:
                    pass

    return paths


gate_delay = {
    "AND"  : 2,
    "OR"   : 2,
    "NAND" : 2,
    "NOR"  : 2,
    "NOT"  : 1,
    "BUF"  : 1,
    "XOR"  : 3,
    "XNOR" : 3,
}


def extract_features(G, path):

    path_length = len(path)
    fanouts = []
    delay = 0

    type_counts = {
        "AND"  : 0,
        "OR"   : 0,
        "NAND" : 0,
        "NOR"  : 0,
        "NOT"  : 0,
        "BUF"  : 0,
    }

    for node in path:
        fanouts.append(G.out_degree(node))
        node_type = G.nodes[node].get("type", "")
        if node_type in gate_delay:
            delay += gate_delay[node_type]
        if node_type in type_counts:
            type_counts[node_type] += 1

    avg_fanout = sum(fanouts) / len(fanouts)

    return {
        "path_length" : path_length,
        "avg_fanout"  : avg_fanout,
        "delay"       : delay,
        "n_AND"       : type_counts["AND"],
        "n_NAND"      : type_counts["NAND"],
        "n_NOT"       : type_counts["NOT"],
        "n_OR"        : type_counts["OR"],
        "n_NOR"       : type_counts["NOR"],
    }