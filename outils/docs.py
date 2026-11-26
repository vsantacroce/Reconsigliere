"""Documentation vivante de Reconsigliere : tient docs/modules à jour avec le code.

    python outils/docs.py                 régénère les parties automatiques et docs/carte.md
    python outils/docs.py --verifier      échoue si une page manque, est incomplète ou n'est pas à jour
    python outils/docs.py --depuis main   échoue si un module a changé depuis main sans que sa page change

Chaque module src/reconsigliere/a/b.py a sa page docs/modules/a/b.md. La page contient le texte
écrit à la main (rubriques obligatoires ci-dessous) et une partie générée entre DEBUT et FIN :
dépendances, modules qui l'utilisent, bibliothèques externes, fonctions publiques.
Bibliothèque standard seulement : le contrôle tourne sans installer les dépendances du programme.
"""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEBUT = "<!-- debut-auto -->"
FIN = "<!-- fin-auto -->"
A_COMPLETER = "_À compléter._"
RUBRIQUES = ["## À quoi il sert", "## Ce qu'il lit", "## Ce qu'il écrit", "## Ce qui casse si on le change"]
PAQUET = Path("src/reconsigliere")
DOSSIER_PAGES = Path("docs/modules")
CARTE = Path("docs/carte.md")
# Lanceurs hors du paquet, documentés comme des modules.
AUTRES_MODULES = {"windows/demarrer.pyw": "windows.demarrer"}
# Fichiers qui ne sont pas du Python mais dont le changement doit mettre à jour une page.
ASSOCIES = {
    "src/reconsigliere/modele.html": "docs/modules/sorties.md",
    "src/reconsigliere/modele_societe.html": "docs/modules/societe.md",
    "installer.ps1": "docs/modules/windows/installer.md",
    "windows/desinstaller.ps1": "docs/modules/windows/installer.md",
}


@dataclass
class Module:
    nom: str
    source: Path
    page: Path
    imports: set[str] = field(default_factory=set)
    externes: set[str] = field(default_factory=set)
    publics: list[tuple[str, str]] = field(default_factory=list)
    lignes: int = 0


def _sources(racine: Path) -> dict[str, Path]:
    res: dict[str, Path] = {}
    paquet = racine / PAQUET
    for f in sorted(paquet.rglob("*.py")):
        if f.name == "__init__.py" or "__pycache__" in f.parts:
            continue
        res[".".join(f.relative_to(paquet).with_suffix("").parts)] = f
    for rel, nom in AUTRES_MODULES.items():
        if (racine / rel).exists():
            res[nom] = racine / rel
    return res


def _page(racine: Path, nom: str) -> Path:
    return racine / DOSSIER_PAGES / (nom.replace(".", "/") + ".md")


def _analyser(m: Module, connus: set[str]) -> None:
    texte = m.source.read_text(encoding="utf-8")
    m.lignes = len(texte.splitlines())
    arbre = ast.parse(texte)
    paquet = m.nom.split(".")[:-1]
    for n in ast.walk(arbre):
        if isinstance(n, ast.ImportFrom) and n.level:
            base = paquet[: len(paquet) - (n.level - 1)] if n.level > 1 else list(paquet)
            cible = base + (n.module.split(".") if n.module else [])
            if ".".join(cible) in connus:
                m.imports.add(".".join(cible))
            for alias in n.names:
                nom = ".".join(cible + [alias.name])
                if nom in connus:
                    m.imports.add(nom)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            noms = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for nom in noms:
                haut = nom.split(".")[0]
                if haut == "reconsigliere":
                    interne = nom.split(".", 1)[1] if "." in nom else ""
                    if interne in connus:
                        m.imports.add(interne)
                elif haut and haut not in sys.stdlib_module_names:
                    m.externes.add(haut)
    m.imports.discard(m.nom)
    for n in arbre.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
            doc = (ast.get_docstring(n) or "").strip().splitlines()
            m.publics.append((n.name, doc[0] if doc else ""))


def modules(racine: Path) -> dict[str, Module]:
    racine = Path(racine)
    sources = _sources(racine)
    tous = {nom: Module(nom, src, _page(racine, nom)) for nom, src in sources.items()}
    for m in tous.values():
        _analyser(m, set(tous))
    return tous


