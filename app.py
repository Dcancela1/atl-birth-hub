"""
Atlanta Birth Hub — Premium redesign for expecting mothers in Georgia.
All facility data, scores, costs, filters, and features preserved.
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

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

:root {
    --bg: #FBF8F4;
    --white: #FFFFFF;
    --sage: #7A9E8E;
    --sage-soft: #EAF2EE;
    --sage-deep: #5A7D6E;
    --terracotta: #C98B7B;
    --terracotta-soft: #F6EDEA;
    --terracotta-deep: #B57565;
    --charcoal: #2C2C2C;
    --gray: #6B6560;
    --gray-soft: #8F8882;
    --border: #EBE4DC;
    --shadow: 0 6px 28px rgba(44, 44, 44, 0.055);
    --shadow-lg: 0 14px 44px rgba(44, 44, 44, 0.09);
    --excellent-bg: #E9F3EC;
    --excellent-fg: #3A6B4F;
    --strong-bg: #E9EFF5;
    --strong-fg: #3A5A78;
    --good-bg: #F7F0E6;
    --good-fg: #8A6528;
    --radius: 16px;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--charcoal);
    font-size: 16.5px;
    line-height: 1.65;
}

#MainMenu, footer, header { visibility: hidden; height: 0; }

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
    max-width: 1120px;
}

/* Base type */
p, label, span, li, .stMarkdown {
    line-height: 1.65;
}
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

/* ═══════════════ HEADER ═══════════════ */
.abh-header {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem 1.85rem 1.35rem;
    margin-bottom: 1.15rem;
    box-shadow: var(--shadow);
}
.abh-header-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
}
.abh-logo {
    font-family: 'Fraunces', serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--charcoal);
    margin: 0;
    letter-spacing: -0.02em;
}
.abh-logo em {
    font-style: normal;
    color: var(--sage);
}
.abh-tagline {
    font-size: 0.95rem;
    color: var(--gray);
    margin: 0.35rem 0 0 0;
    max-width: 420px;
}
.abh-trust {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1.1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
}
.abh-trust-badge {
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--gray);
    background: var(--bg);
    border: 1px solid var(--border);
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
}
.abh-trust-badge.primary {
    background: var(--sage-soft);
    color: var(--sage-deep);
    border-color: #D2E4DB;
}

/* ═══════════════ HERO ═══════════════ */
.abh-hero {
    background:
        radial-gradient(ellipse 80% 80% at 100% 0%, rgba(122,158,142,0.14) 0%, transparent 55%),
        radial-gradient(ellipse 60% 70% at 0% 100%, rgba(201,139,123,0.1) 0%, transparent 50%),
        linear-gradient(160deg, #FFFFFF 0%, #F9F5F0 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2.5rem 2.25rem 2.25rem;
    margin-bottom: 1.35rem;
    box-shadow: var(--shadow);
}
.abh-hero-kicker {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--sage);
    margin: 0 0 0.65rem 0;
}
.abh-hero-title {
    font-family: 'Fraunces', serif;
    font-size: 2.35rem;
    font-weight: 700;
    color: var(--charcoal);
    margin: 0 0 0.75rem 0;
    line-height: 1.18;
    letter-spacing: -0.025em;
}
.abh-hero-value {
    font-size: 1.1rem;
    color: var(--gray);
    line-height: 1.7;
    max-width: 580px;
    margin: 0;
}

/* ═══════════════ SIDEBAR ═══════════════ */
section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.25rem;
}
section[data-testid="stSidebar"] label {
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: var(--charcoal) !important;
}
.sidebar-title {
    font-family: 'Fraunces', serif;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0 0 0.25rem 0;
}
.sidebar-sub {
    font-size: 0.85rem;
    color: var(--gray-soft);
    margin: 0 0 1rem 0;
    line-height: 1.5;
}
.filter-group {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.9rem 1rem 0.65rem;
    margin-bottom: 0.85rem;
}
.filter-group-label {
    font-family: 'Fraunces', serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0 0 0.2rem 0;
}
.filter-help {
    font-size: 0.78rem;
    color: var(--gray-soft);
    margin: 0 0 0.65rem 0;
    line-height: 1.45;
}
.active-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin: 0 0 1rem 0;
}
.active-chip {
    font-size: 0.72rem;
    font-weight: 500;
    background: var(--sage-soft);
    color: var(--sage-deep);
    border: 1px solid #D0E3DB;
    padding: 0.3rem 0.7rem;
    border-radius: 999px;
}

/* Sliders — terracotta accent */
div[data-testid="stSlider"] > div > div > div {
    background: var(--terracotta) !important;
}
div[data-testid="stSlider"] [role="slider"] {
    background: var(--terracotta) !important;
    border: 2px solid var(--white) !important;
    box-shadow: 0 1px 4px rgba(201,139,123,0.4) !important;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: var(--terracotta) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 3px 12px rgba(201,139,123,0.28) !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--terracotta-deep) !important;
    transform: translateY(-1px);
}
.stButton > button:not([kind="primary"]) {
    background: var(--white) !important;
    color: var(--charcoal) !important;
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--sage) !important;
    background: var(--sage-soft) !important;
}

/* Inputs */
.stTextInput input, .stSelectbox > div > div, .stMultiSelect > div > div {
    border-radius: 12px !important;
    border-color: var(--border) !important;
    background: var(--white) !important;
}
.stTextInput input:focus {
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 2px rgba(122,158,142,0.15) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.15rem;
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.35rem;
    margin-bottom: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--gray) !important;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.65rem 1.2rem;
    border-radius: 10px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--charcoal) !important;
    background: var(--sage-soft) !important;
}

/* ═══════════════ FACILITY CARDS ═══════════════ */
.facility-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.65rem 1.75rem;
    margin-bottom: 1.15rem;
    box-shadow: var(--shadow);
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.facility-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
}
.card-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1.25rem;
    flex-wrap: wrap;
}
.card-name {
    font-family: 'Fraunces', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0 0 0.35rem 0;
    line-height: 1.28;
    letter-spacing: -0.015em;
}
.card-meta {
    font-size: 0.92rem;
    color: var(--gray);
    margin: 0 0 0.55rem 0;
}
.type-pill {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--sage-deep);
    background: var(--sage-soft);
    padding: 0.25rem 0.65rem;
    border-radius: 8px;
}
.score-pill {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 5rem;
    padding: 0.75rem 0.95rem;
    border-radius: 14px;
    text-align: center;
    flex-shrink: 0;
}
.score-pill .n {
    font-family: 'Fraunces', serif;
    font-size: 1.75rem;
    font-weight: 700;
    line-height: 1;
}
.score-pill .l {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
    opacity: 0.9;
}
.score-pill.excellent {
    background: var(--excellent-bg);
    color: var(--excellent-fg);
    border: 1px solid #C4DFCE;
}
.score-pill.strong {
    background: var(--strong-bg);
    color: var(--strong-fg);
    border: 1px solid #C5D5E6;
}
.score-pill.good {
    background: var(--good-bg);
    color: var(--good-fg);
    border: 1px solid #E6D7BC;
}
.tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 1rem 0 0.85rem;
}
.tag {
    font-size: 0.76rem;
    font-weight: 500;
    color: var(--charcoal);
    background: var(--bg);
    border: 1px solid var(--border);
    padding: 0.3rem 0.7rem;
    border-radius: 8px;
}
.cost-panel {
    background: linear-gradient(135deg, var(--terracotta-soft) 0%, #FBF6F3 100%);
    border: 1px solid #EAD9D1;
    border-radius: 14px;
    padding: 1rem 1.15rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1.75rem;
    margin-bottom: 0.65rem;
}
.cost-panel .ci strong {
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--gray-soft);
    margin-bottom: 0.2rem;
}
.cost-panel .ci span {
    font-size: 1.12rem;
    font-weight: 600;
    color: var(--charcoal);
    letter-spacing: -0.01em;
}
.card-blurb {
    font-size: 0.95rem;
    color: var(--gray);
    line-height: 1.55;
    margin: 0.35rem 0 0;
    font-style: italic;
}

/* Results chrome */
.results-header {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
    margin: 0.5rem 0 1.15rem;
}
.results-title {
    font-family: 'Fraunces', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0;
}
.results-title span {
    color: var(--sage);
}
.results-sub {
    font-size: 0.88rem;
    color: var(--gray-soft);
    margin: 0.2rem 0 0;
}

/* Empty */
.empty {
    text-align: center;
    padding: 3.25rem 1.75rem;
    background: var(--white);
    border: 1px dashed var(--border);
    border-radius: var(--radius);
    margin: 0.75rem 0 1.5rem;
}
.empty-ico { font-size: 2.25rem; margin-bottom: 0.75rem; opacity: 0.85; }
.empty-h {
    font-family: 'Fraunces', serif;
    font-size: 1.25rem;
    color: var(--charcoal);
    margin: 0 0 0.5rem;
}
.empty-p {
    font-size: 0.95rem;
    color: var(--gray);
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.65;
}

/* Gentle note */
.gentle-note {
    font-size: 0.88rem;
    color: var(--gray);
    line-height: 1.65;
    background: var(--white);
    border: 1px solid var(--border);
    border-left: 3.5px solid var(--sage);
    border-radius: 0 14px 14px 0;
    padding: 1rem 1.25rem;
    margin: 0.85rem 0 1.35rem;
}

/* Methodology panel */
.method-panel {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.15rem 0.25rem;
    margin-bottom: 0.85rem;
    box-shadow: var(--shadow);
}

/* Map shell */
.map-shell {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}
.map-caption {
    font-size: 0.9rem;
    color: var(--gray);
    margin: 0 0 0.85rem;
}

/* Resources hub */
.resources-intro {
    font-size: 1.02rem;
    color: var(--gray);
    line-height: 1.7;
    margin: 0 0 1.5rem;
    max-width: 540px;
}
.resource-section {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    color: var(--charcoal);
    margin: 1.75rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
.resource-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.4rem 1.45rem;
    margin-bottom: 0.85rem;
    box-shadow: var(--shadow);
    min-height: 150px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.resource-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}
.resource-ico { font-size: 1.5rem; margin-bottom: 0.5rem; }
.resource-cat {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--sage);
}
.resource-name {
    font-family: 'Fraunces', serif;
    font-size: 1.08rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0.35rem 0 0.45rem;
    line-height: 1.3;
}
.resource-desc {
    font-size: 0.9rem;
    color: var(--gray);
    line-height: 1.6;
    margin: 0;
}

/* Footer */
.abh-footer {
    margin-top: 3rem;
    padding: 2.25rem 1rem 1.5rem;
    border-top: 1px solid var(--border);
    text-align: center;
}
.abh-footer .brand {
    font-family: 'Fraunces', serif;
    font-size: 1.05rem;
    color: var(--charcoal);
    margin-bottom: 0.5rem;
}
.abh-footer p {
    font-size: 0.82rem;
    color: var(--gray-soft);
    line-height: 1.65;
    max-width: 620px;
    margin: 0.35rem auto;
}
.footer-pills {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 1.15rem;
}
.footer-pill {
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--sage-deep);
    background: var(--sage-soft);
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
}

.stSpinner > div { border-top-color: var(--sage) !important; }

/* Expander polish */
div[data-testid="stExpander"] {
    background: var(--white);
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    box-shadow: var(--shadow);
    margin-bottom: 0.75rem;
}
div[data-testid="stExpander"] summary {
    font-weight: 500;
    color: var(--charcoal);
}

@media (max-width: 768px) {
    .abh-hero-title { font-size: 1.7rem; }
    .abh-hero { padding: 1.65rem 1.25rem; }
    .abh-header { padding: 1.15rem 1.2rem; }
    .facility-card { padding: 1.25rem; }
    .card-name { font-size: 1.15rem; }
    .card-row { flex-direction: column; }
    .score-pill {
        flex-direction: row;
        gap: 0.45rem;
        align-self: flex-start;
        min-width: auto;
        padding: 0.5rem 0.85rem;
    }
    .score-pill .n { font-size: 1.3rem; }
    .cost-panel { gap: 1rem; }
    .results-title { font-size: 1.15rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.5rem 0.7rem; font-size: 0.8rem; }
    .block-container { padding-left: 0.65rem !important; padding-right: 0.65rem !important; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

METHODOLOGY = """
**Scores are a calm planning guide — not a medical recommendation.**

