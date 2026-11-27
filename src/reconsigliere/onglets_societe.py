"""Onglets directs de la fenêtre : un élément par onglet (Brevets, Projets, Revenus, Plan comptable, Partenaires…).

Ce module donne l'ordre des onglets, la phrase qui explique chacun, les lignes des tableaux et la taille de la fenêtre.
Il ne lit rien d'autre que ce que lisent déjà societe.py (societe.xlsx) et exercices.py (référentiel de l'année).
"""

from __future__ import annotations

import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

from . import exercices, societe

# Ordre des onglets principaux : (clé, titre affiché).
ONGLETS: list[tuple[str, str]] = [
    ("reconciliation", "Réconciliation"),
    ("documents", "Documents"),
    ("salaires", "Salaires"),
    ("brevets", "Brevets"),
    ("projets", "Projets"),
    ("revenus", "Revenus"),
    ("plan", "Plan comptable"),
    ("partenaires", "Partenaires"),
    ("annee", "Année comptable"),
    ("apprentissage", "Apprentissage"),
]
ONGLETS_PAR_LIGNE = 5

EXPLICATIONS: dict[str, str] = {
    "reconciliation": "Rapprocher tes transactions bancaires de tes factures et de ta comptabilité.",
    "documents": "Les documents comptables importés (PDF, Excel), type par type, avec leurs contrôles.",
    "salaires": "Réconciliation des salaires par employé et par année.",
    "brevets": "Tes familles de brevets, leurs dépôts par pays et leurs coûts (lus dans entrees › 06_societe).",
    "projets": "Tes projets, capitalisables ou non (onglet Projets du classeur societe.xlsx).",
    "revenus": "Tes sources de revenus : client, contrat, montant annuel, compte (onglet Revenus de societe.xlsx).",
    "plan": "Le plan comptable de l'année choisie, tel qu'il est enregistré pour cette année.",
    "partenaires": "Chaque fournisseur ou client et le compte où il est rangé d'habitude, pour l'année choisie.",
    "annee": "Construire l'année depuis tes fichiers, demander une modification, puis la valider et la verrouiller.",
    "apprentissage": "Ce que le programme a appris de tes corrections de compte, et ses alertes.",
}

COLONNES_PROJETS = [("Projet", 200), ("Capitalisable", 90), ("Brevets liés", 120), ("Début", 85), ("Fin", 85),
                    ("Statut", 110), ("Montant activé CHF", 120)]
COLONNES_REVENUS = [("Source", 140), ("Client", 130), ("Type", 90), ("Contrat", 90), ("Début", 85), ("Fin", 85),
                    ("Montant annuel CHF", 120), ("Compte", 65), ("Statut", 80)]
COLONNES_REFERENTIEL = {
    "PlanComptable": [("Compte", 80), ("Nom", 340), ("Type", 160)],
    "Partenaires": [("Partenaire", 220), ("Compte habituel", 110), ("Nom du compte", 220), ("Écritures", 80),
                    ("Part", 70)],
}


# ---------------------------------------------------------------- mise en forme

