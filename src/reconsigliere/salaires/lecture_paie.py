"""Lecteur du classeur de paie au format 2025 (onglets EMPLOYES, ANNEE, PAYé, Bank Transactions AAAA).

Rend le contenu d'une fiche (voir fiche.py) : le net dû par employé et chaque virement avec son exercice et sa part de salaire.
Les règles d'imputation sont décrites dans docs/modules/salaires/lecture_paie.md.
"""

from __future__ import annotations

import re
from datetime import datetime
from itertools import combinations
from pathlib import Path

import openpyxl

from .. import config
from . import fiche

TOLERANCE = 0.005
MOIS = ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"]


class FormatInconnu(Exception):
    """Le classeur n'a pas la forme attendue."""


def _texte(v) -> str:
    return "" if v is None else str(v).strip()


def _num(v) -> float | None:
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    return None


def _date(v) -> datetime | None:
    if isinstance(v, datetime):
        return v
    t = _texte(v)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(t[:19] if "%H" in fmt else t[:10], fmt)
        except ValueError:
            continue
    return None


def _egal(a: float, b: float) -> bool:
    return abs(a - b) < TOLERANCE


def exercice_du_classeur(chemin: Path) -> int | None:
    """Exercice lu dans ANNEE!B1, ou None si le classeur n'a pas cette forme."""
    try:
        wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    except Exception:  # noqa: BLE001 - fichier illisible : pas un classeur de paie
        return None
    try:
        if "ANNEE" not in wb.sheetnames:
            return None
        v = wb["ANNEE"]["B1"].value
        return int(v) if isinstance(v, (int, float)) or _texte(v).isdigit() else None
    finally:
        wb.close()


def trouver_classeur(annee: int) -> Path | None:
    """Premier classeur de paie de entrees/08_salaires dont l'exercice vaut `annee`."""
    dossier = config.DOSSIER_SALAIRES
    if not dossier.is_dir():
        return None
    for chemin in sorted(dossier.glob("*.xlsx")):
        if chemin.name.startswith("~$"):
            continue
        if exercice_du_classeur(chemin) == annee:
            return chemin
    return None


def _onglet(wb, nom: str, debut: bool = False):
    for n in wb.sheetnames:
        if (n.startswith(nom) if debut else n == nom):
            return wb[n]
    raise FormatInconnu(f"onglet {nom} introuvable : ce classeur n'a pas la forme du classeur de paie 2025.")


def _employes(wb) -> list[str]:
    ws = _onglet(wb, "EMPLOYES")
    noms = []
    for r in ws.iter_rows(min_row=7, values_only=True):
        nom = _texte(r[1] if len(r) > 1 else None)
        if nom and nom not in noms:
            noms.append(nom)
    return noms


def _annee(wb, employes: list[str]) -> tuple[int, dict, dict]:
    """Exercice, net dû {employé: (montant, cellule)} et « Versé selon PAYE » {employé: montant}."""
    ws = _onglet(wb, "ANNEE")
    try:
        annee = int(ws["B1"].value)
    except (TypeError, ValueError) as e:
        raise FormatInconnu("exercice introuvable dans la cellule B1 de l'onglet ANNEE.") from e
    entetes = {_texte(c.value): c.column for c in ws[5] if c.value}
    if "Net définitif" not in entetes:
        raise FormatInconnu("colonne « Net définitif » introuvable en ligne 5 de l'onglet ANNEE.")
    col_net, col_verse = entetes["Net définitif"], entetes.get("Versé selon PAYE")
    du, verse = {}, {}
    for row in ws.iter_rows(min_row=6):
        nom = next((_texte(c.value) for c in reversed(row) if _texte(c.value) in employes), None)
        if not nom or nom in du:
            continue
        cell = ws.cell(row[0].row, col_net)
        du[nom] = (_num(cell.value) or 0.0, f"ANNEE, {cell.coordinate}")
        if col_verse:
            verse[nom] = _num(ws.cell(row[0].row, col_verse).value) or 0.0
    return annee, du, verse


def _reference_paye(wb, employes: list[str]) -> dict:
    """Montants de l'onglet PAYé par employé : salaires (V1-V3), frais et hors période, mois par mois."""
    ws = _onglet(wb, "PAYé")
    colonnes = _colonnes_mois(ws)
    ref = {e: {"salaires": [], "extras": []} for e in employes}
    courant = None
    for row in ws.iter_rows(min_row=1):
        a, code = _texte(row[0].value), _texte(row[1].value) if len(row) > 1 else ""
        m = re.match(r"^E\d+\s+—\s+(.+)$", a)
        if m:
            courant = m.group(1).strip() if m.group(1).strip() in ref else None
            continue
        if courant is None or not code:
            continue
        for mois, col in colonnes.items():
            montant = _num(ws.cell(row[0].row, col).value)
            if not montant:
                continue
            if code in ("V1", "V2", "V3"):
                ref[courant]["salaires"].append(montant)
            elif code in ("PAYE FRAIS", "PAYE HP"):
                ref[courant]["extras"].append({"montant": montant, "genre": "frais" if code == "PAYE FRAIS" else "hp",
                                               "mois": mois, "utilise": False})
    return ref


