"""Ce que le programme apprend de tes corrections de compte.

Tout est recalculé à chaque réconciliation à partir de la colonne « compte » de la feuille transactions de
mes_corrections.xlsx : rien n'est gardé ailleurs. Supprimer une correction retire son effet au lancement suivant.
Seules tes décisions (règle annulée) sont gardées, dans la feuille regles_apprises du même fichier.

Pour chaque partenaire :
1. moins de config.SEUIL_REGLE corrections identiques : « en observation », rien n'est appliqué ;
2. un seul compte (au plus une correction isolée contraire) : règle « active », appliquée aux autres transactions ;
3. plusieurs comptes ayant chacun au moins deux corrections : recherche de ce qui les sépare, dans l'ordre
   période (changement de compte à une date), mot du libellé, seuil de montant (deux comptes seulement).
   Critère trouvé : règle « conditionnelle » (ou « active » depuis la date du changement). Sinon « suspendue » et alerte.
Alertes : référentiel de l'exercice qui range le partenaire sur un autre compte (avec les autres partenaires rangés
sur ce même compte, même erreur possible), compte absent du plan comptable, correction contraire, analyse qui se trompait.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

from . import config, exercices
from .outils import code_compte, normaliser
from .rapprochement import _mots_significatifs

ACTIVE = "active"
CONDITIONNELLE = "conditionnelle"
EN_OBSERVATION = "en observation"
SUSPENDUE = "suspendue"
ANNULEE = "annulée"
ETATS_APPLIQUES = {ACTIVE, CONDITIONNELLE}

ORIGINE_CORRECTION = "ta correction"
ORIGINE_APPRIS = "appris"
ORIGINE_REFERENTIEL = "référentiel"

ATTENTION = "attention"
INFO = "info"

MAX_PARTENAIRES_LISTES = 10


@dataclass
class Observation:
    """Une transaction dont tu as corrigé le compte."""
    id: str
    date: date
    montant: float
    libelle: str
    partenaire: str
    compte: str
    compte_reference: str


@dataclass
class Branche:
    """« compte si condition ». nature : toujours, depuis (date), mot (du libellé), montant_inf, montant_sup."""
    compte: str
    nature: str = "toujours"
    valeur: object = None
    appuis: int = 0

    def convient(self, t: dict) -> bool:
        if self.nature == "depuis":
            return t["date"] >= self.valeur
        if self.nature == "mot":
            return self.valeur in _mots_significatifs(t.get("libelle", ""))
        if self.nature == "montant_inf":
            return abs(t["montant"]) < self.valeur
        if self.nature == "montant_sup":
            return abs(t["montant"]) >= self.valeur
        return True

    def texte(self) -> str:
        if self.nature == "depuis":
            return f"depuis le {self.valeur.strftime('%d.%m.%Y')}"
        if self.nature == "mot":
            return f"si le libellé contient « {self.valeur} »"
        if self.nature == "montant_inf":
            return f"si le montant < {self.valeur:g} {config.DEVISE}"
        if self.nature == "montant_sup":
            return f"si le montant ≥ {self.valeur:g} {config.DEVISE}"
        return "sinon" if self.appuis < 0 else "toujours"


@dataclass
class Regle:
    partenaire: str
    cle: str
    branches: list[Branche]
    etat: str
    corrections: int
    fiabilite: str
    compte_reference: str = ""
    explication: str = ""

    @property
    def compte(self) -> str:
        return " / ".join(dict.fromkeys(b.compte for b in self.branches))

    @property
    def condition(self) -> str:
        if all(b.nature == "toujours" for b in self.branches):
            return ""
        return " ; ".join(f"{b.compte} {b.texte()}" for b in self.branches)

    @property
    def reportable(self) -> bool:
        """Une règle à un seul compte peut être reportée dans le référentiel de l'exercice ouvert."""
        return self.etat == ACTIVE and len({b.compte for b in self.branches}) == 1

    def compte_pour(self, t: dict) -> str | None:
        if self.etat not in ETATS_APPLIQUES:
            return None
        for b in self.branches:
            if b.convient(t):
                return b.compte
        return None


@dataclass
class Alerte:
    niveau: str
    partenaire: str
    message: str


