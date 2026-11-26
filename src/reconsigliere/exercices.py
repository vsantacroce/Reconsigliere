"""Référentiel de la société, versionné par exercice.

Chaque exercice a son dossier entrees/06_societe/exercices/AAAA avec :

- referentiel.xlsx : les listes de l'exercice (plan comptable, partenaires et leur compte habituel,
  brevets, projets, revenus) et l'onglet Changements, qui garde chaque demande datée ;
- etat.json : ouvert ou validé, date de validation, empreinte du référentiel validé et historique.

Cycle :
1. construire(2024) remplit le référentiel du premier exercice à partir des fichiers
   (imports/2024 pour le plan comptable et le grand livre, classeur des brevets, societe.xlsx) ;
2. valider(2024) fige 2024 (lecture seule + empreinte SHA-256) et ouvre 2025 comme copie ;
3. pendant 2025, demander_changement() ajoute, modifie ou retire un élément et l'inscrit dans Changements ;
4. ecarts(2025) compare 2025 en cours à 2024 validé ;
5. valider(2025) fige 2025 et ouvre 2026, etc.
rouvrir(annee, motif) défige un exercice validé ; le motif reste dans l'historique.

Les fichiers normalisés du pipeline d'import sont lus dans entrees/06_societe/imports/AAAA :
onglets PlanComptable(code, nom, type) et GrandLivre(date, compte, libelle_compte, piece,
partenaire, libelle, debit, credit).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from . import societe

OUVERT = "ouvert"
VALIDE = "validé"

# Listes du référentiel : nom de l'onglet -> (colonne clé, colonnes)
LISTES: dict[str, tuple[str, list[str]]] = {
    "PlanComptable": ("code", ["code", "nom", "type"]),
    "Partenaires": ("partenaire", ["partenaire", "compte", "libelle_compte", "occurrences", "part"]),
    "Brevets": ("id", ["id", "famille", "titre", "numero", "pays", "depot", "delivrance", "abandon",
                       "titulaire", "statut"]),
    "Projets": ("projet", ["projet", "capitalisable", "brevets", "debut", "fin", "statut", "montant_active"]),
    "Revenus": ("source", ["source", "client", "type", "contrat", "debut", "fin", "montant_annuel",
                           "compte", "statut"]),
}
NOMS_LISTES = {
    "PlanComptable": "Plan comptable", "Partenaires": "Partenaires", "Brevets": "Brevets",
    "Projets": "Projets", "Revenus": "Revenus",
}
COLONNES_CHANGEMENTS = ["date", "action", "liste", "cle", "champ", "avant", "apres", "motif", "saisi_le"]
ACTIONS = ["ajout", "modification", "retrait"]


class ExerciceVerrouille(Exception):
    """L'exercice est validé : il faut le rouvrir avec un motif avant de le modifier."""


class ExerciceAbsent(Exception):
    pass


# ---------------------------------------------------------------- chemins et état

def dossier_exercices() -> Path:
    return societe.dossier_societe() / "exercices"


def dossier_imports(annee: int) -> Path:
    return societe.dossier_societe() / "imports" / str(annee)


def dossier(annee: int) -> Path:
    return dossier_exercices() / str(annee)


def fichier_referentiel(annee: int) -> Path:
    return dossier(annee) / "referentiel.xlsx"


def _fichier_etat(annee: int) -> Path:
    return dossier(annee) / "etat.json"


def lister() -> list[int]:
    if not dossier_exercices().exists():
        return []
    return sorted(int(p.name) for p in dossier_exercices().iterdir()
                  if p.is_dir() and re.fullmatch(r"\d{4}", p.name) and (p / "referentiel.xlsx").exists())


def lire_etat(annee: int) -> dict:
    try:
        return json.loads(_fichier_etat(annee).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"exercice": annee, "statut": OUVERT, "historique": []}


def _ecrire_etat(annee: int, etat: dict) -> None:
    chemin = _fichier_etat(annee)
    _rendre_modifiable(chemin)
    chemin.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")


def est_valide(annee: int) -> bool:
    return lire_etat(annee).get("statut") == VALIDE


