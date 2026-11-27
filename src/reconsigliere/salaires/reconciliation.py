"""Réconciliation des salaires d'un exercice N : résumé chiffré et classeur pour la fiduciaire.

Lit la fiche N (obligatoire), la fiche N−1 (restes de l'année précédente) et la fiche N+1 (paiements de l'année suivante).
La synthèse du classeur ne contient que des formules qui renvoient aux feuilles de virements.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .. import config
from .fiche import FichierOuvert

CHF = '#,##0.00;-#,##0.00;"–"'
_GRAS = Font(bold=True)
_TITRE = Font(bold=True, size=14)
_SOUS_TITRE = Font(bold=True, size=12)
_ENTETE = PatternFill("solid", fgColor="DDE4EE")
_TOTAL = PatternFill("solid", fgColor="F2F2F2")
_SAISIE = PatternFill("solid", fgColor="FFF2CC")
_AUTRE_EXERCICE = PatternFill("solid", fgColor="E2EFDA")
_BAS = Border(bottom=Side(style="thin", color="999999"))

COLONNES_VIREMENTS = ["Employé", "Date", "Banque", "Montant viré", "Exercice", "Part salaire", "Autre (frais, prêt)",
                      "Votre classement", "Libellé bancaire", "Pièce / écriture", "Imputation",
                      "Contrôle (votre classeur)", "Preuve (fichier)"]
_LARGEURS = [30, 12, 12, 14, 10, 14, 14, 26, 34, 34, 60, 18, 28]


def chemin_sortie(annee: int) -> Path:
    return config.DOSSIER_SORTIES_SALAIRES / f"Reconciliation_salaires_{annee}.xlsx"


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _somme(fiche: dict | None, employe: str, exercice: int) -> float:
    if not fiche:
        return 0.0
    return _r(sum(v["part_salaire"] or 0 for v in fiche["virements"]
                  if v["employe"] == employe and v["exercice"] == exercice))


def _employes(fiche: dict) -> list[str]:
    noms = [d["employe"] for d in fiche["du"]]
    for v in fiche["virements"]:
        if v["employe"] not in noms:
            noms.append(v["employe"])
    return noms


def _du(fiche: dict, employe: str) -> float:
    return _r(sum(d["net_du"] or 0 for d in fiche["du"] if d["employe"] == employe))


def _selon_classeur(fiche: dict, employe: str) -> float | None:
    """Reste de l'année précédente annoncé par le classeur de paie (onglet FRAIS), None s'il n'a pas été lu."""
    valeurs = [d.get("reste_prec_classeur") for d in fiche["du"] if d["employe"] == employe]
    valeurs = [v for v in valeurs if v is not None]
    return _r(sum(valeurs)) if valeurs else None


def _frais_lu(fiche: dict) -> bool:
    return any(d.get("reste_prec_classeur") is not None for d in fiche["du"])


def resume(annee: int, fiche_n: dict, fiche_prec: dict | None, fiche_suiv: dict | None) -> dict:
    lignes = []
    for e in _employes(fiche_n):
        du, paye = _du(fiche_n, e), _somme(fiche_n, e, annee)
        reporte = _r(du - paye)
        suivant = _somme(fiche_suiv, e, annee)
        lignes.append({"employe": e, "du": du, "paye": paye, "reporte": reporte, "paye_suivant": suivant,
                       "ecart": _r(reporte - suivant)})
    total = {k: _r(sum(l[k] for l in lignes)) for k in ("du", "paye", "reporte", "paye_suivant", "ecart")}
    restes = None
    if fiche_prec is not None:
        restes = []
        noms = _employes(fiche_prec) + [d["employe"] for d in fiche_n["du"] if d.get("reste_prec_classeur")
                                        and d["employe"] not in _employes(fiche_prec)]
        for e in noms:
            reporte = _r(_du(fiche_prec, e) - _somme(fiche_prec, e, annee - 1))
            paye = _somme(fiche_n, e, annee - 1)
            selon = _selon_classeur(fiche_n, e)
            if reporte or paye or selon:
                restes.append({"employe": e, "reporte": reporte, "selon_classeur": selon, "paye": paye,
                               "ecart": _r(reporte - paye)})
    r = {"annee": annee, "lignes": lignes, "total": total, "restes_prec": restes}
    r["points"] = points(r, fiche_n, fiche_suiv)
    return r


