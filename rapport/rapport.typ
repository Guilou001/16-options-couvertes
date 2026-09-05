#set document(title: "Ce que rapporte réellement la vente d'options d'achat couvertes", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [options-couvertes], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Ce que rapporte réellement la vente d'options d'achat couvertes]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-04 · #link("https://github.com/Guilou001/16-options-couvertes")[Guilou001/16-options-couvertes]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Un fonds d'options d'achat couvertes détient des actions et vend en même temps une partie de leur hausse future. Cette vente produit une prime régulière, souvent présentée comme un revenu. Toutefois, elle limite aussi les gains lorsque le marché monte et ne garantit pas une protection lorsque le marché baisse.

Le présent projet reconstruit l'indice américain BXM avec des données publiques, mesure la différence entre la volatilité annoncée et la volatilité ensuite réalisée, puis compare deux fonds canadiens investis dans les mêmes banques.

*Résultat principal.* La reconstruction du BXM atteint une corrélation de 0,981 avec l'indice officiel, mais elle le dépasse de 5,23 points de pourcentage par an. Cet écart mesure principalement ce que le VIX ne dit pas sur le prix de l'option vendue. Depuis 1990, la variance anticipée dépasse la variance réalisée dans 84 % des mois. Toutefois, entre 2011 et 2026, le fonds bancaire sans options rapporte 13,96 % par an, contre 11,21 % pour le fonds couvert, avec des pertes maximales presque identiques.

Afin d'expliquer ces résultats, nous présenterons d'abord le fonctionnement d'une option d'achat couverte. Dans un deuxième temps, nous reconstruirons l'indice BXM et isolerons les conventions qui créent un écart. Ensuite, nous mesurerons la prime de variance et comparerons les deux fonds canadiens. Enfin, nous présenterons les limites des données, les variantes et les commandes de reproduction.

Le même contenu en PDF : #link("rapport/rapport.pdf")[rapport/rapport.pdf].

== Les résultats en détail

