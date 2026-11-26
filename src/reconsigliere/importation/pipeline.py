"""Pipeline d'import : document → pages → classement → continuité → (IA) → extraction → sorties."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from .. import config
from ..outils import normaliser
from . import classement, continuite, extracteurs, ia, sorties
from .pages import EXTENSIONS, Ocr, Page, lire_pages

_AUTO = object()
Choisir = Callable[[Page, "str | None"], "str | None"]

RE_ANNEE_EXPLICITE = re.compile(r"(?:exercice|au|per|du \d{1,2}[./]\d{1,2}[./]\d{4} au \d{1,2}[./]\d{1,2}[./])\s*"
                                r"(?:\d{1,2}[./]\d{1,2}[./])?((?:19|20)\d{2})\b")
RE_ANNEE = re.compile(r"\b\d{1,2}[./]\d{1,2}[./]((?:19|20)\d{2})\b|\b((?:19|20)\d{2})-\d{2}-\d{2}\b")
RE_SOCIETE = re.compile(r"^[A-ZÀ-Ü0-9].{1,60}\b(SA|S\.A\.|Sàrl|SARL|AG|GmbH|Ltd|SAS|Inc\.?)$")


def detecter_exercice(pages: list[Page]) -> int:
    texte = normaliser("\n".join(p.texte for p in pages))
    explicites = Counter(int(a) for a in RE_ANNEE_EXPLICITE.findall(texte))
    if explicites:
        return explicites.most_common(1)[0][0]
    annees = Counter(int(a or b) for a, b in RE_ANNEE.findall(texte))
    return annees.most_common(1)[0][0] if annees else date.today().year


def detecter_societe(pages: list[Page]) -> str:
    for p in pages[:3]:
        for l in classement.lignes(p.texte)[:6]:
            if RE_SOCIETE.match(l):
                return l
    return ""


def _chf(x: float) -> str:
    return f"{x:,.2f}".replace(",", "'")


def _controles(tables: dict[str, list[dict]], typees, illisibles: list[int]) -> list[dict]:
    res = []
    gl = tables["grandlivre"]
    if gl:
        d = round(sum(l["debit"] or 0 for l in gl), 2)
        c = round(sum(l["credit"] or 0 for l in gl), 2)
        res.append({"controle": "Grand livre équilibré", "resultat": "ok" if abs(d - c) < 0.01 else "ecart",
                    "detail": f"débits {_chf(d)}, crédits {_chf(c)}, écart {_chf(d - c)}"})
        sans_compte = sum(1 for l in gl if not l["compte"])
        if sans_compte:
            res.append({"controle": "Grand livre : lignes sans compte", "resultat": "ecart",
                        "detail": f"{sans_compte} ligne(s)"})
    totaux = {}
    for l in tables["bilan"]:
        n = normaliser(l["libelle"])
        if n.startswith("total"):
            if re.search(r"\bactifs?\b", n) and "circulant" not in n and "immobilis" not in n:
                totaux["actif"] = l["montant"]
            elif re.search(r"\bpassifs?\b", n):
                totaux["passif"] = l["montant"]
    if len(totaux) == 2:
        ok = abs(totaux["actif"] - totaux["passif"]) < 0.01
        res.append({"controle": "Bilan : actifs = passifs", "resultat": "ok" if ok else "ecart",
                    "detail": f"actifs {_chf(totaux['actif'])}, passifs {_chf(totaux['passif'])}"})
    if illisibles:
        res.append({"controle": "Pages illisibles", "resultat": "ecart",
                    "detail": "pages " + ", ".join(map(str, illisibles)) + " : installer Tesseract OCR ou fournir un PDF texte"})
    a_verifier = [p.numero for p, _, m in typees if m == "a_verifier"]
    if a_verifier:
        res.append({"controle": "Pages à vérifier", "resultat": "ecart",
                    "detail": "pages " + ", ".join(map(str, a_verifier)) + " classées « autre » faute de règle ou d'IA"})
    return res


def importer(chemin: Path, racine: Path | None = None, cle=_AUTO, modele_id: str | None = None,
             choisir: Choisir | None = None, ocr: Ocr | None = None, envoyer: ia.Envoyer | None = None,
             log: Callable[[str], None] = print) -> dict:
    chemin = Path(chemin)
    racine = Path(racine or config.RACINE)
    cle = ia.cle_api() if cle is _AUTO else cle
    modele_id = modele_id or ia.modele()

    log(f"Import de {chemin.name}")
    pages = lire_pages(chemin, ocr)
    log(f"    {len(pages)} page(s) lue(s)")
    typees = continuite.regrouper(pages, [classement.classer(p) for p in pages])

    appels, tokens, illisibles = 0, {"entree": 0, "sortie": 0}, []
    for i, (page, type_, methode) in enumerate(typees):
        if methode != "indecis":
            continue
        if not page.lisible:
            illisibles.append(page.numero)
            typees[i] = (page, "autre", "illisible")
            continue
        contexte = next((t for _, t, _ in reversed(typees[:i]) if t), "")
        trouve, methode = None, "a_verifier"
        if cle:
            trouve, usage = ia.classer_par_ia(page.texte, cle, modele_id, contexte, envoyer=envoyer)
            appels += 1
            tokens = {k: tokens[k] + usage[k] for k in tokens}
            methode = "ia" if trouve else methode
        if not trouve and choisir:
            trouve = choisir(page, contexte or None)
            methode = "manuel" if trouve else methode
        typees[i] = (page, trouve or "autre", methode)

    exercice = detecter_exercice(pages)
    sections = continuite.en_sections(typees)
    tables = {k: [] for k in extracteurs.CLES}
    for s in sections:
        for k, lignes in extracteurs.extraire(s, exercice, chemin.name).items():
            tables[k] += lignes
    for l in tables["grandlivre"]:  # l'exercice d'une écriture suit sa date (exercice civil)
        if l["date"]:
            l["exercice"] = int(l["date"][:4])

    scores = {p.numero: s for p, (_, s, _) in zip(pages, [classement.classer(p) for p in pages])}
    tables["pages"] = [{"page": p.numero, "type": t, "methode": m, "score": scores.get(p.numero),
                        "source": f"{chemin.name} p.{p.numero}"} for p, t, m in typees]
    tables["controles"] = _controles(tables, typees, illisibles)
    meta = {"societe": detecter_societe(pages), "date_debut": f"{exercice}-01-01",
            "date_fin": f"{exercice}-12-31", "devise": config.DEVISE, "fichier_source": chemin.name,
            "empreinte": hashlib.sha1(chemin.read_bytes()).hexdigest(),
            "importe_le": datetime.now().isoformat(timespec="seconds"),
            "modele_ia": modele_id if appels else "", "appels_ia": appels,
            "tokens_entree": tokens["entree"], "tokens_sortie": tokens["sortie"]}
    tables["meta"] = [{"cle": k, "valeur": v} for k, v in meta.items()]

    xlsx = sorties.ecrire_excel(tables, racine, exercice, chemin.stem)
    page_html = sorties.ecrire_html(tables, meta, racine, chemin.stem)
    for s in sections:
        log(f"    {classement.LIBELLES.get(s.type, s.type)} : pages {s.pages[0].numero}–{s.pages[-1].numero}")
    if appels:
        log(f"    IA : {appels} page(s), {tokens['entree']} tokens en entrée, {tokens['sortie']} en sortie")
    for c in tables["controles"]:
        log(f"    {'✓' if c['resultat'] == 'ok' else '!'} {c['controle']} : {c['detail']}")
    log(f"    → {xlsx}")
    return {"exercice": exercice, "excel": xlsx, "html": page_html, "sections": sections,
            "controles": tables["controles"], "appels_ia": appels, "tokens": tokens, "empreinte": meta["empreinte"]}


# ------------------------------------------------------------------ dossier entrees/07_documents

def _index(racine: Path) -> Path:
    return Path(racine) / "sorties" / "imports" / "index.json"


def importer_dossier(racine: Path | None = None, forcer: bool = False, **options) -> list[dict]:
    """Importe chaque document de entrees/07_documents qui ne l'a pas encore été (même contenu)."""
    racine = Path(racine or config.RACINE)
    dossier = racine / "entrees" / "07_documents"
    try:
        deja = json.loads(_index(racine).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        deja = {}
    resultats = []
    for chemin in sorted(p for p in dossier.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS
                         and not p.name.startswith("~$")):
        empreinte = hashlib.sha1(chemin.read_bytes()).hexdigest()
        if not forcer and empreinte in deja and Path(deja[empreinte]).exists():
            continue
        try:
            res = importer(chemin, racine, **options)
        except Exception as erreur:  # un document abîmé n'arrête pas les autres
            options.get("log", print)(f"    ! {chemin.name} : {erreur}")
            continue
        deja[empreinte] = str(res["excel"])
        resultats.append(res)
    _index(racine).parent.mkdir(parents=True, exist_ok=True)
    _index(racine).write_text(json.dumps(deja, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultats
