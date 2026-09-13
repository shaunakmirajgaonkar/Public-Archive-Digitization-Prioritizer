
import io
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Public Archive Digitization Prioritizer",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "sample_public_archive_records.csv"

REQUIRED = [
    "record_id","archive_name","collection","record_title","archive_date",
    "document_language","format_type","condition_score","historical_value_score",
    "public_demand_score","language_rarity_score","digitization_cost_index",
    "physical_risk_index","page_count","catalog_completeness_pct",
    "metadata_quality_pct","digitization_status","storage_location"
]

st.markdown("""
<style>
:root {
  --ink:#172033; --muted:#667085; --line:#e6eaf0; --panel:#ffffff;
  --bg:#f6f8fc; --blue:#4361ee; --cyan:#00a8cc; --green:#18a66a;
  --amber:#f59e0b; --red:#ef476f; --purple:#7c3aed;
}
.stApp { background:linear-gradient(180deg,#f8fbff 0%,#f5f7fb 100%); color:var(--ink); }
.block-container { padding-top:1.1rem; padding-bottom:2.5rem; max-width:1500px; }
[data-testid="stSidebar"] { background:#ffffff; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--ink)!important; }
h1,h2,h3,h4 { color:var(--ink)!important; letter-spacing:-.02em; }
p,li,label,.stMarkdown { color:var(--ink); }
.hero {
  background:linear-gradient(135deg,#eef4ff 0%,#f5f0ff 48%,#effcf8 100%);
  border:1px solid #dfe7f4; border-radius:24px; padding:26px 30px;
  box-shadow:0 12px 35px rgba(42,62,100,.08); margin-bottom:18px;
}
.hero h1 { margin:0 0 6px 0; font-size:34px; }
.hero p { margin:0; color:#5d6b82; font-size:15px; }
.pill { display:inline-block; padding:6px 10px; border-radius:999px;
  background:#fff; border:1px solid #dfe5ef; color:#42526b!important;
  font-size:12px; font-weight:700; margin-right:6px; }
.section {
  background:#fff; border:1px solid var(--line); border-radius:20px;
  padding:20px; box-shadow:0 7px 24px rgba(31,45,70,.05); margin-bottom:16px;
}
.kpi { background:#fff; border:1px solid var(--line); border-radius:18px;
  padding:17px 18px; min-height:118px; box-shadow:0 6px 18px rgba(31,45,70,.05); }
.kpi .label { font-size:12px; color:#6b7280; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
.kpi .value { font-size:28px; font-weight:800; color:#182230; margin-top:8px; }
.kpi .sub { font-size:12px; color:#667085; margin-top:3px; }
.badge { display:inline-block; padding:5px 9px; border-radius:999px; font-weight:800; font-size:11px; }
.badge-low { background:#e8f8ef;color:#087443; } .badge-moderate{background:#fff4db;color:#9a5b00;}
.badge-high{background:#ffe8ed;color:#b42343;} .badge-critical{background:#f8dce5;color:#8b1538;}
.alertbox { border-radius:14px; padding:13px 15px; background:#f7f9fc; border:1px solid #e6eaf0; margin:8px 0; }
.small { color:#667085; font-size:12px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); padding:12px; border-radius:16px; }
.stButton>button { border-radius:11px; border:1px solid #d8deea; }
.stDownloadButton>button { border-radius:11px; }
</style>
""", unsafe_allow_html=True)

