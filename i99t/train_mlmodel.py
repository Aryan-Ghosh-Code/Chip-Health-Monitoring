import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, recall_score, precision_score

df = pd.read_csv("ml_path_dataset.csv")

X = df[["path_length", "avg_fanout",
        "n_AND", "n_NAND", "n_NOT", "n_OR", "n_NOR"]]
y = df["critical"]

print("Dataset shape:", df.shape)
print("Features used:", X.columns.tolist())
print("Critical=1:", y.sum(), "out of", len(y))
print()

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

reports = []
importances = []

for fold, (train_idx, test_idx) in enumerate(skf.split(X, y)):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    model = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    reports.append({
        "fold"      : fold + 1,
        "accuracy"  : (preds == y_test).mean(),
        "precision" : precision_score(y_test, preds, zero_division=0),
        "recall"    : recall_score(y_test, preds, zero_division=0),
        "f1"        : f1_score(y_test, preds, zero_division=0),
    })
    importances.append(model.feature_importances_)

results = pd.DataFrame(reports)
print("Per-fold results:")
print(results.to_string(index=False))
print("\nMean across folds:")
print(results.drop(columns="fold").mean().round(3).to_string())

mean_imp = np.mean(importances, axis=0)
print("\nMean feature importances:")
for feat, imp in sorted(zip(X.columns, mean_imp), key=lambda x: -x[1]):
    print(f"  {feat:<20}: {imp:.4f}")

dummy_acc = max(y.mean(), 1 - y.mean())
print(f"\nDummy classifier accuracy: {dummy_acc:.3f}")
print(f"Mean model accuracy      : {results['accuracy'].mean():.3f}")
print(f"Mean recall on critical=1: {results['recall'].mean():.3f}")
print(f"Mean F1 on critical=1    : {results['f1'].mean():.3f}")