"""
Atlanta Birth Hub — Full visual & UX overhaul for expecting mothers.
Preserves all data, scores, costs, filters, map, resources, and save/compare.
"""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

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

# ─────────────────────────────────────────────────────────────────────────────
# Design system CSS — multi-layer shadows, guided filters, premium cards
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

:root {
    --bg: #FBF8F4;
    --white: #FFFFFF;
    --sage: #7A9E8E;
    --sage-soft: #EAF2EE;
    --sage-mid: #C5D9CF;
    --sage-deep: #5A7D6E;
    --terracotta: #C98B7B;
    --terracotta-soft: #F6EDEA;
    --terracotta-mid: #E5C4B8;
    --terracotta-deep: #B57565;
    --charcoal: #2C2C2C;
    --gray: #6B6560;
    --gray-soft: #8F8882;
    --border: #EBE4DC;
    --shadow-1: 0 1px 2px rgba(44,44,44,0.03);
    --shadow-2: 0 4px 16px rgba(44,44,44,0.04);
    --shadow-3: 0 12px 40px rgba(44,44,44,0.07);
    --shadow-hover: 0 16px 48px rgba(44,44,44,0.1);
    --excellent-bg: #E9F3EC;
    --excellent-fg: #3A6B4F;
    --strong-bg: #E9EFF5;
    --strong-fg: #3A5A78;
    --good-bg: #F7F0E6;
    --good-fg: #8A6528;
    --radius: 16px;
    --radius-sm: 12px;
    --radius-pill: 999px;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, -apple-system, sans-serif !important;
}

.stApp {
    background: var(--bg) !important;
    color: var(--charcoal);
    font-size: 16.5px;
    line-height: 1.65;
}

#MainMenu, footer, header { visibility: hidden !important; height: 0 !important; }
div[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }

.block-container {
    padding-top: 1.75rem !important;
    padding-bottom: 4.5rem !important;
    max-width: 1100px !important;
}

/* Type */
p, label, li, .stMarkdown, .stCaption { line-height: 1.65 !important; }
h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    font-family: 'Fraunces', Georgia, serif !important;
    color: var(--charcoal) !important;
    font-weight: 600 !important;
    letter-spacing: -0.022em;
    line-height: 1.22 !important;
}

/* ════════════ HEADER ════════════ */
.abh-header {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.65rem 2rem 1.4rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-1), var(--shadow-2);
}
.abh-logo {
    font-family: 'Fraunces', serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--charcoal);
    margin: 0;
    letter-spacing: -0.025em;
    line-height: 1.15;
}
.abh-logo em {
    font-style: normal;
    color: var(--sage);
    font-weight: 600;
}
.abh-tagline {
    font-size: 0.95rem;
    color: var(--gray);
    margin: 0.4rem 0 0;
    line-height: 1.5;
}
.abh-trust {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1.2rem;
    padding-top: 1.1rem;
    border-top: 1px solid var(--border);
}
.abh-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.78rem;
    font-weight: 550;
    color: var(--gray);
    background: var(--bg);
    border: 1px solid var(--border);
    padding: 0.38rem 0.9rem;
    border-radius: var(--radius-pill);
    letter-spacing: 0.01em;
}
.abh-badge.accent {
    background: var(--sage-soft);
    color: var(--sage-deep);
    border-color: var(--sage-mid);
}

/* ════════════ HERO ════════════ */
.abh-hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(ellipse 70% 90% at 95% 10%, rgba(122,158,142,0.16) 0%, transparent 55%),
        radial-gradient(ellipse 50% 70% at 5% 90%, rgba(201,139,123,0.12) 0%, transparent 50%),
        linear-gradient(165deg, #FFFFFF 0%, #F9F5F0 55%, #F3F0EA 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2.75rem 2.5rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-1), var(--shadow-2);
}
.abh-hero-kicker {
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--sage);
    margin: 0 0 0.75rem;
}
.abh-hero-title {
    font-family: 'Fraunces', serif;
    font-size: clamp(1.85rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--charcoal);
    margin: 0 0 0.85rem;
    line-height: 1.15;
    letter-spacing: -0.03em;
}
.abh-hero-value {
    font-size: 1.1rem;
    color: var(--gray);
    line-height: 1.7;
    max-width: 560px;
    margin: 0;
}

