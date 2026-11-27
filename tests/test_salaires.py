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
import shutil  # noqa: E402
import subprocess  # noqa: E402

from reconsigliere import salaires  # noqa: E402
from reconsigliere.salaires import fiche, lecture_paie, reconciliation  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paie_fictive  # noqa: E402


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


class TestLecture(AvecDossier):
    def setUp(self):
        super().setUp()
        self.chemin = paie_fictive.creer_classeur_paie(config.DOSSIER_SALAIRES / "HR_paie_2025.xlsx")
        self.lu = lecture_paie.lire(self.chemin)

    def virement(self, employe, montant, jour=None):
        trouves = [v for v in self.lu["virements"] if v["employe"] == employe and abs(v["montant"] - montant) < 0.005
                   and (jour is None or v["date"].day == jour)]
        self.assertEqual(len(trouves), 1, f"{employe} {montant}")
        return trouves[0]

    def test_exercice(self):
        self.assertEqual(self.lu["annee"], 2025)
        self.assertEqual(lecture_paie.exercice_du_classeur(self.chemin), 2025)
        self.assertEqual(lecture_paie.trouver_classeur(2025), self.chemin)
        self.assertIsNone(lecture_paie.trouver_classeur(2026))

    def test_du(self):
        self.assertEqual([d["employe"] for d in self.lu["du"]], paie_fictive.EMPLOYES)
        self.assertEqual(self.lu["du"][0]["net_du"], 38200.00)
        self.assertEqual(self.lu["du"][0]["source"], "ANNEE, AX8")

    def test_virements_et_ids(self):
        self.assertEqual(len(self.lu["virements"]), len(paie_fictive.VIREMENTS))
        self.assertTrue(all(v["id"] for v in self.lu["virements"]))
        self.assertTrue(all(isinstance(v["date"], datetime) for v in self.lu["virements"]))

    def test_pret(self):
        v = self.virement("Durand Alice", 5000.00, jour=26)
        self.assertEqual(v["part_salaire"], 0.0)
        self.assertTrue(v["imputation"].startswith("Prêt"))

    def test_remboursement(self):
        v = self.virement("Durand Alice", 110.80)
        self.assertEqual(v["part_salaire"], 0.0)
        self.assertEqual(v["exercice"], 2025)

    def test_frais_exact_meme_si_regularisation(self):
        v = self.virement("Durand Alice", 1838.01)
        self.assertEqual(v["part_salaire"], 0.0)
        self.assertEqual(v["exercice"], 2025)
        self.assertIn("Frais", v["imputation"])

    def test_regularisation(self):
        v = self.virement("Durand Alice", 5000.00, jour=24)
        self.assertEqual(v["exercice"], 2024)
        self.assertEqual(v["part_salaire"], 5000.00)

    def test_decoupage_salaire_frais(self):
        v = self.virement("Durand Alice", 9881.60)
        self.assertEqual((v["exercice"], v["part_salaire"]), (2025, 9449.85))
        self.assertIn("431.75", v["imputation"])
        v = self.virement("Meier Bruno", 5424.45)
        self.assertEqual((v["exercice"], v["part_salaire"]), (2025, 4885.50))

    def test_decoupage_hors_periode_et_frais(self):
        v = self.virement("Rossi Carla", 391.49)
        self.assertEqual((v["exercice"], v["part_salaire"]), (2024, 286.17))
        self.assertIn("105.32", v["imputation"])

    def test_salaire_simple(self):
        v = self.virement("Rossi Carla", 9654.80, jour=27)
        self.assertEqual((v["exercice"], v["part_salaire"], v["imputation"]), (2025, 9654.80, ""))

    def test_controle_verse_paye(self):
        for nom in paie_fictive.EMPLOYES:
            total = sum(v["part_salaire"] for v in self.lu["virements"] if v["employe"] == nom and v["exercice"] == 2025)
            self.assertAlmostEqual(total, paie_fictive.verse_paye(nom), places=2)
        self.assertEqual(self.lu["controles"], [])
        autre = paie_fictive.creer_classeur_paie(self.racine / "autre.xlsx", verse={"Meier Bruno": 9000.00})
        lu = lecture_paie.lire(autre)
        self.assertEqual(len(lu["controles"]), 1)
        self.assertEqual(lu["controles"][0]["employe"], "Meier Bruno")
        self.assertIn("771.00", lu["controles"][0]["point"])

    def test_format_inconnu(self):
        wb = openpyxl.Workbook()
        wb.active.title = "Feuil1"
        chemin = self.racine / "ancien.xlsx"
        wb.save(chemin)
        with self.assertRaises(lecture_paie.FormatInconnu) as e:
            lecture_paie.lire(chemin)
        self.assertIn("onglet ANNEE introuvable", str(e.exception))
        self.assertIsNone(lecture_paie.exercice_du_classeur(chemin))


