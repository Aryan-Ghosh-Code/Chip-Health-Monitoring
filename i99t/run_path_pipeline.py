"""
run_path_pipeline.py
====================
Builds path-level feature dataset for selected circuits.
Priority: *_mapped.v > *_mapped.blif > *.bench
"""

import os
import pandas as pd
from dataset_builder import build_path_dataset

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

CIRCUITS = ["b01", "b02", "b03", "b06", "b08", "b09", "b10"]

all_data = []

for folder in CIRCUITS:
    v_mapped = os.path.join(DATASET_PATH, folder, f"{folder}_mapped.v")
    b_mapped = os.path.join(DATASET_PATH, folder, f"{folder}_mapped.blif")
    b_raw    = os.path.join(DATASET_PATH, folder, f"{folder}.bench")

    if os.path.exists(v_mapped):
        input_file = v_mapped
        file_type  = "verilog"
    elif os.path.exists(b_mapped):
        input_file = b_mapped
        file_type  = "blif"
    elif os.path.exists(b_raw):
        input_file = b_raw
        file_type  = "bench"
        print(f"  [WARN] {folder}: using raw bench")
    else:
        print(f"  [SKIP] {folder}: no input file")
        continue

    print(f"\nProcessing: {folder}  ({file_type})")

    try:
        df            = build_path_dataset(input_file, file_type=file_type)
        df["circuit"] = folder
        all_data.append(df)
        print(f"  {len(df)} paths extracted")
    except Exception as e:
        print(f"  ERROR: {e}")

if all_data:
    final = pd.concat(all_data, ignore_index=True)
    final.to_csv("path_dataset.csv", index=False)
    print(f"\nDone. path_dataset.csv: {final.shape}")
    print(final.groupby("circuit")["delay"].max())