# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import glob

st.set_page_config(
    page_title="CitiBike 2022 – Interactive Dashboard",
    page_icon="🚲",
    layout="wide"
)

st.title("CitiBike NYC – 2022 Interactive Dashboard")
st.markdown("""
This dashboard shows the most frequented start stations, a seasonality view of trips vs. temperature,
and an interactive Kepler.gl map of origin–destination flows.
""")


DATA_DIR = Path("extracted/csvs")
DAILY_FILE = Path("citibike_weather_2022.csv")
KEPLER_HTML = Path("citibike_kepler_map.html")

@st.cache_data(show_spinner=False)
def load_daily(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    # normalize NOAA tenths °C if needed
    for c in ["TMAX", "TMIN"]:
        if c in df.columns and df[c].abs().max() > 200:
            df[c] = df[c] / 10.0
    df["TMEAN"] = df[["TMAX", "TMIN"]].mean(axis=1)
    return df

@st.cache_data(show_spinner=True)
def compute_top20_stations(data_dir: Path) -> pd.DataFrame:
    usecols = ["start_station_name"]
    counts = {}
    files = sorted(glob.glob(str(data_dir / "*.csv")))
    for f in files:
        for chunk in pd.read_csv(f, usecols=usecols, chunksize=200_000):
            vc = chunk["start_station_name"].value_counts(dropna=True)
            for k, v in vc.items():
                counts[k] = counts.get(k, 0) + int(v)
    stations = (pd.Series(counts, name="rides")
                  .sort_values(ascending=False)
                  .head(20)
                  .reset_index()
                  .rename(columns={"index": "start_station_name"}))
    return stations

# Sidebar controls
st.sidebar.header("Controls")
show_top_n = st.sidebar.slider("Top N stations", 10, 30, 20, step=5)

# === Row 1: Top stations bar ===
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Top Start Stations (2022)")
    if not DATA_DIR.exists():
        st.info("Folder `extracted/csvs` not found. Place monthly trip CSVs there to compute the bar chart.")
    else:
        top_stations = compute_top20_stations(DATA_DIR).head(show_top_n)
        fig_top = px.bar(
            top_stations,
            x="rides",
            y="start_station_name",
            orientation="h",
            labels={"rides": "Trips", "start_station_name": "Start Station"},
            title=f"Top {show_top_n} Start Stations (2022)"
        )
        fig_top.update_layout(
            yaxis=dict(categoryorder="total ascending"),
            template="plotly_white",
            height=550,
            margin=dict(l=140, r=40, t=60, b=40),
        )
        st.plotly_chart(fig_top, use_container_width=True)

# === Row 1: Dual-axis line ===
with col2:
    st.subheader("Trips vs. Temperature (Daily)")
    if not DAILY_FILE.exists():
        st.info("Daily merged file `citibike_weather_2022.csv` not found.")
    else:
        df = load_daily(DAILY_FILE)
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Scatter(x=df["date"], y=df["trips"], name="Trips", mode="lines"))
        fig_dual.add_trace(go.Scatter(x=df["date"], y=df["TMEAN"], name="Temp (°C)", mode="lines", yaxis="y2"))
        fig_dual.update_layout(
            template="plotly_white",
            xaxis_title="Date",
            yaxis=dict(title="Trips"),
            yaxis2=dict(title="Temp (°C)", overlaying="y", side="right"),
            height=550
        )
        st.plotly_chart(fig_dual, use_container_width=True)

# === Row 2: Kepler.gl map (HTML) ===
import streamlit as st
from pathlib import Path

KEPLER_HTML = Path("citibike_kepler_map.html")

st.subheader("Origin–Destination Map (Kepler.gl)")
if KEPLER_HTML.exists():
    with open(KEPLER_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    # render the saved map inline
    st.components.v1.html(html, height=700, scrolling=True)
else:
    st.info("Map file `citibike_kepler_map.html` not found. Save/export your Kepler map here.")