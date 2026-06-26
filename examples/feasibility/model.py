"""Heavy/Medium-duty truck supercharging station feasibility analysis — shared financial model.

Pure functions, no Shiny dependency; imported by both feasibility.qmd (Shiny Express) and
feasibility-static.qmd (Typst static rendering).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# ---------- Font / Plotting Globals ----------
mpl.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Microsoft YaHei", "SimHei"]
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 110

BASE_SHAPE = [0.55, 0.65, 0.75, 0.85, 0.95, 1.0]

# ---------- Default Parameters ----------
DEFAULTS: dict = {
    "site_name": "Dongguan Changping · Railway Station Heavy-Duty Truck Supercharging Hub",
    "location": "Changping Town, Dongguan City, Guangdong Province · ~300 m east of Changping Railway Station",
    "site_area_m2": 5700,
    "n_heavy": 12,
    "power_heavy": 480,
    "daily_sessions_heavy": 6,
    "kwh_per_session_heavy": 280,
    "capex_heavy_per_charger": 350000,
    "n_medium": 15,
    "power_medium": 150,
    "daily_sessions_medium": 8,
    "kwh_per_session_medium": 100,
    "capex_medium_per_charger": 80000,
    "demand_ramp": BASE_SHAPE[:],
    "service_fee": 0.45,
    "electricity_sell": 0.72,
    "electricity_purchase": 0.65,
    "capex_civil_kw": 900,
    "land_rent_year": 1200000,
    "staff_cost_year": 720000,
    "other_opex_year": 240000,
    "maintenance_rate": 0.03,
    "discount_rate": 0.08,
    "residual_rate": 0.10,
    "years": 10,
    "berth_area": 90,
}


def compute(params: dict | None = None) -> dict:
    """Takes a parameters dict and returns a complete calculation result.

    Parameters
    ----------
    params : dict, optional
        Parameter override dictionary. Unspecified keys fall back to DEFAULTS.

    Returns
    -------
    dict
        Dictionary containing all intermediate calculations, financial metrics,
        and auxiliary data.
    """
    p = {**DEFAULTS, **(params or {})}

    N = int(p["years"])
    ramp = list(p["demand_ramp"])
    if len(ramp) < N:
        ramp = ramp + [ramp[-1]] * (N - len(ramp))
    ramp = ramp[:N]

    # ---- Energy ----
    base_heavy = p["n_heavy"] * p["daily_sessions_heavy"] * p["kwh_per_session_heavy"] * 365
    base_medium = p["n_medium"] * p["daily_sessions_medium"] * p["kwh_per_session_medium"] * 365
    kwh_h = [base_heavy * r for r in ramp]
    kwh_m = [base_medium * r for r in ramp]
    kwh_t = [a + b for a, b in zip(kwh_h, kwh_m)]

    # ---- Revenue & Cost ----
    margin = p["service_fee"] + p["electricity_sell"] - p["electricity_purchase"]
    rev_service = [k * p["service_fee"] for k in kwh_t]
    rev_energy = [k * p["electricity_sell"] for k in kwh_t]
    rev_total = [a + b for a, b in zip(rev_service, rev_energy)]
    cost_power = [k * p["electricity_purchase"] for k in kwh_t]

    # ---- CAPEX ----
    connected_kw = p["n_heavy"] * p["power_heavy"] + p["n_medium"] * p["power_medium"]
    capex_equip_heavy = p["n_heavy"] * p["capex_heavy_per_charger"]
    capex_equip_medium = p["n_medium"] * p["capex_medium_per_charger"]
    capex_equip = capex_equip_heavy + capex_equip_medium
    capex_civil = connected_kw * p["capex_civil_kw"]
    capex = capex_equip + capex_civil

    # ---- OPEX ----
    maintenance = capex * p["maintenance_rate"]
    fixed_opex = p["land_rent_year"] + p["staff_cost_year"] + p["other_opex_year"] + maintenance
    opex = [fixed_opex] * N

    # ---- EBITDA & Pre-tax Profit ----
    ebitda = [r - c - o for r, c, o in zip(rev_total, cost_power, opex)]
    dep = capex / N
    profit = [e - dep for e in ebitda]

    # ---- Cash Flow & Financial Metrics ----
    flows = [-capex] + list(ebitda)
    flows[-1] += capex * p["residual_rate"]

    def _npv_at(r: float) -> float:
        return sum(f / (1 + r) ** t for t, f in enumerate(flows))

    npv = _npv_at(p["discount_rate"])

    # IRR bisection method
    lo, hi = -0.99, 5.0
    for _ in range(300):
        mid = (lo + hi) / 2
        if _npv_at(mid) > 0:
            lo = mid
        else:
            hi = mid
    irr = (lo + hi) / 2

    # Static payback period
    cum_cf = np.cumsum(flows)
    payback = None
    for t in range(1, len(cum_cf)):
        if cum_cf[t] >= 0 and cum_cf[t - 1] < 0:
            payback = (t - 1) + (-cum_cf[t - 1]) / (cum_cf[t] - cum_cf[t - 1])
            break

    # Site area
    berth_total_area = (p["n_heavy"] + p["n_medium"]) * p["berth_area"]

    verdict = "Financially viable" if (npv > 0 and irr > p["discount_rate"] and payback and payback < N) else "Financially infeasible"

    return {
        # Passthrough parameters (required by converter)
        "site_name": p["site_name"],
        "location": p["location"],
        "site_area_m2": p["site_area_m2"],
        "n_heavy": p["n_heavy"],
        "power_heavy": p["power_heavy"],
        "daily_sessions_heavy": p["daily_sessions_heavy"],
        "kwh_per_session_heavy": p["kwh_per_session_heavy"],
        "capex_heavy_per_charger": p["capex_heavy_per_charger"],
        "n_medium": p["n_medium"],
        "power_medium": p["power_medium"],
        "daily_sessions_medium": p["daily_sessions_medium"],
        "kwh_per_session_medium": p["kwh_per_session_medium"],
        "capex_medium_per_charger": p["capex_medium_per_charger"],
        "demand_ramp": ramp,
        "service_fee": p["service_fee"],
        "electricity_sell": p["electricity_sell"],
        "electricity_purchase": p["electricity_purchase"],
        "capex_civil_kw": p["capex_civil_kw"],
        "land_rent_year": p["land_rent_year"],
        "staff_cost_year": p["staff_cost_year"],
        "other_opex_year": p["other_opex_year"],
        "maintenance_rate": p["maintenance_rate"],
        "discount_rate": p["discount_rate"],
        "residual_rate": p["residual_rate"],
        "years": N,
        "berth_area": p["berth_area"],
        # Computed values
        "ramp": ramp,
        "base_heavy": base_heavy,
        "base_medium": base_medium,
        "kwh_h": kwh_h,
        "kwh_m": kwh_m,
        "kwh_t": kwh_t,
        "margin": margin,
        "rev_service": rev_service,
        "rev_energy": rev_energy,
        "rev_total": rev_total,
        "cost_power": cost_power,
        "connected_kw": connected_kw,
        "capex_equip_heavy": capex_equip_heavy,
        "capex_equip_medium": capex_equip_medium,
        "capex_equip": capex_equip,
        "capex_civil": capex_civil,
        "capex": capex,
        "maintenance": maintenance,
        "fixed_opex": fixed_opex,
        "opex": opex,
        "ebitda": ebitda,
        "dep": dep,
        "profit": profit,
        "flows": flows,
        "npv": npv,
        "irr": irr,
        "payback": payback,
        "verdict": verdict,
        "mature_kwh": kwh_t[-1] if kwh_t else 0,
        "berth_total_area": berth_total_area,
        # Auxiliary
        "base_kwh_combined": base_heavy + base_medium,
    }


# ═══════════════════════════════════════════════════════════
# Chart Functions
# ═══════════════════════════════════════════════════════════

def plot_revenue(m: dict) -> plt.Figure:
    """Annual energy (heavy/medium truck stacked bars) with EBITDA line."""
    N = m["years"]
    x = np.arange(1, N + 1)
    fig, ax1 = plt.subplots(figsize=(6.8, 3.2))
    ax1.bar(x, [k / 1e4 for k in m["kwh_h"]], label="Heavy-duty (10k kWh)", color="#4C78A8")
    ax1.bar(
        x, [k / 1e4 for k in m["kwh_m"]],
        bottom=[k / 1e4 for k in m["kwh_h"]],
        label="Medium-duty (10k kWh)", color="#F58518",
    )
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Energy (10k kWh)")
    ax2 = ax1.twinx()
    ax2.plot(x, [e / 1e4 for e in m["ebitda"]], "o-", color="#54A24B", label="EBITDA")
    ax2.set_ylabel("EBITDA (10k CNY)")
    l1, la1 = ax1.get_legend_handles_labels()
    l2, la2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, la1 + la2, fontsize=8, loc="upper left", ncol=3)
    ax1.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_cashflow(m: dict) -> plt.Figure:
    """Cumulative discounted cash flow and payback period."""
    N = m["years"]
    dr = m["discount_rate"]
    disc = [f / (1 + dr) ** t for t, f in enumerate(m["flows"])]
    cum = np.cumsum(disc)
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    ax.plot(np.arange(0, N + 1), cum, "o-", color="#4C78A8", label="Cumulative discounted CF")
    ax.axhline(0, color="gray", lw=0.8)
    if m["payback"]:
        ax.axvline(m["payback"], color="#E45756", ls="--", lw=1,
                   label=f"Payback ≈ {m['payback']:.1f} yr")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative discounted CF (CNY)")
    ax.set_xticks(np.arange(0, N + 1))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    return fig


def plot_sensitivity(m: dict) -> plt.Figure:
    """NPV sensitivity heatmap (demand achievement rate × service fee)."""
    N = m["years"]
    capex = m["capex"]
    fixed = m["fixed_opex"]
    sell = m["electricity_sell"]
    pur = m["electricity_purchase"]
    dr = m["discount_rate"]
    resid = m["residual_rate"]
    base_kwh = m["base_kwh_combined"]

    dm = np.linspace(0.6, 1.2, 7)
    sfs = np.linspace(0.25, 0.65, 9)
    M = np.zeros((len(dm), len(sfs)))
    for i, d in enumerate(dm):
        for j, sf in enumerate(sfs):
            k = base_kwh * d
            eb = k * (sf + sell - pur) - fixed
            fl = [-capex] + [eb] * N
            fl[-1] += capex * resid
            M[i, j] = sum(f / (1 + dr) ** t for t, f in enumerate(fl))

    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    im = ax.imshow(M, aspect="auto", cmap="RdYlGn",
                   extent=[sfs[0], sfs[-1], dm[0], dm[-1]], origin="lower")
    ax.set_xlabel("Service fee (CNY/kWh)")
    ax.set_ylabel("Demand achievement rate")
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("NPV (CNY)")
    ax.set_title("NPV sensitivity (demand achievement × service fee)", fontsize=10)
    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════
# Metrics / Tables
# ═══════════════════════════════════════════════════════════

def capex_table(m: dict) -> pd.DataFrame:
    """CAPEX breakdown table."""
    total = m["capex"]
    rows = {
        "Item": [
            "Heavy-duty superchargers & accessories",
            "Medium-duty fast chargers & accessories",
            "Civil works, grid connection & power expansion",
            "Total CAPEX",
        ],
        "Amount (CNY)": [m["capex_equip_heavy"], m["capex_equip_medium"], m["capex_civil"], total],
        "Share": [
            m["capex_equip_heavy"] / total,
            m["capex_equip_medium"] / total,
            m["capex_civil"] / total,
            1.0,
        ],
    }
    return pd.DataFrame(rows)


def proforma_table(m: dict) -> pd.DataFrame:
    """Annual pro forma operating statement."""
    N = m["years"]
    return pd.DataFrame({
        "Year": np.arange(1, N + 1),
        "Demand ramp": [f"{r*100:.0f}%" for r in m["ramp"]],
        "Heavy (10k kWh)": [k / 1e4 for k in m["kwh_h"]],
        "Medium (10k kWh)": [k / 1e4 for k in m["kwh_m"]],
        "Total (10k kWh)": [k / 1e4 for k in m["kwh_t"]],
        "Revenue (10k CNY)": [v / 1e4 for v in m["rev_total"]],
        "Power cost (10k CNY)": [v / 1e4 for v in m["cost_power"]],
        "Opex (10k CNY)": [v / 1e4 for v in m["opex"]],
        "EBITDA (10k CNY)": [v / 1e4 for v in m["ebitda"]],
        "Pre-tax profit (10k CNY)": [v / 1e4 for v in m["profit"]],
    })


def metrics_table(m: dict) -> pd.DataFrame:
    """Key financial metrics summary."""
    pb = f"{m['payback']:.1f} yr" if m["payback"] else "Not recovered within project life"
    irr_str = f"{m['irr']*100:.1f}%" if m["irr"] < 4.99 else "> 500%"
    return pd.DataFrame({
        "Metric": [
            "Total CAPEX",
            "Mature-year EBITDA",
            "Mature-year total energy",
            "Net Present Value (NPV)",
            "Internal Rate of Return (IRR)",
            "Static payback period",
            "Overall verdict",
        ],
        "Value": [
            f"{m['capex']:,.0f} CNY",
            f"{m['ebitda'][-1]:,.0f} CNY",
            f"{m['mature_kwh']/1e4:,.1f} 10k kWh",
            f"{m['npv']:,.0f} CNY",
            irr_str,
            pb,
            m["verdict"],
        ],
    })
