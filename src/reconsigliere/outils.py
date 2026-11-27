"""Petites fonctions communes : normalisation de texte, montants et dates."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

import pandas as pd


def sans_accents(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", str(texte))
    return "".join(c for c in texte if not unicodedata.combining(c))


def normaliser(texte) -> str:
    """Minuscules, sans accents, espaces simples."""
    if texte is None or (isinstance(texte, float) and pd.isna(texte)):
        return ""
    texte = sans_accents(texte).lower()
    return re.sub(r"\s+", " ", texte).strip()


def en_montant(valeur) -> float | None:
    """Convertit 1'234.50, 1 234,50, -89.90 CHF, etc. en nombre."""
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return None
    if isinstance(valeur, (int, float)):
        return round(float(valeur), 2)
    texte = re.sub(r"[^\d,.\-]", "", str(valeur).replace("'", "").replace("’", ""))
    if not texte or texte in {"-", ".", ","}:
        return None
    if "," in texte and "." in texte:
        if texte.rfind(",") > texte.rfind("."):
            texte = texte.replace(".", "").replace(",", ".")
        else:
            texte = texte.replace(",", "")
    elif "," in texte:
        texte = texte.replace(",", ".")
    try:
        return round(float(texte), 2)
    except ValueError:
        return None


def en_date(valeur) -> date | None:
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return None
    if isinstance(valeur, datetime):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    texte = str(valeur).strip()
    iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})", texte)
    if iso:  # AAAA-MM-JJ : ne pas inverser jour et mois
        try:
            return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except ValueError:
            return None
    d = pd.to_datetime(texte, dayfirst=True, errors="coerce")
    return None if pd.isna(d) else d.date()


def nom_de_fichier_sur(texte: str, longueur_max: int = 40) -> str:
    """Rend un texte utilisable dans un nom de fichier Windows."""
    texte = sans_accents(texte or "")
    texte = re.sub(r"[^A-Za-z0-9.\-]+", "-", texte).strip("-")
    return texte[:longueur_max].strip("-") or "Inconnu"


def code_compte(valeur) -> str:
    """Numéro de compte en texte : 6600.0 (saisi comme nombre dans Excel) devient « 6600 »."""
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return ""
    if isinstance(valeur, float) and valeur.is_integer():
        valeur = int(valeur)
    texte = str(valeur).strip()
    return texte[:-2] if re.fullmatch(r"\d+\.0", texte) else texte
