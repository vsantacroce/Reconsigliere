"""Pipeline complet sur un PDF fictif qui contient plusieurs états."""

import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pdf_fictif import ecrire_pdf  # noqa: E402
from reconsigliere import installation  # noqa: E402
from reconsigliere.importation import pipeline  # noqa: E402
from test_importation_classement import ANNEXE, BILAN, GL1, GL2, PNL  # noqa: E402

GL1_EQ = GL1[:4] + ["6000 Loyers", "05.01.2024 BILL/2024/01/0001 Fournisseur SA Loyer 1'200.00 0.00 1'200.00", "Page 1/2"]
GL2_EQ = ["Report 1'200.00", "1100 Clients", "07.01.2024 INV/2024/0001 Client SA Vente 2'000.00 0.00 2'000.00",
          "3200 Ventes", "07.01.2024 INV/2024/0001 Client SA Vente 0.00 2'000.00 -2'000.00", "Page 2/2"]
AMBIGUE = ["Madame, Monsieur, nous vous remercions de votre confiance.",
           "Veuillez trouver ci-joint les documents demandés pour votre dossier."]


def lire(xlsx):
    wb = openpyxl.load_workbook(xlsx)
    return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name) / "R"
        installation.creer_dossiers(self.racine)
        self.pdf = ecrire_pdf(self.racine / "entrees" / "07_documents" / "comptes 2024.pdf",
                              [BILAN, PNL, GL1_EQ, GL2_EQ, ANNEXE, AMBIGUE])

    def tearDown(self):
        self._tmp.cleanup()

    def importer(self, **options):
        options.setdefault("cle", None)
        return pipeline.importer(self.pdf, self.racine, ocr=lambda c, n: "", log=lambda *_: None, **options)

    def test_classeur_normalise(self):
        res = self.importer()
        self.assertEqual(res["exercice"], 2024)
        xlsx = Path(res["excel"])
        self.assertEqual(xlsx.parent, self.racine / "entrees" / "06_societe" / "imports" / "2024")
        self.assertTrue(Path(res["html"]).exists())
        self.assertEqual(Path(res["html"]).parent, self.racine / "sorties" / "imports")
        f = lire(xlsx)
        self.assertEqual(set(f), {"meta", "pages", "controles", "plancomptable", "grandlivre", "bilan",
                                  "compteresultat", "annexe"})
        self.assertEqual(f["grandlivre"][0], ["date", "compte", "libelle_compte", "piece", "partenaire", "libelle",
                                              "debit", "credit", "exercice", "source"])
        gl = f["grandlivre"][1:]
        self.assertEqual(len(gl), 4)
        self.assertTrue(all(isinstance(r[1], str) for r in gl))
        self.assertTrue(all((r[6] is None or r[6] > 0) and (r[7] is None or r[7] > 0) for r in gl))
        self.assertTrue(all(r[8] == 2024 for r in gl))
        self.assertIn("p.4", gl[-1][9])
        meta = dict((k, v) for k, v in f["meta"][1:])
        self.assertEqual(meta["date_debut"], "2024-01-01")
        self.assertEqual(meta["devise"], "CHF")
        self.assertEqual(meta["fichier_source"], "comptes 2024.pdf")
        self.assertEqual(meta["societe"], "Societe Fictive SA")
        pages = f["pages"][1:]
        self.assertEqual([p[1] for p in pages], ["bilan", "compte_resultat", "grand_livre", "grand_livre",
                                                 "annexe", "autre"])
        self.assertEqual(pages[3][2], "continuite")
        self.assertEqual(pages[5][2], "a_verifier")
        controles = {c[0]: c[1] for c in f["controles"][1:]}
        self.assertEqual(controles["Grand livre équilibré"], "ok")
        self.assertEqual(controles["Bilan : actifs = passifs"], "ok")
        self.assertEqual(res["appels_ia"], 0)

    def test_ia_seulement_sur_la_page_ambigue(self):
        appels = []

        def envoyer(req):
            appels.append(req)
            return {"texte": "autre", "entree": 90, "sortie": 2, "stop": "end_turn"}
        res = self.importer(cle="sk-test", envoyer=envoyer)
        self.assertEqual(len(appels), 1)
        self.assertIn("Madame", appels[0]["messages"][0]["content"])
        self.assertEqual(res["appels_ia"], 1)
        self.assertEqual(res["tokens"], {"entree": 90, "sortie": 2})
        pages = lire(res["excel"])["pages"][1:]
        self.assertEqual(pages[5][2], "ia")

    def test_choix_manuel_sans_cle(self):
        vus = []
        res = self.importer(choisir=lambda page, proposition: vus.append(page.numero) or "annexe")
        self.assertEqual(vus, [6])
        pages = lire(res["excel"])["pages"][1:]
        self.assertEqual((pages[5][1], pages[5][2]), ("annexe", "manuel"))

    def test_dossier_deja_importe_saute(self):
        premiers = pipeline.importer_dossier(self.racine, cle=None, ocr=lambda c, n: "", log=lambda *_: None)
        seconds = pipeline.importer_dossier(self.racine, cle=None, ocr=lambda c, n: "", log=lambda *_: None)
        self.assertEqual(len(premiers), 1)
        self.assertEqual(seconds, [])


if __name__ == "__main__":
    unittest.main()
