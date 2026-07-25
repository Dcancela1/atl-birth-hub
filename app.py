"""
Atlanta Birth Hub — Warm, trustworthy Georgia birth facility explorer.
Design system: sage + terracotta accents, soft off-white, premium cards.
"""

from __future__ import annotations

import copy
from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from data_ingestion import (
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

DESIGN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

    :root {
        --bg: #FBF8F4;
        --white: #FFFFFF;
        --sage: #7A9E8E;
        --sage-soft: #E8F1ED;
        --sage-deep: #5F8475;
        --terracotta: #C98B7B;
        --terracotta-soft: #F5EBE7;
        --terracotta-deep: #B57565;
        --charcoal: #2C2C2C;
        --gray: #6B6560;
        --gray-light: #9A948E;
        --border: #EBE4DC;
        --shadow: 0 4px 24px rgba(44, 44, 44, 0.06);
        --shadow-hover: 0 10px 36px rgba(44, 44, 44, 0.1);
        --excellent-bg: #E8F3EC;
        --excellent-text: #3D7A55;
        --strong-bg: #E8F0F8;
        --strong-text: #3D6A94;
        --good-bg: #F8F0E4;
        --good-text: #9A6B2F;
        --radius: 14px;
    }

    .stApp {
        background: var(--bg);
        font-family: 'DM Sans', system-ui, sans-serif;
        color: var(--charcoal);
    }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    /* Typography */
    h1, h2, h3, h4,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        font-family: 'Fraunces', Georgia, serif !important;
        color: var(--charcoal) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        line-height: 1.25 !important;
    }
    p, label, .stCaption, span {
        line-height: 1.6;
    }

    /* ── Header ── */
    .site-header {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem 1.75rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }
    .site-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.75rem;
    }
    .site-logo {
        font-family: 'Fraunces', serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--charcoal);
        margin: 0;
    }
    .site-logo span { color: var(--sage); }
    .site-tagline {
        font-size: 0.9rem;
        color: var(--gray);
        margin: 0.25rem 0 0 0;
    }
    .trust-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.9rem;
        padding-top: 0.9rem;
        border-top: 1px solid var(--border);
    }
    .trust-item {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--gray);
        background: var(--bg);
        border: 1px solid var(--border);
        padding: 0.3rem 0.75rem;
        border-radius: 100px;
    }
    .trust-item.accent {
        background: var(--sage-soft);
        color: var(--sage-deep);
        border-color: #D0E3DB;
    }

    /* ── Hero ── */
    .hero {
        background: linear-gradient(135deg, #FFFFFF 0%, #F7F2EC 50%, #EEF5F1 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 2.25rem 2rem;
        margin-bottom: 1.25rem;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(122,158,142,0.12) 0%, transparent 68%);
        border-radius: 50%;
    }
    .hero-kicker {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--sage);
        margin-bottom: 0.6rem;
        position: relative;
        z-index: 1;
    }
    .hero-title {
        font-family: 'Fraunces', serif;
        font-size: 2.15rem;
        font-weight: 700;
        color: var(--charcoal);
        margin: 0 0 0.65rem 0;
        line-height: 1.2;
        position: relative;
        z-index: 1;
    }
    .hero-value {
        font-size: 1.08rem;
        color: var(--gray);
        line-height: 1.65;
        max-width: 560px;
        margin: 0;
        position: relative;
        z-index: 1;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: var(--white) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] label {
        color: var(--charcoal) !important;
    }
    .filter-group-title {
        font-family: 'Fraunces', serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--charcoal);
        margin: 1.15rem 0 0.35rem 0;
        padding-top: 0.5rem;
        border-top: 1px solid var(--border);
    }
    .filter-group-title:first-of-type {
        border-top: none;
        margin-top: 0.25rem;
    }
    .filter-hint {
        font-size: 0.78rem;
        color: var(--gray-light);
        margin: 0 0 0.5rem 0;
    }
    .active-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin: 0.75rem 0 0.5rem 0;
    }
    .active-chip {
        font-size: 0.72rem;
        font-weight: 500;
        background: var(--sage-soft);
        color: var(--sage-deep);
        border: 1px solid #D0E3DB;
        padding: 0.25rem 0.6rem;
        border-radius: 100px;
    }

    /* Primary CTA */
    .stButton > button[kind="primary"] {
        background: var(--terracotta) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 0 2px 8px rgba(201,139,123,0.25) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--terracotta-deep) !important;
    }
    .stButton > button:not([kind="primary"]) {
        background: var(--white) !important;
        color: var(--charcoal) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: var(--bg) !important;
        border-color: var(--sage) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid var(--border);
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--gray) !important;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.7rem 1.15rem;
        border-radius: 10px 10px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: var(--charcoal) !important;
        background: var(--white) !important;
        border-bottom: 2px solid var(--sage) !important;
    }

    /* ── Result cards ── */
    .facility-card {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem 1.6rem;
        margin-bottom: 1.1rem;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .facility-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
    }
    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .card-name {
        font-family: 'Fraunces', serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--charcoal);
        margin: 0 0 0.3rem 0;
        line-height: 1.3;
    }
    .card-location {
        font-size: 0.88rem;
        color: var(--gray);
        margin: 0 0 0.5rem 0;
    }
    .type-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--sage-deep);
        background: var(--sage-soft);
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
    }
    .score-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 4.5rem;
        padding: 0.65rem 0.85rem;
        border-radius: 14px;
        text-align: center;
    }
    .score-badge .num {
        font-family: 'Fraunces', serif;
        font-size: 1.55rem;
        font-weight: 700;
        line-height: 1;
    }
    .score-badge .label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.2rem;
    }
    .score-badge.excellent {
        background: var(--excellent-bg);
        color: var(--excellent-text);
        border: 1px solid #C5E0CF;
    }
    .score-badge.strong {
        background: var(--strong-bg);
        color: var(--strong-text);
        border: 1px solid #C5D8EC;
    }
    .score-badge.good {
        background: var(--good-bg);
        color: var(--good-text);
        border: 1px solid #E8D9C0;
    }
    .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin: 0.9rem 0;
    }
    .tag {
        font-size: 0.74rem;
        font-weight: 500;
        color: var(--charcoal);
        background: var(--bg);
        border: 1px solid var(--border);
        padding: 0.28rem 0.65rem;
        border-radius: 8px;
    }
    .cost-box {
        background: var(--terracotta-soft);
        border: 1px solid #E8D5CD;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        margin: 0.75rem 0;
    }
    .cost-box .cost-item strong {
        display: block;
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--gray);
        margin-bottom: 0.15rem;
    }
    .cost-box .cost-item span {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--charcoal);
    }
    .card-highlight {
        font-size: 0.9rem;
        color: var(--gray);
        line-height: 1.5;
        margin: 0.5rem 0 0 0;
        font-style: italic;
    }

    /* Results bar */
    .results-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .results-count {
        font-size: 0.95rem;
        color: var(--gray);
    }
    .results-count strong {
        color: var(--charcoal);
        font-size: 1.15rem;
        font-weight: 600;
    }

    /* Empty states */
    .empty-state {
        text-align: center;
        padding: 3rem 1.5rem;
        background: var(--white);
        border: 1px dashed var(--border);
        border-radius: 16px;
        margin: 0.5rem 0 1.5rem 0;
    }
    .empty-icon { font-size: 2.25rem; margin-bottom: 0.75rem; }
    .empty-title {
        font-family: 'Fraunces', serif;
        font-size: 1.2rem;
        color: var(--charcoal);
        margin: 0 0 0.5rem 0;
    }
    .empty-body {
        font-size: 0.95rem;
        color: var(--gray);
        max-width: 380px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Soft disclaimer */
    .soft-note {
        font-size: 0.82rem;
        color: var(--gray);
        line-height: 1.55;
        background: var(--white);
        border: 1px solid var(--border);
        border-left: 3px solid var(--sage);
        border-radius: 0 10px 10px 0;
        padding: 0.85rem 1.1rem;
        margin: 0.75rem 0 1.25rem 0;
    }

    /* Resources */
    .resource-card {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 0.6rem;
        box-shadow: var(--shadow);
        height: 100%;
    }
    .resource-icon { font-size: 1.45rem; margin-bottom: 0.4rem; }
    .resource-cat {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--sage);
    }
    .resource-name {
        font-family: 'Fraunces', serif;
        font-size: 1.02rem;
        font-weight: 600;
        color: var(--charcoal);
        margin: 0.3rem 0;
    }
    .resource-desc {
        font-size: 0.86rem;
        color: var(--gray);
        line-height: 1.55;
        margin: 0;
    }
    .section-heading {
        font-family: 'Fraunces', serif;
        font-size: 1.1rem;
        color: var(--charcoal);
        margin: 1.4rem 0 0.75rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--border);
    }

    /* Footer */
    .site-footer {
        margin-top: 2.5rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid var(--border);
        text-align: center;
    }
    .site-footer .brand {
        font-family: 'Fraunces', serif;
        font-size: 1rem;
        color: var(--charcoal);
        margin-bottom: 0.4rem;
    }
    .site-footer p {
        font-size: 0.8rem;
        color: var(--gray);
        line-height: 1.6;
        max-width: 640px;
        margin: 0.3rem auto;
    }
    .footer-links {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .footer-link {
        font-size: 0.72rem;
        font-weight: 500;
        color: var(--sage-deep);
        background: var(--sage-soft);
        padding: 0.3rem 0.7rem;
        border-radius: 100px;
    }

    .stSpinner > div { border-top-color: var(--sage) !important; }

    @media (max-width: 768px) {
        .hero-title { font-size: 1.65rem; }
        .hero { padding: 1.5rem 1.15rem; }
        .site-header { padding: 1rem 1.15rem; }
        .facility-card { padding: 1.15rem; }
        .card-name { font-size: 1.1rem; }
        .card-top { flex-direction: column; }
        .score-badge { align-self: flex-start; flex-direction: row; gap: 0.4rem; min-width: auto; }
        .score-badge .num { font-size: 1.25rem; }
        .cost-box { gap: 1rem; }
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
        .stTabs [data-baseweb="tab"] { padding: 0.55rem 0.7rem; font-size: 0.8rem; }
    }
</style>
"""
st.markdown(DESIGN_CSS, unsafe_allow_html=True)

METHODOLOGY_COPY = """
**Quality scores help you compare at a glance — they are not medical advice.**

We turn public quality signals into a simple 0–100 score so you can scan options quickly:

- **Hospital star ratings** from CMS Hospital Compare map onto the score (higher stars → higher score)
- **Known maternity strengths** (like high-volume programs or midwifery models) may inform curated listings
- **Birth centers** reflect accreditation-style care and low-intervention philosophy where data allows

**What the badges mean**
- **Excellent (90+)** — strong public quality signals
- **Strong (80–89)** — solid ratings for most families
- **Good (below 80)** — still worth exploring; talk with your care team about fit

Tour in person when you can, ask about your insurance, and use tools like Leapfrog safety grades for a fuller picture. Your comfort and your provider’s guidance matter most.
"""


@st.cache_data(show_spinner=False)
def get_facilities() -> pd.DataFrame:
    return load_facilities()


def init_state() -> None:
    if "applied_filters" not in st.session_state:
        st.session_state.applied_filters = copy.deepcopy(DEFAULT_FILTERS)
    if "saved_ids" not in st.session_state:
        st.session_state.saved_ids = []
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""


def is_saved(facility_id: str) -> bool:
    return facility_id in st.session_state.saved_ids


def toggle_save(facility_id: str) -> None:
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


def active_filter_chips(filters: dict) -> list[str]:
    chips: list[str] = []
    for r in filters.get("regions") or []:
        chips.append(r)
    if filters.get("distance_mode") == "Near my ZIP":
        chips.append(f"Within {filters.get('max_distance', 60)} mi of {filters.get('user_zip', '')}")
    else:
        chips.append("Statewide")
    min_q = filters.get("min_quality_score", 0)
    if min_q:
        chips.append(f"Quality {min_q}+")
    for m in filters.get("quality_metrics") or []:
        chips.append(m)
    for s in filters.get("services") or []:
        chips.append(s)
    pmin, pmax = filters.get("price_min", 4000), filters.get("price_max", 25000)
    if pmin > 4000 or pmax < 25000:
        chips.append(f"${pmin:,}–${pmax:,}")
    for ins in filters.get("insurance") or []:
        chips.append(ins)
    return chips


def render_header(total: int, saved_count: int) -> None:
    st.markdown(
        f"""
        <div class="site-header">
            <div class="site-header-row">
                <div>
                    <p class="site-logo">Atlanta <span>Birth Hub</span></p>
                    <p class="site-tagline">A calm place to explore birth options across Georgia</p>
                </div>
            </div>
            <div class="trust-row">
                <span class="trust-item accent">{total} verified facilities</span>
                <span class="trust-item">CMS data</span>
                <span class="trust-item">No account needed</span>
                <span class="trust-item">♥ {saved_count} saved</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">For expecting mothers</div>
            <h1 class="hero-title">Find a birth place that feels right</h1>
            <p class="hero-value">
                Compare hospitals and birth centers across Georgia — quality, costs, and care style —
                so you can choose with clarity, not overwhelm.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_methodology() -> None:
    with st.expander("How we score quality (and what it means for you)", expanded=False):
        st.markdown(METHODOLOGY_COPY)


def render_soft_disclaimer() -> None:
    st.markdown(
        """
        <div class="soft-note">
            <strong>A gentle note:</strong> Cost ranges are estimates for planning — not guaranteed prices.
            This is a research tool, not medical advice. Always confirm with your provider and request a
            Good Faith Estimate before deciding.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(icon: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-icon">{icon}</div>
            <p class="empty-title">{title}</p>
            <p class="empty-body">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filters() -> None:
    st.sidebar.markdown("### Narrow your search")
    st.sidebar.caption("Use what matters to you — then Apply. You can always reset.")

    applied = st.session_state.applied_filters
    draft = copy.deepcopy(applied)

    # Active chips from currently applied filters
    chips = active_filter_chips(applied)
    if chips:
        chip_html = "".join(f'<span class="active-chip">{c}</span>' for c in chips[:8])
        st.sidebar.markdown(
            f'<div class="active-chips">{chip_html}</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown('<p class="filter-group-title">Location</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p class="filter-hint">Where would you like to give birth?</p>',
        unsafe_allow_html=True,
    )
    draft["regions"] = st.sidebar.multiselect(
        "Region of Georgia",
        GEORGIA_REGIONS,
        default=applied.get("regions", []),
        placeholder="Anywhere in Georgia",
    )
    draft["distance_mode"] = st.sidebar.radio(
        "How far will you travel?",
        ["Statewide", "Near my ZIP"],
        index=0 if applied.get("distance_mode") == "Statewide" else 1,
        horizontal=True,
    )
    if draft["distance_mode"] == "Near my ZIP":
        draft["user_zip"] = st.sidebar.text_input(
            "Your ZIP code",
            value=applied.get("user_zip", DEFAULT_ZIP),
            max_chars=5,
        )
        draft["max_distance"] = st.sidebar.slider(
            "Maximum drive (miles)",
            10, 120,
            int(applied.get("max_distance", 60)),
            step=5,
        )
    else:
        draft["user_zip"] = applied.get("user_zip", DEFAULT_ZIP)

    st.sidebar.markdown('<p class="filter-group-title">Quality</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p class="filter-hint">Start with a quality floor if you want — or leave open.</p>',
        unsafe_allow_html=True,
    )
    score_keys = list(QUALITY_SCORE_OPTIONS.keys())
    score_vals = list(QUALITY_SCORE_OPTIONS.values())
    current = applied.get("min_quality_score", 0)
    draft["min_quality_score"] = QUALITY_SCORE_OPTIONS[
        st.sidebar.selectbox(
            "Minimum quality score",
            score_keys,
            index=score_vals.index(current) if current in score_vals else 0,
            help="See “How we score quality” for a plain-language explanation.",
        )
    ]
    draft["quality_metrics"] = st.sidebar.multiselect(
        "Care strengths that matter",
        QUALITY_METRIC_OPTIONS,
        default=applied.get("quality_metrics", []),
        placeholder="Any strengths",
    )

    st.sidebar.markdown('<p class="filter-group-title">Birth experience</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p class="filter-hint">Hospital, midwifery, NICU, water birth, and more.</p>',
        unsafe_allow_html=True,
    )
    draft["services"] = st.sidebar.multiselect(
        "Services & care style",
        SERVICE_OPTIONS,
        default=applied.get("services", []),
        placeholder="Any experience",
    )

    st.sidebar.markdown('<p class="filter-group-title">Budget</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p class="filter-hint">Facility estimates only — insurance changes your share.</p>',
        unsafe_allow_html=True,
    )
    price = st.sidebar.slider(
        "Estimated vaginal delivery cost ($)",
        4000, 25000,
        (int(applied.get("price_min", 4000)), int(applied.get("price_max", 25000))),
        step=500,
    )
    draft["price_min"], draft["price_max"] = price
    draft["insurance"] = st.sidebar.multiselect(
        "Insurance plans to keep in mind",
        INSURANCE_OPTIONS,
        default=applied.get("insurance", []),
        placeholder="Any insurance",
    )

    with st.sidebar.expander("A few more options"):
        draft["min_births_per_year"] = st.slider(
            "Minimum births per year (volume)",
            0, 4000,
            int(applied.get("min_births_per_year", 0)),
            step=100,
        )
        draft["min_years_operation"] = st.slider(
            "Minimum years serving families",
            0, 80,
            int(applied.get("min_years_operation", 0)),
        )

    st.sidebar.markdown("")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("Apply filters", type="primary", use_container_width=True):
            st.session_state.applied_filters = draft
            st.rerun()
    with c2:
        if st.button("Reset", use_container_width=True):
            st.session_state.applied_filters = copy.deepcopy(DEFAULT_FILTERS)
            st.session_state.search_query = ""
            st.rerun()


def render_result_card(row: pd.Series, key_prefix: str = "search") -> None:
    fid = str(row["facility_id"])
    saved = is_saved(fid)
    score = int(row.get("quality_score", 70))
    tier, tier_label = quality_tier(score)

    dist = row.get("distance_miles")
    if pd.notna(dist):
        loc_line = f"{row.get('location', '')} · {dist:.0f} mi from you"
    else:
        loc_line = f"{row.get('location', '')} · {row.get('region', 'Georgia')}"

    services = row.get("services", [])
    if isinstance(services, str):
        services = [s for s in services.split("|") if s]
    tags = "".join(f'<span class="tag">{s}</span>' for s in services[:5])

    highlight = row.get("key_strength") or row.get("quality_label") or ""
    facility_type = row.get("type", "Hospital")

    st.markdown(
        f"""
        <div class="facility-card">
            <div class="card-top">
                <div>
                    <p class="card-name">{row['name']}</p>
                    <p class="card-location">{loc_line}</p>
                    <span class="type-badge">{facility_type}</span>
                </div>
                <div class="score-badge {tier}">
                    <span class="num">{score}</span>
                    <span class="label">{tier_label}</span>
                </div>
            </div>
            <div class="tags">{tags}</div>
            <div class="cost-box">
                <div class="cost-item">
                    <strong>Vaginal estimate</strong>
                    <span>{row.get('vaginal_cost_display', '—')}</span>
                </div>
                <div class="cost-item">
                    <strong>C-section estimate</strong>
                    <span>{row.get('csection_cost_display', '—')}</span>
                </div>
            </div>
            <p class="card-highlight">{highlight}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
        f'<div class="results-bar"><span class="results-count">'
        f'<strong>{len(df)}</strong> places for you to explore</span></div>',
        unsafe_allow_html=True,
    )

    if df.empty:
        render_empty_state(
            "🌸",
            "No centers match your filters",
            "Try broadening your search — reset filters, choose Statewide, or lower the quality minimum.",
        )
        return

    sort = st.selectbox(
        "Sort by",
        ["Highest quality", "Lowest cost", "Nearest", "A–Z"],
        index=0,
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
    st.caption("Explore locations across Georgia. Tap a pin for a quick snapshot.")

    if df.empty:
        render_empty_state(
            "🗺️",
            "Nothing on the map yet",
            "Widen your filters and apply — then come back to see places light up.",
        )
        return

    with st.spinner("Drawing your map…"):
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
                    f"Quality: {int(row.get('quality_score', 70))}"
                ),
                tooltip=row["name"],
                icon=folium.Icon(color="green", icon="info-sign"),
            ).add_to(cluster)
        st_folium(m, width=None, height=480, returned_objects=[])


