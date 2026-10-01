import pandas as pd

df = pd.read_csv("path_dataset.csv")

def label_per_circuit(group):
    threshold = group["delay"].quantile(0.90)
    group["critical"] = (group["delay"] >= threshold).astype(int)

    # Normalized features — circuit-size independent
    max_delay  = group["delay"].max()
    max_length = group["path_length"].max()

    group["delay_ratio"]  = group["delay"] / max_delay if max_delay > 0 else 0
    group["length_ratio"] = group["path_length"] / max_length if max_length > 0 else 0

    return group

df = df.groupby("circuit", group_keys=False).apply(
    label_per_circuit, include_groups=False
)

# groupby drops the circuit col with include_groups=False, re-add it
# Actually safer to do it differently:
df = pd.read_csv("path_dataset.csv")

results = []
for circuit, group in df.groupby("circuit"):
    threshold = group["delay"].quantile(0.90)
    group = group.copy()
    group["critical"]     = (group["delay"] >= threshold).astype(int)
    group["delay_ratio"]  = group["delay"] / group["delay"].max()
    group["length_ratio"] = group["path_length"] / group["path_length"].max()
    results.append(group)

df = pd.concat(results, ignore_index=True)

print("Shape:", df.shape)
print("\nCritical per circuit:")
print(df.groupby("circuit")["critical"].sum().to_string())
print("\ndelay_ratio range:", df["delay_ratio"].min(), "to", df["delay_ratio"].max())

df.to_csv("ml_path_dataset.csv", index=False)
print("\nDone.")