We translate public quality signals into a simple **0–100** number so you can compare options without drowning in charts:

- **CMS Hospital Compare star ratings** map onto the score (more stars → higher score)
- **Maternity-focused strengths** (volume, midwifery model, high-risk readiness) inform curated listings
- **Birth centers** reflect accredited, low-intervention care models where data supports it

| Badge | Score | In plain language |
|-------|-------|-------------------|
| **Excellent** | 90+ | Strong public quality signals |
| **Strong** | 80–89 | Solid for most families exploring options |
| **Good** | under 80 | Worth a closer look with your care team |

Tour when you can, confirm insurance coverage, and lean on your provider. Your comfort matters as much as any score.
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


def is_saved(fid: str) -> bool:
    return fid in st.session_state.saved_ids


def toggle_save(fid: str) -> None:
    saved = list(st.session_state.saved_ids)
    if fid in saved:
        saved.remove(fid)
    else:
        saved.append(fid)
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
        chips.append(f"Within {filters.get('max_distance', 60)} mi · {filters.get('user_zip', '')}")
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
        chips.append(f"Vaginal ${pmin:,}–${pmax:,}")
    cs_min = filters.get("csection_price_min", 5000)
    cs_max = filters.get("csection_price_max", 30000)
    if cs_min > 5000 or cs_max < 30000:
        chips.append(f"C-section ${cs_min:,}–${cs_max:,}")
    for ins in filters.get("insurance") or []:
        chips.append(ins)
    return chips


