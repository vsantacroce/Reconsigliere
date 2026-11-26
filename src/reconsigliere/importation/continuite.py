"""Passe de continuité : rattache les pages sans titre à la section en cours."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..outils import normaliser
from .classement import lignes, lignes_ecritures, lignes_plan
from .pages import Page

RE_REPORT = re.compile(r"\b(report|a reporter|solde reporte|uebertrag|ubertrag|carried forward|"
                       r"brought forward|suite)\b")
RE_PAGE = re.compile(r"\bpage\s+(\d+)(?:\s*(?:/|sur|of|von)\s*(\d+))?")
MOTS_COLONNES = ("date", "compte", "piece", "libelle", "debit", "credit", "solde", "code", "nom", "type")


@dataclass
class Section:
    type: str
    pages: list[Page] = field(default_factory=list)
    methode: str = "regles"


def _numero_page(texte: str) -> tuple[int, int | None] | None:
    trouve = RE_PAGE.findall(normaliser(texte))
    if not trouve:
        return None
    n, total = trouve[-1]
    return int(n), int(total) if total else None


def _entete(texte: str) -> frozenset[str] | None:
    for l in lignes(texte)[:6]:
        mots = {m for m in MOTS_COLONNES if m in normaliser(l).split()}
        if len(mots) >= 3:
            return frozenset(mots)
    return None


def signe_continuite(precedente: Page, page: Page, type_courant: str) -> bool:
    debut = normaliser("\n".join(lignes(page.texte)[:3]))
    if RE_REPORT.search(debut):
        return True
    a, b = _numero_page(precedente.texte), _numero_page(page.texte)
    if a and b and b[0] == a[0] + 1 and (a[1] is None or a[1] == b[1]):
        return True
    ea, eb = _entete(precedente.texte), _entete(page.texte)
    if ea and eb and ea == eb:
        return True
    if type_courant == "grand_livre" and lignes_ecritures(page.texte) >= 2:
        return True
    if type_courant == "plan_comptable" and lignes_plan(page.texte) >= 3:
        return True
    if (precedente.tableau is not None and page.tableau is not None
            and list(precedente.tableau.columns) == list(page.tableau.columns)):
        return True
    return False


def regrouper(pages: list[Page], classements: list[tuple[str | None, float, bool]]
              ) -> list[tuple[Page, str | None, str]]:
    """Renvoie (page, type ou None, méthode) ; méthode = regles | continuite | indecis."""
    res: list[tuple[Page, str | None, str]] = []
    courant: str | None = None
    precedente: Page | None = None
    for page, (type_, _score, fort) in zip(pages, classements):
        if fort:
            res.append((page, type_, "regles"))
            courant = type_
        elif courant and precedente is not None \
                and (type_ == courant or signe_continuite(precedente, page, courant)):
            res.append((page, courant, "continuite"))
        elif type_:
            res.append((page, type_, "regles"))
            courant = type_
        else:
            res.append((page, None, "indecis"))
        if page.lisible:
            precedente = page
    return res


def en_sections(typees: list[tuple[Page, str | None, str]]) -> list[Section]:
    sections: list[Section] = []
    for page, type_, methode in typees:
        type_ = type_ or "autre"
        if sections and sections[-1].type == type_ and methode == "continuite":
            sections[-1].pages.append(page)
        elif sections and sections[-1].type == type_ and type_ in ("autre", "annexe"):
            sections[-1].pages.append(page)
        else:
            sections.append(Section(type=type_, pages=[page], methode=methode))
    return sections
