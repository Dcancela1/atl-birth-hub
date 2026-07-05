"""
ATL Birth Hub — Georgia Birth Facility Explorer
Soft pink & white design with sidebar filters, result cards, and Folium map.
"""

from __future__ import annotations

import copy

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from data_ingestion import (
    COVERAGE_NOTE,
    DEFAULT_ZIP,
    add_distance_column,
    apply_filters,
    load_facilities,
)
from filters_config import (
    DEFAULT_FILTERS,
    GEORGIA_REGIONS,
    INSURANCE_OPTIONS,
    QUALITY_METRIC_OPTIONS,
    QUALITY_SCORE_OPTIONS,
    SERVICE_OPTIONS,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ATL Birth Hub",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

PINK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    :root {
        --pink-50: #FFF5F7;
        --pink-100: #FFE4EC;
        --pink-200: #FECDD6;
        --pink-300: #FDA4B8;
        --pink-400: #FB7195;
        --pink-500: #F43F68;
        --blush: #F9E8EE;
        --white: #FFFFFF;
        --text: #4A3040;
        --muted: #8B6B7A;
        --border: #F3D4DF;
    }

    .stApp { background: var(--pink-50); font-family: 'Nunito', sans-serif; }
    #MainMenu, footer { visibility: hidden; }

    .block-container { padding-top: 4.5rem; max-width: 1200px; }

    /* Top bar */
    .top-bar {
        position: fixed; top: 0; left: 0; right: 0; z-index: 999;
        background: var(--white); border-bottom: 1px solid var(--border);
        padding: 0.65rem 1.5rem; display: flex; align-items: center; gap: 1rem;
        box-shadow: 0 2px 16px rgba(244,63,104,0.06);
    }
    .top-logo { font-size: 1.5rem; }
    .top-title {
        font-family: 'Playfair Display', serif; font-size: 1.15rem;
        font-weight: 700; color: var(--pink-500); white-space: nowrap;
    }
    .top-sub { font-size: 0.72rem; color: var(--muted); }
    .top-right { margin-left: auto; display: flex; gap: 0.75rem; align-items: center; }
    .top-pill {
        background: var(--pink-100); color: var(--pink-500);
        padding: 0.35rem 0.85rem; border-radius: 100px;
        font-size: 0.8rem; font-weight: 600;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--white) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--pink-500) !important;
        font-family: 'Playfair Display', serif !important;
        font-size: 0.95rem !important;
        margin-top: 1rem !important;
    }

    /* Headings */
    h1, h2, h3, [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
        color: var(--text) !important;
        font-family: 'Playfair Display', serif !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid var(--border); }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; color: var(--muted) !important;
        font-weight: 600; border-radius: 8px 8px 0 0; padding: 0.6rem 1.2rem;
    }
    .stTabs [aria-selected="true"] {
        color: var(--pink-500) !important;
        border-bottom: 2px solid var(--pink-400) !important;
        background: var(--pink-50) !important;
    }

    /* Buttons */
    .stButton > button[kind="primary"], .stButton > button {
        background: var(--pink-400) !important; color: white !important;
        border: none !important; border-radius: 8px !important; font-weight: 600 !important;
    }
    .stButton > button:hover { background: var(--pink-500) !important; }

    /* Result cards */
    .result-card {
        background: var(--white); border: 1px solid var(--border);
        border-radius: 16px; padding: 1.35rem 1.5rem; margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(253,164,184,0.12);
        transition: transform 0.15s ease;
    }
    .result-card:hover { transform: translateY(-2px); }
    .card-name {
        font-family: 'Playfair Display', serif; font-size: 1.2rem;
        font-weight: 700; color: var(--text); margin: 0 0 0.2rem 0;
    }
    .card-meta { font-size: 0.85rem; color: var(--muted); margin-bottom: 0.75rem; }
    .quality-badge {
        display: inline-block; background: var(--pink-100); color: var(--pink-500);
        padding: 0.2rem 0.65rem; border-radius: 100px;
        font-size: 0.75rem; font-weight: 700;
    }
    .highlight-chip {
        display: inline-block; background: var(--blush); color: var(--text);
        padding: 0.2rem 0.55rem; border-radius: 6px;
        font-size: 0.72rem; margin: 0.15rem 0.2rem 0.15rem 0;
    }
    .card-stat { font-size: 0.8rem; color: var(--muted); }
    .card-stat strong { color: var(--text); }

    .empty-state {
        text-align: center; padding: 3rem; color: var(--muted);
        background: var(--white); border-radius: 16px; border: 1px dashed var(--border);
    }

    .coverage-note {
        font-size: 0.8rem; color: var(--muted); line-height: 1.5;
        background: var(--pink-50); border-radius: 8px; padding: 0.75rem 1rem;
        border: 1px solid var(--border); margin-bottom: 1rem;
    }