def render_header(total: int, saved: int) -> None:
    st.markdown(
        f"""
        <div class="abh-header">
            <div class="abh-header-top">
                <div>
                    <p class="abh-logo">Atlanta <em>Birth Hub</em></p>
                    <p class="abh-tagline">A calm place to explore birth options across Georgia</p>
                </div>
            </div>
            <div class="abh-trust">
                <span class="abh-trust-badge primary">{total} verified facilities</span>
                <span class="abh-trust-badge">CMS data</span>
                <span class="abh-trust-badge">No account needed</span>
                <span class="abh-trust-badge">♥ {saved} saved</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="abh-hero">
            <p class="abh-hero-kicker">For expecting mothers</p>
            <h1 class="abh-hero-title">Find a birth place that feels right</h1>
            <p class="abh-hero-value">
                Compare hospitals and birth centers across Georgia — quality, costs, and care style —
                so you can choose with clarity, not overwhelm.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_methodology() -> None:
    with st.expander("How we score quality (and what it means for you)", expanded=False):
        st.markdown(METHODOLOGY)


def render_gentle_note() -> None:
    st.markdown(
        """
        <div class="gentle-note">
            <strong>A gentle note on costs:</strong> Ranges are facility estimates for planning —
            your insurance and care path may change what you pay. This tool supports research;
            it is not medical or financial advice. Request a Good Faith Estimate before you decide.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty(icon: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="empty">
            <div class="empty-ico">{icon}</div>
            <p class="empty-h">{title}</p>
            <p class="empty-p">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.markdown('<p class="sidebar-title">Narrow your search</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p class="sidebar-sub">Choose what matters, then tap Apply. You can always reset.</p>',
        unsafe_allow_html=True,
    )

    applied = st.session_state.applied_filters
    draft = copy.deepcopy(applied)

    chips = active_filter_chips(applied)
    if chips:
        html = "".join(f'<span class="active-chip">{c}</span>' for c in chips[:10])
        st.sidebar.markdown(f'<div class="active-chips">{html}</div>', unsafe_allow_html=True)

    # Location
    st.sidebar.markdown(
        '<div class="filter-group"><p class="filter-group-label">Location</p>'
        '<p class="filter-help">Where would you like to give birth?</p></div>',
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
            help="We estimate straight-line distance to each facility.",
        )
        draft["max_distance"] = st.sidebar.slider(
            "Maximum drive (miles)",
            10, 120,
            int(applied.get("max_distance", 60)),
            step=5,
        )
    else:
        draft["user_zip"] = applied.get("user_zip", DEFAULT_ZIP)

    # Quality
    st.sidebar.markdown(
        '<div class="filter-group"><p class="filter-group-label">Quality</p>'
        '<p class="filter-help">Set a minimum score, or leave open to see everyone.</p></div>',
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
            help="See “How we score quality” for a plain-language guide.",
        )
    ]
    draft["quality_metrics"] = st.sidebar.multiselect(
        "Care strengths that matter to you",
        QUALITY_METRIC_OPTIONS,
        default=applied.get("quality_metrics", []),
        placeholder="Select strengths (optional)",
    )

    # Birth experience
    st.sidebar.markdown(
        '<div class="filter-group"><p class="filter-group-label">Birth experience</p>'
        '<p class="filter-help">Hospital, midwifery, NICU, water birth, and more.</p></div>',
        unsafe_allow_html=True,
    )
    draft["services"] = st.sidebar.multiselect(
        "Services & care style",
        SERVICE_OPTIONS,
        default=applied.get("services", []),
        placeholder="Select services (optional)",
    )

    # Budget — two clearly labeled sliders
    st.sidebar.markdown(
        '<div class="filter-group"><p class="filter-group-label">Budget</p>'
        '<p class="filter-help">Facility estimates only — insurance changes your share.</p></div>',
        unsafe_allow_html=True,
    )
    v_price = st.sidebar.slider(
        "Estimated vaginal delivery cost",
        min_value=4000,
        max_value=25000,
        value=(
            int(applied.get("price_min", 4000)),
            int(applied.get("price_max", 25000)),
        ),
        step=500,
        format="$%d",
        help="Illustrative facility charge range before insurance.",
    )
    draft["price_min"], draft["price_max"] = v_price

    cs_price = st.sidebar.slider(
        "Estimated C-section cost",
        min_value=5000,
        max_value=30000,
        value=(
            int(applied.get("csection_price_min", 5000)),
            int(applied.get("csection_price_max", 30000)),
        ),
        step=500,
        format="$%d",
        help="Facilities without C-section on site (e.g. birth centers) still appear.",
    )
    draft["csection_price_min"], draft["csection_price_max"] = cs_price

    draft["insurance"] = st.sidebar.multiselect(
        "Insurance to keep in mind",
        INSURANCE_OPTIONS,
        default=applied.get("insurance", []),
        placeholder="Select plans (optional)",
    )

    with st.sidebar.expander("Experience & volume (optional)"):
        st.caption("Higher volume can mean more experienced teams for routine births.")
        draft["min_births_per_year"] = st.slider(
            "Minimum births per year",
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
    c1, c2 = st.sidebar.columns([1.35, 1])
    with c1:
        if st.button("Apply filters", type="primary", use_container_width=True):
            st.session_state.applied_filters = draft
            st.rerun()
    with c2:
        if st.button("Reset", use_container_width=True):
            st.session_state.applied_filters = copy.deepcopy(DEFAULT_FILTERS)
            st.session_state.search_query = ""
            st.rerun()


def render_card(row: pd.Series, key_prefix: str = "search") -> None:
    fid = str(row["facility_id"])
    saved = is_saved(fid)
    score = int(row.get("quality_score", 70))
    tier, tier_label = quality_tier(score)

    dist = row.get("distance_miles")
    if pd.notna(dist):
        meta = f"{row.get('location', '')} · {dist:.0f} mi from you"
    else:
        meta = f"{row.get('location', '')} · {row.get('region', 'Georgia')}"

    services = row.get("services", [])
    if isinstance(services, str):
        services = [s for s in services.split("|") if s]
    tags = "".join(f'<span class="tag">{s}</span>' for s in services[:5])
    highlight = row.get("key_strength") or row.get("quality_label") or ""
    ftype = row.get("type", "Hospital")

    st.markdown(
        f"""
        <div class="facility-card">
            <div class="card-row">
                <div>
                    <p class="card-name">{row['name']}</p>
                    <p class="card-meta">{meta}</p>
                    <span class="type-pill">{ftype}</span>
                </div>
                <div class="score-pill {tier}">
                    <span class="n">{score}</span>
                    <span class="l">{tier_label}</span>
                </div>
            </div>
            <div class="tag-row">{tags}</div>
            <div class="cost-panel">
                <div class="ci">
                    <strong>Vaginal estimate</strong>
                    <span>{row.get('vaginal_cost_display', '—')}</span>
                </div>
                <div class="ci">
                    <strong>C-section estimate</strong>
                    <span>{row.get('csection_cost_display', '—')}</span>
                </div>
            </div>
            <p class="card-blurb">{highlight}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns([1.4, 1])
    with b1:
        if st.button(
            "♥ Saved" if saved else "♡ Save to compare",
            key=f"save_btn_{key_prefix}_{fid}",
            use_container_width=True,
        ):
            toggle_save(fid)
            st.rerun()
    with b2:
        with st.expander("View details"):
            st.markdown(f"**Strengths**  \n{row.get('strengths', '—')}")
            st.markdown(f"**What to consider**  \n{row.get('considerations', '—')}")
            st.markdown(
                f"**NICU:** {row.get('nicu_level', '—')} · "
                f"**C-section rate:** {row.get('csection_rate_display', '—')} · "
                f"**Quality label:** {row.get('quality_label', '—')}"
            )
            if pd.notna(row.get("address")):
                st.caption(str(row["address"]))


def render_search(df: pd.DataFrame) -> None:
    st.markdown(
        f"""
        <div class="results-header">
            <div>
                <p class="results-title"><span>{len(df)}</span> places for you to explore</p>
                <p class="results-sub">Sorted for easy scanning — quality first by default</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        render_empty(
            "🌸",
            "No centers match your filters",
            "Try broadening your search — reset filters, choose Statewide, or lower the quality minimum.",
        )
        return

    sort = st.selectbox(
        "Sort results",
        ["Highest quality", "Lowest cost", "Nearest", "A–Z"],
        index=0,
        help="Highest quality is the default so strong options rise to the top.",
    )
    out = df.copy()
    if sort == "Highest quality":
        out = out.sort_values("quality_score", ascending=False)
    elif sort == "Lowest cost":
        out = out.sort_values("vaginal_cost", ascending=True, na_position="last")
    elif sort == "Nearest":
        out = out.sort_values("distance_miles", ascending=True, na_position="last")
    else:
        out = out.sort_values("name")

    for _, row in out.iterrows():
        render_card(row, key_prefix="search")


def render_map(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="map-shell"><p class="map-caption">'
        "Explore locations across Georgia. Tap a pin for a quick snapshot."
        "</p></div>",
        unsafe_allow_html=True,
    )

    if df.empty:
        render_empty(
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
        st_folium(m, width=None, height=500, returned_objects=[])


def render_resources() -> None:
    st.markdown(
        '<p class="resources-intro">Support beyond the hospital walls — education, '
        "postpartum care, feeding, and community resources across Georgia.</p>",
        unsafe_allow_html=True,
    )
    resources = load_resources()
    for category in resources["category"].unique():
        st.markdown(f'<p class="resource-section">{category}</p>', unsafe_allow_html=True)
        cat = resources[resources["category"] == category]
        cols = st.columns(2)
        for i, (_, r) in enumerate(cat.iterrows()):
            with cols[i % 2]:
                st.markdown(
                    f"""
                    <div class="resource-card">
                        <div class="resource-ico">{r['icon']}</div>
                        <div class="resource-cat">{r['category']}</div>
                        <div class="resource-name">{r['name']}</div>
                        <p class="resource-desc">{r['description']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.link_button("Open resource →", r["link"], use_container_width=True)


def render_saved(all_df: pd.DataFrame) -> None:
    saved = all_df[all_df["facility_id"].isin(st.session_state.saved_ids)]
    if saved.empty:
        render_empty(
            "♡",
            "Nothing saved yet",
            "When a place feels promising, tap Save to compare — perfect for partner talks and tour planning.",
        )
        return

    st.markdown(
        f"""
        <div class="results-header">
            <div>
                <p class="results-title"><span>{len(saved)}</span> saved for you</p>
                <p class="results-sub">Compare side by side anytime this session</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for _, row in saved.iterrows():
        render_card(row, key_prefix="saved")


def render_footer(total: int) -> None:
    today = datetime.now().strftime("%B %d, %Y")
    st.markdown(
        f"""
        <div class="abh-footer">
            <div class="brand">Atlanta Birth Hub</div>
            <p>{total} facilities · CMS Hospital Compare & public transparency sources · Updated {today}</p>
            <p>Estimates are for planning only. Not medical or financial advice.
            Confirm details with your care team and hospital billing office.</p>
            <div class="footer-pills">
                <span class="footer-pill">CMS Hospital Compare</span>
                <span class="footer-pill">Price transparency</span>
                <span class="footer-pill">Georgia resources</span>
                <span class="footer-pill">No account required</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    init_state()
    render_sidebar()

    with st.spinner("Gathering trusted options for you…"):
        facilities = get_facilities()

    total = len(facilities)
    render_header(total, len(st.session_state.saved_ids))
    render_hero()
    render_methodology()
    render_gentle_note()

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

    filtered = apply_filters(facilities, filters, user_zip=zip_clean)

    t_search, t_map, t_resources, t_saved = st.tabs(
        ["Search", "Map", "Resources", "Saved"]
    )
    with t_search:
        render_search(filtered)
    with t_map:
        render_map(filtered)
    with t_resources:
        render_resources()
    with t_saved:
        render_saved(facilities)

    render_footer(total)


if __name__ == "__main__":
    main()