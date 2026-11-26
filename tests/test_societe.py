"""Tests de l'état de la société (brevets, coûts, journal) : python -m unittest discover -s tests

Toutes les données sont fictives.
"""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import config, installation, societe  # noqa: E402

AUJOURD_HUI = date(2026, 6, 30)


def classeur_brevets(chemin: Path) -> None:
    """Même forme que le classeur des brevets tenu à la main : onglet IP + onglets Détail AAAA."""
    wb = openpyxl.Workbook()
    ip = wb.active
    ip.title = "IP"
    ip.append(["ID", "Title", "Patent number", "Filing date", "Approved date", "Abandon date",
               "Patent owner", "Author", "Notes"])
    ip.append(["FAM01-01", "Filtre fictif", "WO2020/000001A1", "01.02.2020", None, None,
               "Université X\nExclusive license to Exemple SA", "A. Auteur", None])
    ip.append(["FAM01-02", "Filtre fictif", "EU: EP0000001", "05.03.2022", "10.01.2026", None,
               "Université X\nExclusive license to Exemple SA", "A. Auteur", None])
    ip.append(["FAM02", "Antenne fictive", "WO2023/000002A1", "01.06.2023", None, "31.12.2025",
               "Exemple SA", "B. Auteur", "Abandoned on 31.12.2025"])
    ip.append(["FAM03", "Guide fictif", "WO2024/000003A1\nEU, CN: submitted July 2025", "06.09.2024",
               None, None, "Exemple SA", "B. Auteur", "Used in all projects as of 31.12.2027"])

    entete = ["N° pièce (Odoo)", "Fournisseur", "Facture fournisseur", "Date facture", "Devise", "Brevet",
              "Description de la ligne", "Montant HT (devise)", "Taux → CHF", "Montant HT CHF",
              "Classification", "Nature", "Remarques"]
    d24 = wb.create_sheet("Détail 2024")
    d24.append(entete)
    d24.append(["BILL/1", "Cabinet", "F1", "12.01.2024", "CHF", "FAM02 – Antenne fictive", "Dépôt PCT",
                1000, 1, 1000, "Capitalisable", "Dépôt (filing)", None])
    d24.append(["BILL/2", "Cabinet", "F2", "15.03.2024", "CHF", "FAM01 – Filtre fictif (EP)",
                "Taxe officielle – 3e annuité EP0000001", 500, 1, 500, "Charge", "Annuité / maintien", None])
    d24.append([None, "Sous-total 2024 (CHF)", None, None, None, None, None, None, None, 1000, "Capitalisable", None, None])
    d25 = wb.create_sheet("Détail 2025")
    d25.append(entete)
    d25.append(["BILL/3", "Cabinet", "F3", "20.02.2025", "CHF", "FAM01 – Filtre fictif (EP)",
                "Taxe officielle – 4e annuité EP0000001", 600, 1, 600, "Charge", "Annuité / maintien", None])
    d25.append(["BILL/4", "Office", "F4", "22.09.2025", "EUR", "FAM01 ou FAM03 – réf. à confirmer",
                "Examination fee", 1000, 0.95, 950, "Capitalisable", "Entrée phase EP", None])
    d25.append(["BILL/5", "Cabinet", "F5", "01.10.2025", "CHF", "FAM01 – Filtre fictif (CN)",
                "Réponse office action", 0, 1, 0, "Capitalisable", "Procédure",
                "DOUBLON de BILL/6, montant neutralisé"])
    d25.append(["BILL/6", "Cabinet", "F5", "01.10.2025", "CHF", "FAM01 – Filtre fictif (CN)",
                "Réponse office action", 300, 1, 300, "Capitalisable", "Procédure",
                "Facture retenue ; BILL/5 est son doublon"])
    wb.save(chemin)


