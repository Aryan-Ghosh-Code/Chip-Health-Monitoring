"""
run_pipeline.py
===============
Builds node-level feature dataset across all ITC'99 circuits.
Uses ABC-mapped BLIF files if available, falls back to raw BENCH.
"""

import os
import pandas as pd
from dataset_builder import build_dataset

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

CIRCUITS = [
    "b01", "b02", "b03", "b04", "b05", "b06", "b07", "b08",
    "b09", "b10", "b11", "b12", "b13", "b14", "b15",
    "b17", "b18", "b19", "b20", "b21", "b22"
]

all_data = []

for folder in CIRCUITS:

    blif_mapped = os.path.join(DATASET_PATH, folder, f"{folder}_mapped.blif")
    bench_raw   = os.path.join(DATASET_PATH, folder, f"{folder}.bench")

    if os.path.exists(blif_mapped):
        input_file = blif_mapped
        file_type  = "blif"
    elif os.path.exists(bench_raw):
        input_file = bench_raw
        file_type  = "bench"
        print(f"  [WARN] {folder}: using raw .bench — run generate_mapped_blifs.py")
    else:
        print(f"  [SKIP] {folder}: no input file found")
        continue

    print(f"\nProcessing: {folder}  ({file_type})")

    try:
        df             = build_dataset(input_file, file_type=file_type)
        df["circuit"]  = folder
        all_data.append(df)
    except Exception as e:
        print(f"  [ERROR] {folder}: {e}")

if not all_data:
    print("\nNo data collected.")
else:
    final = pd.concat(all_data, ignore_index=True)
    final.to_csv("final_dataset.csv", index=False)

    print(f"\n{'='*50}")
    print(f"  final_dataset.csv written")
    print(f"  Shape : {final.shape}")
    print(f"\n  Node counts per circuit:")
    print(final.groupby("circuit")["node"].count().to_string())
    print(f"\n  Gate type distribution (all circuits):")
    print(final["type"].value_counts().to_string())