/* ════════════ SIDEBAR / FILTERS ════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #FDFBFA 100%) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1.15rem 2rem !important;
}
section[data-testid="stSidebar"] label {
    font-size: 0.88rem !important;
    font-weight: 550 !important;
    color: var(--charcoal) !important;
}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--gray-soft) !important;
    font-size: 0.8rem !important;
}

.sb-head {
    margin-bottom: 1.25rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.sb-title {
    font-family: 'Fraunces', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0 0 0.3rem;
}
.sb-sub {
    font-size: 0.86rem;
    color: var(--gray-soft);
    margin: 0;
    line-height: 1.5;
}

.chip-tray {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 1.1rem;
    padding: 0.75rem;
    background: var(--bg);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
}
.chip-tray-label {
    width: 100%;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--gray-soft);
    margin-bottom: 0.15rem;
}
.chip {
    font-size: 0.74rem;
    font-weight: 500;
    background: var(--white);
    color: var(--sage-deep);
    border: 1px solid var(--sage-mid);
    padding: 0.32rem 0.7rem;
    border-radius: var(--radius-pill);
    box-shadow: var(--shadow-1);
}

.fg {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem 1rem 0.85rem;
    margin-bottom: 0.9rem;
    box-shadow: var(--shadow-1);
}
.fg-label {
    font-family: 'Fraunces', serif;
    font-size: 0.98rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0 0 0.2rem;
}
.fg-help {
    font-size: 0.8rem;
    color: var(--gray-soft);
    margin: 0 0 0.75rem;
    line-height: 1.45;
}

/* Slider track & thumb */
div[data-testid="stSlider"] > div > div > div[data-baseweb="slider"] div {
    background-color: var(--terracotta) !important;
}
div[data-testid="stSlider"] [role="slider"] {
    background-color: var(--terracotta) !important;
    border: 2.5px solid #fff !important;
    box-shadow: 0 2px 8px rgba(201,139,123,0.35) !important;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #D49A8A 0%, var(--terracotta) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-pill) !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.25rem !important;
    box-shadow: 0 4px 14px rgba(201,139,123,0.32) !important;
    letter-spacing: 0.01em !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--terracotta-deep) !important;
    box-shadow: 0 6px 18px rgba(201,139,123,0.4) !important;
}
.stButton > button:not([kind="primary"]) {
    background: var(--white) !important;
    color: var(--charcoal) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-pill) !important;
    font-weight: 550 !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--sage) !important;
    background: var(--sage-soft) !important;
    color: var(--sage-deep) !important;
}

/* Text inputs */
.stTextInput input {
    border-radius: 14px !important;
    border: 1.5px solid var(--border) !important;
    background: var(--white) !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
    color: var(--charcoal) !important;
}
.stTextInput input:focus {
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 3px rgba(122,158,142,0.15) !important;
}
.stSelectbox > div > div,
.stMultiSelect > div > div {
    border-radius: 12px !important;
    border-color: var(--border) !important;
}

/* Search shell */
.search-shell {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.25rem 0.35rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-1), var(--shadow-2);
}
.search-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--gray-soft);
    margin: 0 0 0.15rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.2rem;
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.4rem;
    box-shadow: var(--shadow-1);
    margin-bottom: 0.75rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--gray) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1.25rem !important;
    border-radius: 10px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--charcoal) !important;
    background: var(--sage-soft) !important;
    box-shadow: var(--shadow-1) !important;
}

