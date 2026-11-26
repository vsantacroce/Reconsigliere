"""Découpe un document en pages : page PDF, image, ou feuille Excel/CSV."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd
from pypdf import PdfReader

from .. import config
from ..outils import normaliser

EXT_PDF = {".pdf"}
EXT_IMAGES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
EXT_TABLEURS = {".xlsx", ".xlsm", ".xls", ".csv"}
EXTENSIONS = EXT_PDF | EXT_IMAGES | EXT_TABLEURS

SEUIL_TEXTE = 40  # en dessous, la page PDF est considérée comme scannée
MOTS_ENTETE = {"date", "compte", "code", "numero", "no", "nom", "libelle", "debit", "credit", "solde",
               "piece", "partenaire", "type", "montant", "description", "intitule", "account", "name",
               "journal", "reference", "label", "balance"}

Ocr = Callable[[Path, "int | None"], str]


@dataclass
class Page:
    numero: int
    texte: str
    tableau: pd.DataFrame | None = None
    lisible: bool = True
    nom_feuille: str = ""


# ------------------------------------------------------------------ OCR

def _tesseract(chemin_image: Path) -> str:
    from ..pdf_extraction import _tesseract as trouver
    exe = trouver()
    if not exe:
        return ""
    try:
        res = subprocess.run([exe, str(chemin_image), "stdout", "-l", config.LANGUES_OCR],
                             capture_output=True, text=True, encoding="utf-8", timeout=180,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return res.stdout
    except Exception:
        return ""


def ocr_defaut(chemin: Path, numero: int | None) -> str:
    """Image : Tesseract direct. Page PDF scannée : Tesseract sur les images de la page."""
    if numero is None:
        return _tesseract(chemin)
    try:
        page = PdfReader(str(chemin)).pages[numero - 1]
        textes = []
        with tempfile.TemporaryDirectory() as d:
            for k, image in enumerate(page.images):
                cible = Path(d) / f"p{numero}_{k}{Path(image.name).suffix or '.png'}"
                cible.write_bytes(image.data)
                textes.append(_tesseract(cible))
        return "\n".join(textes)
    except Exception:
        return ""


# ------------------------------------------------------------------ tableurs

def _ligne_entete(brut: pd.DataFrame) -> int:
    """Première ligne (sur 15) qui ressemble à des en-têtes de colonnes."""
    for i in range(min(15, len(brut))):
        mots = {normaliser(v).strip(" .:") for v in brut.iloc[i].tolist() if isinstance(v, str)}
        if sum(1 for m in mots if m in MOTS_ENTETE or m.split(" ")[0] in MOTS_ENTETE) >= 2:
            return i
    return 0


def _mettre_en_forme(brut: pd.DataFrame) -> pd.DataFrame:
    brut = brut.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    if brut.empty:
        return brut
    i = _ligne_entete(brut)
    colonnes = [str(c).strip() if isinstance(c, str) and c.strip() else f"colonne_{k + 1}"
                for k, c in enumerate(brut.iloc[i].tolist())]
    df = brut.iloc[i + 1:].reset_index(drop=True)
    df.columns = colonnes
    return df


def _texte_tableau(nom: str, df: pd.DataFrame, lignes_max: int = 40) -> str:
    lignes = [nom, " ".join(map(str, df.columns))]
    for _, rang in df.head(lignes_max).iterrows():
        lignes.append(" ".join(str(v) for v in rang.tolist() if isinstance(v, str) and v.strip()))
    return "\n".join(lignes)


def _lire_csv(chemin: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(chemin, sep=None, engine="python", dtype=str, header=None, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.DataFrame()


def _pages_tableur(chemin: Path) -> list[Page]:
    if chemin.suffix.lower() == ".csv":
        feuilles = {chemin.stem: _lire_csv(chemin)}
    else:
        feuilles = pd.read_excel(chemin, sheet_name=None, dtype=str, header=None)
    res = []
    for k, (nom, brut) in enumerate(feuilles.items(), start=1):
        df = _mettre_en_forme(brut)
        res.append(Page(numero=k, texte=_texte_tableau(nom, df), tableau=df,
                        lisible=not df.empty, nom_feuille=str(nom)))
    return res


# ------------------------------------------------------------------ point d'entrée

def lire_pages(chemin: Path, ocr: Ocr | None = None) -> list[Page]:
    chemin = Path(chemin)
    ocr = ocr or ocr_defaut
    ext = chemin.suffix.lower()
    if ext in EXT_TABLEURS:
        return _pages_tableur(chemin)
    if ext in EXT_IMAGES:
        texte = ocr(chemin, None)
        return [Page(numero=1, texte=texte, lisible=len(texte.strip()) >= SEUIL_TEXTE)]
    if ext in EXT_PDF:
        res = []
        for n, p in enumerate(PdfReader(str(chemin)).pages, start=1):
            try:
                texte = p.extract_text() or ""
            except Exception:
                texte = ""
            if len(texte.strip()) < SEUIL_TEXTE:
                lu = ocr(chemin, n)
                texte = lu if len(lu.strip()) > len(texte.strip()) else texte
            res.append(Page(numero=n, texte=texte, lisible=len(texte.strip()) >= SEUIL_TEXTE))
        return res
    raise ValueError(f"Format non pris en charge : {chemin.name}")