def _texte(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%d.%m.%Y")
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    texte = str(v).strip()
    if len(texte) >= 10 and texte[4] == "-" and texte[7] == "-" and texte[:4].isdigit():  # 2024-03-01 → 01.03.2024
        return f"{texte[8:10]}.{texte[5:7]}.{texte[:4]}"
    return texte


def _chf(v) -> str:
    if v in (None, ""):
        return ""
    try:
        return f"{float(v):,.2f}".replace(",", "'")
    except (TypeError, ValueError):
        return str(v)


def _oui_non(v) -> str:
    return "oui" if societe._oui(v) else "non"


# ---------------------------------------------------------------- lignes des tableaux

def lignes_projets(etat: societe.Etat) -> list[tuple]:
    return [(_texte(p.get("Projet")), _oui_non(p.get("Capitalisable (oui/non)")), _texte(p.get("Brevets liés")),
             _texte(p.get("Début")), _texte(p.get("Fin")), _texte(p.get("Statut")), _chf(p.get("Montant activé CHF")))
            for p in etat.projets if _texte(p.get("Projet"))]


def lignes_revenus(etat: societe.Etat) -> list[tuple]:
    return [(_texte(r.get("Source")), _texte(r.get("Client")), _texte(r.get("Type")), _texte(r.get("Contrat")),
             _texte(r.get("Début")), _texte(r.get("Fin")), _chf(r.get("Montant annuel CHF")), _texte(r.get("Compte")),
             _texte(r.get("Statut")))
            for r in etat.revenus if _texte(r.get("Source"))]


def lignes_referentiel(annee: int | None, liste: str) -> tuple[list[tuple], str]:
    """Lignes d'une liste (PlanComptable ou Partenaires) du référentiel de l'année, et une phrase d'état."""
    if annee is None:
        return [], ("Aucune année construite pour l'instant : va dans l'onglet « Année comptable » et clique sur "
                    "« Construire depuis les fichiers… ».")
    try:
        donnees = exercices.lire(annee)[liste]
    except exercices.ExerciceAbsent:
        return [], f"L'année {annee} n'est pas encore construite (onglet « Année comptable »)."
    if liste == "Partenaires":
        lignes = [(_texte(p.get("partenaire")), _texte(p.get("compte")), _texte(p.get("libelle_compte")),
                   _texte(p.get("occurrences")),
                   f"{round(float(p['part']) * 100)} %" if p.get("part") not in (None, "") else "")
                  for p in donnees]
    else:
        lignes = [(_texte(c.get("code")), _texte(c.get("nom")), _texte(c.get("type"))) for c in donnees]
    statut = "validée et verrouillée" if exercices.est_valide(annee) else "ouverte"
    return lignes, f"Année {annee} ({statut}) : {len(lignes)} lignes."


# ---------------------------------------------------------------- taille de la fenêtre

def geometrie(largeur_ecran: int, hauteur_ecran: int, echelle: float) -> str:
    """Taille de la fenêtre en pixels : 1040 × 900 à 100 %, agrandie avec l'affichage de Windows, bornée à l'écran."""
    largeur = min(round(1040 * echelle), largeur_ecran - 40)
    hauteur = min(round(900 * echelle), hauteur_ecran - 80)
    return f"{largeur}x{hauteur}"


# ---------------------------------------------------------------- onglet tableau

class OngletTableau:
    """Un onglet simple : phrase d'état, choix d'année facultatif, tableau, boutons."""

    def __init__(self, parent, colonnes: list[tuple[str, int]], remplir, avec_annee: bool = False,
                 boutons: list[tuple[str, object]] | None = None) -> None:
        self.remplir = remplir  # remplir(annee | None) -> (lignes, phrase)
        self.v_annee = tk.StringVar()
        haut = ttk.Frame(parent)
        haut.pack(fill="x", pady=(0, 6))
        if avec_annee:
            ttk.Label(haut, text="Année :").pack(side="left")
            self.cb_annee = ttk.Combobox(haut, textvariable=self.v_annee, width=8, state="readonly")
            self.cb_annee.pack(side="left", padx=(6, 12))
            self.cb_annee.bind("<<ComboboxSelected>>", lambda _e: self.actualiser())
        else:
            self.cb_annee = None
        self.lbl_etat = ttk.Label(haut, text="", style="Doux.TLabel")
        self.lbl_etat.pack(side="left")

        cadre = ttk.Frame(parent)
        cadre.pack(fill="both", expand=True)
        noms = [f"c{i}" for i in range(len(colonnes))]
        self.arbre = ttk.Treeview(cadre, columns=noms, show="headings", height=12)
        for nom, (titre, largeur) in zip(noms, colonnes):
            self.arbre.heading(nom, text=titre)
            self.arbre.column(nom, width=largeur, anchor="w", stretch=True)
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=defil.set)
        self.arbre.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")

        if boutons:
            bas = ttk.Frame(parent)
            bas.pack(anchor="w", pady=(8, 0))
            for texte, commande in boutons:
                ttk.Button(bas, text=texte, command=commande).pack(side="left", padx=(0, 6))

    def actualiser(self) -> None:
        annee = None
        if self.cb_annee is not None:
            annees = exercices.lister()
            self.cb_annee.configure(values=[str(a) for a in annees])
            choisie = int(self.v_annee.get()) if self.v_annee.get().isdigit() else None
            if choisie not in annees:
                choisie = exercices.exercice_courant()
                self.v_annee.set(str(choisie) if choisie else "")
            annee = choisie
        try:
            lignes, phrase = self.remplir(annee)
        except Exception as e:  # noqa: BLE001 - l'erreur doit apparaître dans la fenêtre
            lignes, phrase = [], f"Lecture impossible : {e}"
        self.arbre.delete(*self.arbre.get_children())
        for ligne in lignes:
            self.arbre.insert("", "end", values=ligne)
        self.lbl_etat.configure(text=phrase)


def remplir_projets(_annee=None) -> tuple[list[tuple], str]:
    lignes = lignes_projets(societe.charger())
    return lignes, (f"{len(lignes)} projet(s)." if lignes else
                    "Aucun projet : ajoute-les dans l'onglet Projets de societe.xlsx (bouton ci-dessous).")


def remplir_revenus(_annee=None) -> tuple[list[tuple], str]:
    lignes = lignes_revenus(societe.charger())
    return lignes, (f"{len(lignes)} source(s) de revenus." if lignes else
                    "Aucune source de revenus : ajoute-les dans l'onglet Revenus de societe.xlsx (bouton ci-dessous).")