def _lien(depuis: Module, vers: Module) -> str:
    rel = Path(os.path.relpath(vers.page, depuis.page.parent)).as_posix()
    return f"[{vers.nom}]({rel})"


def bloc(m: Module, tous: dict[str, Module]) -> str:
    racine = m.page.parents[len(m.nom.split(".")) + 1]
    utilise_par = sorted(n for n, autre in tous.items() if m.nom in autre.imports)
    lignes = [
        DEBUT,
        "_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._",
        "",
        f"- **Fichier :** `{m.source.relative_to(racine).as_posix()}` ({m.lignes} lignes)",
        "- **Dépend de :** " + (", ".join(_lien(m, tous[n]) for n in sorted(m.imports))
                                or "aucun autre module du programme"),
        "- **Utilisé par :** " + (", ".join(_lien(m, tous[n]) for n in utilise_par)
                                  or "aucun module (point d'entrée)"),
        "- **Bibliothèques externes :** " + (", ".join(sorted(m.externes)) or "aucune"),
        "",
        "Fonctions et classes publiques :",
        "",
    ]
    lignes += [f"- `{nom}` : {doc}" if doc else f"- `{nom}`" for nom, doc in m.publics] or ["- aucune"]
    lignes.append(FIN)
    return "\n".join(lignes)


def _id(nom: str) -> str:
    return "m_" + nom.replace(".", "__")


def carte(tous: dict[str, Module]) -> str:
    groupes: dict[str, list[str]] = {}
    for nom in sorted(tous):
        groupes.setdefault(nom.rsplit(".", 1)[0] if "." in nom else "", []).append(nom)
    lignes = [
        "# Carte des modules",
        "",
        "_Page générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._",
        "",
        "Une flèche A → B veut dire « A utilise B » : changer B peut changer le comportement de A.",
        "",
        "```mermaid",
        "flowchart LR",
    ]
    for groupe, noms in groupes.items():
        if groupe:
            lignes.append(f"  subgraph {groupe}")
        lignes += [f'  {_id(n)}["{n.rsplit(".", 1)[-1]}"]' for n in noms]
        if groupe:
            lignes.append("  end")
    for nom in sorted(tous):
        lignes += [f"  {_id(nom)} --> {_id(d)}" for d in sorted(tous[nom].imports)]
    lignes += ["```", "", "| Module | Fichier | Lignes | Utilisé par |", "|---|---|---|---|"]
    for nom in sorted(tous):
        m = tous[nom]
        racine = m.page.parents[len(nom.split(".")) + 1]
        page = m.page.relative_to(racine / "docs").as_posix()
        par = ", ".join(sorted(n for n, a in tous.items() if nom in a.imports)) or "—"
        lignes.append(f"| [{nom}]({page}) | `{m.source.relative_to(racine).as_posix()}` | {m.lignes} | {par} |")
    return "\n".join(lignes) + "\n"


def _lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8").replace("\r\n", "\n")


def _avec_bloc(texte: str, nouveau: str) -> str:
    if DEBUT in texte and FIN in texte:
        avant, reste = texte.split(DEBUT, 1)
        return avant + nouveau + reste.split(FIN, 1)[1]
    return texte.rstrip("\n") + "\n\n## Dépendances (automatique)\n\n" + nouveau + "\n"


def _modele(m: Module) -> str:
    rubriques = "".join(f"{r}\n\n{A_COMPLETER}\n\n" for r in RUBRIQUES)
    return f"# {m.nom}\n\n{rubriques}"


def regenerer(racine: Path) -> list[Path]:
    racine = Path(racine)
    tous = modules(racine)
    ecrits = []
    for m in tous.values():
        ancien = _lire(m.page) if m.page.exists() else None
        nouveau = _avec_bloc(ancien if ancien is not None else _modele(m), bloc(m, tous))
        if nouveau != ancien:
            m.page.parent.mkdir(parents=True, exist_ok=True)
            m.page.write_text(nouveau, encoding="utf-8", newline="\n")
            ecrits.append(m.page)
    chemin = racine / CARTE
    texte = carte(tous)
    if not chemin.exists() or _lire(chemin) != texte:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8", newline="\n")
        ecrits.append(chemin)
    return ecrits