@dataclass
class Analyse:
    regles: list[Regle] = field(default_factory=list)
    alertes: list[Alerte] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    resume: dict = field(default_factory=dict)

    def regle_de(self, partenaire: str) -> Regle | None:
        cle = normaliser(partenaire)
        return next((r for r in self.regles if r.cle == cle), None)


# ---------------------------------------------------------------- observations

def observations(transactions: list[dict], corrections: dict) -> list[Observation]:
    """Les transactions présentes dans les relevés dont la feuille transactions donne un compte."""
    corr = corrections.get("transactions", {})
    resultat = []
    for t in transactions:
        compte = code_compte(corr.get(t["id"], {}).get("compte", ""))
        partenaire = (t.get("partenaire_trouve") or "").strip()
        if not compte or not partenaire:
            continue
        resultat.append(Observation(t["id"], t["date"], t["montant"], t.get("libelle", ""), partenaire, compte,
                                    code_compte(t.get("compte_reference", ""))))
    return sorted(resultat, key=lambda o: (o.date, o.id))


# ---------------------------------------------------------------- recherche d'un critère

def _critere_periode(obs: list[Observation]) -> list[Branche] | None:
    """Toutes les corrections vers le dernier compte sont postérieures à toutes les autres."""
    dernier = obs[-1].compte
    premier_indice = next(i for i, o in enumerate(obs) if o.compte == dernier)
    if any(o.compte != dernier for o in obs[premier_indice:]):
        return None
    appuis = len(obs) - premier_indice
    return [Branche(dernier, "depuis", obs[premier_indice].date, appuis)]


def _critere_mot(obs: list[Observation], comptes: list[str]) -> list[Branche] | None:
    mots = {c: [set(_mots_significatifs(o.libelle)) for o in obs if o.compte == c] for c in comptes}
    distinctifs = {}
    for c in comptes:
        communs = set.intersection(*mots[c])
        ailleurs = set().union(*(m for autre in comptes if autre != c for m in mots[autre]))
        propres = sorted(communs - ailleurs, key=lambda m: (-len(m), m))
        if propres:
            distinctifs[c] = propres[0]
    sans_mot = [c for c in comptes if c not in distinctifs]
    if len(sans_mot) > 1:
        return None
    n = Counter(o.compte for o in obs)
    branches = [Branche(c, "mot", distinctifs[c], n[c]) for c in comptes if c in distinctifs]
    if sans_mot:
        branches.append(Branche(sans_mot[0], "toujours", None, -1))
    return branches


def _critere_montant(obs: list[Observation], comptes: list[str]) -> list[Branche] | None:
    if len(comptes) != 2:
        return None
    montants = {c: [abs(o.montant) for o in obs if o.compte == c] for c in comptes}
    bas, haut = sorted(comptes, key=lambda c: max(montants[c]))
    if max(montants[bas]) >= min(montants[haut]):
        return None
    seuil = float(round((max(montants[bas]) + min(montants[haut])) / 2))
    return [Branche(bas, "montant_inf", seuil, len(montants[bas])),
            Branche(haut, "montant_sup", seuil, len(montants[haut]))]


# ---------------------------------------------------------------- analyse

def _par_partenaire(referentiel: dict | None) -> dict[str, dict]:
    if not referentiel:
        return {}
    return {normaliser(p.get("partenaire")): p for p in referentiel.get("Partenaires", []) if p.get("partenaire")}


def _plan(referentiel: dict | None) -> dict[str, str]:
    if not referentiel:
        return {}
    return {code_compte(p.get("code")): str(p.get("nom") or "").strip()
            for p in referentiel.get("PlanComptable", []) if code_compte(p.get("code"))}


def _regle_simple_a_existe(obs: list[Observation], seuil: int) -> bool:
    """Vrai si, à un moment, une règle à un seul compte a été active (donc mon analyse d'alors était fausse)."""
    n: Counter = Counter()
    for o in obs:
        n[o.compte] += 1
        premier = n.most_common(2)
        if premier[0][1] >= seuil and (len(premier) == 1 or premier[1][1] < 2):
            return True
    return False