def clean_numeric(df):
    for c in REQUIRED:
        if c not in df.columns:
            continue
        if c not in ["record_id","archive_name","collection","record_title","archive_date",
                     "document_language","format_type","digitization_status","storage_location"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def score_records(df):
    d = df.copy()
    # Screening-only, transparent weighted model. Higher score = greater preservation priority.
    condition_need = 100 - d["condition_score"].clip(0,100)
    cost_need = d["digitization_cost_index"].clip(0,100)
    risk = d["physical_risk_index"].clip(0,100)
    demand = d["public_demand_score"].clip(0,100)
    historic = d["historical_value_score"].clip(0,100)
    rarity = d["language_rarity_score"].clip(0,100)
    completeness_gap = 100 - d["catalog_completeness_pct"].clip(0,100)
    metadata_gap = 100 - d["metadata_quality_pct"].clip(0,100)

    d["priority_score"] = np.round(
        0.24*condition_need + 0.18*historic + 0.16*demand + 0.12*rarity +
        0.12*risk + 0.08*cost_need + 0.05*completeness_gap + 0.05*metadata_gap, 1
    ).clip(0,100)

    def cls(x):
        if x >= 75: return "Critical"
        if x >= 55: return "High"
        if x >= 35: return "Moderate"
        return "Low"
    d["priority_class"] = d["priority_score"].map(cls)
    d["condition_gap"] = np.round(condition_need,1)
    d["metadata_gap"] = np.round(metadata_gap,1)
    d["catalog_gap"] = np.round(completeness_gap,1)
    d["priority_rank"] = d["priority_score"].rank(method="min", ascending=False).astype(int)
    return d.sort_values(["priority_score","historical_value_score"], ascending=False)

def validate(df):
    missing = [c for c in REQUIRED if c not in df.columns]
    return missing

@st.cache_data
def load_default():
    return clean_numeric(pd.read_csv(DATA_PATH))

if "data" not in st.session_state:
    st.session_state.data = load_default()

with st.sidebar:
    st.markdown("## 🗂️ Archive Intelligence")
    st.caption("100% local • CSV-first • screening only")
    st.markdown("---")
    uploaded = st.file_uploader("Load local archive CSV", type=["csv"])
    if uploaded is not None:
        try:
            candidate = pd.read_csv(uploaded)
            missing = validate(candidate)
            if missing:
                st.error("Missing columns: " + ", ".join(missing))
            else:
                st.session_state.data = clean_numeric(candidate)
                st.success(f"Loaded {len(candidate):,} records")
        except Exception as e:
            st.error(f"CSV could not be read: {e}")

    df0 = st.session_state.data.copy()
    st.markdown("### Filters")
    archive_filter = st.multiselect("Archive", sorted(df0["archive_name"].dropna().unique()), default=sorted(df0["archive_name"].dropna().unique()))
    collection_filter = st.multiselect("Collection", sorted(df0["collection"].dropna().unique()), default=sorted(df0["collection"].dropna().unique()))
    status_filter = st.multiselect("Digitization status", sorted(df0["digitization_status"].dropna().unique()), default=sorted(df0["digitization_status"].dropna().unique()))
    min_demand = st.slider("Minimum public demand", 0, 100, 0)
    min_historic = st.slider("Minimum historical value", 0, 100, 0)
    st.markdown("---")
    st.caption("No APIs, cloud inference, external database, or remote data source is required.")

mask = (
    df0["archive_name"].isin(archive_filter) &
    df0["collection"].isin(collection_filter) &
    df0["digitization_status"].isin(status_filter) &
    (df0["public_demand_score"] >= min_demand) &
    (df0["historical_value_score"] >= min_historic)
)
df = score_records(df0.loc[mask].copy())

st.markdown("""
<div class="hero">
  <div>
    <span class="pill">LOCAL-FIRST</span><span class="pill">PRESERVATION INTELLIGENCE</span><span class="pill">DECISION SUPPORT</span>
  </div>
  <h1>🗂️ Public Archive Digitization Prioritizer</h1>
  <p>Transparent preservation screening for fragile public records using condition, historical value, demand, language rarity, risk, completeness, and digitization cost signals.</p>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Priority Explorer", "Collections & Trends", "Scenario Lab", "Data Quality", "Export"])

if df.empty:
    st.warning("No records match the active filters. Broaden the sidebar filters.")
    st.stop()

with tabs[0]:
    n = len(df); critical = int((df.priority_class=="Critical").sum()); high = int((df.priority_class=="High").sum())
    avg = df.priority_score.mean(); digitized = int((df.digitization_status=="Digitized").sum())
    cols = st.columns(5)
    cards = [
        ("Records in view", f"{n:,}", "Filtered archive records"),
        ("Avg priority", f"{avg:.1f}/100", "Explainable screening score"),
        ("Critical", f"{critical:,}", "Highest review tier"),
        ("High", f"{high:,}", "Elevated review tier"),
        ("Digitized", f"{digitized:,}", f"{digitized/max(n,1)*100:.0f}% of view"),
    ]
    for c,(lab,val,sub) in zip(cols,cards):
        c.markdown(f'<div class="kpi"><div class="label">{lab}</div><div class="value">{val}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section">', unsafe_allow_html=True)
    left,right = st.columns([1.25,1])
    with left:
        st.subheader("Priority landscape")
        counts = df["priority_class"].value_counts().reindex(["Low","Moderate","High","Critical"]).fillna(0).reset_index()
        counts.columns=["Class","Records"]
        fig = px.bar(counts, x="Class", y="Records", text="Records", color="Class",
                     color_discrete_sequence=["#18a66a","#f59e0b","#ef476f","#8b1538"])
        fig.update_layout(height=330, margin=dict(l=10,r=10,t=10,b=10), plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Priority drivers")
        drivers = pd.DataFrame({
            "Driver":["Condition deterioration","Historical value","Public demand","Physical risk","Language rarity","Digitization cost"],
            "Average signal":[df.condition_gap.mean(),df.historical_value_score.mean(),df.public_demand_score.mean(),
                              df.physical_risk_index.mean(),df.language_rarity_score.mean(),df.digitization_cost_index.mean()]
        }).sort_values("Average signal")
        fig2=px.bar(drivers.tail(6), x="Average signal", y="Driver", orientation="h", text_auto=".0f")
        fig2.update_layout(height=330, margin=dict(l=10,r=10,t=10,b=10), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Immediate preservation review queue")
    q = df.head(10)[["priority_rank","record_id","record_title","archive_name","condition_score","historical_value_score","public_demand_score","priority_score","priority_class"]]
    st.dataframe(q, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Interactive priority explorer")
    a,b,c = st.columns(3)
    with a: class_pick = st.multiselect("Priority class", ["Low","Moderate","High","Critical"], default=["High","Critical"])
    with b: language_pick = st.multiselect("Language", sorted(df.document_language.unique()), default=sorted(df.document_language.unique()))
    with c: max_cost = st.slider("Maximum cost index",0,100,100)
    ex = df[df.priority_class.isin(class_pick) & df.document_language.isin(language_pick) & (df.digitization_cost_index<=max_cost)].copy()
    st.caption(f"{len(ex):,} records in explorer view")
    if not ex.empty:
        fig=px.scatter(ex, x="condition_score", y="historical_value_score", size="public_demand_score",
                       color="priority_class", hover_name="record_title",
                       hover_data=["archive_name","document_language","priority_score","physical_risk_index"],
                       color_discrete_map={"Low":"#18a66a","Moderate":"#f59e0b","High":"#ef476f","Critical":"#8b1538"})
        fig.update_layout(height=430, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(ex[["priority_rank","record_id","record_title","collection","document_language","format_type","priority_score","priority_class","digitization_status"]].sort_values("priority_score",ascending=False),
                     use_container_width=True, hide_index=True)
    else: st.info("No records match the explorer filters.")
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Collection portfolio")
    agg=df.groupby("collection",as_index=False).agg(
        records=("record_id","count"), avg_priority=("priority_score","mean"),
        avg_condition=("condition_score","mean"), avg_demand=("public_demand_score","mean"),
        avg_historic=("historical_value_score","mean"), avg_risk=("physical_risk_index","mean")
    ).sort_values("avg_priority",ascending=False)
    fig=px.bar(agg.head(12), x="collection", y="avg_priority", text_auto=".1f", color="avg_priority", color_continuous_scale="Bluered")
    fig.update_layout(height=380, xaxis_tickangle=-25, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
    l,r=st.columns(2)
    with l:
        lang=df.groupby("document_language",as_index=False).agg(records=("record_id","count"),avg_rarity=("language_rarity_score","mean")).sort_values("records",ascending=False)
        st.plotly_chart(px.bar(lang,x="document_language",y="records",color="avg_rarity",color_continuous_scale="Viridis").update_layout(height=350,plot_bgcolor="white",paper_bgcolor="white"),use_container_width=True)
    with r:
        status=df["digitization_status"].value_counts().reset_index(); status.columns=["status","records"]
        st.plotly_chart(px.pie(status,names="status",values="records",hole=.58).update_layout(height=350,paper_bgcolor="white"),use_container_width=True)
    st.dataframe(agg.round(1),use_container_width=True,hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[3]:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("What-if preservation scenario")
    st.caption("Scenario outputs are planning estimates only; they do not establish archival standards or guarantee preservation outcomes.")
    l,r=st.columns([1,1.25])
    with l:
        condition_boost=st.slider("Condition improvement after preservation",0,40,15)
        demand_boost=st.slider("Demand visibility improvement",0,30,5)
        metadata_boost=st.slider("Metadata completeness improvement",0,30,10)
        cost_reduction=st.slider("Digitization cost-index reduction",0,40,10)
    sc=df.copy()
    sc["condition_score"]=np.minimum(100,sc["condition_score"]+condition_boost)
    sc["public_demand_score"]=np.minimum(100,sc["public_demand_score"]+demand_boost)
    sc["metadata_quality_pct"]=np.minimum(100,sc["metadata_quality_pct"]+metadata_boost)
    sc["digitization_cost_index"]=np.maximum(0,sc["digitization_cost_index"]-cost_reduction)
    sc=score_records(sc)
    with r:
        before=df["priority_score"].mean(); after=sc["priority_score"].mean()
        fig=go.Figure(go.Bar(x=["Current","Scenario"],y=[before,after],text=[f"{before:.1f}",f"{after:.1f}"],textposition="auto"))
        fig.update_layout(height=310,plot_bgcolor="white",paper_bgcolor="white",yaxis_title="Average priority score")
        st.plotly_chart(fig,use_container_width=True)
        st.metric("Average score change",f"{after-before:+.1f}")
    impact=df[["record_id","record_title","priority_score"]].merge(sc[["record_id","priority_score"]],on="record_id",suffixes=("_current","_scenario"))
    impact["score_change"]=impact["priority_score_scenario"]-impact["priority_score_current"]
    st.dataframe(impact.sort_values("score_change")[["record_id","record_title","priority_score_current","priority_score_scenario","score_change"]].head(15).round(1),
                 use_container_width=True,hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[4]:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Record-quality and readiness")
    q1=(100-df.catalog_completeness_pct).mean(); q2=(100-df.metadata_quality_pct).mean()
    c1,c2,c3=st.columns(3)
    c1.metric("Average catalog gap",f"{q1:.1f}%")
    c2.metric("Average metadata gap",f"{q2:.1f}%")
    c3.metric("Records without digitization",f"{(df.digitization_status!='Digitized').sum():,}")
    readiness=df.assign(
        catalog_gap=100-df.catalog_completeness_pct,
        metadata_gap=100-df.metadata_quality_pct
    )[["record_id","record_title","catalog_completeness_pct","metadata_quality_pct","format_type","storage_location","digitization_status","priority_score"]].sort_values("priority_score",ascending=False)
    st.dataframe(readiness,use_container_width=True,hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[5]:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Local export center")
    st.write("Export the currently filtered and scored dataset. The download is generated entirely in memory.")
    export=df.copy()
    csv_bytes=export.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered priority dataset",csv_bytes,"archive_digitization_priority_export.csv","text/csv")
    st.download_button("⬇️ Download original filtered records",df0.loc[mask].to_csv(index=False).encode("utf-8"),"archive_filtered_records.csv","text/csv")
    st.dataframe(export.head(30),use_container_width=True,hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="section">
<b>Responsible-use note:</b> This application is a local screening and decision-support tool. Priority scores summarize supplied signals and should be validated by archivists, conservators, records managers, historians, public institutions, and applicable preservation policies before action.
</div>
""", unsafe_allow_html=True)
