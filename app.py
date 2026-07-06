"""
Atlanta Birth Hub — Premium Georgia birth facility explorer.
Designed for expecting mothers: warm, trustworthy, and beautifully clear.
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
    apply_filters,
    load_facilities,
    load_resources,
)
from filters_config import (
    DEFAULT_FILTERS,
    GEORGIA_REGIONS,
    INSURANCE_OPTIONS,
    QUALITY_METRIC_OPTIONS,
    QUALITY_SCORE_OPTIONS,
    SERVICE_OPTIONS,
)

st.set_page_config(
    page_title="Atlanta Birth Hub",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

PREMIUM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

    :root {
        --blush-50: #FFF9FA;
        --blush-100: #FFF0F3;
        --blush-200: #FFE1E8;
        --blush-300: #F9C5D1;
        --rose-400: #E891A8;
        --rose-500: #D9728E;
        --sage-400: #7DB5A8;
        --sage-500: #5D9C8E;
        --sage-50: #EFF7F4;
        --white: #FFFFFF;
        --cream: #FDFBF9;
        --text: #3D2F35;
        --muted: #7A6570;
        --border: #F0E4E8;
        --shadow: 0 8px 32px rgba(217, 114, 142, 0.08);
        --shadow-hover: 0 12px 40px rgba(217, 114, 142, 0.14);
    }

    .stApp {
        background: linear-gradient(180deg, var(--blush-50) 0%, var(--cream) 100%);
        font-family: 'DM Sans', sans-serif;
        color: var(--text);
    }
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 1rem; max-width: 1140px; }

    /* Hero */
    .premium-hero {
        background: linear-gradient(135deg, #FFF5F7 0%, #FFFFFF 45%, #EFF7F4 100%);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 2.5rem 2rem 2rem 2rem;
        margin-bottom: 1.25rem;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    .premium-hero::before {
        content: '';
        position: absolute; top: -40%; right: -8%;
        width: 280px; height: 280px;
        background: radial-gradient(circle, rgba(232,145,168,0.18) 0%, transparent 70%);
        border-radius: 50%;
    }
    .premium-hero::after {
        content: '';
        position: absolute; bottom: -30%; left: -5%;
        width: 200px; height: 200px;
        background: radial-gradient(circle, rgba(93,156,142,0.12) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-eyebrow {
        font-size: 0.72rem; font-weight: 600; letter-spacing: 0.14em;
        text-transform: uppercase; color: var(--sage-500);
        margin-bottom: 0.5rem; position: relative; z-index: 1;
    }
    .hero-title {
        font-family: 'Fraunces', serif;
        font-size: 2.6rem; font-weight: 700;
        color: var(--text); margin: 0 0 0.65rem 0;
        letter-spacing: -0.02em; line-height: 1.15;
        position: relative; z-index: 1;
    }
    .hero-tagline {
        font-size: 1.08rem; color: var(--muted);
        line-height: 1.6; max-width: 620px; margin: 0;
        position: relative; z-index: 1;
    }
    .hero-trust {
        display: flex; flex-wrap: wrap; gap: 0.5rem;
        margin-top: 1.25rem; position: relative; z-index: 1;
    }
    .trust-pill {
        background: var(--white); border: 1px solid var(--border);
        color: var(--muted); padding: 0.35rem 0.8rem;
        border-radius: 100px; font-size: 0.78rem; font-weight: 500;
    }
    .trust-pill.sage { background: var(--sage-50); color: var(--sage-500); border-color: #C5E4DC; }

    /* Search strip */
    .search-strip {
        background: var(--white); border: 1px solid var(--border);
        border-radius: 14px; padding: 0.85rem 1rem;
        margin-bottom: 1rem; box-shadow: 0 2px 12px rgba(0,0,0,0.03);
    }
    .search-label {
        font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; color: var(--muted); margin-bottom: 0.35rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--white) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] h3 {
        font-family: 'Fraunces', serif !important;
        color: var(--rose-500) !important;
        font-size: 0.92rem !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--rose-400) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
        background: var(--white) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
    }

    /* Typography */
    h1, h2, h3, [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
        color: var(--text) !important;
        font-family: 'Fraunces', serif !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem; border-bottom: 1px solid var(--border); background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; color: var(--muted) !important;
        font-weight: 600; font-size: 0.92rem;
        padding: 0.7rem 1.25rem; border-radius: 10px 10px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: var(--rose-500) !important;
        background: var(--blush-50) !important;
        border-bottom: 2px solid var(--rose-400) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .main .stButton > button {
        background: var(--blush-100) !important;
        color: var(--rose-500) !important;
        border: 1px solid var(--border) !important;
    }
    .main .stButton > button:hover {
        background: var(--blush-200) !important;
        transform: translateY(-1px);
    }

    /* Result cards */
    .result-card {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1.5rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .result-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-hover);
    }
    .card-header {
        display: flex; justify-content: space-between;
        align-items: flex-start; gap: 1rem; flex-wrap: wrap;
    }
    .card-name {
        font-family: 'Fraunces', serif;
        font-size: 1.28rem; font-weight: 600;
        color: var(--text); margin: 0 0 0.3rem 0; line-height: 1.3;
    }
    .card-meta {
        font-size: 0.86rem; color: var(--muted); margin: 0;
    }
    .card-type {
        display: inline-block; font-size: 0.68rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.06em;
        color: var(--sage-500); background: var(--sage-50);
        padding: 0.15rem 0.5rem; border-radius: 4px; margin-top: 0.35rem;
    }
    .quality-badge {
        display: inline-flex; align-items: center; gap: 0.3rem;
        padding: 0.45rem 0.85rem; border-radius: 12px;
        font-size: 0.8rem; font-weight: 700; white-space: nowrap;
    }
    .quality-badge.excellent { background: var(--sage-50); color: var(--sage-500); border: 1px solid #B8DDD4; }
    .quality-badge.strong { background: var(--blush-100); color: var(--rose-500); border: 1px solid var(--blush-300); }
    .quality-badge.good { background: var(--cream); color: var(--muted); border: 1px solid var(--border); }
    .quality-badge .score { font-size: 1.05rem; }

    .chip-row { margin: 0.85rem 0 0.65rem 0; display: flex; flex-wrap: wrap; gap: 0.35rem; }
    .highlight-chip {
        background: var(--blush-50); color: var(--text);
        border: 1px solid var(--border);
        padding: 0.25rem 0.6rem; border-radius: 8px;
        font-size: 0.74rem; font-weight: 500;
    }
    .highlight-chip.sage {
        background: var(--sage-50); color: var(--sage-500); border-color: #C5E4DC;
    }
    .card-footer {
        display: flex; flex-wrap: wrap; gap: 1.25rem;
        padding-top: 0.85rem; margin-top: 0.85rem;
        border-top: 1px solid var(--border);
        font-size: 0.82rem; color: var(--muted);
    }
    .card-footer strong { color: var(--text); display: block; font-size: 0.68rem;
        text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.15rem; }

    /* Empty & loading states */
    .empty-state {
        text-align: center; padding: 3.5rem 2rem;
        background: var(--white); border-radius: 20px;
        border: 1px dashed var(--blush-300);
        margin: 1rem 0;
    }
    .empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
    .empty-title {
        font-family: 'Fraunces', serif; font-size: 1.25rem;
        color: var(--text); margin: 0 0 0.5rem 0;
    }
    .empty-body { color: var(--muted); font-size: 0.95rem; line-height: 1.6; max-width: 400px; margin: 0 auto; }

    .results-header {
        display: flex; justify-content: space-between; align-items: center;
        flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;
    }
    .results-count {
        font-size: 0.9rem; color: var(--muted);
    }
    .results-count strong { color: var(--text); font-size: 1.1rem; }

    /* About box */
    .about-box {
        background: var(--white); border: 1px solid var(--border);
        border-radius: 16px; padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem; font-size: 0.9rem;
        line-height: 1.65; color: var(--muted);
    }
    .about-box h4 {
        font-family: 'Fraunces', serif; color: var(--text);
        margin: 0 0 0.5rem 0; font-size: 1rem;
    }
    .about-box ul { margin: 0.5rem 0 0 1.1rem; padding: 0; }
    .about-box li { margin-bottom: 0.35rem; }

    /* Trust footer */
    .trust-footer {
        margin-top: 2.5rem; padding: 1.5rem 0 2rem 0;
        border-top: 1px solid var(--border);
        text-align: center;
    }
    .trust-footer .brand {
        font-family: 'Fraunces', serif; font-size: 0.95rem;
        color: var(--text); margin-bottom: 0.35rem;
    }
    .trust-footer p {
        font-size: 0.8rem; color: var(--muted);
        line-height: 1.6; max-width: 680px; margin: 0.25rem auto;
    }
    .trust-badges {
        display: flex; justify-content: center; flex-wrap: wrap;
        gap: 0.5rem; margin-top: 0.85rem;
    }
    .trust-badge {
        font-size: 0.72rem; font-weight: 600;
        color: var(--sage-500); background: var(--sage-50);
        padding: 0.3rem 0.75rem; border-radius: 100px;
    }

    /* Mobile */
    @media (max-width: 768px) {
        .hero-title { font-size: 1.85rem; }
        .hero-tagline { font-size: 0.95rem; }
        .premium-hero { padding: 1.75rem 1.25rem; border-radius: 18px; }
        .result-card { padding: 1.15rem 1.2rem; border-radius: 16px; }
        .card-name { font-size: 1.1rem; }
        .card-header { flex-direction: column; }
        .quality-badge { align-self: flex-start; }
        .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
        .stTabs [data-baseweb="tab"] { padding: 0.55rem 0.75rem; font-size: 0.82rem; }
    }

    /* Resource cards */
    .resource-card {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1.35rem 1.4rem;
        margin-bottom: 0.65rem;
        height: 100%;
        box-shadow: 0 4px 18px rgba(217, 114, 142, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .resource-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow);
    }
    .resource-icon { font-size: 1.6rem; margin-bottom: 0.45rem; }
    .resource-cat {
        font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; color: var(--sage-500);
    }
    .resource-name {
        font-family: 'Fraunces', serif;
        font-size: 1.05rem; font-weight: 600;
        color: var(--text); margin: 0.35rem 0 0.4rem 0; line-height: 1.35;
    }
    .resource-desc {
        font-size: 0.86rem; color: var(--muted);
        line-height: 1.55; margin: 0;
    }
    .resource-section-title {
        font-family: 'Fraunces', serif;
        font-size: 1.1rem; color: var(--text);
        margin: 1.5rem 0 0.85rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--border);
    }

    /* Spinner overlay feel */
    .stSpinner > div { border-top-color: var(--rose-400) !important; }
</style>
"""
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

