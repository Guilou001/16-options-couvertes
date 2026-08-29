"""Les identités du buy-write : calendrier, plafond au prix d'exercice, prime, variance."""

import numpy as np
import pandas as pd
import pytest

from ovc.buywrite import (
    annualized_gap,
    bs_call,
    next_strike,
    nw_tstat,
    synthetic_buywrite,
    third_fridays,
    variance_premium,
)


def test_third_fridays_hand_cases():
    tf = third_fridays(pd.Timestamp("2021-10-01"), pd.Timestamp("2026-03-01"))
    assert pd.Timestamp("2021-10-15") in tf      # le 1er octobre 2021 était un vendredi
    assert pd.Timestamp("2024-06-21") in tf
    assert pd.Timestamp("2026-02-20") in tf


def test_next_strike_strictly_above():
    assert next_strike(5001.2) == 5005.0
    assert next_strike(4999.9) == 5000.0
    assert next_strike(5000.0) == 5005.0         # strictement au-dessus du niveau


def test_bs_call_hand_value_via_parity():
    # P(40, 40, 6 %, 0,2, 1 an) = 2,066 (tableau 1 de LS) ; C = P + S - K e^(-rT)
    attendu = 2.066 + 40.0 - 40.0 * np.exp(-0.06)
    assert bs_call(40.0, 40.0, 0.06, 0.2, 1.0) == pytest.approx(attendu, abs=2e-3)


def _serie_plate(niveau: float, jours: int = 400) -> pd.Series:
    idx = pd.bdate_range("2020-01-01", periods=jours)
    return pd.Series(niveau, index=idx)


def test_synthetic_flat_market_returns_the_premium():
    # marché immobile, taux nul : chaque période rend exactement la prime (call jamais exercé)
    gspc = _serie_plate(1000.0)
    tr = _serie_plate(500.0)
    vix = _serie_plate(20.0)
    rate = _serie_plate(0.0)
    syn = synthetic_buywrite(gspc, tr, vix, rate)
    assert (~syn["exerce"]).all()
    attendu = syn["prime_pct"] / 100.0
    assert np.allclose(syn["r_synthetique"], attendu, atol=1e-12)


def test_synthetic_capped_at_strike_in_a_rally():
    # l'indice saute de 20 % sans dividende : le gain est plafonné à (K + prime)/S - 1
    idx = pd.bdate_range("2020-01-01", periods=90)
    gspc = pd.Series(1000.0, index=idx)
    gspc.iloc[40:] = 1200.0
    tr = gspc.copy()                             # rendement total = rendement prix (déclaré)
    vix = pd.Series(20.0, index=idx)
    rate = pd.Series(0.0, index=idx)
    syn = synthetic_buywrite(gspc, tr, vix, rate)
    saut = syn[syn["exerce"]]
    assert len(saut) >= 1
    row = saut.iloc[0]
    attendu = (row["strike"] + row["prime_pct"] / 100.0 * 1000.0) / 1000.0 - 1.0
    assert row["r_synthetique"] == pytest.approx(attendu, abs=1e-12)


def test_variance_premium_zero_when_implied_matches_realized():
    # rendement quotidien constant r : variance réalisée = 21 r² ; VIX calé dessus -> prime nulle
    idx = pd.bdate_range("2019-01-01", periods=700)
    r = 0.01
    gspc = pd.Series(100.0 * np.exp(np.arange(700) * r), index=idx)
    var_mensuelle = 21 * r**2
    vix_niveau = np.sqrt(var_mensuelle * 365.0 / 30.0) * 100.0
    vix = pd.Series(vix_niveau, index=idx)
    vrp = variance_premium(vix, gspc)
    assert len(vrp) > 10
    assert np.allclose(vrp["prime"], 0.0, atol=1e-12)


def test_nw_tstat_detects_positive_mean():
    rng = np.random.default_rng(0)
    x = rng.normal(0.5, 1.0, 400)
    assert nw_tstat(x) > 5
    assert abs(nw_tstat(rng.normal(0.0, 1.0, 400))) < 3


def test_annualized_gap_zero_on_identical_series():
    idx = pd.date_range("2020-01-31", periods=36, freq="ME")
    r = pd.Series(np.full(36, 0.01), index=idx)
    g = annualized_gap(r, r.copy())
    assert g["ecart_annualise_pb"] == pytest.approx(0.0, abs=1e-9)
    assert g["erreur_reproduction_pb"] == pytest.approx(0.0, abs=1e-9)
