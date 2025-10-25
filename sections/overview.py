# sections/overview.py
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from utils.prep import population_union_for_year, population_union_by_year, population_union_audit

def _ensure_year(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.year.astype("Int64")
    return pd.to_numeric(series, errors="coerce").astype("Int64")

def render(tables: dict):

    dq   = tables.get("dq", {}) if isinstance(tables, dict) else {}
    fine = tables.get("fine")

    # KPIs
    st.header("Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows (current data)", f"{dq.get('rows', 0):,}".replace(",", " "))
    c2.metric("Regions", f"{dq.get('regions', 0)}")
    c3.metric("Departments", f"{dq.get('departments', 0)}")

    if isinstance(fine, pd.DataFrame):
        pop_2023 = population_union_for_year(fine, 2023, method="median")   # or "min"
        c4.metric("Total analyzed population (union of Npop, 2023)", f"{int(pop_2023):,}".replace(",", " "))
    else:
        c4.metric("Total analyzed population (union of Npop, 2023)", "—")

    # Total analyzed population by year
    st.header("Trends")

    st.markdown("""
#### Understanding the overall dynamics
How many people are covered by this national health dataset each year?  
Has the analyzed population grown over time?  
The chart below answers these questions by showing the evolution of the total analyzed population.
""")
    st.subheader("Total analyzed population by year")
    if isinstance(fine, pd.DataFrame):
        pop_trend = population_union_by_year(fine, method="median")
        if len(pop_trend) > 0:
            fig_pop = px.line(pop_trend, x="annee", y="npop_union", markers=True)
            fig_pop.update_layout(xaxis_title="Year", yaxis_title="Union of Npop")
            st.plotly_chart(fig_pop, use_container_width=True)
        else:
            st.info("No population trend available (insufficient columns or empty data).")
    else:
        st.info("No population trend available (missing fine table).")

    # Prevalence by sex 
    st.markdown("""
### Is there disparities ? (point of view by sex)
Men and women do not experience diseases in the same way.  
In the next steps, we’ll examine how other factors, like age and location, might also shape these health trends.           
But first, let’s look at prevalence differences between sexes in this graph.
                
While biological differences play a role, social and behavioral factors (like preventive care, lifestyle, and occupational exposure) also influence prevalence rates.  
""")

    st.subheader("Average prevalence over time by sex")
    if isinstance(fine, pd.DataFrame) and {"annee", "sexe", "prev"}.issubset(fine.columns):
        df = fine.copy()
        df["annee"] = _ensure_year(df["annee"])
        df["prev"]  = pd.to_numeric(df["prev"], errors="coerce")

        sex_ts = (
            df.dropna(subset=["annee", "sexe", "prev"])
              .groupby(["annee", "sexe"], observed=False, as_index=False)["prev"]
              .mean()
              .rename(columns={"prev": "Average prevalence"})
              .sort_values(["annee", "sexe"])
        )
        if len(sex_ts) > 0:
            fig_sex = px.line(sex_ts, x="annee", y="Average prevalence", color="sexe", markers=True)
            fig_sex.update_layout(xaxis_title="Year", yaxis_title="Average prevalence")
            st.plotly_chart(fig_sex, use_container_width=True)
        else:
            st.info("No sex-based trend available for the current data.")
    else:
        st.info("No sex-based trend available (required columns missing).")

    # Variables
    st.markdown("### Variables description")
    st.markdown("""
- annee: This is the reference year of the data.

- patho_niv1: This is the main category of the pathology or treatment. Example: "Cardioneurovascular diseases".

- patho_niv2: This is a more specific subcategory of the pathology. Example: "Valvular disease".

- patho_niv3: This is the most detailed level of the pathology or treatment (often identical to patho_niv2 if no further subdivision exists). Example: "Valvular disease".

- cla_age_5: This is the coded age group, usually grouped in 5-year intervals. Example: "75-79".

- sexe: This is the sex code: 1 = male, 2 = female (generally).

- region: This is the code of the administrative region.

- dept: This is the code of the administrative department.

- Ntop: This is the number of patients treated for this pathology in the area. Values <11 are masked as "NS" (Not Significant) to protect confidentiality.

- Npop: This is the total reference population for the area and age group.

- prev: This is the prevalence, i.e., the percentage of patients affected by the pathology within the reference population.
                

Those variables form the core of the dataset were deleted because they were useless for the analysis: 
- top: This is an internal unique code used to identify the pathology or treatment in the mapping. Example: "MCV_MVA_IND".

- Niveau prioritaire: This indicates the priority level or internal hierarchical category, often used for data visualization (e.g., "2,3").

- libelle_classe_age: This is the readable label for the age class. Example: "from 75 to 79 years old".

- libelle_sexe: This is the readable label for sex. Example: "men" or "women".

- tri: This is a sorting variable used for display or ranking in visualizations.
    """)

    st.header("Data Quality")

    if isinstance(fine, pd.DataFrame) and len(fine) > 0:
        df = fine.copy()

        # Normalize key numeric columns
        for col in ["npop", "ntop", "prev"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Year as numeric (Int64)
        if "annee" in df.columns:
            df["annee"] = _ensure_year(df["annee"])

        # 1) Missingness overview (top 12 columns with highest missing rate)
        miss = df.isna().mean().sort_values(ascending=False).reset_index()
        miss.columns = ["column", "missing_rate"]
        top_miss = miss.head(12)

        st.subheader("Missingness overview")
        if len(top_miss) > 0:
            fig_miss = px.bar(
                top_miss,
                x="column",
                y="missing_rate",
                text_auto=".0%",
                title=None
            )
            fig_miss.update_layout(
                xaxis_title="Column",
                yaxis_title="Missing rate",
                margin=dict(l=0, r=0, t=0, b=0)
            )
            fig_miss.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_miss, use_container_width=True)
            with st.expander("Full missingness table"):
                st.dataframe(miss, use_container_width=True)
        else:
            st.info("No missing values detected.")

        # 2) Value range checks (prev in [0,100], ntop/npop non-negative)
        st.subheader("Range checks")
        issues = []

        if "prev" in df.columns:
            prev_invalid = df["prev"].dropna()
            n_out = int(((prev_invalid < 0) | (prev_invalid > 100)).sum())
            if n_out > 0:
                issues.append(f"- `prev`: {n_out:,} values outside [0, 100].")
        if "npop" in df.columns:
            n_npop_neg = int((df["npop"].dropna() < 0).sum())
            if n_npop_neg > 0:
                issues.append(f"- `npop`: {n_npop_neg:,} negative values.")
        if "ntop" in df.columns:
            n_ntop_neg = int((df["ntop"].dropna() < 0).sum())
            if n_ntop_neg > 0:
                issues.append(f"- `ntop`: {n_ntop_neg:,} negative values.")

        if issues:
            st.markdown("**Potential range issues detected:**")
            st.markdown("\n".join(issues))
        else:
            st.success("No range issues detected on `prev`, `npop`, or `ntop`.")

        # 3) Year coverage (gaps)
        st.subheader("Year coverage")
        if "annee" in df.columns and df["annee"].notna().any():
            years = sorted(df["annee"].dropna().astype(int).unique().tolist())
            y_min, y_max = min(years), max(years)
            full_span = set(range(y_min, y_max + 1))
            missing_years = sorted(full_span.difference(years))
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Min year", f"{y_min}")
            with c2:
                st.metric("Max year", f"{y_max}")
            if missing_years:
                st.warning(f"Gaps in coverage: {', '.join(map(str, missing_years))}")
            else:
                st.success("No gaps detected in year coverage.")
        else:
            st.info("No year information available to assess coverage.")

        # 4) Simple consistency signals
        st.subheader("Consistency signals")
        notes = []

        # Prevalence implied by ntop/npop (spot-check median relative error)
        if {"ntop", "npop", "prev"}.issubset(df.columns):
            chk = df.dropna(subset=["ntop", "npop", "prev"]).copy()
            chk = chk[chk["npop"] > 0]
            if len(chk) > 0:
                # prev is in percent; expected_prev = ntop/npop * 100
                chk["prev_expected"] = (chk["ntop"] / chk["npop"]) * 100.0
                rel_err = np.abs(chk["prev"] - chk["prev_expected"]) / np.where(chk["prev_expected"] != 0, chk["prev_expected"], np.nan)
                med_rel_err = np.nanmedian(rel_err) if np.isfinite(rel_err).any() else np.nan
                if np.isfinite(med_rel_err):
                    notes.append(f"- Median relative error between reported `prev` and `ntop/npop*100`: ~{med_rel_err*100:.1f}% (lower is better).")
        # Region vs department population order-of-magnitude sanity (optional)
        if {"region", "npop"}.issubset(df.columns):
            reg_pop = df.dropna(subset=["region", "npop"]).groupby("region", as_index=False)["npop"].sum()
            if len(reg_pop) > 0:
                top_reg = reg_pop.sort_values("npop", ascending=False).head(1).iloc[0]
                notes.append(f"- Largest region by population in the dataset: **{top_reg['region']}** (~{int(top_reg['npop']):,}).")

        if notes:
            for n in notes:
                st.markdown(n)
        else:
            st.info("No additional consistency notes available for the current dataset.")
    else:
        st.info("No fine-grained table available to assess data quality.")

    st.markdown("""
    ---
    ### Insights and next steps
    The trends suggest that France’s healthcare data is not static ; it reflects population aging, improved diagnosis, and better chronic disease management.  
    In the next sections, we’ll dive deeper into **regional disparities**, **specific disease categories**, and **possible demographic drivers** of these patterns.
    """)
