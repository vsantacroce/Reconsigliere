"""Tests de la réconciliation des salaires : python -m unittest discover -s tests

Toutes les données sont fictives.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datetime import datetime  # noqa: E402
from unittest import mock  # noqa: E402

import openpyxl  # noqa: E402

from reconsigliere import config, installation  # noqa: E402
from reconsigliere.salaires import fiche  # noqa: E402


def vir(employe, jour, montant, exercice=2025, part=None, **autres):
    v = {"id": "", "employe": employe, "date": datetime(2025, 1, jour), "banque": "BANQUE-CHF",
         "montant": montant, "exercice": exercice, "part_salaire": montant if part is None else part,
         "type": "Salaire", "libelle": "Debit salary", "piece": f"BNK/2025/{jour:05d}", "imputation": "",
         "controle": "", "preuve": ""}
    v.update(autres)
    return v


def fiche_lue(virements, du=None, points=None):
    """Fiche telle que rendue par le lecteur : ids remplis, auto = valeurs proposées."""
    f = {"du": du or [{"employe": "Durand Alice", "net_du": 1000.0, "source": "ANNEE, AX8", "remarque": ""}],
         "virements": [dict(v) for v in virements], "points": points or []}
    fiche.identifiants(f["virements"])
    f["auto"] = fiche.valeurs_auto(f)
    return f


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


class TestFiche(AvecDossier):
    def test_aller_retour(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0), vir("Durand Alice", 6, 50.0, exercice=2024)],
                      points=[{"employe": "Durand Alice", "point": "Vérifier janvier"}])
        fiche.ecrire(2025, f)
        lu = fiche.lire(2025)
        self.assertEqual(lu["du"], f["du"])
        self.assertEqual(lu["virements"], f["virements"])
        self.assertEqual(lu["points"], f["points"])
        self.assertEqual(lu["auto"], f["auto"])
        self.assertIsInstance(lu["virements"][0]["date"], datetime)
        wb = openpyxl.load_workbook(fiche.chemin_fiche(2025))
        self.assertEqual(wb["auto"].sheet_state, "hidden")

    def test_lire_absente(self):
        self.assertIsNone(fiche.lire(2030))

    def test_ids_virements_identiques(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0), vir("Durand Alice", 5, 800.0)])
        ids = [v["id"] for v in f["virements"]]
        self.assertEqual(ids, ["20250105-DurandAlice-800.00-1", "20250105-DurandAlice-800.00-2"])

    def test_relecture_sans_correction(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0)])
        nouvelle = fiche_lue([vir("Durand Alice", 5, 800.0)])
        resultat, bilan = fiche.fusionner(f, nouvelle)
        self.assertEqual(resultat["virements"], nouvelle["virements"])
        self.assertEqual(bilan, {"ajoutes": 0, "retires": 0, "gardees": 0, "manuels": 0})

    def test_premiere_lecture(self):
        nouvelle = fiche_lue([vir("Durand Alice", 5, 800.0)])
        resultat, bilan = fiche.fusionner(None, nouvelle)
        self.assertEqual(resultat["virements"], nouvelle["virements"])
        self.assertEqual(bilan["ajoutes"], 1)

    def test_correction_gardee(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0), vir("Durand Alice", 6, 30.0)])
        f["virements"][0]["part_salaire"] = 700.0
        f["virements"][0]["imputation"] = "100 de frais"
        nouvelle = fiche_lue([vir("Durand Alice", 5, 800.0, libelle="nouveau"), vir("Durand Alice", 6, 30.0, part=0.0)])
        resultat, bilan = fiche.fusionner(f, nouvelle)
        v0, v1 = resultat["virements"]
        self.assertEqual(v0["part_salaire"], 700.0)
        self.assertEqual(v0["imputation"], "100 de frais")
        self.assertEqual(v0["libelle"], "nouveau")
        self.assertEqual(v1["part_salaire"], 0.0)  # pas corrigé : la nouvelle valeur du lecteur s'applique
        self.assertEqual(resultat["auto"][v0["id"]]["part_salaire"], 800.0)
        self.assertEqual(bilan["gardees"], 2)  # part_salaire et imputation du premier virement

    def test_preuve_gardee(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0)])
        f["virements"][0]["preuve"] = "fiche_paie_janvier.pdf"
        resultat, _ = fiche.fusionner(f, fiche_lue([vir("Durand Alice", 5, 800.0)]))
        self.assertEqual(resultat["virements"][0]["preuve"], "fiche_paie_janvier.pdf")

    def test_net_du_corrige_garde(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0)])
        f["du"][0]["net_du"] = 990.0
        resultat, bilan = fiche.fusionner(f, fiche_lue([vir("Durand Alice", 5, 800.0)]))
        self.assertEqual(resultat["du"][0]["net_du"], 990.0)
        self.assertEqual(bilan["gardees"], 1)

    def test_ligne_manuelle_gardee(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0)])
        f["virements"].append(vir("Durand Alice", 20, 120.0, imputation="ajouté à la main"))
        resultat, bilan = fiche.fusionner(f, fiche_lue([vir("Durand Alice", 5, 800.0)]))
        self.assertEqual(len(resultat["virements"]), 2)
        self.assertEqual(resultat["virements"][1]["imputation"], "ajouté à la main")
        self.assertEqual(bilan["manuels"], 1)

    def test_virement_disparu_retire(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0), vir("Durand Alice", 6, 30.0)])
        resultat, bilan = fiche.fusionner(f, fiche_lue([vir("Durand Alice", 5, 800.0)]))
        self.assertEqual(len(resultat["virements"]), 1)
        self.assertEqual(bilan["retires"], 1)

    def test_points_gardes(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0)], points=[{"employe": "", "point": "à moi"}])
        resultat, _ = fiche.fusionner(f, fiche_lue([vir("Durand Alice", 5, 800.0)]))
        self.assertEqual(resultat["points"], [{"employe": "", "point": "à moi"}])

    def test_fichier_ouvert(self):
        f = fiche_lue([vir("Durand Alice", 5, 800.0)])
        with mock.patch("openpyxl.Workbook.save", side_effect=PermissionError("verrou")):
            with self.assertRaises(fiche.FichierOuvert) as e:
                fiche.ecrire(2025, f)
        self.assertIn("fiche_salaires_2025.xlsx", str(e.exception))


if __name__ == "__main__":
    unittest.main()
