"""Profile every raw CSV in the RR data pack (read-only)."""
from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "rr_data_pack"
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 200)

for f in sorted(RAW.glob("*.csv")):
    df = pd.read_csv(f, low_memory=False)
    print(f"\n######## {f.name}: {df.shape[0]} rows x {df.shape[1]} cols; full-row dupes={df.duplicated().sum()}")
    rows = []
    for c in df.columns:
        s = df[c]
        rows.append(dict(col=c, dtype=str(s.dtype), nulls=int(s.isna().sum()),
                         nunique=int(s.nunique()),
                         sample=", ".join(map(str, s.dropna().unique()[:6]))[:110]))
    print(pd.DataFrame(rows).to_string(index=False))
