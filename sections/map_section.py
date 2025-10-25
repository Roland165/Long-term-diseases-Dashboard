# sections/map_section.py
from pathlib import Path
import json
import re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

def _ensure_year(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.year.astype("Int64")
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _safe_num(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")


def _zfill_dept(series: pd.Series) -> pd.Series:
    """
    Normalize department codes:
    - keep '2A','2B' for Corsica
    - zero-fill numeric codes to 2 or 3 digits (metropole -> 2, DROM -> 3)
    """
    def norm(x):
        s = str(x).strip().upper()
        if s in {"2A", "2B"}:
            return s
        s_digits = re.sub(r"\D", "", s)
        if s_digits == "":
            return s
        n = int(s_digits)
        if 970 <= n <= 989:
            return f"{n:03d}" 
        return f"{n:02d}"
    return series.astype(str).map(norm)


def _zfill_region(series: pd.Series) -> pd.Series:
    """
    Normalize region codes to 2-digit strings (01..84, 93, 94, and 01..06 for DOM).
    """
    def norm(x):
        s = str(x).strip()
        if s == "":
            return s
        if re.fullmatch(r"\d{2}", s):
            return s
        try:
            n = int(float(s))
            return f"{n:02d}"
        except Exception:
            return s  
    return series.astype(str).map(norm)


def _detect_feature_id_key(geojson) -> str:
    """
    Try common property names that store the code we want to match (dept or region).
    Returns a featureidkey string like 'properties.code' usable by plotly.
    """
    cand_props = [
        "code", "id",
        "code_insee", "code_dept", "code_departement", "dep", "departement", "INSEE_DEP", "INSEE_DEP_CODE",
        "code_reg", "code_region", "insee_reg", "INSEE_REG", "REGION"
    ]
    feats = geojson.get("features", [])
    if not feats:
        return ""
    props = feats[0].get("properties", {})
    for k in cand_props:
        if k in props:
            return f"properties.{k}"
    return "properties.code"


def _read_geojson(geo_path: Path):
    if not geo_path.exists():
        return None
    try:
        with geo_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _guess_name_key(geojson) -> str | None:
    for k in ["nom", "name", "libelle", "nom_dep", "nom_reg", "departement", "region", "DEP_NAME", "REG_NAME"]:
        if geojson["features"] and k in geojson["features"][0].get("properties", {}):
            return k
    return None


def _choropleth_or_bar(
    agg: pd.DataFrame,
    code_col: str,
    geo_path: Path,
    map_title: str,
    color_title: str,
    fmt_hover: str,
):
    """
    Generic renderer for dept/region maps with graceful fallback to a ranked bar chart.
    `agg` must contain [code_col, 'value'].
    """
    gj = _read_geojson(geo_path)
    if gj is None:
        st.warning(
            f"GeoJSON not found at `{geo_path.as_posix()}` — showing a ranked bar chart instead. "
            f"Add the appropriate GeoJSON to enable the map."
        )
        if len(agg) > 0:
            agg_sorted = agg.sort_values("value", ascending=False)
            fig_bar = px.bar(agg_sorted, x=code_col, y="value", title=map_title, text_auto=".2s")
            fig_bar.update_layout(xaxis_title=code_col.upper(), yaxis_title=color_title, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)
            st.dataframe(agg_sorted.rename(columns={code_col: code_col.upper(), "value": color_title}), use_container_width=True)
        else:
            st.info("No data after filtering.")
        return

    featureidkey = _detect_feature_id_key(gj)
    name_key = _guess_name_key(gj)
    code_prop = featureidkey.split(".", 1)[-1] if "." in featureidkey else featureidkey

    # lookup table
    gj_rows = []
    for ft in gj.get("features", []):
        props = ft.get("properties", {})
        code = str(props.get(code_prop.replace("properties.", ""), "")).upper()
        if code:
            gj_rows.append({code_col: code, "label_name": props.get(name_key, code)})
    gj_lookup = pd.DataFrame(gj_rows).drop_duplicates(subset=[code_col])

    plot_df = gj_lookup.merge(agg, on=code_col, how="left")

    if len(plot_df) == 0:
        st.info("No feature codes could be matched with your data. Check the code column vs. GeoJSON properties.")
        return

    fig = px.choropleth(
        plot_df,
        geojson=gj,
        locations=code_col,
        featureidkey=featureidkey,
        color="value",
        color_continuous_scale="YlOrRd",
        hover_name="label_name",
        hover_data={code_col: True, "value": True},
        title=None,
        projection="mercator",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title=color_title),
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Code: %{location}<br>Value: %{z"
        + fmt_hover
        + "}<extra></extra>"
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander(f"Data by {code_col}"):
        st.dataframe(
            plot_df[[code_col, "label_name", "value"]]
            .rename(columns={code_col: code_col.upper(), "label_name": "Name", "value": color_title})
            .sort_values(color_title, ascending=False),
            use_container_width=True,
        )


# main render function
def render(df: pd.DataFrame):
    st.header("Map — Department & Region heatmaps")

    # filter
    with st.expander("Filters", expanded=True):
        years = sorted(df["annee"].dropna().astype(int).unique().tolist()) if "annee" in df.columns else []
        if years:
            y_min, y_max = min(years), max(years)
            sel_years = st.slider("Years", y_min, y_max, value=(max(y_min, 2015), y_max), step=1)
        else:
            sel_years = None

        reg_opts = sorted(df["region"].dropna().unique().tolist()) if "region" in df.columns else []
        sel_regions = st.multiselect("Regions (codes)", reg_opts, default=[])

        sex_opts = sorted(df["sexe"].dropna().unique().tolist()) if "sexe" in df.columns else []
        sel_sexe = st.multiselect("Sex (1=male, 2=female, 9=unspecified)", sex_opts, default=[])

        p1_opts = sorted(df["patho_niv1"].dropna().unique().tolist()) if "patho_niv1" in df.columns else []
        sel_p1 = st.multiselect("Pathology (Level 1)", p1_opts, default=[])

        p2_opts = sorted(df["patho_niv2"].dropna().unique().tolist()) if "patho_niv2" in df.columns else []
        sel_p2 = st.multiselect("Pathology (Level 2)", p2_opts, default=[])

        age_opts = sorted(df["cla_age_5"].dropna().unique().tolist()) if "cla_age_5" in df.columns else []
        sel_age = st.multiselect("Age class (5-year groups)", age_opts, default=[])

        metric = st.radio(
            "Color by",
            ["Average prevalence (weighted)", "Cases (sum of Ntop)", "Population (sum of Npop)"],
            horizontal=True,
        )

    # apply filters
    f = df.copy()
    if "annee" in f.columns:
        f["annee"] = _ensure_year(f["annee"])
    if sel_years:
        f = f[(f["annee"] >= sel_years[0]) & (f["annee"] <= sel_years[1])]
    if sel_regions:
        f = f[f["region"].isin(sel_regions)]
    if sel_sexe:
        f = f[f["sexe"].isin(sel_sexe)]
    if sel_p1:
        f = f[f["patho_niv1"].isin(sel_p1)]
    if sel_p2:
        f = f[f["patho_niv2"].isin(sel_p2)]
    if sel_age:
        f = f[f["cla_age_5"].isin(sel_age)]

    _safe_num(f, ["ntop", "npop", "prev"])

    # "Departments" section
    st.subheader("Department heatmap")

    if "dept" not in f.columns:
        st.warning("No `dept` column in data — cannot draw department heatmap.")
    else:
        fd = f.copy()
        fd["dept"] = _zfill_dept(fd["dept"])
        fd = fd[~fd["dept"].isin({"999", "099", "99", "000"})]

        if metric.startswith("Average prevalence"):
            tmp = fd.dropna(subset=["dept", "prev", "npop"]).copy()
            if len(tmp) == 0:
                agg_dept = pd.DataFrame(columns=["dept", "value"])
            else:
                tmp["wprev"] = tmp["prev"] * tmp["npop"]
                agg_dept = (
                    tmp.groupby("dept", as_index=False)
                       .agg(wprev=("wprev", "sum"), w=("npop", "sum"))
                )
                agg_dept["value"] = np.where(agg_dept["w"] > 0, agg_dept["wprev"] / agg_dept["w"], np.nan)
                agg_dept = agg_dept[["dept", "value"]]
            color_title = "Average prevalence (weighted)"
            fmt_hover = ".2f"
        elif metric.startswith("Cases"):
            tmp = fd.dropna(subset=["dept", "ntop"]).copy()
            agg_dept = tmp.groupby("dept", as_index=False)["ntop"].sum().rename(columns={"ntop": "value"})
            color_title = "Cases (sum of Ntop)"
            fmt_hover = ",.0f"
        else:
            tmp = fd.dropna(subset=["dept", "npop"]).copy()
            agg_dept = tmp.groupby("dept", as_index=False)["npop"].sum().rename(columns={"npop": "value"})
            color_title = "Population (sum of Npop)"
            fmt_hover = ",.0f"

        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Filtered rows", f"{len(fd):,}".replace(",", " "))
        c2.metric("Departments with data", f"{agg_dept['dept'].nunique() if len(agg_dept) else 0}")
        if metric.startswith("Average prevalence"):
            c3.metric("Overall (weighted)", f"{(agg_dept['value'] * 1.0).mean():.2f}" if len(agg_dept) else "—")
        else:
            c3.metric("Total", f"{int(agg_dept['value'].sum()):,}".replace(",", " ") if len(agg_dept) else "—")

        _choropleth_or_bar(
            agg=agg_dept,
            code_col="dept",
            geo_path=Path("data/geo/departements.geojson"),
            map_title="Departments",
            color_title=color_title,
            fmt_hover=fmt_hover,
        )

    st.markdown("---")

    # "Regions" section
    st.subheader("Region heatmap")

    if "region" not in f.columns:
        st.warning("No `region` column in data — cannot draw region heatmap.")
        return

    fr = f.copy()
    fr["region"] = _zfill_region(fr["region"])

    if metric.startswith("Average prevalence"):
        tmp = fr.dropna(subset=["region", "prev", "npop"]).copy()
        if len(tmp) == 0:
            agg_reg = pd.DataFrame(columns=["region", "value"])
        else:
            tmp["wprev"] = tmp["prev"] * tmp["npop"]
            agg_reg = (
                tmp.groupby("region", as_index=False)
                   .agg(wprev=("wprev", "sum"), w=("npop", "sum"))
            )
            agg_reg["value"] = np.where(agg_reg["w"] > 0, agg_reg["wprev"] / agg_reg["w"], np.nan)
            agg_reg = agg_reg[["region", "value"]]
        color_title_r = "Average prevalence (weighted)"
        fmt_hover_r = ".2f"
    elif metric.startswith("Cases"):
        tmp = fr.dropna(subset=["region", "ntop"]).copy()
        agg_reg = tmp.groupby("region", as_index=False)["ntop"].sum().rename(columns={"ntop": "value"})
        color_title_r = "Cases (sum of Ntop)"
        fmt_hover_r = ",.0f"
    else:
        tmp = fr.dropna(subset=["region", "npop"]).copy()
        agg_reg = tmp.groupby("region", as_index=False)["npop"].sum().rename(columns={"npop": "value"})
        color_title_r = "Population (sum of Npop)"
        fmt_hover_r = ",.0f"

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Filtered rows", f"{len(fr):,}".replace(",", " "))
    c2.metric("Regions with data", f"{agg_reg['region'].nunique() if len(agg_reg) else 0}")
    if metric.startswith("Average prevalence"):
        c3.metric("Overall (weighted)", f"{(agg_reg['value'] * 1.0).mean():.2f}" if len(agg_reg) else "—")
    else:
        c3.metric("Total", f"{int(agg_reg['value'].sum()):,}".replace(",", " ") if len(agg_reg) else "—")

    _choropleth_or_bar(
        agg=agg_reg,
        code_col="region",
        geo_path=Path("data/geo/regions.geojson"),
        map_title="Regions",
        color_title=color_title_r,
        fmt_hover=fmt_hover_r,
    )
