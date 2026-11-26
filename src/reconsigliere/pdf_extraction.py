"""Lecture des factures (PDF et images) et repérage des montants, dates, IBAN et numéros."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

from . import config
from .outils import en_date, en_montant, normaliser

RE_MONTANT = re.compile(r"(?<![\d])(\d{1,3}(?:['’ .]\d{3})*(?:[.,]\d{2}))(?![\d])")
RE_DATE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b")
RE_IBAN = re.compile(r"\b([A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,3})?)\b")
RE_NUMERO = re.compile(
    r"\b(?:facture|rechnung|invoice|n[o°]|nr|num[eé]ro|r[eé]f[eé]rence)\b\.?\s*[:#.]?\s*((?=[A-Z0-9\-/]*\d)[A-Z0-9][A-Z0-9\-/]{3,})",
    re.IGNORECASE,
)


def empreinte(chemin: Path) -> str:
    return hashlib.sha1(chemin.read_bytes()).hexdigest()


def lire_texte(chemin: Path) -> str:
    try:
        lecteur = PdfReader(str(chemin))
        return "\n".join((page.extract_text() or "") for page in lecteur.pages)
    except Exception as erreur:  # PDF protégé ou abîmé
        return f"__ERREUR_LECTURE__ {erreur}"


def _tesseract() -> str | None:
    if config.CHEMIN_TESSERACT and Path(config.CHEMIN_TESSERACT).exists():
        return config.CHEMIN_TESSERACT
    trouve = shutil.which("tesseract")
    if trouve:
        return trouve
    defaut = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    return str(defaut) if defaut.exists() else None


def lire_image(chemin: Path) -> str:
    """Lit le texte d'une image si Tesseract OCR est installé, sinon renvoie une chaîne vide."""
    exe = _tesseract()
    if not exe:
        return ""
    try:
        resultat = subprocess.run([exe, str(chemin), "stdout", "-l", config.LANGUES_OCR],
                                  capture_output=True, text=True, encoding="utf-8", timeout=120,
                                  # Windows : pas de fenêtre noire qui clignote pour chaque image
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return resultat.stdout
    except Exception as erreur:
        return f"__ERREUR_LECTURE__ {erreur}"


def ocr_disponible() -> bool:
    return _tesseract() is not None


def analyser_piece(chemin: Path) -> dict:
    texte = lire_texte(chemin) if chemin.suffix.lower() == ".pdf" else lire_image(chemin)
    montants = sorted({m for m in (en_montant(x) for x in RE_MONTANT.findall(texte)) if m}, reverse=True)
    dates = []
    for j, m, a in RE_DATE.findall(texte):
        a = ("20" + a) if len(a) == 2 else a
        d = en_date(f"{j}.{m}.{a}")
        if d and 2000 <= d.year <= 2100 and d not in dates:
            dates.append(d)
    ibans = sorted({i.replace(" ", "") for i in RE_IBAN.findall(texte)})
    numeros = list(dict.fromkeys(RE_NUMERO.findall(texte)))[:5]
    return {
        "chemin": chemin,
        "nom": chemin.name,
        "empreinte": empreinte(chemin),
        "texte": texte,
        "texte_norm": normaliser(texte) + " " + normaliser(chemin.stem.replace("_", " ")),
        "lisible": bool(texte.strip()) and not texte.startswith("__ERREUR_LECTURE__"),
        "montants": montants,
        "dates": dates,
        "ibans": ibans,
        "numeros": numeros,
    }


def analyser_dossier(dossier: Path) -> list[dict]:
    if not dossier.exists():
        return []
    vus: set[str] = set()
    resultats = []
    fichiers = sorted(p for p in dossier.rglob("*")
                      if p.is_file() and p.suffix.lower() in config.EXTENSIONS_PIECES)
    for chemin in fichiers:
        info = analyser_piece(chemin)
        if info["empreinte"] in vus:  # doublon exact
            continue
        vus.add(info["empreinte"])
        resultats.append(info)
    return resultats