</style>
"""
st.markdown(PINK_CSS, unsafe_allow_html=True)


def init_state() -> None:
    if "applied_filters" not in st.session_state:
        st.session_state.applied_filters = copy.deepcopy(DEFAULT_FILTERS)
    if "saved_ids" not in st.session_state:
        st.session_state.saved_ids = set()
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""


def render_top_bar(saved_count: int) -> None:
    st.markdown(
        f"""
        <div class="top-bar">
            <span class="top-logo">🌸</span>
            <div>
                <div class="top-title">ATL Birth Hub</div>
                <div class="top-sub">Find your birth space in Georgia</div>
            </div>
            <div class="top-right">
                <span class="top-pill">♥ Saved ({saved_count})</span>
                <span class="top-pill">Profile</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filters() -> dict:
    """Render filter UI; return draft filter dict (applied on button click)."""
    st.sidebar.markdown("### Filters")
    st.sidebar.caption("Set your preferences, then tap **Apply Filters**.")

    draft = copy.deepcopy(st.session_state.applied_filters)

    st.sidebar.markdown("#### 📍 Location")
    draft["regions"] = st.sidebar.multiselect(
        "Georgia regions",
        GEORGIA_REGIONS,
        default=st.session_state.applied_filters.get("regions", []),
        placeholder="All regions (statewide)",
    )
    draft["distance_mode"] = st.sidebar.radio(
        "Distance",
        ["Statewide", "Near my ZIP"],
        index=0 if st.session_state.applied_filters.get("distance_mode") == "Statewide" else 1,
        horizontal=True,
    )
    if draft["distance_mode"] == "Near my ZIP":
        draft["user_zip"] = st.sidebar.text_input("ZIP code", value=st.session_state.applied_filters.get("user_zip", DEFAULT_ZIP), max_chars=5)
        draft["max_distance"] = st.sidebar.slider("Max miles", 10, 120, int(st.session_state.applied_filters.get("max_distance", 60)), step=5)
    else:
        draft["user_zip"] = st.session_state.applied_filters.get("user_zip", DEFAULT_ZIP)

    st.sidebar.markdown("#### ⭐ Quality & Ratings")
    score_label = st.sidebar.selectbox(
        "Overall quality score",
        list(QUALITY_SCORE_OPTIONS.keys()),
        index=list(QUALITY_SCORE_OPTIONS.values()).index(st.session_state.applied_filters.get("min_quality_score", 0)),
    )
    draft["min_quality_score"] = QUALITY_SCORE_OPTIONS[score_label]
    draft["quality_metrics"] = st.sidebar.multiselect(
        "Quality metrics",
        QUALITY_METRIC_OPTIONS,
        default=st.session_state.applied_filters.get("quality_metrics", []),
    )

    st.sidebar.markdown("#### 💕 Services Offered")
    draft["services"] = st.sidebar.multiselect(
        "Services",
        SERVICE_OPTIONS,
        default=st.session_state.applied_filters.get("services", []),
        placeholder="Any service",
    )

    st.sidebar.markdown("#### 💳 Price & Insurance")
    price = st.sidebar.slider(
        "Vaginal delivery estimate ($)",
        4000, 25000,
        (
            int(st.session_state.applied_filters.get("price_min", 4000)),
            int(st.session_state.applied_filters.get("price_max", 25000)),
        ),
        step=500,
    )
    draft["price_min"], draft["price_max"] = price
    draft["insurance"] = st.sidebar.multiselect(
        "Insurance accepted",
        INSURANCE_OPTIONS,
        default=st.session_state.applied_filters.get("insurance", []),
        placeholder="Any insurance",
    )

    with st.sidebar.expander("Additional filters"):
        draft["min_births_per_year"] = st.slider(
            "Min. births per year",
            0, 4000,
            int(st.session_state.applied_filters.get("min_births_per_year", 0)),
            step=100,
        )
        draft["min_years_operation"] = st.slider(
            "Min. years in operation",
            0, 80,
            int(st.session_state.applied_filters.get("min_years_operation", 0)),
        )

    col_a, col_b = st.sidebar.columns(2)
    with col_a:
        if st.button("Apply Filters", type="primary", use_container_width=True):
            st.session_state.applied_filters = draft
            st.rerun()
    with col_b:
        if st.button("Reset All", use_container_width=True):
            st.session_state.applied_filters = copy.deepcopy(DEFAULT_FILTERS)
            st.session_state.search_query = ""
            st.rerun()

    return draft