def fiche_n(annee, du, virements, points=None):
    f = {"du": [{"employe": e, "net_du": m, "source": "test", "remarque": ""} for e, m in du],
         "virements": [], "points": points or []}
    for i, (employe, montant, exercice, part, typ) in enumerate(virements, 1):
        f["virements"].append({"id": f"{annee}-{i}", "employe": employe, "date": datetime(annee, 1 + i % 12, 5),
                               "banque": "B", "montant": montant, "exercice": exercice, "part_salaire": part,
                               "type": typ, "libelle": "", "piece": f"P{i}", "imputation": "", "controle": "",
                               "preuve": ""})
    f["auto"] = fiche.valeurs_auto(f)
    return f


class TestReconciliation(AvecDossier):
    def setUp(self):
        super().setUp()
        self.f24 = fiche_n(2024, [("Durand Alice", 500.0), ("Ancien Paul", 300.0)],
                           [("Durand Alice", 450.0, 2024, 450.0, "Salaire"), ("Ancien Paul", 200.0, 2024, 200.0, "Salaire")])
        self.f25 = fiche_n(2025, [("Durand Alice", 1000.0)],
                           [("Durand Alice", 800.0, 2025, 800.0, "Salaire"),
                            ("Durand Alice", 50.0, 2024, 50.0, "Régularisation 2024"),
                            ("Durand Alice", 5000.0, 2025, 0.0, "Prêt / avance")])
        self.f26 = fiche_n(2026, [("Durand Alice", 1200.0)],
                           [("Durand Alice", 150.0, 2025, 150.0, "Régularisation 2025"),
                            ("Durand Alice", 900.0, 2026, 900.0, "Salaire")])

    def test_resume_valeurs(self):
        r = reconciliation.resume(2025, self.f25, self.f24, self.f26)
        l = r["lignes"][0]
        self.assertEqual((l["employe"], l["du"], l["paye"], l["reporte"], l["paye_suivant"], l["ecart"]),
                         ("Durand Alice", 1000.0, 800.0, 200.0, 150.0, 50.0))
        self.assertEqual(r["total"]["ecart"], 50.0)
        restes = {x["employe"]: x for x in r["restes_prec"]}
        self.assertEqual((restes["Durand Alice"]["reporte"], restes["Durand Alice"]["paye"],
                          restes["Durand Alice"]["ecart"]), (50.0, 50.0, 0.0))

    def test_employe_seulement_en_precedent(self):
        r = reconciliation.resume(2025, self.f25, self.f24, self.f26)
        restes = {x["employe"]: x for x in r["restes_prec"]}
        self.assertEqual((restes["Ancien Paul"]["reporte"], restes["Ancien Paul"]["ecart"]), (100.0, 100.0))
        chemin = reconciliation.ecrire(2025, self.f25, self.f24, self.f26)
        valeurs = [c.value for c in openpyxl.load_workbook(chemin)["Synthèse"]["A"]]
        self.assertIn("Ancien Paul", valeurs)

    def test_synthese_formules(self):
        chemin = reconciliation.ecrire(2025, self.f25, self.f24, self.f26)
        self.assertEqual(chemin, config.DOSSIER_SORTIES_SALAIRES / "Reconciliation_salaires_2025.xlsx")
        wb = openpyxl.load_workbook(chemin)
        self.assertEqual(wb.sheetnames, ["Synthèse", "Dû 2025", "Reste 2024", "Payé en 2025", "Payé en 2026",
                                         "Points à vérifier"])
        ws = wb["Synthèse"]
        self.assertEqual(ws["A5"].value, "Durand Alice")
        for c in "BCDEF":
            self.assertTrue(str(ws[f"{c}5"].value).startswith("="), c)
        points = " ".join(str(c.value) for c in wb["Points à vérifier"]["B"] if c.value)
        self.assertIn("Prêt", points)

    def test_sans_precedent(self):
        chemin = reconciliation.ecrire(2025, self.f25, None, self.f26)
        wb = openpyxl.load_workbook(chemin)
        self.assertNotIn("Reste 2024", wb.sheetnames)
        self.assertNotIn("Restes 2024 payés en 2025", [c.value for c in wb["Synthèse"]["A"]])
        self.assertIsNone(reconciliation.resume(2025, self.f25, None, None)["restes_prec"])

    def test_sans_suivant(self):
        chemin = reconciliation.ecrire(2025, self.f25, self.f24, None)
        wb = openpyxl.load_workbook(chemin)
        ws = wb["Payé en 2026"]
        self.assertIsNone(ws["A5"].value)
        points = " ".join(str(c.value) for c in wb["Points à vérifier"]["B"] if c.value)
        self.assertIn("Aucune fiche 2026", points)

    def test_points_de_la_fiche_repris(self):
        self.f25["points"] = [{"employe": "Durand Alice", "point": "Point écrit à la main"}]
        wb = openpyxl.load_workbook(reconciliation.ecrire(2025, self.f25, None, None))
        self.assertIn("Point écrit à la main", [c.value for c in wb["Points à vérifier"]["B"]])

    @unittest.skipUnless(shutil.which("soffice"), "LibreOffice absent")
    def test_recalcul_libreoffice(self):
        chemin = reconciliation.ecrire(2025, self.f25, self.f24, self.f26)
        sortie = self.racine / "calc"
        subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", str(sortie), str(chemin)],
                       check=True, capture_output=True, timeout=120)
        ws = openpyxl.load_workbook(sortie / chemin.name, data_only=True)["Synthèse"]
        self.assertEqual([ws[f"{c}5"].value for c in "BCDEF"], [1000, 800, 200, 150, 50])
        r = reconciliation.resume(2025, self.f25, self.f24, self.f26)
        ligne_total = next(i for i in range(5, 15) if ws[f"A{i}"].value == "Total")
        self.assertEqual(ws[f"F{ligne_total}"].value, r["total"]["ecart"])

    def test_generer_bout_en_bout(self):
        paie_fictive.creer_classeur_paie(config.DOSSIER_SALAIRES / "paie.xlsx")
        bilan = salaires.lire_classeur(2025)
        self.assertEqual(bilan["ajoutes"], len(paie_fictive.VIREMENTS))
        self.assertTrue(fiche.chemin_fiche(2025).exists())
        chemin, r = salaires.generer(2025)
        self.assertTrue(chemin.exists())
        self.assertEqual(r["lignes"][0]["paye"], paie_fictive.verse_paye("Durand Alice"))
        self.assertEqual(salaires.exercices_disponibles(), [2025])

    def test_lire_classeur_absent(self):
        with self.assertRaises(salaires.ClasseurAbsent):
            salaires.lire_classeur(2025)
        with self.assertRaises(salaires.ClasseurAbsent):
            salaires.generer(2025)


if __name__ == "__main__":
    unittest.main()
