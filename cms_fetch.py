"""
CMS Hospital Compare data fetcher for Metro Atlanta birthing facilities.

Sources:
  - Hospital General Information (dataset xubh-q36u)
  - Maternal Health / Cesarean Birth PC_02 (dataset nrdb-3fcy) when available
"""

from __future__ import annotations

import json
import math
import re
import urllib.request
from typing import Any, Optional

import pandas as pd
import pgeocode

CMS_HOSPITAL_API = (
    "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0"
)
CMS_MATERNAL_API = (
    "https://data.cms.gov/provider-data/api/1/datastore/query/nrdb-3fcy/0"
)

ATLANTA_CENTER = (33.7490, -84.3880)
METRO_RADIUS_MILES = 60

INCLUDED_HOSPITAL_TYPES = {
    "Acute Care Hospitals",
    "Critical Access Hospitals",
}

EXCLUDED_NAME_PATTERNS = re.compile(
    r"PSYCHIATRIC|BEHAVIORAL|RIDGEWOOD|PEACHFORD|SUMMITRIDGE|VA MEDICAL|"
    r"CHILDREN'?S|SCOTTISH RITE|ANCHOR HOSPITAL",
    re.I,
)

# CMS facility IDs with hand-curated rich profiles (keys match CMS facility_id)
CURATED_BY_CMS_ID: dict[str, dict[str, Any]] = {
    "110161": {
        "facility_id": "northside-atlanta",
        "name": "Northside Hospital Atlanta",
        "location": "Atlanta (Sandy Springs)",
        "vaginal_cost": 11250,
        "csection_cost": 16000,
        "vaginal_cost_display": "$8.5k–$14k",
        "csection_cost_display": "$12k–$20k",
        "csection_rate": 0.275,
        "csection_rate_display": "~25–30%",
        "key_strength": "High volume leader",
        "strengths": "Renowned maternity program; private rooms; strong lactation support; experienced teams for routine births",
        "considerations": "Higher costs than community hospitals; busy environment; parking can be challenging during peak hours",
        "nicu_level": "Level III",
        "high_risk": True,
    },
    "110078": {
        "facility_id": "emory-midtown",
        "name": "Emory University Hospital Midtown",
        "location": "Atlanta (Midtown)",
        "vaginal_cost": 12250,
        "csection_cost": 17750,
        "vaginal_cost_display": "$9k–$15.5k",
        "csection_cost_display": "$13.5k–$22k",
        "csection_rate": 0.28,
        "csection_rate_display": "~28%",
        "key_strength": "High-risk expertise",
        "strengths": "Academic medical center; complex care expertise; strong maternal-fetal medicine; research-backed protocols",
        "considerations": "Premium pricing; urban campus; may feel more clinical for families wanting a cozy birth experience",
        "nicu_level": "Level III",
        "teaching_hospital": True,
        "high_risk": True,
    },
    "110083": {
        "facility_id": "piedmont-atlanta",
        "name": "Piedmont Atlanta Hospital",
        "location": "Atlanta",
        "vaginal_cost": 10500,
        "csection_cost": 15000,
        "vaginal_cost_display": "$7.8k–$13.2k",
        "csection_cost_display": "$11.5k–$18.5k",
        "csection_rate": 0.26,
        "csection_rate_display": "~26%",
        "key_strength": "Balanced comprehensive care",
        "strengths": "Buckhead location; modern birthing suites; strong patient satisfaction; integrated women's health",
        "considerations": "Costs above metro average; limited public transit access; valet parking fees",
        "nicu_level": "Level III",
        "teaching_hospital": True,
    },
    "110035": {
        "facility_id": "wellstar-kennestone",
        "name": "Wellstar Kennestone Hospital",
        "location": "Marietta",
        "vaginal_cost": 11000,
        "csection_cost": 15750,
        "vaginal_cost_display": "$8.2k–$13.8k",
        "csection_cost_display": "$12k–$19.5k",
        "csection_rate": 0.27,
        "csection_rate_display": "~27%",
        "key_strength": "Suburban convenience + options",
        "strengths": "Suburban convenience; family-centered care; spacious campus; more approachable than intown pricing",
        "considerations": "Longer drive from core Atlanta; C-section rate near metro average",
        "nicu_level": "Level III",
    },
    "110079": {
        "facility_id": "grady-memorial",
        "name": "Grady Memorial Hospital",
        "location": "Atlanta",
        "vaginal_cost": 8750,
        "csection_cost": 12750,
        "vaginal_cost_display": "$6.5k–$11k",
        "csection_cost_display": "$9.5k–$16k",
        "csection_rate": 0.32,
        "csection_rate_display": "~32%",
        "quality_label": "Good for complex",
        "key_strength": "Safety net + complex care",
        "strengths": "Safety-net hospital; most affordable hospital option; trauma & high-risk expertise; community-rooted care",
        "considerations": "Busy public hospital; wait times can vary; fewer amenity-focused perks than private hospitals",
        "nicu_level": "Level III",
        "teaching_hospital": True,
        "high_risk": True,
    },
}

