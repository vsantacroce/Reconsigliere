"""Pages, classement et continuité du pipeline d'import (données fictives)."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pdf_fictif import ecrire_pdf  # noqa: E402
from reconsigliere.importation import classement, continuite, pages  # noqa: E402
from reconsigliere.importation.pages import Page  # noqa: E402

BILAN = ["Societe Fictive SA", "Bilan au 31.12.2024", "Actifs", "Actifs circulants",
         "1020 Banque 12'500.00 10'000.00", "Total des actifs 12'500.00 10'000.00",
         "Passifs", "Capital-actions 100'000.00", "Total des passifs 12'500.00 10'000.00"]
PNL = ["Compte de résultat 2024", "Produits", "3200 Ventes 50'000.00", "Charges",
       "6000 Loyer -12'000.00", "Résultat de l'exercice 38'000.00"]
GL1 = ["Grand livre du 01.01.2024 au 31.12.2024", "Date Compte Pièce Libellé Débit Crédit Solde",
       "1020 Banque", "05.01.2024 BILL/2024/01/0001 Fournisseur SA Loyer 0.00 1'200.00 -1'200.00",
       "07.01.2024 INV/2024/0001 Client SA Vente 2'000.00 0.00 800.00", "Page 1/2"]
GL2 = ["Report 800.00", "12.02.2024 BILL/2024/02/0004 Fournisseur SA Loyer 0.00 1'200.00 -400.00",
       "28.02.2024 INV/2024/0002 Client SA Vente 2'000.00 0.00 1'600.00", "Page 2/2"]
GL3 = ["12.03.2024 BILL/2024/03/0001 Fournisseur SA Loyer 0.00 1'200.00 400.00",
       "14.03.2024 INV/2024/0003 Client SA Vente 1'000.00 0.00 1'400.00"]
PLAN = ["Plan comptable", "Code Nom Type", "1000 Caisse Actifs circulants",
        "1020 Banque Banque et espèces", "2000 Créanciers Payable"]
ANNEXE = ["Annexe aux comptes annuels 2024", "1. Principes comptables",
          "Les présents comptes ont été établis selon le droit suisse (art. 957 ss CO)."]


def page(lignes, n=1, tableau=None):
    return Page(numero=n, texte="\n".join(lignes), tableau=tableau)


class TestPages(unittest.TestCase):
    def test_pdf_une_page_par_page(self):
        with tempfile.TemporaryDirectory() as d:
            p = ecrire_pdf(Path(d) / "doc.pdf", [BILAN, PNL])
            res = pages.lire_pages(p)
        self.assertEqual([x.numero for x in res], [1, 2])
        self.assertIn("Bilan au 31.12.2024", res[0].texte)
        self.assertTrue(res[0].lisible)

    def test_page_pdf_vide_sans_ocr_illisible(self):
        with tempfile.TemporaryDirectory() as d:
            p = ecrire_pdf(Path(d) / "scan.pdf", [[], PNL])
            res = pages.lire_pages(p, ocr=lambda chemin, numero: "")
        self.assertFalse(res[0].lisible)
        self.assertTrue(res[1].lisible)

    def test_excel_une_page_par_feuille(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "classeur.xlsx"
            with pd.ExcelWriter(p) as w:
                pd.DataFrame({"Code": ["0100"], "Nom": ["Caisse"]}).to_excel(w, sheet_name="Plan", index=False)
                pd.DataFrame({"Date": ["01.01.2024"], "Débit": [1.0]}).to_excel(w, sheet_name="GL", index=False)
            res = pages.lire_pages(p)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].tableau["Code"].iloc[0], "0100")
        self.assertIn("Plan", res[0].texte)

    def test_csv_une_page(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "gl.csv"
            p.write_text("Date;Compte;Débit;Crédit\n01.01.2024;1020;10;\n", encoding="utf-8")
            res = pages.lire_pages(p)
        self.assertEqual(len(res), 1)
        self.assertEqual(list(res[0].tableau.columns), ["Date", "Compte", "Débit", "Crédit"])
        self.assertEqual(res[0].tableau["Compte"].iloc[0], "1020")


class TestClassement(unittest.TestCase):
    def test_types_avec_titre(self):
        for lignes, attendu in [(BILAN, "bilan"), (PNL, "compte_resultat"), (GL1, "grand_livre"),
                                (PLAN, "plan_comptable"), (ANNEXE, "annexe")]:
            with self.subTest(attendu=attendu):
                type_, score, titre = classement.classer(page(lignes))
                self.assertEqual(type_, attendu)
                self.assertTrue(titre)

    def test_page_de_chiffres_indecise(self):
        type_, _, titre = classement.classer(page(["12.50 13.00", "Total 25.50"]))
        self.assertIsNone(type_)
        self.assertFalse(titre)

    def test_suite_de_grand_livre_sans_titre(self):
        type_, _, titre = classement.classer(page(GL2))
        self.assertFalse(titre)

    def test_tableau_grand_livre_par_entetes(self):
        df = pd.DataFrame(columns=["Date", "Compte", "Libellé", "Débit", "Crédit"])
        type_, _, _ = classement.classer(page(["Feuille1"], tableau=df))
        self.assertEqual(type_, "grand_livre")

    def test_tableau_plan_comptable_par_entetes(self):
        df = pd.DataFrame(columns=["Code", "Nom du compte", "Type"])
        type_, _, _ = classement.classer(page(["Export"], tableau=df))
        self.assertEqual(type_, "plan_comptable")


class TestContinuite(unittest.TestCase):
    def _typer(self, liste):
        ps = [page(l, n=i + 1) for i, l in enumerate(liste)]
        return continuite.regrouper(ps, [classement.classer(p) for p in ps])

    def test_grand_livre_sur_trois_pages(self):
        typees = self._typer([GL1, GL2, GL3])
        self.assertEqual([t for _, t, _ in typees], ["grand_livre"] * 3)
        self.assertEqual([m for _, _, m in typees], ["regles", "continuite", "continuite"])
        sections = continuite.en_sections(typees)
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(sections[0].pages), 3)

    def test_nouveau_titre_coupe(self):
        sections = continuite.en_sections(self._typer([BILAN, PNL, GL1, GL2]))
        self.assertEqual([s.type for s in sections], ["bilan", "compte_resultat", "grand_livre"])

    def test_page_sans_signe_reste_indecise(self):
        typees = self._typer([ANNEXE, ["12.50 13.00", "Total 25.50"]])
        self.assertEqual(typees[1][1], None)
        self.assertEqual(typees[1][2], "indecis")

    def test_premiere_page_indecise(self):
        typees = self._typer([["12.50 13.00"], BILAN])
        self.assertEqual(typees[0][2], "indecis")
        self.assertEqual(typees[1][1], "bilan")


if __name__ == "__main__":
    unittest.main()
