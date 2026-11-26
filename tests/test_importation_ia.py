"""IA en secours et banc de comparaison : aucun appel réseau, l'envoi est simulé."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import installation  # noqa: E402
from reconsigliere.importation import banc, ia  # noqa: E402


def faux(reponse="grand_livre", entree=120, sortie=3, stop="end_turn"):
    appels = []

    def envoyer(requete):
        appels.append(requete)
        r = reponse(requete) if callable(reponse) else reponse
        return {"texte": r, "entree": entree, "sortie": sortie, "stop": stop}
    envoyer.appels = appels
    return envoyer


class TestReglages(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.p = mock.patch.object(installation, "_fichier_reglages",
                                   return_value=Path(self.dossier.name) / "reglages.json")
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.dossier.cleanup()

    def test_memoriser_garde_la_cle(self):
        installation.ecrire_reglage("cle_api_anthropic", "sk-test")
        installation.memoriser(Path("/tmp/travail"))
        self.assertEqual(installation.lire_reglages()["cle_api_anthropic"], "sk-test")
        self.assertEqual(installation.dossier_memorise(), Path("/tmp/travail"))

    def test_cle_et_modele(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(ia.cle_api())
            self.assertEqual(ia.modele(), "claude-haiku-5-5")
            installation.ecrire_reglage("cle_api_anthropic", "sk-reglage")
            installation.ecrire_reglage("modele_ia", "sonnet")
            self.assertEqual(ia.cle_api(), "sk-reglage")
            self.assertEqual(ia.modele(), "claude-sonnet-5-5")
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-env", "RECONSIGLIERE_MODELE": "haiku"}):
            self.assertEqual(ia.cle_api(), "sk-env")
            self.assertEqual(ia.modele(), "claude-haiku-5-5")


class TestClasserParIA(unittest.TestCase):
    def test_requete_courte_et_modele(self):
        envoyer = faux("Grand livre")
        type_, usage = ia.classer_par_ia("x" * 10_000, "sk", "claude-haiku-5-5", envoyer=envoyer)
        self.assertEqual(type_, "grand_livre")
        req = envoyer.appels[0]
        self.assertEqual(req["model"], "claude-haiku-5-5")
        self.assertLessEqual(len(req["messages"][0]["content"]), ia.EXTRAIT_MAX + 200)
        self.assertEqual(usage, {"entree": 120, "sortie": 3})

    def test_reponses_variees(self):
        for reponse, attendu in [("compte_resultat", "compte_resultat"), ("Compte de résultat.", "compte_resultat"),
                                 ("BILAN", "bilan"), ("plan comptable", "plan_comptable"),
                                 ("annexe", "annexe"), ("je ne sais pas", "autre")]:
            with self.subTest(reponse=reponse):
                self.assertEqual(ia.classer_par_ia("p", "sk", "claude-haiku-5-5", envoyer=faux(reponse))[0], attendu)

    def test_erreur_reseau_ou_refus(self):
        def casse(_):
            raise OSError("hors ligne")
        self.assertIsNone(ia.classer_par_ia("p", "sk", "claude-haiku-5-5", envoyer=casse)[0])
        self.assertIsNone(ia.classer_par_ia("p", "sk", "claude-haiku-5-5", envoyer=faux("bilan", stop="refusal"))[0])

    def test_reglage_reflexion_par_modele(self):
        self.assertEqual(ia.requete("p", "claude-haiku-5-5")["thinking"], {"type": "disabled"})
        self.assertEqual(ia.requete("p", "claude-sonnet-5-5")["thinking"], {"type": "between_tools"})


class TestBanc(unittest.TestCase):
    def test_comparer(self):
        attendus = {b["texte"][:40]: b["attendu"] for b in banc.PAGES}
        oracle = faux(lambda req: next(v for k, v in attendus.items() if k in req["messages"][0]["content"]))
        res = banc.comparer(["haiku", "sonnet"], "sk", envoyer=oracle)
        self.assertEqual([r["modele"] for r in res], ["claude-haiku-5-5", "claude-sonnet-5-5"])
        self.assertEqual(res[0]["justes"], len(banc.PAGES))
        self.assertEqual(res[0]["entree"], 120 * len(banc.PAGES))
        self.assertGreater(res[1]["cout_usd"], res[0]["cout_usd"])
        self.assertGreaterEqual(len(banc.PAGES), 12)


if __name__ == "__main__":
    unittest.main()
