"""Trois figures : le BXM reconstruit, la prime de variance, le duel ZWB contre ZEB."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]


def use_style():
    import matplotlib as mpl
    from cycler import cycler
    from matplotlib.ticker import FuncFormatter

    mpl.rcParams.update({
        "figure.dpi": 200, "savefig.dpi": 200, "figure.constrained_layout.use": True,
        "font.size": 11, "axes.titlesize": 12, "axes.prop_cycle": cycler(color=OKABE_ITO),
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5,
        "legend.frameon": False, "lines.linewidth": 1.7,
    })
    return FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def _croissance(r: pd.Series) -> pd.Series:
    return (1 + r).cumprod() * 100


def fig_bxm(r_bxm: pd.Series, r_syn: pd.Series, r_idx: pd.Series, gap_pb: float,
            dest: Path) -> None:
    """Le BXM officiel, sa reconstruction VIX et l'indice total : qui garde la hausse ?"""
    fr = use_style()
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9.2, 6.2), sharex=True, height_ratios=[2.1, 1])
    for r, name, color, style in [(r_idx, "S&P 500 rendement total", OKABE_ITO[1], "-"),
                                  (r_bxm, "BXM officiel", OKABE_ITO[0], "-"),
                                  (r_syn, "reconstruction Black-Scholes + VIX", OKABE_ITO[3], "--")]:
        w = _croissance(r)
        ax.plot(w.index, w, color=color, linestyle=style,
                label=f"{name} ({w.iloc[-1]:,.0f})".replace(",", " "))
    ax.set_yscale("log")
    ax.set_yticks([100, 200, 400, 800, 1600])
    ax.yaxis.set_major_formatter(fr)
    ax.yaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_ylabel("Valeur de 100 (échelle log)")
    ax.legend(fontsize=8.5, loc="upper left")
    ax.set_title("Vendre la hausse coûte la hausse : le BXM décroche de l'indice dans chaque grand rebond")
    common = r_syn.dropna().index.intersection(r_bxm.dropna().index)
    diff = (_croissance(r_syn.loc[common]) / _croissance(r_bxm.loc[common]) - 1) * 100
    ax2.plot(diff.index, diff, color=OKABE_ITO[2])
    ax2.axhline(0, color="0.4", linewidth=0.8)
    ax2.set_ylabel("Synthétique / officiel - 1 (%)", fontsize=9)
    ax2.yaxis.set_major_formatter(fr)
    ax2.set_title(f"L'écart cumulé ({gap_pb:+.0f} pb/an) est le prix du skew que le VIX ne voit pas",
                  fontsize=10.5)
    fig.savefig(dest)
    plt.close(fig)


def fig_vrp(vrp: pd.DataFrame, tstat: float, dest: Path) -> None:
    """La prime de variance : l'assurance est structurellement payée au-dessus de son coût."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    vol_imp = np.sqrt(vrp["implicite"] * 365.0 / 30.0) * 100
    vol_rea = np.sqrt(vrp["realisee"] * 252.0 / 21.0) * 100
    ax.plot(vrp.index, vol_imp, color=OKABE_ITO[0], linewidth=1.1,
            label=f"volatilité implicite (VIX), moyenne {vol_imp.mean():.1f} %".replace(".", ","))
    ax.plot(vrp.index, vol_rea, color=OKABE_ITO[3], linewidth=1.1,
            label=f"volatilité réalisée ensuite, moyenne {vol_rea.mean():.1f} %".replace(".", ","))
    ax.set_ylabel("Volatilité annualisée (%)")
    ax.yaxis.set_major_formatter(fr)
    part = float((vrp["prime"] > 0).mean() * 100)
    ax.legend(fontsize=9, title=f"prime positive {part:.0f} % des mois ; t de Newey-West {tstat:.1f}".replace(".", ","))
    ax.set_title("L'implicite dépasse la réalisée presque tout le temps : la prime que le vendeur encaisse")
    fig.savefig(dest)
    plt.close(fig)


def fig_zwb(px: pd.DataFrame, dest: Path) -> None:
    """ZWB contre ZEB : le produit à revenu contre son jumeau nu, sur les mêmes banques."""
    fr = use_style()
    both = px[["ZWB.TO", "ZEB.TO"]].dropna()
    r = both.pct_change().dropna()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for col, name, color in [("ZEB.TO", "ZEB (banques, sans options)", OKABE_ITO[0]),
                             ("ZWB.TO", "ZWB (mêmes banques + calls vendus)", OKABE_ITO[3])]:
        w = (1 + r[col]).cumprod() * 100
        cagr = (w.iloc[-1] / 100) ** (252 / len(w)) - 1
        vol = r[col].std() * np.sqrt(252)
        ax.plot(w.index, w, color=color,
                label=f"{name} : {cagr * 100:.1f} %/an, vol {vol * 100:.1f} %".replace(".", ","))
    ax.set_ylabel("Valeur de 100 (dividendes réinvestis)")
    ax.yaxis.set_major_formatter(fr)
    ax.legend(fontsize=9, loc="upper left")
    ax.set_title("Le « revenu » des calls vendus n'est pas gratuit : il se paie en hausse abandonnée")
    fig.savefig(dest)
    plt.close(fig)