def render_resources_tab() -> None:
    st.caption("Support beyond the hospital — education, postpartum, feeding, and community care.")

    resources = load_resources()
    for category in resources["category"].unique():
        st.markdown(f'<p class="section-heading">{category}</p>', unsafe_allow_html=True)
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
                st.link_button("Open resource →", resource["link"], use_container_width=True)


def render_saved_tab(all_df: pd.DataFrame) -> None:
    saved = all_df[all_df["facility_id"].isin(st.session_state.saved_ids)]

    if saved.empty:
        render_empty_state(
            "♡",
            "Nothing saved yet",
            "When a place feels promising, tap Save to compare — perfect for partner discussions and tour planning.",
        )
        return

    st.caption(f"**{len(saved)}** saved — yours to revisit anytime this session.")
    for _, row in saved.iterrows():
        render_result_card(row, key_prefix="saved")


def render_footer(total: int) -> None:
    today = datetime.now().strftime("%B %d, %Y")
    st.markdown(
        f"""
        <div class="site-footer">
            <div class="brand">Atlanta Birth Hub</div>
            <p>
                {total} facilities · Data from CMS Hospital Compare and public transparency sources ·
                Updated {today}
            </p>
            <p>
                Estimates are for planning only. Not medical or financial advice.
                Confirm details with your care team and hospital billing office.
            </p>
            <div class="footer-links">
                <span class="footer-link">CMS Hospital Compare</span>
                <span class="footer-link">Price transparency</span>
                <span class="footer-link">Georgia maternity resources</span>
                <span class="footer-link">No account required</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    init_state()
    render_sidebar_filters()

    with st.spinner("Gathering trusted options for you…"):
        all_facilities = get_facilities()

    total = len(all_facilities)
    render_header(total, len(st.session_state.saved_ids))
    render_hero()
    render_methodology()
    render_soft_disclaimer()

    st.session_state.search_query = st.text_input(
        "Search by name or city",
        value=st.session_state.search_query,
        placeholder="Search hospitals, cities, or regions…",
    )

    filters = copy.deepcopy(st.session_state.applied_filters)
    filters["search_query"] = st.session_state.search_query

    zip_clean = None
    if filters.get("distance_mode") == "Near my ZIP":
        zip_clean = str(filters.get("user_zip", DEFAULT_ZIP)).strip()[:5]
        if not zip_clean.isdigit() or len(zip_clean) != 5:
            st.warning("Please enter a valid 5-digit ZIP for distance filtering.")
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

    render_footer(total)


if __name__ == "__main__":
    main()