def _colonnes_mois(ws) -> dict:
    colonnes = {}
    for row in ws.iter_rows(min_row=1, max_row=20):
        for c in row:
            if _texte(c.value) in MOIS and _texte(c.value) not in colonnes:
                colonnes[_texte(c.value)] = c.column
        if len(colonnes) == 12:
            break
    return colonnes


def _hors_periode_du(wb, employes: list[str]) -> dict | None:
    """Onglet FRAIS (le dû) : somme des lignes HP (frais/salaire hors période) par employé. None sans onglet FRAIS."""
    if "FRAIS" not in wb.sheetnames:
        return None
    ws = wb["FRAIS"]
    colonnes = _colonnes_mois(ws)
    du = {e: 0.0 for e in employes}
    courant = None
    for row in ws.iter_rows(min_row=1):
        a, code = _texte(row[0].value), _texte(row[1].value) if len(row) > 1 else ""
        m = re.match(r"^E\d+\s+—\s+(.+)$", a)
        if m:
            courant = m.group(1).strip() if m.group(1).strip() in du else None
            continue
        if courant and code == "HP":
            du[courant] = round(du[courant] + sum(_num(ws.cell(row[0].row, c).value) or 0.0
                                                  for c in colonnes.values()), 2)
    return du


def _notes(wb, employes: list[str]) -> dict:
    """Textes des lignes « Nom — Note » des onglets PAYé et FRAIS, avec l'onglet et le mois."""
    notes = {e: [] for e in employes}
    for onglet in ("PAYé", "FRAIS"):
        if onglet not in wb.sheetnames:
            continue
        ws = wb[onglet]
        mois = {col: nom for nom, col in _colonnes_mois(ws).items()}
        for row in ws.iter_rows(min_row=1):
            m = re.match(r"^(.+?)\s+—\s+Note$", _texte(row[0].value))
            if not m or m.group(1).strip() not in notes:
                continue
            for c in row[1:]:
                if isinstance(c.value, str) and c.value.strip() and not c.value.startswith("="):
                    ou = f"{onglet}, {mois[c.column]}" if c.column in mois else onglet
                    notes[m.group(1).strip()].append(f"Note de votre classeur ({ou}) : {c.value.strip()}")
    return {e: " | ".join(t) for e, t in notes.items()}


def _colonnes_banque(ws) -> dict:
    noms = {"date": "Date", "employe": "Employé", "type": "Type", "montant": "Montant (CHF)", "libelle": "Libellé",
            "banque": "Banque", "piece": "Écriture comptable", "controle": "Rapprochement fiche"}
    entetes = {_texte(c.value): c.column - 1 for c in ws[1] if c.value}
    manquantes = [v for k, v in noms.items() if v not in entetes and k in ("date", "employe", "montant")]
    if manquantes:
        raise FormatInconnu(f"colonnes {', '.join(manquantes)} introuvables dans l'onglet {ws.title}.")
    return {k: entetes.get(v) for k, v in noms.items()}


def _extra_exact(extras: list[dict], montant: float, genre: str | None = None) -> dict | None:
    return next((x for x in extras if not x["utilise"] and _egal(x["montant"], montant)
                 and (genre is None or x["genre"] == genre)), None)


def _decrire(x: dict) -> str:
    return f"{x['montant']:.2f} de {'frais' if x['genre'] == 'frais' else 'solde de l’année précédente'} (PAYé, {x['mois']})"


def _imputer(v: dict, annee: int, ref: dict) -> None:
    """Règles d'imputation, dans l'ordre (voir la conception)."""
    typ, montant = v["type"].lower(), v["montant"]
    extras = ref.get(v["employe"], {"extras": [], "salaires": []})
    v["exercice"], v["part_salaire"], v["imputation"] = annee, montant, ""

    if typ.startswith("prêt") or typ.startswith("pret"):
        v["part_salaire"], v["imputation"] = 0.0, "Prêt à l'employé : ni salaire ni frais."
        return
    if typ.startswith("remboursement"):
        x = _extra_exact(extras["extras"], montant, "frais")
        if x:
            x["utilise"] = True
        v["part_salaire"], v["imputation"] = 0.0, "Remboursement de frais."
        return
    x = _extra_exact(extras["extras"], montant, "frais")
    if x:
        x["utilise"] = True
        v["part_salaire"] = 0.0
        v["imputation"] = f"Frais (PAYé, {x['mois']})" + (
            f", bien que marqué « {v['type']} »." if "régularisation" in typ or "salaire" in typ else ".")
        return
    m = re.search(r"r[ée]gularisation\s+(\d{4})", typ)
    x = _extra_exact(extras["extras"], montant, "hp")
    if m or x:
        if x:
            x["utilise"] = True
        v["exercice"] = int(m.group(1)) if m else annee - 1
        v["imputation"] = f"Solde du salaire {v['exercice']}."
        return
    v["_a_decouper"] = True


