"""Écriture du classeur normalisé (pour l'Assistant société) et de la page lisible."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

import pandas as pd

from ..outils import nom_de_fichier_sur
from .classement import LIBELLES

COLONNES = {
    "meta": ["cle", "valeur"],
    "pages": ["page", "type", "methode", "score", "source"],
    "controles": ["controle", "resultat", "detail"],
    "plancomptable": ["code", "nom", "type", "exercice", "source"],
    "grandlivre": ["date", "compte", "libelle_compte", "piece", "partenaire", "libelle", "debit", "credit",
                   "exercice", "source"],
    "bilan": ["rubrique", "compte", "libelle", "montant", "colonne_exercice_precedent", "niveau", "exercice", "source"],
    "compteresultat": ["rubrique", "compte", "libelle", "montant", "colonne_exercice_precedent", "niveau",
                       "exercice", "source"],
    "annexe": ["page", "texte", "source"],
}
TITRES = {"plancomptable": "Plan comptable", "grandlivre": "Grand livre", "bilan": "Bilan",
          "compteresultat": "Compte de résultat", "annexe": "Annexe et autres pages"}
METHODES = {"regles": "règles locales", "continuite": "suite de la page précédente", "ia": "IA",
            "manuel": "choix manuel", "a_verifier": "à vérifier", "illisible": "illisible"}


def _cible_libre(chemin: Path) -> Path:
    """Si le fichier est ouvert dans Excel (verrouillé), écrit à côté avec l'heure."""
    try:
        if chemin.exists():
            with open(chemin, "a+b"):
                pass
        return chemin
    except PermissionError:
        return chemin.with_name(f"{chemin.stem}_{datetime.now():%Y%m%d-%H%M%S}{chemin.suffix}")


def ecrire_excel(tables: dict[str, list[dict]], racine: Path, exercice: int, nom: str) -> Path:
    dossier = Path(racine) / "entrees" / "06_societe" / "imports" / str(exercice)
    dossier.mkdir(parents=True, exist_ok=True)
    cible = _cible_libre(dossier / f"{nom_de_fichier_sur(nom, 60)}.xlsx")
    with pd.ExcelWriter(cible, engine="openpyxl") as w:
        for onglet, colonnes in COLONNES.items():
            df = pd.DataFrame(tables.get(onglet, []), columns=colonnes)
            df.to_excel(w, sheet_name=onglet, index=False)
            feuille = w.sheets[onglet]
            for i, col in enumerate(colonnes, start=1):
                largeur = max([len(col)] + [len(str(v)) for v in df[col].head(200).tolist()])
                feuille.column_dimensions[feuille.cell(1, i).column_letter].width = min(60, largeur + 2)
            feuille.freeze_panes = "A2"
    return cible


def _montant(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return f"{v:,.2f}".replace(",", "'")


def _tableau(lignes: list[dict], colonnes: list[str], max_lignes: int = 500) -> str:
    num = {"debit", "credit", "montant", "colonne_exercice_precedent"}
    tete = "".join(f"<th>{html.escape(c)}</th>" for c in colonnes)
    corps = []
    for l in lignes[:max_lignes]:
        cellules = []
        for c in colonnes:
            v = l.get(c)
            if c in num:
                cellules.append(f'<td class="n">{_montant(v)}</td>')
            else:
                classe_td = ' class="texte"' if c == "texte" else ""
                cellules.append(f"<td{classe_td}>{html.escape('' if v is None else str(v))}</td>")
        classe = f' class="niv{l.get("niveau")}"' if l.get("niveau") else ""
        corps.append(f"<tr{classe}>{''.join(cellules)}</tr>")
    reste = f"<p class='note'>… {len(lignes) - max_lignes} ligne(s) de plus dans le classeur.</p>" \
        if len(lignes) > max_lignes else ""
    return f"<table><thead><tr>{tete}</tr></thead><tbody>{''.join(corps)}</tbody></table>{reste}"


def ecrire_html(tables: dict[str, list[dict]], meta: dict, racine: Path, nom: str) -> Path:
    dossier = Path(racine) / "sorties" / "imports"
    dossier.mkdir(parents=True, exist_ok=True)
    cible = dossier / f"{nom_de_fichier_sur(nom, 60)}.html"
    pages = "".join(
        f"<tr><td>{p['page']}</td><td>{LIBELLES.get(p['type'], p['type'])}</td>"
        f"<td class='m-{p['methode']}'>{METHODES.get(p['methode'], p['methode'])}</td></tr>"
        for p in tables["pages"])
    controles = "".join(
        f"<li class='{c['resultat']}'>{'✓' if c['resultat'] == 'ok' else '⚠'} {html.escape(c['controle'])} : "
        f"{html.escape(c['detail'])}</li>" for c in tables["controles"]) or "<li>Aucun contrôle applicable.</li>"
    blocs = []
    for cle, titre in TITRES.items():
        if tables.get(cle):
            colonnes = [c for c in COLONNES[cle] if c not in ("exercice", "source")] + ["source"]
            blocs.append(f"<h2>{titre} <small>{len(tables[cle])} ligne(s)</small></h2>"
                         + _tableau(tables[cle], colonnes))
    ia = (f"{meta['appels_ia']} page(s) envoyée(s) à {meta['modele_ia']}, {meta['tokens_entree']} tokens en entrée"
          if meta.get("appels_ia") else "aucun appel IA")
    contenu = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Import {html.escape(meta['fichier_source'])}</title>
<style>
:root {{ --fond:#f7f7f5; --texte:#1f2328; --bord:#d8d8d2; --accent:#2f5d8a; --ok:#1a7f37; --ko:#b35900; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fond:#16181b; --texte:#e6e6e3; --bord:#34383d; --accent:#7fb0e0; --ok:#57c785; --ko:#f0a050; }} }}
body {{ font-family: "Segoe UI", system-ui, sans-serif; background:var(--fond); color:var(--texte); margin:0 auto; padding:16px; max-width:1200px; }}
h1 {{ font-size:1.4rem; }} h2 {{ font-size:1.1rem; color:var(--accent); margin-top:2rem; }} small {{ font-weight:normal; opacity:.7; }}
table {{ border-collapse:collapse; width:100%; font-size:.85rem; display:block; overflow-x:auto; }}
th, td {{ border-bottom:1px solid var(--bord); padding:4px 8px; text-align:left; white-space:nowrap; }}
td.texte {{ white-space:normal; min-width:320px; }} td.n {{ text-align:right; font-variant-numeric:tabular-nums; }} tr.niv1 td {{ font-weight:600; }}
li.ok {{ color:var(--ok); }} li.ecart {{ color:var(--ko); }} .m-ia, .m-manuel, .m-a_verifier, .m-illisible {{ color:var(--ko); }}
.resume {{ display:flex; gap:24px; flex-wrap:wrap; }} .note {{ opacity:.7; }}
</style></head><body>
<h1>{html.escape(meta['fichier_source'])}</h1>
<p>{html.escape(meta.get('societe') or 'Société non détectée')} · exercice {meta['date_debut'][:4]} · {meta['devise']} · {ia}</p>
<div class="resume"><div><h2>Pages</h2><table><thead><tr><th>Page</th><th>Type</th><th>Reconnu par</th></tr></thead>
<tbody>{pages}</tbody></table></div><div><h2>Contrôles</h2><ul>{controles}</ul></div></div>
{''.join(blocs)}
</body></html>"""
    cible.write_text(contenu, encoding="utf-8")
    return cible
