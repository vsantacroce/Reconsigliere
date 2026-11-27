"""Tests de l'apprentissage depuis les corrections : python -m unittest discover -s tests

Toutes les données sont fictives.
"""

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import openpyxl
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import apprentissage, config, corrections  # noqa: E402
from reconsigliere.outils import code_compte  # noqa: E402


def tr(tid, jour, montant, libelle, partenaire, reference=""):
    return {"id": tid, "date": jour, "montant": montant, "libelle": libelle,
            "partenaire_trouve": partenaire, "compte_reference": reference,
            "compte_propose": f"{reference} Ancien" if reference else "", "fiabilite_compte": ""}


def jeu(comptes, partenaire="Migros", libelles=None, montants=None, debut=date(2025, 1, 10), reference="6500"):
    """Transactions corrigées : une par compte donné, une par semaine."""
    transactions, corr = [], {}
    for i, compte in enumerate(comptes):
        libelle = libelles[i] if libelles else f"ACHAT {partenaire.upper()} {i}"
        montant = montants[i] if montants else -50.0
        t = tr(f"T{i}", debut + timedelta(days=7 * i), montant, libelle, partenaire, reference)
        transactions.append(t)
        corr[t["id"]] = {"compte": compte}
    return transactions, {"transactions": corr, "annulees": set()}


def analyser(transactions, corr, referentiel=None):
    return apprentissage.analyser(apprentissage.observations(transactions, corr), corr["annulees"], referentiel)


class TestCodeCompte(unittest.TestCase):
    def test_formes(self):
        self.assertEqual(code_compte(6600.0), "6600")
        self.assertEqual(code_compte(" 6600 "), "6600")
        self.assertEqual(code_compte(None), "")
        self.assertEqual(code_compte(float("nan")), "")


