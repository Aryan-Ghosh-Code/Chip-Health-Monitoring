"""
run_path_pipeline.py
====================
Builds path-level feature dataset for selected circuits.
Uses ABC-mapped BLIF files if available, falls back to raw BENCH.
"""

import os
import pandas as pd
from dataset_builder import build_path_dataset

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

CIRCUITS = ["b01", "b02", "b03", "b06", "b08", "b09", "b10"]

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
        print(f"  [WARN] {folder}: using raw .bench")
    else:
        print(f"  [SKIP] {folder}: no input file found")
        continue

    print(f"\nProcessing: {folder}  ({file_type})")

    try:
        df            = build_path_dataset(input_file, file_type=file_type)
        df["circuit"] = folder
        all_data.append(df)
        print(f"  {len(df)} paths extracted")
    except Exception as e:
        print(f"  ERROR: {e}")

final = pd.concat(all_data, ignore_index=True)
final.to_csv("path_dataset.csv", index=False)
print(f"\nDone. path_dataset.csv: {final.shape}")
print(final.groupby("circuit")["delay"].max())