def _regle_du_partenaire(obs: list[Observation], seuil: int, alertes: list[Alerte]) -> Regle:
    nom = obs[-1].partenaire
    n = Counter(o.compte for o in obs)
    total = len(obs)
    significatifs = [c for c, k in n.most_common() if k >= 2]
    majoritaire, k = n.most_common(1)[0]

    if len(significatifs) < 2:
        contraires = total - k
        if contraires:
            alertes.append(Alerte(INFO, nom, f"{nom} : {contraires} correction(s) contraire(s) à la règle {majoritaire} "
                                             f"(vers {', '.join(c for c in n if c != majoritaire)}). "
                                             "Si elles se répètent, j'en chercherai la raison."))
        etat = ACTIVE if k >= seuil else EN_OBSERVATION
        explication = (f"{k} correction(s) vers {majoritaire}" if etat == ACTIVE
                       else f"{k} correction(s) sur {seuil} nécessaires avant d'appliquer seul ce compte")
        return Regle(nom, normaliser(nom), [Branche(majoritaire, "toujours", None, k)], etat,
                     total, f"{k} corrections sur {total}", explication=explication)

    utiles = [o for o in obs if o.compte in significatifs]
    regle_simple_aurait_existe = _regle_simple_a_existe(obs, seuil)
    periode = _critere_periode(utiles)
    if periode:
        b = periode[0]
        anciens = ", ".join(c for c in significatifs if c != b.compte)
        etat = ACTIVE if b.appuis >= seuil else EN_OBSERVATION
        if any(n[c] >= seuil for c in significatifs if c != b.compte):
            alertes.append(Alerte(ATTENTION, nom, f"{nom} : mon analyse se trompait. Tu l'as rangé sur {anciens}, "
                                                  f"puis sur {b.compte} {b.texte()}. J'applique {b.compte} à partir de cette date."))
        return Regle(nom, normaliser(nom), periode, etat, total, f"{b.appuis} corrections sur {b.appuis} depuis cette date",
                     explication=f"changement de compte : {anciens} avant, {b.compte} {b.texte()}")

    for chercher in (_critere_mot, _critere_montant):
        branches = chercher(utiles, significatifs)
        if branches:
            regle = Regle(nom, normaliser(nom), branches, CONDITIONNELLE, total,
                          f"{len(utiles)} corrections sur {total} expliquées par le critère",
                          explication="plusieurs comptes de prédilection, séparés par un critère")
            debut = "mon analyse se trompait : " if regle_simple_aurait_existe else ""
            alertes.append(Alerte(ATTENTION, nom, f"{nom} : {debut}ce partenaire a plusieurs comptes. "
                                                  f"Critère trouvé : {regle.condition}."))
            return regle

    alertes.append(Alerte(ATTENTION, nom, f"{nom} : tes corrections vont vers {', '.join(significatifs)} et je ne trouve "
                                          "aucun critère qui les sépare (date, mot du libellé, montant). Critère introuvable : "
                                          "je n'applique plus rien seul pour ce partenaire, à trancher."))
    return Regle(nom, normaliser(nom), [Branche(c, "toujours", None, n[c]) for c in significatifs], SUSPENDUE, total,
                 f"{k} corrections sur {total} pour le compte le plus fréquent",
                 explication="plusieurs comptes sans critère trouvé")


