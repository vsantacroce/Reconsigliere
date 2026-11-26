"""Extracteurs spécialisés (données fictives)."""

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere.importation import extracteurs  # noqa: E402
from reconsigliere.importation.continuite import Section  # noqa: E402
from reconsigliere.importation.pages import Page  # noqa: E402


def section(type_, *textes, tableau=None):
    return Section(type=type_, pages=[Page(numero=i + 1, texte="\n".join(t), tableau=tableau)
                                       for i, t in enumerate(textes)])


class TestPlanComptable(unittest.TestCase):
    def test_texte(self):
        s = section("plan_comptable", ["Plan comptable", "Code Nom Type", "0100 Caisse Banque et espèces",
                                       "227101 Brevet PAT01 Actifs non-circulants", "2000 Créanciers Payable"])
        lignes = extracteurs.extraire(s, 2024, "plan.pdf")["plancomptable"]
        self.assertEqual([l["code"] for l in lignes], ["0100", "227101", "2000"])
        self.assertEqual(lignes[0]["nom"], "Caisse")
        self.assertEqual(lignes[0]["type"], "Banque et espèces")
        self.assertEqual(lignes[1]["exercice"], 2024)
        self.assertEqual(lignes[2]["source"], "plan.pdf p.1")

    def test_excel(self):
        df = pd.DataFrame({"Code": ["0100", "1020"], "Nom du compte": ["Caisse", "Banque"],
                           "Type": ["Banque et espèces", None]})
        lignes = extracteurs.extraire(section("plan_comptable", ["x"], tableau=df), 2024, "p.xlsx")["plancomptable"]
        self.assertEqual(lignes[0], {"code": "0100", "nom": "Caisse", "type": "Banque et espèces",
                                     "exercice": 2024, "source": "p.xlsx p.1"})
        self.assertEqual(lignes[1]["type"], "")


class TestGrandLivre(unittest.TestCase):
    def test_texte_debit_credit_non_signes(self):
        s = section("grand_livre",
                    ["Grand livre 2024", "Date Pièce Libellé Débit Crédit Solde", "1020 Banque",
                     "05.01.2024 BILL/2024/01/0001 Loyer janvier 0.00 1'200.00 -1'200.00",
                     "07.01.2024 INV/2024/0001 Vente 2'000.00 0.00 800.00"],
                    ["Report 800.00", "6000 Loyers", "05.01.2024 BILL/2024/01/0001 Loyer janvier 1'200.00 0.00 1'200.00",
                     "Total 6000 1'200.00 0.00"])
        gl = extracteurs.extraire(s, 2024, "gl.pdf")["grandlivre"]
        self.assertEqual(len(gl), 3)
        self.assertEqual(gl[0]["date"], "2024-01-05")
        self.assertEqual(gl[0]["compte"], "1020")
        self.assertEqual(gl[0]["libelle_compte"], "Banque")
        self.assertEqual(gl[0]["piece"], "BILL/2024/01/0001")
        self.assertEqual(gl[0]["libelle"], "Loyer janvier")
        self.assertIsNone(gl[0]["debit"])
        self.assertEqual(gl[0]["credit"], 1200.0)
        self.assertEqual(gl[1]["debit"], 2000.0)
        self.assertEqual(gl[2]["compte"], "6000")
        self.assertEqual(gl[2]["source"], "gl.pdf p.2")
        self.assertEqual(gl[0]["partenaire"], "")

    def test_texte_partenaire_separe_par_tiret(self):
        s = section("grand_livre", ["Grand livre 2024", "1020 Banque",
                                    "05.01.2024 BILL/2024/01/0001 - Fournisseur SA - Loyer janvier 0.00 1'200.00",
                                    "06.01.2024 Client SA - Acompte 500.00 0.00",
                                    "07.01.2024 BNK1/2024/0003 Frais bancaires 0.00 12.50"])
        gl = extracteurs.extraire(s, 2024, "gl.pdf")["grandlivre"]
        self.assertEqual([(l["piece"], l["partenaire"], l["libelle"]) for l in gl],
                         [("BILL/2024/01/0001", "Fournisseur SA", "Loyer janvier"),
                          ("", "Client SA", "Acompte"), ("BNK1/2024/0003", "", "Frais bancaires")])

    def test_excel_odoo_compte_combine_et_montant_signe(self):
        df = pd.DataFrame({
            "Compte": ["1020 Banque", None, "6000 Loyers"],
            "Date": ["05.01.2024", "07.01.2024", "2024-01-05"],
            "Écriture": ["BILL/2024/01/0001", "INV/2024/0001", "BILL/2024/01/0001"],
            "Partenaire": ["Fournisseur SA", "/", "Fournisseur SA"],
            "Libellé": ["Loyer", "Vente", "Loyer"],
            "Montant": ["-1'200.00", "2000", "1200.00"],
        })
        gl = extracteurs.extraire(section("grand_livre", ["x"], tableau=df), 2024, "gl.xlsx")["grandlivre"]
        self.assertEqual([l["compte"] for l in gl], ["1020", "1020", "6000"])
        self.assertEqual(gl[0]["libelle_compte"], "Banque")
        self.assertEqual((gl[0]["debit"], gl[0]["credit"]), (None, 1200.0))
        self.assertEqual((gl[1]["debit"], gl[1]["credit"]), (2000.0, None))
        self.assertEqual(gl[1]["partenaire"], "")
        self.assertEqual(gl[2]["date"], "2024-01-05")
        self.assertEqual(gl[0]["piece"], "BILL/2024/01/0001")

    def test_excel_colonnes_debit_credit(self):
        df = pd.DataFrame({"Date": ["31.01.2024"], "Compte": ["0100"], "Débit": ["50.00"], "Crédit": [None]})
        gl = extracteurs.extraire(section("grand_livre", ["x"], tableau=df), 2024, "g.csv")["grandlivre"]
        self.assertEqual(gl[0]["compte"], "0100")
        self.assertEqual((gl[0]["debit"], gl[0]["credit"]), (50.0, None))


