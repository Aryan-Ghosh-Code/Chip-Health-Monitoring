"""
Step A — Static Timing Analysis (STA)
======================================
Computes per-gate Arrival Time (AAT), Required Arrival Time (RAT),
and Slack for every node and path in the circuit.

Pipeline position:
    .bench → graph_builder → sta.py → path delays + slack
    
Inputs:  bench_file path, clock_period (optional)
Outputs: 
    - node_timing dict  {node: {aat, rat, slack, delay}}
    - path_timing list  [{path, delay, slack, start, end}]
    - cp  (critical path — minimum slack)
    - ncp (near-critical paths — within ncp_margin of CP)
    - pcp_candidates (NCP paths flagged by high SP, filled after Step B)

Gate delay table (approximate 45nm, ps units):
    These replace unit delays (AND=2) with physically scaled values.
    Source: Nangate 45nm Open Cell Library typical corner.
    Will be replaced by Liberty LUT in a future phase.
"""

from bench_parser import parse_bench
from graph_builder import build_graph
from collections import deque
import networkx as nx


# ── Gate delay table (picoseconds, 45nm typical corner) ──────────────────────
# These are representative values consistent with published 45nm data.
# NOT from HSPICE — substitute for academic project.
GATE_DELAY_PS = {
    "AND"          : 42,
    "NAND"         : 35,   # NAND faster than AND in CMOS
    "OR"           : 45,
    "NOR"          : 38,
    "NOT"          : 22,
    "BUF"          : 18,
    "XOR"          : 68,
    "XNOR"         : 70,
    "DFF_Q"        :  0,   # Clock-to-Q modelled separately; 0 here
    "DFF_D"        :  0,   # Setup time not modelled yet
    "INPUT"        :  0,
    "IMPLICIT_INPUT":  0,
}
DEFAULT_DELAY_PS = 40      # fallback for unknown types


def get_gate_delay(gate_type):
    return GATE_DELAY_PS.get(gate_type, DEFAULT_DELAY_PS)


# ═════════════════════════════════════════════════════════════════════════════
# FORWARD PASS — Actual Arrival Time (AAT)
# ═════════════════════════════════════════════════════════════════════════════

def compute_aat(G):
    """
    AAT(node) = max over all predecessors p of:
                    AAT(p) + delay(p)
    
    Startpoints (PI, DFF_Q) have AAT = 0.
    Uses Kahn's topological sort to process in dependency order.
    """
    in_deg = {n: G.in_degree(n) for n in G.nodes}
    aat    = {n: 0.0 for n in G.nodes}
    queue  = deque(n for n, d in in_deg.items() if d == 0)

    while queue:
        node = queue.popleft()
        d    = get_gate_delay(G.nodes[node].get("type", ""))

        for succ in G.successors(node):
            candidate = aat[node] + d
            if candidate > aat[succ]:
                aat[succ] = candidate
            in_deg[succ] -= 1
            if in_deg[succ] == 0:
                queue.append(succ)

    return aat


# ═════════════════════════════════════════════════════════════════════════════
# BACKWARD PASS — Required Arrival Time (RAT)
# ═════════════════════════════════════════════════════════════════════════════

def compute_rat(G, aat, clock_period_ps):
    """
    RAT(endpoint) = clock_period  (signal must arrive before clock edge)
    RAT(node)     = min over all successors s of:
                        RAT(s) - delay(node)
    
    Processed in reverse topological order.
    """
    topo  = list(nx.topological_sort(G))
    rat   = {n: clock_period_ps for n in G.nodes}

    for node in reversed(topo):
        d = get_gate_delay(G.nodes[node].get("type", ""))
        for succ in G.successors(node):
            candidate = rat[succ] - d
            if candidate < rat[node]:
                rat[node] = candidate

    return rat


# ═════════════════════════════════════════════════════════════════════════════
# SLACK
# ═════════════════════════════════════════════════════════════════════════════

def compute_slack(aat, rat):
    """
    Slack = RAT - AAT
    Positive slack → timing margin exists
    Zero slack     → path is exactly at timing limit (critical)
    Negative slack → timing violation
    """
    return {n: rat[n] - aat[n] for n in aat}


# ═════════════════════════════════════════════════════════════════════════════
# AUTO-CLOCK: pick clock period just above max AAT
# ═════════════════════════════════════════════════════════════════════════════

