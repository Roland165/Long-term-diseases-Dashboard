import os, sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

# Local imports
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from utils.io import read_csv_flexible, load_parquet_cached, save_report
from utils.prep import clean_raw, coerce_cleaned, make_tables
from sections import intro, overview, deep_dives, conclusions
from sections import map_section  # optional map section

# config Streamlit page
st.set_page_config(page_title="Long-term diseases Dashboard", layout="wide")

# Data source (code-configured)
USE_CLEANED = True  # True => effectifs_cleaned.csv ; False => effectifs.csv
DATA_PATH_CLEAN = Path("data/effectifs_cleaned.csv")
DATA_PATH_RAW = Path("data/effectifs.csv")
DATA_PATH = DATA_PATH_CLEAN if USE_CLEANED else DATA_PATH_RAW
DATA_IS_ALREADY_CLEAN = USE_CLEANED

# load & prepare data with caching
@st.cache_data(show_spinner=False)
def load_and_prepare(data_path: str, already_clean: bool):
    p = Path(data_path)
    parquet_path = Path("data_cache") / (p.stem + ".parquet")
    raw = load_parquet_cached(p, parquet_path)
    df = coerce_cleaned(raw) if already_clean else clean_raw(raw)
    tables = make_tables(df)
    return df, tables, p.name

df, tables_all, meta = load_and_prepare(str(DATA_PATH), DATA_IS_ALREADY_CLEAN)

#sidebar styling
st.markdown("""
<style>
/* Fond de la sidebar neutre (noir/gris foncé si thème dark) */
[data-testid="stSidebar"] {
  padding-top: 1.25rem;
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

/* Titre sidebar (optionnel) */
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
  font-weight: 600;
}

/* Groupe radio vertical, sans espacements excessifs */
div[role="radiogroup"] {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: .25rem;
}

/* OPTION: reset complet – pas de box, juste du texte */
div[role="radiogroup"] > label {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 6px 2px !important;
  margin: 0 !important;
  border-radius: 0 !important;
  cursor: pointer;
  color: inherit !important;
  font-weight: 500;
  position: relative;
  transition: color .2s ease, transform .2s ease;
}

/* Cacher la pastille du radio */
div[role="radiogroup"] > label > div:first-child {
  display: none !important;
}

/* Hover: légère translation + couleur discrète (utilise la couleur du thème) */
div[role="radiogroup"] > label:hover {
  transform: translateX(2px);
  opacity: 0.95;
}

/* Soulignement animé (ligne fine sous l’item) */
div[role="radiogroup"] > label::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -4px;
  height: 2px;
  width: 0%;
  background: currentColor; /* reprend la couleur du texte */
  opacity: 0.7;
  transition: width .22s ease;
}

/* Au survol: on prévisualise un petit soulignement */
div[role="radiogroup"] > label:hover::after {
  width: 35%;
}

/* Actif: soulignement complet + légère emphase */
div[role="radiogroup"] > label[data-checked="true"] {
  font-weight: 600 !important;
}
div[role="radiogroup"] > label[data-checked="true"]::after {
  width: 100%;
  opacity: 1;
}
</style>
""", unsafe_allow_html=True)


st.sidebar.markdown("<h1>Long-term diseases Dashboard</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border: 1px solid #30363d;'>", unsafe_allow_html=True)

# Modernized navigation labels
nav_options = {
    "Introduction": "Introduction",
    "Overview": "📈 Overview",
    "Deep Dives": "🔍 Deep Dives",
    "Map": "🗺️ Map",
    "Conclusion": "Conclusion"
}

page = st.sidebar.radio(" ", list(nav_options.values()))

# Map icon labels back to real page names
page_key = [k for k, v in nav_options.items() if v == page][0]


# route to the selected page
if page_key == "Introduction":
    st.title("Introduction")
    intro.render()

elif page_key == "Overview":
    st.title("Overview")
    overview.render(tables_all)

elif page_key == "Deep Dives":
    st.title("Deep Dives")
    deep_dives.render(df, tables_all)


elif page_key == "Map":
    st.title("Map")
    map_section.render(df)


elif page_key == "Conclusion":
    conclusions.render()

