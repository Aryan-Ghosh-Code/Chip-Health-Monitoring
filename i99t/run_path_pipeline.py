import os
import pandas as pd
from dataset_builder import build_path_dataset

DATASET_PATH = r"E:\Projects\ChipHealthAnalysis\i99t"

CIRCUITS = ["b01", "b02", "b03", "b06", "b08", "b09", "b10"]

all_data = []

for folder in CIRCUITS:
    bench_file = os.path.join(DATASET_PATH, folder, f"{folder}.bench")
    if os.path.exists(bench_file):
        print(f"\nProcessing: {folder}")
        try:
            df = build_path_dataset(bench_file)
            df["circuit"] = folder
            all_data.append(df)
            print(f"  {len(df)} paths extracted")
        except Exception as e:
            print(f"  ERROR: {e}")

final = pd.concat(all_data, ignore_index=True)
final.to_csv("path_dataset.csv", index=False)
print(f"\nDone. path_dataset.csv: {final.shape}")
print(final.groupby("circuit")["delay"].max())