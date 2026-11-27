"""Fiche de salaires d'un exercice : le net dû par employé et chaque virement avec son exercice et sa part de salaire.

La fiche est écrite par le lecteur du classeur de paie et peut être corrigée à la main. L'onglet masqué `auto` garde ce que le
lecteur avait proposé : à la relecture, une valeur qui en diffère est une correction et elle est gardée.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill

from .. import config

COLONNES_DU = ["employe", "net_du", "source", "remarque"]
COLONNES_VIREMENTS = ["id", "employe", "date", "banque", "montant", "exercice", "part_salaire", "type", "libelle",
                      "piece", "imputation", "controle", "preuve"]
COLONNES_POINTS = ["employe", "point"]
CORRIGEABLES = ["exercice", "part_salaire", "imputation"]
COLONNES_AUTO = ["cle"] + CORRIGEABLES + ["net_du"]
PREFIXE_DU = "du:"

_SAISIE = PatternFill("solid", fgColor="FFF2CC")
_ENTETE = PatternFill("solid", fgColor="DDE4EE")
_LARGEURS = {"id": 34, "employe": 30, "date": 12, "libelle": 34, "piece": 32, "imputation": 60, "type": 24,
             "preuve": 28, "source": 18, "remarque": 50, "point": 90, "controle": 18}


class FichierOuvert(Exception):
    """Le fichier est ouvert dans Excel : impossible de l'écrire."""


def chemin_fiche(annee: int) -> Path:
    return config.DOSSIER_FICHES_SALAIRES / f"fiche_salaires_{annee}.xlsx"


def _montant(v) -> float:
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return 0.0


def identifiants(virements: list[dict]) -> None:
    """Donne à chaque virement un identifiant stable : AAAAMMJJ-employé-montant-rang."""
    vus: dict[str, int] = {}
    for v in virements:
        d = v.get("date")
        jour = d.strftime("%Y%m%d") if isinstance(d, datetime) else "00000000"
        base = f"{jour}-{re.sub(r'[^0-9A-Za-zÀ-ÿ]', '', str(v.get('employe') or ''))}-{_montant(v.get('montant')):.2f}"
        vus[base] = vus.get(base, 0) + 1
        v["id"] = f"{base}-{vus[base]}"


def valeurs_auto(f: dict) -> dict:
    """Valeurs proposées par le lecteur, par identifiant de virement et par employé (net dû)."""
    auto = {v["id"]: {c: v.get(c) for c in CORRIGEABLES} for v in f["virements"] if v.get("id")}
    for d in f["du"]:
        auto[PREFIXE_DU + d["employe"]] = {"net_du": d.get("net_du")}
    return auto


def _egal(a, b) -> bool:
    if isinstance(a, (int, float)) or isinstance(b, (int, float)):
        try:
            return abs(float(a or 0) - float(b or 0)) < 0.005
        except (TypeError, ValueError):
            return False
    return (a or "") == (b or "")


def fusionner(ancienne: dict | None, nouvelle: dict) -> tuple[dict, dict]:
    """Nouvelle lecture du classeur de paie, en gardant les corrections et les preuves de l'ancienne fiche."""
    bilan = {"ajoutes": 0, "retires": 0, "gardees": 0, "manuels": 0}
    resultat = {"du": [dict(d) for d in nouvelle["du"]], "virements": [dict(v) for v in nouvelle["virements"]],
                "points": [], "auto": valeurs_auto(nouvelle)}
    if ancienne is None:
        bilan["ajoutes"] = len(resultat["virements"])
        return resultat, bilan

    auto_ancien = ancienne.get("auto", {})
    anciens = {v["id"]: v for v in ancienne["virements"] if v.get("id") in auto_ancien}
    nouveaux_ids = {v["id"] for v in resultat["virements"]}
    for v in resultat["virements"]:
        a = anciens.get(v["id"])
        if a is None:
            bilan["ajoutes"] += 1
            continue
        for c in CORRIGEABLES:
            if not _egal(a.get(c), auto_ancien[v["id"]].get(c)):
                v[c] = a.get(c)
                bilan["gardees"] += 1
        v["preuve"] = a.get("preuve") or v.get("preuve") or ""
    bilan["retires"] = sum(1 for i in anciens if i not in nouveaux_ids)
    manuels = [dict(v) for v in ancienne["virements"] if v.get("id") not in auto_ancien]
    bilan["manuels"] = len(manuels)
    resultat["virements"].extend(manuels)

    anciens_du = {d["employe"]: d for d in ancienne["du"]}
    for d in resultat["du"]:
        a = anciens_du.get(d["employe"])
        proposee = auto_ancien.get(PREFIXE_DU + d["employe"], {}).get("net_du")
        if a is not None and proposee is not None and not _egal(a.get("net_du"), proposee):
            d["net_du"] = a.get("net_du")
            bilan["gardees"] += 1
    resultat["points"] = [dict(p) for p in ancienne.get("points", [])]
    return resultat, bilan


