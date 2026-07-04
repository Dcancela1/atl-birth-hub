"""
ATL Birth Hub — Metro Atlanta Birth Facility Explorer

Tesla-inspired minimal UI with clear, upfront filters and honest coverage messaging.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from data_ingestion import (
    COVERAGE_NOTE,
    DEFAULT_ZIP,
    PRIORITY_LABELS,
    PRIORITY_OPTIONS,
    QUALITY_FILTER_OPTIONS,
    load_facilities,
    load_resources,
    prepare_facility_data,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ATL Birth Hub",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Tesla-inspired CSS — minimal, high-contrast, generous whitespace
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --black: #171717;
            --gray-900: #262626;
            --gray-600: #525252;
            --gray-400: #A3A3A3;
            --gray-200: #E5E5E5;
            --gray-100: #F5F5F5;
            --white: #FFFFFF;
            --accent: #5D9C8E;
            --accent-soft: #E8F4F0;
        }

        .stApp {
            background: var(--white);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        #MainMenu, footer, header { visibility: hidden; }

        /* Hide sidebar — filters live in main panel */
        section[data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }

        .block-container {
            padding-top: 2rem;
            max-width: 1100px;
        }

        /* Typography */
        .main h1, .main h2, .main h3,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        .stTabs [data-baseweb="tab-panel"] h1,
        .stTabs [data-baseweb="tab-panel"] h2,
        .stTabs [data-baseweb="tab-panel"] h3 {
            color: var(--black) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em;
        }

        [data-testid="stMetricLabel"] { color: var(--gray-600) !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
        [data-testid="stMetricValue"] { color: var(--black) !important; font-weight: 600 !important; }

        /* Hero — Tesla-style minimal */
        .tesla-hero {
            padding: 0 0 2.5rem 0;
            border-bottom: 1px solid var(--gray-200);
            margin-bottom: 2rem;
        }
        .tesla-hero h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--black);
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.03em;
        }
        .tesla-hero .subtitle {
            font-size: 1.05rem;
            color: var(--gray-600);
            margin: 0;
            line-height: 1.5;
            max-width: 560px;
        }
        .tesla-meta {
            margin-top: 1rem;
            font-size: 0.8rem;
            color: var(--gray-400);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        /* Coverage banner */
        .coverage-banner {
            background: var(--gray-100);
            border: 1px solid var(--gray-200);
            border-radius: 4px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 2rem;
        }
        .coverage-banner .title {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--gray-600);
            margin-bottom: 0.5rem;
        }
        .coverage-banner .body {
            font-size: 0.92rem;
            color: var(--gray-900);
            line-height: 1.55;
            margin: 0;
        }
        .coverage-banner .count {
            display: inline-block;
            background: var(--black);
            color: white;
            padding: 0.15rem 0.5rem;
            border-radius: 2px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.35rem;
        }

        /* Filter panel container */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--gray-200) !important;
            border-radius: 4px !important;
            padding: 0.5rem 1rem 1rem 1rem !important;
            margin-bottom: 2rem !important;
        }
        .filter-panel-title {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--gray-400);
            margin-bottom: 1.5rem;
        }
        .filter-step-label {
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--gray-600);
            margin-bottom: 0.35rem;
        }
        .filter-step-hint {
            font-size: 0.82rem;
            color: var(--gray-400);
            margin-top: 0.25rem;
        }

        /* Active filter chips */
        .active-filters {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1.25rem;
            padding-top: 1.25rem;
            border-top: 1px solid var(--gray-200);
        }
        .filter-chip {
            background: var(--gray-100);
            border: 1px solid var(--gray-200);
            color: var(--gray-900);
            padding: 0.35rem 0.75rem;
            border-radius: 2px;
            font-size: 0.78rem;
            font-weight: 500;
        }
        .filter-chip strong {
            color: var(--gray-400);
            font-weight: 600;
            margin-right: 0.25rem;
        }

        /* Tabs — underline style */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 1px solid var(--gray-200);
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            border-radius: 0;
            padding: 0.85rem 1.5rem;
            font-weight: 500;
            font-size: 0.9rem;
            color: var(--gray-600) !important;
            border-bottom: 2px solid transparent;
        }
        .stTabs [aria-selected="true"] {
            color: var(--black) !important;
            border-bottom: 2px solid var(--black) !important;
            background: transparent !important;
        }

        /* Inputs */
        .stTextInput input, .stSelectbox > div > div, .stMultiSelect > div > div {
            border-radius: 2px !important;
            border-color: var(--gray-200) !important;
        }
        .stSlider [data-baseweb="slider"] div { font-size: 0.85rem; }

        /* Buttons */
        .stButton > button {
            background: var(--black) !important;
            color: white !important;
            border-radius: 2px !important;
            border: none !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.02em;
            padding: 0.55rem 1.25rem !important;
        }
        .stButton > button:hover {
            background: var(--gray-900) !important;
        }
        .stLinkButton > a {
            border-radius: 2px !important;
            border: 1px solid var(--gray-200) !important;
            background: white !important;
            color: var(--black) !important;
            font-weight: 500 !important;
        }

        /* Cards */
        .profile-card {
            border: 1px solid var(--gray-200);
            border-radius: 4px;
            padding: 2rem;
            margin: 1rem 0;
        }
        .profile-card h2 { margin-top: 0; font-size: 1.5rem; }
        .stat-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--gray-400);
            margin-bottom: 0.25rem;
        }
        .stat-value { font-size: 1.35rem; font-weight: 600; color: var(--black); }
        .stat-value.accent { color: var(--accent); }

        .resource-card {
            border: 1px solid var(--gray-200);
            border-radius: 4px;
            padding: 1.25rem;
            margin-bottom: 0.5rem;
            height: 100%;
        }
        .resource-cat {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--gray-400);
        }
        .resource-name {
            font-size: 1rem;
            font-weight: 600;
            color: var(--black);
            margin: 0.4rem 0;
        }
        .resource-desc {
            font-size: 0.88rem;
            color: var(--gray-600);
            line-height: 1.5;
            margin: 0;
        }

        .map-placeholder {
            border: 1px dashed var(--gray-200);
            border-radius: 4px;
            padding: 2.5rem;
            text-align: center;
            color: var(--gray-600);
            margin-bottom: 1.5rem;
        }

        .disclaimer-line {
            font-size: 0.8rem;
            color: var(--gray-400);
            line-height: 1.5;
            border-top: 1px solid var(--gray-200);
            padding-top: 1.5rem;
            margin-top: 2rem;
        }

        .stDataFrame { border: 1px solid var(--gray-200); border-radius: 4px; }

        /* Table filter sub-panel */
        .table-filters-label {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--gray-400);
            margin: 1.5rem 0 0.75rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def format_distance(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return f"{value:.0f}"


def get_consideration_message(row: pd.Series) -> tuple[str, str]:
    if row.get("birth_center"):
        return (
            "Best suited for low-risk pregnancies seeking midwifery-led, low-intervention care. "
            "Hospital transfer is part of the safety plan if needed.",
            "success",
        )
    if row.get("high_risk") or "complex" in str(row.get("key_strength", "")).lower():
        return (
            "Strong choice for higher-risk pregnancies. Ask about maternal-fetal medicine during your tour.",
            "info",
        )
    return (
        "Well-rounded option for most births. Schedule a tour to see if it feels right.",
        "info",
    )


def render_hero() -> None:
    st.markdown(
        f"""
        <div class="tesla-hero">
            <h1>ATL Birth Hub</h1>
            <p class="subtitle">Compare birthing hospitals and birth centers across Metro Atlanta — costs, quality, and distance from home.</p>
            <p class="tesla-meta">Updated {datetime.now().strftime('%b %d, %Y')} · 60-mile radius</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_coverage_notice(
    db_total: int,
    in_radius: int,
    db_hospitals: int,
    radius_hospitals: int,
) -> None:
    birth_centers = db_total - db_hospitals
    st.markdown(
        f"""
        <div class="coverage-banner">
            <div class="title">Coverage</div>
            <p class="body">
                <span class="count">{in_radius} showing</span>
                from <strong>{db_total} facilities</strong> in our database
                ({db_hospitals} hospitals, {birth_centers} birth center(s) within 60 mi of Atlanta).
                Your filter: {radius_hospitals} hospitals in current radius.
                {COVERAGE_NOTE}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_filter_panel() -> tuple[str, float, list[str]]:
    """Main filter control panel — always visible, clearly labeled."""
    st.markdown('<div class="filter-panel-title">Personalize your search</div>', unsafe_allow_html=True)

    # Step 1: Location
    col_zip, col_radius, col_results = st.columns([1, 2, 1])
    with col_zip:
        st.markdown('<div class="filter-step-label">① Your ZIP code</div>', unsafe_allow_html=True)
        user_zip = st.text_input(
            "ZIP",
            value=DEFAULT_ZIP,
            max_chars=5,
            label_visibility="collapsed",
            placeholder="30341",
        )
        st.markdown('<div class="filter-step-hint">Where you live</div>', unsafe_allow_html=True)

    with col_radius:
        st.markdown('<div class="filter-step-label">② Max drive distance</div>', unsafe_allow_html=True)
        max_distance = st.slider(
            "Miles",
            min_value=10,
            max_value=60,
            value=40,
            step=5,
            label_visibility="collapsed",
            format="%d mi",
        )
        st.markdown(
            f'<div class="filter-step-hint">Showing facilities within <strong>{max_distance} miles</strong></div>',
            unsafe_allow_html=True,
        )

    with col_results:
        st.markdown('<div class="filter-step-label">③ Results</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="filter-step-hint" style="margin-top:0.5rem;">Updates as you adjust filters above</div>',
            unsafe_allow_html=True,
        )

    # Step 2: Priorities
    st.markdown('<div class="filter-step-label" style="margin-top:1.5rem;">④ What matters most</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="filter-step-hint">Select one or more — we\'ll rank facilities by how well they match</div>',
        unsafe_allow_html=True,
    )

    priority_cols = st.columns(3)
    selected: list[str] = []
    for i, priority in enumerate(PRIORITY_OPTIONS):
        with priority_cols[i % 3]:
            if st.checkbox(
                priority,
                value=priority in ["Lower costs", "Strong midwifery support"],
                key=f"prio_{priority}",
                help=PRIORITY_LABELS.get(priority, ""),
            ):
                selected.append(priority)

    return user_zip, max_distance, selected


def render_active_filters(
    zip_code: str,
    radius: float,
    priorities: list[str],
    result_count: int,
) -> None:
    chips = [
        f"<span class='filter-chip'><strong>ZIP</strong> {zip_code}</span>",
        f"<span class='filter-chip'><strong>Radius</strong> {radius:.0f} mi</span>",
        f"<span class='filter-chip'><strong>Showing</strong> {result_count} facilities</span>",
    ]
    for p in priorities:
        chips.append(f"<span class='filter-chip'><strong>Priority</strong> {p}</span>")
    if not priorities:
        chips.append("<span class='filter-chip'><strong>Priority</strong> None selected</span>")

    st.markdown(
        f'<div class="active-filters">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )


def render_summary_metrics(df: pd.DataFrame, priorities: list[str]) -> None:
    cols = st.columns(4)
    avg = df["vaginal_cost"].dropna().mean()
    avg_q = df["quality_rating"].dropna().mean()

    with cols[0]:
        st.metric("In your radius", len(df))
    with cols[1]:
        st.metric("Avg. vaginal cost", f"${avg:,.0f}" if pd.notna(avg) else "—")
    with cols[2]:
        st.metric("Avg. quality", f"{avg_q:.1f}/5" if pd.notna(avg_q) else "—")
    with cols[3]:
        if priorities:
            st.metric("Best match", df.iloc[0]["name"].split()[0])
        elif df["distance_miles"].notna().any():
            st.metric("Nearest", df.loc[df["distance_miles"].idxmin()]["name"].split()[0])
        else:
            st.metric("Nearest", "—")


def render_compare_tab(df: pd.DataFrame) -> None:
    st.markdown("### Compare")
    st.caption("Side-by-side view. All costs are facility estimates before insurance.")

    st.markdown('<div class="table-filters-label">Refine this table</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1])
    with c1:
        search = st.text_input("Search", placeholder="Hospital name or city…", label_visibility="visible")
    with c2:
        available_ratings = sorted(
            {q for q in df["quality_label"].dropna().unique()}
            | set(QUALITY_FILTER_OPTIONS)
        )
        rating_filter = st.multiselect(
            "Quality level",
            available_ratings,
            default=available_ratings,
        )
    with c3:
        sort_by = st.selectbox(
            "Sort by",
            ["Match %", "Distance", "Cost", "Quality", "C-section rate"],
        )
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear", use_container_width=True):
            st.rerun()

    filtered = df.copy()
    if search:
        mask = filtered.apply(
            lambda row: search.lower() in str(row["name"]).lower()
            or search.lower() in str(row.get("location", "")).lower(),
            axis=1,
        )
        filtered = filtered[mask]
    if rating_filter:
        filtered = filtered[filtered["quality_label"].isin(rating_filter)]

    sort_map = {
        "Match %": ("match_score", False),
        "Distance": ("distance_miles", True),
        "Cost": ("vaginal_cost", True),
        "Quality": ("quality_rating", False),
        "C-section rate": ("csection_rate", True),
    }
    col_name, ascending = sort_map[sort_by]
    filtered = filtered.sort_values(col_name, ascending=ascending, na_position="last")

    display = filtered.copy()
    display["Distance"] = display["distance_miles"].apply(lambda x: f"{format_distance(x)} mi")
    display["Match"] = display["match_score"].apply(lambda x: f"{x:.0f}%")

    st.dataframe(
        display[
            [
                "name", "location", "vaginal_cost_display", "csection_cost_display",
                "quality_label", "csection_rate_display", "key_strength", "Distance", "Match",
            ]
        ].rename(columns={
            "name": "Facility",
            "location": "Area",
            "vaginal_cost_display": "Vaginal est.",
            "csection_cost_display": "C-section est.",
            "quality_label": "Quality",
            "csection_rate_display": "C-section rate",
            "key_strength": "Strength",
            "Match": "Match",
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Vaginal est.": st.column_config.TextColumn(help="Facility charge range before insurance."),
            "C-section est.": st.column_config.TextColumn(help="Facility charge range for cesarean delivery."),
            "C-section rate": st.column_config.TextColumn(help="Low-risk C-section rate. Discuss with your provider."),
            "Match": st.column_config.TextColumn(help="Alignment with your selected priorities."),
        },
    )

    if filtered.empty:
        st.info("No matches. Widen your radius or clear table filters.")


def render_profiles_tab(df: pd.DataFrame) -> None:
    st.markdown("### Profiles")
    st.caption("Full detail on one facility at a time.")

    selected = st.selectbox("Select facility", df["name"].tolist())
    if not selected:
        return

    row = df[df["name"] == selected].iloc[0]
    dist = format_distance(row.get("distance_miles"))

    st.markdown(
        f"""
        <div class="profile-card">
            <h2>{selected}</h2>
            <p style="color:#525252; margin-bottom:1.5rem;">{row['location']} · {dist} mi from your ZIP</p>
            <div style="display:flex; gap:3rem; flex-wrap:wrap;">
                <div><div class="stat-label">Vaginal</div><div class="stat-value accent">{row['vaginal_cost_display']}</div></div>
                <div><div class="stat-label">C-section</div><div class="stat-value">{row['csection_cost_display']}</div></div>
                <div><div class="stat-label">Match</div><div class="stat-value">{row['match_score']:.0f}%</div></div>
                <div><div class="stat-label">Quality</div><div class="stat-value">{row['quality_label']}</div></div>
            </div>
            <div style="margin-top:1.5rem; padding-top:1.5rem; border-top:1px solid #E5E5E5;">
                <div class="stat-label">Strength</div>
                <p style="color:#525252; margin:0.25rem 0 0 0;">{row['key_strength']} — {row['strengths']}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    message, alert_type = get_consideration_message(row)
    (st.success if alert_type == "success" else st.info)(message)
    st.markdown(f"**Consider:** {row['considerations']}")


def render_map_tab(df: pd.DataFrame, user_zip: str) -> None:
    st.markdown("### Map")
    st.caption(f"Facilities within your radius of ZIP {user_zip}.")

    st.markdown(
        """
        <div class="map-placeholder">
            <p style="margin:0; font-weight:500; color:#171717;">Interactive map coming soon</p>
            <p style="margin:0.5rem 0 0 0; font-size:0.88rem;">Drive times, clickable pins, and nearby resources.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    map_df = df[["latitude", "longitude"]].dropna()
    if not map_df.empty:
        st.map(map_df.rename(columns={"latitude": "lat", "longitude": "lon"}), zoom=9.5)


def render_resources_tab() -> None:
    st.markdown("### Resources")
    st.caption("Local support beyond the hospital stay.")

    resources = load_resources()
    for category in resources["category"].unique():
        st.markdown(f"**{category}**")
        cat_df = resources[resources["category"] == category]
        cols = st.columns(2)
        for idx, (_, r) in enumerate(cat_df.iterrows()):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="resource-card">
                        <div class="resource-cat">{r['category']}</div>
                        <div class="resource-name">{r['name']}</div>
                        <p class="resource-desc">{r['description']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.link_button("Open", r["link"], use_container_width=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    render_hero()

    full_df = load_facilities()
    db_total = len(full_df)
    db_hospitals = int((full_df["type"] == "Hospital").sum())

    with st.container(border=True):
        user_zip, max_distance, priorities = render_filter_panel()

        zip_clean = str(user_zip).strip()[:5]
        if not zip_clean.isdigit() or len(zip_clean) != 5:
            st.warning("Enter a valid 5-digit ZIP code.")
            zip_clean = DEFAULT_ZIP

        df = prepare_facility_data(zip_clean, max_distance, priorities)
        render_active_filters(zip_clean, max_distance, priorities, len(df))

    radius_hospitals = int((df["type"] == "Hospital").sum()) if not df.empty else 0
    render_coverage_notice(db_total, len(df), db_hospitals, radius_hospitals)

    if df.empty:
        st.warning("No facilities in this radius. Increase max drive distance above.")
        return

    render_summary_metrics(df, priorities)

    t1, t2, t3, t4 = st.tabs(["Compare", "Profiles", "Map", "Resources"])

    with t1:
        render_compare_tab(df)
    with t2:
        render_profiles_tab(df)
    with t3:
        render_map_tab(df, zip_clean)
    with t4:
        render_resources_tab()

    st.markdown(
        """
        <p class="disclaimer-line">
        Costs are illustrative ranges, not guaranteed prices. This is not medical or financial advice.
        Always request a Good Faith Estimate and verify with your provider and hospital billing office.
        </p>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()