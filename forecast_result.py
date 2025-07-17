import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ===== Load Data =====
@st.cache_data
def load_data():
    return pd.read_csv("forecast_result.csv", parse_dates=True, index_col=0)

df = load_data()
df.index = pd.to_datetime(df.index)
df["forecast_ppfd"] = pd.to_numeric(df["forecast_ppfd"], errors="coerce")

# ลบคอลัมน์ DLI_chunk ถ้ามี
if "DLI_chunk" in df.columns:
    df = df.drop(columns=["DLI_chunk"])

# ===== Page Config =====
st.set_page_config(page_title="Tomato Light Forecast 🍅", page_icon="tomato", layout="centered")

# ===== Title =====
st.markdown("""
    <style>
        .title-text {
            text-align: center;
            color: #d62828;
            font-weight: 800;
            font-size: 40px;
        }
        .subtitle-text {
            text-align: center;
            color: #6c757d;
            font-size: 22px;
            margin-bottom: 15px;
        }
    </style>
    <div class="title-text">🌤️Tomato Greenhouse Light Forecast🍅</div>
    <div class="subtitle-text">การทำนายค่าแสง PPFD และค่า DLI สะสมใน 1 วัน</div>
    <hr>
""", unsafe_allow_html=True)

# ===== Date Range Filter =====
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("📅 เลือกวันเริ่มต้น", df.index.min().date())
with col2:
    end_date = st.date_input("📅 เลือกวันสิ้นสุด", df.index.max().date())

if start_date > end_date:
    st.error("❌ กรุณาเลือกวันสิ้นสุดให้มากกว่าวันเริ่มต้น")
    st.stop()

filtered_df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]
if filtered_df.empty:
    st.warning("⚠️ ไม่มีข้อมูลในช่วงเวลาที่เลือก")
    st.stop()

# ===== Summary Metrics =====
# สมมติข้อมูลวัดทุก 30 นาที = 1800 วินาที
time_diff = 1800

# คำนวณ DLI จาก forecast_ppfd ตามช่วงเวลาข้อมูล
dli_total = (filtered_df["forecast_ppfd"] * time_diff).sum() / 1_000_000

low_light = filtered_df["forecast_ppfd"] < 200
high_light = filtered_df["forecast_ppfd"] > 500
total_points = len(filtered_df)

col3, col4, col5 = st.columns(3)
col3.metric("☀️ DLI สะสม (mol/m²/day)", f"{dli_total:.2f}")
col4.metric("🌑 ต่ำกว่าเกณฑ์ (<200)", f"{low_light.sum()} ({low_light.sum()/total_points*100:.1f}%)")
col5.metric("🌞 สูงเกินเกณฑ์ (>500)", f"{high_light.sum()} ({high_light.sum()/total_points*100:.1f}%)")

# ===== PPFD Stats =====
st.markdown("### 🔍 สถิติค่าทำนายค่าแสง (PPFD)")
col6, col7, col8 = st.columns(3)
col6.markdown(f"<div style='font-size:20px;'>💡 ค่าเฉลี่ย: <b>{filtered_df['forecast_ppfd'].mean():.1f}</b> µmol/m²/s</div>", unsafe_allow_html=True)
col7.markdown(f"<div style='font-size:20px;'>🔺 ค่าสูงสุด: <b>{filtered_df['forecast_ppfd'].max():.1f}</b> µmol/m²/s</div>", unsafe_allow_html=True)
col8.markdown(f"<div style='font-size:20px;'>🔻 ค่าต่ำสุด: <b>{filtered_df['forecast_ppfd'].min():.1f}</b> µmol/m²/s</div>", unsafe_allow_html=True)

st.markdown("---")

# ===== Plot Graph =====
st.subheader("📈 กราฟทำนายค่าแสง (PPFD)")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=filtered_df.index,
    y=filtered_df["forecast_ppfd"],
    mode='lines+markers',
    name='PPFD Forecast',
    line=dict(color='#d62828', width=2),
    marker=dict(size=5)
))

fig.add_hline(y=200, line_dash="dot", line_color="blue", annotation_text="ต่ำกว่าเกณฑ์", annotation_position="bottom left")
fig.add_hline(y=500, line_dash="dot", line_color="orange", annotation_text="สูงเกินเกณฑ์", annotation_position="top left")

fig.update_layout(
    xaxis_title="เวลา",
    yaxis_title="PPFD (µmol/m²/s)",
    template="plotly_white",
    height=450,
    margin=dict(l=40, r=40, t=40, b=40),
    legend=dict(x=0, y=1.1, orientation='h')
)
fig.update_xaxes(tickangle=45)

st.plotly_chart(fig, use_container_width=True)

# ===== Data Table =====
st.subheader("🗓️ ตารางทำนายค่าแสง (ทุก 30 นาที)")
styled_df = filtered_df.style.format({
    "forecast_ppfd": "{:.1f}",
}).background_gradient(subset=["forecast_ppfd"], cmap='YlOrRd')
st.dataframe(styled_df, use_container_width=True)

# ===== Download Button =====
csv = filtered_df.to_csv().encode('utf-8')
st.download_button(
    label="⬇️ ดาวน์โหลดข้อมูล CSV",
    data=csv,
    file_name='forecast_filtered.csv',
    mime='text/csv'
)