QUALITY_SCORE_HELP = """
**How we calculate quality scores (0–100)**

Scores are a planning guide — not a medical recommendation.

- **CMS star ratings** (Hospital Compare) are converted to a 0–100 scale (5 stars ≈ 100)
- **Curated facilities** may blend star ratings with known strengths in maternity care
- **Birth centers** use accreditation and midwifery-model indicators

Always tour in person, talk with your provider, and check [Leapfrog Group](https://www.leapfroggroup.org/) for safety grades.
"""


@st.cache_data(show_spinner=False)
def get_facilities() -> pd.DataFrame:
    return load_facilities()


def init_state() -> None:
    defaults = ("applied_filters", "saved_ids", "search_query", "data_loaded")
    if "applied_filters" not in st.session_state:
        st.session_state.applied_filters = copy.deepcopy(DEFAULT_FILTERS)
    if "saved_ids" not in st.session_state:
        st.session_state.saved_ids = []
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""


def is_saved(facility_id: str) -> bool:
    return facility_id in st.session_state.saved_ids


def toggle_save(facility_id: str) -> None:
    """Toggle saved state — reassign list so Streamlit persists the change."""
    saved = list(st.session_state.saved_ids)
    if facility_id in saved:
        saved.remove(facility_id)
    else:
        saved.append(facility_id)
    st.session_state.saved_ids = saved


