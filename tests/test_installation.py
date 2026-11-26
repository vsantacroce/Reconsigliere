"""Tests du dossier de travail choisi dans la fenêtre : python -m unittest discover -s tests"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import config, installation  # noqa: E402


class TestInstallation(unittest.TestCase):
    def test_resoudre_cree_un_sous_dossier(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(installation.resoudre(Path(d)), Path(d).resolve() / "Reconsigliere")

    def test_resoudre_garde_un_dossier_existant(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "entrees").mkdir()
            self.assertEqual(installation.resoudre(Path(d)), Path(d).resolve())

    def test_creer_dossiers_sans_ecraser(self):
        with tempfile.TemporaryDirectory() as d:
            racine = Path(d) / "R"
            installation.creer_dossiers(racine)
            self.assertTrue(installation.est_installe(racine))
            lisezmoi = racine / "entrees" / "01_factures" / "LISEZMOI.md"
            lisezmoi.write_text("perso", encoding="utf-8")
            self.assertEqual(installation.creer_dossiers(racine), [])
            self.assertEqual(lisezmoi.read_text(encoding="utf-8"), "perso")

    def test_definir_racine(self):
        ancienne = config.RACINE
        try:
            with tempfile.TemporaryDirectory() as d:
                config.definir_racine(d)
                self.assertEqual(config.FICHIER_CORRECTIONS,
                                 Path(d).resolve() / "entrees" / "05_mes_corrections" / "mes_corrections.xlsx")
        finally:
            config.definir_racine(ancienne)


if __name__ == "__main__":
    unittest.main()
