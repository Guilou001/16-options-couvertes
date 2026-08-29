"""Le buy-write synthétique : la méthodologie BXM refaite avec Black-Scholes et le VIX.

La méthodologie officielle (Cboe, rapporté) : détenir le S&P 500 (dividendes compris) et
vendre chaque troisième vendredi un call SPX d'un mois, au premier prix d'exercice
AU-DESSUS du niveau de l'indice, tenu jusqu'au règlement. La reconstruction en données
libres remplace le prix de marché du call par Black-Scholes avec le VIX comme volatilité
implicite : l'écart cumulé au BXM officiel CHIFFRE ce que cette approximation ignore, en
tête le skew (le VIX, moyenne de variance sur toutes les monnaies, dépasse la volatilité
implicite du call à la monnaie quand le skew est pentu : la prime synthétique est trop
riche, le synthétique doit battre l'officiel). Conventions déclarées : roulement au cours
de CLÔTURE du vendredi d'échéance (le règlement officiel est le SOQ du matin), prix
d'exercice arrondi au multiple de 5 supérieur, prime placée au taux 1 mois.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


def bs_call(s: float, k: float, r: float, sigma: float, t: float, q: float = 0.0) -> float:
    """Black-Scholes avec rendement en dividendes q : le call vendu porte sur l'indice PRIX,
    qui croît de r - q sous la mesure risque-neutre (l'omettre surprix le call, mesuré :
    environ 8 pb de l'indice par mois au rendement moyen de 1,9 %)."""
    if t <= 0 or sigma <= 0:
        return max(s * np.exp(-q * t) - k, 0.0)
    d1 = (np.log(s / k) + (r - q + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    return float(s * np.exp(-q * t) * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2))


def third_fridays(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Les troisièmes vendredis de chaque mois entre start et end."""
    out = []
    for month_start in pd.date_range(start.normalize().replace(day=1), end, freq="MS"):
        fridays = pd.date_range(month_start, month_start + pd.offsets.MonthEnd(0), freq="W-FRI")
        out.append(fridays[2])
    idx = pd.DatetimeIndex(out)
    return idx[(idx >= start) & (idx <= end)]


def next_strike(s: float, step: float = 5.0) -> float:
    """Le premier prix d'exercice strictement au-dessus du niveau (grille de 5 points)."""
    k = np.ceil(s / step) * step
    return float(k + step) if k == s else float(k)


def synthetic_buywrite(gspc: pd.Series, sp500tr: pd.Series, vix: pd.Series,
                       rate_pct: pd.Series) -> pd.DataFrame:
    """Les rendements de période (échéance à échéance) du buy-write synthétique.

    À chaque troisième vendredi t : prime = BS(S_t, K, r, VIX_t/100, tau) ; à l'échéance
    suivante u : rendement = [jambe longue en rendement TOTAL - règlement du call +
    prime capitalisée] / S_t - 1, la base étant la jambe longue seule (prime en compte
    espèces, convention déclarée).
    """
    common = gspc.dropna().index.intersection(sp500tr.dropna().index)
    fridays = third_fridays(common.min(), common.max())
    # chaque échéance est ramenée au dernier jour de Bourse <= vendredi (jours fériés)
    dates = [common[common.searchsorted(f, side="right") - 1] for f in fridays]
    dates = pd.DatetimeIndex(sorted(set(dates)))
    rows = []
    for t, u in zip(dates[:-1], dates[1:], strict=False):
        s_t = float(gspc.loc[t])
        k = next_strike(s_t)
        tau = (u - t).days / 365.0
        r = float(rate_pct.reindex([t], method="ffill").iloc[0] or 0.0) / 100.0
        sigma = float(vix.reindex([t], method="ffill").iloc[0]) / 100.0
        # rendement en dividendes observable ex ante : l'écart TR moins prix des 252 séances passées
        pos = common.searchsorted(t)
        if pos >= 252:
            t0 = common[pos - 252]
            q = float(sp500tr.loc[t] / sp500tr.loc[t0]) / float(gspc.loc[t] / gspc.loc[t0]) - 1.0
            q = max(q, 0.0)
        else:
            q = 0.0
        prime = bs_call(s_t, k, r, sigma, tau, q)
        s_u = float(gspc.loc[u])
        reglement = max(s_u - k, 0.0)
        jambe_longue = s_t * float(sp500tr.loc[u] / sp500tr.loc[t])
        r_bw = (jambe_longue - reglement + prime * (1.0 + r * tau)) / s_t - 1.0
        r_indice = float(sp500tr.loc[u] / sp500tr.loc[t]) - 1.0
        rows.append({"debut": t, "fin": u, "strike": k, "vix": sigma * 100,
                     "prime_pct": prime / s_t * 100, "r_synthetique": r_bw,
                     "r_indice_tr": r_indice, "exerce": reglement > 0})
    return pd.DataFrame(rows).set_index("fin")


def period_returns(level: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    """Les rendements d'une série de niveaux entre dates consécutives (échéance à échéance)."""
    lv = level.reindex(dates, method="ffill")
    return lv.pct_change().dropna()


def annualized_gap(r_a: pd.Series, r_b: pd.Series) -> dict[str, float]:
    """Écart annualisé, erreur de réplication et corrélation entre deux séries de périodes."""
    common = r_a.dropna().index.intersection(r_b.dropna().index)
    a, b = r_a.loc[common], r_b.loc[common]
    n = len(common)
    per_year = 12.0
    cum_a = float((1 + a).prod() ** (per_year / n))
    cum_b = float((1 + b).prod() ** (per_year / n))
    return {"ecart_annualise_pb": (cum_a - cum_b) * 1e4,
            "erreur_reproduction_pb": float((a - b).std(ddof=1) * np.sqrt(per_year) * 1e4),
            "correlation": float(a.corr(b)), "n_periodes": float(n)}


def variance_premium(vix: pd.Series, gspc: pd.Series) -> pd.DataFrame:
    """La prime de variance à la Carr-Wu : variance implicite (VIX au carré) contre réalisée.

    Chaque fin de mois : implicite = (VIX/100)^2 x 30/365 ; réalisée = somme des carrés des
    rendements log quotidiens des 21 séances suivantes. La prime, implicite moins réalisée,
    est ce que l'acheteur d'assurance paie en moyenne.
    """
    logret = np.log(gspc / gspc.shift(1)).dropna()
    month_ends = gspc.resample("ME").last().index
    rows = []
    for me in month_ends:
        pos = logret.index.searchsorted(me, side="right")
        fenetre = logret.iloc[pos: pos + 21]
        if len(fenetre) < 21:
            continue
        v = vix.reindex([me], method="ffill").iloc[0]
        if not np.isfinite(v):
            continue
        implicite = (v / 100.0) ** 2 * 30.0 / 365.0
        realisee = float((fenetre**2).sum())
        rows.append({"mois": me, "implicite": implicite, "realisee": realisee,
                     "prime": implicite - realisee})
    return pd.DataFrame(rows).set_index("mois")


def nw_tstat(x: np.ndarray, lags: int = 6) -> float:
    """Le t de Student de la moyenne, variance Newey-West (fenêtre de Bartlett)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    xm = x - x.mean()
    var = float((xm**2).mean())
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1.0)
        var += 2.0 * w * float((xm[lag:] * xm[:-lag]).mean())
    return float(x.mean() / np.sqrt(var / n))
