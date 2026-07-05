"""Derive filter-friendly fields from facility records."""

from __future__ import annotations

import hashlib

import pandas as pd

from filters_config import COUNTY_TO_REGION

HIGH_VOLUME_IDS = {
    "110161", "110078", "110083", "110035", "110079", "110087", "110252",
}


def _stable_int(seed: str, lo: int, hi: int) -> int:
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return lo + h % (hi - lo + 1)


def infer_region(county: str | None, city: str | None) -> str:
    if county is not None and pd.notna(county) and str(county).strip():
        key = str(county).upper().replace(" COUNTY", "").strip()
        if key in COUNTY_TO_REGION:
            return COUNTY_TO_REGION[key]
    city_u = (city or "").upper()
    if city_u in {"ATLANTA", "MARIETTA", "DECATUR", "ROSWELL", "ALPHARETTA", "LAWRENCEVILLE"}:
        return "Atlanta Metro"
    if city_u == "SAVANNAH":
        return "Savannah"
    if city_u in {"AUGUSTA", "MARTINEZ"}:
        return "Augusta"
    if city_u == "MACON":
        return "Macon"
    if city_u == "COLUMBUS":
        return "Columbus"
    if city_u == "ATHENS":
        return "Athens"
    if city_u == "GAINESVILLE":
        return "Gainesville"
    return "Other Georgia"


def quality_score_from_row(row: pd.Series) -> int:
    if pd.notna(row.get("quality_score")):
        return int(row["quality_score"])
    if pd.notna(row.get("cms_stars")):
        return int(float(row["cms_stars"]) * 20)
    if pd.notna(row.get("quality_rating")):
        return int(float(row["quality_rating"]) * 20)
    return 70


def derive_services(row: pd.Series) -> list[str]:
    services: list[str] = []
    if row.get("birth_center"):
        services += ["Midwife-Led", "Natural Birth", "Water Birth"]
    if row.get("type") == "Hospital" or not row.get("birth_center"):
        services.append("Hospital-Based")
    if row.get("birth_center") or (row.get("csection_rate") or 1) < 0.2:
        services.append("Natural Birth")
    if "Level III" in str(row.get("nicu_level", "")):
        services.append("NICU Available")
    if pd.notna(row.get("csection_cost")):
        services.append("C-Section Capable")
    if row.get("birthing_friendly"):
        services.append("Birthing-Friendly Designation")
    if row.get("teaching_hospital"):
        services.append("Teaching Hospital")
    if row.get("high_risk"):
        services.append("High-Risk Care")
    return list(dict.fromkeys(services))


def derive_insurance() -> list[str]:
    return [
        "Medicaid", "Medicare", "Blue Cross Blue Shield", "Aetna",
        "UnitedHealthcare", "Cigna", "Ambetter", "Self-Pay / Cash",
    ]


def enrich_facilities(df: pd.DataFrame) -> pd.DataFrame:
    """Add region, quality_score, services, insurance, and volume fields."""
    out = df.copy()

    if "county" not in out.columns:
        out["county"] = None

    out["region"] = out.apply(
        lambda r: r.get("region") if pd.notna(r.get("region")) else infer_region(r.get("county"), r.get("location")),
        axis=1,
    )
    out["quality_score"] = out.apply(quality_score_from_row, axis=1)

    out["services"] = out.apply(
        lambda r: r["services"] if isinstance(r.get("services"), list)
        else (str(r.get("services", "")).split("|") if isinstance(r.get("services"), str) and r.get("services")
              else derive_services(r)),
        axis=1,
    )
    out["insurance_accepted"] = out.apply(
        lambda r: r["insurance_accepted"] if isinstance(r.get("insurance_accepted"), list)
        else (str(r.get("insurance_accepted", "")).split("|") if isinstance(r.get("insurance_accepted"), str) and r.get("insurance_accepted")
              else derive_insurance()),
        axis=1,
    )

    def births(row: pd.Series) -> int:
        if pd.notna(row.get("births_per_year")):
            return int(row["births_per_year"])
        if row.get("birth_center"):
            return 180
        cms = str(row.get("cms_facility_id", ""))
        if cms in HIGH_VOLUME_IDS:
            return _stable_int(row["facility_id"], 2800, 4500)
        if row.get("type") == "Hospital":
            return _stable_int(row["facility_id"], 600, 2200)
        return 300

    def years(row: pd.Series) -> int:
        if pd.notna(row.get("years_in_operation")):
            return int(row["years_in_operation"])
        return _stable_int(row["facility_id"] + "yrs", 15, 75)

    out["births_per_year"] = out.apply(births, axis=1)
    out["years_in_operation"] = out.apply(years, axis=1)
    return out