def _f(x: float) -> str:
    return f"{x:,.2f}".replace(",", "'")


def points(r: dict, fiche_n: dict, fiche_suiv: dict | None) -> list[dict]:
    annee = r["annee"]
    out = []
    if fiche_suiv is None:
        out.append({"employe": "Tous", "point": f"Aucune fiche {annee + 1} : la colonne « Payé en {annee + 1} » est vide, "
                                                 f"l'écart égale donc le reporté. Déposer le classeur de paie {annee + 1}."})
    for l in r["lignes"]:
        if l["ecart"] > 0:
            out.append({"employe": l["employe"], "point": f"Reste à payer {_f(l['ecart'])} sur le salaire {annee}."})
        elif l["ecart"] < 0:
            out.append({"employe": l["employe"], "point": f"Payé en trop {_f(-l['ecart'])} sur le salaire {annee}."})
    for x in r["restes_prec"] or []:
        if x["ecart"]:
            sens = "reste à payer" if x["ecart"] > 0 else "payé en trop"
            out.append({"employe": x["employe"],
                        "point": f"Salaire {annee - 1} : {sens} {_f(abs(x['ecart']))} après les paiements de {annee}."})
        if _frais_lu(fiche_n) and abs((x["selon_classeur"] or 0) - x["reporte"]) >= 0.005:
            out.append({"employe": x["employe"], "point": (
                f"Reste {annee - 1} : {_f(x['reporte'])} selon la fiche {annee - 1}, {_f(x['selon_classeur'] or 0)} "
                f"selon votre classeur (onglet FRAIS). Vérifier lequel est juste.")})
    for d in fiche_n["du"]:
        if d.get("note_classeur"):
            out.append({"employe": d["employe"], "point": d["note_classeur"]})
    for d in fiche_n["du"]:
        if d.get("remarque", "").startswith("Contrôle"):
            out.append({"employe": d["employe"], "point": d["remarque"]})
    for v in fiche_n["virements"]:
        jour = v["date"].strftime("%d.%m.%Y") if isinstance(v["date"], datetime) else ""
        quoi = f"{_f(v['montant'])} du {jour}"
        typ = (v.get("type") or "").lower()
        if typ.startswith("prêt") or typ.startswith("pret"):
            out.append({"employe": v["employe"], "point": f"Prêt de {quoi} : exclu du salaire. Vérifier son remboursement."})
        elif "régularisation" in typ and not v["part_salaire"]:
            out.append({"employe": v["employe"],
                        "point": f"{quoi}, marqué « {v['type']} », classé hors salaire : {v.get('imputation', '')}"})
        elif (v.get("imputation") or "").startswith("Découpage") or "À vérifier" in (v.get("imputation") or ""):
            out.append({"employe": v["employe"], "point": f"Virement de {quoi} : {v['imputation']}"})
    out.extend(dict(p) for p in fiche_n.get("points", []) if p.get("point"))
    return out


# ------------------------------------------------------------------ classeur

def _entetes(ws, ligne: int, noms: list[str], largeurs: list[int] | None = None) -> None:
    for i, nom in enumerate(noms, 1):
        c = ws.cell(ligne, i, nom)
        c.font, c.fill, c.border = _GRAS, _ENTETE, _BAS
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if largeurs:
            ws.column_dimensions[get_column_letter(i)].width = largeurs[i - 1]


def _total(ws, r: int, debut: int, fin: int, cols, ncols: int, libelle: str = "Total") -> None:
    ws.cell(r, 1, libelle).font = _GRAS
    for c in cols:
        lettre = get_column_letter(c)
        cell = ws.cell(r, c, f"=SUM({lettre}{debut}:{lettre}{fin})" if fin >= debut else 0)
        cell.number_format, cell.font = CHF, _GRAS
    for c in range(1, ncols + 1):
        ws.cell(r, c).fill = _TOTAL


def _titre(ws, titre: str, note: str) -> None:
    ws["A1"], ws["A1"].font = titre, _TITRE
    ws["A2"] = note