def exercice_courant() -> int | None:
    """Le dernier exercice ouvert, sinon le dernier exercice tout court."""
    annees = lister()
    ouverts = [a for a in annees if not est_valide(a)]
    return (ouverts or annees or [None])[-1]


def exercice_pour(quand: date) -> int | None:
    """L'exercice qui couvre une date, sinon le plus proche avant elle, sinon le premier."""
    annees = lister()
    if not annees:
        return None
    if quand.year in annees:
        return quand.year
    avant = [a for a in annees if a < quand.year]
    return avant[-1] if avant else annees[0]


def empreinte(chemin: Path) -> str:
    return hashlib.sha256(Path(chemin).read_bytes()).hexdigest()


def _rendre_lecture_seule(chemin: Path) -> None:
    if chemin.exists():
        os.chmod(chemin, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def _rendre_modifiable(chemin: Path) -> None:
    if chemin.exists():
        os.chmod(chemin, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH)


def _maintenant() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- lecture et écriture du référentiel

def _valeur_cellule(v):
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def lire(annee: int) -> dict[str, list[dict]]:
    """Toutes les listes de l'exercice, plus « Changements »."""
    chemin = fichier_referentiel(annee)
    if not chemin.exists():
        raise ExerciceAbsent(f"Aucun référentiel pour {annee}.")
    wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    resultat: dict[str, list[dict]] = {}
    for nom in [*LISTES, "Changements"]:
        lignes: list[dict] = []
        if nom in wb.sheetnames:
            rangs = list(wb[nom].iter_rows(values_only=True))
            if rangs:
                entete = [str(c).strip() if c is not None else "" for c in rangs[0]]
                for r in rangs[1:]:
                    if not any(v not in (None, "") for v in r):
                        continue
                    lignes.append({entete[i]: _valeur_cellule(r[i]) for i in range(min(len(entete), len(r)))
                                   if entete[i]})
        resultat[nom] = lignes
    wb.close()
    return resultat


def _ecrire(annee: int, listes: dict[str, list[dict]]) -> Path:
    chemin = fichier_referentiel(annee)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    _rendre_modifiable(chemin)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for nom, (cle, colonnes) in [*LISTES.items(), ("Changements", ("", COLONNES_CHANGEMENTS))]:
        ws = wb.create_sheet(nom)
        lignes = listes.get(nom, [])
        extra = [c for l in lignes for c in l if c not in colonnes]
        entete = colonnes + sorted(set(extra), key=extra.index)
        ws.append(entete)
        if cle:
            lignes = sorted(lignes, key=lambda l: _cle_tri(l.get(cle)))
        for l in lignes:
            ws.append([l.get(c) for c in entete])
        for i, c in enumerate(entete, start=1):
            ws.cell(row=1, column=i).font = Font(bold=True)
            ws.column_dimensions[get_column_letter(i)].width = max(12, min(40, len(c) + 6))
        ws.freeze_panes = "A2"
    wb.save(chemin)
    return chemin


def _cle_tri(v) -> tuple:
    texte = "" if v is None else str(v)
    return (0, texte.zfill(12)) if texte.isdigit() else (1, societe._norm(texte))


# ---------------------------------------------------------------- construction depuis les fichiers

def _onglet_normalise(wb, nom: str) -> list[dict]:
    """Lit un onglet du pipeline d'import (noms de colonnes en minuscules sans accents)."""
    cible = societe._norm(nom).replace(" ", "")
    for ws in wb.worksheets:
        if societe._norm(ws.title).replace(" ", "") == cible:
            rangs = list(ws.iter_rows(values_only=True))
            if not rangs:
                return []
            entete = [societe._norm(c).replace(" ", "_") for c in rangs[0]]
            return [{entete[i]: r[i] for i in range(min(len(entete), len(r))) if entete[i]}
                    for r in rangs[1:] if any(v not in (None, "") for v in r)]
    return []


def lire_imports(annee: int) -> tuple[list[dict], list[dict]]:
    """Plan comptable et lignes de grand livre déposés dans imports/AAAA."""
    plan: dict[str, dict] = {}
    grand_livre: list[dict] = []
    d = dossier_imports(annee)
    if not d.exists():
        return [], []
    for chemin in sorted(d.rglob("*.xls[xm]")):
        if chemin.name.startswith("~$"):
            continue
        wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
        for l in _onglet_normalise(wb, "PlanComptable"):
            code = _code(l.get("code"))
            if code:
                plan[code] = {"code": code, "nom": societe._texte(l.get("nom")),
                              "type": societe._texte(l.get("type"))}
        for l in _onglet_normalise(wb, "GrandLivre"):
            exercice = l.get("exercice")
            if exercice not in (None, "") and str(exercice).strip() != str(annee):
                continue
            grand_livre.append(l)
        wb.close()
    return list(plan.values()), grand_livre


def _code(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def partenaires_depuis_grand_livre(lignes: list[dict], plan: dict[str, str]) -> list[dict]:
    """Pour chaque partenaire, le compte de contrepartie le plus fréquent (hors banque et tiers)."""
    par_partenaire: dict[str, Counter] = defaultdict(Counter)
    noms: dict[str, str] = {}
    for l in lignes:
        partenaire = societe._texte(l.get("partenaire"))
        compte = _code(l.get("compte"))
        if not partenaire or not compte or partenaire in {"/", "-"}:
            continue
        if _compte_technique(compte):
            continue
        cle = societe._norm(partenaire)
        noms.setdefault(cle, partenaire)
        par_partenaire[cle][compte] += 1
        if compte not in plan and l.get("libelle_compte"):
            plan[compte] = societe._texte(l.get("libelle_compte"))
    resultat = []
    for cle, comptes in par_partenaire.items():
        compte, n = comptes.most_common(1)[0]
        total = sum(comptes.values())
        resultat.append({"partenaire": noms[cle], "compte": compte, "libelle_compte": plan.get(compte, ""),
                         "occurrences": total, "part": round(n / total, 2)})
    return resultat


def _compte_technique(compte: str) -> bool:
    """Comptes qui ne disent rien de la nature de la dépense : liquidités, débiteurs, créanciers, TVA.

    Plan comptable suisse PME : 10xx liquidités, 1100 débiteurs, 1170/1171 impôt préalable,
    2000 créanciers, 2200/2201 TVA due.
    """
    return bool(re.match(r"^(10\d\d|110\d|117\d|200\d|220\d)", compte))


def _brevets_au(fin: date) -> list[dict]:
    """Les dépôts de brevets connus au dernier jour de l'exercice, avec leur statut à cette date."""
    etat = societe.charger(fin)
    lignes = []
    for d in etat.depots:
        if d.en_preparation:
            m = re.search(r"(20\d\d)", d.numero)
            if not m or int(m.group(1)) > fin.year:
                continue
            statut = "Entrée annoncée"
        else:
            if d.depot and d.depot > fin:
                continue
            # Vu depuis la fin de l'exercice : un abandon ou une délivrance postérieurs ne sont pas encore connus.
            statut = ("Abandonné" if d.abandon and d.abandon <= fin
                      else "Délivré" if d.delivrance and d.delivrance <= fin else "En cours")
        lignes.append({
            "id": d.id, "famille": d.famille, "titre": d.titre, "numero": d.numero, "pays": d.pays,
            "depot": d.depot.isoformat() if d.depot else None,
            "delivrance": d.delivrance.isoformat() if d.delivrance and d.delivrance <= fin else None,
            "abandon": d.abandon.isoformat() if d.abandon and d.abandon <= fin else None,
            "titulaire": " / ".join(x.strip() for x in d.titulaire.splitlines() if x.strip()), "statut": statut})
    return lignes


def _projets_et_revenus() -> tuple[list[dict], list[dict]]:
    etat = societe.charger()
    projets = [{
        "projet": societe._texte(p.get("Projet")),
        "capitalisable": "oui" if societe._oui(p.get("Capitalisable (oui/non)")) else "non",
        "brevets": societe._texte(p.get("Brevets liés")), "debut": _valeur_cellule(p.get("Début")),
        "fin": _valeur_cellule(p.get("Fin")), "statut": societe._texte(p.get("Statut")),
        "montant_active": p.get("Montant activé CHF")} for p in etat.projets if societe._texte(p.get("Projet"))]
    revenus = [{
        "source": societe._texte(r.get("Source")), "client": societe._texte(r.get("Client")),
        "type": societe._texte(r.get("Type")), "contrat": societe._texte(r.get("Contrat")),
        "debut": _valeur_cellule(r.get("Début")), "fin": _valeur_cellule(r.get("Fin")),
        "montant_annuel": r.get("Montant annuel CHF"), "compte": societe._texte(r.get("Compte")),
        "statut": societe._texte(r.get("Statut"))} for r in etat.revenus if societe._texte(r.get("Source"))]
    return projets, revenus


def listes_depuis_fichiers(annee: int) -> dict[str, list[dict]]:
    """Ce que disent les fichiers déposés pour l'exercice, sans rien écrire.

    Une liste vide (par exemple pas encore de grand livre pour l'exercice) vaut None :
    elle ne doit pas faire croire que tous les éléments ont disparu.
    """
    plan_lignes, grand_livre = lire_imports(annee)
    plan = {p["code"]: p["nom"] for p in plan_lignes}
    partenaires = partenaires_depuis_grand_livre(grand_livre, plan)
    for code, nom in plan.items():
        if not any(p["code"] == code for p in plan_lignes):
            plan_lignes.append({"code": code, "nom": nom, "type": ""})
    projets, revenus = _projets_et_revenus()
    return {
        "PlanComptable": plan_lignes,
        "Partenaires": partenaires,
        "Brevets": _brevets_au(date(annee, 12, 31)),
        "Projets": projets,
        "Revenus": revenus,
    }


def construire(annee: int, ecraser_changements: bool = False) -> dict[str, int]:
    """Remplit le référentiel de l'exercice à partir des fichiers déposés.

    Refusé si l'exercice est validé. Refusé aussi s'il contient déjà des changements,
    sauf avec ecraser_changements=True.
    """
    if fichier_referentiel(annee).exists():
        if est_valide(annee):
            raise ExerciceVerrouille(f"L'exercice {annee} est validé.")
        if lire(annee)["Changements"] and not ecraser_changements:
            raise ValueError(f"L'exercice {annee} contient déjà des changements : "
                             "reconstruire les effacerait.")
    listes = listes_depuis_fichiers(annee)
    listes["Changements"] = []
    _ecrire(annee, listes)
    etat = lire_etat(annee)
    etat.update({"exercice": annee, "statut": OUVERT})
    etat.setdefault("historique", []).append({"le": _maintenant(), "action": "construit depuis les fichiers"})
    _ecrire_etat(annee, etat)
    return {nom: len(lignes) for nom, lignes in listes.items() if nom != "Changements"}


# ---------------------------------------------------------------- changements de l'exercice ouvert

def demander_changement(annee: int, action: str, liste: str, cle: str, valeurs: dict | None = None,
                        motif: str = "", quand: date | None = None) -> list[dict]:
    """Applique un changement à une liste de l'exercice ouvert et l'inscrit dans Changements.

    - ajout : crée l'élément cle avec valeurs (refusé s'il existe déjà) ;
    - modification : change les champs donnés dans valeurs ;
    - retrait : enlève l'élément.
    Rend les lignes ajoutées à Changements.
    """
    if est_valide(annee):
        raise ExerciceVerrouille(f"L'exercice {annee} est validé : rouvre-le avec un motif pour le modifier.")
    if action not in ACTIONS:
        raise ValueError(f"Action inconnue : {action}. Choisis parmi {', '.join(ACTIONS)}.")
    if liste not in LISTES:
        raise ValueError(f"Liste inconnue : {liste}.")
    cle = str(cle).strip()
    if not cle:
        raise ValueError("Indique l'élément concerné (code, nom ou identifiant).")
    if not motif.strip():
        raise ValueError("Indique le motif du changement.")
    valeurs = {k: v for k, v in (valeurs or {}).items() if k}
    listes = lire(annee)
    nom_cle, colonnes = LISTES[liste]
    lignes = listes[liste]
    existant = next((l for l in lignes if str(l.get(nom_cle, "")).strip() == cle), None)
    quand_iso = (quand or date.today()).isoformat()
    base = {"date": quand_iso, "action": action, "liste": liste, "cle": cle, "motif": motif.strip(),
            "saisi_le": _maintenant()}
    nouvelles: list[dict] = []
    if action == "ajout":
        if existant is not None:
            raise ValueError(f"{cle} existe déjà dans {NOMS_LISTES[liste]} : utilise une modification.")
        ligne = {nom_cle: cle, **valeurs}
        lignes.append(ligne)
        details = ", ".join(f"{k} = {v}" for k, v in valeurs.items())
        nouvelles.append({**base, "champ": "", "avant": "", "apres": details})
    elif action == "modification":
        if existant is None:
            raise ValueError(f"{cle} n'existe pas dans {NOMS_LISTES[liste]} : utilise un ajout.")
        if not valeurs:
            raise ValueError("Indique au moins un champ à modifier.")
        for champ, apres in valeurs.items():
            avant = existant.get(champ)
            existant[champ] = apres
            nouvelles.append({**base, "champ": champ, "avant": avant, "apres": apres})
    else:
        if existant is None:
            raise ValueError(f"{cle} n'existe pas dans {NOMS_LISTES[liste]}.")
        lignes.remove(existant)
        resume = ", ".join(f"{k} = {v}" for k, v in existant.items() if k != nom_cle and v not in (None, ""))
        nouvelles.append({**base, "champ": "", "avant": resume, "apres": ""})
    listes["Changements"].extend(nouvelles)
    _ecrire(annee, listes)
    return nouvelles


# ---------------------------------------------------------------- écarts entre deux exercices

@dataclass
class Ecart:
    liste: str
    cle: str
    nature: str        # ajout, retrait, modification
    champ: str = ""
    avant: object = None
    apres: object = None


def ecarts(annee: int, reference: int | None = None) -> list[Ecart]:
    """Différences entre l'exercice et l'exercice de référence (par défaut le précédent existant)."""
    if reference is None:
        precedents = [a for a in lister() if a < annee]
        if not precedents:
            return []
        reference = precedents[-1]
    return comparer(lire(reference), lire(annee))


def _resume_ligne(ligne: dict, nom_cle: str) -> str:
    return ", ".join(f"{k} = {v}" for k, v in ligne.items() if k != nom_cle and v not in (None, ""))


def comparer(ancien: dict[str, list[dict]], actuel: dict[str, list[dict]]) -> list[Ecart]:
    """Écarts liste par liste. Une liste absente ou vide d'un côté est ignorée."""
    resultat: list[Ecart] = []
    for liste, (nom_cle, colonnes) in LISTES.items():
        if not ancien.get(liste) and not actuel.get(liste):
            continue
        a = {str(l.get(nom_cle)).strip(): l for l in ancien.get(liste) or [] if l.get(nom_cle) not in (None, "")}
        n = {str(l.get(nom_cle)).strip(): l for l in actuel.get(liste) or [] if l.get(nom_cle) not in (None, "")}
        for cle in sorted(n.keys() - a.keys(), key=_cle_tri):
            resultat.append(Ecart(liste, cle, "ajout", apres=_resume_ligne(n[cle], nom_cle)))
        for cle in sorted(a.keys() - n.keys(), key=_cle_tri):
            resultat.append(Ecart(liste, cle, "retrait", avant=_resume_ligne(a[cle], nom_cle)))
        for cle in sorted(a.keys() & n.keys(), key=_cle_tri):
            for champ in colonnes:
                if champ == nom_cle or liste == "Partenaires" and champ in ("occurrences", "part"):
                    continue
                va, vn = a[cle].get(champ), n[cle].get(champ)
                if _egal(va, vn):
                    continue
                resultat.append(Ecart(liste, cle, "modification", champ, va, vn))
    return resultat


def suggestions(annee: int) -> list[Ecart]:
    """Ce que les fichiers déposés disent de différent du référentiel ouvert.

    Une liste que les fichiers ne fournissent pas pour cet exercice (vide) n'est pas comparée :
    sans grand livre 2025, les partenaires 2025 restent ceux du référentiel.
    """
    fichiers = listes_depuis_fichiers(annee)
    actuel = lire(annee)
    for liste, lignes in fichiers.items():
        if not lignes:
            actuel[liste] = []
    return comparer(actuel, fichiers)


def appliquer(annee: int, ecart: Ecart, motif: str, quand: date | None = None) -> list[dict]:
    """Applique un écart proposé par suggestions() comme une demande de changement."""
    nom_cle, colonnes = LISTES[ecart.liste]
    if ecart.nature == "modification":
        return demander_changement(annee, "modification", ecart.liste, ecart.cle, {ecart.champ: ecart.apres},
                                   motif, quand)
    if ecart.nature == "retrait":
        return demander_changement(annee, "retrait", ecart.liste, ecart.cle, None, motif, quand)
    ligne = next(l for l in listes_depuis_fichiers(annee)[ecart.liste] if str(l.get(nom_cle)).strip() == ecart.cle)
    valeurs = {k: v for k, v in ligne.items() if k != nom_cle and v not in (None, "")}
    return demander_changement(annee, "ajout", ecart.liste, ecart.cle, valeurs, motif, quand)


def _egal(a, b) -> bool:
    vide = (None, "")
    if a in vide and b in vide:
        return True
    return str(a).strip() == str(b).strip()


# ---------------------------------------------------------------- validation, contrôle, réouverture

def valider(annee: int, ouvrir_suivant: bool = True) -> int | None:
    """Fige l'exercice (lecture seule + empreinte) et ouvre le suivant comme copie.

    Rend l'année ouverte, ou None si le suivant existait déjà.
    """
    chemin = fichier_referentiel(annee)
    if not chemin.exists():
        raise ExerciceAbsent(f"Aucun référentiel pour {annee}.")
    if est_valide(annee):
        raise ExerciceVerrouille(f"L'exercice {annee} est déjà validé.")
    etat = lire_etat(annee)
    nb_changements = len(lire(annee)["Changements"])
    etat.update({"exercice": annee, "statut": VALIDE, "valide_le": _maintenant(),
                 "empreinte": empreinte(chemin)})
    etat.setdefault("historique", []).append(
        {"le": etat["valide_le"], "action": "validé et verrouillé", "changements": nb_changements})
    _ecrire_etat(annee, etat)
    _rendre_lecture_seule(chemin)
    _rendre_lecture_seule(_fichier_etat(annee))
    suivant = annee + 1
    if not ouvrir_suivant or fichier_referentiel(suivant).exists():
        return None
    listes = lire(annee)
    listes["Changements"] = []
    _ecrire(suivant, listes)
    _ecrire_etat(suivant, {"exercice": suivant, "statut": OUVERT, "ouvert_depuis": annee,
                           "historique": [{"le": _maintenant(), "action": f"ouvert comme copie de {annee} validé"}]})
    return suivant


def verifier(annee: int) -> str | None:
    """Rend un message si le référentiel d'un exercice validé a été modifié depuis sa validation."""
    etat = lire_etat(annee)
    if etat.get("statut") != VALIDE:
        return None
    chemin = fichier_referentiel(annee)
    if not chemin.exists():
        return f"Exercice {annee} : le référentiel validé a disparu."
    if empreinte(chemin) != etat.get("empreinte"):
        return (f"Exercice {annee} : le référentiel a été modifié après sa validation du "
                f"{_jour(etat.get('valide_le'))}. Rouvre l'exercice avec un motif, ou restaure le fichier.")
    return None


def rouvrir(annee: int, motif: str) -> None:
    if not motif.strip():
        raise ValueError("Un motif est obligatoire pour rouvrir un exercice validé.")
    if not est_valide(annee):
        raise ValueError(f"L'exercice {annee} n'est pas validé.")
    etat = lire_etat(annee)
    _rendre_modifiable(_fichier_etat(annee))
    _rendre_modifiable(fichier_referentiel(annee))
    etat["statut"] = OUVERT
    etat.pop("empreinte", None)
    etat.setdefault("historique", []).append({"le": _maintenant(), "action": "rouvert", "motif": motif.strip()})
    _ecrire_etat(annee, etat)


def _jour(iso: str | None) -> str:
    if not iso:
        return "?"
    return date.fromisoformat(iso[:10]).strftime("%d.%m.%Y")


# ---------------------------------------------------------------- comptes proposés pour la réconciliation

class Proposeur:
    """Propose un compte à partir du référentiel de l'exercice de chaque transaction."""

    def __init__(self) -> None:
        self._cache: dict[int, tuple[dict[str, dict], dict[str, str]]] = {}

    def _referentiel(self, annee: int):
        if annee not in self._cache:
            listes = lire(annee)
            partenaires = {societe._norm(p.get("partenaire")): p for p in listes["Partenaires"]
                           if p.get("partenaire")}
            plan = {_code(p.get("code")): societe._texte(p.get("nom")) for p in listes["PlanComptable"]}
            self._cache[annee] = (partenaires, plan)
        return self._cache[annee]

    def proposer(self, partenaire: str, quand: date, libelle: str = "") -> dict | None:
        annee = exercice_pour(quand)
        if annee is None:
            return None
        partenaires, plan = self._referentiel(annee)
        cle = societe._norm(partenaire)
        p = partenaires.get(cle) if cle else None
        origine = "partenaire"
        if p is None:
            texte = societe._norm(f"{partenaire} {libelle}")
            candidats = [(len(k), v) for k, v in partenaires.items() if len(k) >= 4 and k in texte]
            if not candidats:
                return None
            p = max(candidats, key=lambda c: c[0])[1]
            origine = "libellé"
        compte = _code(p.get("compte"))
        part = p.get("part") or 0
        occurrences = p.get("occurrences") or 0
        return {"compte": compte, "libelle_compte": plan.get(compte) or societe._texte(p.get("libelle_compte")),
                "exercice": annee, "origine": origine,
                "fiabilite": f"{int(round(float(part) * 100))} % sur {occurrences} écriture(s)" if occurrences else ""}


def proposer_comptes(transactions: list[dict]) -> int:
    """Ajoute compte_propose / fiabilite_compte à chaque transaction. Rend le nombre de propositions."""
    for t in transactions:
        t["compte_propose"] = ""
        t["fiabilite_compte"] = ""
    if not lister():
        return 0
    proposeur = Proposeur()
    n = 0
    for t in transactions:
        try:
            p = proposeur.proposer(t.get("partenaire_trouve") or "", t["date"], t.get("libelle") or "")
        except ExerciceAbsent:
            p = None
        if p:
            t["compte_propose"] = f"{p['compte']} {p['libelle_compte']}".strip()
            t["fiabilite_compte"] = ", ".join(x for x in (p["fiabilite"], f"selon {p['origine']}",
                                                         f"référentiel {p['exercice']}") if x)
            n += 1
    return n


# ---------------------------------------------------------------- résumé pour la fenêtre

def resume(annee: int) -> dict:
    etat = lire_etat(annee)
    listes = lire(annee)
    return {
        "exercice": annee,
        "statut": etat.get("statut", OUVERT),
        "valide_le": etat.get("valide_le"),
        "compteurs": {NOMS_LISTES[n]: len(listes[n]) for n in LISTES},
        "changements": listes["Changements"],
        "historique": etat.get("historique", []),
        "alerte": verifier(annee),
    }


def copier_vers(annee: int, cible: Path) -> Path:
    """Copie le référentiel (pour l'ouvrir dans Excel sans risquer de modifier la version verrouillée)."""
    cible = Path(cible)
    shutil.copy2(fichier_referentiel(annee), cible)
    _rendre_modifiable(cible)
    return cible
