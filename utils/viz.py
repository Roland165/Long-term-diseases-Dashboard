# utils/viz.py
import plotly.express as px

def line_timeseries(df):
    if df is None or len(df)==0: return None
    fig = px.line(df, x="annee", y="prev_moy", markers=True)
    fig.update_layout(xaxis_title="Année", yaxis_title="Prévalence moyenne")
    return fig

def bar_by_region(df, value="prev_moy", top=15):
    if df is None or len(df)==0: return None
    topn = df.head(top)
    fig = px.bar(topn, x="region", y=value)
    fig.update_layout(xaxis_title="Région (code)", yaxis_title="Prévalence moyenne")
    return fig

def violin_by_sexe(df_raw):
    import plotly.express as px
    if df_raw is None or len(df_raw)==0: return None
    fig = px.violin(df_raw, x="sexe", y="prev", box=True, points="outliers")
    fig.update_layout(xaxis_title="Sexe (1=H,2=F,9=NSP)", yaxis_title="Prévalence")
    return fig
