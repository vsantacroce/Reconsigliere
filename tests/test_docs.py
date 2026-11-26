"""Tests de la documentation vivante (outils/docs.py) : python -m unittest discover -s tests"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_chemin = Path(__file__).resolve().parents[1] / "outils" / "docs.py"
_spec = importlib.util.spec_from_file_location("outils_docs", _chemin)
docs = importlib.util.module_from_spec(_spec)
sys.modules["outils_docs"] = docs
_spec.loader.exec_module(docs)

SOURCES = {
    "src/reconsigliere/__init__.py": '__version__ = "0"\n',
    "src/reconsigliere/config.py": '"""Réglages."""\nRACINE = 1\n\ndef definir_racine(r):\n    """Change le dossier."""\n',
    "src/reconsigliere/fenetre.py": (
        '"""Fenêtre."""\nimport tkinter\nfrom . import config\n\n'
        'def _prive():\n    pass\n\n'
        'class Fenetre:\n    """La fenêtre."""\n    def lancer(self):\n'
        '        from .__main__ import main  # import tardif\n'),
    "src/reconsigliere/__main__.py": '"""Lancement."""\nimport pandas as pd\nfrom . import config\n\ndef main():\n    pass\n',
    "src/reconsigliere/importation/__init__.py": "",
    "src/reconsigliere/importation/pipeline.py": (
        '"""Pipeline."""\nfrom .. import config\nfrom ..outils_absent import x\nfrom . import pages\n'),
    "src/reconsigliere/importation/pages.py": '"""Pages."""\nfrom pypdf import PdfReader\n',
}


def page(titre: str) -> str:
    return (f"# {titre}\n\n" + "".join(f"{r}\n\nTexte.\n\n" for r in docs.RUBRIQUES)
            + f"{docs.DEBUT}\n{docs.FIN}\n")


def creer_depot(d: Path) -> Path:
    for rel, texte in SOURCES.items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(texte, encoding="utf-8")
    for nom in ("config", "fenetre", "__main__", "importation/pipeline", "importation/pages"):
        f = d / "docs" / "modules" / f"{nom}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(page(nom), encoding="utf-8")
    return d


class TestModules(unittest.TestCase):
    def test_imports_tardifs_et_relatifs_sont_resolus(self):
        with tempfile.TemporaryDirectory() as d:
            m = docs.modules(creer_depot(Path(d)))
            self.assertEqual(set(m), {"config", "fenetre", "__main__", "importation.pipeline", "importation.pages"})
            self.assertEqual(m["fenetre"].imports, {"config", "__main__"})
            self.assertEqual(m["importation.pipeline"].imports, {"config", "importation.pages"})
            self.assertEqual(m["__main__"].externes, {"pandas"})
            self.assertEqual(m["fenetre"].externes, set())  # tkinter fait partie de Python
            self.assertEqual(m["importation.pipeline"].page, Path(d) / "docs/modules/importation/pipeline.md")

    def test_publics_avec_premiere_ligne_de_docstring(self):
        with tempfile.TemporaryDirectory() as d:
            m = docs.modules(creer_depot(Path(d)))
            self.assertEqual(m["config"].publics, [("definir_racine", "Change le dossier.")])
            self.assertEqual(m["fenetre"].publics, [("Fenetre", "La fenêtre.")])

    def test_bloc_cite_utilise_par(self):
        with tempfile.TemporaryDirectory() as d:
            tous = docs.modules(creer_depot(Path(d)))
            bloc = docs.bloc(tous["config"], tous)
            self.assertIn("fenetre", bloc.split("Utilisé par")[1])
            self.assertIn("importation/pipeline.md", bloc)


class TestVerifier(unittest.TestCase):
    def test_bloc_perime_signale_puis_corrige(self):
        with tempfile.TemporaryDirectory() as d:
            racine = creer_depot(Path(d))
            self.assertTrue(any("pas à jour" in p for p in docs.verifier(racine)))
            docs.regenerer(racine)
            self.assertEqual(docs.verifier(racine), [])
            self.assertIn("```mermaid", (racine / "docs" / "carte.md").read_text(encoding="utf-8"))

    def test_page_manquante_et_rubrique_manquante(self):
        with tempfile.TemporaryDirectory() as d:
            racine = creer_depot(Path(d))
            docs.regenerer(racine)
            (racine / "docs/modules/config.md").unlink()
            f = racine / "docs/modules/fenetre.md"
            f.write_text(f.read_text(encoding="utf-8").replace(docs.RUBRIQUES[3], "## Autre"), encoding="utf-8")
            problemes = docs.verifier(racine)
            self.assertTrue(any("config" in p and "manque" in p for p in problemes))
            self.assertTrue(any("fenetre" in p and docs.RUBRIQUES[3] in p for p in problemes))

    def test_regenerer_cree_une_page_a_completer(self):
        with tempfile.TemporaryDirectory() as d:
            racine = creer_depot(Path(d))
            (racine / "docs/modules/config.md").unlink()
            docs.regenerer(racine)
            texte = (racine / "docs/modules/config.md").read_text(encoding="utf-8")
            self.assertIn(docs.A_COMPLETER, texte)
            self.assertEqual(texte.count("## Dépendances (automatique)"), 1)
            self.assertTrue(any("à compléter" in p for p in docs.verifier(racine)))

    def test_fins_de_ligne_windows_tolerees(self):
        with tempfile.TemporaryDirectory() as d:
            racine = creer_depot(Path(d))
            docs.regenerer(racine)
            f = racine / "docs/modules/config.md"
            f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
            self.assertEqual(docs.verifier(racine), [])


def git(d: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=d, check=True, capture_output=True, text=True).stdout


class TestPagesOubliees(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = creer_depot(Path(self._tmp.name))
        git(self.d, "init", "-q")
        git(self.d, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
        git(self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")

    def tearDown(self):
        self._tmp.cleanup()

    def commit(self):
        git(self.d, "add", "-A")
        git(self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")

    def test_source_modifiee_sans_sa_page(self):
        (self.d / "src/reconsigliere/config.py").write_text("RACINE = 2\n", encoding="utf-8")
        self.commit()
        self.assertEqual(docs.pages_oubliees(self.d, "HEAD~1"),
                         ["src/reconsigliere/config.py → docs/modules/config.md"])

    def test_source_modifiee_avec_sa_page(self):
        (self.d / "src/reconsigliere/config.py").write_text("RACINE = 2\n", encoding="utf-8")
        f = self.d / "docs/modules/config.md"
        f.write_text(f.read_text(encoding="utf-8") + "\nMis à jour.\n", encoding="utf-8")
        self.commit()
        self.assertEqual(docs.pages_oubliees(self.d, "HEAD~1"), [])

    def test_source_supprimee_non_exigee(self):
        (self.d / "src/reconsigliere/importation/pages.py").unlink()
        self.commit()
        self.assertEqual(docs.pages_oubliees(self.d, "HEAD~1"), [])

    def test_fichier_associe_exige_sa_page(self):
        f = self.d / "src/reconsigliere/modele_societe.html"
        f.write_text("<html></html>", encoding="utf-8")
        self.commit()
        self.assertEqual(docs.pages_oubliees(self.d, "HEAD~1"),
                         ["src/reconsigliere/modele_societe.html → docs/modules/societe.md"])

    def test_reference_inconnue(self):
        self.assertEqual(docs.main(["--racine", str(self.d), "--depuis", "nexistepas"]), 2)


if __name__ == "__main__":
    unittest.main()