def render_result_card(row: pd.Series, show_save: bool = True) -> None:
    fid = row["facility_id"]
    saved = fid in st.session_state.saved_ids
    dist = row.get("distance_miles")
    dist_txt = f"{dist:.0f} mi away" if pd.notna(dist) else row.get("region", "Georgia")

    services = row.get("services", [])
    if isinstance(services, str):
        services = services.split("|") if services else []
    chips = "".join(f'<span class="highlight-chip">{s}</span>' for s in services[:4])

    st.markdown(
        f"""
        <div class="result-card">
            <div style="display:flex;justify-content:space-between;align-items:start;">
                <div>
                    <p class="card-name">{row['name']}</p>
                    <p class="card-meta">{row.get('location','')} · {row.get('region','')} · {dist_txt}</p>
                </div>
                <span class="quality-badge">{row.get('quality_score', 70)}% quality</span>
            </div>
            <div style="margin:0.5rem 0;">{chips}</div>
            <div class="card-stat">
                <strong>Vaginal:</strong> {row.get('vaginal_cost_display','—')} &nbsp;·&nbsp;
                <strong>C-section:</strong> {row.get('csection_cost_display','—')} &nbsp;·&nbsp;
                <strong>{row.get('key_strength', row.get('quality_label',''))}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if show_save:
        label = "♥ Saved" if saved else "♡ Save"
        if st.button(label, key=f"save_{fid}"):
            if saved:
                st.session_state.saved_ids.discard(fid)
            else:
                st.session_state.saved_ids.add(fid)
            st.rerun()


def render_search_tab(df: pd.DataFrame) -> None:
    st.markdown(f'<p class="coverage-note">{COVERAGE_NOTE}</p>', unsafe_allow_html=True)
    st.caption(f"**{len(df)}** places match your filters")

    if df.empty:
        st.markdown(
            '<div class="empty-state"><p>No facilities match your filters.</p>'
            '<p>Try <strong>Reset All</strong> or widen your search.</p></div>',
            unsafe_allow_html=True,
        )
        return

    sort = st.selectbox("Sort by", ["Quality score", "Price (low)", "Distance", "Name"], label_visibility="collapsed")
    sorted_df = df.copy()
    if sort == "Quality score":
        sorted_df = sorted_df.sort_values("quality_score", ascending=False)
    elif sort == "Price (low)":
        sorted_df = sorted_df.sort_values("vaginal_cost", ascending=True, na_position="last")
    elif sort == "Distance":
        sorted_df = sorted_df.sort_values("distance_miles", ascending=True, na_position="last")
    else:
        sorted_df = sorted_df.sort_values("name")

    for _, row in sorted_df.iterrows():
        render_result_card(row)


def render_map_tab(df: pd.DataFrame) -> None:
    st.caption("Explore birthing facilities across Georgia. Click a pin for details.")

    if df.empty:
        st.info("Apply filters with at least one result to see the map.")
        return

    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="CartoDB positron")

    cluster = MarkerCluster(name="Facilities").add_to(m)
    for _, row in df.iterrows():
        if pd.isna(row.get("latitude")):
            continue
        popup = (
            f"<b>{row['name']}</b><br>"
            f"{row.get('region','')}<br>"
            f"Quality: {row.get('quality_score',70)}%<br>"
            f"{row.get('vaginal_cost_display','')}"
        )
        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=popup,
            tooltip=row["name"],
            icon=folium.Icon(color="lightred", icon="plus"),
        ).add_to(cluster)

    st_folium(m, width=None, height=500, returned_objects=[])


def render_saved_tab(all_df: pd.DataFrame) -> None:
    saved = all_df[all_df["facility_id"].isin(st.session_state.saved_ids)]
    st.caption("Your saved places — perfect for comparing tours later.")

    if saved.empty:
        st.markdown(
            '<div class="empty-state"><p>No saved places yet.</p>'
            '<p>Tap <strong>♡ Save</strong> on any result card.</p></div>',
            unsafe_allow_html=True,
        )
        return

    for _, row in saved.iterrows():
        render_result_card(row)


def render_profile_panel() -> None:
    with st.expander("Profile & preferences", expanded=False):
        st.markdown("**Guest mode** — browsing without an account.")
        st.caption("Future versions may add due-date reminders and saved birth plans.")
        st.markdown(f"**Saved places:** {len(st.session_state.saved_ids)}")


def main() -> None:
    init_state()
    all_facilities = load_facilities()

    render_top_bar(len(st.session_state.saved_ids))
    render_sidebar_filters()

    # Central search bar (below fixed top bar)
    st.session_state.search_query = st.text_input(
        "Search",
        value=st.session_state.search_query,
        placeholder="Search hospitals, cities, or regions…",
        label_visibility="collapsed",
    )

    filters = copy.deepcopy(st.session_state.applied_filters)
    filters["search_query"] = st.session_state.search_query

    user_zip = filters.get("user_zip", DEFAULT_ZIP)
    if filters.get("distance_mode") == "Near my ZIP":
        zip_clean = str(user_zip).strip()[:5]
        if not zip_clean.isdigit() or len(zip_clean) != 5:
            st.warning("Enter a valid 5-digit ZIP for distance filtering.")
            zip_clean = DEFAULT_ZIP
    else:
        zip_clean = None

    filtered = apply_filters(all_facilities, filters, user_zip=zip_clean)

    render_profile_panel()

    tab_search, tab_map, tab_saved = st.tabs(["🔍 Search", "🗺️ Map", "♥ Saved"])

    with tab_search:
        render_search_tab(filtered)
    with tab_map:
        render_map_tab(filtered)
    with tab_saved:
        render_saved_tab(all_facilities)

    st.caption(
        "Costs are illustrative estimates — not guaranteed prices. Not medical or financial advice. "
        "Always request a Good Faith Estimate from your facility."
    )


if __name__ == "__main__":
    main()