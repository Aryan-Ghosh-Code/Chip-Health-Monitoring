import os
import pandas as pd
from dataset_builder import build_dataset

DATASET_PATH = r"E:\\Projects\\ChipHealthAnalysis\\i99t"

all_data = []

for folder in os.listdir(DATASET_PATH):

    bench_file = os.path.join(DATASET_PATH, folder, f"{folder}.bench")

    if os.path.exists(bench_file):

        print("\nProcessing:", bench_file)

        df = build_dataset(bench_file)

        df["circuit"] = folder

        all_data.append(df)

final_dataset = pd.concat(all_data)

final_dataset.to_csv("final_dataset.csv", index=False)

print("\nDataset created: final_dataset.csv")