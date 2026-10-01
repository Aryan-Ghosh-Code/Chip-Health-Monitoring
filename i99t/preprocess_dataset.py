import pandas as pd

df = pd.read_csv("E:\Projects\ChipHealthAnalysis\I99T\i99t\\final_dataset.csv")

# One‑hot encode gate types
df = pd.get_dummies(df, columns=["type"])

# Save processed dataset
df.to_csv("E:\Projects\ChipHealthAnalysis\I99T\i99t\processed_dataset.csv", index=False)

print("Processed dataset created.")