"""Lecture des imports pour l'onglet Documents (données fictives, sans fenêtre)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pdf_fictif import ecrire_pdf  # noqa: E402
from reconsigliere import installation  # noqa: E402
from reconsigliere.importation import catalogue, pipeline  # noqa: E402
from test_importation_classement import ANNEXE, BILAN, PNL, PLAN  # noqa: E402
from test_importation_pipeline import AMBIGUE, GL1_EQ, GL2_EQ  # noqa: E402

GL_2023 = ["Grand livre 2023", "1020 Banque", "05.01.2023 BNK/2023/0001 Frais 0.00 10.00"]


class TestCatalogue(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name) / "R"
        installation.creer_dossiers(self.racine)
        docs = self.racine / "entrees" / "07_documents"
        ecrire_pdf(docs / "comptes 2024.pdf", [BILAN, PNL, GL1_EQ, GL2_EQ, ANNEXE, AMBIGUE])
        ecrire_pdf(docs / "plan.pdf", [["Plan comptable exercice 2024"] + PLAN[1:] + ["1000 Caisse bis Actifs circulants"]])
        ecrire_pdf(docs / "gl 2023.pdf", [GL_2023])
        pipeline.importer_dossier(self.racine, cle=None, ocr=lambda c, n: "", log=lambda *_: None)
        self.imports = catalogue.charger(self.racine)

    def tearDown(self):
        self._tmp.cleanup()

    def imp(self, nom):
        return next(i for i in self.imports if i.source == nom)

    def test_charger_et_resume(self):
        self.assertEqual(sorted(i.source for i in self.imports), ["comptes 2024.pdf", "gl 2023.pdf", "plan.pdf"])
        c = self.imp("comptes 2024.pdf")
        self.assertEqual(c.exercice, 2024)
        self.assertEqual(c.nb_pages, 6)
        self.assertEqual(c.resume_sections(), "Bilan p.1 · Compte de résultat p.2 · Grand livre p.3–4 · "
                                              "Annexe p.5 · Autre p.6")
        self.assertEqual(c.etat, "a_verifier")
        self.assertEqual(c.methodes, {"regles": 4, "continuite": 1, "a_verifier": 1})
        self.assertEqual(c.chemin_source, self.racine / "entrees" / "07_documents" / "comptes 2024.pdf")
        self.assertTrue(c.html.exists())
        self.assertEqual(catalogue.exercices(self.imports), [2023, 2024])

    def test_vue_grand_livre_filtree_par_exercice(self):
        v = catalogue.vue(self.imports, "grand_livre", 2024)
        self.assertEqual([s["fichier"] for s in v["sources"]], ["comptes 2024.pdf"])
        self.assertEqual(v["sources"][0]["pages"], "p.3–4")
        self.assertEqual(len(v["lignes"]), 4)
        self.assertEqual(v["controles"][0]["resultat"], "ok")
        tout = catalogue.vue(self.imports, "grand_livre", None)
        self.assertEqual(len(tout["lignes"]), 5)
        self.assertEqual(tout["controles"][0]["resultat"], "ecart")

    def test_vue_plan_comptable_doublons(self):
        v = catalogue.vue(self.imports, "plan_comptable", None)
        self.assertEqual([l["code"] for l in v["lignes"]], ["1000", "1020", "2000", "1000"])
        doublons = next(c for c in v["controles"] if c["controle"] == "Codes en double")
        self.assertEqual((doublons["resultat"], doublons["detail"]), ("ecart", "1000"))

    def test_vue_bilan_et_arbre(self):
        v = catalogue.vue(self.imports, "bilan", 2024)
        self.assertEqual(v["controles"][0]["resultat"], "ok")
        arbre = catalogue.arbre(v["lignes"])
        self.assertEqual([n["libelle"] for n in arbre], ["Actifs", "Passifs"])
        self.assertEqual(arbre[0]["enfants"][0]["libelle"], "Actifs circulants")
        self.assertEqual(arbre[0]["enfants"][0]["enfants"][0]["libelle"], "1020 Banque")

    def test_annexe_et_autres_separes(self):
        self.assertEqual([l["page"] for l in catalogue.vue(self.imports, "annexe", None)["lignes"]], [5])
        autres = catalogue.vue(self.imports, "autre", None)
        self.assertEqual([l["page"] for l in autres["lignes"]], [6])
        self.assertEqual(autres["controles"][0]["resultat"], "ecart")

    def test_classeur_etranger_ignore(self):
        import openpyxl
        wb = openpyxl.Workbook()
        wb.active.title = "PlanComptable"
        wb.save(self.racine / "entrees" / "06_societe" / "imports" / "2024" / "manuel.xlsx")
        self.assertEqual(len(catalogue.charger(self.racine)), 3)


if __name__ == "__main__":
    unittest.main()