def _feuille(wb, titre: str, colonnes: list[str], lignes: list[dict], saisie: tuple[str, ...] = ()):
    ws = wb.create_sheet(titre)
    ws.append(colonnes)
    for i, c in enumerate(colonnes, 1):
        cell = ws.cell(1, i)
        cell.font, cell.fill = Font(bold=True), _ENTETE
        ws.column_dimensions[cell.column_letter].width = _LARGEURS.get(c, 14)
    for ligne in lignes:
        ws.append([ligne.get(c) for c in colonnes])
    for i, c in enumerate(colonnes, 1):
        if c in saisie:
            for r in range(2, ws.max_row + 1):
                ws.cell(r, i).fill = _SAISIE
        if c == "date":
            for r in range(2, ws.max_row + 1):
                ws.cell(r, i).number_format = "DD.MM.YYYY"
    ws.freeze_panes = "A2"
    return ws


def ecrire(annee: int, f: dict) -> Path:
    chemin = chemin_fiche(annee)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    _feuille(wb, "du", COLONNES_DU, f["du"], saisie=("net_du",))
    _feuille(wb, "virements", COLONNES_VIREMENTS, f["virements"], saisie=("exercice", "part_salaire", "imputation", "preuve"))
    _feuille(wb, "points", COLONNES_POINTS, f.get("points", []))
    auto = [{"cle": k, **v} for k, v in f.get("auto", {}).items()]
    _feuille(wb, "auto", COLONNES_AUTO, auto).sheet_state = "hidden"
    try:
        wb.save(chemin)
    except PermissionError as e:
        raise FichierOuvert(f"Ferme {chemin.name} dans Excel, puis recommence.") from e
    return chemin


def _lignes(ws) -> list[dict]:
    rangs = list(ws.iter_rows(values_only=True))
    if not rangs:
        return []
    entetes = [str(c or "").strip() for c in rangs[0]]
    resultat = []
    for r in rangs[1:]:
        if all(v in (None, "") for v in r):
            continue
        resultat.append({e: v for e, v in zip(entetes, r) if e})
    return resultat


def _normaliser_virement(v: dict) -> dict:
    out = {c: v.get(c) for c in COLONNES_VIREMENTS}
    for c in ("id", "employe", "banque", "type", "libelle", "piece", "imputation", "controle", "preuve"):
        out[c] = "" if out[c] is None else str(out[c])
    out["montant"] = _montant(out["montant"])
    out["part_salaire"] = _montant(out["part_salaire"])
    try:
        out["exercice"] = int(out["exercice"])
    except (TypeError, ValueError):
        out["exercice"] = None
    return out


def lire(annee: int) -> dict | None:
    chemin = chemin_fiche(annee)
    if not chemin.exists():
        return None
    wb = openpyxl.load_workbook(chemin, data_only=True)
    du = [{"employe": str(d.get("employe") or ""), "net_du": _montant(d.get("net_du")),
           "source": str(d.get("source") or ""), "remarque": str(d.get("remarque") or "")}
          for d in _lignes(wb["du"]) if d.get("employe")]
    virements = [_normaliser_virement(v) for v in _lignes(wb["virements"]) if v.get("employe")]
    points = [{"employe": str(p.get("employe") or ""), "point": str(p.get("point") or "")}
              for p in _lignes(wb["points"])] if "points" in wb.sheetnames else []
    auto = {}
    if "auto" in wb.sheetnames:
        for a in _lignes(wb["auto"]):
            cle = str(a.get("cle") or "")
            if cle.startswith(PREFIXE_DU):
                auto[cle] = {"net_du": _montant(a.get("net_du"))}
            elif cle:
                ex = a.get("exercice")
                auto[cle] = {"exercice": int(ex) if ex not in (None, "") else None,
                             "part_salaire": _montant(a.get("part_salaire")),
                             "imputation": "" if a.get("imputation") is None else str(a.get("imputation"))}
    return {"du": du, "virements": virements, "points": points, "auto": auto}
