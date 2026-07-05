"""
ATL Birth Hub — Data Ingestion Module

Loads facility data from CSV or falls back to curated sample data.
Designed for future integration with hospital Machine-Readable Files (MRFs)
and CMS quality datasets.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import pandas as pd

from facility_enrichment import enrich_facilities
from filters_config import DEFAULT_FILTERS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
FACILITIES_CSV = DATA_DIR / "facilities.csv"

# ---------------------------------------------------------------------------
# Metro Atlanta ZIP centroids (approximate) for distance calculations
# Extend this dict or swap for geopy / Census ZCTA data in production.
# ---------------------------------------------------------------------------
ZIP_COORDINATES: dict[str, tuple[float, float]] = {
    "30301": (33.7490, -84.3880),
    "30303": (33.7515, -84.3915),
    "30305": (33.8410, -84.3795),
    "30306": (33.7860, -84.3510),
    "30307": (33.7650, -84.3340),
    "30308": (33.7710, -84.3770),
    "30309": (33.7980, -84.3880),
    "30310": (33.7310, -84.4280),
    "30311": (33.7390, -84.4670),
    "30312": (33.7400, -84.3770),
    "30313": (33.7620, -84.3960),
    "30314": (33.7580, -84.4240),
    "30315": (33.7070, -84.3680),
    "30316": (33.7200, -84.3370),
    "30317": (33.7520, -84.3120),
    "30318": (33.7920, -84.4320),
    "30319": (33.8650, -84.3360),
    "30324": (33.8190, -84.3540),
    "30326": (33.8480, -84.3620),
    "30327": (33.8680, -84.4060),
    "30328": (33.9330, -84.3740),
    "30329": (33.8250, -84.3260),
    "30331": (33.7220, -84.4910),
    "30332": (33.7750, -84.3960),
    "30334": (33.7490, -84.3880),
    "30336": (33.7350, -84.5180),
    "30337": (33.6530, -84.4490),
    "30338": (33.9460, -84.3340),
    "30339": (33.8830, -84.4610),
    "30340": (33.8980, -84.2620),
    "30341": (33.8910, -84.2830),
    "30342": (33.8780, -84.3780),
    "30344": (33.6830, -84.4590),
    "30345": (33.8510, -84.2860),
    "30346": (33.9230, -84.3410),
    "30349": (33.6180, -84.4770),
    "30350": (33.9800, -84.3340),
    "30354": (33.6620, -84.3860),
    "30360": (33.9310, -84.2730),
    "30004": (34.0750, -84.2940),
    "30005": (34.0780, -84.2210),
    "30008": (33.9490, -84.4990),
    "30009": (34.0230, -84.3610),
    "30022": (34.0230, -84.1980),
    "30024": (34.0520, -84.1680),
    "30030": (33.7750, -84.2960),
    "30032": (33.7410, -84.2750),
    "30033": (33.8080, -84.2820),
    "30034": (33.7070, -84.2750),
    "30035": (33.7260, -84.2560),
    "30038": (33.6950, -84.2270),
    "30039": (33.9780, -84.1680),
    "30043": (33.9770, -84.1200),
    "30044": (33.9420, -84.1250),
    "30045": (33.9340, -84.0720),
    "30047": (33.7570, -84.0060),
    "30052": (33.7890, -84.0030),
    "30058": (33.6940, -84.0850),
    "30060": (33.9520, -84.5490),
    "30062": (34.0230, -84.4720),
    "30064": (33.9160, -84.5580),
    "30066": (34.0180, -84.5200),
    "30067": (33.9780, -84.4560),
    "30068": (33.9670, -84.4200),
    "30071": (33.9560, -84.1980),
    "30075": (34.0400, -84.4200),
    "30076": (34.0410, -84.3410),
    "30078": (33.8570, -84.0190),
    "30079": (33.7070, -84.1680),
    "30080": (33.8850, -84.5140),
    "30082": (33.8670, -84.4770),
    "30083": (33.7140, -84.2180),
    "30084": (33.8910, -84.2130),
    "30087": (33.6170, -84.0330),
    "30088": (33.7570, -84.1940),
    "30092": (33.9590, -84.2200),
    "30093": (33.9780, -84.1540),
    "30096": (33.9780, -84.1200),
    "30101": (33.9850, -84.5940),
    "30106": (33.7860, -84.5860),
    "30126": (33.6670, -84.5810),
    "30127": (33.6670, -84.0170),
    "30144": (33.9520, -84.5490),
    "30213": (33.6100, -84.4540),
    "30214": (33.4700, -84.4510),
    "30260": (33.6830, -84.4490),
    "30268": (33.5200, -84.6510),
    "30274": (33.5700, -84.3340),
    "30281": (33.4470, -84.1830),
    "30291": (33.5960, -84.4500),
    "30296": (33.5700, -84.2880),
    "30297": (33.6000, -84.2880),
}

DEFAULT_ZIP = "30341"

# Updated automatically when CMS data is refreshed.
COVERAGE_NOTE = (
    "128 Georgia birthing facilities from CMS Hospital Compare — hospitals statewide plus "
    "accredited birth centers. Psychiatric, children's-only, and VA hospitals excluded."
)

PRIORITY_LABELS: dict[str, str] = {
    "Lower costs": "Keep facility fees as low as possible",
    "Lower C-section rates": "Prefer hospitals with lower surgical birth rates",
    "Strong midwifery support": "Midwife-led or midwife-friendly care",
    "High-risk / NICU capabilities": "Level III NICU and complex pregnancy support",
    "Holistic / low-intervention": "Minimal interventions, birth-center style",
    "Best overall ratings": "Top quality scores and patient satisfaction",
}

PRIORITY_OPTIONS = [
    "Lower costs",
    "Lower C-section rates",
    "Strong midwifery support",
    "High-risk / NICU capabilities",
    "Holistic / low-intervention",
    "Best overall ratings",
]

QUALITY_FILTER_OPTIONS = [
    "Strong",
    "Good",
    "Good for complex",
    "Fair",
    "Not rated",
    "Excellent for low-intervention",
]

# ---------------------------------------------------------------------------
# Sample facility data — aligned with illustrative public-source ranges
# Numeric fields (vaginal_cost, etc.) are midpoints used for sorting/scoring.
# ---------------------------------------------------------------------------
SAMPLE_FACILITIES: list[dict] = [
    {
        "facility_id": "northside-atl",
        "name": "Northside Hospital Atlanta",
        "type": "Hospital",
        "location": "Atlanta (Sandy Springs)",
        "address": "1000 Johnson Ferry Rd NE, Atlanta, GA 30342",
        "zip_code": "30342",
        "latitude": 33.8780,
        "longitude": -84.3780,
        "vaginal_cost": 11250,
        "csection_cost": 16000,
        "vaginal_cost_display": "$8.5k–$14k",
        "csection_cost_display": "$12k–$20k",
        "quality_rating": 4.4,
        "quality_label": "Strong",
        "cms_stars": 4,
        "csection_rate": 0.275,
        "csection_rate_display": "~25–30%",
        "nicu_level": "Level III",
        "birth_center": False,
        "teaching_hospital": False,
        "high_risk": False,
        "key_strength": "High volume leader",
        "strengths": "Renowned maternity program; private rooms; strong lactation support; experienced teams for routine births",
        "considerations": "Higher costs than community hospitals; busy environment; parking can be challenging during peak hours",
        "priorities": ["Best overall ratings", "High-risk / NICU capabilities"],
    },
    {
        "facility_id": "emory-midtown",
        "name": "Emory University Hospital Midtown",
        "type": "Hospital",
        "location": "Atlanta (Midtown)",
        "address": "550 Peachtree St NE, Atlanta, GA 30308",
        "zip_code": "30308",
        "latitude": 33.7710,
        "longitude": -84.3770,
        "vaginal_cost": 12250,
        "csection_cost": 17750,
        "vaginal_cost_display": "$9k–$15.5k",
        "csection_cost_display": "$13.5k–$22k",
        "quality_rating": 4.5,
        "quality_label": "Strong",
        "cms_stars": 5,
        "csection_rate": 0.28,
        "csection_rate_display": "~28%",
        "nicu_level": "Level III",
        "birth_center": False,
        "teaching_hospital": True,
        "high_risk": True,
        "key_strength": "High-risk expertise",
        "strengths": "Academic medical center; complex care expertise; strong maternal-fetal medicine; research-backed protocols",
        "considerations": "Premium pricing; urban campus; may feel more clinical for families wanting a cozy birth experience",
        "priorities": ["High-risk / NICU capabilities", "Best overall ratings", "Strong midwifery support"],
    },
    {
        "facility_id": "piedmont-atl",
        "name": "Piedmont Atlanta Hospital",
        "type": "Hospital",
        "location": "Atlanta",
        "address": "1968 Peachtree Rd NW, Atlanta, GA 30309",
        "zip_code": "30309",
        "latitude": 33.7980,
        "longitude": -84.3880,
        "vaginal_cost": 10500,
        "csection_cost": 15000,
        "vaginal_cost_display": "$7.8k–$13.2k",
        "csection_cost_display": "$11.5k–$18.5k",
        "quality_rating": 4.0,
        "quality_label": "Good",
        "cms_stars": 4,
        "csection_rate": 0.26,
        "csection_rate_display": "~26%",
        "nicu_level": "Level III",
        "birth_center": False,
        "teaching_hospital": True,
        "high_risk": False,
        "key_strength": "Balanced comprehensive care",
        "strengths": "Buckhead location; modern birthing suites; strong patient satisfaction; integrated women's health",
        "considerations": "Costs above metro average; limited public transit access; valet parking fees",
        "priorities": ["Best overall ratings", "Lower C-section rates"],
    },
    {
        "facility_id": "kennestone",
        "name": "Wellstar Kennestone Hospital",
        "type": "Hospital",
        "location": "Marietta",
        "address": "677 Church St NE, Marietta, GA 30060",
        "zip_code": "30060",
        "latitude": 33.9520,
        "longitude": -84.5490,
        "vaginal_cost": 11000,
        "csection_cost": 15750,
        "vaginal_cost_display": "$8.2k–$13.8k",
        "csection_cost_display": "$12k–$19.5k",
        "quality_rating": 3.8,
        "quality_label": "Good",
        "cms_stars": 3,
        "csection_rate": 0.27,
        "csection_rate_display": "~27%",
        "nicu_level": "Level III",
        "birth_center": False,
        "teaching_hospital": False,
        "high_risk": False,
        "key_strength": "Suburban convenience + options",
        "strengths": "Suburban convenience; family-centered care; spacious campus; more approachable than intown pricing",
        "considerations": "Longer drive from core Atlanta; C-section rate near metro average",
        "priorities": ["Lower costs", "High-risk / NICU capabilities"],
    },
    {
        "facility_id": "grady",
        "name": "Grady Memorial Hospital",
        "type": "Hospital",
        "location": "Atlanta",
        "address": "80 Jesse Hill Jr Dr SE, Atlanta, GA 30303",
        "zip_code": "30303",
        "latitude": 33.7515,
        "longitude": -84.3915,
        "vaginal_cost": 8750,
        "csection_cost": 12750,
        "vaginal_cost_display": "$6.5k–$11k",
        "csection_cost_display": "$9.5k–$16k",
        "quality_rating": 3.7,
        "quality_label": "Good for complex",
        "cms_stars": 3,
        "csection_rate": 0.32,
        "csection_rate_display": "~32%",
        "nicu_level": "Level III",
        "birth_center": False,
        "teaching_hospital": True,
        "high_risk": True,
        "key_strength": "Safety net + complex care",
        "strengths": "Safety-net hospital; most affordable hospital option; trauma & high-risk expertise; community-rooted care",
        "considerations": "Busy public hospital; wait times can vary; fewer amenity-focused perks than private hospitals",
        "priorities": ["Lower costs", "High-risk / NICU capabilities"],
    },
    {
        "facility_id": "atl-birth-center",
        "name": "Atlanta Birth Center",
        "type": "Birth Center",
        "location": "Atlanta",
        "address": "1 Baltimore Pl NW, Atlanta, GA 30308",
        "zip_code": "30308",
        "latitude": 33.7680,
        "longitude": -84.3820,
        "vaginal_cost": 6000,
        "csection_cost": None,
        "vaginal_cost_display": "$4.5k–$7.5k*",
        "csection_cost_display": "N/A**",
        "quality_rating": 4.8,
        "quality_label": "Excellent for low-intervention",
        "cms_stars": None,
        "csection_rate": 0.06,
        "csection_rate_display": "Very low (midwifery model)",
        "nicu_level": "N/A",
        "birth_center": True,
        "teaching_hospital": False,
        "high_risk": False,
        "key_strength": "Holistic, accredited birth center",
        "strengths": "Midwifery-led care; homelike suites; water birth options; holistic, low-intervention philosophy",
        "considerations": "Not equipped for C-sections on-site; transfers to hospital if complications arise; limited to low-risk pregnancies",
        "priorities": ["Holistic / low-intervention", "Strong midwifery support", "Lower costs"],
    },
]

LOCAL_RESOURCES: list[dict] = [
    {
        "category": "Birth Centers & Midwifery",
        "name": "Atlanta Birth Center",
        "description": "Atlanta's only freestanding accredited birth center — midwifery-led, holistic care.",
        "link": "https://www.atlantabirthcenter.org/",
        "icon": "🌿",
    },
    {
        "category": "Birth Centers & Midwifery",
        "name": "ACNM Midwife Finder",
        "description": "Find a Certified Nurse-Midwife via the American College of Nurse-Midwives directory.",
        "link": "https://www.midwife.org/find-a-midwife",
        "icon": "🤝",
    },
    {
        "category": "Education & Preparation",
        "name": "Hospital Tours & Childbirth Classes",
        "description": "Virtual tours and classes through Northside, Emory, Piedmont, and Wellstar maternity programs.",
        "link": "https://www.northside.com/",
        "icon": "📚",
    },
    {
        "category": "Education & Preparation",
        "name": "Local Prenatal Wellness",
        "description": "Prenatal yoga, hypnobirthing, and parenting prep classes across metro Atlanta.",
        "link": "https://www.google.com/search?q=prenatal+yoga+atlanta",
        "icon": "🧘",
    },
    {
        "category": "Postpartum & Support",
        "name": "Atlanta Doula Collective",
        "description": "Directory of certified birth and postpartum doulas serving the metro area.",
        "link": "https://www.google.com/search?q=atlanta+doula+collective",
        "icon": "💪",
    },
    {
        "category": "Postpartum & Support",
        "name": "La Leche League of Georgia",
        "description": "Peer-led breastfeeding support groups and IBCLC referrals across the region.",
        "link": "https://www.lllusa.org/",
        "icon": "🤱",
    },
    {
        "category": "Cost & Insurance Guidance",
        "name": "Good Faith Estimates",
        "description": "Always request a personalized Good Faith Estimate from every provider and facility.",
        "link": "https://www.cms.gov/nosurprises",
        "icon": "💳",
    },
    {
        "category": "Cost & Insurance Guidance",
        "name": "Hospital Price Transparency Tools",
        "description": "Use each hospital's price transparency estimator to compare in-network benefits.",
        "link": "https://www.cms.gov/hospital-price-transparency",
        "icon": "💰",
    },
    {
        "category": "Mental Health & Wellness",
        "name": "Postpartum Support International — GA",
        "description": "Warmline, support groups, and referrals for perinatal mood and anxiety disorders.",
        "link": "https://www.postpartum.net/",
        "icon": "💜",
    },
    {
        "category": "Mental Health & Wellness",
        "name": "Perinatal Mental Health Alliance of Georgia",
        "description": "Therapist directory and resources for pregnancy and postpartum mental health.",
        "link": "https://www.google.com/search?q=perinatal+mental+health+georgia",
        "icon": "🌿",
    },
    {
        "category": "Lactation & Feeding",
        "name": "Peach Tree Lactation Consultants",
        "description": "IBCLC-certified consultants offering home and virtual breastfeeding support.",
        "link": "https://www.google.com/search?q=peach+tree+lactation+atlanta",
        "icon": "💚",
    },
    {
        "category": "Lactation & Feeding",
        "name": "Mothers' Milk Bank of Georgia",
        "description": "Donor milk program and breastfeeding resources for NICU and preemie families.",
        "link": "https://www.mothersmilkbankgeorgia.org/",
        "icon": "🍼",
    },
    {
        "category": "Community & Advocacy",
        "name": "Healthy Mothers, Healthy Babies Coalition of GA",
        "description": "Advocacy, education, and resources for maternal and infant health equity statewide.",
        "link": "https://www.hmhbga.org/",
        "icon": "🌸",
    },
    {
        "category": "Community & Advocacy",
        "name": "Georgia WIC Program",
        "description": "Nutrition support, breastfeeding help, and referrals for qualifying families.",
        "link": "https://dph.georgia.gov/WIC",
        "icon": "🍎",
    },
    {
        "category": "Community & Advocacy",
        "name": "Sista Midwife Productions",
        "description": "Culturally congruent doula training and birth support for Black families in Georgia.",
        "link": "https://www.sistamidwife.com/",
        "icon": "✨",
    },
]


# ---------------------------------------------------------------------------
# Distance utilities
# ---------------------------------------------------------------------------
def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in miles between two coordinates."""
    radius_earth_miles = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius_earth_miles * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_zip_coordinates(zip_code: str) -> Optional[tuple[float, float]]:
    """Return (lat, lon) for a ZIP code, or None if unknown."""
    cleaned = str(zip_code).strip()[:5]
    return ZIP_COORDINATES.get(cleaned)


