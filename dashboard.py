import pandas as pd
import streamlit as st
import plotly.express as px

from streamlit_autorefresh import st_autorefresh
from monitoring_state import load_history


# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="AI Medical Monitoring",
    page_icon="📊",
    layout="wide"
)


# =========================
# CSS CARD + LAYOUT FIX
# =========================
st.markdown("""
<style>

.block-container {
    padding-top: 0.2rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
}

div.element-container {
    margin-bottom: -0.2rem !important;
}

h1 {
    font-size: 19px !important;
    margin-bottom: -0.4rem !important;
}

h2 {
    font-size: 15px !important;
    margin-bottom: -0.2rem !important;
}

h3 {
    font-size: 13px !important;
    margin-bottom: -0.2rem !important;
}

.card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 12px 14px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.25);
}

.card-title {
    font-size: 12px;
    opacity: 0.7;
}

.card-value {
    font-size: 20px;
    font-weight: 700;
}

div[data-testid="column"] {
    padding-left: 6px;
    padding-right: 6px;
}

.js-plotly-plot {
    margin-top: -0.5rem !important;
    margin-bottom: -0.5rem !important;
}

</style>
""", unsafe_allow_html=True)


# =========================
# AUTO REFRESH
# =========================
st_autorefresh(
    interval=3600000,  # 1 jam
    key="monitoring_refresh"
)


# =========================
# LOAD DATA
# =========================
history = load_history()

if not history:
    st.warning("Belum ada data monitoring")
    st.stop()

overall = history.get("overall", [])

if not overall:
    st.warning("Belum ada data overall")
    st.stop()

df = pd.DataFrame(overall)

if "created_at" not in df.columns:
    st.error("Kolom created_at tidak ditemukan pada monitoring_state.json")
    st.stop()

# pastikan timestamp valid
df["created_at"] = pd.to_datetime(
    df["created_at"],
    errors="coerce"
)

df = df.dropna(subset=["created_at"])

if df.empty:
    st.warning("Data monitoring tidak valid")
    st.stop()

# urutkan berdasarkan waktu
df = df.sort_values("created_at")

# ==========================================
# FILTER DATA 24 JAM TERAKHIR
# ==========================================
last_time = df["created_at"].max()
start_time = last_time - pd.Timedelta(hours=24)

df = df[
    df["created_at"] >= start_time
]

if df.empty:
    st.warning("Belum ada data monitoring dalam 24 jam terakhir")
    st.stop()

latest = df.iloc[-1]

if len(df) > 1:
    previous = df.iloc[-2]
else:
    previous = latest

last_update = latest["created_at"].strftime(
    "%d-%m-%Y %H:%M:%S"
)

total_snapshot = len(df)

def metric_delta(current, previous):
    diff = current - previous

    if diff > 0:
        return f"▲ +{diff:.2f}%"
    elif diff < 0:
        return f"▼ {abs(diff):.2f}%"
    else:
        return "▬ 0.00%"
    
def total_data_delta(current, previous):
    diff = int(current - previous)

    if diff > 0:
        return f"▲ +{diff:,}"
    elif diff < 0:
        return f"▼ {abs(diff):,}"
    else:
        return "▬ 0"


# =========================
# RENAME LABEL
# =========================
df = df.rename(columns={
    "precision": "Precision",
    "recall": "Recall",
    "f1_score": "F1-Score",
    "FP": "False Positive",
    "FN": "False Negative"
})


# =========================
# HEADER
# =========================
st.title("📊 AI Medical Monitoring Dashboard")

st.caption(
    f"Last Update: {last_update} | "
    f"Window: 24 Hours | "
    f"Snapshots: {total_snapshot}"
)


# =========================
# =========================================================
# 📌 SUMMARY (CARD UI)
# =========================================================
st.markdown("### 📌 Summary")

c1, c2, c3, c4 = st.columns(4)

def render_metric_card(
    title,
    value,
    previous,
    suffix="%",
    is_integer=False
):
    diff = value - previous

    if diff > 0:
        color = "#2ecc71"
        icon = "▲"
        delta = (
            f"{icon} +{diff:,.0f}"
            if is_integer
            else f"{icon} +{diff:.2f}{suffix}"
        )

    elif diff < 0:
        color = "#e74c3c"
        icon = "▼"
        delta = (
            f"{icon} {abs(diff):,.0f}"
            if is_integer
            else f"{icon} {abs(diff):.2f}{suffix}"
        )

    else:
        color = "#95a5a6"
        icon = "—"
        delta = (
            f"{icon} 0"
            if is_integer
            else f"{icon} 0.00{suffix}"
        )

    value_text = (
        f"{value:,.0f}"
        if is_integer
        else f"{value:.2f}{suffix}"
    )

    html = f"""
<div class="card">
    <div class="card-title">{title}</div>

    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div class="card-value">{value_text}</div>

        <div style="color:{color};font-size:13px;font-weight:600;">
            {delta}
        </div>
    </div>
</div>
"""
    return html