+ *Le VIX ne suffit PAS à répliquer le BXM, et l'écart est la mesure du skew.* Un buy-write synthétique (S&P 500 en rendement total, call vendu chaque troisième vendredi, prix Black-Scholes avec le VIX comme volatilité et le dividende réalisé des 252 séances passées) suit l'officiel à 0,981 de corrélation mais le bat de +523 pb/an : le VIX, moyenne de la variance implicite sur TOUS les prix d'exercice cotés, surévalue systématiquement le call à la monnaie que le skew rend moins cher. La donnée libre chiffre ce qu'elle ne capte pas, et c'est le résultat. (Mesuré, 292 périodes 2002-2026 ; sans le dividende, l'écart monte à +630 : la première version de ce dépôt l'omettait, et la variante est rejouée dans #raw("results/tables/conventions_sensibilite.csv"), qui la chiffre à +107 pb/an.)
+ *La prime de risque de variance existe, et elle est grosse.* Sur 438 mois depuis 1990, la variance implicite (VIX au carré) dépasse la variance ensuite réalisée dans 84 % des mois (t de Newey-West : 3,3) : le vendeur d'options encaisse une assurance structurellement surpayée, et c'est le vrai moteur des stratégies couvertes, pas le « revenu ». (Mesuré.)
+ *ZWB contre ZEB, mêmes banques canadiennes : le jumeau nu gagne.* Depuis 2011, ZEB (banques sans options) fait 13,96 %/an contre 11,21 % pour ZWB (mêmes banques, options d'achat vendues), pour un pire creux quasi IDENTIQUE (-39,7 % contre -39,4 %) : la vente des options d'achat a coûté 2,75 points par an et n'a pas protégé quand ça comptait. (Mesuré.)

== La question

La parité put-call dit que la prime encaissée n'est pas un revenu mais le prix de la hausse abandonnée ; pourtant les FNB d'options d'achat couvertes collectent des milliards en promettant les deux. Que reste-t-il du produit quand on le décompose avec des données libres : une prime de variance réelle, ou un tour de passe-passe comptable ?

== Les données (100 % libres, téléchargées par script, jamais commitées)

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Source*],
    [*Contenu*],
    [*Période*],
    [*Statut*],
    [Cboe #raw("BXM_History.csv")],
    [l'indice buy-write officiel, quotidien],
    [2002-03-22 à 2026-08 (mesuré : le CSV libre ne remonte PAS à 1986)],
    [mesuré ; usage personnel, jamais republié],
    [FRED #raw("VIXCLS"), #raw("DGS1MO")],
    [VIX quotidien ; taux 1 mois],
    [1990- ; 2001-],
    [mesuré],
    [Yahoo #raw("^GSPC"), #raw("^SP500TR"), #raw("ZWB.TO"), #raw("ZEB.TO")],
    [indice prix, indice rendement total, le duel canadien],
    [2011-02 pour ZWB],
    [mesuré ; usage personnel],
)

Conséquence déclarée : l'échantillon de Whaley (2002), 1988-2001, n'est pas recouvrable en données libres ; la validation se fait sur 2002-2026, vingt-quatre ans qui contiennent 2008, 2020 et 2022. La licence Cboe interdit la redistribution : aucune série brute dans le dépôt, seulement des statistiques dérivées.

== Volet 1 : le BXM reconstruit, et ce que l'écart enseigne

La méthodologie officielle (rapporté, PDF Cboe) : détenir le S&P 500 dividendes compris, vendre chaque troisième vendredi le call SPX d'un mois au premier prix d'exercice ÉGAL OU SUPÉRIEUR au niveau relevé avant 11 h, régler au SOQ, prime réinvestie dans le portefeuille couvert. Nos conventions, déclarées et mesurées par la contre-vérification : roulement au cours de clôture du vendredi, prix d'exercice STRICTEMENT au-dessus (effet : -0,2 pb/an), prime placée au taux 1 mois (convention conservatrice : la base officielle donnerait environ +30 pb/an de plus), call valorisé par Black-Scholes au VIX avec le rendement en dividendes réalisé des 252 séances précédentes, observable ex ante.

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Mesure (292 périodes d'échéance à échéance, 2002-2026)*],
    [*Valeur*],
    [Corrélation synthétique / officiel],
    [0,9813],
    [Écart annualisé synthétique moins officiel],
    [*+523 pb/an*],
    [Erreur de réplication],
    [236 pb/an],
    [Rendements annualisés : indice TR / BXM / synthétique],
    [10,3 % / 6,2 % / 11,5 %],
    [Volatilités : indice TR / BXM / synthétique],
    [17,7 % / 12,3 % / 12,0 %],
)

*Lecture guidée.* La forme est la bonne : corrélation 0,981, volatilité quasi égale à l'officiel (12,0 contre 12,3). Le niveau ne l'est pas : +523 pb/an. La cause est connue et c'est la leçon du volet : le VIX agrège la variance implicite de TOUS les prix d'exercice, où les puts hors de la monnaie, chers à cause du skew, pèsent lourd. Le call légèrement hors de la monnaie que le BXM vend se négocie à une volatilité NETTEMENT plus basse, et le vendre au prix du VIX encaisse une prime fictive. L'ordre de grandeur se vérifie : le véga d'un call d'un mois à la monnaie vaut environ 11 pb de l'indice par point de volatilité, donc environ 137 pb/an ; les +523 pb/an équivalent à 3,8 points de volatilité d'écart entre le VIX et la volatilité implicite du call vendu, dans la fourchette de 2 à 5 points que la littérature rapporte, conventions de roulement comprises. Quiconque backteste des ventes d'options avec le VIX comme volatilité surévalue donc ses primes d'environ cinq points de rendement par an sur ce produit. Le synthétique qui « bat » l'indice est un mirage de données, chiffré au lieu d'être vendu. (Mesuré ; la séparation fine entre skew, convexité et roulement exigerait les prix d'options réels, non libres, déclaré.)

#figure(image("../results/figures/bxm.png", width: 100%), caption: [BXM])

*Comment lire cette figure.* En haut, 100 \$ dans l'indice total (jaune), le BXM officiel (bleu) et la reconstruction (tirets orange), échelle log. Le bleu décroche du jaune dans chaque grand rebond (2009, 2020) : vendre la hausse coûte la hausse, surtout quand elle arrive d'un coup. En bas, le rapport synthétique/officiel : une dérive régulière (le skew de tous les mois) accélérée en 2008-09 (quand le VIX s'envole, la prime fictive aussi).

== Volet 2 : la prime de variance, le vrai moteur (mesuré, #raw("results/tables/prime_variance.csv"))

Chaque fin de mois depuis 1990 : la variance implicite ((VIX/100)² x 30/365) contre la variance réalisée des 21 séances suivantes (somme des carrés des rendements log). La différence est ce que l'acheteur d'assurance paie en trop, à la Carr et Wu (2009).

#figure(image("../results/figures/prime_variance.png", width: 100%), caption: [Prime de variance])

*Comment lire cette figure.* La volatilité implicite (bleu) vit au-dessus de la réalisée (orange) presque en permanence : prime positive 84 % des mois, t de Newey-West de 3,3 sur 438 mois. Les exceptions sont les crises (2008, 2020), où la réalisée explose au-dessus : le vendeur d'assurance encaisse petit tous les mois et paie gros d'un coup. C'est exactement le profil de rendement d'un FNB d'options couvertes.

== Volet 3 : le duel canadien (mesuré, #raw("results/tables/zwb_zeb.csv"))

#figure(image("../results/figures/zwb_zeb.png", width: 100%), caption: [ZWB contre ZEB])

*Comment lire cette figure.* Deux FNB de BMO sur le MÊME panier de banques canadiennes : ZEB sans options, ZWB avec options d'achat vendues. Depuis 2011 : 13,96 %/an contre 11,21 %, volatilité 15,8 % contre 14,6 %, pire creux -39,7 % contre -39,4 %. La vente de options d'achat a acheté 1,2 point de volatilité en moins au prix de 2,75 points de rendement par an, et n'a presque rien amorti dans la vraie baisse : quand le panier tombe de 39,7 % (mesuré, mars 2020), un call vendu n'en absorbe que sa prime. Le « revenu » mensuel est réel ; le coût l'est aussi, il est juste moins visible.

== Reproduire

#raw("uv sync --locked --all-extras\nuv run pytest        # 12 tests fermés, sans réseau\nuv run ovc fetch     # Cboe + FRED + Yahoo (~2 Mo)\nuv run ovc lab       # trois volets : 5 tables, 3 figures (~1 min)", block: true, lang: "bash")

Les tests, tous fermés :

- troisièmes vendredis sur cas datés ; prix d'exercice strictement au-dessus ;
- Black-Scholes par parité contre la valeur à la main du dépôt 15 ; le dividende abaisse

le call de l'ordre mesuré (~8 pb de l'indice par mois) ;

- marché immobile = la prime exactement ; rallye = plafonné au prix d'exercice plus la

prime (identités) ;

- prime de variance nulle quand l'implicite égale la réalisée (formule exacte) ;
- t de Newey-West sur moyennes connues ; écart annualisé nul sur séries identiques.

== Limites, avec statut

+ *Le synthétique n'est pas une réplication au pb, et c'est le résultat.* L'écart de +523 pb/an mesure ensemble le skew, la convexité du VIX et les conventions de roulement ; les prix d'options réels qui permettraient de les séparer ne sont pas libres. (Mesuré pour le total, déclaré pour la décomposition.)
+ *Le roulement est à la clôture du vendredi*, pas au SOQ du matin ni au cours moyen pondéré de l'après-midi comme l'officiel : du bruit de réplication, logé dans les 236 pb d'erreur. (Déclaré.)
+ *Le dividende est estimé, pas observé* : le rendement réalisé des 252 séances passées sert de q dans Black-Scholes (moyenne : 1,9 %/an) ; la première version du dépôt l'omettait et #raw("conventions_sensibilite.csv") chiffre l'omission à +107 pb/an, désormais corrigée dans le modèle. (Mesuré.)
+ *ZWB et ZEB diffèrent aussi par leurs frais.* Aujourd'hui : 44 pb d'écart de RFG (72 contre 28) et 63 pb en comptant les frais d'opérations de ZWB ; mais ZEB facturait 55 pb avant sa baisse du 1er septembre 2021 (annonce BMO du 2021-08-18), d'où un écart moyen d'environ 20 à 40 pb sur l'échantillon (rapporté et pondéré). La part mécanique des 2,75 points, la hausse abandonnée, est donc PLUS grande que les frais : le constat du volet 3 en sort renforcé.
+ *Whaley 2002 n'est pas répliqué* : son échantillon précède le CSV libre. (Déclaré, mesuré.)

== Références

- Whaley, R. E. (2002), « Return and risk of CBOE buy write monthly index », \*Journal of

Derivatives\* 9(3) : l'étude fondatrice, hors de portée des données libres.

- Carr, P. et L. Wu (2009), « Variance risk premiums », _Review of Financial Studies_

22(3) : le cadre du volet 2.

- Israelov, R. et L. N. Nielsen (2015), « Covered calls uncovered » (SSRN 2444999) : la

décomposition dont le volet 3 est l'écho canadien.

- Cboe, méthodologie officielle du BXM (PDF public).

== English summary

Covered-call ETFs are Canada's favourite "income" product. (1) We rebuild the Cboe BXM buy-write index from free data: hold the S&P 500 total return, sell the 1-month SPX call at the first strike above the index every third Friday, priced by Black-Scholes with the VIX as implied volatility and the trailing-252-day realized dividend yield. Result, 292 expiry-to-expiry periods 2002-2026: correlation 0.981 with the official index, but +523 bp/yr TOO RICH (the first version omitted the dividend; the repo now replays that variant and measures the omission at +107 bp/yr). That gap IS the finding: the VIX averages implied variance across all strikes (skew included), while the slightly-OTM call the BXM sells trades at a much lower volatility, about 3.9 vol points lower here (via the ~137 bp/yr-per-vol-point vega of a 1-month ATM call): anyone backtesting option selling with VIX-priced premiums overstates returns by about five points a year on this product. (2) The variance risk premium is real: implied variance exceeds subsequently realized variance in 84 % of 438 months since 1990 (Newey-West t = 3.3), with crisis months as the violent exceptions: that premium, not "income", is what covered-call funds harvest. (3) The Canadian duel: since 2011, ZEB (bare bank basket) returns 13.96 %/yr vs 11.21 % for ZWB (same banks plus written calls), with nearly IDENTICAL worst drawdowns (-39.7 % vs -39.4 %): the calls cost 2.75 points a year and protected almost nothing in March

+ Free data only (Cboe personal use, never redistributed); 12 closed-form tests.

== Licence et citation

Code sous licence MIT ; rapport et figures CC BY 4.0. Données : Cboe (usage personnel, jamais republiées), FRED, Yahoo (usage personnel). Citer via #raw("CITATION.cff").
