import argparse
from netlist_loader import load_circuit
from graph_builder import build_graph
from feature_extractor import get_all_paths
from sta import run_sta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True, help="Circuit name e.g. b01")
    ap.add_argument("--clock", type=float, default=None)
    args = ap.parse_args()

    path, inputs, outputs, gates = load_circuit(args.bench)
    G = build_graph(inputs, outputs, gates)

    print(f"\n{'='*60}\n  STA - {args.bench}\n  netlist: {path}\n{'='*60}")
    paths = get_all_paths(G, inputs, outputs)
    print(f"  Paths found   : {len(paths)}")

    node_timing, path_timing, cp, ncp, pcp, clock_ps = run_sta(
        path, paths, clock_period_ps=args.clock)
    print(f"  Clock period  : {clock_ps:.1f} ps")
    print(f"  CP paths      : {len(cp)}")
    print(f"  NCP paths     : {len(ncp)}")
    print(f"  PCP candidates: {len(pcp)}")

    if cp:
        print(f"\n  Critical path: slack={cp[0]['path_slack_ps']:.1f} ps  "
              f"delay={cp[0]['path_delay_ps']:.1f} ps  gates={cp[0]['n_gates']}")
        print(f"  {cp[0]['path']}")

    print("\n  Top 10:")
    for i, p in enumerate(path_timing[:10], 1):
        print(f"  {i:<3}{p['path_delay_ps']:<9.1f}{p['path_slack_ps']:<9.1f}"
              f"{p['n_gates']:<4}{p['start']} -> {p['end']}")


if __name__ == "__main__":
    main()