from dataset_builder import build_dataset

bench_file = r"E:\\Projects\\ChipHealthAnalysis\\i99t\\b01\\b01_C.bench"

df = build_dataset(bench_file)

print("\n===== b01 DATASET =====")
print(df.to_string(index=False))

print("\n===== DEPTH SUMMARY =====")
print(df["depth"].describe())

print("\n===== MAX DEPTH =====")
print(df["depth"].max())