def quality_tier(score: int) -> tuple[str, str]:
    if score >= 90:
        return "excellent", "Excellent"
    if score >= 80:
        return "strong", "Strong"
    return "good", "Good"


def render_hero(saved_count: int, total_facilities: int) -> None:
    st.markdown(
        f"""
        <div class="premium-hero">
            <div class="hero-eyebrow">Made for expecting mothers in Georgia</div>
            <h1 class="hero-title">Atlanta Birth Hub</h1>
            <p class="hero-tagline">
                Helping expecting mothers find trusted, high-quality birth centers across Georgia —
                with calm guidance, clear costs, and the warmth you deserve.
            </p>
            <div class="hero-trust">
                <span class="trust-pill sage">✓ {total_facilities} verified listings</span>
                <span class="trust-pill">♥ {saved_count} saved</span>
                <span class="trust-pill">CMS Hospital Compare data</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_about_section() -> None:
    with st.expander("About this app & quality scores", expanded=False):
        st.markdown(QUALITY_SCORE_HELP)
        st.caption(COVERAGE_NOTE)


def render_empty_state(
    icon: str,
    title: str,
    body: str,
    hint: str | None = None,
) -> None:
    hint_html = f'<p style="margin-top:1rem;font-size:0.85rem;color:var(--sage-500);">{hint}</p>' if hint else ""
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-icon">{icon}</div>
            <p class="empty-title">{title}</p>
            <p class="empty-body">{body}</p>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filters() -> None:
    st.sidebar.markdown("### Your search")
    st.sidebar.caption("Take your time — there's no wrong way to explore.")

    draft = copy.deepcopy(st.session_state.applied_filters)

    st.sidebar.markdown("##### Location")
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
        draft["user_zip"] = st.sidebar.text_input(
            "ZIP code",
            value=st.session_state.applied_filters.get("user_zip", DEFAULT_ZIP),
            max_chars=5,
        )
        draft["max_distance"] = st.sidebar.slider(
            "Max miles", 10, 120,
            int(st.session_state.applied_filters.get("max_distance", 60)), step=5,
        )
    else:
        draft["user_zip"] = st.session_state.applied_filters.get("user_zip", DEFAULT_ZIP)

    st.sidebar.markdown("##### Quality & ratings")
    score_keys = list(QUALITY_SCORE_OPTIONS.keys())
    score_vals = list(QUALITY_SCORE_OPTIONS.values())
    current = st.session_state.applied_filters.get("min_quality_score", 0)
    draft["min_quality_score"] = QUALITY_SCORE_OPTIONS[st.sidebar.selectbox(
        "Overall quality score",
        score_keys,
        index=score_vals.index(current) if current in score_vals else 0,
        help="Based on CMS star ratings and curated maternity indicators. See 'About this app'.",
    )]
    draft["quality_metrics"] = st.sidebar.multiselect(
        "Quality highlights",
        QUALITY_METRIC_OPTIONS,
        default=st.session_state.applied_filters.get("quality_metrics", []),
    )

    st.sidebar.markdown("##### Services offered")
    draft["services"] = st.sidebar.multiselect(
        "Services",
        SERVICE_OPTIONS,
        default=st.session_state.applied_filters.get("services", []),
        placeholder="Any service",
    )

    st.sidebar.markdown("##### Price & insurance")
    price = st.sidebar.slider(
        "Estimated vaginal delivery cost ($)",
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
        placeholder="Any plan",
    )

    with st.sidebar.expander("More filters"):
        draft["min_births_per_year"] = st.slider(
            "Min. births per year", 0, 4000,
            int(st.session_state.applied_filters.get("min_births_per_year", 0)), step=100,
        )
        draft["min_years_operation"] = st.slider(
            "Min. years in operation", 0, 80,
            int(st.session_state.applied_filters.get("min_years_operation", 0)),
        )

    st.sidebar.markdown("---")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("Apply filters", type="primary", use_container_width=True):
            st.session_state.applied_filters = draft
            st.rerun()
    with c2:
        if st.button("Reset all", use_container_width=True):
            st.session_state.applied_filters = copy.deepcopy(DEFAULT_FILTERS)
            st.session_state.search_query = ""
            st.rerun()


def render_result_card(row: pd.Series, show_save: bool = True, key_prefix: str = "search") -> None:
    fid = str(row["facility_id"])
    saved = is_saved(fid)
    score = int(row.get("quality_score", 70))
    tier, tier_label = quality_tier(score)

    dist = row.get("distance_miles")
    dist_txt = f"{dist:.0f} mi from you" if pd.notna(dist) else str(row.get("region", "Georgia"))

    services = row.get("services", [])
    if isinstance(services, str):
        services = [s for s in services.split("|") if s]

    chips = ""
    for i, s in enumerate(services[:5]):
        cls = "highlight-chip sage" if s in ("NICU Available", "Birthing-Friendly Designation") else "highlight-chip"
        chips += f'<span class="{cls}">{s}</span>'

    facility_type = row.get("type", "Hospital")
    type_cls = "card-type"

    st.markdown(
        f"""
        <div class="result-card">
            <div class="card-header">
                <div>
                    <p class="card-name">{row['name']}</p>
                    <p class="card-meta">{row.get('location', '')} · {dist_txt}</p>
                    <span class="{type_cls}">{facility_type}</span>
                </div>
                <div class="quality-badge {tier}" title="Planning guide — not medical advice">
                    <span class="score">{score}</span>
                    <span>{tier_label}</span>
                </div>
            </div>
            <div class="chip-row">{chips}</div>
            <div class="card-footer">
                <div><strong>Vaginal est.</strong>{row.get('vaginal_cost_display', '—')}</div>
                <div><strong>C-section est.</strong>{row.get('csection_cost_display', '—')}</div>
                <div><strong>Highlight</strong>{row.get('key_strength', row.get('quality_label', ''))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if show_save:
        btn_key = f"save_btn_{key_prefix}_{fid}"
        if st.button(
            "♥ Saved" if saved else "♡ Save to compare",
            key=btn_key,
            use_container_width=True,
        ):
            toggle_save(fid)
            st.rerun()


def render_search_tab(df: pd.DataFrame) -> None:
    st.markdown(
        f'<div class="results-header"><span class="results-count">'
        f'<strong>{len(df)}</strong> places match your search</span></div>',
        unsafe_allow_html=True,
    )

    if df.empty:
        render_empty_state(
            "🌸",
            "No centers match your filters",
            "Try broadening your search — reset filters, choose Statewide, or lower the quality score minimum.",
            "Tip: Start with one region or service, then narrow down.",
        )
        return

    sort = st.selectbox(
        "Sort results",
        ["Highest quality", "Lowest cost", "Nearest", "A–Z"],
        label_visibility="collapsed",
    )
    sorted_df = df.copy()
    if sort == "Highest quality":
        sorted_df = sorted_df.sort_values("quality_score", ascending=False)
    elif sort == "Lowest cost":
        sorted_df = sorted_df.sort_values("vaginal_cost", ascending=True, na_position="last")
    elif sort == "Nearest":
        sorted_df = sorted_df.sort_values("distance_miles", ascending=True, na_position="last")
    else:
        sorted_df = sorted_df.sort_values("name")

    for _, row in sorted_df.iterrows():
        render_result_card(row, key_prefix="search")


def render_map_tab(df: pd.DataFrame) -> None:
    st.caption("Tap a pin to explore — soft colors, real locations across Georgia.")

    if df.empty:
        render_empty_state(
            "🗺️",
            "No locations to show yet",
            "Adjust your filters and tap Apply — your map will bloom with options.",
        )
        return

    with st.spinner("Loading your map…"):
        m = folium.Map(
            location=[df["latitude"].mean(), df["longitude"].mean()],
            zoom_start=7,
            tiles="CartoDB positron",
        )
        cluster = MarkerCluster(name="Birth facilities").add_to(m)
        for _, row in df.iterrows():
            if pd.isna(row.get("latitude")):
                continue
            folium.Marker(
                [row["latitude"], row["longitude"]],
                popup=(
                    f"<b>{row['name']}</b><br>"
                    f"{row.get('region', '')}<br>"
                    f"Quality: {int(row.get('quality_score', 70))}/100"
                ),
                tooltip=row["name"],
                icon=folium.Icon(color="lightred", icon="heart"),
            ).add_to(cluster)
        st_folium(m, width=None, height=480, returned_objects=[])


def render_resources_tab() -> None:
    st.caption(
        "You don't have to figure this out alone — curated Georgia resources for every stage of your journey."
    )

    resources = load_resources()
    for category in resources["category"].unique():
        st.markdown(f'<p class="resource-section-title">{category}</p>', unsafe_allow_html=True)
        cat_df = resources[resources["category"] == category]
        cols = st.columns(2)
        for idx, (_, resource) in enumerate(cat_df.iterrows()):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="resource-card">
                        <div class="resource-icon">{resource['icon']}</div>
                        <div class="resource-cat">{resource['category']}</div>
                        <div class="resource-name">{resource['name']}</div>
                        <p class="resource-desc">{resource['description']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.link_button("Visit resource →", resource["link"], use_container_width=True)

    st.markdown(
        '<p style="font-size:0.82rem;color:var(--muted);margin-top:1.5rem;text-align:center;">'
        "Links open trusted external sites. Always confirm details directly with providers.</p>",
        unsafe_allow_html=True,
    )


def render_saved_tab(all_df: pd.DataFrame) -> None:
    saved = all_df[all_df["facility_id"].isin(st.session_state.saved_ids)]

    if saved.empty:
        render_empty_state(
            "♡",
            "Your saved list is empty",
            "When a place feels right, tap Save to compare — like pinning favorites on your birth journey.",
        )
        return

    st.caption(f"**{len(saved)}** saved — ready for tours and conversations with your partner.")
    for _, row in saved.iterrows():
        render_result_card(row, key_prefix="saved")


def render_trust_footer() -> None:
    st.markdown(
        """
        <div class="trust-footer">
            <div class="brand">Atlanta Birth Hub</div>
            <p>Data from verified public sources: CMS Hospital Compare, hospital transparency files, and accredited birth center records.</p>
            <p>Costs are illustrative estimates — not guaranteed prices. This is not medical or financial advice. Always request a Good Faith Estimate and speak with your care team.</p>
            <div class="trust-badges">
                <span class="trust-badge">✓ CMS Hospital Compare</span>
                <span class="trust-badge">✓ Birthing-friendly indicators</span>
                <span class="trust-badge">✓ No account required</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    init_state()
    render_sidebar_filters()

    with st.spinner("Gathering trusted birth options for you…"):
        all_facilities = get_facilities()

    render_hero(len(set(st.session_state.saved_ids)), len(all_facilities))
    render_about_section()

    st.markdown('<div class="search-strip"><div class="search-label">Search</div></div>', unsafe_allow_html=True)
    st.session_state.search_query = st.text_input(
        "Search facilities",
        value=st.session_state.search_query,
        placeholder="Hospital name, city, or region…",
        label_visibility="collapsed",
    )

    filters = copy.deepcopy(st.session_state.applied_filters)
    filters["search_query"] = st.session_state.search_query

    zip_clean = None
    if filters.get("distance_mode") == "Near my ZIP":
        zip_clean = str(filters.get("user_zip", DEFAULT_ZIP)).strip()[:5]
        if not zip_clean.isdigit() or len(zip_clean) != 5:
            st.warning("Please enter a valid 5-digit ZIP code for distance filtering.")
            zip_clean = DEFAULT_ZIP

    filtered = apply_filters(all_facilities, filters, user_zip=zip_clean)

    tab_search, tab_map, tab_resources, tab_saved = st.tabs(
        ["Search", "Map", "Resources", "Saved"]
    )

    with tab_search:
        render_search_tab(filtered)
    with tab_map:
        render_map_tab(filtered)
    with tab_resources:
        render_resources_tab()
    with tab_saved:
        render_saved_tab(all_facilities)

    render_trust_footer()


if __name__ == "__main__":
    main()