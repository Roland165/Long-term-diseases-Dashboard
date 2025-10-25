# utils/io.py — lecture flexible + enregistrement du rapport
# utils/io.py
from pathlib import Path
import pandas as pd

def sniff_sep(sample: str) -> str:
    if ";" in sample and sample.count(";") >= sample.count(","):
        return ";"
    return ","

def read_csv_flexible(path_or_buf) -> pd.DataFrame:
    """
    Lecture CSV rapide avec détection du séparateur (';' ou ',').
    Utilise pyarrow si dispo, sinon fallback python.
    """
    import io

    # Détecte le séparateur
    def sniff_sep(sample: str) -> str:
        if ";" in sample and sample.count(";") >= sample.count(","):
            return ";"
        return ","

    try:
        import pyarrow  # on teste simplement sa présence
        engine = "pyarrow"
    except ImportError:
        engine = "python"

    # Lecture du fichier
    if isinstance(path_or_buf, (str, Path)):
        p = Path(path_or_buf)
        with p.open("rb") as fh:
            head = fh.read(4096).decode("utf-8", errors="ignore")
        sep = sniff_sep(head)
        return pd.read_csv(
            p,
            sep=sep,
            dtype=str,
            na_values=["", "NA", "NaN", "nan", "None"],
            engine=engine,
        )
    else:
        # bytes upload (rare ici)
        head = path_or_buf[:4096].decode("utf-8", errors="ignore")
        sep = sniff_sep(head)
        return pd.read_csv(
            io.BytesIO(path_or_buf),
            sep=sep,
            dtype=str,
            na_values=["", "NA", "NaN", "nan", "None"],
            engine=engine,
        )

def save_report(report: dict, out_path: Path = Path("reports/data_quality_report.json")):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import json, numpy as np
    def safe(o):
        if isinstance(o, (np.generic,)):
            return o.item()
        return o
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=safe))

def load_parquet_cached(csv_path: Path, parquet_path: Path) -> pd.DataFrame:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    if parquet_path.exists() and parquet_path.stat().st_mtime > csv_path.stat().st_mtime:
        return pd.read_parquet(parquet_path)
    df = read_csv_flexible(csv_path)
    try:
        df.to_parquet(parquet_path, engine="pyarrow", compression="zstd", index=False)
    except Exception:
        pass
    return df