class TestSociete(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name) / "R"
        self._ancienne = config.RACINE
        installation.creer_dossiers(self.racine)
        config.definir_racine(self.racine)
        classeur_brevets(societe.dossier_societe() / "brevets.xlsx")

    def tearDown(self):
        config.definir_racine(self._ancienne)
        self._tmp.cleanup()

    def test_dossier_cree(self):
        self.assertTrue((self.racine / "entrees" / "06_societe" / "LISEZMOI.md").exists())

    def test_brevets_familles_et_depots(self):
        societe.creer_modele_si_absent()
        d = societe.synthese(societe.charger(AUJOURD_HUI))
        familles = {f["famille"]: f for f in d["familles"]}
        self.assertEqual(set(familles), {"FAM01", "FAM02", "FAM03", "FAM01 + FAM03"})
        self.assertEqual(familles["FAM01"]["statut"], "Délivrée (au moins un pays)")
        self.assertTrue(familles["FAM01"]["licence"])
        self.assertEqual(familles["FAM02"]["statut"], "Abandonnée")
        self.assertEqual(familles["FAM03"]["pays"], ["CN", "EP"])
        self.assertEqual(familles["FAM01 + FAM03"]["statut"], "À répartir")
        ep = [x for x in familles["FAM01"]["depots"] if x["pays"] == "EP"][0]
        self.assertEqual(ep["numero"], "EP0000001")
        c = d["compteurs"]
        self.assertEqual((c["familles"], c["familles_actives"]), (3, 2))
        self.assertEqual(c["depots_actifs"], 3)      # FAM01 WO + EP, FAM03 WO
        self.assertEqual(c["entrees_annoncees"], 2)  # FAM03 EP + CN

    def test_couts_et_totaux(self):
        d = societe.synthese(societe.charger(AUJOURD_HUI))
        self.assertEqual(d["compteurs"]["capitalisable"], 2250.0)   # sous-total ignoré, doublon à 0
        self.assertEqual(d["compteurs"]["charge"], 1100.0)
        self.assertEqual([a["annee"] for a in d["annees"]], [2024, 2025])
        self.assertEqual(d["annees"][-1]["cumul_capitalisable"], 2250.0)
        fam01 = [f for f in d["familles"] if f["famille"] == "FAM01"][0]
        self.assertEqual(fam01["dernieres_annuites"][0]["date"], "2025-02-20")

    def test_points_d_attention(self):
        points = " | ".join(societe.synthese(societe.charger(AUJOURD_HUI))["attention"])
        self.assertIn("FAM02 est abandonnée au 31.12.2025 : 1'000.00 CHF", points)
        self.assertIn("FAM01 + FAM03", points)
        self.assertIn("BILL/5", points)
        self.assertNotIn("BILL/6", points)
        self.assertIn("31.12.2027", points)

    def test_journal_projets_revenus(self):
        chemin = societe.creer_modele_si_absent()
        wb = openpyxl.load_workbook(chemin)
        wb["Projets"].append(["Projet A", "oui", "FAM01", None, None, "En cours", 5000, None])
        wb["Projets"].append(["Projet B", "non", None, None, None, "Idée", None, None])
        wb["Revenus"].append(["Licence", "Client", "Licence", "C1", None, "31.12.2025", 2000, "3400", "Actif", None])
        wb["Revenus"].append(["Service", "Client", "Développement", "C2", None, None, 3000, "3200", "Actif", None])
        wb.save(chemin)
        societe.ajouter_au_journal(date(2026, 6, 1), "Brevet", "Dépôt CN", "FAM03", 120.5)
        donnees, page = societe.actualiser(AUJOURD_HUI)
        c = donnees["compteurs"]
        self.assertEqual((c["projets"], c["projets_capitalisables"]), (2, 1))
        self.assertEqual((c["revenus_actifs"], c["revenus_annuels"]), (1, 3000.0))
        self.assertEqual(donnees["journal"][0]["evenement"], "Dépôt CN")
        self.assertEqual(donnees["journal"][0]["montant"], 120.5)
        self.assertTrue(page.exists())
        self.assertNotIn("__DONNEES__", page.read_text(encoding="utf-8"))

    def test_modele_jamais_ecrase(self):
        chemin = societe.creer_modele_si_absent()
        societe.ajouter_au_journal(date(2026, 1, 1), "Autre", "Garder", "", None)
        societe.creer_modele_si_absent()
        self.assertEqual(societe.synthese(societe.charger(AUJOURD_HUI))["journal"][0]["evenement"], "Garder")
        self.assertTrue(chemin.exists())

    def test_format_chf(self):
        self.assertEqual(societe.format_chf(44095.5), "44'095.50")
        self.assertEqual(societe.format_chf(-1234567.891), "−1'234'567.89")
        self.assertEqual(societe.format_chf(0), "0.00")


if __name__ == "__main__":
    unittest.main()