BIRTH_CENTERS: list[dict[str, Any]] = [
    {
        "facility_id": "atlanta-birth-center",
        "cms_facility_id": "",
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
        "birthing_friendly": True,
        "key_strength": "Holistic, accredited birth center",
        "strengths": "Midwifery-led care; homelike suites; water birth options; holistic, low-intervention philosophy",
        "considerations": "Not equipped for C-sections on-site; transfers to hospital if complications arise; limited to low-risk pregnancies",
        "priorities": "Holistic / low-intervention|Strong midwifery support|Lower costs",
        "data_source": "curated",
    },
]

LEVEL_III_CMS_IDS = {
    "110161", "110078", "110083", "110035", "110079", "110010", "110076",
    "110082", "110087", "110252", "110005", "110008", "110143", "110198",
    "110230", "110191", "110192", "110215", "110229", "110091", "110018",
    "110030", "110046", "110074", "110226",
}

TEACHING_CMS_IDS = {
    "110010", "110078", "110076", "110079", "110082", "110226", "110230",
}

HIGH_RISK_CMS_IDS = {
    "110010", "110078", "110079", "110161", "110082",
}

_nominatim = pgeocode.Nominatim("us")


def _post_cms(url: str, conditions: list[dict]) -> list[dict]:
    payload = json.dumps({
        "limit": 1000,
        "offset": 0,
        "conditions": conditions,
        "count": True,
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.load(resp)
    return data.get("results", [])


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:60] or "facility"


def format_hospital_name(name: str) -> str:
    formatted = name.strip().title()
    return formatted.replace("'S", "'s").replace(" Of ", " of ")


def parse_cms_rating(raw: Optional[str]) -> tuple[Optional[float], Optional[int]]:
    if not raw or raw in ("Not Available", ""):
        return None, None
    try:
        stars = int(float(raw))
        return float(stars), stars
    except (TypeError, ValueError):
        return None, None


def quality_label_from_stars(stars: Optional[int], high_risk: bool = False) -> str:
    if stars is None:
        return "Not rated"
    if stars >= 4:
        return "Strong"
    if stars == 3:
        return "Good"
    if high_risk:
        return "Good for complex"
    return "Fair"


def estimate_costs(stars: Optional[int], hospital_type: str) -> tuple[int, int, str, str]:
    """Illustrative facility cost midpoints and display ranges by tier."""
    if "Critical Access" in hospital_type:
        low_v, high_v, low_c, high_c = 4500, 8500, 7500, 13000
    elif stars is not None and stars >= 4:
        low_v, high_v, low_c, high_c = 8000, 14500, 11500, 21000
    elif stars is not None and stars <= 2:
        low_v, high_v, low_c, high_c = 5500, 10000, 8500, 15500
    else:
        low_v, high_v, low_c, high_c = 7000, 12000, 10000, 17500

    mid_v = (low_v + high_v) // 2
    mid_c = (low_c + high_c) // 2

    def fmt(lo: int, hi: int) -> str:
        return f"${lo/1000:.1f}k–${hi/1000:.1f}k".replace(".0k", "k")

    return mid_v, mid_c, fmt(low_v, high_v), fmt(low_c, high_c)


def geocode_zip(zip_code: str) -> tuple[Optional[float], Optional[float]]:
    cleaned = str(zip_code).strip()[:5]
    loc = _nominatim.query_postal_code(cleaned)
    if pd.isna(loc.latitude) or pd.isna(loc.longitude):
        return None, None
    return float(loc.latitude), float(loc.longitude)


def fetch_cesarean_rates() -> dict[str, str]:
    """Return {cms_facility_id: score_text} for Cesarean Birth measure."""
    rows = _post_cms(CMS_MATERNAL_API, [
        {"property": "state", "value": "GA", "operator": "="},
        {"property": "measure_id", "value": "PC_02", "operator": "="},
    ])
    return {
        r["facility_id"]: r["score"]
        for r in rows
        if r.get("score") not in (None, "", "Not Available")
    }


def fetch_georgia_hospitals() -> list[dict]:
    return _post_cms(CMS_HOSPITAL_API, [
        {"property": "state", "value": "GA", "operator": "="},
    ])


def normalize_cms_record(
    record: dict,
    cesarean_rates: dict[str, str],
    distance_miles: float,
) -> Optional[dict]:
    cms_id = record["facility_id"]
    name = format_hospital_name(record["facility_name"])
    hospital_type = record.get("hospital_type", "")

    if hospital_type not in INCLUDED_HOSPITAL_TYPES:
        return None
    if EXCLUDED_NAME_PATTERNS.search(record["facility_name"]):
        return None

    zip_code = str(record["zip_code"]).strip()[:5]
    lat, lon = geocode_zip(zip_code)
    if lat is None or lon is None:
        return None

    curated = CURATED_BY_CMS_ID.get(cms_id, {})
    rating, stars = parse_cms_rating(record.get("hospital_overall_rating"))
    high_risk = cms_id in HIGH_RISK_CMS_IDS or curated.get("high_risk", False)
    teaching = cms_id in TEACHING_CMS_IDS or curated.get("teaching_hospital", False)
    nicu = curated.get("nicu_level") or (
        "Level III" if cms_id in LEVEL_III_CMS_IDS else "Level II"
    )

    if not curated:
        mid_v, mid_c, disp_v, disp_c = estimate_costs(stars, hospital_type)
    else:
        mid_v = curated.get("vaginal_cost", 10000)
        mid_c = curated.get("csection_cost", 15000)
        disp_v = curated.get("vaginal_cost_display", "$7k–$12k")
        disp_c = curated.get("csection_cost_display", "$10k–$17k")

    csection_display = curated.get("csection_rate_display")
    csection_rate = curated.get("csection_rate")
    if cms_id in cesarean_rates:
        raw = cesarean_rates[cms_id]
        if "%" in raw:
            csection_display = raw
            try:
                csection_rate = float(raw.replace("%", "").strip()) / 100
            except ValueError:
                pass
    if csection_display is None:
        csection_display = "Contact hospital"
        csection_rate = 0.29

    city = record.get("citytown", "").strip().title()
    address = f"{record.get('address', '').strip().title()}, {city}, GA {zip_code}"
    quality_label = curated.get("quality_label") or quality_label_from_stars(stars, high_risk)

    return {
        "facility_id": curated.get("facility_id", slugify(name)),
        "cms_facility_id": cms_id,
        "name": curated.get("name", name),
        "type": "Hospital",
        "location": city,
        "address": address,
        "zip_code": zip_code,
        "county": record.get("countyparish", "").strip().title(),
        "latitude": lat,
        "longitude": lon,
        "distance_from_atlanta": round(distance_miles, 1),
        "vaginal_cost": mid_v,
        "csection_cost": mid_c,
        "vaginal_cost_display": disp_v,
        "csection_cost_display": disp_c,
        "quality_rating": rating if rating is not None else 3.5,
        "quality_label": quality_label,
        "cms_stars": stars,
        "csection_rate": csection_rate,
        "csection_rate_display": csection_display,
        "nicu_level": nicu,
        "birth_center": False,
        "teaching_hospital": teaching,
        "high_risk": high_risk,
        "birthing_friendly": record.get("meets_criteria_for_birthing_friendly") == "Y",
        "hospital_ownership": record.get("hospital_ownership", ""),
        "key_strength": curated.get(
            "key_strength",
            "Acute care hospital with labor & delivery services",
        ),
        "strengths": curated.get(
            "strengths",
            f"CMS-listed acute care hospital in {city}; offers maternity services. "
            f"Overall CMS rating: {stars or 'not rated'} stars.",
        ),
        "considerations": curated.get(
            "considerations",
            "Cost and experience vary by insurance and care team. Schedule a tour and request a Good Faith Estimate.",
        ),
        "priorities": "",
        "data_source": "curated" if cms_id in CURATED_BY_CMS_ID else "cms",
    }


def build_metro_facility_dataset(statewide: bool = True) -> pd.DataFrame:
    """Fetch CMS GA hospitals; statewide by default, append birth centers."""
    hospitals = fetch_georgia_hospitals()
    cesarean_rates = fetch_cesarean_rates()

    records: list[dict] = []
    for h in hospitals:
        zip_code = str(h["zip_code"]).strip()[:5]
        lat, lon = geocode_zip(zip_code)
        if lat is None:
            continue
        dist = haversine_miles(ATLANTA_CENTER[0], ATLANTA_CENTER[1], lat, lon)
        if not statewide and dist > METRO_RADIUS_MILES:
            continue
        normalized = normalize_cms_record(h, cesarean_rates, dist)
        if normalized:
            records.append(normalized)

    df = pd.DataFrame(records)
    if df.empty:
        return df

    df = df.sort_values("distance_from_atlanta").drop_duplicates(subset=["cms_facility_id"])
    birth_df = pd.DataFrame(BIRTH_CENTERS)
    birth_df["distance_from_atlanta"] = round(haversine_miles(
        ATLANTA_CENTER[0], ATLANTA_CENTER[1],
        float(birth_df.iloc[0]["latitude"]), float(birth_df.iloc[0]["longitude"]),
    ), 1)
    for col in df.columns:
        if col not in birth_df.columns:
            birth_df[col] = None
    birth_df = birth_df[df.columns]
    df = pd.concat([df, birth_df], ignore_index=True)
    return df.sort_values("distance_from_atlanta", na_position="last").reset_index(drop=True)