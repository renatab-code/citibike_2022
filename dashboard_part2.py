# dashboard_part2.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="CitiBike 2022 — Interactive Dashboard (Part 2)",
    page_icon="🚲",
    layout="wide",
)

# -----------------------
# Files (small, cloud-ready)
# -----------------------
DAILY_SMALL   = Path("daily_sample.csv")
STATIONS_SMALL= Path("top_stations_sample.csv")
KEPLER_HTML   = Path("citibike_kepler_map.html")

@st.cache_data(show_spinner=False)
def load_daily_small(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    # If you used TMAX/TMIN/TMEAN in notebooks, ensure TMEAN exists:
    if "TMEAN" not in df.columns and {"TMAX","TMIN"} <= set(df.columns):
        df["TMEAN"] = df[["TMAX","TMIN"]].mean(axis=1) / 10.0 if df[["TMAX","TMIN"]].abs().max().max() > 200 else df[["TMAX","TMIN"]].mean(axis=1)
    return df

@st.cache_data(show_spinner=False)
def load_stations_small(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

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
# Intro Page
# -----------------------
if page == "Intro":
    st.title("CitiBike NYC — 2022 Interactive Dashboard (Part 2)")
    st.markdown(
        """
        Welcome! This dashboard explores **CitiBike NYC** ride activity in 2022:
        - A **seasonality** view of trips vs. temperature (daily).
        - The **most frequented** start stations.
        - An interactive **origin–destination** map (Kepler.gl).
        
        Use the sidebar to navigate the pages.  
        Data sources: CitiBike system data (tripdata) and NOAA LaGuardia station.
        """
    )

# -----------------------
# Dual-Axis Page
# -----------------------
elif page == "Trips vs Temperature (Dual-Axis)":
    st.title("Trips vs Temperature (Daily)")
    if not DAILY_SMALL.exists():
        st.info("`daily_sample.csv` not found. Please run the notebook step to create it.")
    else:
        df = load_daily_small(DAILY_SMALL)

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
            **Interpretation:** Warmer months show higher trip counts, while colder periods drop
            activity notably. This supports seasonal rebalancing and fleet planning—**summer**
            stock/maintenance should be prioritized in high-demand neighborhoods.
            """
        )

# -----------------------
# Top Stations Page
# -----------------------
elif page == "Top Start Stations":
    st.title("Most Popular Start Stations")
    top_n = st.sidebar.slider("Top N stations", 10, 50, 20, step=5)

    if not STATIONS_SMALL.exists():
        st.info("`top_stations_sample.csv` not found. Please run the notebook step to create it.")
    else:
        stations = load_stations_small(STATIONS_SMALL).head(top_n)
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
            **Interpretation:** A handful of start stations capture a large share of rides.
            These areas are strong candidates for **rebalancing hubs**, **predictive maintenance**,
            and **dock expansion**.
            """
        )

# -----------------------
# Kepler Map Page
# -----------------------
elif page == "Origin–Destination Map (Kepler.gl)":
    st.title("OD Map (Kepler.gl)")
    if KEPLER_HTML.exists():
        with open(KEPLER_HTML, "r", encoding="utf-8") as f:
            html = f.read()
        st.components.v1.html(html, height=740, scrolling=True)
    else:
        st.info("Kepler map `citibike_kepler_map.html` not found. Export it and place it in the project root.")
    st.markdown(
        """
        **Interpretation:** OD arcs reveal **corridors** and hotspots (e.g., Midtown↔Downtown).  
        High-density flows point to **rebalancing** needs and reveal **commuter patterns**.
        """
    )

# -----------------------
# Extra Analysis Page
# -----------------------
elif page == "Extra Analysis":
    st.title("Extra Analysis")

    if not DAILY_SMALL.exists():
        st.info("`daily_sample.csv` not found. Please create the sample first.")
    else:
        df = load_daily_small(DAILY_SMALL)

        # --- Weekday vs Weekend analysis ---
        df["weekday"] = df["date"].dt.day_name()
        df["is_weekend"] = df["weekday"].isin(["Saturday", "Sunday"])
        trips_by_day = df.groupby("weekday")["trips"].mean().reindex(
            ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        )

        fig_weekday = px.bar(
            trips_by_day,
            x=trips_by_day.index,
            y=trips_by_day.values,
            labels={"x":"Day of Week", "y":"Avg Trips"},
            title="Average Trips by Weekday vs Weekend",
        )
        fig_weekday.update_layout(template="plotly_white")
        st.plotly_chart(fig_weekday, use_container_width=True)

        st.markdown(
            """
            **Insight:**  
            - **Weekdays** (Mon–Fri) show higher and more consistent trip volumes — reflecting commuter patterns.  
            - **Weekends** see fewer rides overall, but with more variability.  
            This indicates CitiBike demand is strongly tied to **commuting**, suggesting weekday fleet reliability should be a top priority.
            """
        )

# ----------------------------
# Recommendations Page
# ----------------------------
elif page == "Recommendations":
    st.title("Recommendations")

    st.markdown("""
    ### TL;DR
    NYC Citi Bike demand is highly **concentrated in a few core stations**, **peaks in warm months**, 
    and shows **clear directional flows** during commute windows. To reduce stockouts and stranded bikes, 
    we recommend a combination of **targeted rebalancing**, **micro-capacity upgrades**, and **light pricing nudges**, 
    validated via **short pilots** and tracked with **simple, outcome-based KPIs**.

    ---
    ### What the data shows (from this dashboard)
    - **Top Stations:** A small set of stations drive a disproportionate share of rides. These are prime candidates for
      capacity/rebalancing and for small infrastructure upgrades (more docks/parking corrals).
    - **Seasonality:** Trips climb with warmer temperatures. Expect spring ramp-up and summer peaks; plan staffing and
      truck hours accordingly.
    - **OD Flows:** Kepler.gl arcs highlight **commuter corridors** and **tourist funnels** (e.g., waterfronts/parks). 
      Morning flows concentrate into central job hubs; evenings reverse the pattern.

    ---
    ### Action Plan (6–8 weeks)
    **1) Targeted Rebalancing (Mon–Fri, commute hours)**
    - Create a **hotlist** of ~20 high-leverage stations (from “Top Stations” + OD flow endpoints).
    - Run **AM rebalancing 6–9am** (pull from residential edges → feed job-center cores).
    - Run **PM rebalancing 4–7pm** (reverse).
    - Use a lightweight rule: _“keep hotlist stations between 30% and 85% fill”_.

    **2) Micro-capacity Upgrades**
    - Add **10–20 docks** at the **top 8–10** chronic stockout/overflow stations (or set up surface corrals).
    - Coordinate with city/NYC DOT for temporary curbside corrals near stations with repeated overflow (seen on map).

    **3) Gentle Pricing Nudges (pilot)**
    - **Offload peaks:** give **–$0.50** or **+5 free minutes** for trips that **start at saturated stations** or **end at under-filled ones**.
    - **Day-of-week balancing:** weekend bonus minutes to smooth Sunday evening surges back into cores.

    **4) Information Nudges**
    - In-app “nearest station with 5+ bikes” banners when a user opens an empty station.
    - Station-level signage: QR codes to the next best station (≤ 3–5 minutes walk).

    ---
    ### Pilots (fast, measurable)
    **Pilot A — Hotlist Rebalancing**
    - **Scope:** 3 weeks, weekdays only, top ~20 stations.
    - **Success if:** Stockouts (0 bikes) **–30%** and full docks (0 returns) **–25%** during commute periods.

    **Pilot B — Dock Boost**
    - **Scope:** Add docks/corrals at 8–10 worst offenders.
    - **Success if:** Overflow events **–40%** and return-denial events **–30%** at treated stations.

    **Pilot C — Pricing Nudge**
    - **Scope:** 2 weeks, apply bonus minutes or small discounts on targeted start/end stations.
    - **Success if:** **+10–15%** lift in desired re-routing (measured by share of trips moved to target stations) 
      without harming conversion.

    ---
    ### KPIs to Track (weekly)
    - **Availability:** Share of time stations have **≥ 3 bikes** available (target: **≥ 90%** for hotlist).
    - **Return Success:** Share of time stations have **≥ 3 empty docks** (target: **≥ 90%**).
    - **Stockout count** (0-bike minutes) & **Overflow count** (0-dock minutes) per station and time window.
    - **Nudge effect:** % of rides re-routed to target stations; utilization of bonus minutes.
    - **Member experience:** ride cancellations/abandonment (proxy: app opens at empty station with no trip started).

    ---
    ### Ops notes
    - **Staffing:** align truck hours with **6–9am** and **4–7pm** windows.
    - **Weather:** pre-stage bikes before hot spells/weekends; scale back on cold/rainy days.
    - **Events:** load a calendar for parades, street fairs, games; place pop-up corrals accordingly.

    ---
    ### Risks & Mitigations
    - **Demand uncertainty:** keep pilots short; roll back underperforming nudges.
    - **Neighborhood equity:** distribute capacity upgrades across boroughs where possible; publish a fairness score.
    - **Over-rebalancing costs:** watch **cost per avoided stockout**; stop at diminishing returns.

    ---
    ### What to build next (data & product)
    - Add **hour-of-day** ridership aggregates (weather joined) to refine commute windows automatically.
    - Persist **station-hour features** (avg departures/arrivals, stockout probability) to improve rebalancing heuristics.
    - Keep collecting **nudge A/B** results to tune bonus size and timing.

    ---
    **Bottom line:** start with **hotlist rebalancing + small dock boosts** at chronic pain points, and **layer light nudges** 
    to spread load. Measure weekly, expand only what moves the KPIs.
    """)

    # Optional: quick KPI placeholders you can wire up later
    c1, c2, c3 = st.columns(3)
    c1.metric("Hotlist availability (≥3 bikes)", "—", "target ≥ 90%")
    c2.metric("Return success (≥3 docks)", "—", "target ≥ 90%")
    c3.metric("Stockouts (commute hrs)", "—", "target −30%"
        )