def analyser(obs: list[Observation], annulees: set[tuple[str, str]] | None = None,
             referentiel: dict | None = None, seuil: int | None = None) -> Analyse:
    """Règles et alertes tirées des corrections. referentiel : {"exercice", "Partenaires", "PlanComptable"} ou None."""
    seuil = seuil or config.SEUIL_REGLE
    annulees = annulees or set()
    partenaires_ref = _par_partenaire(referentiel)
    plan = _plan(referentiel)
    exercice = (referentiel or {}).get("exercice", "")
    groupes: dict[str, list[Observation]] = defaultdict(list)
    for o in obs:
        groupes[normaliser(o.partenaire)].append(o)

    analyse = Analyse(observations=list(obs))
    for cle, liste in sorted(groupes.items()):
        alertes: list[Alerte] = []
        regle = _regle_du_partenaire(liste, seuil, alertes)
        ref = partenaires_ref.get(cle)
        regle.compte_reference = (code_compte(ref.get("compte")) if ref else "") or next(
            (c for c, _ in Counter(o.compte_reference for o in liste if o.compte_reference).most_common(1)), "")
        if (cle, regle.compte) in annulees:
            regle.etat = ANNULEE
            regle.explication = "annulée par toi (feuille regles_apprises de mes_corrections.xlsx)"
            alertes = [a for a in alertes if a.niveau == INFO]
        elif regle.etat == ACTIVE and regle.compte_reference and regle.compte_reference != regle.compte:
            message = (f"{regle.partenaire} : le référentiel {exercice or ''} le range sur {regle.compte_reference}, "
                       f"tes corrections disent {regle.compte}. Je l'applique ; reporte la règle dans l'exercice ouvert "
                       f"pour corriger le référentiel.").replace("  ", " ")
            memes = [p.get("partenaire") for k, p in partenaires_ref.items()
                     if k != cle and code_compte(p.get("compte")) == regle.compte_reference]
            if memes:
                deja = {normaliser(o.partenaire) for o in obs if o.compte == regle.compte
                        and o.compte_reference == regle.compte_reference}
                noms = [f"{m} (déjà corrigé une fois)" if normaliser(m) in deja else m
                        for m in sorted(memes)[:MAX_PARTENAIRES_LISTES]]
                plus = f" et {len(memes) - MAX_PARTENAIRES_LISTES} autre(s)" if len(memes) > MAX_PARTENAIRES_LISTES else ""
                message += (f" Même erreur possible : sont aussi rangés sur {regle.compte_reference} "
                            f"{', '.join(noms)}{plus}. À vérifier.")
            alertes.append(Alerte(ATTENTION, regle.partenaire, message))
        if plan:
            for c in dict.fromkeys(b.compte for b in regle.branches):
                if c not in plan:
                    alertes.append(Alerte(ATTENTION, regle.partenaire,
                                          f"{regle.partenaire} : le compte {c} est absent du plan comptable "
                                          f"{exercice}. Faute de frappe ou compte à créer ?".rstrip()))
        analyse.regles.append(regle)
        analyse.alertes.extend(alertes)

    etats = Counter(r.etat for r in analyse.regles)
    analyse.resume = {
        "corrections": len(obs),
        "partenaires": len(analyse.regles),
        "corrigees_par_rapport_au_referentiel": sum(1 for o in obs if o.compte_reference and o.compte != o.compte_reference),
        "actives": etats[ACTIVE],
        "conditionnelles": etats[CONDITIONNELLE],
        "en_observation": etats[EN_OBSERVATION],
        "suspendues": etats[SUSPENDUE],
        "annulees": etats[ANNULEE],
        "alertes": len(analyse.alertes),
        "appliquees": 0,
        "seuil": seuil,
    }
    return analyse


# ---------------------------------------------------------------- application aux transactions

def appliquer(transactions: list[dict], analyse: Analyse, corrections: dict, plan: dict[str, str] | None = None) -> int:
    """Compte final de chaque transaction : ta correction, sinon la règle apprise, sinon le référentiel.

    Remplit compte_propose, fiabilite_compte et origine_compte. Rend le nombre de transactions où une règle apprise
    a été appliquée.
    """
    plan = plan or {}
    corr = corrections.get("transactions", {})
    appliquees = 0
    for t in transactions:
        propre = code_compte(corr.get(t["id"], {}).get("compte", ""))
        regle = analyse.regle_de(t.get("partenaire_trouve") or "")
        compte = regle.compte_pour(t) if regle and not propre else None
        if propre:
            t["compte_propose"] = f"{propre} {plan.get(propre, '')}".strip()
            t["fiabilite_compte"] = "ta correction"
            t["origine_compte"] = ORIGINE_CORRECTION
        elif compte:
            t["compte_propose"] = f"{compte} {plan.get(compte, '')}".strip()
            details = [regle.fiabilite, "appris de tes corrections"]
            if regle.condition:
                details.append(regle.condition)
            t["fiabilite_compte"] = ", ".join(details)
            t["origine_compte"] = ORIGINE_APPRIS
            appliquees += 1
        else:
            t["origine_compte"] = ORIGINE_REFERENTIEL if t.get("compte_propose") else ""
    analyse.resume["appliquees"] = appliquees
    return appliquees


def referentiel_courant() -> dict | None:
    """Le référentiel du dernier exercice ouvert (sinon du dernier exercice), ou None s'il n'y en a pas."""
    try:
        annee = exercices.exercice_courant()
        if annee is None:
            return None
        listes = exercices.lire(annee)
    except Exception:  # noqa: BLE001 - l'apprentissage fonctionne aussi sans référentiel
        return None
    return {"exercice": annee, "Partenaires": listes["Partenaires"], "PlanComptable": listes["PlanComptable"]}


