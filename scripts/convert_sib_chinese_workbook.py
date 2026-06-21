from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

MISSING = {"", "-", "—", "–", "NA", "N/A", "nan", "None", "null"}


def is_missing(v) -> bool:
    if pd.isna(v):
        return True
    return str(v).strip() in MISSING


def clean_str(v) -> str:
    return "" if is_missing(v) else str(v).strip()


def parse_number(v, avg_range: bool = True):
    if is_missing(v):
        return pd.NA
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    s = s.replace("％", "%").replace("，", ",").replace("（", "(").replace("）", ")")
    s = s.replace("约", "").replace("~", "-").replace("–", "-").replace("—", "-")
    range_match = re.match(r"^\s*([<>≤≥]?)\s*(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)", s)
    if range_match and avg_range:
        return (float(range_match.group(2)) + float(range_match.group(3))) / 2
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else pd.NA


def yn(v) -> str:
    s = clean_str(v).lower()
    if s in {"y", "yes", "是", "true", "1"}:
        return "yes"
    if s in {"n", "no", "否", "false", "0"}:
        return "no"
    return ""


def paper_id_from_custom(custom: str) -> str:
    s = clean_str(custom)
    prefix = s.split("-")[0] if "-" in s else s
    digits = re.sub(r"\D", "", prefix)
    return f"SIB_P{int(digits):03d}" if digits else "SIB_PUNK"


def standardize_device(v) -> str:
    s = clean_str(v)
    if "Half" in s or "半" in s:
        return "half_cell"
    if "Full" in s or "全" in s:
        return "full_cell"
    return s


def standardize_electrolyte(v) -> str:
    s = clean_str(v)
    if "碳酸" in s or "carbonate" in s.lower():
        return "carbonate"
    if "醚" in s or "ether" in s.lower():
        return "ether"
    return s


def derive_quality_and_check(rec: dict, row: pd.Series) -> tuple[str, str, str]:
    notes = " | ".join([
        clean_str(row.get("口径说明 / 异常说明")),
        clean_str(row.get("P0????")),
    ])
    main = clean_str(row.get("主分析纳入？（建议碳酸酯 = Y；醚系多为 N）")).upper()
    source = clean_str(row.get("表 / 图编号（如 Fig.3a, Table S2）"))
    doi = clean_str(row.get("DOI（建议必填）"))
    reasons: list[str] = []
    lower_notes = notes.lower()
    if "p0" in lower_notes or "removed" in lower_notes or "excluded" in lower_notes:
        reasons.append("P0/exclusion note present")
    if main == "N":
        reasons.append("not in main carbonate-biomass analysis subset")
    if any(kw in lower_notes for kw in ["估算", "读取", "约", "approx", "estimated"]):
        reasons.append("figure-estimated or approximate value")
    if not doi or not source:
        reasons.append("incomplete provenance")
    if pd.isna(rec.get("ice_percent")):
        reasons.append("missing ICE target")
    if pd.isna(rec.get("current_density_mag")):
        reasons.append("missing/ambiguous current density")
    if pd.isna(rec.get("mass_loading_mg_cm2")):
        reasons.append("missing/ambiguous mass loading")
    prec = str(rec.get("precursor", ""))
    if any(k.lower() in prec.lower() for k in ["pvc", "聚氯乙烯", "pitch", "酚醛"]):
        reasons.append("synthetic/non-biomass precursor component")

    if any("P0" in r or "exclusion" in r or "not in main" in r or "non-biomass" in r for r in reasons):
        tier = "Tier3"
    elif reasons:
        tier = "Tier1" if doi and source and len(reasons) <= 2 and "missing ICE target" not in reasons else "Tier2"
    else:
        tier = "Tier1"
    return tier, ("yes" if reasons else "no"), "; ".join(reasons)