/* ════════════ FACILITY CARDS ════════════ */
.fc {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.75rem 1.85rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-1), var(--shadow-2);
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.fc:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-hover);
}
.fc-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1.25rem;
    flex-wrap: wrap;
}
.fc-name {
    font-family: 'Fraunces', serif;
    font-size: 1.38rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0 0 0.35rem;
    line-height: 1.25;
    letter-spacing: -0.02em;
}
.fc-meta {
    font-size: 0.92rem;
    color: var(--gray);
    margin: 0 0 0.55rem;
}
.fc-type {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--sage-deep);
    background: var(--sage-soft);
    border: 1px solid var(--sage-mid);
    padding: 0.25rem 0.7rem;
    border-radius: 8px;
}
.fc-score {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 5.25rem;
    padding: 0.8rem 1rem;
    border-radius: 14px;
    text-align: center;
    flex-shrink: 0;
}
.fc-score .n {
    font-family: 'Fraunces', serif;
    font-size: 1.85rem;
    font-weight: 700;
    line-height: 1;
}
.fc-score .l {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.28rem;
}
.fc-score.excellent {
    background: var(--excellent-bg);
    color: var(--excellent-fg);
    border: 1px solid #C4DFCE;
}
.fc-score.strong {
    background: var(--strong-bg);
    color: var(--strong-fg);
    border: 1px solid #C5D5E6;
}
.fc-score.good {
    background: var(--good-bg);
    color: var(--good-fg);
    border: 1px solid #E6D7BC;
}
.fc-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 1.1rem 0 0.95rem;
}
.fc-tag {
    font-size: 0.76rem;
    font-weight: 500;
    color: var(--charcoal);
    background: var(--bg);
    border: 1px solid var(--border);
    padding: 0.32rem 0.72rem;
    border-radius: 8px;
}
.fc-cost {
    background: linear-gradient(135deg, var(--terracotta-soft) 0%, #FCFAF8 100%);
    border: 1px solid var(--terracotta-mid);
    border-radius: 14px;
    padding: 1.05rem 1.2rem;
    display: flex;
    flex-wrap: wrap;
    gap: 2rem;
    margin-bottom: 0.75rem;
}
.fc-cost .ci strong {
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--gray-soft);
    margin-bottom: 0.2rem;
}
.fc-cost .ci span {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--charcoal);
    letter-spacing: -0.015em;
}
.fc-blurb {
    font-size: 0.95rem;
    color: var(--gray);
    line-height: 1.55;
    margin: 0.4rem 0 0;
    font-style: italic;
}

/* Results header */
.rh {
    margin: 0.35rem 0 1.25rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.rh-title {
    font-family: 'Fraunces', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0;
    letter-spacing: -0.02em;
}
.rh-title em {
    font-style: normal;
    color: var(--sage);
}
.rh-sub {
    font-size: 0.9rem;
    color: var(--gray-soft);
    margin: 0.3rem 0 0;
}

/* Empty */
.empty {
    text-align: center;
    padding: 3.5rem 2rem;
    background: var(--white);
    border: 1.5px dashed var(--border);
    border-radius: var(--radius);
    margin: 1rem 0 1.75rem;
    box-shadow: var(--shadow-1);
}
.empty-ico { font-size: 2.35rem; margin-bottom: 0.85rem; opacity: 0.9; }
.empty-h {
    font-family: 'Fraunces', serif;
    font-size: 1.3rem;
    color: var(--charcoal);
    margin: 0 0 0.55rem;
}
.empty-p {
    font-size: 0.98rem;
    color: var(--gray);
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.65;
}

/* Gentle note */
.gentle {
    font-size: 0.9rem;
    color: var(--gray);
    line-height: 1.7;
    background: var(--white);
    border: 1px solid var(--border);
    border-left: 4px solid var(--sage);
    border-radius: 0 14px 14px 0;
    padding: 1.1rem 1.35rem;
    margin: 0.9rem 0 1.4rem;
    box-shadow: var(--shadow-1);
}

/* Map */
.map-wrap {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    box-shadow: var(--shadow-1), var(--shadow-2);
    margin-bottom: 1rem;
}
.map-cap {
    font-size: 0.92rem;
    color: var(--gray);
    margin: 0 0 1rem;
    line-height: 1.55;
}

/* Resources hub */
.res-intro {
    font-size: 1.05rem;
    color: var(--gray);
    line-height: 1.7;
    margin: 0.25rem 0 1.75rem;
    max-width: 520px;
}
.res-section {
    font-family: 'Fraunces', serif;
    font-size: 1.18rem;
    color: var(--charcoal);
    margin: 2rem 0 1.1rem;
    padding-bottom: 0.55rem;
    border-bottom: 1px solid var(--border);
    letter-spacing: -0.015em;
}
.res-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.5rem 1.5rem 1.35rem;
    margin-bottom: 1rem;
    min-height: 168px;
    box-shadow: var(--shadow-1), var(--shadow-2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.res-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}
.res-ico { font-size: 1.55rem; margin-bottom: 0.55rem; }
.res-cat {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--sage);
}
.res-name {
    font-family: 'Fraunces', serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--charcoal);
    margin: 0.4rem 0 0.5rem;
    line-height: 1.3;
}
.res-desc {
    font-size: 0.9rem;
    color: var(--gray);
    line-height: 1.6;
    margin: 0;
}

