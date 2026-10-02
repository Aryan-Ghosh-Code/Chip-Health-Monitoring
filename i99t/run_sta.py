"""
run_sta.py — Run STA on a single circuit and print results.
Usage:
    python run_sta.py --bench b01
    python run_sta.py --bench b10
"""

import argparse
import os
from bench_parser import parse_bench
from graph_builder import build_graph
from feature_extractor import get_all_paths
from sta import run_sta

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True, help="Circuit name e.g. b01")
    ap.add_argument("--clock", type=float, default=None,
                    help="Clock period in ps. Default: auto (5% above CP delay)")
    args = ap.parse_args()

    bench_file = os.path.join(DATASET_PATH, args.bench, f"{args.bench}.bench")

    # Parse and enumerate paths
    print(f"\n{'='*60}")
    print(f"  STA — {args.bench}")
    print(f"{'='*60}")

    inputs, outputs, gates = parse_bench(bench_file)
    G = build_graph(inputs, outputs, gates)

    print(f"\n[1/3] Enumerating paths...")
    paths = get_all_paths(G, inputs, outputs)
    print(f"  Found {len(paths)} paths")

    # Run STA
    print(f"\n[2/3] Running STA...")
    node_timing, path_timing, cp, ncp, pcp, clock_ps = run_sta(
        bench_file, paths, clock_period_ps=args.clock
    )
    print(f"  Clock period : {clock_ps:.1f} ps")
    print(f"  Total paths  : {len(path_timing)}")
    print(f"  CP  paths    : {len(cp)}")
    print(f"  NCP paths    : {len(ncp)}")
    print(f"  PCP candidates: {len(pcp)}  (SP/AF not yet applied)")

    # Print critical path
    print(f"\n[3/3] Critical Path Analysis")
    print(f"{'─'*60}")

    if cp:
        print(f"\n  CRITICAL PATH (slack = {cp[0]['path_slack_ps']:.1f} ps):")
        print(f"  Delay  : {cp[0]['path_delay_ps']:.1f} ps")
        print(f"  Gates  : {cp[0]['n_gates']}")
        print(f"  Path   : {cp[0]['path']}")

    print(f"\n  TOP 10 MOST CRITICAL PATHS:")
    print(f"  {'#':<4} {'Delay(ps)':<12} {'Slack(ps)':<12} {'Gates':<7} Start → End")
    print(f"  {'─'*60}")
    for i, p in enumerate(path_timing[:10]):
        print(f"  {i+1:<4} {p['path_delay_ps']:<12.1f} "
              f"{p['path_slack_ps']:<12.1f} {p['n_gates']:<7} "
              f"{p['start']} → {p['end']}")

    print(f"\n  NEAR-CRITICAL PATHS (NCP, within 10% of CP):")
    if ncp:
        for p in ncp[:5]:
            print(f"    delay={p['path_delay_ps']:.1f}ps  "
                  f"slack={p['path_slack_ps']:.1f}ps  "
                  f"{p['start']} → {p['end']}")
    else:
        print("    None found (circuit may have very few paths)")

    # Node slack summary
    print(f"\n  MOST CRITICAL NODES (lowest slack):")
    print(f"  {'Node':<30} {'Type':<14} {'AAT(ps)':<10} {'RAT(ps)':<10} Slack(ps)")
    print(f"  {'─'*68}")
    sorted_nodes = sorted(node_timing.items(),
                          key=lambda x: x[1]["slack_ps"])
    for node, nt in sorted_nodes[:10]:
        if nt["type"] not in ("INPUT", "DFF_Q", "IMPLICIT_INPUT"):
            print(f"  {node:<30} {nt['type']:<14} "
                  f"{nt['aat_ps']:<10.1f} {nt['rat_ps']:<10.1f} "
                  f"{nt['slack_ps']:.1f}")

    print(f"\n{'='*60}")
    print(f"  Done. Next step: run sp_simulator.py on {args.bench}")
    print(f"  Then: run bti_model.py to compute aged delays at t=1,3,5yr")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()