def convert(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for i, row in df.iterrows():
        voltage_low = parse_number(row.get("截止电压下限 (V)"))
        voltage_high = parse_number(row.get("截止电压上限 (V)"))
        voltage_window = ""
        if not pd.isna(voltage_low) and not pd.isna(voltage_high):
            voltage_window = f"{float(voltage_low):g}-{float(voltage_high):g} V"
        rec = {
            "sample_id": f"SIB_{i+1:03d}",
            "original_sample_id": clean_str(row.get("自定义编号")),
            "paper_id": paper_id_from_custom(row.get("自定义编号")),
            "year": parse_number(row.get("发表年份（YYYY）")),
            "doi": clean_str(row.get("DOI（建议必填）")),
            "source_location": clean_str(row.get("表 / 图编号（如 Fig.3a, Table S2）")),
            "material_system": "biomass_derived_hard_carbon",
            "device_system": standardize_device(row.get("Half-cell / Full-cell（下拉）")),
            "sample_name": clean_str(row.get("论文中样品名 / 编号")),
            "precursor": clean_str(row.get("生物质来源（自由文本）")),
            "pretreatment": clean_str(row.get("预处理（下拉）")),
            "activation_method": clean_str(row.get("活化方式（下拉；硬碳常为 None）")),
            "carbonization_temperature_c": parse_number(row.get("碳化 / 热解温度 (°C)")),
            "bet_m2_g": parse_number(row.get("BET 比表面积 (m²/g)")),
            "total_pore_volume_cm3_g": parse_number(row.get("总孔容 (cm³/g)")),
            "micropore_volume_cm3_g": parse_number(row.get("微孔孔容 (cm³/g)")),
            "d002_nm": parse_number(row.get("XRD 层间距 d002 (nm)")),
            "id_ig": parse_number(row.get("Raman ID/IG")),
            "n_at_percent": parse_number(row.get("XPS N 原子 % (at%)")),
            "o_at_percent": parse_number(row.get("XPS O 原子 % (at%)")),
            "mass_loading_mg_cm2": parse_number(row.get("载量 (mg/cm²)")),
            "electrolyte": standardize_electrolyte(row.get("电解液大类（下拉）")),
            "main_analysis_included": yn(row.get("主分析纳入？（建议碳酸酯 = Y；醚系多为 N）")),
            "sodium_salt": clean_str(row.get("钠盐（如 NaPF6）")),
            "salt_concentration_m": parse_number(row.get("钠盐浓度 (M)")),
            "solvent": clean_str(row.get("溶剂细节（EC/PC/DEC/DME…）")),
            "additive": clean_str(row.get("添加剂（FEC/VC 等）")),
            "separator": clean_str(row.get("隔膜（下拉）")),
            "voltage_window": voltage_window,
            "current_basis": clean_str(row.get("电流 / 倍率口径（下拉）")),
            "current_density_mag": parse_number(row.get("电流 / 倍率数值（与口径对应）")),
            "rate_test_reported": yn(row.get("是否提供倍率测试（Y/N）")),
            "first_charge_capacity_mah_g": parse_number(row.get("首圈充电容量 (mAh/g)")),
            "first_discharge_capacity_mah_g": parse_number(row.get("首圈放电容量 (mAh/g)")),
            "ice_percent": parse_number(row.get("首圈库仑效率 (%)")),
            "reversible_capacity_mah_g": parse_number(row.get("第 N 圈可逆容量 (mAh/g)")),
            "capacity_retention_percent": parse_number(row.get("容量保持率 (%)（需注明基准圈）")),
            "low_voltage_plateau_capacity_mah_g": parse_number(row.get("低电位平台容量 (mAh/g)")),
            "slope_capacity_mah_g": parse_number(row.get("斜坡容量 (mAh/g)")),
            "plateau_fraction_percent": parse_number(row.get("平台占比 (%)")),
            "data_source_type": clean_str(row.get("数据来源（下拉）")),
            "extraction_note": clean_str(row.get("口径说明 / 异常说明")),
            "p0_note": clean_str(row.get("P0????")),
            "public_release_status": "DO_NOT_UPLOAD_BEFORE_MANUSCRIPT_FREEZE",
        }
        tier, manual, reason = derive_quality_and_check(rec, row)
        rec["quality_tier"] = tier
        rec["needs_manual_check"] = manual
        rec["check_reason"] = reason
        out.append(rec)
    return pd.DataFrame(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert the user's Chinese-header SIB workbook into the normalized carbon-literature BO schema.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--sheet", default="Sheet1")
    parser.add_argument("--output", required=True)
    parser.add_argument("--main-only", action="store_true", help="Keep only rows marked as main_analysis_included == yes")
    args = parser.parse_args()
    df = pd.read_excel(args.input, sheet_name=args.sheet)
    converted = convert(df)
    if args.main_only:
        converted = converted[converted["main_analysis_included"] == "yes"].copy()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    converted.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"Converted {len(converted)} rows -> {args.output}")


if __name__ == "__main__":
    main()
