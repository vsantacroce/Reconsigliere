"""Tests sans données réelles : python -m unittest discover -s tests"""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reconsigliere import rapprochement  # noqa: E402
from reconsigliere.outils import en_montant, nom_de_fichier_sur  # noqa: E402


def pdf(nom, montants, dates, texte="", ibans=(), numeros=()):
    return {"nom": nom, "empreinte": nom, "chemin": Path(nom), "montants": list(montants),
            "dates": list(dates), "texte_norm": texte.lower(), "ibans": list(ibans),
            "numeros": list(numeros), "lisible": True}


def transaction(tid, d, montant, libelle, **autres):
    t = {"id": tid, "date": d, "montant": montant, "libelle": libelle, "iban": "",
         "reference": "", "partenaire": "", "fichier": "", "statut": "", "source": "test"}
    t.update(autres)
    return t


VIDE = {"regles_partenaires": [], "transactions": {}}


class TestMontants(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(en_montant("1'234.50"), 1234.50)
        self.assertEqual(en_montant("1 234,50"), 1234.50)
        self.assertEqual(en_montant("-89.90 CHF"), -89.90)
        self.assertEqual(en_montant("1.234,50"), 1234.50)

    def test_nom_fichier(self):
        self.assertEqual(nom_de_fichier_sur("Café Müller / Genève"), "Cafe-Muller-Geneve")


class TestRapprochement(unittest.TestCase):
    def test_lien_sur(self):
        t = [transaction("T1", date(2026, 3, 14), -89.90, "ORDRE E-BANKING SWISSCOM")]
        p = [pdf("facture.pdf", [89.90], [date(2026, 3, 1)], "swisscom facture")]
        rapprochement.reconcilier(t, p, [], [], VIDE)
        self.assertEqual(t[0]["pdf"]["nom"], "facture.pdf")
        self.assertEqual(t[0]["statut"], rapprochement.STATUT_A_COMPTABILISER)

    def test_manquant(self):
        t = [transaction("T1", date(2026, 3, 14), -50.00, "ACHAT MIGROS")]
        rapprochement.reconcilier(t, [pdf("x.pdf", [12.00], [])], [], [], VIDE)
        self.assertEqual(t[0]["statut"], rapprochement.STATUT_MANQUANT)

    def test_comptabilise(self):
        t = [transaction("T1", date(2026, 3, 14), -89.90, "SWISSCOM")]
        compta = [{"date": date(2026, 3, 10), "montant": 89.90, "fichier": "", "libelle": ""}]
        rapprochement.reconcilier(t, [], compta, [], VIDE)
        self.assertEqual(t[0]["statut"], rapprochement.STATUT_COMPTABILISE)

    def test_corrections_priment(self):
        t = [transaction("T1", date(2026, 3, 14), -20.00, "FRAIS")]
        corr = {"regles_partenaires": [("frais", "Banque")],
                "transactions": {"T1": {"partenaire": "", "pdf": "", "explication": "Frais de tenue",
                                        "statut_force": "Sans piece"}}}
        rapprochement.reconcilier(t, [], [], [], corr)
        self.assertEqual(t[0]["partenaire_trouve"], "Banque")
        self.assertEqual(t[0]["statut"], rapprochement.STATUT_EXPLIQUE)

    def test_un_pdf_une_transaction(self):
        t = [transaction("T1", date(2026, 3, 14), -100.0, "A"),
             transaction("T2", date(2026, 3, 15), -100.0, "B")]
        p = [pdf("une.pdf", [100.0], [date(2026, 3, 14)])]
        rapprochement.reconcilier(t, p, [], [], VIDE)
        self.assertEqual(sum(x["pdf"] is not None for x in t), 1)


if __name__ == "__main__":
    unittest.main()