with c1:
    st.markdown(
        render_metric_card(
            "Precision",
            latest["precision"],
            previous["precision"]
        ),
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        render_metric_card(
            "Recall",
            latest["recall"],
            previous["recall"]
        ),
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        render_metric_card(
            "F1-Score",
            latest["f1_score"],
            previous["f1_score"]
        ),
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        render_metric_card(
            "Total Data",
            latest["total_data"],
            previous["total_data"],
            is_integer=True
        ),
        unsafe_allow_html=True
    )

# =========================
# =========================================================
# 📊 CHART ROW (3 COLUMN = COL-4 STYLE)
# =========================================================
col1, col2, col3 = st.columns(3)


# =========================
# PERFORMANCE TREND
# =========================
with col1:

    st.markdown("### 📈 Performance Trend")

    fig = px.line(
        df,
        x="created_at",
        y=["Precision", "Recall", "F1-Score"],
        markers=True,
        template="plotly_dark"
    )

    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=5, b=0),
        hovermode="x unified",
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    fig.update_xaxes(
        tickformat="%H:%M",
        title=""
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False}
    )


# =========================
# FP / FN TREND
# =========================
with col2:

    st.markdown("### ⚠️ False Positive / False Negative")

    fig2 = px.line(
        df,
        x="created_at",
        y=["False Positive", "False Negative"],
        markers=True,
        template="plotly_dark"
    )

    fig2.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=5, b=0),
        hovermode="x unified",
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    fig2.update_xaxes(
        tickformat="%H:%M",
        title=""
    )

    st.plotly_chart(
        fig2,
        width="stretch",
        config={"displayModeBar": False}
    )


# =========================
# FIELD F1 SCORE
# =========================
with col3:

    st.markdown("### 🧠 Field F1-Score")

    summary_field = history.get("summary_field", [])

    if summary_field:

        field_df = pd.DataFrame(summary_field[-1]["data"])

        fig3 = px.bar(
            field_df.sort_values("f1_score", ascending=True),
            x="field",
            y="f1_score",
            text="f1_score",
            color="f1_score",
            template="plotly_dark",
            color_continuous_scale=[
                [0.0, "#e74c3c"],
                [0.5, "#f1c40f"],
                [1.0, "#2ecc71"]
            ]
        )

        fig3.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=5, b=0),
            showlegend=False,
            coloraxis_showscale=False,
            xaxis=dict(showticklabels=True),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        fig3.update_traces(
            texttemplate='%{text:.2f}%',
            textposition='outside'
        )

        st.plotly_chart(
            fig3,
            width="stretch",
            config={"displayModeBar": False}
        )


# =========================
# =========================================================
# 👨‍⚕️ DOCTOR PERFORMANCE (FULL WIDTH / COL-12)
# =========================================================
st.markdown("## 👨‍⚕️ Doctor Performance (F1-Score)")

doctor_perf = history.get("doctor_performance", [])

if doctor_perf:

    doc_df = pd.DataFrame(doctor_perf[-1].get("data", []))

    doc_df = doc_df.rename(columns={
        "dokter": "doctor",
        "doctor_name": "doctor",
        "nama_dokter": "doctor",
        "name": "doctor",
        "f1": "F1-Score"
    })

    doc_df = doc_df.dropna(subset=["doctor", "F1-Score"])
    doc_df = doc_df[doc_df["doctor"].astype(str).str.strip() != ""]

    doc_df = doc_df.groupby("doctor", as_index=False)["F1-Score"].mean()

    doc_df = doc_df.sort_values("F1-Score", ascending=True)

    fig4 = px.bar(
        doc_df,
        x="doctor",
        y="F1-Score",
        text="F1-Score",
        color="F1-Score",
        template="plotly_dark",
        color_continuous_scale=[
            [0.0, "#e74c3c"],
            [0.5, "#f1c40f"],
            [1.0, "#2ecc71"]
        ]
    )

    fig4.update_layout(
        height=600,
        margin=dict(l=10, r=10, t=20, b=10),
        coloraxis_showscale=False,
        xaxis=dict(
            showticklabels=True,
            tickangle=-45,
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=10)
        ),
        yaxis=dict(title="F1-Score")
    )

    fig4.update_traces(
        hovertemplate="Doctor: %{x}<br>F1-Score: %{y:.2f}%<extra></extra>",
        texttemplate="%{y:.2f}%",
        textposition="outside"
    )

    st.plotly_chart(
        fig4,
        width="stretch",
        config={"displayModeBar": False}
    )


# =========================
# TABLE SECTION
# =========================
colA, colB = st.columns(2)

with colA:
    st.markdown("## 📋 Top Problem Episode")

    problem_episode = history.get("problem_episode", [])

    if problem_episode:
        st.dataframe(
            pd.DataFrame(problem_episode[-1]["data"]),
            width="stretch"
        )

with colB:
    st.markdown("## ⚠️ Missing Phrase")

    missing_data = history.get("kontrol_missing_phrase", [])

    if missing_data:
        st.dataframe(
            pd.DataFrame(missing_data[-1]["data"]),
            width="stretch"
        )


# =========================
# RAW JSON
# =========================
with st.expander("🧾 Raw Monitoring JSON"):
    st.json(history)


# =========================
# FOOTER
# =========================
st.caption("AI Medical Monitoring Dashboard")