"""Ce qui a été importé, relu depuis les classeurs normalisés, pour l'onglet Documents.

Source unique : entrees/06_societe/imports/AAAA/*.xlsx, les mêmes classeurs que lit l'Assistant société.
Aucun tkinter ici : tout est testable sans fenêtre.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl

from ..outils import nom_de_fichier_sur, normaliser
from .classement import LIBELLES
from .sorties import COLONNES

# type de page → onglet du classeur
TABLES = {"plan_comptable": "plancomptable", "grand_livre": "grandlivre", "bilan": "bilan",
          "compte_resultat": "compteresultat", "annexe": "annexe", "autre": "annexe"}
METHODES_A_VERIFIER = {"a_verifier", "illisible"}


@dataclass
class Import:
    classeur: Path
    racine: Path
    meta: dict = field(default_factory=dict)
    tables: dict[str, list[dict]] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return str(self.meta.get("fichier_source") or self.classeur.name)

    @property
    def exercice(self) -> int | None:
        try:
            return int(str(self.meta.get("date_debut", ""))[:4])
        except ValueError:
            return None

    @property
    def pages(self) -> list[dict]:
        return self.tables.get("pages", [])

    @property
    def controles(self) -> list[dict]:
        return self.tables.get("controles", [])

    @property
    def nb_pages(self) -> int:
        return len(self.pages)

    @property
    def methodes(self) -> dict[str, int]:
        return dict(Counter(p["methode"] for p in self.pages))

    @property
    def etat(self) -> str:
        if any(c["resultat"] != "ok" for c in self.controles) or \
                any(p["methode"] in METHODES_A_VERIFIER for p in self.pages):
            return "a_verifier"
        return "ok"

    @property
    def chemin_source(self) -> Path:
        return self.racine / "entrees" / "07_documents" / self.source

    @property
    def html(self) -> Path:
        return self.racine / "sorties" / "imports" / f"{nom_de_fichier_sur(Path(self.source).stem, 60)}.html"

    def pages_de(self, type_: str) -> list[int]:
        return [int(p["page"]) for p in self.pages if p["type"] == type_]

    def sections(self) -> list[tuple[str, list[int]]]:
        res: list[tuple[str, list[int]]] = []
        for p in self.pages:
            if res and res[-1][0] == p["type"]:
                res[-1][1].append(int(p["page"]))
            else:
                res.append((p["type"], [int(p["page"])]))
        return res

    def resume_sections(self) -> str:
        return " · ".join(f"{LIBELLES.get(t, t)} {plage(n)}" for t, n in self.sections())


def plage(numeros: list[int]) -> str:
    """[3, 4, 5, 8] → « p.3–5, 8 »."""
    morceaux, debut, prec = [], None, None
    for n in sorted(numeros):
        if debut is None:
            debut = prec = n
        elif n == prec + 1:
            prec = n
        else:
            morceaux.append(f"{debut}–{prec}" if prec != debut else f"{debut}")
            debut = prec = n
    if debut is not None:
        morceaux.append(f"{debut}–{prec}" if prec != debut else f"{debut}")
    return "p." + ", ".join(morceaux) if morceaux else ""


def _lire_classeur(chemin: Path, racine: Path) -> Import | None:
    try:
        wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    except Exception:
        return None
    try:
        noms = {ws.title.lower(): ws for ws in wb.worksheets}
        if "meta" not in noms or "pages" not in noms:
            return None  # classeur qui ne vient pas du pipeline d'import
        tables = {}
        for onglet, colonnes in COLONNES.items():
            ws = noms.get(onglet)
            lignes = list(ws.iter_rows(values_only=True)) if ws is not None else []
            if not lignes:
                tables[onglet] = []
                continue
            entetes = [str(c or "") for c in lignes[0]]
            tables[onglet] = [dict(zip(entetes, l)) for l in lignes[1:] if any(v is not None for v in l)]
        meta = {l["cle"]: l["valeur"] for l in tables.pop("meta")}
        return Import(classeur=chemin, racine=racine, meta=meta, tables=tables)
    finally:
        wb.close()


def charger(racine: Path) -> list[Import]:
    dossier = Path(racine) / "entrees" / "06_societe" / "imports"
    if not dossier.exists():
        return []
    res = [i for c in sorted(dossier.glob("*/*.xlsx")) if not c.name.startswith("~$")
           for i in [_lire_classeur(c, Path(racine))] if i]
    return sorted(res, key=lambda i: (i.exercice or 0, i.source))


def exercices(imports: list[Import]) -> list[int]:
    return sorted({i.exercice for i in imports if i.exercice})


# ------------------------------------------------------------------ vues par type

def _chf(x: float) -> str:
    return f"{x:,.2f}".replace(",", "'")


def _controles(type_: str, lignes: list[dict], imports: list[Import]) -> list[dict]:
    res = []
    if type_ == "grand_livre" and lignes:
        d = round(sum(l["debit"] or 0 for l in lignes), 2)
        c = round(sum(l["credit"] or 0 for l in lignes), 2)
        res.append({"controle": "Grand livre équilibré", "resultat": "ok" if abs(d - c) < 0.01 else "ecart",
                    "detail": f"débits {_chf(d)}, crédits {_chf(c)}, écart {_chf(d - c)}"})
        sans = sum(1 for l in lignes if not l.get("compte"))
        if sans:
            res.append({"controle": "Lignes sans compte", "resultat": "ecart", "detail": f"{sans} ligne(s)"})
        partenaires = sum(1 for l in lignes if l.get("partenaire"))
        res.append({"controle": "Lignes avec partenaire", "resultat": "ok" if partenaires else "info",
                    "detail": f"{partenaires} sur {len(lignes)}"})
    elif type_ == "plan_comptable" and lignes:
        doublons = sorted(k for k, n in Counter(str(l["code"]) for l in lignes).items() if n > 1)
        res.append({"controle": "Codes en double", "resultat": "ecart" if doublons else "ok",
                    "detail": ", ".join(doublons) or "aucun"})
        sans_nom = [str(l["code"]) for l in lignes if not l.get("nom")]
        if sans_nom:
            res.append({"controle": "Comptes sans nom", "resultat": "ecart", "detail": ", ".join(sans_nom)})
    elif type_ in ("bilan", "compte_resultat"):
        nom = "Bilan : actifs = passifs" if type_ == "bilan" else None
        for imp in imports:
            for c in imp.controles:
                if nom and c["controle"] == nom:
                    res.append({**c, "detail": f"{imp.source} : {c['detail']}"})
        if type_ == "compte_resultat":
            for l in lignes:
                if normaliser(l["libelle"]).startswith(("resultat", "benefice", "perte de l'exercice")):
                    res.append({"controle": "Résultat lu", "resultat": "info",
                                "detail": f"{l['libelle']} : {_chf(l['montant'])}"})
    elif type_ == "autre" and lignes:
        res.append({"controle": "Pages non comptables", "resultat": "ecart",
                    "detail": f"{len(lignes)} page(s) : à vérifier ou à ignorer"})
    for imp in imports:  # pages illisibles ou laissées « à vérifier » de ce type
        douteuses = [str(p["page"]) for p in imp.pages if p["type"] == type_ and p["methode"] in METHODES_A_VERIFIER]
        if douteuses and type_ != "autre":
            res.append({"controle": "Pages à vérifier", "resultat": "ecart",
                        "detail": f"{imp.source} p.{', '.join(douteuses)}"})
    return res


def vue(imports: list[Import], type_: str, exercice: int | None) -> dict:
    """Sources, contrôles et lignes d'un type de document, pour un exercice (None = tous)."""
    choisis = [i for i in imports if exercice is None or i.exercice == exercice]
    table = TABLES[type_]
    sources, lignes, retenus = [], [], []
    for imp in choisis:
        pages = imp.pages_de(type_)
        if not pages:
            continue
        retenus.append(imp)
        methodes = Counter(p["methode"] for p in imp.pages if p["type"] == type_)
        sources.append({"fichier": imp.source, "pages": plage(pages), "exercice": imp.exercice,
                        "methodes": dict(methodes), "import": imp})
        lignes_imp = imp.tables.get(table, [])
        if table == "annexe":
            lignes_imp = [l for l in lignes_imp if int(l["page"]) in pages]
        lignes += lignes_imp
    return {"sources": sources, "lignes": lignes, "controles": _controles(type_, lignes, retenus)}


def arbre(lignes: list[dict]) -> list[dict]:
    """Bilan ou compte de résultat en arbre : rubrique › sous-rubrique › ligne."""
    racines: list[dict] = []

    def noeud(liste, libelle):
        for n in liste:
            if n["libelle"] == libelle and n.get("groupe"):
                return n
        n = {"libelle": libelle, "groupe": True, "enfants": [], "montant": None, "precedent": None}
        liste.append(n)
        return n
    for l in lignes:
        niveau = racines
        for partie in [p for p in re.split(r"\s*/\s*", l.get("rubrique") or "") if p]:
            niveau = noeud(niveau, partie)["enfants"]
        libelle = f"{l['compte']} {l['libelle']}".strip() if l.get("compte") else l["libelle"]
        niveau.append({"libelle": libelle, "groupe": False, "enfants": [], "montant": l.get("montant"),
                       "precedent": l.get("colonne_exercice_precedent"), "niveau": l.get("niveau")})
    return racines
