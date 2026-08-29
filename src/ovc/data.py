"""Quatre sources libres : le BXM officiel (Cboe), le VIX (FRED), les indices et FNB (Yahoo).

Licence Cboe (rapporté, cboe.com/terms) : consultation et téléchargement pour usage
personnel non commercial, redistribution interdite : la série brute n'est JAMAIS commitée
ni republiée, seules des statistiques dérivées apparaissent dans le dépôt. Le CSV libre de
BXM commence le 2002-03-22 (mesuré) : l'échantillon de Whaley (1988-2001) n'est pas
recouvrable en données libres, la validation se fait donc sur 2002-2026, déclaré.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw")

BXM_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/BXM_History.csv"
VIX_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
RATE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS1MO"
TICKERS = ["^GSPC", "^SP500TR", "ZWB.TO", "ZEB.TO"]

UA = {"User-Agent": "ovc laboratoire pedagogique (github.com/Guilou001/16-options-couvertes)"}


def fetch() -> None:
    """Télécharge tout (jamais commité)."""
    import yfinance as yf

    RAW.mkdir(parents=True, exist_ok=True)
    for url, name in [(BXM_URL, "bxm.csv"), (VIX_URL, "vix.csv"), (RATE_URL, "dgs1mo.csv")]:
        r = requests.get(url, headers=UA, timeout=120)
        r.raise_for_status()
        (RAW / name).write_bytes(r.content)
    px = yf.download(TICKERS, period="max", auto_adjust=True, progress=False)["Close"]
    px.to_csv(RAW / "prix_yahoo.csv")


def load_bxm() -> pd.Series:
    """Le niveau quotidien du BXM (dates MM/JJ/AAAA dans le CSV Cboe)."""
    df = pd.read_csv(RAW / "bxm.csv")
    s = pd.Series(df["BXM"].to_numpy(), index=pd.to_datetime(df["DATE"], format="%m/%d/%Y"))
    return s.sort_index().rename("bxm")


def _fred(name: str, col: str) -> pd.Series:
    df = pd.read_csv(RAW / name, na_values=["."])
    df.columns = ["date", col]
    return pd.Series(df[col].to_numpy(), index=pd.to_datetime(df["date"]),
                     name=col).dropna().sort_index()


def load_vix() -> pd.Series:
    return _fred("vix.csv", "vix")


def load_rate() -> pd.Series:
    """Le taux 1 mois (CMT, %), pour capitaliser la prime pendant la période."""
    return _fred("dgs1mo.csv", "i_1m")


def load_yahoo() -> pd.DataFrame:
    px = pd.read_csv(RAW / "prix_yahoo.csv", index_col=0, parse_dates=True)
    return px
