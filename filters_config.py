"""Filter options and Georgia region mapping for ATL Birth Hub."""

from __future__ import annotations

GEORGIA_REGIONS = [
    "Atlanta Metro",
    "Savannah",
    "Augusta",
    "Macon",
    "Columbus",
    "Athens",
    "Gainesville",
    "Albany",
    "Valdosta",
    "Rome",
    "Other Georgia",
]

SERVICE_OPTIONS = [
    "Water Birth",
    "Midwife-Led",
    "Hospital-Based",
    "Natural Birth",
    "NICU Available",
    "C-Section Capable",
    "Birthing-Friendly Designation",
    "Teaching Hospital",
    "High-Risk Care",
]

INSURANCE_OPTIONS = [
    "Medicaid",
    "Medicare",
    "Blue Cross Blue Shield",
    "Aetna",
    "UnitedHealthcare",
    "Cigna",
    "Ambetter",
    "Self-Pay / Cash",
]

QUALITY_METRIC_OPTIONS = [
    "Birthing-Friendly Hospital",
    "Low C-Section Rate (<28%)",
    "High CMS Star Rating (4+)",
    "Level III NICU",
    "Teaching / Academic Center",
]

QUALITY_SCORE_OPTIONS = {
    "Any score": 0,
    "70+": 70,
    "80+": 80,
    "90+": 90,
}

COUNTY_TO_REGION: dict[str, str] = {
    "FULTON": "Atlanta Metro",
    "DEKALB": "Atlanta Metro",
    "COBB": "Atlanta Metro",
    "GWINNETT": "Atlanta Metro",
    "CLAYTON": "Atlanta Metro",
    "CHEROKEE": "Atlanta Metro",
    "FORSYTH": "Atlanta Metro",
    "HENRY": "Atlanta Metro",
    "DOUGLAS": "Atlanta Metro",
    "FAYETTE": "Atlanta Metro",
    "ROCKDALE": "Atlanta Metro",
    "PAULDING": "Atlanta Metro",
    "COWETA": "Atlanta Metro",
    "BARTOW": "Atlanta Metro",
    "NEWTON": "Atlanta Metro",
    "WALTON": "Atlanta Metro",
    "BARROW": "Atlanta Metro",
    "SPALDING": "Atlanta Metro",
    "HALL": "Gainesville",
    "CHATHAM": "Savannah",
    "BRYAN": "Savannah",
    "EFFINGHAM": "Savannah",
    "RICHMOND": "Augusta",
    "COLUMBIA": "Augusta",
    "BIBB": "Macon",
    "HOUSTON": "Macon",
    "MUSCOGEE": "Columbus",
    "HARRIS": "Columbus",
    "CLARKE": "Athens",
    "DOUGHERTY": "Albany",
    "LOWNDES": "Valdosta",
    "FLOYD": "Rome",
    "LUMPKIN": "Gainesville",
    "DAWSON": "Atlanta Metro",
    "PICKENS": "Atlanta Metro",
}

DEFAULT_FILTERS: dict = {
    "regions": [],
    "distance_mode": "Statewide",
    "max_distance": 60,
    "user_zip": "30341",
    "min_quality_score": 0,
    "quality_metrics": [],
    "services": [],
    "price_min": 4000,
    "price_max": 25000,
    "insurance": [],
    "min_births_per_year": 0,
    "min_years_operation": 0,
    "search_query": "",
}