def _feuille_virements(wb, titre: str, sous_titre: str, note: str, virements: list[dict], ordre: list[str],
                       exercice_principal: int) -> None:
    ws = wb.create_sheet(titre)
    _titre(ws, sous_titre, note)
    _entetes(ws, 4, COLONNES_VIREMENTS, _LARGEURS)
    ws.freeze_panes = "A5"
    r = 5
    noms = ordre + sorted({v["employe"] for v in virements} - set(ordre))
    for nom in noms:
        mes = sorted((v for v in virements if v["employe"] == nom), key=lambda v: v["date"] or datetime.max)
        if not mes:
            continue
        debut = r
        for v in mes:
            valeurs = [nom, v["date"], v.get("banque"), v["montant"], v["exercice"], v["part_salaire"], f"=D{r}-F{r}",
                       v.get("type"), v.get("libelle"), v.get("piece"), v.get("imputation"), v.get("controle"),
                       v.get("preuve")]
            for c, val in enumerate(valeurs, 1):
                ws.cell(r, c, val if val != "" else None)
            ws.cell(r, 2).number_format = "DD.MM.YYYY"
            for c in (4, 6, 7):
                ws.cell(r, c).number_format = CHF
            if v.get("imputation"):
                ws.cell(r, 11).font = Font(color="9C5700")
            if v["exercice"] != exercice_principal:
                for c in range(1, 13):
                    ws.cell(r, c).fill = _AUTRE_EXERCICE
            ws.cell(r, 13).fill = _SAISIE
            r += 1
        _total(ws, r, debut, r - 1, (4, 6, 7), 13, f"Sous-total {nom}")
        r += 2


