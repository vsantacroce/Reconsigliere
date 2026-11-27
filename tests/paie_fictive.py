"""Classeur de paie fictif à la forme du classeur 2025 (onglets EMPLOYES, ANNEE, PAYé, Bank Transactions AAAA).

Trois employés fictifs, un cas de chaque règle d'imputation :
- Durand Alice : salaire 9'449.85 ; avril viré avec 431.75 de frais (9'881.60) ; frais de 1'838.01 marqués « Régularisation » ;
  solde de l'année précédente 5'000.00 ; prêt 5'000.00 ; remboursement de frais 110.80.
- Meier Bruno : salaire 4'885.50 ; mai viré avec 538.95 de frais (5'424.45).
- Rossi Carla : salaire 9'654.80 ; 391.49 = 286.17 de solde de l'année précédente + 105.32 de frais.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import openpyxl

MOIS = ["janv", "févr", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc"]
EMPLOYES = ["Durand Alice", "Meier Bruno", "Rossi Carla"]

# (employé, code, {mois (1-12): montant}) - lignes de l'onglet PAYé
PAYE = [
    ("Durand Alice", "V1", {1: 9449.85, 2: 9449.85, 3: 9449.85, 4: 9449.85}),
    ("Durand Alice", "PAYE FRAIS", {1: 1838.01, 3: 110.80}),
    ("Durand Alice", "PAYE FRAIS", {4: 431.75}),
    ("Durand Alice", "PAYE HP", {6: 5000.00}),
    ("Meier Bruno", "V1", {4: 4885.50, 5: 4885.50}),
    ("Meier Bruno", "PAYE FRAIS", {4: 538.95}),
    ("Rossi Carla", "V1", {5: 9654.80, 6: 9654.80}),
    ("Rossi Carla", "PAYE FRAIS", {6: 105.32}),
    ("Rossi Carla", "PAYE HP", {6: 286.17}),
]

# (date, employé, type, montant, libellé, écriture)
VIREMENTS = [
    ("2025-01-24", "Durand Alice", "Régularisation 2024", 1838.01, "purchase of software", "BNK/2025/00001"),
    ("2025-02-05", "Durand Alice", "Salaire jan", 9449.85, "salary", "BNK/2025/00002"),
    ("2025-03-06", "Durand Alice", "Salaire fev", 9449.85, "salary", "BNK/2025/00003"),
    ("2025-04-02", "Durand Alice", "Salaire mar", 9449.85, "salary", "BNK/2025/00004"),
    ("2025-04-02", "Durand Alice", "Remboursement de frais mars", 110.80, "reimbursement", "BNK/2025/00005"),
    ("2025-05-02", "Durand Alice", "Salaire Avril", 9881.60, "salary", "BNK/2025/00006"),
    ("2025-06-24", "Durand Alice", "Régularisation 2024", 5000.00, "salary correction", "BNK/2025/00007"),
    ("2025-06-26", "Durand Alice", "Prêt / avance", 5000.00, "loan", "BNK/2025/00008"),
    ("2025-05-02", "Meier Bruno", "Salaire + remboursement", 5424.45, "salary + reimbursement", "BNK/2025/00009"),
    ("2025-05-27", "Meier Bruno", "Salaire", 4885.50, "salary", "BNK/2025/00010"),
    ("2025-05-27", "Rossi Carla", "Salaire", 9654.80, "salary", "BNK/2025/00011"),
    ("2025-06-23", "Rossi Carla", "Salaire", 391.49, "Debit salary", "BNK/2025/00012"),
    ("2025-06-24", "Rossi Carla", "Salaire", 9654.80, "salary", "BNK/2025/00013"),
]

NET_DU = {"Durand Alice": 38200.00, "Meier Bruno": 9771.00, "Rossi Carla": 19309.60}


def verse_paye(employe: str) -> float:
    return round(sum(m for e, code, mois in PAYE if e == employe and code == "V1" for m in mois.values()), 2)


def creer_classeur_paie(chemin: Path, annee: int = 2025, verse: dict | None = None) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SCHEMA"
    ws["B1"] = "FLUX DU CLASSEUR DE PAIE"

    emp = wb.create_sheet("EMPLOYES")
    emp["A1"] = "EMPLOYES — liste maîtresse"
    emp.append([])
    for i, titre in enumerate(["ID", "Nom complet", "Sexe", "N° AVS", "Entrée", "Sortie", "Actif", "Notes"], 1):
        emp.cell(6, i, titre)
    for i, nom in enumerate(EMPLOYES, 7):
        emp.cell(i, 1, f"E{i - 6}")
        emp.cell(i, 2, nom)
        emp.cell(i, 7, "Oui")
    emp.cell(10, 1, "E4")  # emplacement libre

    an = wb.create_sheet("ANNEE")
    an["A1"], an["B1"] = "ANNÉE", annee
    for col, titre in [(1, "Employé"), (50, "Net définitif"), (51, "Net selon ODOO"), (52, "Versé selon PAYE"),
                       (53, "Correction (de Fin d'année)"), (54, "Notes")]:
        an.cell(5, col, titre)
    an.cell(7, 1, "TOTAUX")
    verse = verse or {}
    for i, nom in enumerate(EMPLOYES, 8):
        an.cell(i, 1, f"{i - 7:02d} — {nom}")
        an.cell(i, 50, NET_DU[nom])
        an.cell(i, 52, verse.get(nom, verse_paye(nom)))
        an.cell(i, 54, "Année complète")
        an.cell(i, 56, nom)
    an.cell(11, 1, "E4 — emplacement libre")

    pay = wb.create_sheet("PAYé")
    pay["A1"], pay["G1"] = "PAYÉ - Transactions bancaire", annee
    pay.cell(5, 1, "Rubrique")
    for m, nom_mois in enumerate(MOIS, 5):
        pay.cell(5, m, nom_mois)
    r = 7
    for n, nom in enumerate(EMPLOYES, 1):
        pay.cell(r, 1, f"E{n} — {nom}")
        r += 1
        for e, code, mois in PAYE:
            if e != nom:
                continue
            pay.cell(r, 1, f"{nom} · {code}")
            pay.cell(r, 2, code)
            for m, montant in mois.items():
                pay.cell(r, 4 + m, montant)
            r += 1
        pay.cell(r, 1, f"TOTAL VERSÉ {nom}")
        pay.cell(r, 2, "PAYE TOT")
        r += 2

    bk = wb.create_sheet(f"Bank Transactions {annee}")
    bk.append(["Date", "Employé", "Type", "Montant (CHF)", "IBAN (relevé)", "IBAN de référence", "Libellé", "Partenaire",
               "Catégorie", "Sous-catégorie", "Banque", "Écriture comptable", "Ordre passé par", "Rapprochement fiche",
               "InvID"])
    for i, (jour, nom, typ, montant, libelle, piece) in enumerate(VIREMENTS):
        d = jour if i % 2 else datetime.strptime(jour, "%Y-%m-%d")  # dates en texte et en date, comme dans le réel
        bk.append([d, nom, typ, montant, None, None, libelle, f"Société fictive SA, {nom}", "Salaires & RH", None,
                   "BANQUE-CHF", piece, "Société fictive SA", "à vérifier" if i % 3 == 0 else "OK — net de fiche", i])
    bk.append([None, None, "TOTAL", 99999.99])
    chemin.parent.mkdir(parents=True, exist_ok=True)
    wb.save(chemin)
    return chemin
