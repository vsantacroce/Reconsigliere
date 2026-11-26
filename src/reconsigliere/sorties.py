"""Production des sorties : PDF renommés, Excel de réconciliation et page interactive."""

from __future__ import annotations

import html
import json
import shutil
from collections import Counter
from pathlib import Path

import pandas as pd

from . import config
from .outils import nom_de_fichier_sur
from .rapprochement import STATUT_A_COMPTABILISER, STATUT_A_CONFIRMER


def nom_logique(t: dict) -> str:
    p = t["pdf"]
    date = t["date"]
    if p and p["dates"]:
        date = min(p["dates"], key=lambda d: abs((d - t["date"]).days))
    parties = [date.isoformat(), nom_de_fichier_sur(t["partenaire_trouve"]),
               f"{abs(t['montant']):.2f}{config.DEVISE}"]
    if p and p["numeros"]:
        parties.append(nom_de_fichier_sur(p["numeros"][0], 25))
    extension = p["chemin"].suffix.lower() if p else ".pdf"
    return "_".join(parties) + extension


def vider(dossier: Path) -> None:
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)


def copier_pdfs(transactions: list[dict]) -> None:
    vider(config.DOSSIER_PDF_RENOMMES)
    vider(config.DOSSIER_A_COMPTABILISER)
    pris: set[str] = set()
    for t in transactions:
        t["pdf_renomme"] = ""
        if t["pdf"] is None:
            continue
        nom = nom_logique(t)
        base, ext = Path(nom).stem, Path(nom).suffix
        n = 2
        while nom.lower() in pris:
            nom, n = f"{base}_{n}{ext}", n + 1
        pris.add(nom.lower())
        shutil.copy2(t["pdf"]["chemin"], config.DOSSIER_PDF_RENOMMES / nom)
        t["pdf_renomme"] = nom
        if t["statut"] in (STATUT_A_COMPTABILISER, STATUT_A_CONFIRMER):
            shutil.copy2(t["pdf"]["chemin"], config.DOSSIER_A_COMPTABILISER / nom)


def _lignes(transactions: list[dict]) -> list[dict]:
    return [{
        "id_transaction": t["id"],
        "date": t["date"].isoformat(),
        "montant": t["montant"],
        "libelle": t["libelle"],
        "partenaire": t["partenaire_trouve"],
        "origine_partenaire": t["origine_partenaire"],
        "statut": t["statut"],
        "compte_propose": t.get("compte_propose", ""),
        "fiabilite_compte": t.get("fiabilite_compte", ""),
        "pdf_renomme": t.get("pdf_renomme", ""),
        "pdf_original": t["pdf"]["nom"] if t["pdf"] else "",
        "score": t["score"],
        "raisons": t["raisons"],
        "explication": t["explication"],
        "source": t["source"],
    } for t in transactions]


def ecrire_excel(transactions: list[dict], orphelins: list[dict]) -> Path:
    chemin = config.DOSSIER_SORTIES / "reconciliation.xlsx"
    lignes = _lignes(transactions)
    resume = Counter(l["statut"] for l in lignes)
    with pd.ExcelWriter(chemin, engine="openpyxl") as w:
        pd.DataFrame(lignes).to_excel(w, sheet_name="reconciliation", index=False)
        pd.DataFrame([{"pdf": p["nom"], "lisible": p["lisible"],
                       "montants_trouves": ", ".join(f"{m:.2f}" for m in p["montants"][:5]),
                       "dates_trouvees": ", ".join(d.isoformat() for d in p["dates"][:3])}
                      for p in orphelins]).to_excel(w, sheet_name="pdf_sans_transaction", index=False)
        pd.DataFrame([{"statut": k, "nombre": v} for k, v in resume.items()]).to_excel(
            w, sheet_name="resume", index=False)
    return chemin


def ecrire_html(transactions: list[dict], orphelins: list[dict]) -> Path:
    chemin = config.DOSSIER_SORTIES / "reconciliation.html"
    donnees = json.dumps({"lignes": _lignes(transactions),
                          "orphelins": [p["nom"] for p in orphelins],
                          "devise": config.DEVISE}, ensure_ascii=False)
    gabarit = (Path(__file__).parent / "modele.html").read_text(encoding="utf-8")
    chemin.write_text(gabarit.replace("__DONNEES__", donnees.replace("</", "<\\/")), encoding="utf-8")
    return chemin
