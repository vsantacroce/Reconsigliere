"""État de la société : brevets, projets, sources de revenus et journal.

Tout est lu dans le dossier entrees/06_societe :

- n'importe quel classeur Excel qui contient une liste de brevets (colonnes ID, titre,
  numéro, date de dépôt, date de délivrance, date d'abandon, titulaire…) ;
- n'importe quel onglet de coûts de brevets (colonnes brevet, classification
  capitalisable/charge, montant CHF, date de facture…) ;
- le classeur societe.xlsx, créé au premier lancement, avec les onglets Projets,
  Revenus et Journal que tu tiens au jour le jour.

Ce module n'utilise qu'openpyxl : il se charge vite, la fenêtre l'appelle directement.

Ligne de commande : python -m reconsigliere.societe [--dossier CHEMIN]
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from . import config

NOM_DOSSIER = "entrees/06_societe"
NOM_CLASSEUR = "societe.xlsx"

CAPITALISABLE = "Capitalisable"
CHARGE = "Charge"

# ---------------------------------------------------------------- colonnes reconnues

COLONNES_BREVETS = {
    "id": ["id", "identifiant", "ref", "reference", "référence"],
    "titre": ["title", "titre", "intitule", "intitulé"],
    "numero": ["patent number", "numero", "numéro", "numero de brevet", "numéro de brevet",
               "application number", "publication"],
    "depot": ["filing date", "date de depot", "date de dépôt", "depot", "dépôt"],
    "delivrance": ["approved date", "grant date", "date de delivrance", "date de délivrance",
                   "delivrance", "délivrance"],
    "abandon": ["abandon date", "date d'abandon", "abandon", "abandoned date"],
    "titulaire": ["patent owner", "owner", "titulaire", "proprietaire", "propriétaire"],
    "inventeurs": ["author", "authors", "inventor", "inventors", "inventeur", "inventeurs", "auteur"],
    "notes": ["notes", "note", "remarques", "commentaire"],
}

COLONNES_COUTS = {
    "piece": ["n° piece (odoo)", "n° piece", "piece", "pièce", "no piece", "numero piece"],
    "fournisseur": ["fournisseur", "partenaire", "supplier"],
    "facture": ["facture fournisseur", "facture", "invoice"],
    "date": ["date facture", "date", "invoice date"],
    "devise": ["devise", "currency"],
    "brevet": ["brevet", "patent"],
    "description": ["description de la ligne", "description", "libelle", "libellé"],
    "montant_devise": ["montant ht (devise)", "montant devise"],
    "montant": ["montant ht chf", "montant chf", "montant ht (chf)"],
    "classification": ["classification", "traitement"],
    "nature": ["nature", "categorie", "catégorie"],
    "remarques": ["remarques", "notes", "commentaire"],
}

# Onglets du classeur societe.xlsx tenu au jour le jour.
MODELE = {
    "Projets": ["Projet", "Capitalisable (oui/non)", "Brevets liés", "Début", "Fin", "Statut",
                "Montant activé CHF", "Notes"],
    "Revenus": ["Source", "Client", "Type", "Contrat", "Début", "Fin", "Montant annuel CHF",
                "Compte", "Statut", "Notes"],
    "Journal": ["Date", "Catégorie", "Événement", "Lien", "Montant CHF"],
}

CATEGORIES_JOURNAL = ["Brevet", "Projet", "Revenu", "Contrat", "Financement", "Équipe", "Autre"]

PAYS = {"WO": "PCT", "EP": "Europe", "EU": "Europe", "CN": "Chine", "US": "États-Unis",
        "CH": "Suisse", "JP": "Japon", "KR": "Corée", "GB": "Royaume-Uni", "DE": "Allemagne",
        "FR": "France", "IN": "Inde", "CA": "Canada", "AU": "Australie"}


def dossier_societe() -> Path:
    return config.RACINE / NOM_DOSSIER


def fichier_classeur() -> Path:
    return dossier_societe() / NOM_CLASSEUR


# ---------------------------------------------------------------- petites conversions

def _norm(texte) -> str:
    texte = unicodedata.normalize("NFKD", str(texte or ""))
    texte = "".join(c for c in texte if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", texte).strip()


def _texte(valeur) -> str:
    return "" if valeur is None else str(valeur).strip()


def _date(valeur) -> date | None:
    if valeur is None or valeur == "":
        return None
    if isinstance(valeur, datetime):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    texte = str(valeur).strip()
    m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", texte)
    if m:
        j, mo, a = (int(x) for x in m.groups())
        try:
            return date(a, mo, j)
        except ValueError:
            return None
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", texte)
    if m:
        try:
            return date(*(int(x) for x in m.groups()))
        except ValueError:
            return None
    return None


def _montant(valeur) -> float:
    if valeur is None or valeur == "":
        return 0.0
    if isinstance(valeur, (int, float)):
        return round(float(valeur), 2)
    texte = re.sub(r"[^\d.,\-]", "", str(valeur).replace("'", "").replace("’", ""))
    if "," in texte and "." not in texte:
        texte = texte.replace(",", ".")
    texte = texte.replace(",", "")
    try:
        return round(float(texte), 2)
    except ValueError:
        return 0.0


def _oui(valeur) -> bool:
    return _norm(valeur) in {"oui", "o", "yes", "y", "x", "1", "vrai", "true", "capitalisable"}


def _trouver_colonnes(entete: list, alias: dict[str, list[str]]) -> dict[str, int]:
    noms = [_norm(c) for c in entete]
    trouvees: dict[str, int] = {}
    for cle, possibles in alias.items():
        for possible in possibles:
            p = _norm(possible)
            if p in noms and noms.index(p) not in trouvees.values():
                trouvees[cle] = noms.index(p)
                break
    return trouvees


def _lignes_avec_entete(ws, alias: dict[str, list[str]], obligatoires: set[str], max_entete: int = 10):
    """Cherche la ligne d'en-tête dans les premières lignes de l'onglet, puis rend les lignes suivantes."""
    lignes = list(ws.iter_rows(values_only=True))
    for i, ligne in enumerate(lignes[:max_entete]):
        cols = _trouver_colonnes(list(ligne), alias)
        if obligatoires <= cols.keys():
            return cols, lignes[i + 1:]
    return None, []


def _val(ligne, cols: dict[str, int], cle: str):
    i = cols.get(cle)
    return ligne[i] if i is not None and i < len(ligne) else None


# ---------------------------------------------------------------- modèle

@dataclass
class Depot:
    id: str
    famille: str
    titre: str
    numero: str
    pays: str
    depot: date | None = None
    delivrance: date | None = None
    abandon: date | None = None
    titulaire: str = ""
    inventeurs: str = ""
    notes: str = ""
    en_preparation: bool = False   # entrée annoncée (« submitted ») sans ligne propre

    def statut(self, aujourd_hui: date) -> str:
        if self.abandon and self.abandon <= aujourd_hui:
            return "Abandonné"
        if self.abandon:
            return "Abandon prévu"
        if self.delivrance:
            return "Délivré"
        return "En cours"


@dataclass
class Cout:
    famille: str          # « PAT01 » ou « PAT03 + PAT04 » quand le coût est à répartir
    pays: str
    date: date | None
    piece: str
    fournisseur: str
    facture: str
    description: str
    devise: str
    montant: float
    classification: str
    nature: str
    remarques: str
    source: str


@dataclass
class Etat:
    aujourd_hui: date
    depots: list[Depot] = field(default_factory=list)
    couts: list[Cout] = field(default_factory=list)
    projets: list[dict] = field(default_factory=list)
    revenus: list[dict] = field(default_factory=list)
    journal: list[dict] = field(default_factory=list)
    fichiers: list[str] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- lecture des brevets

_RE_FAMILLE = re.compile(r"\b([A-Z]{2,5}\d{1,3})(?:-\d+)?\b")


def famille_de(identifiant: str) -> str:
    m = _RE_FAMILLE.search(identifiant or "")
    return m.group(1) if m else (identifiant or "").split("-")[0].strip()


def familles_citees(texte: str) -> list[str]:
    vues: list[str] = []
    for m in _RE_FAMILLE.finditer(texte or ""):
        if m.group(1) not in vues:
            vues.append(m.group(1))
    return vues


def _pays_du_numero(ligne: str) -> str:
    ligne = ligne.strip().upper()
    m = re.match(r"^([A-Z]{2})\s*:", ligne)
    if m:
        return "EP" if m.group(1) == "EU" else m.group(1)
    m = re.match(r"^([A-Z]{2})\s*\d", ligne)
    if m:
        return m.group(1)
    return ""


def _depots_d_une_ligne(ligne, cols) -> list[Depot]:
    identifiant = _texte(_val(ligne, cols, "id"))
    if not identifiant:
        return []
    numero_brut = _texte(_val(ligne, cols, "numero"))
    lignes_numero = [l.strip() for l in numero_brut.splitlines() if l.strip()]
    commun = dict(
        famille=famille_de(identifiant),
        titre=_texte(_val(ligne, cols, "titre")),
        depot=_date(_val(ligne, cols, "depot")),
        delivrance=_date(_val(ligne, cols, "delivrance")),
        abandon=_date(_val(ligne, cols, "abandon")),
        titulaire=_texte(_val(ligne, cols, "titulaire")),
        inventeurs=_texte(_val(ligne, cols, "inventeurs")),
        notes=_texte(_val(ligne, cols, "notes")),
    )
    principal = lignes_numero[0] if lignes_numero else ""
    pays = _pays_du_numero(principal)
    principal = re.sub(r"^[A-Z]{2}\s*:\s*", "", principal)
    depots = [Depot(id=identifiant, numero=principal, pays=pays, **commun)]
    # Lignes suivantes du type « EU, CN, US: submitted July 2025 » : entrées nationales annoncées.
    for suite in lignes_numero[1:]:
        m = re.match(r"^((?:[A-Z]{2}\s*,\s*)*[A-Z]{2})\s*:\s*(.*)$", suite.strip())
        if not m:
            continue
        for code in re.split(r"\s*,\s*", m.group(1)):
            code = "EP" if code == "EU" else code
            depots.append(Depot(id=f"{identifiant}-{code}", numero=m.group(2).strip(), pays=code,
                                en_preparation=True, **{**commun, "depot": None}))
    return depots


def lire_brevets(ws) -> list[Depot]:
    cols, lignes = _lignes_avec_entete(ws, COLONNES_BREVETS, {"id", "titre", "numero"})
    if cols is None:
        return []
    depots: list[Depot] = []
    for ligne in lignes:
        depots.extend(_depots_d_une_ligne(ligne, cols))
    return depots


# ---------------------------------------------------------------- lecture des coûts

def _pays_du_libelle(texte: str) -> str:
    m = re.search(r"\(([A-Z]{2}(?:\s*\+\s*[A-Z]{2})*)\)", texte or "")
    return m.group(1).replace(" ", "") if m else ""


def _classification(valeur) -> str:
    n = _norm(valeur)
    if n.startswith("capital") or n.startswith("activ"):
        return CAPITALISABLE
    if n.startswith("charge") or n.startswith("expense"):
        return CHARGE
    return ""


def lire_couts(ws, source: str) -> list[Cout]:
    cols, lignes = _lignes_avec_entete(ws, COLONNES_COUTS, {"brevet", "classification", "montant"})
    if cols is None:
        return []
    couts = []
    for ligne in lignes:
        brevet = _texte(_val(ligne, cols, "brevet"))
        classification = _classification(_val(ligne, cols, "classification"))
        if not brevet or not classification:
            continue  # lignes de sous-total, vides ou de rappel
        familles = familles_citees(brevet)
        couts.append(Cout(
            famille=" + ".join(familles) if familles else brevet,
            pays=_pays_du_libelle(brevet),
            date=_date(_val(ligne, cols, "date")),
            piece=_texte(_val(ligne, cols, "piece")),
            fournisseur=_texte(_val(ligne, cols, "fournisseur")),
            facture=_texte(_val(ligne, cols, "facture")),
            description=_texte(_val(ligne, cols, "description")),
            devise=_texte(_val(ligne, cols, "devise")) or config.DEVISE,
            montant=_montant(_val(ligne, cols, "montant")),
            classification=classification,
            nature=_texte(_val(ligne, cols, "nature")),
            remarques=_texte(_val(ligne, cols, "remarques")),
            source=source,
        ))
    return couts


# ---------------------------------------------------------------- classeur tenu à la main

def creer_modele_si_absent() -> Path:
    """Crée societe.xlsx avec ses onglets vides. Ne touche jamais à un fichier existant."""
    chemin = fichier_classeur()
    if chemin.exists():
        return chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for nom, colonnes in MODELE.items():
        ws = wb.create_sheet(nom)
        ws.append(colonnes)
        for i, c in enumerate(colonnes, start=1):
            ws.cell(row=1, column=i).font = Font(bold=True)
            ws.column_dimensions[get_column_letter(i)].width = max(14, len(c) + 4)
        ws.freeze_panes = "A2"
    wb.save(chemin)
    return chemin


def _lire_onglet_libre(wb, nom: str) -> list[dict]:
    if nom not in wb.sheetnames:
        return []
    lignes = list(wb[nom].iter_rows(values_only=True))
    if not lignes:
        return []
    entete = [_texte(c) for c in lignes[0]]
    resultat = []
    for ligne in lignes[1:]:
        if not any(v not in (None, "") for v in ligne):
            continue
        resultat.append({entete[i]: ligne[i] for i in range(min(len(entete), len(ligne))) if entete[i]})
    return resultat


def ajouter_au_journal(quand: date, categorie: str, evenement: str, lien: str = "",
                       montant: float | None = None) -> Path:
    """Ajoute une ligne à l'onglet Journal de societe.xlsx.

    PermissionError si le classeur est ouvert dans Excel : la fenêtre l'affiche.
    """
    chemin = creer_modele_si_absent()
    wb = openpyxl.load_workbook(chemin)
    if "Journal" not in wb.sheetnames:
        ws = wb.create_sheet("Journal")
        ws.append(MODELE["Journal"])
    ws = wb["Journal"]
    ws.append([quand, categorie, evenement, lien or None, montant])
    ws.cell(row=ws.max_row, column=1).number_format = "DD.MM.YYYY"
    wb.save(chemin)
    return chemin


# ---------------------------------------------------------------- chargement complet

def charger(aujourd_hui: date | None = None) -> Etat:
    etat = Etat(aujourd_hui=aujourd_hui or date.today())
    dossier = dossier_societe()
    if not dossier.exists():
        return etat
    par_id: dict[str, Depot] = {}
    for chemin in sorted(dossier.rglob("*.xls[xm]")):
        if chemin.name.startswith("~$"):
            continue
        try:
            wb = openpyxl.load_workbook(chemin, data_only=True, read_only=True)
        except Exception as e:  # noqa: BLE001 - un fichier illisible ne doit pas tout arrêter
            etat.avertissements.append(f"{chemin.name} : illisible ({e.__class__.__name__}).")
            continue
        etat.fichiers.append(chemin.name)
        for ws in wb.worksheets:
            for d in lire_brevets(ws):
                par_id[d.id] = d
            etat.couts.extend(lire_couts(ws, f"{chemin.name} › {ws.title}"))
        if chemin.name.lower() == NOM_CLASSEUR:
            etat.projets = _lire_onglet_libre(wb, "Projets")
            etat.revenus = _lire_onglet_libre(wb, "Revenus")
            etat.journal = _lire_onglet_libre(wb, "Journal")
        wb.close()
    etat.depots = list(par_id.values())
    return etat


# ---------------------------------------------------------------- synthèse

def _cle_famille(f: str) -> tuple:
    m = re.search(r"(\d+)", f)
    return (int(m.group(1)) if m else 999, f)


def synthese(etat: Etat) -> dict:
    """Chiffres du tableau de bord, prêts à afficher."""
    j = etat.aujourd_hui
    familles: dict[str, dict] = {}
    for d in etat.depots:
        f = familles.setdefault(d.famille, {
            "famille": d.famille, "titre": d.titre, "titulaire": d.titulaire,
            "inventeurs": d.inventeurs, "depots": [], "notes": []})
        f["depots"].append({
            "id": d.id, "pays": d.pays, "nom_pays": PAYS.get(d.pays, d.pays), "numero": d.numero,
            "depot": d.depot.isoformat() if d.depot else "",
            "delivrance": d.delivrance.isoformat() if d.delivrance else "",
            "abandon": d.abandon.isoformat() if d.abandon else "",
            "statut": "Entrée annoncée" if d.en_preparation else d.statut(j)})
        if d.notes and d.notes not in f["notes"]:
            f["notes"].append(d.notes)

    annees = sorted({c.date.year for c in etat.couts if c.date})
    couts_par_groupe: dict[str, dict] = defaultdict(lambda: {CAPITALISABLE: 0.0, CHARGE: 0.0,
                                                               "par_annee": defaultdict(lambda: {CAPITALISABLE: 0.0, CHARGE: 0.0})})
    annuites: dict[str, list] = defaultdict(list)
    for c in etat.couts:
        g = couts_par_groupe[c.famille]
        g[c.classification] += c.montant
        if c.date:
            g["par_annee"][c.date.year][c.classification] += c.montant
        desc = _norm(c.description)
        if c.montant and ("annuit" in desc or "renewal" in desc) and "package" not in desc \
                and "maintenance fee" not in desc:
            annuites[c.famille].append(c)

    lignes_familles = []
    for nom in sorted(set(familles) | set(couts_par_groupe), key=_cle_famille):
        f = familles.get(nom, {"famille": nom, "titre": "Coûts communs à répartir", "titulaire": "",
                               "inventeurs": "", "depots": [], "notes": []})
        statuts = [d["statut"] for d in f["depots"] if d["statut"] != "Entrée annoncée"]
        if not f["depots"]:
            statut = "À répartir"
        elif statuts and all(s == "Abandonné" for s in statuts):
            statut = "Abandonnée"
        elif any(s == "Délivré" for s in statuts):
            statut = "Délivrée (au moins un pays)"
        else:
            statut = "Active"
        g = couts_par_groupe.get(nom)
        dernieres: dict[str, Cout] = {}
        for c in annuites.get(nom, []):
            for pays in (c.pays or "").split("+"):
                if pays not in dernieres or (c.date or date.min) > (dernieres[pays].date or date.min):
                    dernieres[pays] = c
        lignes_familles.append({
            **f,
            "statut": statut,
            "licence": any(m in _norm(f["titulaire"]) for m in ("licence", "license")),
            "pays": sorted({d["pays"] for d in f["depots"] if d["pays"] and d["pays"] != "WO"}),
            "capitalisable": round(g[CAPITALISABLE], 2) if g else 0.0,
            "charge": round(g[CHARGE], 2) if g else 0.0,
            "par_annee": {a: {k: round(v, 2) for k, v in g["par_annee"][a].items()} for a in annees} if g else {},
            "dernieres_annuites": [
                {"pays": p, "date": c.date.isoformat() if c.date else "", "description": c.description,
                 "montant": c.montant} for p, c in sorted(dernieres.items())],
        })

    actives = [f for f in lignes_familles if f["statut"] not in ("Abandonnée", "À répartir")]
    depots_actifs = [d for f in actives for d in f["depots"] if d["statut"] in ("En cours", "Délivré", "Abandon prévu")]

    par_annee = {a: {CAPITALISABLE: 0.0, CHARGE: 0.0} for a in annees}
    for c in etat.couts:
        if c.date:
            par_annee[c.date.year][c.classification] += c.montant
    cumul = 0.0
    tableau_annees = []
    for a in annees:
        cumul += par_annee[a][CAPITALISABLE]
        tableau_annees.append({"annee": a, "capitalisable": round(par_annee[a][CAPITALISABLE], 2),
                               "charge": round(par_annee[a][CHARGE], 2), "cumul_capitalisable": round(cumul, 2)})

    projets = [{
        "nom": _texte(p.get("Projet")), "capitalisable": _oui(p.get("Capitalisable (oui/non)")),
        "brevets": _texte(p.get("Brevets liés")), "statut": _texte(p.get("Statut")),
        "montant": _montant(p.get("Montant activé CHF")), "notes": _texte(p.get("Notes"))}
        for p in etat.projets if _texte(p.get("Projet"))]
    revenus = [{
        "source": _texte(r.get("Source")), "client": _texte(r.get("Client")), "type": _texte(r.get("Type")),
        "contrat": _texte(r.get("Contrat")), "statut": _texte(r.get("Statut")),
        "fin": (_date(r.get("Fin")).isoformat() if _date(r.get("Fin")) else ""),
        "montant": _montant(r.get("Montant annuel CHF")), "compte": _texte(r.get("Compte"))}
        for r in etat.revenus if _texte(r.get("Source"))]
    revenus_actifs = [r for r in revenus
                      if not (r["fin"] and r["fin"] < j.isoformat())
                      and _norm(r["statut"]) not in {"termine", "terminé", "clos", "perdu", "abandonne"}]
    journal = sorted(({
        "date": _date(e.get("Date")).isoformat() if _date(e.get("Date")) else "",
        "categorie": _texte(e.get("Catégorie")), "evenement": _texte(e.get("Événement")),
        "lien": _texte(e.get("Lien")),
        "montant": _montant(e.get("Montant CHF")) if e.get("Montant CHF") not in (None, "") else None}
        for e in etat.journal if _texte(e.get("Événement"))), key=lambda e: e["date"], reverse=True)

    return {
        "date": j.isoformat(),
        "devise": config.DEVISE,
        "fichiers": etat.fichiers,
        "compteurs": {
            "familles": len([f for f in lignes_familles if f["depots"]]),
            "familles_actives": len(actives),
            "depots_actifs": len(depots_actifs),
            "entrees_annoncees": sum(1 for f in actives for d in f["depots"] if d["statut"] == "Entrée annoncée"),
            "sous_licence": sum(1 for f in actives if f["licence"]),
            "projets": len(projets),
            "projets_capitalisables": sum(1 for p in projets if p["capitalisable"]),
            "revenus_actifs": len(revenus_actifs),
            "revenus_annuels": round(sum(r["montant"] for r in revenus_actifs), 2),
            "capitalisable": round(sum(c.montant for c in etat.couts if c.classification == CAPITALISABLE), 2),
            "charge": round(sum(c.montant for c in etat.couts if c.classification == CHARGE), 2),
        },
        "familles": lignes_familles,
        "annees": tableau_annees,
        "projets": projets,
        "revenus": revenus,
        "journal": journal,
        "attention": points_d_attention(etat, lignes_familles),
    }


def points_d_attention(etat: Etat, familles: list[dict]) -> list[str]:
    points = list(etat.avertissements)
    for f in familles:
        if f["statut"] == "Abandonnée" and f["capitalisable"]:
            abandon = max((d["abandon"] for d in f["depots"] if d["abandon"]), default="")
            quand = f" au {date.fromisoformat(abandon).strftime('%d.%m.%Y')}" if abandon else ""
            points.append(f"{f['famille']} est abandonnée{quand} : {format_chf(f['capitalisable'])} CHF "
                          "capitalisés sont à sortir de l'actif ou à amortir.")
        if f["statut"] == "À répartir" and (f["capitalisable"] or f["charge"]):
            points.append(f"{f['famille']} : {format_chf(f['capitalisable'] + f['charge'])} CHF de coûts "
                          "communs restent à répartir entre les familles.")
    vus = set()
    for c in etat.couts:
        if "doublon" in _norm(c.remarques) and c.montant == 0 and c.piece not in vus:
            vus.add(c.piece)
            points.append(f"Pièce {c.piece} ({c.fournisseur}, facture {c.facture}) marquée comme doublon : "
                          "à annuler dans la comptabilité.")
    notes_futures: dict[str, list[str]] = {}
    for d in etat.depots:
        if d.en_preparation:
            continue
        for m in re.finditer(r"(\d{1,2}\.\d{1,2}\.\d{4})", d.notes):
            quand = _date(m.group(1))
            if quand and quand > etat.aujourd_hui and ("as of" in _norm(d.notes) or " au " in _norm(d.notes)):
                notes_futures.setdefault(d.notes, []).append(d.id)
                break
    for texte, ids in notes_futures.items():
        points.append(f"{', '.join(ids)} : la note « {texte} » porte une date postérieure à aujourd'hui, à vérifier.")
    return points


def format_chf(montant: float) -> str:
    signe = "−" if montant < 0 else ""
    entier, decimales = f"{abs(montant):.2f}".split(".")
    groupes = []
    while entier:
        groupes.insert(0, entier[-3:])
        entier = entier[:-3]
    return signe + "'".join(groupes) + "." + decimales


# ---------------------------------------------------------------- page HTML

def ecrire_html(donnees: dict) -> Path:
    sorties = config.DOSSIER_SORTIES
    sorties.mkdir(parents=True, exist_ok=True)
    chemin = sorties / "societe.html"
    gabarit = (Path(__file__).parent / "modele_societe.html").read_text(encoding="utf-8")
    texte = json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")
    chemin.write_text(gabarit.replace("__DONNEES__", texte), encoding="utf-8")
    return chemin


def actualiser(aujourd_hui: date | None = None) -> tuple[dict, Path]:
    """Crée le classeur si besoin, relit tout et réécrit sorties/societe.html."""
    creer_modele_si_absent()
    donnees = synthese(charger(aujourd_hui))
    return donnees, ecrire_html(donnees)


def _ligne_de_commande() -> None:
    from . import installation
    parser = argparse.ArgumentParser(prog="reconsigliere.societe")
    parser.add_argument("--dossier", type=Path, help="dossier de travail (par défaut : celui de la fenêtre)")
    args = parser.parse_args()
    dossier = args.dossier or installation.dossier_memorise()
    if dossier:
        config.definir_racine(dossier)
    donnees, chemin = actualiser()
    c = donnees["compteurs"]
    print(f"Familles de brevets : {c['familles_actives']} actives sur {c['familles']}")
    print(f"Dépôts actifs : {c['depots_actifs']} (+ {c['entrees_annoncees']} entrées annoncées)")
    print(f"Projets capitalisables : {c['projets_capitalisables']} sur {c['projets']}")
    print(f"Sources de revenus actives : {c['revenus_actifs']}")
    print(f"Coûts brevets : {format_chf(c['capitalisable'])} capitalisables, {format_chf(c['charge'])} en charge")
    for p in donnees["attention"]:
        print(f"  ! {p}")
    print(chemin)


if __name__ == "__main__":
    _ligne_de_commande()

