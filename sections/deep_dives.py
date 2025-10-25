# sections/deep_dives.py
import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------- small helpers ----------
def _ensure_year(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.year.astype("Int64")
    return pd.to_numeric(s, errors="coerce").astype("Int64")

_AGE_BIN_RE = re.compile(
    r"^\s*(\d+)\s*-\s*(\d+)\s*$|^\s*(\d+)\s*\+|^\s*(\d+)\s*et\s*plus\s*$",
    re.IGNORECASE
)

def _age_sort_key(val: str) -> tuple:
    """Return numeric sort key for '0-4','75-79','95+','95 et plus'."""
    s = str(val).strip()
    m = _AGE_BIN_RE.match(s)
    if not m:
        return (999, 999)
    if m.group(1) and m.group(2):  # a-b
        return (int(m.group(1)), int(m.group(2)))
    n = m.group(3) or m.group(4)    # n+ or 'n et plus'
    return (int(n), 200)

def _order_age_bins(series: pd.Series) -> pd.Categorical:
    cats = sorted({str(x) for x in series.dropna().astype(str)}, key=_age_sort_key)
    return pd.Categorical(series.astype(str), categories=cats, ordered=True)

def _safe_num(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

def _note(msg: str):
    st.caption(f"ℹ️ {msg}")

# shorten long labels (keep before '(' or cut at 28 chars)
def _short_label(x: str) -> str:
    base = str(x).split("(")[0].strip()
    return (base[:28] + "…") if len(base) > 28 else base


# ---------- main ----------
def render(df, tables_all):
    st.header("Deep Dives")

    # ===== Sommaire cliquable =====
    st.markdown(
        """
<a id="top"></a>
### On this page
- [1. Filters, Trend & KPIs](#part1)
- [2. Core analyses](#part2)
  - [2.1 Pathology landscape](#sec1)
  - [2.2 Co-occurrences](#sec2)
  - [2.3 Regional outliers](#sec3)
- [3. Focus: Cancers](#part3)
        """,
        unsafe_allow_html=True,
    )

    st.markdown("""
Explore specific **pathologies**, **co-occurrences**, and **regional patterns**.  
Use the filters to focus the story; each chart comes with a short takeaway.
""")

    # ------------------------------------------------------------------
    # PART 1 — Filters + Trend & KPIs
    # ------------------------------------------------------------------
    st.markdown('<a id="part1"></a>', unsafe_allow_html=True)
    st.subheader("1. Filters, Trend & KPIs")

    # ===== Filters =====
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

    # Apply filters safely (INCLUSIVE range)
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
    # Retire quelques agrégats classiques
    if "dept" in f.columns:
        f = f[~f["dept"].isin({"099", "999", "000", "99"})]

    _safe_num(f, ["ntop", "npop", "prev"])

    # ===== Trend (just below Filters) =====
    st.subheader("Trend — Average prevalence over time (current filters)")
    if {"annee", "prev"}.issubset(f.columns) and len(f) > 0:
        ts = (
            f.dropna(subset=["annee", "prev"])
             .groupby("annee", as_index=False)["prev"].mean()
             .rename(columns={"prev": "Average prevalence"})
             .sort_values("annee")
        )
        if len(ts) > 0:
            fig_ts = px.line(ts, x="annee", y="Average prevalence", markers=True)
            fig_ts.update_layout(xaxis_title="Year", yaxis_title="Average prevalence")
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            _note("No trend available after filtering.")
    else:
        _note("Time or prevalence columns not available with current filters.")

    # ===== KPI Strip =====
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Filtered rows", f"{len(f):,}".replace(",", " "))
    c2.metric("Regions", f"{f['region'].nunique() if 'region' in f.columns else 0}")
    c3.metric("Departments", f"{f['dept'].nunique() if 'dept' in f.columns else 0}")
    c4.metric("Avg. prevalence", f"{f['prev'].mean():.2f}" if "prev" in f.columns and len(f) else "—")

    st.markdown('[Back to top](#top)  ', unsafe_allow_html=True)
    st.markdown("---")

    # ------------------------------------------------------------------
    # PART 2 — Core analyses (1,2,3)
    # ------------------------------------------------------------------
    st.markdown('<a id="part2"></a>', unsafe_allow_html=True)
    st.subheader("2. Core analyses")

    # ===== 1) Pathology landscape (Treemap) =====
    st.markdown('<a id="sec1"></a>', unsafe_allow_html=True)
    st.markdown("#### 2.1 What dominates? — Pathology landscape")
    st.markdown("Each rectangle is a pathology group; its area reflects the number of cases (`Ntop`) in the current selection.")
    if {"patho_niv1", "patho_niv2", "ntop"}.issubset(f.columns) and len(f) > 0:
        g = f.dropna(subset=["patho_niv1", "patho_niv2", "ntop"]).copy()
        g = g.groupby(["patho_niv1", "patho_niv2"], as_index=False)["ntop"].sum()
        g = g[g["ntop"] > 0]
        if len(g) > 0:
            fig_tree = px.treemap(g, path=["patho_niv1", "patho_niv2"], values="ntop", hover_data={"ntop": ":,d"})
            fig_tree.update_traces(root_color="rgba(0,0,0,0)")
            fig_tree.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_tree, use_container_width=True)
            top1 = g.sort_values("ntop", ascending=False).iloc[0]
            st.caption(
                f"**Takeaway:** largest block is **{top1['patho_niv1']} → {top1['patho_niv2']}** "
                f"(~{int(top1['ntop']):,} cases)."
            )
        else:
            st.info("No pathology counts for the current filters.")
    else:
        st.info("Pathology columns missing to build the treemap.")

    st.markdown('[Back to top](#top)  ', unsafe_allow_html=True)
    st.markdown("---")

    # ===== 2) How do diseases overlap? =====
    st.markdown('<a id="sec2"></a>', unsafe_allow_html=True)
    st.markdown("#### 2.2 How do diseases overlap? — The web of chronic conditions")
    st.markdown("""
Some chronic diseases frequently appear together.  
Below, we focus on the **top pathology groups** (by total cases) to keep the view readable.
""")

    if {"patho_niv1", "region", "annee"}.issubset(f.columns) and len(f) > 0:
        # --- parameters for readability ---
        top_k = st.slider("Show top N pathology groups (by cases)", 5, 25, 12, step=1)
        min_abs_corr = st.slider("Minimum absolute correlation to annotate", 0.40, 0.95, 0.60, step=0.05)

        # choose top_k pathologies by total cases to reduce noise
        size_by_patho = (
            f.dropna(subset=["patho_niv1"])
             .groupby("patho_niv1", observed=False)["ntop"]
             .sum()
             .sort_values(ascending=False)
        )
        keep = size_by_patho.head(top_k).index.tolist()
        df_small = f[f["patho_niv1"].isin(keep)].copy()

        # pivot: prevalence presence by (region, year, age) -> columns=pathologies
        if {"prev", "cla_age_5"}.issubset(df_small.columns):
            unit = (
                df_small.groupby(["region", "annee", "cla_age_5", "patho_niv1"], observed=False)["prev"]
                        .mean()
                        .unstack(fill_value=0)
            )
        else:
            unit = (
                df_small.groupby(["region", "annee", "patho_niv1"], observed=False)
                        .size()
                        .unstack(fill_value=0)
            )

        # correlation matrix between pathologies
        corr = unit.corr()

        labels_short = [_short_label(c) for c in corr.columns]

        # mask upper triangle for readability
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        corr_masked = corr.mask(mask)

        # heatmap
        fig_hm = px.imshow(
            corr_masked,
            x=labels_short, y=labels_short,
            color_continuous_scale="RdBu", zmin=-1, zmax=1,
            origin="upper", aspect="auto"
        )
        fig_hm.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=520)
        fig_hm.update_xaxes(tickangle=-30, automargin=True)
        fig_hm.update_yaxes(automargin=True)

        # annotate only strong correlations
        annos = []
        for i in range(corr.shape[0]):
            for j in range(corr.shape[1]):
                if j >= i:
                    continue
                val = corr.iat[i, j]
                if pd.isna(val) or abs(val) < min_abs_corr:
                    continue
                annos.append(dict(
                    x=labels_short[j], y=labels_short[i],
                    text=f"{val:.2f}", showarrow=False, font=dict(size=10)
                ))
        fig_hm.update_layout(annotations=annos)
        st.plotly_chart(fig_hm, use_container_width=True)

        # ---- top pairs table + narrative (positive and negative) ----
        c2 = corr.copy()
        c2.index = c2.index.astype(str)
        c2.columns = c2.columns.astype(str)
        c2.index.name = "pA"
        c2.columns.name = "pB"

        corr_long = c2.stack().reset_index(name="corr")  # cols: pA, pB, corr

        # keep only lower triangle using column order (avoids categorical compares)
        col_order = {name: i for i, name in enumerate(list(c2.columns))}
        corr_long["i"] = corr_long["pA"].map(col_order).astype("int64")
        corr_long["j"] = corr_long["pB"].map(col_order).astype("int64")
        corr_long = corr_long[corr_long["i"] < corr_long["j"]].drop(columns=["i", "j"])

        # positive top
        top_pairs = corr_long.sort_values("corr", ascending=False).head(10)
        # negative strongest
        neg_pair = corr_long.sort_values("corr", ascending=True).head(1)

        # shorten labels for display
        top_pairs_display = top_pairs.copy()
        top_pairs_display["pA"] = top_pairs_display["pA"].map(_short_label)
        top_pairs_display["pB"] = top_pairs_display["pB"].map(_short_label)

        st.markdown("**Top co-occurring pathology pairs** (by correlation)")
        st.dataframe(
            top_pairs_display.rename(columns={"pA": "Pathology A", "pB": "Pathology B", "corr": "Correlation"}),
            use_container_width=True
        )

        # automatic commentary below the heatmap
        pos_txt = "—"
        if len(top_pairs) > 0:
            a, b, cval = top_pairs.iloc[0]["pA"], top_pairs.iloc[0]["pB"], float(top_pairs.iloc[0]["corr"])
            pos_txt = f"strongest **positive** link: **{_short_label(a)}** with **{_short_label(b)}** (corr ≈ {cval:.2f})."

        neg_txt = ""
        if len(neg_pair) > 0 and not np.isnan(neg_pair.iloc[0]["corr"]):
            na, nb, nval = neg_pair.iloc[0]["pA"], neg_pair.iloc[0]["pB"], float(neg_pair.iloc[0]["corr"])
            neg_txt = f" The most **negative** association is **{_short_label(na)}** vs **{_short_label(nb)}** (corr ≈ {nval:.2f})."

        st.markdown(
            f"*Reading the map:* darker blue blocks indicate conditions that tend to rise together across the same age/region/year slices; red indicates divergence. In the current selection, the {pos_txt}{neg_txt}"
        )
    else:
        st.info("Not enough data to compute co-occurrence between diseases.")

    st.markdown('[Back to top](#top)  ', unsafe_allow_html=True)
    st.markdown("---")

    # ===== 3) Where is it unusual? — Regional outliers =====
    st.markdown('<a id="sec3"></a>', unsafe_allow_html=True)
    st.markdown("#### 2.3 Where is it unusual? — Regional outliers")
    st.markdown("Average prevalence vs population base by region. Regions above the median line combine **large populations** with **high prevalence** and deserve attention.")

    if {"region", "prev", "npop"}.issubset(f.columns) and len(f) > 0:
        r = f.dropna(subset=["region", "prev", "npop"]).copy()
        r = (r.groupby("region", as_index=False)
               .agg(avg_prev=("prev", "mean"), pop=("npop", "sum")))
        r = r[r["pop"] > 0]

        med_prev = float(r["avg_prev"].median()) if len(r) else np.nan

        fig_sc = px.scatter(
            r, x="pop", y="avg_prev", hover_name="region",
            size="pop", size_max=28
        )
        # add median reference line
        fig_sc.add_shape(
            type="line",
            x0=r["pop"].min(), x1=r["pop"].max(),
            y0=med_prev, y1=med_prev,
            line=dict(dash="dash")
        )
        fig_sc.update_layout(
            xaxis_title="Population base (sum of Npop, filtered)",
            yaxis_title="Average prevalence",
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_sc, use_container_width=True)

        top_reg = r.sort_values("avg_prev", ascending=False).head(3)
        names = ", ".join(top_reg["region"].astype(str).tolist())
        st.caption(f"**Takeaway:** highest prevalence (given current filters) in: **{names}**.")
    else:
        st.info("Need `region`, `prev`, and `npop` to assess regional outliers.")

    st.markdown('[Back to top](#top)  ', unsafe_allow_html=True)
    st.markdown("---")

    # ------------------------------------------------------------------
    # PART 3 — Focus: Cancers
    # ------------------------------------------------------------------
    st.markdown('<a id="part3"></a>', unsafe_allow_html=True)
    st.subheader("3. Focus — Cancers")

    # Try to detect cancer rows (niv1 or niv2 contains 'cancer')
    cancer_mask = pd.Series(False, index=f.index)
    for col in ["patho_niv1", "patho_niv2"]:
        if col in f.columns:
            cancer_mask = cancer_mask | f[col].astype(str).str.contains("cancer", case=False, na=False)
    fc = f[cancer_mask].copy()

    if len(fc) == 0:
        st.info("No cancer-related rows in the current selection.")
        return

    # 3a) Trend of cancer cases (Ntop) and prevalence
    cols = st.columns(2)
    with cols[0]:
        if {"annee", "ntop"}.issubset(fc.columns):
            ts_cases = (
                fc.dropna(subset=["annee", "ntop"])
                  .groupby("annee", as_index=False)["ntop"].sum()
                  .rename(columns={"ntop": "Cancer cases"})
                  .sort_values("annee")
            )
            if len(ts_cases) > 0:
                fig_c1 = px.line(ts_cases, x="annee", y="Cancer cases", markers=True)
                fig_c1.update_layout(xaxis_title="Year", yaxis_title="Cases (Ntop)")
                st.plotly_chart(fig_c1, use_container_width=True)

    with cols[1]:
        if {"annee", "prev"}.issubset(fc.columns):
            ts_prev = (
                fc.dropna(subset=["annee", "prev"])
                  .groupby("annee", as_index=False)["prev"].mean()
                  .rename(columns={"prev": "Cancer prevalence"})
                  .sort_values("annee")
            )
            if len(ts_prev) > 0:
                fig_c2 = px.line(ts_prev, x="annee", y="Cancer prevalence", markers=True)
                fig_c2.update_layout(xaxis_title="Year", yaxis_title="Average prevalence")
                st.plotly_chart(fig_c2, use_container_width=True)

    # 3b) Most detected cancers (by cases)
    #    Aggregate by pathology level 2 when available, else by level 1.
    target_col = "patho_niv2" if "patho_niv2" in fc.columns else "patho_niv1"
    if {target_col, "ntop"}.issubset(fc.columns):
        top_types = (
            fc.dropna(subset=[target_col, "ntop"])
              .groupby(target_col, as_index=False)["ntop"].sum()
              .sort_values("ntop", ascending=False)
              .head(20)
        )
        if len(top_types) > 0:
            fig_top = px.bar(
                top_types,
                x=target_col,
                y="ntop",
                text_auto=".2s",
                title="Cancer — most detected (cases)"
            )
            fig_top.update_layout(xaxis_title="Cancer type", yaxis_title="Cases (Ntop)", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_top, use_container_width=True)

    # 3c) Age profile of cancer burden — readable scale with side-by-side controls
    st.markdown("**Cancer — age profile**")
    colA, colB = st.columns([1, 1])
    with colA:
        scale = st.radio("Y-axis", ["Auto", "Log (base 10)", "Clip to 99th percentile"], horizontal=False)
    with colB:
        metric_choice = st.radio("Metric", ["Cases (Ntop)", "Rate per 100k", "Share of total (%)"], horizontal=False)

    if {"cla_age_5"}.issubset(fc.columns) and len(fc) > 0:
        # order age bins
        fc["cla_age_5"] = _order_age_bins(fc["cla_age_5"])

        # base aggregation
        grp = fc.groupby("cla_age_5", as_index=False).agg(
            ntop=("ntop", "sum"),
            npop=("npop", "sum")
        )

        # compute the selected metric
        if metric_choice == "Cases (Ntop)":
            grp["value"] = grp["ntop"]
            y_title = "Cases (Ntop)"
            text_fmt = ".2s"
        elif metric_choice == "Rate per 100k":
            grp["value"] = np.where(grp["npop"] > 0, grp["ntop"] / grp["npop"] * 1e5, np.nan)
            y_title = "Rate per 100k"
            text_fmt = ".1f"
        else:  # Share of total (%)
            tot = grp["ntop"].sum()
            grp["value"] = np.where(tot > 0, grp["ntop"] / tot * 100.0, np.nan)
            y_title = "Share of total (%)"
            text_fmt = ".1f"

        # build the bar chart
        fig_age = px.bar(grp, x="cla_age_5", y="value", text_auto=text_fmt)

        # axis behaviour
        if scale == "Log (base 10)":
            fig_age.update_yaxes(type="log")
        elif scale == "Clip to 99th percentile":
            q = np.nanquantile(grp["value"], 0.99) if grp["value"].notna().any() else None
            if q and np.isfinite(q):
                fig_age.update_yaxes(range=[0, float(q * 1.05)])

        fig_age.update_layout(
            title=f"Cancer — age profile ({metric_choice.lower()})",
            xaxis_title="Age class (5y)",
            yaxis_title=y_title,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_age, use_container_width=True)
    else:
        st.info("No age information available for the current cancer selection.")

    # --------- Footnote ---------
    st.markdown("""
---
**Reading guide**  
- *Ntop* = number of cases; *Npop* = reference population; *prev* = prevalence (%).  
- Some aggregated lines (e.g., `dept=999`) are excluded elsewhere to avoid double counting.
""")