class TestEtats(unittest.TestCase):
    def test_bilan_deux_colonnes_et_niveaux(self):
        s = section("bilan", ["Bilan au 31.12.2024", "2024 2023", "Actifs", "Actifs circulants",
                              "1020 Banque 12'500.00 10'000.00", "Total des actifs 12'500.00 10'000.00",
                              "Passifs", "Perte reportée (1'000.00) -500.00"])
        b = extracteurs.extraire(s, 2024, "b.pdf")["bilan"]
        self.assertEqual(len(b), 3)
        self.assertEqual(b[0], {"rubrique": "Actifs / Actifs circulants", "compte": "1020", "libelle": "Banque",
                                "montant": 12500.0, "colonne_exercice_precedent": 10000.0, "niveau": 3,
                                "exercice": 2024, "source": "b.pdf p.1"})
        self.assertEqual(b[1]["niveau"], 1)
        self.assertEqual(b[1]["libelle"], "Total des actifs")
        self.assertEqual(b[2]["montant"], -1000.0)
        self.assertEqual(b[2]["colonne_exercice_precedent"], -500.0)
        self.assertEqual(b[2]["rubrique"], "Passifs")

    def test_compte_resultat_signe_garde(self):
        s = section("compte_resultat", ["Compte de résultat 2024", "Charges", "6000 Loyer -12'000.00",
                                        "Résultat de l'exercice -12'000.00"])
        r = extracteurs.extraire(s, 2024, "r.pdf")["compteresultat"]
        self.assertEqual(r[0]["montant"], -12000.0)
        self.assertEqual((r[1]["niveau"], r[1]["rubrique"]), (1, ""))
        self.assertIsNone(r[0]["colonne_exercice_precedent"])

    def test_annexe_texte(self):
        s = section("annexe", ["Annexe 2024", "Principes comptables"], ["Suite"])
        a = extracteurs.extraire(s, 2024, "a.pdf")["annexe"]
        self.assertEqual([x["page"] for x in a], [1, 2])
        self.assertIn("Principes comptables", a[0]["texte"])


if __name__ == "__main__":
    unittest.main()
