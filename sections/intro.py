import streamlit as st

def render():
    # Title
    st.title("Regional and Demographic Patterns of Disease Prevalence in France")
    st.caption("Source: [data.gouv.fr](https://www.data.gouv.fr/datasets/pathologies-effectif-de-patients-par-pathologie-sexe-classe-dage-et-territoire-departement-region/community-resources) | Data from 2015 to 2023, updated July 2025")

    # Introduction
    st.markdown("""
    ### 1. Introduction
    Health data is not only about numbers, it tells a real story about populations, behaviors, and inequalities.  
    This study aims to explore the distribution and evolution of disease prevalence across French regions, age groups, and sexes using [open data from the national health insurance system](https://www.data.gouv.fr/datasets/pathologies-effectif-de-patients-par-pathologie-sexe-classe-dage-et-territoire-departement-region/community-resources).

    The dataset provides aggregated statistics on the number of patients treated for various **pathologies**, along with their **age, sex, and geographical location**.  
    It also includes computed **prevalence rates**, representing the proportion of individuals affected by a specific condition within the covered population.
    """)

    # Dataset structure
    st.markdown("""
    ### 2. Dataset Overview
    - **Time coverage:** 2015–2023  
    - **Geographical level:** French regions and departments
    - **Demographics:** age classes (divided into 5-year groups) and sex (1=male, 2=female)  
    - **Health variables:** pathology category (3 levels), number of patients (`Ntop`), population (`Npop`), and prevalence (`prev`)  

    All variables are described in detail in the Overview tab.
    """)

    # Main research question
    st.markdown("""
    ## How do long-term disease prevalence patterns vary across French regions and demographics, and what trends can be observed between 2015 and 2023?
    """)

    # Study goals
    st.markdown("""
    ### 4. Study Objectives
    1. **Describe** the evolution of overall disease prevalence over time.  
    2. **Compare** regional disparities and identify areas with significantly higher or lower rates.  
    3. **Analyze** how prevalence changes by age and sex for key pathologies.  
    4. **Interpret** these patterns to highlight potential inequalities or public health priorities.
    """)

    # Technical note
    st.markdown("""
    ### 5. Technical Notes
    - Data cleaning includes normalization of columns, type casting, and replacement of missing values.  
    - Aggregations are performed on regional and national levels.  
    - Visualizations are interactive and can be filtered dynamically.
    """)