def auto_clock(aat, margin_factor=1.05):
    """
    Set clock period = max AAT * margin_factor.
    This ensures CP has slack close to 0 but not negative.
    margin_factor=1.05 gives 5% timing margin.
    """
    max_aat = max(aat.values())
    return max_aat * margin_factor


# ═════════════════════════════════════════════════════════════════════════════
# PATH TIMING
# ═════════════════════════════════════════════════════════════════════════════

def compute_path_timing(G, paths, aat, rat, slack):
    """
    For each enumerated path, compute:
        path_delay = AAT at endpoint
        path_slack = slack at endpoint
        path_slack_min = minimum slack along any node in the path
    """
    results = []
    for path in paths:
        if not path:
            continue
        endpoint    = path[-1]
        startpoint  = path[0]
        path_delay  = aat[endpoint]
        path_slack  = slack[endpoint]
        min_slack   = min(slack[n] for n in path)

        results.append({
            "start"         : startpoint,
            "end"           : endpoint,
            "path_delay_ps" : round(path_delay, 2),
            "path_slack_ps" : round(path_slack, 2),
            "min_slack_ps"  : round(min_slack, 2),
            "n_gates"       : len(path),
            "path"          : " -> ".join(path),
        })

    # Sort by slack ascending (most critical first)
    results.sort(key=lambda x: x["path_slack_ps"])
    return results


# ═════════════════════════════════════════════════════════════════════════════
# CP / NCP / PCP CLASSIFICATION
# ═════════════════════════════════════════════════════════════════════════════

def classify_paths(path_timing, ncp_margin=0.10):
    """
    CP  = path(s) with minimum slack (slack ≈ 0)
    NCP = paths whose slack is within ncp_margin of CP slack
          i.e. slack <= CP_slack + ncp_margin * clock_period
    PCP = NCP candidates (SP/AF flagged after Step B)
    
    ncp_margin=0.10 means within 10% of clock period above CP slack.
    """
    if not path_timing:
        return [], [], []

    cp_slack = path_timing[0]["path_slack_ps"]   # already sorted

    # CP: all paths at minimum slack (may be ties)
    cp  = [p for p in path_timing if p["path_slack_ps"] == cp_slack]

    # NCP: paths within ncp_margin * max_delay of CP slack
    max_delay  = max(p["path_delay_ps"] for p in path_timing)
    ncp_cutoff = cp_slack + ncp_margin * max_delay
    ncp = [p for p in path_timing
           if cp_slack < p["path_slack_ps"] <= ncp_cutoff]

    # PCP candidates = NCP (SP/AF will filter further in Step B)
    pcp_candidates = ncp.copy()

    return cp, ncp, pcp_candidates


# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def run_sta(bench_file, paths, clock_period_ps=None):
    """
    Full STA pipeline for one circuit.
    
    Args:
        bench_file      : path to .bench file
        paths           : list of paths from get_all_paths()
        clock_period_ps : if None, auto-computed from max AAT
    
    Returns:
        node_timing : dict {node: {aat, rat, slack, delay, type}}
        path_timing : list of path dicts sorted by slack (CP first)
        cp, ncp, pcp: classified path lists
        clock_ps    : clock period used
    """
    inputs, outputs, gates = parse_bench(bench_file)
    G = build_graph(inputs, outputs, gates)

    # Forward pass
    aat = compute_aat(G)

    # Auto clock if not specified
    if clock_period_ps is None:
        clock_period_ps = auto_clock(aat, margin_factor=1.05)

    # Backward pass
    rat   = compute_rat(G, aat, clock_period_ps)
    slack = compute_slack(aat, rat)

    # Node timing table
    node_timing = {}
    for node in G.nodes:
        ntype = G.nodes[node].get("type", "UNKNOWN")
        node_timing[node] = {
            "type"     : ntype,
            "delay_ps" : get_gate_delay(ntype),
            "aat_ps"   : round(aat[node], 2),
            "rat_ps"   : round(rat[node], 2),
            "slack_ps" : round(slack[node], 2),
        }

    # Path timing
    path_timing    = compute_path_timing(G, paths, aat, rat, slack)
    cp, ncp, pcp   = classify_paths(path_timing)

    return node_timing, path_timing, cp, ncp, pcp, clock_period_ps