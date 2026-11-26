"""Tests du lanceur qui se met à jour (windows/demarrer.pyw), sans réseau."""

import importlib.machinery
import importlib.util
import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]


def charger_lanceur(base: Path):
    os.environ["RECONSIGLIERE_BASE"] = str(base)
    chargeur = importlib.machinery.SourceFileLoader("demarrer", str(RACINE / "windows" / "demarrer.pyw"))
    spec = importlib.util.spec_from_loader("demarrer", chargeur)
    module = importlib.util.module_from_spec(spec)
    chargeur.exec_module(module)
    return module


def archive(sha: str, version: str) -> bytes:
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as z:
        z.writestr(f"reconsigliere-{sha}/src/reconsigliere/__init__.py", f'__version__ = "{version}"\n')
        z.writestr(f"reconsigliere-{sha}/requirements.txt", "pandas\n")
    return tampon.getvalue()


class TestMiseAJour(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.base = Path(self.dossier.name)
        self.lanceur = charger_lanceur(self.base)
        self.lanceur.installer_bibliotheques = lambda requirements: None

    def tearDown(self):
        os.environ.pop("RECONSIGLIERE_BASE", None)
        self.dossier.cleanup()

    def test_remplace_le_programme_et_note_la_version(self):
        (self.base / "app" / "ancien").mkdir(parents=True)
        self.lanceur.requete = lambda url, accept=None: archive("abc123", "9.9.9")
        self.lanceur.mettre_a_jour("abc123", lambda texte: None)
        self.assertIn("9.9.9", (self.base / "app" / "src" / "reconsigliere" / "__init__.py").read_text())
        self.assertFalse((self.base / "app" / "ancien").exists())
        self.assertEqual((self.base / "version.txt").read_text(), "abc123")

    def test_hors_ligne_garde_la_version_installee(self):
        def panne(branche):
            raise OSError("pas de réseau")
        self.lanceur.dernier_commit = panne
        (self.base / "app").mkdir()
        (self.base / "version.txt").write_text("ancien")
        self.lanceur.verifier_mise_a_jour()
        self.assertEqual((self.base / "version.txt").read_text(), "ancien")
        self.assertIn("mise à jour impossible", (self.base / "journal.txt").read_text(encoding="utf-8"))

    def test_archive_inattendue_ne_casse_rien(self):
        (self.base / "app").mkdir()
        (self.base / "app" / "garde").write_text("x")
        self.lanceur.requete = lambda url, accept=None: b"PK\x05\x06" + b"\0" * 18  # zip vide
        with self.assertRaises(Exception):
            self.lanceur.mettre_a_jour("zzz", lambda texte: None)
        self.assertTrue((self.base / "app" / "garde").exists())


if __name__ == "__main__":
    unittest.main()
