"""
run_pipeline.py
===============
Builds node-level feature dataset across all ITC'99 circuits.
Priority: *_mapped.v > *_mapped.blif > *.bench
"""

import os
import pandas as pd
from dataset_builder import build_dataset

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

CIRCUITS = [
    "b01", "b02", "b03", "b04", "b05", "b06", "b07", "b08",
    "b09", "b10", "b11", "b12", "b13", "b14", "b15",
    "b17", "b20", "b21", "b22"
]

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
        print(f"  [SKIP] {folder}: no input file found")
        continue

    print(f"\nProcessing: {folder}  ({file_type})")

    try:
        df            = build_dataset(input_file, file_type=file_type)
        df["circuit"] = folder
        all_data.append(df)
    except Exception as e:
        print(f"  [ERROR] {folder}: {e}")

if all_data:
    final = pd.concat(all_data, ignore_index=True)
    final.to_csv("final_dataset.csv", index=False)
    print(f"\n{'='*50}")
    print(f"  final_dataset.csv  shape: {final.shape}")
    print(f"\n  Node counts per circuit:")
    print(final.groupby("circuit")["node"].count().to_string())
    print(f"\n  Gate type distribution:")
    print(final["type"].value_counts().to_string())