def ecrire(annee: int, fiche_n: dict, fiche_prec: dict | None, fiche_suiv: dict | None) -> Path:
    res = resume(annee, fiche_n, fiche_prec, fiche_suiv)
    n, prec, suiv = annee, annee - 1, annee + 1
    employes = _employes(fiche_n)
    wb = openpyxl.Workbook()
    syn = wb.active
    syn.title = "Synthèse"

    du = wb.create_sheet(f"Dû {n}")
    _titre(du, f"Salaire net dû pour l'exercice {n}", "Source : votre classeur de paie, repris dans la fiche de l'exercice.")
    _entetes(du, 4, ["Employé", f"Net dû {n} (CHF)", "Source (cellule)", "Remarque",
                     f"Reste {prec} selon votre classeur (FRAIS)", "Note de votre classeur"], [30, 18, 20, 60, 20, 80])
    for i, d in enumerate(fiche_n["du"], 5):
        for c, val in enumerate([d["employe"], d["net_du"], d["source"], d.get("remarque") or None,
                                 d.get("reste_prec_classeur"), d.get("note_classeur") or None], 1):
            du.cell(i, c, val)
        du.cell(i, 2).number_format = du.cell(i, 5).number_format = CHF
        du.cell(i, 6).alignment = Alignment(wrap_text=True, vertical="top")
    _total(du, 5 + len(fiche_n["du"]), 5, 4 + len(fiche_n["du"]), (2, 5), 6)

    if fiche_prec is not None:
        rp = wb.create_sheet(f"Reste {prec}")
        _titre(rp, f"Salaire {prec} resté dû à fin {prec}",
               f"Source : fiche {prec} (net dû et virements de l'exercice {prec}).")
        _entetes(rp, 4, ["Employé", f"Dû {prec}", f"Payé en {prec}", f"Reporté de {prec}"], [30, 16, 16, 18])
        i = 5
        for e in _employes(fiche_prec):
            rp.cell(i, 1, e)
            rp.cell(i, 2, _du(fiche_prec, e))
            rp.cell(i, 3, _somme(fiche_prec, e, prec))
            rp.cell(i, 4, f"=ROUND(B{i}-C{i},2)")
            for c in (2, 3, 4):
                rp.cell(i, c).number_format = CHF
            i += 1
        _total(rp, i, 5, i - 1, (2, 3, 4), 4)

    _feuille_virements(wb, f"Payé en {n}", f"Virements de {n} aux employés", (
        f"Tous les virements {n} aux employés. « Exercice » indique l'année de salaire réglée (lignes vertes : autre "
        f"exercice). « Part salaire » est ce qui compte dans la synthèse. La colonne « Preuve » (fond jaune) est à remplir."),
        fiche_n["virements"], employes, n)
    suivants = [v for v in (fiche_suiv or {"virements": []})["virements"] if v["exercice"] == n]
    _feuille_virements(wb, f"Payé en {suiv}", f"Virements de {suiv} pour le solde des salaires {n}", (
        f"Virements de {suiv} qui règlent le salaire {n} (fiche {suiv}, exercice = {n})." if fiche_suiv is not None else
        f"Aucune fiche {suiv} pour l'instant : déposer le classeur de paie {suiv} dans entrees/08_salaires puis régénérer."),
        suivants, employes, n)

    # Synthèse : formules uniquement
    _titre(syn, f"Salaires {n} – réconciliation par employé", (
        f"Montants nets en CHF. Chaque colonne renvoie à sa feuille. Reporté = Dû − Payé en {n}. "
        f"Écart = Reporté − Payé en {suiv} (positif : reste à payer ; négatif : payé en trop)."))
    syn["A2"].alignment = Alignment(wrap_text=True)
    syn.merge_cells("A2:F2")
    syn.row_dimensions[2].height = 35
    _entetes(syn, 4, ["Employé", f"Dû {n}", f"Payé en {n}", f"Reporté à {suiv}", f"Payé en {suiv}", "Écart"],
             [30, 16, 16, 16, 16, 14])
    pn, ps = f"'Payé en {n}'", f"'Payé en {suiv}'"
    r = 5
    for e in employes:
        syn.cell(r, 1, e)
        syn.cell(r, 2, f"=SUMIFS('Dû {n}'!$B:$B,'Dû {n}'!$A:$A,$A{r})")
        syn.cell(r, 3, f"=SUMIFS({pn}!$F:$F,{pn}!$A:$A,$A{r},{pn}!$E:$E,{n})")
        syn.cell(r, 4, f"=ROUND(B{r}-C{r},2)")
        syn.cell(r, 5, f"=SUMIFS({ps}!$F:$F,{ps}!$A:$A,$A{r},{ps}!$E:$E,{n})")
        syn.cell(r, 6, f"=ROUND(D{r}-E{r},2)")
        for c in range(2, 7):
            syn.cell(r, c).number_format = CHF
        r += 1
    _total(syn, r, 5, r - 1, range(2, 7), 6)
    if res["restes_prec"] is not None:
        r += 3
        syn.cell(r, 1, f"Restes {prec} payés en {n}").font = _SOUS_TITRE
        r += 1
        frais = _frais_lu(fiche_n)
        if frais:
            _entetes(syn, r, ["Employé", f"Reporté de {prec} (fiche {prec})", "Selon votre classeur (FRAIS)",
                              f"Payé en {n}", "Écart"])
        else:
            _entetes(syn, r, ["Employé", f"Reporté de {prec}", f"Payé en {n}", "Écart"])
        r += 1
        debut = r
        paye = 4 if frais else 3
        for x in res["restes_prec"]:
            syn.cell(r, 1, x["employe"])
            syn.cell(r, 2, f"=SUMIFS('Reste {prec}'!$D:$D,'Reste {prec}'!$A:$A,$A{r})")
            if frais:
                syn.cell(r, 3, f"=SUMIFS('Dû {n}'!$E:$E,'Dû {n}'!$A:$A,$A{r})")
            lp = get_column_letter(paye)
            syn.cell(r, paye, f"=SUMIFS({pn}!$F:$F,{pn}!$A:$A,$A{r},{pn}!$E:$E,{prec})")
            syn.cell(r, paye + 1, f"=ROUND(B{r}-{lp}{r},2)")
            for c in range(2, paye + 2):
                syn.cell(r, c).number_format = CHF
            r += 1
        _total(syn, r, debut, r - 1, range(2, paye + 2), paye + 1)
    syn.freeze_panes = "A5"
    syn.page_setup.orientation = "landscape"
    syn.page_setup.fitToWidth = 1

    pv = wb.create_sheet("Points à vérifier")
    _titre(pv, "Points à vérifier avant envoi à la fiduciaire", "")
    _entetes(pv, 3, ["Employé", "Point"], [30, 120])
    for i, p in enumerate(res["points"], 4):
        pv.cell(i, 1, p["employe"])
        pv.cell(i, 2, p["point"]).alignment = Alignment(wrap_text=True, vertical="top")

    chemin = chemin_sortie(annee)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    try:
        wb.save(chemin)
    except PermissionError as e:
        raise FichierOuvert(f"Ferme {chemin.name} dans Excel, puis recommence.") from e
    return chemin
