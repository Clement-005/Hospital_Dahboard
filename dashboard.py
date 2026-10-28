"""
Hospital Operations Dashboard (soft UI style) for the Streamlit hospital_app.
 
Usage in app.py:
    from dashboard import show_dashboard
    ...
    if page == "Dashboard":
        show_dashboard(engine)
 
st.set_page_config(layout="wide", ...) must be the first Streamlit call in app.py.
If your column names differ, edit DASHBOARD_SQL below (keep the aliases on the right).
"""
 
from datetime import date, timedelta
 
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text
 
CURRENCY = "GHS"   # change to "$" if your billing amounts are in dollars
 
# One query feeds the whole dashboard. Rename the columns on the LEFT to match your tables.
DASHBOARD_SQL = """
SELECT
    a.admission_id        AS admission_id,
    a.patient_id          AS patient_id,
    p.age                 AS age,
    p.gender              AS gender,
    a.date_of_admission   AS admission_date,
    a.discharge_date      AS discharge_date,
    a.admission_type      AS admission_type,
    a.medical_condition   AS medical_condition,
    a.test_results        AS test_results,
    b.billing_amount      AS billing_amount,
    b.insurance_provider  AS insurance_provider
FROM admissions a
JOIN patients p       ON p.patient_id = a.patient_id
LEFT JOIN billings b  ON b.admission_id = a.admission_id
"""
 
# Palette
BLUE, TEAL, SKY, AMBER, RED, GREEN = "#2F6FE4", "#2CC4C9", "#8FB8F5", "#F4B740", "#EF5D6C", "#1E9E6A"
INK, MUTED, LINE = "#0F2547", "#6B7D99", "#E3ECF7"
 
ICONS = {
    "money":  '<path d="M12 2v20M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "bed":    '<path d="M2 4v16M2 8h18a2 2 0 0 1 2 2v10M2 17h20M6 8v9"/>',
    "clock":  '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "users":  '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "in":     '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/>',
    "out":    '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    "alert":  '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01"/>',
    "check":  '<path d="M20 6 9 17l-5-5"/>',
    "steth":  '<path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 12 0V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 12 0v-4"/><circle cx="20" cy="10" r="2"/>',
    "receipt":'<path d="M4 2v20l3-2 3 2 3-2 3 2 3-2 1 .7V2l-3 2-3-2-3 2-3-2-3 2z"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "id":     '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="11" r="2.5"/><path d="M15 9h3M15 13h3M6 17c.6-1.5 1.8-2.2 3-2.2s2.4.7 3 2.2"/>',
    "cross":  '<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>',
}
 
 
def icon(name, color=BLUE, size=20):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')
 
 
# ---------------------------------------------------------------- data
 
@st.cache_data(ttl=300, show_spinner="Loading hospital data...")
def load_data(_engine):
    with _engine.connect() as conn:
        df = pd.read_sql(text(DASHBOARD_SQL), conn)
    return prepare(df)
 
 
def prepare(df):
    df = df.copy()
    df["admission_date"] = pd.to_datetime(df["admission_date"], errors="coerce")
    df["discharge_date"] = pd.to_datetime(df["discharge_date"], errors="coerce")
    df["billing_amount"] = pd.to_numeric(df["billing_amount"], errors="coerce")
    df["los"] = (df["discharge_date"] - df["admission_date"]).dt.days
    return df
 
 
def in_range(df, col, start, end):
    s, e = pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1)
    return df[(df[col] >= s) & (df[col] < e)]
 
 
def pct_change(cur, prev):
    if prev in (0, None) or pd.isna(prev):
        return None
    return (cur - prev) / prev * 100
 
 
def money(x):
    if pd.isna(x):
        return "n/a"
    if abs(x) >= 1e9:
        return f"{CURRENCY} {x/1e9:.2f}B"
    if abs(x) >= 1e6:
        return f"{CURRENCY} {x/1e6:.2f}M"
    if abs(x) >= 1e3:
        return f"{CURRENCY} {x/1e3:.1f}K"
    return f"{CURRENCY} {x:,.0f}"
 
 