def add_distance_column(df: pd.DataFrame, user_zip: str) -> pd.DataFrame:
    """Add distance_miles column based on user ZIP centroid."""
    result = df.copy()
    user_coords = get_zip_coordinates(user_zip)

    if user_coords is None:
        result["distance_miles"] = None
        return result

    user_lat, user_lon = user_coords
    result["distance_miles"] = result.apply(
        lambda row: round(
            haversine_miles(user_lat, user_lon, row["latitude"], row["longitude"]),
            1,
        ),
        axis=1,
    )
    return result


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------
def compute_priority_score(row: pd.Series, selected_priorities: list[str]) -> float:
    """Score how well a facility matches user-selected priorities (0–100)."""
    if not selected_priorities:
        return 50.0

    score = 0.0
    max_per_priority = 100 / len(selected_priorities)

    for priority in selected_priorities:
        if priority == "Lower costs":
            if pd.notna(row.get("vaginal_cost")) and pd.notna(row.get("csection_cost")):
                avg_cost = (row["vaginal_cost"] + row["csection_cost"]) / 2
            elif pd.notna(row.get("vaginal_cost")):
                avg_cost = row["vaginal_cost"]
            else:
                avg_cost = 99999
            score += max_per_priority * max(0, 1 - avg_cost / 20000)

        elif priority == "Lower C-section rates":
            rate = row.get("csection_rate") or 0.5
            score += max_per_priority * max(0, 1 - rate / 0.5)

        elif priority == "Strong midwifery support":
            score += max_per_priority * (1.0 if row.get("birth_center") else 0.15)

        elif priority == "High-risk / NICU capabilities":
            nicu = str(row.get("nicu_level", ""))
            high_risk = row.get("high_risk", False)
            if "Level III" in nicu and high_risk:
                score += max_per_priority
            elif "Level III" in nicu:
                score += max_per_priority * 0.75
            elif high_risk:
                score += max_per_priority * 0.6

        elif priority == "Holistic / low-intervention":
            if row.get("birth_center"):
                score += max_per_priority
            else:
                rate = row.get("csection_rate") or 0.35
                score += max_per_priority * max(0, 1 - rate / 0.35) * 0.5

        elif priority == "Best overall ratings":
            rating = row.get("quality_rating") or 0
            score += max_per_priority * (rating / 5.0)

    return round(score, 1)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def _postprocess_facility_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize CSV/dataset columns for the app."""
    df = df.copy()
    for col in ("birth_center", "teaching_hospital", "high_risk", "birthing_friendly"):
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    if "priorities" in df.columns:
        df["priorities"] = df["priorities"].apply(
            lambda x: x.split("|") if isinstance(x, str) and x else []
        )
    return enrich_facilities(df)


def apply_filters(df: pd.DataFrame, filters: dict, user_zip: str | None = None) -> pd.DataFrame:
    """Apply sidebar filters to the facility dataframe."""
    result = df.copy()

    query = (filters.get("search_query") or "").strip().lower()
    if query:
        result = result[
            result.apply(
                lambda r: query in str(r["name"]).lower()
                or query in str(r.get("location", "")).lower()
                or query in str(r.get("region", "")).lower(),
                axis=1,
            )
        ]

    regions = filters.get("regions") or []
    if regions:
        result = result[result["region"].isin(regions)]

    if filters.get("distance_mode") != "Statewide" and user_zip:
        result = add_distance_column(result, user_zip)
        max_dist = filters.get("max_distance", 60)
        result = result[result["distance_miles"].isna() | (result["distance_miles"] <= max_dist)]

    min_q = filters.get("min_quality_score", 0)
    if min_q:
        result = result[result["quality_score"] >= min_q]

    for metric in filters.get("quality_metrics") or []:
        if metric == "Birthing-Friendly Hospital":
            result = result[result["birthing_friendly"] == True]  # noqa: E712
        elif metric == "Low C-Section Rate (<28%)":
            result = result[result["csection_rate"] < 0.28]
        elif metric == "High CMS Star Rating (4+)":
            stars = pd.to_numeric(result["cms_stars"], errors="coerce")
            result = result[stars >= 4]
        elif metric == "Level III NICU":
            result = result[result["nicu_level"].astype(str).str.contains("Level III", na=False)]
        elif metric == "Teaching / Academic Center":
            result = result[result["teaching_hospital"] == True]  # noqa: E712

    for svc in filters.get("services") or []:
        result = result[result["services"].apply(lambda s: svc in (s if isinstance(s, list) else []))]

    pmin = filters.get("price_min", 0)
    pmax = filters.get("price_max", 999999)
    result = result[
        result["vaginal_cost"].isna()
        | ((result["vaginal_cost"] >= pmin) & (result["vaginal_cost"] <= pmax))
    ]

    ins = filters.get("insurance") or []
    if ins:
        result = result[
            result["insurance_accepted"].apply(
                lambda accepted: any(i in (accepted if isinstance(accepted, list) else []) for i in ins)
            )
        ]

    min_births = filters.get("min_births_per_year", 0)
    if min_births:
        result = result[result["births_per_year"] >= min_births]

    min_years = filters.get("min_years_operation", 0)
    if min_years:
        result = result[result["years_in_operation"] >= min_years]

    return result.reset_index(drop=True)


def refresh_facilities_from_cms() -> pd.DataFrame:
    """
    Pull Georgia hospitals from CMS, filter to Metro Atlanta, write facilities.csv.

    Future MRF integration:
    -----------------------
    1. Download hospital MRF JSON/CSV from CMS price transparency pages.
    2. Parse billing codes for DRG 765 (vaginal delivery) and DRG 766 (C-section).
    3. Extract negotiated rates by payer; compute facility median cash/self-pay estimate.
    4. Build vaginal_cost_display / csection_cost_display range strings from rate distributions.
    5. Merge with CMS maternal health measures when scores are published for GA hospitals.
    """
    from cms_fetch import build_metro_facility_dataset

    df = build_metro_facility_dataset(statewide=True)
    df = enrich_facilities(df)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    export_df = df.copy()
    if "priorities" in export_df.columns:
        export_df["priorities"] = export_df["priorities"].apply(
            lambda x: "|".join(x) if isinstance(x, list) else (x or "")
        )
    for col in ("services", "insurance_accepted"):
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(
                lambda x: "|".join(x) if isinstance(x, list) else (x or "")
            )
    export_df.to_csv(FACILITIES_CSV, index=False)
    return _postprocess_facility_df(df)


def load_facilities() -> pd.DataFrame:
    """Load facility data from CSV; refresh from CMS if missing."""
    if FACILITIES_CSV.exists():
        return _postprocess_facility_df(pd.read_csv(FACILITIES_CSV))

    try:
        return refresh_facilities_from_cms()
    except Exception:
        return _postprocess_facility_df(pd.DataFrame(SAMPLE_FACILITIES))


def load_resources() -> pd.DataFrame:
    """Load curated local support resources."""
    return pd.DataFrame(LOCAL_RESOURCES)


def prepare_facility_data(user_zip: str, max_distance: float, priorities: list[str]) -> pd.DataFrame:
    """
    Load, enrich, filter, and score facility data for the app.

    Args:
        user_zip: User's home ZIP code for distance calculation.
        max_distance: Maximum distance in miles (60-mile metro radius default).
        priorities: User-selected priority tags for match scoring.

    Returns:
        Filtered DataFrame sorted by priority match score (descending).
    """
    df = load_facilities()
    df = add_distance_column(df, user_zip)

    if priorities:
        df["match_score"] = df.apply(
            lambda row: compute_priority_score(row, priorities), axis=1
        )
    else:
        df["match_score"] = 50.0

    user_coords = get_zip_coordinates(user_zip)
    if user_coords is not None:
        df = df[df["distance_miles"].isna() | (df["distance_miles"] <= max_distance)]

    return df.sort_values("match_score", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    import sys

    if "--refresh" in sys.argv or not FACILITIES_CSV.exists():
        df = refresh_facilities_from_cms()
        print(f"Refreshed {len(df)} facilities → {FACILITIES_CSV}")
    else:
        df = load_facilities()
        print(f"Loaded {len(df)} facilities from {FACILITIES_CSV}")