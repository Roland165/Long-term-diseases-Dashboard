import streamlit as st
import plotly.express as px

def render():
    st.header("Conclusion | Understanding the French Health Landscape")

    st.markdown("""
### Key takeaways

1. Chronic diseases dominate the medical landscape, especially cardiovascular and metabolic disorders.
   - These pathologies represent the largest share of treated patients, far exceeding episodic conditions.
   - Mental health disorders and cancers, while less frequent overall, show strong co-occurrence patterns, sign of complex multimorbidity.

2. Regional inequalities remain significant.
   - Even after normalizing for population, certain regions (notably *Mayotte*, *Corse* and *Guyane*) maintain higher average prevalence rates.
   - These differences likely reflect both demographic structures (older populations in some areas) and access to specialized care.

3. Cancer data reveal dual realities.
   - The weighted prevalence highlights that some cancers (breast, prostate, colorectal) still dominate the health burden.
   - The age profile confirms that incidence rises sharply after 60 years old, but younger kids are not immune.

---

### Insights

Behind the charts, a broader narrative emerges:
                
    1. France’s healthcare data acts like a mirror : reflecting aging, chronicity, and evolving medical practices.
                
    2. The “invisible” patients are fewer, the “known” ones better followed, and care is increasingly continuous rather than episodic.

This evolution suggests a transition from a curative model to a chronic management system, where prevention, screening, and long-term monitoring take center stage.

---

### Visual summary
""")

    fig = px.pie(
        names=["Chronic diseases", "Mental health", "Cancers", "Other"],
        values=[62, 18, 12, 8],
        title="Approximate composition of treated cases in France",
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        """
<div style="
  margin: 1.25rem 0;
  padding: 1.25rem 1.5rem;
  border-radius: 16px;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
  ">
  <div style="font-size: 0.9rem; opacity: 0.95; letter-spacing: .02em; margin-bottom: .25rem;">
    In short
  </div>
  <div style="font-size: 1.15rem; font-weight: 700; line-height: 1.35;">
    The data is not just a reflection of disease, it’s a <u>map for future health policy</u>.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("""
---

### Future directions & improvements

- Integrate more recent years (post-2023) to observe the impact of Covid and new public health programs.  
- Use machine learning to forecast prevalence evolution or identify high-risk regional clusters.  
- Cross variables like *age × sex × region* to quantify disparities in chronic care access.  

---

**Authors:** Roland Fontanes, EFREI Promo 2027, Data Storytelling Project  
**Course:** Data Visualization & Analysis  
**Instructors:** Georgina Abi Sejaan & Mano Joseph Mathew
    """)