# ---------------------------------------------------------------- styling
 
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: linear-gradient(180deg, #EAF2FC 0%, #F5F9FE 45%, #EEF4FB 100%); color: {INK}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }}
 
[data-testid="stSidebar"] {{ background: rgba(255,255,255,.72); border-right: 1px solid {LINE};
    backdrop-filter: blur(10px); }}
[data-testid="stSidebar"] label p {{ font-weight: 500; color: #3A4E6E; }}
 
/* any container whose key starts with "card" becomes a soft card */
div[class*="st-key-card"] {{ background: rgba(255,255,255,.85); border: 1px solid {LINE}; border-radius: 18px;
    box-shadow: 0 6px 24px rgba(31,79,160,.07); padding: 18px 20px 14px; }}
div[class*="st-key-card"] [data-testid="stPlotlyChart"] {{ margin-top: -6px; }}
div[class*="st-key-card"] > div {{ border: none !important; }}
 
.hd-title {{ font-size: 2.15rem; font-weight: 800; color: {INK}; letter-spacing: -.02em; margin: 0; line-height: 1.15; }}
.hd-sub {{ color: {MUTED}; font-size: .95rem; margin-top: 4px; }}
.hd-user {{ display:flex; align-items:center; gap:10px; justify-content:flex-end; }}
.hd-avatar {{ width:38px; height:38px; border-radius:50%; background:#DCE8FB; color:{BLUE}; font-weight:700;
    display:flex; align-items:center; justify-content:center; font-size:.85rem; }}
.hd-name {{ font-weight:600; font-size:.9rem; color:{INK}; line-height:1.2; }}
.hd-role {{ font-size:.78rem; color:{MUTED}; }}
 
.kpi {{ background: rgba(255,255,255,.85); border:1px solid {LINE}; border-radius:18px; padding:18px 20px;
    box-shadow: 0 6px 24px rgba(31,79,160,.07); height: 100%; }}
.kpi-ic {{ width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin-bottom:12px; }}
.kpi-label {{ color:{MUTED}; font-size:.86rem; font-weight:500; }}
.kpi-value {{ font-size:1.75rem; font-weight:800; color:{INK}; letter-spacing:-.02em; margin:2px 0 6px; }}
.kpi-delta {{ font-size:.8rem; font-weight:600; }}
.kpi-delta span {{ color:{MUTED}; font-weight:400; margin-left:4px; }}
 
.card-h {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }}
.card-t {{ font-weight:700; font-size:1.02rem; color:{INK}; }}
.card-s {{ font-size:.8rem; color:{MUTED}; }}
 
table.ct {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.84rem; white-space:nowrap; }}
table.ct th {{ text-align:left; color:{MUTED}; font-weight:500; background:#F1F6FD; padding:9px 8px; }}
table.ct th:first-child {{ border-radius:10px 0 0 10px; }} table.ct th:last-child {{ border-radius:0 10px 10px 0; }}
div[data-testid='stMarkdownContainer'] table.ct, div[data-testid='stMarkdownContainer'] table.ct tr, div[data-testid='stMarkdownContainer'] table.ct th, div[data-testid='stMarkdownContainer'] table.ct td {{ border:none !important; }}
table.ct {{ display:table; }}
div[data-testid='stMarkdownContainer'] table.ct td {{ padding:11px 8px; border-bottom:1px solid #EEF3FA !important; color:{INK}; }}
table.ct tr:last-child td {{ border-bottom:none; }}
.dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; vertical-align:middle; }}
.bar {{ display:inline-block; width:64px; height:8px; background:#E7EEF8; border-radius:99px; vertical-align:middle; overflow:hidden; }}
.bar > i {{ display:block; height:100%; border-radius:99px; }}
.num {{ font-variant-numeric: tabular-nums; }}
 
.alert-row {{ display:flex; align-items:center; gap:10px; padding:7px 10px; border-radius:12px; margin-bottom:6px; }}
.alert-row.bad {{ background:#FDEEF0; }} .alert-row.ok {{ background:#EAF7F1; }}
.alert-ic {{ width:34px; height:34px; border-radius:10px; background:#fff; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.alert-txt {{ flex:1; font-size:.86rem; font-weight:600; color:{INK}; line-height:1.25; }}
.alert-txt small {{ display:block; font-weight:400; color:{MUTED}; font-size:.76rem; }}
.alert-n {{ font-size:.82rem; font-weight:700; white-space:nowrap; }}
 
.flow {{ display:flex; align-items:flex-start; justify-content:space-between; gap:6px; padding:6px 4px 2px; }}
.flow-step {{ text-align:center; flex:1; }}
.flow-ic {{ width:56px; height:56px; border-radius:50%; margin:0 auto 10px; display:flex; align-items:center; justify-content:center;
    background:#fff; box-shadow: 0 6px 18px rgba(31,79,160,.12); }}
.flow-name {{ font-weight:700; font-size:.88rem; color:{INK}; }}
.flow-val {{ font-size:.82rem; color:{BLUE}; margin-top:2px; }}
.flow-arrow {{ align-self:center; color:#9DB6DD; font-size:1.5rem; margin-top:-28px; }}
.pill {{ background:#E3F6EC; color:{GREEN}; font-size:.75rem; font-weight:600; padding:4px 10px; border-radius:99px; }}
.pill.warn {{ background:#FFF3DC; color:#B7791F; }}
 
.ins-row {{ display:flex; align-items:center; justify-content:space-between; padding:9px 0; border-bottom:1px solid #EEF3FA; }}
.ins-row:last-child {{ border-bottom:none; }}
.ins-name {{ font-size:.88rem; font-weight:500; color:{INK}; }}
.ins-pct {{ text-align:right; font-weight:700; font-size:.88rem; color:{INK}; }}
.ins-pct small {{ display:block; font-weight:400; color:{MUTED}; font-size:.74rem; }}
 
.act {{ display:flex; gap:12px; align-items:center; padding:10px 12px; background:#F6F9FE; border-radius:12px; margin-bottom:8px; }}
.act-ic {{ width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.act-t {{ font-size:.86rem; font-weight:500; color:{INK}; line-height:1.3; }}
.act-d {{ font-size:.76rem; color:{MUTED}; }}
</style>
"""
 
 
def card_header(title, sub=""):
    st.markdown(f'<div class="card-h"><div class="card-t">{title}</div>'
                f'<div class="card-s">{sub}</div></div>', unsafe_allow_html=True)
 
 
def plotly_base(fig, height):
    fig.update_layout(height=height, margin=dict(l=4, r=4, t=4, b=4),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", color=MUTED, size=12),
                      hoverlabel=dict(bgcolor="white", font_color=INK, bordercolor=LINE))
    return fig
 
 
def show_chart(fig):
    cfg = {"displayModeBar": False}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg)        # newer Streamlit
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=cfg)  # older Streamlit
 
 
# ---------------------------------------------------------------- sections
 
def kpi_card(col, ic, ic_bg, ic_color, label, value, delta, good_when_up=True):
    if delta is None:
        d_html = f'<div class="kpi-delta" style="color:{MUTED}">no earlier data</div>'
    else:
        up = delta >= 0
        good = up == good_when_up
        color = GREEN if good else RED
        arrow = "&#8599;" if up else "&#8600;"
        d_html = (f'<div class="kpi-delta" style="color:{color}">{arrow} {delta:+.1f}%'
                  f'<span>vs previous period</span></div>')
    col.markdown(f'<div class="kpi"><div class="kpi-ic" style="background:{ic_bg}">{icon(ic, ic_color)}</div>'
                 f'<div class="kpi-label">{label}</div><div class="kpi-value num">{value}</div>{d_html}</div>',
                 unsafe_allow_html=True)
 
 
def kpi_row(cur, prev):
    c = st.columns(4, gap="small")
    billed, billed_p = cur["billing_amount"].sum(), prev["billing_amount"].sum()
    adm, adm_p = len(cur), len(prev)
    los, los_p = cur["los"].mean(), prev["los"].mean()
    pts, pts_p = cur["patient_id"].nunique(), prev["patient_id"].nunique()
    kpi_card(c[0], "money", "#E3EDFC", BLUE, "Total Billed", money(billed), pct_change(billed, billed_p))
    kpi_card(c[1], "bed", "#E0F7F7", "#13A3A8", "Admissions", f"{adm:,}", pct_change(adm, adm_p))
    kpi_card(c[2], "clock", "#FFF4DE", "#D99A1E", "Avg Length of Stay",
             "n/a" if pd.isna(los) else f"{los:.1f} days", pct_change(los, los_p), good_when_up=False)
    kpi_card(c[3], "users", "#EAE8FD", "#6A5AE0", "Patients Treated", f"{pts:,}", pct_change(pts, pts_p))
 
 
def condition_table(cur):
    colors = [BLUE, TEAL, "#6A5AE0", AMBER, "#4BA3F2", RED, GREEN, "#9B7BEA"]
    g = (cur.groupby("medical_condition")
            .agg(adm=("admission_id", "count"), los=("los", "mean"), billed=("billing_amount", "sum"))
            .sort_values("adm", ascending=False).head(8))
    total = max(len(cur), 1)
    rows = ""
    for i, (name, r) in enumerate(g.iterrows()):
        share = r.adm / total * 100
        c = colors[i % len(colors)]
        los = "n/a" if pd.isna(r.los) else f"{r.los:.1f} d"
        rows += (f'<tr><td><span class="dot" style="background:{c}"></span><b>{name}</b></td>'
                 f'<td class="num">{int(r.adm):,}</td>'
                 f'<td><span class="bar"><i style="width:{share:.0f}%;background:{c}"></i></span>'
                 f'<span class="num" style="margin-left:8px;color:{MUTED}">{share:.0f}%</span></td>'
                 f'<td class="num">{los}</td><td class="num">{money(r.billed)}</td></tr>')
    if not rows:
        rows = f'<tr><td colspan="5" style="color:{MUTED}">No admissions in this period.</td></tr>'
    st.markdown('<table class="ct"><tr><th>Condition</th><th>Admissions</th><th>Share</th>'
                f'<th>Avg stay</th><th>Billed</th></tr>{rows}</table>', unsafe_allow_html=True)
 
 
def flow_chart(df, start, end):
    adm = in_range(df, "admission_date", start, end)
    dis = in_range(df, "discharge_date", start, end)
    days = (pd.Timestamp(end) - pd.Timestamp(start)).days
    rule, label = ("D", "per day") if days <= 45 else ("W-MON", "per week") if days <= 200 else ("MS", "per month")
    a = adm.set_index("admission_date").resample(rule)["admission_id"].count()
    d = dis.set_index("discharge_date").resample(rule)["admission_id"].count()
    idx = a.index.union(d.index)
    a, d = a.reindex(idx, fill_value=0), d.reindex(idx, fill_value=0)
    fig = go.Figure()
    fig.add_scatter(x=idx, y=a, name="Admissions", mode="lines+markers", line=dict(color=BLUE, width=2.5, shape="spline"),
                    marker=dict(size=5), fill="tozeroy", fillcolor="rgba(47,111,228,.08)")
    fig.add_scatter(x=idx, y=d, name="Discharges", mode="lines+markers", line=dict(color=TEAL, width=2.5, shape="spline"),
                    marker=dict(size=5), fill="tozeroy", fillcolor="rgba(44,196,201,.08)")
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.12, x=0, font=dict(color=INK)))
    fig.update_xaxes(showgrid=False, linecolor=LINE)
    fig.update_yaxes(gridcolor="#EAF0F8", zeroline=False, title=None)
    show_chart(plotly_base(fig, 310))
    return label
 
 
def donut(series, colors, center_value, center_label):
    counts = series.dropna().value_counts()
    total = counts.sum() or 1
    labels = [f"{k}   {v/total*100:.0f}%" for k, v in counts.items()]
    fig = go.Figure(go.Pie(labels=labels, values=counts.values, hole=.7, sort=False, direction="clockwise",
                           marker=dict(colors=colors[:len(counts)], line=dict(color="white", width=3)),
                           textinfo="none", hovertemplate="%{label}<br>%{value:,} admissions<extra></extra>"))
    fig.add_annotation(text=f"<b style='font-size:22px;color:{INK}'>{center_value}</b><br>"
                            f"<span style='font-size:11px'>{center_label}</span>", showarrow=False)
    fig.update_layout(showlegend=True, legend=dict(x=1.02, y=.5, yanchor="middle", font=dict(color=INK, size=12)))
    show_chart(plotly_base(fig, 280))
 
 
def data_alerts(df):
    checks = [
        ("Negative bills", "Amount below zero", int((df["billing_amount"] < 0).sum())),
        ("Bad date order", "Discharge before admission", int((df["discharge_date"] < df["admission_date"]).sum())),
        ("Missing dates", "Admission or discharge empty", int(df["admission_date"].isna().sum() + df["discharge_date"].isna().sum())),
        ("Unbilled admissions", "No row in billings", int(df["billing_amount"].isna().sum())),
        ("Ages out of range", "Below 0 or above 120", int(((df["age"] < 0) | (df["age"] > 120)).sum())),
    ]
    html = ""
    for title, sub, n in checks:
        bad = n > 0
        html += (f'<div class="alert-row {"bad" if bad else "ok"}"><div class="alert-ic">'
                 f'{icon("alert" if bad else "check", RED if bad else GREEN, 18)}</div>'
                 f'<div class="alert-txt">{title}<small>{sub}</small></div>'
                 f'<div class="alert-n" style="color:{RED if bad else GREEN}">'
                 f'{f"{n:,} rows" if bad else "All clear"}</div></div>')
    st.markdown(html, unsafe_allow_html=True)
    return sum(c[2] for c in checks)
 
 
def patient_flow(df, cur, start, end):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    in_ward = df[(df["admission_date"] <= e) & ((df["discharge_date"].isna()) | (df["discharge_date"] > e))]
    discharged = in_range(df, "discharge_date", start, end)
    steps = [
        ("id", "#E3EDFC", BLUE, "Registered", f"{cur['patient_id'].nunique():,} patients"),
        ("in", "#E0F7F7", "#13A3A8", "Admitted", f"{len(cur):,} admissions"),
        ("steth", "#EAE8FD", "#6A5AE0", "In Treatment", f"{len(in_ward):,} in ward"),
        ("out", "#E3F6EC", GREEN, "Discharged", f"{len(discharged):,} patients"),
        ("receipt", "#FFF4DE", "#D99A1E", "Billed", money(cur["billing_amount"].sum())),
    ]
    parts = []
    for ic, bg, colr, name, val in steps:
        parts.append(f'<div class="flow-step"><div class="flow-ic" style="background:{bg}">{icon(ic, colr, 24)}</div>'
                     f'<div class="flow-name">{name}</div><div class="flow-val">{val}</div></div>')
    st.markdown('<div class="flow">' + '<div class="flow-arrow">&#10230;</div>'.join(parts) + '</div>',
                unsafe_allow_html=True)
 
 
def insurer_panel(cur):
    metric_opts = ["Billed", "Admissions", "Avg bill"]
    if hasattr(st, "segmented_control"):
        metric = st.segmented_control("Metric", metric_opts, default="Billed", key="ins_metric",
                                      label_visibility="collapsed") or "Billed"
    else:
        metric = st.radio("Metric", metric_opts, horizontal=True, key="ins_metric", label_visibility="collapsed")
    g = cur.groupby("insurance_provider").agg(billed=("billing_amount", "sum"),
                                              adm=("admission_id", "count"),
                                              avg=("billing_amount", "mean"))
    if g.empty:
        st.caption("No bills in this period.")
        return
    col = {"Billed": "billed", "Admissions": "adm", "Avg bill": "avg"}[metric]
    g = g.sort_values(col, ascending=True).tail(8)
    total = g[col].sum()
    if col == "billed":
        labels = [f"{v/total*100:.0f}%  ·  {money(v)}" for v in g[col]]
    elif col == "adm":
        labels = [f"{v/total*100:.0f}%  ·  {int(v):,}" for v in g[col]]
    else:
        labels = [money(v) for v in g[col]]
    shades = ["#C9DBF8", "#A9C6F4", "#86AEEE", "#5E92E8", BLUE, "#1F57C3", "#173F8E", "#122F6B"]
    fig = go.Figure(go.Bar(x=g[col], y=g.index, orientation="h", text=labels, textposition="outside",
                           cliponaxis=False, textfont=dict(color=INK, size=12),
                           marker=dict(color=shades[-len(g):], cornerradius=6),
                           hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
    fig.update_xaxes(visible=False, range=[0, g[col].max() * 1.75])
    fig.update_yaxes(showgrid=False, tickfont=dict(color=INK, size=12))
    show_chart(plotly_base(fig, 330))
 
 
def recent_activity(df, end):
    e = pd.Timestamp(end) + pd.Timedelta(days=1)
    a = df[df["admission_date"] < e].nlargest(5, "admission_date")
    d = df[df["discharge_date"] < e].nlargest(5, "discharge_date")
    events = []
    for _, r in a.iterrows():
        kind = str(r.admission_type or "").lower()
        ic, bg, colr = (("alert", "#FDEEF0", RED) if kind == "emergency" else ("in", "#E3EDFC", BLUE))
        events.append((r.admission_date, ic, bg, colr,
                       f"{r.admission_type or 'New'} admission #{r.admission_id} &middot; {r.medical_condition}"))
    for _, r in d.iterrows():
        events.append((r.discharge_date, "out", "#E3F6EC", GREEN,
                       f"Admission #{r.admission_id} discharged &middot; {money(r.billing_amount)} billed"))
    events = sorted(events, key=lambda x: x[0], reverse=True)[:5]
    html = ""
    for dt, ic, bg, colr, txt in events:
        html += (f'<div class="act"><div class="act-ic" style="background:{bg}">{icon(ic, colr, 18)}</div>'
                 f'<div><div class="act-t">{txt}</div><div class="act-d">{dt:%d %b %Y}</div></div></div>')
    st.markdown(html or f'<div class="card-s">No activity yet.</div>', unsafe_allow_html=True)
 
 
# ---------------------------------------------------------------- page
 
def show_dashboard(engine=None, df=None):
    """Render the dashboard. Pass engine for MySQL, or df (already loaded) for demo mode."""
    st.markdown(CSS, unsafe_allow_html=True)
    if df is None:
        df = load_data(engine)
    else:
        df = prepare(df)
 
    if df.empty or df["admission_date"].isna().all():
        st.info("No admissions in the database yet.")
        return
 
    max_d = df["admission_date"].max().date()
    min_d = df["admission_date"].min().date()
 
    # Header
    user = st.session_state.get("user", {"username": "Admin", "role": "admin"})
    uname = str(user.get("username", "Admin"))
    initials = "".join(w[0] for w in uname.replace("_", " ").split()[:2]).upper() or "AD"
    h1, h2, h3 = st.columns([2.6, 1.2, 1], vertical_alignment="center")
    h1.markdown('<div class="hd-title" style="font-size:2.15rem;font-weight:800;line-height:1.15">Hospital Operations Dashboard</div>'
                '<div class="hd-sub">Live admissions, billing and patient flow from hospital_db.</div>',
                unsafe_allow_html=True)
    default_start = max(min_d, max_d - timedelta(days=89))
    rng = h2.date_input("Period", value=(default_start, max_d), min_value=min_d, max_value=max_d,
                        format="DD/MM/YYYY", label_visibility="collapsed")
    h3.markdown(f'<div class="hd-user"><div class="hd-avatar">{initials}</div><div>'
                f'<div class="hd-name">{uname}</div><div class="hd-role">{str(user.get("role", "")).replace("_", " ").title()}</div>'
                f'</div></div>', unsafe_allow_html=True)
 
    start, end = (rng if isinstance(rng, (tuple, list)) and len(rng) == 2 else (default_start, max_d))
    length = (end - start).days + 1
    cur = in_range(df, "admission_date", start, end)
    prev = in_range(df, "admission_date", start - timedelta(days=length), start - timedelta(days=1))
 
    st.write("")
    kpi_row(cur, prev)
    st.write("")
 
    # Equal-height cards per row (pixels). Every row uses equal-width columns.
    H_ROW2, H_ROW3, H_ROW5 = 440, 370, 440
    st.markdown(f"""<style>
    .st-key-card_conditions, .st-key-card_flowchart {{ min-height:{H_ROW2}px; }}
    .st-key-card_types, .st-key-card_alerts, .st-key-card_tests {{ min-height:{H_ROW3}px; }}
    .st-key-card_insurers, .st-key-card_activity {{ min-height:{H_ROW5}px; }}
    </style>""", unsafe_allow_html=True)
 
    # Row 2: condition table | admissions vs discharges
    l, r = st.columns(2, gap="medium")
    with l:
        with st.container(key="card_conditions"):
            card_header("Admissions by Medical Condition", f"{start:%d %b} to {end:%d %b %Y}")
            condition_table(cur)
    with r:
        with st.container(key="card_flowchart"):
            card_header("Admissions vs Discharges", "")
            unit = flow_chart(df, start, end)
            st.caption(f"Counts {unit}")
 
    # Row 3: admission type | data quality | test results
    a, b, c = st.columns(3, gap="medium")
    with a:
        with st.container(key="card_types"):
            card_header("Admission Type", "this period")
            donut(cur["admission_type"], [BLUE, TEAL, SKY, "#C9D6EA"], f"{len(cur):,}", "Admissions")
    with b:
        with st.container(key="card_alerts"):
            card_header("Data Quality Alerts", "all records")
            data_alerts(df)
    with c:
        with st.container(key="card_tests"):
            card_header("Test Results", "this period")
            donut(cur["test_results"], [BLUE, AMBER, RED, TEAL], f"{cur['test_results'].notna().sum():,}", "Tests")
 
    # Row 4: patient journey (full width)
    issues = int((df["billing_amount"] < 0).sum() + (df["discharge_date"] < df["admission_date"]).sum())
    with st.container(key="card_journey"):
        pill = ('<span class="pill">Data healthy</span>' if issues == 0
                else f'<span class="pill warn">{issues:,} records need review</span>')
        st.markdown(f'<div class="card-h"><div class="card-t">Patient Journey</div>{pill}</div>',
                    unsafe_allow_html=True)
        patient_flow(df, cur, start, end)
 
    # Row 5: insurers | recent activity
    l, r = st.columns(2, gap="medium")
    with l:
        with st.container(key="card_insurers"):
            card_header("Billing by Insurance Provider", "this period")
            insurer_panel(cur)
    with r:
        with st.container(key="card_activity"):
            card_header("Recent Activity", f"up to {end:%d %b %Y}")
            recent_activity(df, end)