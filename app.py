"""
Atlanta Birth Hub — GENIUS MODE visual overhaul.
Calm Airbnb-grade hierarchy, softer blush accents.
All data, filters, map, resources, and save/compare preserved.
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

# ═══════════════════════════════════════════════════════════════════════════
# MAXIMUM CSS — override Streamlit as hard as the framework allows
# ═══════════════════════════════════════════════════════════════════════════
CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

:root {
    --bg: #F8F5F1;
    --bg2: #FBF9F6;
    --white: #FFFFFF;
    --blush: #C99A8A;
    --blush-hover: #B88676;
    --blush-soft: #F8F0EC;
    --blush-line: #E5CFC5;
    --sage: #7A9E8E;
    --sage-soft: #EAF3EF;
    --sage-line: #C9DDD3;
    --sage-deep: #54786A;
    --ink: #1F1F1F;
    --ink2: #4A4541;
    --muted: #8A837C;
    --line: #E8E2D9;
    --line2: #F0EBE4;
    --sx: 0 1px 2px rgba(31,31,31,0.04);
    --sm: 0 2px 8px rgba(31,31,31,0.04), 0 1px 2px rgba(31,31,31,0.03);
    --md: 0 10px 30px rgba(31,31,31,0.06), 0 2px 8px rgba(31,31,31,0.03);
    --lg: 0 22px 56px rgba(31,31,31,0.08), 0 6px 16px rgba(31,31,31,0.04);
    --ex-bg: #E8F4EC; --ex-fg: #2D6A47; --ex-bd: #BFDCCB;
    --st-bg: #EAF0F6; --st-fg: #355A7A; --st-bd: #C2D4E6;
    --gd-bg: #F8F1E6; --gd-fg: #8A6424; --gd-bd: #E6D6B8;
    --r: 20px;
    --rp: 999px;
}

/* ── Nuclear reset ── */
html, body, .stApp, [class*="css"], p, span, label, input, button, textarea, select, div {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background: var(--bg) !important;
    color: var(--ink);
    font-size: 16.5px;
    line-height: 1.65;
}
#MainMenu, footer, header { visibility: hidden !important; height: 0 !important; }
div[data-testid="stDecoration"],
div[data-testid="stToolbar"],
div[data-testid="stStatusWidget"],
#stDecoration { display: none !important; }

.block-container {
    padding: 2.25rem 2rem 5.5rem !important;
    max-width: 1040px !important;
}
section.main .block-container { max-width: 1040px !important; }

/* Headings */
h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important;
    color: var(--ink) !important;
    font-weight: 600 !important;
    letter-spacing: -0.028em !important;
    line-height: 1.18 !important;
}

/* Reduce Streamlit element density */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--line) !important;
    border-radius: 16px !important;
}
[data-testid="stMarkdownContainer"] p { line-height: 1.65 !important; }

/* ════════════ HEADER ════════════ */
.abh-h {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 2rem 2.25rem 1.75rem;
    margin-bottom: 1.75rem;
    box-shadow: var(--sm);
}
.abh-logo {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--ink);
    margin: 0;
    letter-spacing: -0.035em;
    line-height: 1.1;
}
.abh-logo em {
    font-style: normal;
    color: var(--sage);
    font-weight: 600;
}
.abh-tag {
    font-size: 1.02rem;
    color: var(--ink2);
    margin: 0.55rem 0 0;
    line-height: 1.5;
    font-weight: 400;
}
.abh-trust {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 1.5rem;
    padding-top: 1.35rem;
    border-top: 1px solid var(--line2);
}
.abh-pill {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--ink2);
    background: var(--bg);
    border: 1px solid var(--line);
    padding: 0.48rem 1.05rem;
    border-radius: var(--rp);
    letter-spacing: 0.01em;
}
.abh-pill.on {
    background: var(--sage-soft);
    color: var(--sage-deep);
    border-color: var(--sage-line);
    font-weight: 600;
}

/* ════════════ HERO ════════════ */
.abh-hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(ellipse 70% 90% at 100% -10%, rgba(201,154,138,0.16) 0%, transparent 55%),
        radial-gradient(ellipse 50% 70% at -5% 110%, rgba(122,158,142,0.12) 0%, transparent 50%),
        linear-gradient(168deg, #FFFFFF 0%, #FBF8F4 100%);
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 3.5rem 3rem 3.25rem;
    margin-bottom: 2.25rem;
    box-shadow: var(--md);
}
.abh-kicker {
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.17em;
    text-transform: uppercase;
    color: var(--sage);
    margin: 0 0 1rem;
}
.abh-h1 {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: clamp(2.1rem, 4.8vw, 2.9rem);
    font-weight: 700;
    color: var(--ink);
    margin: 0 0 1.15rem;
    line-height: 1.1;
    letter-spacing: -0.04em;
    max-width: 13ch;
}
.abh-value {
    font-size: 1.15rem;
    color: var(--ink2);
    line-height: 1.75;
    max-width: 36em;
    margin: 0;
    font-weight: 400;
}

/* ════════════ SIDEBAR ════════════ */
section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--line) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding: 2rem 1.35rem 3.5rem !important;
    background: var(--white) !important;
}
section[data-testid="stSidebar"] label {
    font-size: 0.9rem !important;
    font-weight: 550 !important;
    color: var(--ink) !important;
    letter-spacing: -0.01em !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    opacity: 1 !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
    font-size: 0.84rem !important;
    line-height: 1.55 !important;
}
section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0.1rem; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div {
    padding-bottom: 0.15rem;
}

.sb-h { margin-bottom: 1.75rem; padding-bottom: 1.25rem; border-bottom: 1px solid var(--line2); }
.sb-t {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 0.45rem;
    letter-spacing: -0.025em;
}
.sb-s {
    font-size: 0.9rem;
    color: var(--muted);
    margin: 0;
    line-height: 1.55;
}

.chips {
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem 1.05rem;
    margin-bottom: 1.5rem;
}
.chips-l {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.11em;
    color: var(--muted);
    margin-bottom: 0.65rem;
}
.chip {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 500;
    background: var(--white);
    color: var(--sage-deep);
    border: 1px solid var(--sage-line);
    padding: 0.38rem 0.8rem;
    border-radius: var(--rp);
    margin: 0.18rem 0.25rem 0.18rem 0;
    box-shadow: var(--sx);
}

.fg {
    background: var(--bg2);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.25rem 1.15rem 1.1rem;
    margin: 0 0 1.25rem;
    box-shadow: var(--sx);
}
.fg-t {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 0.3rem;
}
.fg-h {
    font-size: 0.84rem;
    color: var(--muted);
    margin: 0 0 1rem;
    line-height: 1.5;
}

/* Form controls */
.stTextInput input {
    border-radius: 14px !important;
    border: 1.5px solid var(--line) !important;
    background: var(--white) !important;
    padding: 0.9rem 1.15rem !important;
    font-size: 0.95rem !important;
    color: var(--ink) !important;
    box-shadow: var(--sx) !important;
}
.stTextInput input:focus {
    border-color: var(--blush) !important;
    box-shadow: 0 0 0 3px rgba(201,154,138,0.2) !important;
}
.stSelectbox > div > div,
.stMultiSelect > div > div {
    border-radius: 14px !important;
    border-color: var(--line) !important;
    background: var(--white) !important;
    box-shadow: var(--sx) !important;
    min-height: 2.85rem !important;
}

/* Radio as soft segments */
div[role="radiogroup"] { gap: 0.55rem !important; flex-wrap: wrap !important; }
div[role="radiogroup"] label {
    background: var(--white) !important;
    border: 1.5px solid var(--line) !important;
    border-radius: var(--rp) !important;
    padding: 0.5rem 1.1rem !important;
    margin: 0 !important;
    transition: all 0.15s ease !important;
}
div[role="radiogroup"] label:has(input:checked) {
    background: var(--sage-soft) !important;
    border-color: var(--sage-line) !important;
}

/* Sliders */
div[data-testid="stSlider"] > div > div > div { background: var(--blush) !important; }
div[data-testid="stSlider"] [role="slider"] {
    background: var(--blush) !important;
    border: 3px solid #fff !important;
    box-shadow: 0 2px 12px rgba(201,154,138,0.45) !important;
    width: 1.2rem !important;
    height: 1.2rem !important;
}
div[data-testid="stSlider"] { padding-top: 0.35rem !important; padding-bottom: 0.65rem !important; }

/* Buttons */
.stButton > button {
    border-radius: var(--rp) !important;
    font-weight: 600 !important;
    font-size: 0.93rem !important;
    padding: 0.75rem 1.4rem !important;
    min-height: 3rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.18s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--blush) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 4px 18px rgba(201,154,138,0.38) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--blush-hover) !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(201,154,138,0.42) !important;
}
.stButton > button:not([kind="primary"]) {
    background: var(--white) !important;
    color: var(--ink) !important;
    border: 1.5px solid var(--line) !important;
    box-shadow: var(--sx) !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--sage) !important;
    background: var(--sage-soft) !important;
    color: var(--sage-deep) !important;
}

.stLinkButton > a {
    border-radius: var(--rp) !important;
    border: 1.5px solid var(--line) !important;
    background: var(--white) !important;
    color: var(--ink) !important;
    font-weight: 550 !important;
    padding: 0.7rem 1.25rem !important;
    box-shadow: var(--sx) !important;
}
.stLinkButton > a:hover {
    border-color: var(--blush) !important;
    background: var(--blush-soft) !important;
    color: var(--blush-hover) !important;
}

/* Search */
.search-box {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1.35rem 1.5rem 0.55rem;
    margin-bottom: 2rem;
    box-shadow: var(--sm);
}
.search-lbl {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0 0 0.1rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.3rem;
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 0.5rem;
    box-shadow: var(--sm);
    margin-bottom: 2rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    font-size: 0.93rem !important;
    padding: 0.85rem 1.5rem !important;
    border-radius: 12px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    background: var(--bg) !important;
    box-shadow: var(--sx) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ════════════ FACILITY CARDS ════════════ */
.fc {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 2.15rem 2.15rem 1.9rem;
    margin-bottom: 2rem;
    box-shadow: var(--md);
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.fc:hover {
    transform: translateY(-4px);
    box-shadow: var(--lg);
}
.fc-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1.5rem;
    flex-wrap: wrap;
}
.fc-name {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 0.45rem;
    line-height: 1.2;
    letter-spacing: -0.03em;
}
.fc-meta {
    font-size: 0.98rem;
    color: var(--ink2);
    margin: 0 0 0.8rem;
    font-weight: 400;
}
.fc-type {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--sage-deep);
    background: var(--sage-soft);
    border: 1px solid var(--sage-line);
    padding: 0.32rem 0.85rem;
    border-radius: 10px;
}
.fc-score {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 5.75rem;
    padding: 1.05rem 1.15rem;
    border-radius: 18px;
    text-align: center;
    flex-shrink: 0;
}
.fc-score .n {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 2.1rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.04em;
}
.fc-score .l {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.4rem;
}
.fc-score.ex { background: var(--ex-bg); color: var(--ex-fg); border: 1px solid var(--ex-bd); }
.fc-score.st { background: var(--st-bg); color: var(--st-fg); border: 1px solid var(--st-bd); }
.fc-score.gd { background: var(--gd-bg); color: var(--gd-fg); border: 1px solid var(--gd-bd); }

.fc-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 1.5rem 0 1.25rem;
}
.fc-tag {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--ink2);
    background: var(--bg);
    border: 1px solid var(--line);
    padding: 0.42rem 0.9rem;
    border-radius: 10px;
}
.fc-cost {
    background: linear-gradient(150deg, var(--blush-soft) 0%, #FFFCFA 100%);
    border: 1px solid var(--blush-line);
    border-radius: 16px;
    padding: 1.3rem 1.45rem;
    display: flex;
    flex-wrap: wrap;
    gap: 2.5rem;
    margin-bottom: 1rem;
}
.fc-cost .ci strong {
    display: block;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--muted);
    margin-bottom: 0.3rem;
}
.fc-cost .ci span {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--ink);
    letter-spacing: -0.025em;
}
.fc-blurb {
    font-size: 1rem;
    color: var(--ink2);
    line-height: 1.6;
    margin: 0.55rem 0 0;
    font-style: italic;
}

/* Results header */
.rh {
    margin: 0.15rem 0 2rem;
    padding-bottom: 1.4rem;
    border-bottom: 1px solid var(--line);
}
.rh-t {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.55rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0;
    letter-spacing: -0.03em;
}
.rh-t em { font-style: normal; color: var(--sage); }
.rh-s {
    font-size: 0.98rem;
    color: var(--muted);
    margin: 0.45rem 0 0;
}

/* Empty */
.empty {
    text-align: center;
    padding: 4.5rem 2.25rem;
    background: var(--white);
    border: 1.5px dashed var(--line);
    border-radius: 22px;
    margin: 1.5rem 0 2.25rem;
    box-shadow: var(--sm);
}
.empty-i { font-size: 2.6rem; margin-bottom: 1.1rem; opacity: 0.9; }
.empty-t {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.4rem;
    color: var(--ink);
    margin: 0 0 0.65rem;
}
.empty-p {
    font-size: 1.02rem;
    color: var(--ink2);
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.7;
}

/* Gentle note */
.gentle {
    font-size: 0.98rem;
    color: var(--ink2);
    line-height: 1.75;
    background: var(--white);
    border: 1px solid var(--line);
    border-left: 4px solid var(--sage);
    border-radius: 0 18px 18px 0;
    padding: 1.35rem 1.6rem;
    margin: 1.25rem 0 2rem;
    box-shadow: var(--sm);
}

/* Map */
.map-box {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1.65rem;
    box-shadow: var(--md);
    margin-bottom: 1.5rem;
}
.map-cap {
    font-size: 1rem;
    color: var(--ink2);
    margin: 0 0 1.25rem;
    line-height: 1.65;
}

/* Resources */
.res-intro {
    font-size: 1.12rem;
    color: var(--ink2);
    line-height: 1.75;
    margin: 0.25rem 0 2.25rem;
    max-width: 38em;
}
.res-sec {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.3rem;
    color: var(--ink);
    margin: 2.75rem 0 1.4rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--line);
    letter-spacing: -0.025em;
}
.res-c {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.9rem 1.75rem 1.65rem;
    margin-bottom: 1.35rem;
    min-height: 188px;
    box-shadow: var(--md);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.res-c:hover { transform: translateY(-3px); box-shadow: var(--lg); }
.res-i { font-size: 1.7rem; margin-bottom: 0.7rem; }
.res-k {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: var(--sage);
}
.res-n {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.18rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0.5rem 0 0.6rem;
    line-height: 1.28;
    letter-spacing: -0.02em;
}
.res-d {
    font-size: 0.98rem;
    color: var(--ink2);
    line-height: 1.65;
    margin: 0;
}

/* Footer */
.abh-f {
    margin-top: 4.5rem;
    padding: 3.25rem 1rem 2rem;
    border-top: 1px solid var(--line);
    text-align: center;
}
.abh-f .b {
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 1.2rem;
    color: var(--ink);
    margin-bottom: 0.7rem;
}
.abh-f p {
    font-size: 0.9rem;
    color: var(--muted);
    line-height: 1.75;
    max-width: 540px;
    margin: 0.4rem auto;
}
.f-pills {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 1.65rem;
}
.f-p {
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--sage-deep);
    background: var(--sage-soft);
    border: 1px solid var(--sage-line);
    padding: 0.45rem 1rem;
    border-radius: var(--rp);
}

/* Expanders */
div[data-testid="stExpander"] {
    background: var(--white) !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    box-shadow: var(--sm) !important;
    margin-bottom: 1.15rem !important;
}
div[data-testid="stExpander"] details { border: none !important; }
div[data-testid="stExpander"] summary { padding: 0.95rem 0.6rem !important; }
div[data-testid="stExpander"] summary p {
    font-weight: 550 !important;
    color: var(--ink) !important;
    font-size: 1rem !important;
}

div[data-testid="stAlert"] {
    border-radius: 16px !important;
    border: 1px solid var(--line) !important;
}

.stSpinner > div { border-top-color: var(--blush) !important; }

/* Sidebar apply zone breathing room */
section[data-testid="stSidebar"] .stButton { margin-top: 0.25rem; }

@media (max-width: 768px) {
    .abh-hero { padding: 2.15rem 1.5rem; border-radius: 20px; }
    .abh-h1 { font-size: 1.85rem; max-width: none; }
    .abh-h { padding: 1.5rem 1.4rem; }
    .fc { padding: 1.5rem 1.4rem; margin-bottom: 1.5rem; border-radius: 18px; }
    .fc-name { font-size: 1.25rem; }
    .fc-row { flex-direction: column; gap: 1.1rem; }
    .fc-score {
        flex-direction: row;
        gap: 0.55rem;
        align-self: flex-start;
        min-width: auto;
        padding: 0.65rem 1.05rem;
    }
    .fc-score .n { font-size: 1.45rem; }
    .fc-cost { gap: 1.35rem; padding: 1.1rem 1.2rem; }
    .rh-t { font-size: 1.3rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.65rem 0.9rem !important; font-size: 0.84rem !important; }
    .block-container { padding: 1.35rem 0.9rem 4rem !important; }
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
        return "ex", "Excellent"
    if score >= 80:
        return "st", "Strong"
    return "gd", "Good"


def chip_specs(filters: dict) -> list[dict[str, Any]]:
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


def render_header(total: int, saved: int) -> None:
    st.markdown(
        f"""
        <div class="abh-h">
            <p class="abh-logo">Atlanta <em>Birth Hub</em></p>
            <p class="abh-tag">A calm place to explore birth options across Georgia</p>
            <div class="abh-trust">
                <span class="abh-pill on">{total} verified facilities</span>
                <span class="abh-pill">CMS data</span>
                <span class="abh-pill">No account needed</span>
                <span class="abh-pill">♥ {saved} saved</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="abh-hero">
            <p class="abh-kicker">For expecting mothers</p>
            <h1 class="abh-h1">Find a birth place that feels right</h1>
            <p class="abh-value">
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
            <div class="empty-i">{icon}</div>
            <p class="empty-t">{title}</p>
            <p class="empty-p">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.markdown(
        """
        <div class="sb-h">
            <p class="sb-t">Narrow your search</p>
            <p class="sb-s">Choose what matters, then Apply. You can always start over.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    applied = st.session_state.applied_filters
    draft = copy.deepcopy(applied)

    chips = chip_specs(applied)
    if chips:
        labels = " ".join(f'<span class="chip">{c["label"]}</span>' for c in chips[:10])
        st.sidebar.markdown(
            f'<div class="chips"><div class="chips-l">Active filters</div>{labels}</div>',
            unsafe_allow_html=True,
        )
        st.sidebar.caption("Tap to remove:")
        n = min(len(chips), 4)
        cols = st.sidebar.columns(n)
        for i, chip in enumerate(chips[:8]):
            with cols[i % n]:
                short = chip["label"][:12] + ("…" if len(chip["label"]) > 12 else "")
                if st.button(f"× {short}", key=f"rm_{i}_{chip['action']}_{chip['value']}", use_container_width=True):
                    remove_chip(chip["action"], chip["value"])
                    st.rerun()

    st.sidebar.markdown(
        '<div class="fg"><p class="fg-t">Location</p>'
        '<p class="fg-h">Where would you like to give birth?</p></div>',
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
            help="Straight-line estimate to each facility.",
        )
        draft["max_distance"] = st.sidebar.slider(
            "Maximum drive (miles)",
            10, 120,
            int(applied.get("max_distance", 60)),
            step=5,
        )
    else:
        draft["user_zip"] = applied.get("user_zip", DEFAULT_ZIP)

    st.sidebar.markdown(
        '<div class="fg"><p class="fg-t">Quality</p>'
        '<p class="fg-h">Set a floor if you like — or leave open.</p></div>',
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
        placeholder="Optional",
    )

    st.sidebar.markdown(
        '<div class="fg"><p class="fg-t">Birth experience</p>'
        '<p class="fg-h">Hospital, midwifery, NICU, water birth, and more.</p></div>',
        unsafe_allow_html=True,
    )
    draft["services"] = st.sidebar.multiselect(
        "Services & care style",
        SERVICE_OPTIONS,
        default=applied.get("services", []),
        placeholder="Optional",
    )

    st.sidebar.markdown(
        '<div class="fg"><p class="fg-t">Budget</p>'
        '<p class="fg-h">Facility estimates only — insurance changes your share.</p></div>',
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
        placeholder="Optional",
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
    st.sidebar.markdown("")
    c1, c2 = st.sidebar.columns([1.5, 1])
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
            <div class="fc-row">
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

    b1, b2 = st.columns([1.45, 1])
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
            <p class="rh-t"><em>{len(df)}</em> places for you to explore</p>
            <p class="rh-s">Highest quality first — change sort anytime</p>
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
        '<div class="map-box"><p class="map-cap">'
        "Explore locations across Georgia. Tap a pin for a quick snapshot — "
        "the same trusted listings as Search, on the map."
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
                icon=folium.Icon(color="beige", icon="info-sign"),
            ).add_to(cluster)
        st_folium(m, width=None, height=560, returned_objects=[])
    st.markdown("</div>", unsafe_allow_html=True)


def render_resources() -> None:
    st.markdown(
        '<p class="res-intro">Support beyond the hospital walls — education, '
        "postpartum care, feeding, and community resources across Georgia.</p>",
        unsafe_allow_html=True,
    )
    resources = load_resources()
    for category in resources["category"].unique():
        st.markdown(f'<p class="res-sec">{category}</p>', unsafe_allow_html=True)
        cat = resources[resources["category"] == category]
        cols = st.columns(2, gap="large")
        for i, (_, r) in enumerate(cat.iterrows()):
            with cols[i % 2]:
                st.markdown(
                    f"""
                    <div class="res-c">
                        <div class="res-i">{r['icon']}</div>
                        <div class="res-k">{r['category']}</div>
                        <div class="res-n">{r['name']}</div>
                        <p class="res-d">{r['description']}</p>
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
            <p class="rh-t"><em>{len(saved)}</em> saved for you</p>
            <p class="rh-s">Compare side by side anytime this session</p>
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
        <div class="abh-f">
            <div class="b">Atlanta Birth Hub</div>
            <p>{total} facilities · CMS Hospital Compare & public transparency sources · Updated {today}</p>
            <p>Estimates are for planning only. Not medical or financial advice.
            Confirm details with your care team and hospital billing office.</p>
            <div class="f-pills">
                <span class="f-p">CMS Hospital Compare</span>
                <span class="f-p">Price transparency</span>
                <span class="f-p">Georgia resources</span>
                <span class="f-p">No account required</span>
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
        '<div class="search-box"><p class="search-lbl">Search</p></div>',
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