def _decouper(v: dict, annee: int, ref: dict) -> None:
    """Virement = salaire PAYé (ou rien) + un ou deux montants de frais / hors période non encore utilisés."""
    del v["_a_decouper"]
    montant = v["montant"]
    r = ref.get(v["employe"], {"extras": [], "salaires": []})
    if any(_egal(s, montant) for s in r["salaires"]):
        return
    libres = [x for x in r["extras"] if not x["utilise"]]
    for taille in (1, 2):
        for combo in combinations(libres, taille):
            reste = round(montant - sum(x["montant"] for x in combo), 2)
            if not (abs(reste) < TOLERANCE or any(_egal(s, reste) for s in r["salaires"])):
                continue
            for x in combo:
                x["utilise"] = True
            hp = round(sum(x["montant"] for x in combo if x["genre"] == "hp"), 2)
            details = " + ".join(_decrire(x) for x in combo)
            if abs(reste) < TOLERANCE and hp:
                v["exercice"], v["part_salaire"] = annee - 1, hp
                v["imputation"] = f"Découpage : {details}."
            else:
                v["part_salaire"] = max(reste, 0.0)
                v["imputation"] = f"Découpage : salaire {reste:.2f} + {details}."
                if hp:
                    v["imputation"] += " À vérifier : le solde de l'année précédente n'est pas compté."
            return


def lire(chemin: Path) -> dict:
    """Lit le classeur de paie et rend {annee, du, virements, points, controles, verse_paye}."""
    try:
        wb = openpyxl.load_workbook(chemin, data_only=True)
    except Exception as e:  # noqa: BLE001
        raise FormatInconnu(f"{Path(chemin).name} illisible : {e}") from e
    if "ANNEE" not in wb.sheetnames:
        raise FormatInconnu("onglet ANNEE introuvable : ce classeur n'a pas la forme du classeur de paie 2025.")
    employes = _employes(wb)
    annee, du_brut, verse = _annee(wb, employes)
    ref = _reference_paye(wb, employes)
    ws = _onglet(wb, "Bank Transactions", debut=True)
    col = _colonnes_banque(ws)

    virements = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        get = lambda k: row[col[k]] if col.get(k) is not None and col[k] < len(row) else None  # noqa: E731
        employe, d, montant = _texte(get("employe")), _date(get("date")), _num(get("montant"))
        if employe not in employes or d is None or montant is None:
            continue
        virements.append({"id": "", "employe": employe, "date": d, "banque": _texte(get("banque")), "montant": montant,
                          "exercice": annee, "part_salaire": montant, "type": _texte(get("type")),
                          "libelle": _texte(get("libelle")), "piece": _texte(get("piece")), "imputation": "",
                          "controle": _texte(get("controle")), "preuve": ""})
    virements.sort(key=lambda v: (employes.index(v["employe"]), v["date"]))
    for v in virements:
        _imputer(v, annee, ref)
    for v in virements:
        if v.get("_a_decouper"):
            _decouper(v, annee, ref)
    fiche.identifiants(virements)

    hp, notes = _hors_periode_du(wb, employes), _notes(wb, employes)
    du = [{"employe": e, "net_du": du_brut[e][0], "source": du_brut[e][1], "remarque": "",
           "reste_prec_classeur": None if hp is None else hp[e], "note_classeur": notes[e]}
          for e in employes if e in du_brut]
    controles = []
    for e in employes:
        if e not in verse:
            continue
        total = round(sum(v["part_salaire"] for v in virements if v["employe"] == e and v["exercice"] == annee), 2)
        if not _egal(total, verse[e]):
            controles.append({"employe": e, "point": (
                f"Virements de salaire {annee} : {total:,.2f} ; votre classeur (Versé selon PAYE) : {verse[e]:,.2f} ; "
                f"écart {total - verse[e]:,.2f}. Vérifier le classement des virements dans la fiche.").replace(",", "'")})
    for c in controles:
        for d in du:
            if d["employe"] == c["employe"]:
                d["remarque"] = "Contrôle : " + c["point"]
    return {"annee": annee, "du": du, "virements": virements, "points": [], "controles": controles, "verse_paye": verse}
