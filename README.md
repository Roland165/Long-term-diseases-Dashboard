# 🩺 French Health Data Storytelling — Streamlit Dashboard

A data storytelling web application built with Streamlit, Plotly, and Pandas, exploring the French health landscape from open public datasets (pathologies, demographics, and prevalence rates).  

## Overview

This dashboard provides an interactive exploration of:
- The distribution of chronic and acute diseases across France  
- Regional inequalities in prevalence  
- Co-occurrence between major pathologies  
- A detailed focus on cancer trends, age profiles, and key metrics  

It’s designed for students, researchers, and healthcare professionals seeking insightful visual analytics of French public health data.

---

## Try Now

You can access the hosted version here:  
**[https://roland165-long-term-diseases.streamlit.app](https://roland165-long-term-diseases.streamlit.app)**

Or run it locally :
### 1. Clone the repository
```bash
git clone https://github.com/Roland165/Long-term-diseases-Dashboard
cd french-health-storytelling
pip install -r requirements.txt
then download the dataset from https://www.data.gouv.fr/datasets/pathologies-effectif-de-patients-par-pathologie-sexe-classe-dage-et-territoire-departement-region/community-resources
place your csv file in data/
if you want a faster application
    run the Project_jupyter.ipynb 
else
    in the app.py file, change USE_CLEANED = True to False

streamlit run app.py
```
---

## Features

- **Interactive filters** (region, year, sex, age, pathology levels)  
- **Heatmaps** of prevalence by department and region  
- **Treemaps** showing disease landscape  
- **Correlation maps** between chronic pathologies  
- **Cancer-specific analysis** (trends, types, and age distribution)  
- **Narrative conclusion** summarizing insights and policy implications  

---

Project Structure

```
project/
│
├── app.py                     # Main Streamlit entry point
├── data/                      # Data folder (CSV, JSON, GeoJSON)
│   └── geo/                   # Geographic data for maps
│
├── sections/                  # Modular Streamlit sections
│   ├── map_section.py         # Department & region heatmaps
│   ├── deep_dives.py          # Core analytics and correlations
│   ├── conclusion_section.py  # Narrative conclusion
│   └── intro_section.py       # Landing page (optional)
│
├── utils/                     # Data cleaning & helpers
│   ├── io.py                  # Handles data import/export (CSV, JSON, and caching)
│   ├── prep.py                # Cleans and harmonizes datasets
│   └── viz.py                 # Helper functions for reusable Plotly visualizations and styling
│
└── requirements.txt           # Dependencies
```