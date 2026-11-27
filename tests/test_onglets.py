"""Tests des onglets directs (Brevets, Projets, Revenus, Plan comptable, Partenaires…) : données fictives.

python -m unittest discover -s tests
"""

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import config, exercices, installation, onglets_societe, societe  # noqa: E402
from test_exercices import import_normalise  # noqa: E402
from test_societe import classeur_brevets  # noqa: E402


class TestOrdreDesOnglets(unittest.TestCase):
    def test_chaque_element_est_un_onglet_direct(self):
        titres = [titre for _cle, titre in onglets_societe.ONGLETS]
        self.assertEqual(titres, ["Réconciliation", "Documents", "Salaires", "Brevets", "Projets", "Revenus",
                                  "Plan comptable", "Partenaires", "Année comptable", "Apprentissage"])

    def test_plus_de_regroupement_flou(self):
        for _cle, titre in onglets_societe.ONGLETS:
            self.assertNotIn("État de la société", titre)
            self.assertNotIn("Exercice", titre)
            self.assertNotIn("Assistant", titre)

    def test_chaque_onglet_a_une_phrase_d_explication(self):
        for cle, _titre in onglets_societe.ONGLETS:
            self.assertTrue(onglets_societe.EXPLICATIONS.get(cle), cle)


class TestLignes(unittest.TestCase):
    def test_projets(self):
        etat = societe.Etat(aujourd_hui=date(2026, 1, 1), projets=[
            {"Projet": "Filtre X", "Capitalisable (oui/non)": "oui", "Brevets liés": "FAM01",
             "Début": date(2024, 3, 1), "Fin": None, "Statut": "En cours", "Montant activé CHF": 12500.5},
            {"Projet": None, "Statut": "ligne vide ignorée"}])
        self.assertEqual(onglets_societe.lignes_projets(etat),
                         [("Filtre X", "oui", "FAM01", "01.03.2024", "", "En cours", "12'500.50")])

    def test_revenus(self):
        etat = societe.Etat(aujourd_hui=date(2026, 1, 1), revenus=[
            {"Source": "Licence A", "Client": "Client SA", "Type": "Licence", "Contrat": "C-1",
             "Début": date(2025, 1, 1), "Fin": date(2027, 12, 31), "Montant annuel CHF": 30000,
             "Compte": 3400, "Statut": "Active"}])
        self.assertEqual(onglets_societe.lignes_revenus(etat),
                         [("Licence A", "Client SA", "Licence", "C-1", "01.01.2025", "31.12.2027", "30'000.00",
                           "3400", "Active")])


class TestReferentiel(unittest.TestCase):
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

    def test_sans_annee_construite(self):
        lignes, message = onglets_societe.lignes_referentiel(None, "PlanComptable")
        self.assertEqual(lignes, [])
        self.assertIn("Année comptable", message)

    def test_plan_comptable_et_partenaires(self):
        exercices.construire(2024)
        plan, message = onglets_societe.lignes_referentiel(2024, "PlanComptable")
        self.assertIn(("1020", "Banque", "Actif"), plan)
        self.assertEqual(len(plan), 6)
        self.assertIn("6 lignes", message)
        partenaires, _ = onglets_societe.lignes_referentiel(2024, "Partenaires")
        telco = [p for p in partenaires if p[0] == "Telco SA"][0]
        self.assertEqual(telco, ("Telco SA", "6510", "Téléphone et internet", "6", "83 %"))


class TestGeometrie(unittest.TestCase):
    def test_echelle_normale(self):
        self.assertEqual(onglets_societe.geometrie(1920, 1080, 1.0), "1040x900")

    def test_agrandissement_150(self):
        self.assertEqual(onglets_societe.geometrie(2880, 1620, 1.5), "1560x1350")

    def test_bornee_a_l_ecran(self):
        largeur, hauteur = map(int, onglets_societe.geometrie(1366, 768, 1.25).split("x"))
        self.assertLessEqual(largeur, 1366 - 40)
        self.assertLessEqual(hauteur, 768 - 80)


if __name__ == "__main__":
    unittest.main()
