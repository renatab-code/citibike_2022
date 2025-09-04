#dashboard_part2.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# -----------------------
# File paths (keep your names)
# -----------------------
DAILY_SAMPLE  = Path("daily_sample.csv")                 # daily merged sample (<25MB)
TRIPS_SAMPLE  = Path("trips_sample_topstations.csv")     # top stations sample (<25MB)
KEPLER_HTML   = Path("citibike_kepler_map.html")         # exported Kepler.gl HTML
INTRO_IMG     = Path("nyc_bikes.jpg")                    # your intro image
RECO_IMG      = Path("nyc_commute.jpg")                  # optional; falls back to intro image

# -----------------------
# Streamlit page config
# -----------------------
st.set_page_config(
    page_title="CitiBike 2022 — Interactive Dashboard (Part 2)",
    page_icon="🚲",
    layout="wide",
)

# -----------------------
# Cached loaders
# -----------------------
@st.cache_data(show_spinner=False)
def load_daily_sample() -> pd.DataFrame:
    if DAILY_SAMPLE.exists():
        df = pd.read_csv(DAILY_SAMPLE, parse_dates=["date"])
        # Ensure TMEAN exists (derive from TMAX/TMIN if needed, and convert tenths °C)
        if "TMEAN" not in df.columns and {"TMAX","TMIN"} <= set(df.columns):
            if df[["TMAX","TMIN"]].abs().max().max() > 200:
                df["TMAX"] = df["TMAX"] / 10.0
                df["TMIN"] = df["TMIN"] / 10.0
            df["TMEAN"] = df[["TMAX","TMIN"]].mean(axis=1)
        return df
    # Tiny fallback so the app still boots on Cloud
    df = pd.DataFrame({
        "date": pd.date_range("2022-01-01", periods=30, freq="D"),
        "trips": (pd.Series(range(30))*120 + 5000).astype(int),
        "TMEAN": 5 + (pd.Series(range(30)) % 10),
    })
    return df

@st.cache_data(show_spinner=False)
def load_topstations() -> pd.DataFrame:
    if TRIPS_SAMPLE.exists():
        return pd.read_csv(TRIPS_SAMPLE)
    # Tiny fallback
    return pd.DataFrame({
        "start_station_name": [f"Station {i}" for i in range(1, 11)],
        "rides": [3200, 3000, 2900, 2700, 2600, 2500, 2400, 2300, 2200, 2100],
    })

def read_kepler_html():
    if KEPLER_HTML.exists():
        return KEPLER_HTML.read_text(encoding="utf-8")
    return None

# -----------------------
# Sidebar navigation
# -----------------------
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Go to page:",
    [
        "Intro",
        "Trips vs Temperature (Dual-Axis)",
        "Top Start Stations",
        "Origin–Destination Map (Kepler.gl)",
        "Extra Analysis",
        "Recommendations",
    ],
)

# -----------------------
# Intro Page (uses your image)
# -----------------------
if page == "Intro":
    st.title("CitiBike NYC — 2022 Interactive Dashboard (Part 2)")

    if INTRO_IMG.exists():
        st.image(str(INTRO_IMG), use_column_width=True, caption="NYC CitiBike at work")

    st.markdown(
        """
        Welcome! This dashboard explores **CitiBike NYC** ride activity in 2022:

        • A **seasonality** view of trips vs. temperature (daily)  
        • The **most frequented** start stations  
        • An interactive **origin–destination** map (Kepler.gl)

        Use the sidebar to navigate the pages.  
        **Data sources:** CitiBike system data (tripdata) and NOAA (LaGuardia).
        """
    )

