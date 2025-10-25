# utils/prep.py — normalise "clean" vs "raw" et prépare les tables

import pandas as pd

def _to_float(x):
    if pd.isna(x):
        return pd.NA
    s = str(x).strip().replace(",", ".")
    try:
        return float(s)
    except:
        return pd.NA

def harmonize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (df.columns
        .str.strip().str.lower().str.replace(" ", "_")
        .str.replace("é","e").str.replace("è","e").str.replace("ê","e")
        .str.replace("à","a").str.replace("ô","o").str.replace("œ","oe"))
    return df

# utils/prep.py (ajouter)
def _downcast_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], errors="coerce", downcast="float")
    for col in df.select_dtypes(include=["int64","Int64"]).columns:
        # garde Int64 si NaN nécessaires, sinon int32
        if str(df[col].dtype) == "Int64":
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce", downcast="integer")
    return df

def _categorize(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


# effectifs_cleaned.csv
def coerce_cleaned(df: pd.DataFrame) -> pd.DataFrame:
    df = harmonize_columns(df)

    # annee: accepte '2023-01-01' ou '2023'
    if "annee" in df.columns:
        df["annee"] = pd.to_datetime(df["annee"], errors="coerce").dt.year.astype("Int64")

    # strings usuelles
    for col in ["region","dept","top","cla_age_5","patho_niv1","patho_niv2","patho_niv3",
                "libelle_classe_age","libelle_sexe","niveau_prioritaire"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    # normalise dept sur 3 chiffres (évite '99' vs '099')
    if "dept" in df.columns:
        df["dept"] = df["dept"].astype("string").str.strip().str.zfill(3)

    # sexe
    if "sexe" in df.columns:
        df["sexe"] = pd.to_numeric(df["sexe"], errors="coerce").astype("Int64")

    # numériques
    for col in ["ntop","npop","prev","tri"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = _downcast_numeric(df)
    df = _categorize(df, ["region","dept","top","cla_age_5","patho_niv1","patho_niv2","patho_niv3","libelle_classe_age","libelle_sexe"])
    return df

# effectifs.csv
def clean_raw(df: pd.DataFrame) -> pd.DataFrame:
    df = harmonize_columns(df)

    # annee en Int
    if "annee" in df.columns:
        df["annee"] = pd.to_datetime(df["annee"], errors="coerce").dt.year.astype("Int64")

    # strings
    for col in ["region","dept","top","cla_age_5","patho_niv1","patho_niv2","patho_niv3",
                "libelle_classe_age","libelle_sexe","niveau_prioritaire"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    # normalise dept sur 3 chiffres (évite '99' vs '099')
    if "dept" in df.columns:
        df["dept"] = df["dept"].astype("string").str.strip().str.zfill(3)

    # sexe
    if "sexe" in df.columns:
        df["sexe"] = pd.to_numeric(df["sexe"], errors="coerce").astype("Int64")

    # numériques avec virgule potentielle
    for col in ["ntop","npop","prev","tri"]:
        if col in df.columns:
            df[col] = df[col].map(_to_float)

    if "annee" in df.columns:
        df = df[df["annee"].between(2000, 2100) | df["annee"].isna()]

    key_cols = [c for c in ["annee","region","dept","prev"] if c in df.columns]
    if key_cols:
        df = df.dropna(subset=key_cols, how="all")

    df = _downcast_numeric(df)
    df = _categorize(df, ["region","dept","top","cla_age_5","patho_niv1","patho_niv2","patho_niv3","libelle_classe_age","libelle_sexe"])
    return df

import re
import pandas as pd

_AGE_5Y_PATTERN = re.compile(
    r"^\s*\d{1,2}\s*-\s*\d{1,2}\s*$|^\s*\d{1,2}\s*\+\s*$|^\s*\d{2}\s*et\s*plus\s*$",
    flags=re.IGNORECASE
)

def _ensure_year(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.year.astype("Int64")
    return pd.to_numeric(series, errors="coerce").astype("Int64")

def _filter_population_scope(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "annee" in out.columns:
        out["annee"] = _ensure_year(out["annee"])
    if "dept" in out.columns:
        out["dept"] = out["dept"].astype(str).str.zfill(3)
        out = out[out["dept"] != "999"]  # remove aggregates only
    if "cla_age_5" in out.columns:
        out = out[out["cla_age_5"].astype(str).str.strip().str.len() > 0]
        out = out[out["cla_age_5"].astype(str).apply(lambda s: bool(_AGE_5Y_PATTERN.search(s)))]
    return out

def _dedup_npop_per_slice(tmp: pd.DataFrame, method: str = "median") -> pd.Series:

    tmp = tmp.copy()
    agg = {"median": "median", "min": "min", "max": "max", "first": "first"}[method]
    if "cla_age_5" in tmp.columns:
        return tmp.groupby(["dept", "cla_age_5"], observed=False)["npop"].agg(agg)
    else:
        return tmp.groupby(["dept"], observed=False)["npop"].agg(agg)

def population_union_for_year(df: pd.DataFrame, year: int, method: str = "median") -> float:
    required = {"annee", "dept", "npop"}
    if not required.issubset(df.columns):
        return float("nan")

    tmp = _filter_population_scope(df)
    tmp = tmp[tmp["annee"] == year]
    if tmp.empty:
        return float("nan")

    tmp["npop"] = pd.to_numeric(tmp["npop"], errors="coerce")
    tmp = tmp.dropna(subset=["npop"])

    dedup = _dedup_npop_per_slice(tmp, method=method)
    return float(dedup.sum())

def population_union_by_year(df: pd.DataFrame, method: str = "median") -> pd.DataFrame:
    required = {"annee", "dept", "npop"}
    if not required.issubset(df.columns):
        return pd.DataFrame(columns=["annee", "npop_union"])

    tmp = _filter_population_scope(df)
    tmp["npop"] = pd.to_numeric(tmp["npop"], errors="coerce")
    tmp = tmp.dropna(subset=["annee", "npop"])
    if tmp.empty:
        return pd.DataFrame(columns=["annee", "npop_union"])

    if "cla_age_5" in tmp.columns:
        dedup = (tmp.groupby(["annee", "dept", "cla_age_5"], observed=False)["npop"]
                   .agg(method)
                   .reset_index())
    else:
        dedup = (tmp.groupby(["annee", "dept"], observed=False)["npop"]
                   .agg(method)
                   .reset_index())

    out = (dedup.groupby("annee", observed=False)["npop"]
              .sum()
              .reset_index(name="npop_union")
              .sort_values("annee"))
    return out

def population_union_audit(df: pd.DataFrame, year: int) -> dict:
    required = {"annee", "dept", "npop"}
    if not required.issubset(df.columns):
        return {"slices": 0, "multi_values": 0}

    tmp = _filter_population_scope(df)
    tmp = tmp[tmp["annee"] == year]
    tmp["npop"] = pd.to_numeric(tmp["npop"], errors="coerce")
    tmp = tmp.dropna(subset=["npop"])
    if tmp.empty:
        return {"slices": 0, "multi_values": 0}

    if "cla_age_5" in tmp.columns:
        counts = (tmp.groupby(["dept", "cla_age_5"], observed=False)["npop"]
                    .nunique()
                    .reset_index(name="n_unique"))
    else:
        counts = (tmp.groupby(["dept"], observed=False)["npop"]
                    .nunique()
                    .reset_index(name="n_unique"))
    multi = int((counts["n_unique"] > 1).sum())
    return {"slices": int(len(counts)), "multi_values": multi}


# tables for viz
def make_tables(df: pd.DataFrame) -> dict:
    out = {}

    # Ensure numeric dtypes for aggregations
    for c in ["ntop", "npop", "prev"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 0) Fine (narrow) table for fast re-aggregation in pages
    fine_dims = [c for c in ["annee", "region", "dept", "sexe", "cla_age_5"] if c in df.columns]
    keep_cols = [c for c in ["ntop", "npop", "prev"] if c in df.columns]
    if fine_dims and keep_cols:
        out["fine"] = df[fine_dims + keep_cols].copy()

    # 1) Timeseries: prevalence over time (mean prev per year)
    if set(["annee", "prev"]).issubset(df.columns):
        out["timeseries"] = (
            df.dropna(subset=["annee", "prev"])
              .groupby("annee", observed=False, as_index=False)["prev"]
              .mean()
              .rename(columns={"prev": "prev_moy"})
              .sort_values("annee")
        )

    # 2) By region (unweighted average prevalence)
    if set(["region", "prev"]).issubset(df.columns):
        out["by_region"] = (
            df.dropna(subset=["region", "prev"])
              .groupby("region", observed=False, as_index=False)["prev"]
              .mean()
              .rename(columns={"prev": "prev_moy"})
              .sort_values("prev_moy", ascending=False)
        )

    # 2b) By region (weighted by Npop) if available
    if set(["region", "prev", "npop"]).issubset(df.columns):
        tmp = df.dropna(subset=["region", "prev", "npop"]).copy()
        tmp["w"] = tmp["npop"]
        tmp["wp"] = tmp["prev"] * tmp["w"]
        by_reg_w = (
            tmp.groupby("region", observed=False, as_index=False)
               .agg(prev_pond=("wp", "sum"), w=("w", "sum"))
        )
        by_reg_w["prev_pond"] = by_reg_w["prev_pond"] / by_reg_w["w"]
        out["by_region_weighted"] = by_reg_w.sort_values("prev_pond", ascending=False)

    # 3) By sex (descriptive stats on prevalence)
    if set(["sexe", "prev"]).issubset(df.columns):
        out["by_sexe_desc"] = (
            df.dropna(subset=["sexe", "prev"])
              .groupby("sexe", observed=False)["prev"]
              .describe()
              .reset_index()
        )

    # 4) Data quality / summary
    regions_n = int(df["region"].dropna().nunique()) if "region" in df.columns else 0
    depts_n   = int(df["dept"].dropna().nunique()) if "dept" in df.columns else 0

    try:
        pop_union_2023 = population_union_for_year(df, 2023, method="median")
    except Exception:
        pop_union_2023 = float("nan")

    out["dq"] = {
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "regions": regions_n,
        "departments": depts_n,
        # keep both key names for compatibility
        "population_union_npop": pop_union_2023,
        "population_union_npop_2023": pop_union_2023,
        "annees": sorted([int(x) for x in df["annee"].dropna().unique().tolist()]) if "annee" in df.columns else [],
        "has_weight": bool("npop" in df.columns),
        "has_sex": bool("sexe" in df.columns),
        "cols_list": list(df.columns),
    }

    return out