def _verifier_rubriques(nom: str, texte: str) -> list[str]:
    problemes = [f"{nom} : rubrique « {r} » absente" for r in RUBRIQUES if r not in texte.splitlines()]
    if A_COMPLETER in texte:
        problemes.append(f"{nom} : rubriques à compléter")
    return problemes


def verifier(racine: Path) -> list[str]:
    racine = Path(racine)
    tous = modules(racine)
    problemes = []
    for m in tous.values():
        rel = m.page.relative_to(racine).as_posix()
        if not m.page.exists():
            problemes.append(f"{rel} manque (python outils/docs.py la crée, puis complète-la)")
            continue
        texte = _lire(m.page)
        problemes += _verifier_rubriques(rel, texte)
        if _avec_bloc(texte, bloc(m, tous)) != texte:
            problemes.append(f"{rel} : partie générée pas à jour (lance python outils/docs.py)")
    for source, page in sorted(ASSOCIES.items()):
        if (racine / source).exists():
            if not (racine / page).exists():
                problemes.append(f"{page} manque (documente {source})")
            else:
                problemes += _verifier_rubriques(page, _lire(racine / page))
    if not (racine / CARTE).exists() or _lire(racine / CARTE) != carte(tous):
        problemes.append(f"{CARTE.as_posix()} pas à jour (lance python outils/docs.py)")
    return sorted(set(problemes))


def page_de(rel: str) -> str | None:
    """Page qui documente un fichier du dépôt (chemin relatif), ou None s'il n'est pas surveillé."""
    if rel in ASSOCIES:
        return ASSOCIES[rel]
    if rel in AUTRES_MODULES:
        return (DOSSIER_PAGES / (AUTRES_MODULES[rel].replace(".", "/") + ".md")).as_posix()
    chemin = Path(rel)
    if chemin.suffix == ".py" and chemin.name != "__init__.py" and chemin.is_relative_to(PAQUET):
        return (DOSSIER_PAGES / chemin.relative_to(PAQUET).with_suffix(".md")).as_posix()
    return None


def _git(racine: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=racine, capture_output=True, text=True)
    if r.returncode:
        raise ValueError(r.stderr.strip() or f"git {' '.join(args)} a échoué")
    return r.stdout


def pages_oubliees(racine: Path, ref: str) -> list[str]:
    """Fichiers surveillés modifiés depuis ref (base commune) dont la page n'a pas changé."""
    racine = Path(racine)
    _git(racine, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    base = _git(racine, "merge-base", ref, "HEAD").strip()
    changes = set(_git(racine, "diff", "--name-only", base, "--").split())
    presents = set(_git(racine, "diff", "--name-only", "--diff-filter=d", base, "--").split())
    oublis = []
    for rel in sorted(presents):
        page = page_de(rel)
        if page and page not in changes:
            oublis.append(f"{rel} → {page}")
    return oublis


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python outils/docs.py", description=__doc__.splitlines()[0])
    p.add_argument("--racine", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--verifier", action="store_true", help="vérifie sans rien écrire")
    p.add_argument("--depuis", metavar="REF", help="exige la page de chaque module modifié depuis REF")
    args = p.parse_args(argv)
    code = 0
    if args.depuis:
        try:
            oublis = pages_oubliees(args.racine, args.depuis)
        except ValueError as e:
            print(f"Référence {args.depuis} introuvable : {e}")
            return 2
        for o in oublis:
            print(f"Module modifié sans sa page : {o}")
        if oublis:
            print("Mets à jour ces pages (rôle, entrées, sorties, ce qui casse) dans la même modification.")
            code = 1
    if args.verifier:
        for prob in verifier(args.racine):
            print(prob)
            code = 1
    if not args.depuis and not args.verifier:
        for f in regenerer(args.racine):
            print(f"mis à jour : {f.relative_to(args.racine).as_posix()}")
    return code


if __name__ == "__main__":
    sys.exit(main())