/* Footer */
.abh-foot {
    margin-top: 3.25rem;
    padding: 2.5rem 1rem 1.5rem;
    border-top: 1px solid var(--border);
    text-align: center;
}
.abh-foot .brand {
    font-family: 'Fraunces', serif;
    font-size: 1.08rem;
    color: var(--charcoal);
    margin-bottom: 0.55rem;
}
.abh-foot p {
    font-size: 0.84rem;
    color: var(--gray-soft);
    line-height: 1.7;
    max-width: 600px;
    margin: 0.35rem auto;
}
.foot-pills {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1.25rem;
}
.foot-pill {
    font-size: 0.74rem;
    font-weight: 500;
    color: var(--sage-deep);
    background: var(--sage-soft);
    border: 1px solid var(--sage-mid);
    padding: 0.38rem 0.85rem;
    border-radius: var(--radius-pill);
}

/* Expanders */
div[data-testid="stExpander"] {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    box-shadow: var(--shadow-1) !important;
    margin-bottom: 0.85rem !important;
}
div[data-testid="stExpander"] details summary p {
    font-weight: 550 !important;
    color: var(--charcoal) !important;
}

.stSpinner > div { border-top-color: var(--sage) !important; }

@media (max-width: 768px) {
    .abh-hero { padding: 1.75rem 1.35rem; }
    .abh-hero-title { font-size: 1.7rem; }
    .abh-header { padding: 1.2rem 1.25rem; }
    .fc { padding: 1.3rem 1.25rem; }
    .fc-name { font-size: 1.15rem; }
    .fc-top { flex-direction: column; }
    .fc-score {
        flex-direction: row;
        gap: 0.5rem;
        align-self: flex-start;
        min-width: auto;
        padding: 0.55rem 0.9rem;
    }
    .fc-score .n { font-size: 1.35rem; }
    .fc-cost { gap: 1.1rem; }
    .rh-title { font-size: 1.2rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.55rem 0.75rem !important; font-size: 0.8rem !important; }
    .block-container { padding-left: 0.7rem !important; padding-right: 0.7rem !important; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

METHODOLOGY = """
**Scores are a calm planning guide — not a medical recommendation.**

We turn public quality signals into a simple **0–100** number so you can compare without drowning in charts:

- **CMS Hospital Compare star ratings** map onto the score (more stars → higher score)
- **Maternity strengths** (volume, midwifery model, high-risk readiness) inform curated listings
- **Birth centers** reflect accredited, low-intervention care where data supports it

| Badge | Score | What it means for you |
|-------|-------|------------------------|
| **Excellent** | 90+ | Strong public quality signals |
| **Strong** | 80–89 | Solid for most families exploring options |
| **Good** | under 80 | Worth a closer look with your care team |

Tour when you can, confirm insurance, and lean on your provider. Your comfort matters as much as any number.
"""


# ─────────────────────────────────────────────────────────────────────────────
# State & helpers
# ─────────────────────────────────────────────────────────────────────────────
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


def chip_specs(filters: dict) -> list[dict[str, Any]]:
    """Structured chips with remove actions."""
    chips: list[dict[str, Any]] = []
    for r in filters.get("regions") or []:
        chips.append({"label": r, "action": "region", "value": r})
    if filters.get("distance_mode") == "Near my ZIP":
        chips.append({
            "label": f"Within {filters.get('max_distance', 60)} mi · {filters.get('user_zip', '')}",
            "action": "distance",
            "value": None,
        })
    min_q = filters.get("min_quality_score", 0)
    if min_q:
        chips.append({"label": f"Quality {min_q}+", "action": "quality", "value": None})
    for m in filters.get("quality_metrics") or []:
        chips.append({"label": m, "action": "metric", "value": m})
    for s in filters.get("services") or []:
        chips.append({"label": s, "action": "service", "value": s})
    pmin, pmax = filters.get("price_min", 4000), filters.get("price_max", 25000)
    if pmin > 4000 or pmax < 25000:
        chips.append({"label": f"Vaginal ${pmin:,}–${pmax:,}", "action": "vaginal_price", "value": None})
    cs_min = filters.get("csection_price_min", 5000)
    cs_max = filters.get("csection_price_max", 30000)
    if cs_min > 5000 or cs_max < 30000:
        chips.append({"label": f"C-section ${cs_min:,}–${cs_max:,}", "action": "cs_price", "value": None})
    for ins in filters.get("insurance") or []:
        chips.append({"label": ins, "action": "insurance", "value": ins})
    return chips


def remove_chip(action: str, value: Any = None) -> None:
    f = copy.deepcopy(st.session_state.applied_filters)
    if action == "region" and value:
        f["regions"] = [r for r in (f.get("regions") or []) if r != value]
    elif action == "distance":
        f["distance_mode"] = "Statewide"
    elif action == "quality":
        f["min_quality_score"] = 0
    elif action == "metric" and value:
        f["quality_metrics"] = [m for m in (f.get("quality_metrics") or []) if m != value]
    elif action == "service" and value:
        f["services"] = [s for s in (f.get("services") or []) if s != value]
    elif action == "vaginal_price":
        f["price_min"], f["price_max"] = 4000, 25000
    elif action == "cs_price":
        f["csection_price_min"], f["csection_price_max"] = 5000, 30000
    elif action == "insurance" and value:
        f["insurance"] = [i for i in (f.get("insurance") or []) if i != value]
    st.session_state.applied_filters = f


# ─────────────────────────────────────────────────────────────────────────────
# UI sections
# ─────────────────────────────────────────────────────────────────────────────
def render_header(total: int, saved: int) -> None:
    st.markdown(
        f"""
        <div class="abh-header">
            <p class="abh-logo">Atlanta <em>Birth Hub</em></p>
            <p class="abh-tagline">A calm place to explore birth options across Georgia</p>
            <div class="abh-trust">
                <span class="abh-badge accent">{total} verified facilities</span>
                <span class="abh-badge">CMS data</span>
                <span class="abh-badge">No account needed</span>
                <span class="abh-badge">♥ {saved} saved</span>
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
        <div class="gentle">
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
    st.sidebar.markdown(
        """
        <div class="sb-head">
            <p class="sb-title">Narrow your search</p>
            <p class="sb-sub">Choose what matters, then Apply. You can always reset.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    applied = st.session_state.applied_filters
    draft = copy.deepcopy(applied)

    # Removable active chips
    chips = chip_specs(applied)
    if chips:
        st.sidebar.markdown(
            '<div class="chip-tray"><div class="chip-tray-label">Active filters</div></div>',
            unsafe_allow_html=True,
        )
        # Show chips as HTML + remove buttons in a compact row
        for i, chip in enumerate(chips[:8]):
            c1, c2 = st.sidebar.columns([4, 1])
            with c1:
                st.markdown(f'<span class="chip">{chip["label"]}</span>', unsafe_allow_html=True)
            with c2:
                if st.button("×", key=f"rm_chip_{i}_{chip['action']}_{chip['value']}", help=f"Remove {chip['label']}"):
                    remove_chip(chip["action"], chip["value"])
                    st.rerun()

    # Location
    st.sidebar.markdown(
        '<div class="fg"><p class="fg-label">Location</p>'
        '<p class="fg-help">Where would you like to give birth?</p></div>',
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
        '<div class="fg"><p class="fg-label">Quality</p>'
        '<p class="fg-help">Set a floor if you like — or leave open to see everyone.</p></div>',
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
        placeholder="Optional — pick any that matter",
    )

    # Birth experience
    st.sidebar.markdown(
        '<div class="fg"><p class="fg-label">Birth experience</p>'
        '<p class="fg-help">Hospital, midwifery, NICU, water birth, and more.</p></div>',
        unsafe_allow_html=True,
    )
    draft["services"] = st.sidebar.multiselect(
        "Services & care style",
        SERVICE_OPTIONS,
        default=applied.get("services", []),
        placeholder="Optional — pick any that fit you",
    )

    # Budget
    st.sidebar.markdown(
        '<div class="fg"><p class="fg-label">Budget</p>'
        '<p class="fg-help">Facility estimates only — insurance changes your share.</p></div>',
        unsafe_allow_html=True,
    )
    v_price = st.sidebar.slider(
        "Estimated vaginal delivery cost",
        4000, 25000,
        (int(applied.get("price_min", 4000)), int(applied.get("price_max", 25000))),
        step=500,
        format="$%d",
        help="Illustrative facility charge range before insurance.",
    )
    draft["price_min"], draft["price_max"] = v_price

    cs_price = st.sidebar.slider(
        "Estimated C-section cost",
        5000, 30000,
        (int(applied.get("csection_price_min", 5000)), int(applied.get("csection_price_max", 30000))),
        step=500,
        format="$%d",
        help="Birth centers without C-section on site still appear.",
    )
    draft["csection_price_min"], draft["csection_price_max"] = cs_price

    draft["insurance"] = st.sidebar.multiselect(
        "Insurance to keep in mind",
        INSURANCE_OPTIONS,
        default=applied.get("insurance", []),
        placeholder="Optional — any plans you use",
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
    c1, c2 = st.sidebar.columns([1.4, 1])
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
    tags = "".join(f'<span class="fc-tag">{s}</span>' for s in services[:5])
    highlight = row.get("key_strength") or row.get("quality_label") or ""
    ftype = row.get("type", "Hospital")

    st.markdown(
        f"""
        <div class="fc">
            <div class="fc-top">
                <div>
                    <p class="fc-name">{row['name']}</p>
                    <p class="fc-meta">{meta}</p>
                    <span class="fc-type">{ftype}</span>
                </div>
                <div class="fc-score {tier}">
                    <span class="n">{score}</span>
                    <span class="l">{tier_label}</span>
                </div>
            </div>
            <div class="fc-tags">{tags}</div>
            <div class="fc-cost">
                <div class="ci">
                    <strong>Vaginal estimate</strong>
                    <span>{row.get('vaginal_cost_display', '—')}</span>
                </div>
                <div class="ci">
                    <strong>C-section estimate</strong>
                    <span>{row.get('csection_cost_display', '—')}</span>
                </div>
            </div>
            <p class="fc-blurb">{highlight}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns([1.35, 1])
    with b1:
        if st.button(
            "♥ Saved" if saved else "♡ Save to compare",
            key=f"save_btn_{key_prefix}_{fid}",
            type="primary" if not saved else "secondary",
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
        <div class="rh">
            <p class="rh-title"><em>{len(df)}</em> places for you to explore</p>
            <p class="rh-sub">Highest quality first — change sort anytime</p>
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
        '<div class="map-wrap"><p class="map-cap">'
        "Explore locations across Georgia. Tap a pin for a quick snapshot — "
        "the same trusted listings as Search, laid out on the map."
        "</p>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown("</div>", unsafe_allow_html=True)
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
        st_folium(m, width=None, height=520, returned_objects=[])
    st.markdown("</div>", unsafe_allow_html=True)


def render_resources() -> None:
    st.markdown(
        '<p class="res-intro">Support beyond the hospital walls — education, '
        "postpartum care, feeding, and community resources across Georgia.</p>",
        unsafe_allow_html=True,
    )
    resources = load_resources()
    for category in resources["category"].unique():
        st.markdown(f'<p class="res-section">{category}</p>', unsafe_allow_html=True)
        cat = resources[resources["category"] == category]
        cols = st.columns(2, gap="medium")
        for i, (_, r) in enumerate(cat.iterrows()):
            with cols[i % 2]:
                st.markdown(
                    f"""
                    <div class="res-card">
                        <div class="res-ico">{r['icon']}</div>
                        <div class="res-cat">{r['category']}</div>
                        <div class="res-name">{r['name']}</div>
                        <p class="res-desc">{r['description']}</p>
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
        <div class="rh">
            <p class="rh-title"><em>{len(saved)}</em> saved for you</p>
            <p class="rh-sub">Compare side by side anytime this session</p>
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
        <div class="abh-foot">
            <div class="brand">Atlanta Birth Hub</div>
            <p>{total} facilities · CMS Hospital Compare & public transparency sources · Updated {today}</p>
            <p>Estimates are for planning only. Not medical or financial advice.
            Confirm details with your care team and hospital billing office.</p>
            <div class="foot-pills">
                <span class="foot-pill">CMS Hospital Compare</span>
                <span class="foot-pill">Price transparency</span>
                <span class="foot-pill">Georgia resources</span>
                <span class="foot-pill">No account required</span>
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

    st.markdown(
        '<div class="search-shell"><p class="search-label">Search</p></div>',
        unsafe_allow_html=True,
    )
    st.session_state.search_query = st.text_input(
        "Search by name or city",
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