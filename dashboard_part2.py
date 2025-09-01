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

# dashboard_part2.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(
    page_title="CitiBike 2022 — Interactive Dashboard (Part 2)",
    page_icon="🚲",
    layout="wide",
)

# ---------- Files ----------
DATA_DAILY   = Path("citibike_weather_2022.csv")     # tiny daily file (safe to keep in repo)
TRIPS_SAMPLE = Path("trips_sample.csv.gz")           # created in Step 3
KEPLER_HTML  = Path("citibike_kepler_map.html")      # or a lighter export: citibike_kepler_map_light.html

# ---------- Loaders (cached) ----------
@st.cache_data(show_spinner=False)
def load_daily() -> pd.DataFrame:
    df = pd.read_csv(DATA_DAILY, parse_dates=["date"])
    # Some students scaled NOAA 10x; normalize if you did
    for c in ["TMAX", "TMIN"]:
        if c in df and df[c].abs().max() > 200:
            df[c] = df[c] / 10.0
    if "TMEAN" not in df and {"TMAX","TMIN"}.issubset(df.columns):
        df["TMEAN"] = df[["TMAX","TMIN"]].mean(axis=1)
    return df

@st.cache_data(show_spinner=False)
def load_trips_sample() -> pd.DataFrame:
    dtypes = {
        "start_station_name": "category",
        "end_station_name": "category",
        "rideable_type": "category",
        "member_casual": "category",
    }
    df = pd.read_csv(TRIPS_SAMPLE, dtype=dtypes, parse_dates=["started_at"])
    return df

# ---------- Sidebar Navigation ----------
st.sidebar.header("Navigation")
pages = [
    "Intro",
    "Trips vs Temperature (dual axis)",
    "Top Start Stations (bar)",
    "Origin–Destination Map (Kepler.gl)",
    "Extra Analysis (you choose!)",
    "Recommendations",
]
page = st.sidebar.selectbox("Go to page", pages, index=0)

# ---------- Page: Intro ----------
if page == "Intro":
    st.title("CitiBike NYC — 2022 Interactive Dashboard")
    st.markdown("""
**Welcome!** This dashboard explores NYC CitiBike usage in 2022.
It includes:
- A seasonal view of trips vs. temperature  
- Top start stations across the city  
- An interactive Kepler.gl map of origin–destination flows  
- A flexible analysis page and recommendations
""")
    st.info("Use the left sidebar to switch between pages.")

# ---------- Page: Dual axis ----------
elif page == "Trips vs Temperature (dual axis)":
    st.title("Trips vs. Temperature (Daily, 2022)")
    if not DATA_DAILY.exists():
        st.error(f"Daily file `{DATA_DAILY}` not found.")
    else:
        df = load_daily()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["date"], y=df["trips"],
                                 name="Trips", mode="lines"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["TMEAN"],
                                 name="Temp (°C)", mode="lines", yaxis="y2"))
        fig.update_layout(
            template="plotly_white",
            xaxis_title="Date",
            yaxis=dict(title="Trips"),
            yaxis2=dict(title="Temp (°C)", overlaying="y", side="right"),
            height=560, margin=dict(t=60, r=40, b=40, l=60)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Interpretation")
        st.markdown("""
Trip volume generally **rises with warmer temperatures** and dips in the coldest months.
Spikes unrelated to temperature often reflect **weekends, holidays, or special events**.
""")

# ---------- Page: Top stations ----------
elif page == "Top Start Stations (bar)":
    st.title("Most Popular Start Stations")
    if not TRIPS_SAMPLE.exists():
        st.error(f"Sample file `{TRIPS_SAMPLE}` not found. Create it in Step 3.")
    else:
        trips = load_trips_sample()
        n = st.sidebar.slider("Top N stations", 5, 30, 20, step=5)
        top = (trips["start_station_name"]
               .value_counts(dropna=True)
               .head(n)
               .rename_axis("start_station_name")
               .reset_index(name="rides"))
        fig = px.bar(top, x="rides", y="start_station_name",
                     orientation="h", labels={"rides": "Trips", "start_station_name": "Start Station"},
                     template="plotly_white", height=600)
        fig.update_layout(yaxis=dict(categoryorder="total ascending"), margin=dict(l=140, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Interpretation")
        st.markdown("""
A small set of stations accounts for a **large share of departures**. These hubs likely need
**more docks/bikes** or **more frequent rebalancing** to reduce shortages.
""")

# ---------- Page: Kepler Map ----------
elif page == "Origin–Destination Map (Kepler.gl)":
    st.title("Origin–Destination Flows (Kepler.gl)")
    if not KEPLER_HTML.exists():
        st.warning(f"Kepler map `{KEPLER_HTML}` not found. Export from Kepler.gl and place it in the repo.")
    else:
        with open(KEPLER_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        st.components.v1.html(html, height=700, scrolling=True)

        st.subheader("Interpretation")
        st.markdown("""
Flows cluster in **Manhattan & nearby transit corridors**, indicating commute-heavy patterns.
Long arcs can highlight **cross-borough links** and potential **rebalancing routes**.
""")

# ---------- Page: Extra analysis ----------
elif page == "Extra Analysis (you choose!)":
    st.title("Extra Analysis")

    if not TRIPS_SAMPLE.exists():
        st.error(f"Sample file `{TRIPS_SAMPLE}` not found.")
    else:
        trips = load_trips_sample()
        # Example: hourly profile by rider type (if member_casual present)
        trips["hour"] = trips["started_at"].dt.hour
        if "member_casual" in trips.columns:
            hourly = (trips.groupby(["member_casual","hour"])
                            .size().reset_index(name="rides"))
            fig = px.line(hourly, x="hour", y="rides", color="member_casual",
                          template="plotly_white", markers=True, height=520)
            fig.update_layout(xaxis=dict(dtick=1), yaxis_title="Trips")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("""
**Members** tend to ride during **commute hours**, while **casual users** push more rides
in midday/evening—useful for targeted rebalancing schedules.
""")
        else:
            st.info("Column `member_casual` not in sample → replace with a chart you prefer.")

# ---------- Page: Recommendations ----------
else:
    st.title("Recommendations")
    st.markdown("""
**1. Boost supply at top hubs.**  
Add docks or dynamic rebalancing where departures concentrate.

**2. Temperature-aware planning.**  
Increase operations in warm months and weekends; scale down in cold weather.

**3. Transit integration.**  
Hubs near subway/ferry terminals show high flow — prioritize these for quick turnarounds.

**4. Rider-type scheduling.**  
Use hourly patterns to tailor staffing: commute-hour focus for members, weekend/midday for casuals.

**5. Pilot rebalancing routes.**  
Use OD arcs and station pairs with chronic net-outs to define efficient truck loops.
""")