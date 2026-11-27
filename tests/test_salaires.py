"""Tests de la réconciliation des salaires : python -m unittest discover -s tests

Toutes les données sont fictives.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import config, installation  # noqa: E402


class AvecDossier(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self.tmp.name)
        self.ancienne = config.RACINE
        config.definir_racine(self.racine)

    def tearDown(self):
        config.definir_racine(self.ancienne)
        self.tmp.cleanup()


class TestDossiers(AvecDossier):
    def test_dossiers_crees(self):
        installation.creer_dossiers(self.racine)
        self.assertTrue((self.racine / "entrees" / "08_salaires" / "fiches").is_dir())
        self.assertEqual(config.DOSSIER_SALAIRES, self.racine.resolve() / "entrees" / "08_salaires")
        self.assertEqual(config.DOSSIER_FICHES_SALAIRES, config.DOSSIER_SALAIRES / "fiches")
        self.assertEqual(config.DOSSIER_SORTIES_SALAIRES, self.racine.resolve() / "sorties" / "salaires")


if __name__ == "__main__":
    unittest.main()