def executer(transactions: list[dict], corrections: dict) -> Analyse:
    """Appelé par la réconciliation, après exercices.proposer_comptes."""
    referentiel = referentiel_courant()
    analyse = analyser(observations(transactions, corrections), corrections.get("annulees", set()), referentiel)
    appliquer(transactions, analyse, corrections, _plan(referentiel))
    return analyse


def reporter(partenaire: str, compte: str, nb_corrections: int, annee: int | None = None) -> list[dict]:
    """Inscrit la règle dans le référentiel de l'exercice ouvert (changement daté et motivé)."""
    annee = annee or exercices.exercice_courant()
    if annee is None:
        raise ValueError("Aucun exercice construit : construis d'abord l'année dans l'onglet « Année comptable ».")
    listes = exercices.lire(annee)
    plan = _plan({"PlanComptable": listes["PlanComptable"]})
    existant = next((p for p in listes["Partenaires"] if normaliser(p.get("partenaire")) == normaliser(partenaire)), None)
    valeurs = {"compte": compte, "libelle_compte": plan.get(compte, "")}
    motif = f"appris de {nb_corrections} corrections dans mes_corrections.xlsx"
    if existant:
        return exercices.demander_changement(annee, "modification", "Partenaires", str(existant["partenaire"]),
                                             valeurs, motif)
    return exercices.demander_changement(annee, "ajout", "Partenaires", partenaire, valeurs, motif)


# ---------------------------------------------------------------- sortie lisible

COLONNES_REGLES = ["partenaire", "compte", "condition", "etat", "fiabilite", "corrections", "compte_reference",
                   "explication"]
COLONNES_ALERTES = ["niveau", "partenaire", "message"]
COLONNES_CORRECTIONS = ["date", "partenaire", "libelle", "montant", "compte_reference", "compte", "id_transaction"]


def fichier_sortie() -> Path:
    return config.DOSSIER_SORTIES / "apprentissage.xlsx"


def ecrire(analyse: Analyse) -> Path:
    """sorties/apprentissage.xlsx : resume, regles, alertes, corrections. Relu par l'onglet Apprentissage."""
    wb = openpyxl.Workbook()
    resume = wb.active
    resume.title = "resume"
    resume.append(["cle", "valeur"])
    resume.append(["calcule_le", datetime.now().strftime("%d.%m.%Y %H:%M")])
    for k, v in analyse.resume.items():
        resume.append([k, v])
    feuilles = {
        "regles": (COLONNES_REGLES, [[r.partenaire, r.compte, r.condition, r.etat, r.fiabilite, r.corrections,
                                      r.compte_reference, r.explication] for r in analyse.regles]),
        "alertes": (COLONNES_ALERTES, [[a.niveau, a.partenaire, a.message] for a in analyse.alertes]),
        "corrections": (COLONNES_CORRECTIONS, [[o.date.isoformat(), o.partenaire, o.libelle, o.montant,
                                                o.compte_reference, o.compte, o.id] for o in analyse.observations]),
    }
    for nom, (colonnes, lignes) in feuilles.items():
        ws = wb.create_sheet(nom)
        ws.append(colonnes)
        for l in lignes:
            ws.append(l)
    for ws in wb.worksheets:
        for c in ws[1]:
            c.font = Font(bold=True)
    chemin = fichier_sortie()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    wb.save(chemin)
    return chemin


def lire_sortie() -> dict | None:
    """Relit sorties/apprentissage.xlsx, ou None s'il n'existe pas encore."""
    chemin = fichier_sortie()
    if not chemin.exists():
        return None
    wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    resultat: dict = {"resume": {}, "regles": [], "alertes": [], "corrections": []}
    for nom in resultat:
        if nom not in wb.sheetnames:
            continue
        rangs = list(wb[nom].iter_rows(values_only=True))
        if not rangs:
            continue
        entete = [str(c) for c in rangs[0]]
        lignes = [dict(zip(entete, r)) for r in rangs[1:]]
        resultat[nom] = {l["cle"]: l["valeur"] for l in lignes} if nom == "resume" else lignes
    wb.close()
    resultat["calcule_le"] = resultat["resume"].pop("calcule_le", "")
    return resultat
