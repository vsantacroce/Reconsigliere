"""Réglages du projet. Modifie ce fichier pour adapter l'outil à tes fichiers."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
DOSSIER_CODE = RACINE


def definir_racine(racine) -> None:
    """Change le dossier de travail (celui qui contient entrees et sorties)."""
    global RACINE, DOSSIER_FACTURES, DOSSIER_TRANSACTIONS, DOSSIER_INFOS_BANCAIRES
    global DOSSIER_COMPTABILITE, DOSSIER_CORRECTIONS, FICHIER_CORRECTIONS
    global DOSSIER_SORTIES, DOSSIER_PDF_RENOMMES, DOSSIER_A_COMPTABILISER
    RACINE = Path(racine).resolve()
    DOSSIER_FACTURES = RACINE / "entrees" / "01_factures"
    DOSSIER_TRANSACTIONS = RACINE / "entrees" / "02_transactions_a_reconcilier"
    DOSSIER_INFOS_BANCAIRES = RACINE / "entrees" / "03_infos_bancaires"
    DOSSIER_COMPTABILITE = RACINE / "entrees" / "04_comptabilite"
    DOSSIER_CORRECTIONS = RACINE / "entrees" / "05_mes_corrections"
    FICHIER_CORRECTIONS = DOSSIER_CORRECTIONS / "mes_corrections.xlsx"
    DOSSIER_SORTIES = RACINE / "sorties"
    DOSSIER_PDF_RENOMMES = DOSSIER_SORTIES / "pdf_renommes"
    DOSSIER_A_COMPTABILISER = DOSSIER_SORTIES / "a_comptabiliser"


definir_racine(RACINE)

DEVISE = "CHF"

# Types de pièces acceptés
EXTENSIONS_PIECES = {".pdf", ".png", ".jpg", ".jpeg"}

# Lecture du texte des images (optionnelle) : installe Tesseract OCR pour l'activer.
# Laisse vide pour le chercher automatiquement.
CHEMIN_TESSERACT = ""
LANGUES_OCR = "fra+deu+eng"

# Tolérances du rapprochement
TOLERANCE_MONTANT = 0.01      # écart de montant accepté
TOLERANCE_JOURS = 15          # écart de date accepté entre facture et paiement
SEUIL_SUR = 60                # score à partir duquel le lien est considéré comme sûr
SEUIL_A_CONFIRMER = 40        # score à partir duquel le lien est proposé

# Apprentissage : nombre de corrections identiques de compte pour un partenaire avant que le programme
# applique seul ce compte aux transactions suivantes (voir docs/apprentissage.md).
SEUIL_REGLE = 3

# Noms de colonnes reconnus dans les Excel (en minuscules, sans accents).
# Ajoute ici les noms utilisés par ta banque ou ta comptabilité.
ALIAS_COLONNES = {
    "date": ["date", "date valeur", "date de valeur", "date comptable", "date operation",
             "date transaction", "booking date", "value date", "datum"],
    "montant": ["montant", "amount", "betrag", "montant chf", "montant total"],
    "debit": ["debit", "débit", "sortie", "retrait", "lastschrift"],
    "credit": ["credit", "crédit", "entree", "versement", "gutschrift"],
    "libelle": ["libelle", "libellé", "description", "texte", "communication", "details",
                "motif", "texte de reservation", "buchungstext", "avis"],
    "iban": ["iban", "compte", "iban contrepartie", "compte contrepartie"],
    "reference": ["reference", "référence", "ref", "numero", "no facture", "numero facture",
                  "reference qr", "invoice"],
    "partenaire": ["partenaire", "fournisseur", "client", "beneficiaire", "bénéficiaire",
                   "donneur d'ordre", "contrepartie", "nom", "tiers"],
    "fichier": ["fichier", "nom fichier", "nom du fichier", "piece", "pièce", "document", "pdf"],
    "statut": ["statut", "etat", "état", "status"],
}