# -----------------------
# Dual-Axis page
# -----------------------
elif page == "Trips vs Temperature (Dual-Axis)":
    st.title("Trips vs Temperature (Daily)")

    df = load_daily_sample()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["trips"],  name="Trips",     mode="lines"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["TMEAN"], name="Temp (°C)", mode="lines", yaxis="y2"))

    fig.update_layout(
        template="plotly_white",
        xaxis_title="Date",
        yaxis=dict(title="Trips"),
        yaxis2=dict(title="Temp (°C)", overlaying="y", side="right"),
        height=560,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
        **Interpretation:** Warmer months show higher trip counts; colder months dip.  
        Plan **staffing and rebalancing** with seasonality in mind and prepare for summer peaks.
        """
    )

# -----------------------
# Top stations page
# -----------------------
elif page == "Top Start Stations":
    st.title("Most Popular Start Stations")
    top_n = st.sidebar.slider("Top N stations", 10, 50, 20, step=5)

    stations = load_topstations().head(top_n)
    fig_bar = px.bar(
        stations,
        x="rides", y="start_station_name",
        orientation="h",
        labels={"rides":"Trips", "start_station_name":"Start Station"},
        title=f"Top {top_n} Start Stations (2022)",
    )
    fig_bar.update_layout(
        template="plotly_white",
        height=600,
        margin=dict(l=160, r=40, t=60, b=40),
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(
        """
        **Interpretation:** A small set of stations handles a big share of rides.  
        They’re prime for **dock capacity**, **rebalancing hubs**, and **predictive maintenance**.
        """
    )

# -----------------------
# Kepler map page (HTML fallback)
# -----------------------
elif page == "Origin–Destination Map (Kepler.gl)":
    st.title("OD Map (Kepler.gl)")

    html = read_kepler_html()
    if html:
        st.components.v1.html(html, height=740, scrolling=True)
        st.caption("Kepler.gl map rendered from `citibike_kepler_map.html`.")
    else:
        st.info("`citibike_kepler_map.html` not found. Export the Kepler.gl map and place it in the project root.")

    st.markdown(
        """
        **Interpretation:** OD arcs reveal **commuter corridors** and hotspots (e.g., Midtown↔Downtown).  
        High-density flows highlight **rebalancing** needs and **dock scarcity** by time of day.
        """
    )

# -----------------------
# Extra Analysis (weekday pattern example)
# -----------------------
elif page == "Extra Analysis":
    st.title("Extra Analysis")

    df = load_daily_sample()
    df["weekday"] = df["date"].dt.day_name()
    wk = (df.groupby("weekday")["trips"].mean()
            .reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]))
    fig = px.bar(
        x=wk.index, y=wk.values,
        labels={"x":"Day of Week", "y":"Avg Trips"},
        title="Average Trips by Weekday vs Weekend",
    )
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    st.write(
        "Weekdays dominate (commuting). Consider **AM/PM** rebalancing windows and **weekend nudges**."
    )

# -----------------------
# Recommendations (with banner image)
# -----------------------
elif page == "Recommendations":
    st.title("Recommendations")

    banner = RECO_IMG if RECO_IMG.exists() else (INTRO_IMG if INTRO_IMG.exists() else None)
    if banner:
        st.image(str(banner), use_column_width=True, caption="Core corridors & peak demand drive ops decisions")

    st.markdown(
        """
        ### TL;DR
        Focus on:  
        1) **Hotlist rebalancing** at ~20 key stations (AM 6–9, PM 4–7)  
        2) **Micro-capacity** (10–20 docks/corrals) at chronic stockout/full sites  
        3) **Light pricing nudges** + **in-app guidance** to ease peaks

        ### KPIs (weekly)
        - Availability: ≥90% of time with **≥3 bikes** and **≥3 empty docks** at hotlist stations  
        - Stockouts/Overflows: ↓30% during commute periods  
        - Nudge effect: **+10–15%** rides shifted to target stations

        ### Ops notes
        - Align truck hours with **6–9am** and **4–7pm** windows  
        - Pre-stage for hot spells/weekends; scale back on cold/rainy days  
        - Use event calendars (games, parades) for pop-up corrals near venues
        """
    )