class TestCorrections(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ancienne = config.RACINE
        config.definir_racine(self.tmp.name)

    def tearDown(self):
        config.definir_racine(self.ancienne)
        self.tmp.cleanup()

    def test_ancien_fichier_sans_compte_ni_regles(self):
        config.FICHIER_CORRECTIONS.parent.mkdir(parents=True)
        with pd.ExcelWriter(config.FICHIER_CORRECTIONS, engine="openpyxl") as w:
            pd.DataFrame([{"mot_dans_libelle": "", "partenaire": ""}]).to_excel(w, sheet_name="partenaires", index=False)
            pd.DataFrame([{"id_transaction": "T1", "partenaire": "Migros"}]).to_excel(
                w, sheet_name="transactions", index=False)
        c = corrections.charger()
        self.assertEqual(c["transactions"]["T1"]["compte"], "")
        self.assertEqual(c["annulees"], set())

    def test_modele_a_colonne_compte_et_feuille_regles(self):
        corrections.creer_modele_si_absent()
        wb = openpyxl.load_workbook(config.FICHIER_CORRECTIONS)
        self.assertIn("compte", [c.value for c in wb["transactions"][1]])
        self.assertIn("regles_apprises", wb.sheetnames)

    def test_compte_saisi_comme_nombre(self):
        corrections.creer_modele_si_absent()
        wb = openpyxl.load_workbook(config.FICHIER_CORRECTIONS)
        ws = wb["transactions"]
        entete = [c.value for c in ws[1]]
        ligne = [None] * len(entete)
        ligne[entete.index("id_transaction")] = "T1"
        ligne[entete.index("compte")] = 6600
        ws.append(ligne)
        wb.save(config.FICHIER_CORRECTIONS)
        self.assertEqual(corrections.charger()["transactions"]["T1"]["compte"], "6600")

    def test_annuler_puis_retablir(self):
        corrections.creer_modele_si_absent()
        corrections.annuler_regle("Migros", "6600")
        self.assertEqual(corrections.charger()["annulees"], {("migros", "6600")})
        corrections.retablir_regle("MIGROS", "6600")
        self.assertEqual(corrections.charger()["annulees"], set())

    def test_annuler_ajoute_la_feuille_a_un_ancien_fichier(self):
        config.FICHIER_CORRECTIONS.parent.mkdir(parents=True)
        with pd.ExcelWriter(config.FICHIER_CORRECTIONS, engine="openpyxl") as w:
            pd.DataFrame([{"id_transaction": "T1"}]).to_excel(w, sheet_name="transactions", index=False)
        corrections.annuler_regle("Migros", "6600")
        self.assertEqual(corrections.charger()["annulees"], {("migros", "6600")})
        self.assertEqual(corrections.charger()["transactions"]["T1"]["compte"], "")


class TestRegles(unittest.TestCase):
    def test_trois_corrections_identiques_donnent_une_regle_active(self):
        a = analyser(*jeu(["6600"] * 3))
        r = a.regles[0]
        self.assertEqual(r.etat, apprentissage.ACTIVE)
        self.assertEqual(r.compte, "6600")
        self.assertEqual(r.fiabilite, "3 corrections sur 3")

    def test_deux_corrections_restent_en_observation(self):
        a = analyser(*jeu(["6600"] * 2))
        self.assertEqual(a.regles[0].etat, apprentissage.EN_OBSERVATION)

    def test_une_correction_contraire_ne_casse_pas_la_regle(self):
        a = analyser(*jeu(["6600", "6600", "6000", "6600", "6600"]))
        r = a.regles[0]
        self.assertEqual(r.etat, apprentissage.ACTIVE)
        self.assertEqual(r.fiabilite, "4 corrections sur 5")
        self.assertTrue(any("contraire" in x.message for x in a.alertes))

    def test_changement_de_compte_a_une_date(self):
        a = analyser(*jeu(["6500"] * 3 + ["6600"] * 3))
        r = a.regles[0]
        self.assertEqual(r.etat, apprentissage.ACTIVE)
        self.assertEqual(r.compte, "6600")
        self.assertIn("depuis le", r.condition)
        self.assertTrue(any("se trompait" in x.message for x in a.alertes))
        vieux = tr("X", date(2024, 12, 1), -50, "ACHAT MIGROS", "Migros")
        neuf = tr("Y", date(2026, 1, 1), -50, "ACHAT MIGROS", "Migros")
        self.assertIsNone(r.compte_pour(vieux))
        self.assertEqual(r.compte_pour(neuf), "6600")

    def test_mot_du_libelle_separe_deux_comptes(self):
        comptes = ["6000", "6200", "6000", "6200", "6000", "6200"]
        libelles = ["MIGROS MARCHE", "MIGROS CARBURANT", "MIGROS MARCHE", "MIGROS CARBURANT",
                    "MIGROS MARCHE", "MIGROS CARBURANT"]
        a = analyser(*jeu(comptes, libelles=libelles))
        r = a.regles[0]
        self.assertEqual(r.etat, apprentissage.CONDITIONNELLE)
        self.assertEqual(r.compte_pour(tr("Z", date(2026, 1, 1), -9, "MIGROS CARBURANT 12", "Migros")), "6200")
        self.assertEqual(r.compte_pour(tr("Z", date(2026, 1, 1), -9, "MIGROS MARCHE 12", "Migros")), "6000")
        self.assertIn("carburant", r.condition)
        self.assertFalse(any("se trompait" in x.message for x in a.alertes))

    def test_regle_active_puis_deuxieme_compte_l_analyse_se_trompait(self):
        comptes = ["6000", "6000", "6000", "6200", "6000", "6200"]
        libelles = ["MIGROS MARCHE"] * 3 + ["MIGROS CARBURANT", "MIGROS MARCHE", "MIGROS CARBURANT"]
        a = analyser(*jeu(comptes, libelles=libelles))
        self.assertEqual(a.regles[0].etat, apprentissage.CONDITIONNELLE)
        self.assertTrue(any("se trompait" in x.message for x in a.alertes))

    def test_montant_separe_deux_comptes(self):
        comptes = ["6000", "1500", "6000", "1500", "6000"]
        montants = [-20.0, -900.0, -35.0, -1200.0, -15.0]
        a = analyser(*jeu(comptes, montants=montants))
        r = a.regles[0]
        self.assertEqual(r.etat, apprentissage.CONDITIONNELLE)
        self.assertEqual(r.compte_pour(tr("Z", date(2026, 1, 1), -40.0, "ACHAT", "Migros")), "6000")
        self.assertEqual(r.compte_pour(tr("Z", date(2026, 1, 1), -800.0, "ACHAT", "Migros")), "1500")
        self.assertIn("montant", r.condition)

    def test_critere_introuvable_suspend_et_alerte(self):
        comptes = ["6000", "6200", "6200", "6000", "6000", "6200"]
        montants = [-20.0, -25.0, -10.0, -30.0, -12.0, -22.0]
        a = analyser(*jeu(comptes, montants=montants))
        self.assertEqual(a.regles[0].etat, apprentissage.SUSPENDUE)
        self.assertEqual(a.regles[0].condition, "")
        self.assertIsNone(a.regles[0].compte_pour(tr("Z", date(2026, 1, 1), -20, "ACHAT", "Migros")))
        self.assertTrue(any("introuvable" in x.message for x in a.alertes))

    def test_regle_annulee_ne_s_applique_pas(self):
        transactions, corr = jeu(["6600"] * 3)
        corr["annulees"] = {("migros", "6600")}
        a = analyser(transactions, corr)
        self.assertEqual(a.regles[0].etat, apprentissage.ANNULEE)
        self.assertIsNone(a.regles[0].compte_pour(transactions[0]))

    def test_referentiel_faux_et_meme_erreur_ailleurs(self):
        referentiel = {"exercice": 2025,
                       "Partenaires": [{"partenaire": "Migros", "compte": "6500"},
                                       {"partenaire": "Coop", "compte": "6500"},
                                       {"partenaire": "Telco SA", "compte": "6510"}],
                       "PlanComptable": [{"code": "6500", "nom": "Frais"}, {"code": "6600", "nom": "Publicité"}]}
        a = analyser(*jeu(["6600"] * 3), referentiel=referentiel)
        texte = " ".join(x.message for x in a.alertes)
        self.assertIn("6500", texte)
        self.assertIn("Coop", texte)
        self.assertNotIn("Telco", texte)
        self.assertEqual(a.regles[0].compte_reference, "6500")

    def test_compte_absent_du_plan(self):
        referentiel = {"exercice": 2025, "Partenaires": [], "PlanComptable": [{"code": "6500", "nom": "Frais"}]}
        a = analyser(*jeu(["6699"] * 3), referentiel=referentiel)
        self.assertTrue(any("absent du plan comptable" in x.message for x in a.alertes))


class TestApplication(unittest.TestCase):
    def test_ordre_correction_puis_regle_puis_referentiel(self):
        transactions, corr = jeu(["6600"] * 3)
        nouvelle = tr("N", date(2025, 6, 1), -42.0, "ACHAT MIGROS 99", "Migros", "6500")
        autre = tr("A", date(2025, 6, 1), -42.0, "COOP", "Coop", "6500")
        transactions += [nouvelle, autre]
        analyse = analyser(transactions, corr)
        n = apprentissage.appliquer(transactions, analyse, corr, plan={"6600": "Publicité"})
        self.assertEqual(n, 1)
        self.assertEqual(transactions[0]["origine_compte"], "ta correction")
        self.assertEqual(nouvelle["compte_propose"], "6600 Publicité")
        self.assertEqual(nouvelle["origine_compte"], "appris")
        self.assertIn("3 corrections sur 3", nouvelle["fiabilite_compte"])
        self.assertEqual(autre["origine_compte"], "référentiel")
        self.assertEqual(analyse.resume["appliquees"], 1)

    def test_resume(self):
        transactions, corr = jeu(["6600"] * 3)
        a = analyser(transactions, corr)
        self.assertEqual(a.resume["corrections"], 3)
        self.assertEqual(a.resume["corrigees_par_rapport_au_referentiel"], 3)
        self.assertEqual(a.resume["actives"], 1)


class TestBoutEnBout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ancienne = config.RACINE
        config.definir_racine(self.tmp.name)

    def tearDown(self):
        config.definir_racine(self.ancienne)
        self.tmp.cleanup()

    def test_sortie_lisible_puis_relue_par_l_onglet(self):
        transactions, corr = jeu(["6600"] * 3)
        a = analyser(transactions, corr)
        config.DOSSIER_SORTIES.mkdir(parents=True)
        chemin = apprentissage.ecrire(a)
        self.assertEqual(chemin.name, "apprentissage.xlsx")
        relu = apprentissage.lire_sortie()
        self.assertEqual(relu["regles"][0]["partenaire"], "Migros")
        self.assertEqual(relu["regles"][0]["compte"], "6600")
        self.assertEqual(relu["resume"]["actives"], 1)


class TestReporter(unittest.TestCase):
    def setUp(self):
        from reconsigliere import exercices
        self.exercices = exercices
        self.tmp = tempfile.TemporaryDirectory()
        self.ancienne = config.RACINE
        config.definir_racine(self.tmp.name)
        listes = {nom: [] for nom in exercices.LISTES}
        listes["Changements"] = []
        listes["PlanComptable"] = [{"code": "6500", "nom": "Frais"}, {"code": "6600", "nom": "Publicité"}]
        listes["Partenaires"] = [{"partenaire": "Migros", "compte": "6500"}]
        exercices._ecrire(2025, listes)

    def tearDown(self):
        config.definir_racine(self.ancienne)
        self.tmp.cleanup()

    def test_modifie_le_partenaire_avec_motif(self):
        changements = apprentissage.reporter("MIGROS", "6600", 4)
        self.assertEqual(changements[0]["avant"], "6500")
        self.assertIn("appris de 4 corrections", changements[0]["motif"])
        migros = self.exercices.lire(2025)["Partenaires"][0]
        self.assertEqual(str(migros["compte"]), "6600")
        self.assertEqual(migros["libelle_compte"], "Publicité")

    def test_ajoute_un_partenaire_absent(self):
        apprentissage.reporter("Coop", "6600", 3)
        noms = [p["partenaire"] for p in self.exercices.lire(2025)["Partenaires"]]
        self.assertIn("Coop", noms)

    def test_exercice_valide_refuse(self):
        self.exercices.valider(2025, ouvrir_suivant=False)
        with self.assertRaises(self.exercices.ExerciceVerrouille):
            apprentissage.reporter("Migros", "6600", 3, annee=2025)

    def test_sans_exercice(self):
        config.definir_racine(Path(self.tmp.name) / "vide")
        with self.assertRaises(ValueError):
            apprentissage.reporter("Migros", "6600", 3)


class TestReconciliationComplete(unittest.TestCase):
    """La réconciliation lit les corrections de compte, applique la règle et écrit sorties/apprentissage.xlsx."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ancienne = config.RACINE
        config.definir_racine(self.tmp.name)

    def tearDown(self):
        config.definir_racine(self.ancienne)
        self.tmp.cleanup()

    def test_regle_appliquee_a_la_quatrieme_transaction(self):
        from reconsigliere.__main__ import main
        from reconsigliere import installation
        installation.creer_dossiers(config.RACINE)
        lignes = [{"date": f"0{i + 1}.03.2025", "montant": -40 - i, "libelle": f"ACHAT MIGROS {i}"} for i in range(4)]
        pd.DataFrame(lignes).to_csv(config.DOSSIER_TRANSACTIONS / "banque.csv", sep=";", index=False)
        main(log=lambda _t: None)
        ids = pd.read_excel(config.DOSSIER_SORTIES / "reconciliation.xlsx")["id_transaction"].tolist()
        wb = openpyxl.load_workbook(config.FICHIER_CORRECTIONS)
        ws = wb["transactions"]
        entete = [c.value for c in ws[1]]
        for tid in ids[:3]:
            ligne = [None] * len(entete)
            ligne[entete.index("id_transaction")] = tid
            ligne[entete.index("compte")] = "6600"
            ws.append(ligne)
        wb.save(config.FICHIER_CORRECTIONS)

        resultat = main(log=lambda _t: None)
        sortie = pd.read_excel(config.DOSSIER_SORTIES / "reconciliation.xlsx").set_index("id_transaction")
        self.assertEqual(str(sortie.loc[ids[3], "compte_propose"]), "6600")
        self.assertEqual(sortie.loc[ids[3], "origine_compte"], "appris")
        self.assertEqual(sortie.loc[ids[0], "origine_compte"], "ta correction")
        self.assertEqual(resultat["apprentissage"], apprentissage.fichier_sortie())
        self.assertEqual(apprentissage.lire_sortie()["resume"]["appliquees"], 1)


if __name__ == "__main__":
    unittest.main()
