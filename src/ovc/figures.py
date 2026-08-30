"""Trois figures : le BXM reconstruit, la prime de variance, le duel ZWB contre ZEB."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gvf.style import OKABE_ITO, appliquer, formateur  # noqa: F401

# La palette et les réglages viennent de la couche partagée du portefeuille : les mêmes
# couleurs et la même virgule décimale dans tous les dépôts, corrigées à un seul endroit.


def use_style():
    """Les réglages communs, puis le formateur d'axe en français."""
    appliquer()
    return formateur()


def _croissance(r: pd.Series) -> pd.Series:
    return (1 + r).cumprod() * 100


def fig_bxm(r_bxm: pd.Series, r_syn: pd.Series, r_idx: pd.Series, gap_pb: float,
            base: str, dest: Path) -> None:
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
    # la graduation partait à 100 alors que les courbes descendent sous 76 en 2002 : tout le premier
    # creux, dont le README fait un argument, se lisait sans repère
    ax.set_yticks([75, 100, 200, 400, 800, 1600])
    ax.yaxis.set_major_formatter(fr)
    ax.yaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_ylabel("Croissance de 100 $ US\n(échelle logarithmique)", fontsize=9.5)
    ax.legend(fontsize=8.5, loc="upper left",
              title=f"base 100 au {base}, dividendes réinvestis, avant frais et impôts")
    ax.set_title("Vendre la hausse coûte la hausse : le BXM décroche de l'indice dans chaque grand rebond")
    common = r_syn.dropna().index.intersection(r_bxm.dropna().index)
    diff = (_croissance(r_syn.loc[common]) / _croissance(r_bxm.loc[common]) - 1) * 100
    ax2.plot(diff.index, diff, color=OKABE_ITO[2])
    ax2.axhline(0, color="0.4", linewidth=0.8)
    ax2.set_ylabel("Écart cumulé du synthétique\nà l'officiel (%)", fontsize=9)
    ax2.yaxis.set_major_formatter(fr)
    # la courbe est un rapport de richesses cumulées : son équivalent annualisé se COMPOSE, il ne
    # vaut pas la différence des deux rendements annualisés citée au README (les deux sont donnés)
    annees = (diff.index[-1] - diff.index[0]).days / 365.25
    compose_pb = ((1 + diff.iloc[-1] / 100.0) ** (1 / annees) - 1) * 1e4
    ax2.set_title(f"La courbe finit {diff.iloc[-1]:+.0f} % au-dessus, soit {compose_pb:+.0f} points de "
                  f"base par an composés\n(écart des rendements annualisés : {gap_pb:+.0f} points de "
                  f"base par an) : le prix de l'asymétrie des volatilités implicites",
                  fontsize=9.5)
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
            label=f"volatilité réalisée des 21 séances suivantes, "
                  f"moyenne {vol_rea.mean():.1f} %".replace(".", ","))
    # les deux courbes n'annualisent pas sur la même base de jours : le dire évite de croire qu'un
    # simple croisement suffit à rendre la prime positive
    ax.set_ylabel("Volatilité annualisée (%)\nimplicite sur 365/30, réalisée sur 252/21", fontsize=9.5)
    ax.yaxis.set_major_formatter(fr)
    part = float((vrp["prime"] > 0).mean() * 100)
    ax.legend(fontsize=9,
              title=f"prime en VARIANCE positive {part:.0f} % des mois\n"
                    f"(t de Newey-West sur la prime en variance : {tstat:.1f})".replace(".", ","))
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
                             ("ZWB.TO", "ZWB (mêmes banques, options d'achat vendues)", OKABE_ITO[3])]:
        w = (1 + r[col]).cumprod() * 100
        cagr = (w.iloc[-1] / 100) ** (252 / len(w)) - 1
        vol = r[col].std() * np.sqrt(252)
        ax.plot(w.index, w, color=color,
                label=f"{name} : rendement annualisé {cagr * 100:.1f} %, "
                      f"volatilité annualisée {vol * 100:.1f} %".replace(".", ","))
    # les cours Yahoo sont ajustés : ils sont déjà nets du ratio de frais de gestion, et les
    # distributions de ces FNB mêlent dividendes, primes d'options et remboursement de capital
    ax.set_ylabel(f"Croissance de 100 $ CA placés le {both.index[0].date()}\n"
                  "(distributions réinvesties, net des frais de gestion)", fontsize=9.5)
    ax.yaxis.set_major_formatter(fr)
    ax.legend(fontsize=9, loc="upper left")
    ax.set_title("Le « revenu » des options d'achat vendues n'est pas gratuit : "
                 "il se paie en hausse abandonnée", fontsize=11.5)
    fig.savefig(dest)
    plt.close(fig)
