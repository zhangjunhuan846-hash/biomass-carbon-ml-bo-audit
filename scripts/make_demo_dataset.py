from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def make_demo(n_papers: int = 14, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    precursors = ["rice husk", "lignin", "cellulose", "coconut shell", "pomelo peel", "wood", "corn stalk", "sucrose", "chitosan"]
    electrolytes = ["1 M NaPF6 in EC/DEC", "1 M NaClO4 in EC/PC", "1 M NaPF6 in diglyme", "1 M NaPF6 in EC/DMC"]
    rows = []
    sample_idx = 1
    for p in range(1, n_papers+1):
        n_samples = int(rng.integers(4, 8))
        year = int(rng.integers(2019, 2027))
        paper_shift = rng.normal(0, 4)
        for j in range(n_samples):
            temp = float(rng.choice([900, 1000, 1100, 1200, 1300, 1400, 1500]) + rng.normal(0, 25))
            bet = float(max(5, rng.lognormal(mean=4.2, sigma=0.65)))
            pore = float(max(0.02, bet/1100 + rng.normal(0, 0.05)))
            d002 = float(np.clip(0.335 + rng.normal(0.035, 0.015) - (temp-1100)*0.000015, 0.335, 0.42))
            idig = float(np.clip(1.0 + rng.normal(0.15, 0.18) - (temp-1200)*0.00012, 0.55, 1.7))
            n_at = float(max(0, rng.normal(1.5, 1.0)))
            o_at = float(max(0, rng.normal(6.0, 2.5) - (temp-1000)*0.004))
            current = float(rng.choice([20, 25, 50, 100, 200, 500]))
            mass_loading = float(max(0.4, rng.normal(1.2, 0.35))) if rng.random() > 0.25 else np.nan
            # Synthetic target: plausible but deliberately not factual.
            ice = 64 + 0.018*(temp-1000) - 0.018*bet + 18*(d002-0.36) - 1.1*o_at + 0.8*n_at + paper_shift + rng.normal(0, 4)
            ice = float(np.clip(ice, 25, 92))
            cap = 230 + 0.06*bet + 400*(d002-0.35) + 5*idig - 0.04*current + rng.normal(0, 25)
            cap = float(np.clip(cap, 80, 520))
            quality = rng.choice(["Tier0", "Tier1", "Tier2", "Tier3"], p=[0.35, 0.35, 0.22, 0.08])
            needs_check = "yes" if quality == "Tier3" or rng.random() < 0.08 else "no"
            check_reason = "synthetic suspicious outlier / needs source check" if needs_check == "yes" else ""
            if rng.random() < 0.08:
                bet = np.nan
            if rng.random() < 0.1:
                d002 = np.nan
            if rng.random() < 0.12:
                idig = np.nan
            rows.append({
                "sample_id": f"SYN-SIB-{sample_idx:03d}",
                "paper_id": f"P{p:03d}",
                "year": year,
                "doi": f"synthetic-demo-doi-{p:03d}",
                "source_location": f"Synthetic Table {p}",
                "material_system": "synthetic biomass hard carbon",
                "device_system": "SIB",
                "precursor": rng.choice(precursors),
                "carbonization_temperature_c": round(temp, 1),
                "activation_method": rng.choice(["none", "KOH", "CO2", "steam"], p=[0.55,0.2,0.15,0.1]),
                "bet_m2_g": round(bet, 2) if not np.isnan(bet) else np.nan,
                "total_pore_volume_cm3_g": round(pore, 3),
                "d002_nm": round(d002, 4) if not np.isnan(d002) else np.nan,
                "id_ig": round(idig, 3) if not np.isnan(idig) else np.nan,
                "n_at_percent": round(n_at, 2),
                "o_at_percent": round(o_at, 2),
                "electrolyte": rng.choice(electrolytes),
                "current_density_mag": current,
                "mass_loading_mg_cm2": round(mass_loading, 2) if not np.isnan(mass_loading) else np.nan,
                "voltage_window": "0.01-3.0 V vs Na/Na+",
                "ice_percent": round(ice, 2),
                "reversible_capacity_mah_g": round(cap, 1),
                "specific_capacitance_f_g": np.nan,
                "quality_tier": quality,
                "needs_manual_check": needs_check,
                "check_reason": check_reason,
                "notes": "SYNTHETIC DEMO ROW - not literature data"
            })
            sample_idx += 1
    return pd.DataFrame(rows)


def main() -> None:
    out = Path("examples/sib_hard_carbon_synthetic/synthetic_sib_hard_carbon.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df = make_demo()
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} synthetic rows to {out}")


if __name__ == "__main__":
    main()
