import networkx as nx

def build_graph(inputs, outputs, gates):

    G = nx.DiGraph()

    # Primary inputs — startpoints, depth 0
    for i in inputs:
        G.add_node(i, type="INPUT")

    # DFF outputs (Q pins) — also startpoints, depth 0
    # Named with DFF_Q_ prefix to separate from D input node
    dff_q_nodes = {}
    for gate in gates:
        if gate["type"] == "DFF":
            q_name = "DFF_Q_" + gate["gate"]
            G.add_node(q_name, type="DFF_Q")
            dff_q_nodes[gate["gate"]] = q_name

    # Combinational gates
    for gate in gates:
        if gate["type"] == "DFF":
            # Model D input as an endpoint node
            d_name = gate["gate"]   # keep original name as D input sink
            G.add_node(d_name, type="DFF_D")
            for inp in gate["inputs"]:
                driver = dff_q_nodes.get(inp, inp)  # remap if driven by DFF Q
                if driver not in G:
                    G.add_node(driver, type="IMPLICIT_INPUT")
                G.add_edge(driver, d_name)
        else:
            name  = gate["gate"]
            gtype = gate["type"]
            G.add_node(name, type=gtype)
            for inp in gate["inputs"]:
                # Remap: if inp is a DFF gate name, use its Q node
                driver = dff_q_nodes.get(inp, inp)
                if driver not in G:
                    G.add_node(driver, type="IMPLICIT_INPUT")
                G.add_edge(driver, name)

    # Mark output nodes
    for o in outputs:
        if o in G.nodes:
            G.nodes[o]["output"] = True

    return G