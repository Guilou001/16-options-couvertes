"""Ligne de commande : télécharger, reconstruire le BXM, mesurer la prime de variance, le duel ZWB."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Options d'achat couvertes : reconstruction du BXM (Black-Scholes + VIX), "
                       "prime de risque de variance, ZWB contre ZEB.")


@app.callback()
def main() -> None:
    """Sous-commandes nommées."""


@app.command()
def fetch() -> None:
    """BXM (Cboe), VIX et taux 1 mois (FRED), indices et FNB (Yahoo)."""
    from ovc import data

    data.fetch()
    bxm = data.load_bxm()
    typer.echo(f"BXM : {len(bxm)} jours, {bxm.index[0].date()} -> {bxm.index[-1].date()} ; "
               f"VIX : {len(data.load_vix())} jours")


@app.command()
def lab(out: Path = Path("results")) -> None:
    """Les trois volets : tables et figures."""
    import pandas as pd

    from ovc import buywrite as bw
    from ovc import data, figures

    bxm = data.load_bxm()
    vix = data.load_vix()
    rate = data.load_rate()
    px = data.load_yahoo()
    gspc = px["^GSPC"].dropna()
    tr = px["^SP500TR"].dropna()

    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    # volet 1 : la reconstruction, sur l'échantillon commun BXM (2002-03-22+)
    # le moteur reçoit l'HISTORIQUE COMPLET et non la tranche postérieure au premier BXM : le
    # rendement en dividendes s'estime sur les 252 séances antérieures, et tronquer en amont le
    # forçait silencieusement à zéro sur les douze premières périodes
    debut = bxm.index[0]
    syn = bw.synthetic_buywrite(gspc, tr, vix, rate)
    syn = syn.loc[syn["debut"] >= debut]
    r_syn = syn["r_synthetique"]
    r_bxm = bw.period_returns(bxm, pd.DatetimeIndex([syn["debut"].iloc[0], *syn.index]))
    r_idx = syn["r_indice_tr"]
    stats = bw.annualized_gap(r_syn, r_bxm)
    pd.DataFrame([stats]).round(4).to_csv(tables / "reconstruction_bxm.csv", index=False)
    syn.assign(debut=syn["debut"].astype(str)).round(5).to_csv(tables / "periodes_synthetiques.csv")
    figures.fig_bxm(r_bxm, r_syn, r_idx, stats["ecart_annualise_pb"],
                    str(syn["debut"].iloc[0].date()), figs / "bxm.png")

    # ce que coûtent les conventions : chaque variante est REJOUÉE ici, au lieu d'être citée de
    # mémoire dans le README (l'omission du dividende y valait « environ 106 pb/an », mesurée ici)
    variantes = [("référence", {}),
                 ("sans rendement en dividendes", {"dividendes": False}),
                 ("prix d'exercice au niveau ou au-dessus (règle Cboe)",
                  {"strike_strictement_au_dessus": False})]
    lignes = []
    for nom, kwargs in variantes:
        v = bw.synthetic_buywrite(gspc, tr, vix, rate, **kwargs)
        v = v.loc[v["debut"] >= debut]
        g = bw.annualized_gap(v["r_synthetique"], r_bxm)
        lignes.append({"variante": nom, "ecart_annualise_pb": g["ecart_annualise_pb"],
                       "ecart_vs_reference_pb": g["ecart_annualise_pb"] - stats["ecart_annualise_pb"],
                       "correlation": g["correlation"], "n_periodes": g["n_periodes"]})
    pd.DataFrame(lignes).round(4).to_csv(tables / "conventions_sensibilite.csv", index=False)
    typer.echo(pd.DataFrame(lignes).round(2).to_string(index=False))

    perf = pd.DataFrame([
        {"serie": "S&P 500 TR", "rendement_annuel_pct": ((1 + r_idx).prod() ** (12 / len(r_idx)) - 1) * 100,
         "vol_annuelle_pct": r_idx.std(ddof=1) * (12**0.5) * 100},
        {"serie": "BXM officiel", "rendement_annuel_pct": ((1 + r_bxm).prod() ** (12 / len(r_bxm)) - 1) * 100,
         "vol_annuelle_pct": r_bxm.std(ddof=1) * (12**0.5) * 100},
        {"serie": "synthétique", "rendement_annuel_pct": ((1 + r_syn).prod() ** (12 / len(r_syn)) - 1) * 100,
         "vol_annuelle_pct": r_syn.std(ddof=1) * (12**0.5) * 100},
    ])
    perf.round(2).to_csv(tables / "rendement_risque.csv", index=False)

    # volet 2 : la prime de variance (depuis 1990, tout l'historique du VIX)
    vrp = bw.variance_premium(vix, gspc)
    t = bw.nw_tstat(vrp["prime"].to_numpy())
    vrp.round(6).to_csv(tables / "prime_variance.csv")
    figures.fig_vrp(vrp, t, figs / "prime_variance.png")

    # volet 3 : ZWB contre ZEB
    figures.fig_zwb(px, figs / "zwb_zeb.png")
    both = px[["ZWB.TO", "ZEB.TO"]].dropna()
    r = both.pct_change().dropna()
    duel = pd.DataFrame([{
        "depuis": str(r.index[0].date()),
        "cagr_zwb_pct": ((1 + r["ZWB.TO"]).prod() ** (252 / len(r)) - 1) * 100,
        "cagr_zeb_pct": ((1 + r["ZEB.TO"]).prod() ** (252 / len(r)) - 1) * 100,
        "vol_zwb_pct": r["ZWB.TO"].std() * (252**0.5) * 100,
        "vol_zeb_pct": r["ZEB.TO"].std() * (252**0.5) * 100,
        "pire_baisse_zwb_pct": (((1 + r["ZWB.TO"]).cumprod() / (1 + r["ZWB.TO"]).cumprod().cummax()) - 1).min() * 100,
        "pire_baisse_zeb_pct": (((1 + r["ZEB.TO"]).cumprod() / (1 + r["ZEB.TO"]).cumprod().cummax()) - 1).min() * 100,
    }])
    duel.round(2).to_csv(tables / "zwb_zeb.csv", index=False)

    typer.echo(f"reconstruction BXM : écart {stats['ecart_annualise_pb']:+.0f} pb/an, "
               f"erreur {stats['erreur_reproduction_pb']:.0f} pb/an, corr {stats['correlation']:.4f} "
               f"({int(stats['n_periodes'])} périodes)")
    typer.echo(perf.round(2).to_string(index=False))
    typer.echo(f"prime de variance : positive {100 * (vrp['prime'] > 0).mean():.0f} % des mois, "
               f"t NW {t:.1f} ({len(vrp)} mois)")
    typer.echo(duel.round(2).to_string(index=False))


if __name__ == "__main__":
    app()
