"""Tests du référentiel versionné par exercice : python -m unittest discover -s tests

Toutes les données sont fictives.
"""

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import config, exercices, installation, societe  # noqa: E402
from test_societe import classeur_brevets  # noqa: E402


def import_normalise(chemin: Path, annee: int) -> None:
    """Classeur au format du pipeline d'import : onglets PlanComptable et GrandLivre."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    plan = wb.active
    plan.title = "PlanComptable"
    plan.append(["code", "nom", "type", "exercice", "source"])
    for code, nom, genre in [("1020", "Banque", "Actif"), ("2000", "Créanciers", "Passif"),
                             ("1700", "Brevets", "Actif"), ("6510", "Téléphone et internet", "Charge"),
                             ("6570", "Informatique", "Charge"), ("3200", "Ventes de services", "Produit")]:
        plan.append([code, nom, genre, annee, "plan.pdf, p. 1"])
    gl = wb.create_sheet("GrandLivre")
    gl.append(["date", "compte", "libelle_compte", "piece", "partenaire", "libelle", "debit", "credit",
               "exercice", "source"])
    lignes = []
    for i in range(5):
        lignes += [(f"{annee}-0{i + 1}-15", "6510", "Téléphone et internet", f"BILL/{i}", "Telco SA", "Abonnement", 80.0, None),
                   (f"{annee}-0{i + 1}-15", "2000", "Créanciers", f"BILL/{i}", "Telco SA", "Abonnement", None, 80.0)]
    lignes += [(f"{annee}-06-01", "6570", "Informatique", "BILL/9", "Telco SA", "Routeur", 300.0, None),
               (f"{annee}-07-01", "1700", "Brevets", "BILL/10", "Cabinet Brevets", "Dépôt", 1000.0, None),
               (f"{annee}-07-01", "2000", "Créanciers", "BILL/10", "Cabinet Brevets", "Dépôt", None, 1000.0),
               (f"{annee}-07-02", "1020", "Banque", "BNK/1", "Cabinet Brevets", "Paiement", None, 1000.0),
               (f"{annee}-08-01", "6570", "Informatique", "BILL/11", "/", "Sans partenaire", 50.0, None),
               (f"{annee - 1}-12-31", "6570", "Informatique", "BILL/0", "Ancien SA", "Autre exercice", 10.0, None)]
    for date_, compte, lib, piece, partenaire, libelle, debit, credit in lignes:
        exercice = int(date_[:4])
        gl.append([date_, compte, lib, piece, partenaire, libelle, debit, credit, exercice, "gl.pdf, p. 2"])
    wb.save(chemin)


class TestExercices(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name) / "R"
        self._ancienne = config.RACINE
        installation.creer_dossiers(self.racine)
        config.definir_racine(self.racine)
        classeur_brevets(societe.dossier_societe() / "brevets.xlsx")
        import_normalise(exercices.dossier_imports(2024) / "export_2024.xlsx", 2024)

    def tearDown(self):
        config.definir_racine(self._ancienne)
        for p in self.racine.rglob("*"):
            if p.is_file():
                os.chmod(p, 0o644)
        self._tmp.cleanup()

    def test_construire_premier_exercice(self):
        compteurs = exercices.construire(2024)
        self.assertEqual(compteurs["PlanComptable"], 6)
        listes = exercices.lire(2024)
        partenaires = {p["partenaire"]: p for p in listes["Partenaires"]}
        self.assertEqual(set(partenaires), {"Telco SA", "Cabinet Brevets"})   # « / » et autre exercice ignorés
        self.assertEqual(partenaires["Telco SA"]["compte"], "6510")            # 5 fois sur 6, créanciers ignorés
        self.assertEqual(partenaires["Telco SA"]["part"], 0.83)
        self.assertEqual(partenaires["Cabinet Brevets"]["compte"], "1700")     # banque ignorée
        brevets = {b["id"]: b for b in listes["Brevets"]}
        self.assertEqual(brevets["FAM02"]["statut"], "En cours")              # abandonné seulement fin 2025
        self.assertNotIn("FAM03-EP", brevets)                                  # annoncé en 2025
        self.assertEqual(brevets["FAM01-02"]["delivrance"], None)              # délivré en 2026
        self.assertEqual(exercices.exercice_courant(), 2024)

    def test_societe_ignore_les_dossiers_d_exercices(self):
        exercices.construire(2024)
        etat = societe.charger(date(2026, 6, 30))
        self.assertEqual(etat.fichiers, ["brevets.xlsx"])

    def test_valider_verrouille_et_ouvre_le_suivant(self):
        exercices.construire(2024)
        self.assertEqual(exercices.valider(2024), 2025)
        self.assertTrue(exercices.est_valide(2024))
        self.assertFalse(exercices.fichier_referentiel(2024).stat().st_mode & 0o222)
        self.assertIsNone(exercices.verifier(2024))
        self.assertEqual(exercices.exercice_courant(), 2025)
        self.assertEqual(exercices.lire(2025)["Partenaires"], exercices.lire(2024)["Partenaires"])
        self.assertEqual(exercices.lire(2025)["Changements"], [])
        with self.assertRaises(exercices.ExerciceVerrouille):
            exercices.demander_changement(2024, "retrait", "Brevets", "FAM02", motif="test")
        with self.assertRaises(exercices.ExerciceVerrouille):
            exercices.construire(2024)

    def test_changements_et_ecarts(self):
        exercices.construire(2024)
        exercices.valider(2024)
        exercices.demander_changement(2025, "retrait", "Brevets", "FAM02", motif="Abandonné au 31.12.2025",
                                      quand=date(2025, 12, 31))
        exercices.demander_changement(2025, "ajout", "PlanComptable", "1720",
                                      {"nom": "Brevets en cours", "type": "Actif"}, motif="Séparer les dépôts en cours")
        exercices.demander_changement(2025, "modification", "Partenaires", "Telco SA", {"compte": "6570"},
                                      motif="Abonnement reclassé en informatique")
        changements = exercices.lire(2025)["Changements"]
        self.assertEqual([c["action"] for c in changements], ["retrait", "ajout", "modification"])
        self.assertEqual(changements[2]["avant"], "6510")
        self.assertEqual(changements[2]["apres"], "6570")
        e = {(x.liste, x.cle, x.nature, x.champ) for x in exercices.ecarts(2025)}
        self.assertEqual(e, {("Brevets", "FAM02", "retrait", ""), ("PlanComptable", "1720", "ajout", ""),
                             ("Partenaires", "Telco SA", "modification", "compte")})
        with self.assertRaises(ValueError):
            exercices.demander_changement(2025, "ajout", "PlanComptable", "1720", {"nom": "x"}, motif="doublon")
        with self.assertRaises(ValueError):
            exercices.demander_changement(2025, "retrait", "Brevets", "FAM99", motif="inconnu")
        with self.assertRaises(ValueError):
            exercices.demander_changement(2025, "retrait", "Brevets", "FAM01-01", motif="  ")
        with self.assertRaises(ValueError):
            exercices.construire(2025)   # des changements existent déjà

    def test_suggestions_depuis_les_fichiers(self):
        exercices.construire(2024)
        exercices.valider(2024)
        # Aucun grand livre 2025 : partenaires et plan comptable ne sont pas comparés.
        e = {(x.liste, x.cle, x.nature, x.champ): x for x in exercices.suggestions(2025)}
        self.assertFalse(any(k[0] in ("Partenaires", "PlanComptable") for k in e))
        self.assertIn(("Brevets", "FAM03-EP", "ajout", ""), e)              # entrée annoncée en 2025
        self.assertIn(("Brevets", "FAM02", "modification", "statut"), e)    # abandonné au 31.12.2025
        self.assertEqual(e[("Brevets", "FAM02", "modification", "statut")].apres, "Abandonné")
        exercices.appliquer(2025, e[("Brevets", "FAM03-EP", "ajout", "")], "Selon le classeur des brevets")
        exercices.appliquer(2025, e[("Brevets", "FAM02", "modification", "statut")], "Selon le classeur des brevets")
        brevets = {b["id"]: b for b in exercices.lire(2025)["Brevets"]}
        self.assertEqual(brevets["FAM03-EP"]["pays"], "EP")
        self.assertEqual(brevets["FAM02"]["statut"], "Abandonné")
        restantes = {(x.liste, x.cle, x.nature, x.champ) for x in exercices.suggestions(2025)}
        self.assertNotIn(("Brevets", "FAM03-EP", "ajout", ""), restantes)
        self.assertIn(("Brevets", "FAM02", "modification", "abandon"), restantes)

    def test_modification_apres_validation_detectee(self):
        exercices.construire(2024)
        exercices.valider(2024)
        chemin = exercices.fichier_referentiel(2024)
        os.chmod(chemin, 0o644)
        wb = openpyxl.load_workbook(chemin)
        wb["PlanComptable"].append(["9999", "Ajout en douce", ""])
        wb.save(chemin)
        self.assertIn("modifié après sa validation", exercices.verifier(2024))

    def test_rouvrir_exige_un_motif(self):
        exercices.construire(2024)
        exercices.valider(2024)
        with self.assertRaises(ValueError):
            exercices.rouvrir(2024, " ")
        exercices.rouvrir(2024, "Correction demandée par la fiduciaire")
        self.assertFalse(exercices.est_valide(2024))
        historique = exercices.lire_etat(2024)["historique"]
        self.assertEqual(historique[-1]["motif"], "Correction demandée par la fiduciaire")
        exercices.demander_changement(2024, "modification", "PlanComptable", "6510", {"nom": "Télécom"},
                                      motif="Libellé corrigé")
        self.assertIsNone(exercices.valider(2024))   # 2025 existe déjà : pas de nouvelle copie

    def test_comptes_proposes_selon_l_exercice(self):
        exercices.construire(2024)
        exercices.valider(2024)
        exercices.demander_changement(2025, "modification", "Partenaires", "Telco SA", {"compte": "6570"},
                                      motif="Reclassement")
        transactions = [
            {"partenaire_trouve": "Telco SA", "date": date(2024, 3, 1), "libelle": ""},
            {"partenaire_trouve": "Telco SA", "date": date(2025, 3, 1), "libelle": ""},
            {"partenaire_trouve": "", "date": date(2025, 4, 1), "libelle": "PAIEMENT CABINET BREVETS FACT 12"},
            {"partenaire_trouve": "Inconnu", "date": date(2025, 4, 1), "libelle": "rien"},
        ]
        self.assertEqual(exercices.proposer_comptes(transactions), 3)
        self.assertTrue(transactions[0]["compte_propose"].startswith("6510"))
        self.assertEqual(transactions[0]["compte_reference"], "6510")
        self.assertEqual(transactions[3]["compte_reference"], "")
        self.assertIn("référentiel 2024", transactions[0]["fiabilite_compte"])
        self.assertTrue(transactions[1]["compte_propose"].startswith("6570"))
        self.assertEqual(transactions[2]["compte_propose"], "1700 Brevets")
        self.assertIn("selon libellé", transactions[2]["fiabilite_compte"])
        self.assertEqual(transactions[3]["compte_propose"], "")

    def test_sans_exercice_aucune_proposition(self):
        t = [{"partenaire_trouve": "Telco SA", "date": date(2024, 3, 1), "libelle": ""}]
        self.assertEqual(exercices.proposer_comptes(t), 0)
        self.assertEqual(t[0]["compte_propose"], "")


if __name__ == "__main__":
    unittest.main()
