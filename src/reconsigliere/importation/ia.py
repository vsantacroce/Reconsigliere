"""IA en secours, pour les seules pages que les règles locales n'ont pas su classer.

Chaque appel envoie un extrait court (EXTRAIT_MAX caractères) et attend un seul mot.
Sans clé API, rien n'est envoyé : la page est laissée au choix manuel.
"""

from __future__ import annotations

import os
from typing import Callable

from .. import installation
from ..outils import normaliser
from .classement import TYPES

MODELES = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
MODELE_DEFAUT = "haiku"
# Prix en dollars par million de tokens (entrée, sortie), tarif public de l'API Anthropic.
PRIX = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.00, 10.00)}
# Réflexion coupée : inutile pour répondre par un mot, et elle coûterait des tokens de sortie.
REFLEXION = {"claude-haiku-5-5": {"type": "disabled"}, "claude-sonnet-5-5": {"type": "between_tools"}}
EXTRAIT_MAX = 2000

CONSIGNE = ("Tu classes une page de document comptable suisse. Réponds par un seul mot parmi : "
            "bilan, compte_resultat, grand_livre, plan_comptable, annexe, autre. "
            "bilan = actifs et passifs ; compte_resultat = produits et charges ; "
            "grand_livre = écritures datées par compte avec débit/crédit ; "
            "plan_comptable = liste de comptes sans montants ; annexe = texte explicatif des comptes annuels.")

SYNONYMES = {
    "compte de resultat": "compte_resultat", "pnl": "compte_resultat", "p&l": "compte_resultat",
    "grand livre": "grand_livre", "grand-livre": "grand_livre", "plan comptable": "plan_comptable",
    "balance sheet": "bilan", "bs": "bilan",
}

Envoyer = Callable[[dict], dict]


def cle_api() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY") or installation.lire_reglages().get("cle_api_anthropic") or None


def modele() -> str:
    choix = (os.environ.get("RECONSIGLIERE_MODELE") or installation.lire_reglages().get("modele_ia")
             or MODELE_DEFAUT).strip().lower()
    return choix if choix.startswith("claude-") else MODELES.get(choix, MODELES[MODELE_DEFAUT])


def extrait(texte: str) -> str:
    lignes = [" ".join(l.split()) for l in texte.splitlines() if l.strip()]
    return "\n".join(lignes)[:EXTRAIT_MAX]


def requete(texte: str, modele_id: str, contexte: str = "") -> dict:
    contenu = (f"Section précédente : {contexte}\n" if contexte else "") + "Page :\n" + extrait(texte)
    return {
        "model": modele_id,
        "max_tokens": 64,
        "system": CONSIGNE,
        "thinking": REFLEXION.get(modele_id, {"type": "adaptive"}),
        "output_config": {"effort": "low"},
        "messages": [{"role": "user", "content": contenu}],
    }


def envoyeur_sdk(cle: str) -> Envoyer:
    import anthropic  # importé seulement si l'IA est utilisée

    client = anthropic.Anthropic(api_key=cle, timeout=60.0, max_retries=2)

    def envoyer(req: dict) -> dict:
        rep = client.messages.create(**req)
        texte = "".join(b.text for b in rep.content if b.type == "text")
        return {"texte": texte, "entree": rep.usage.input_tokens, "sortie": rep.usage.output_tokens,
                "stop": rep.stop_reason}
    return envoyer


def interpreter(reponse: str) -> str:
    n = normaliser(reponse).strip(" .:!\"'`*")
    if n in TYPES:
        return n
    for mot, type_ in SYNONYMES.items():
        if n == mot or n.startswith(mot):
            return type_
    for type_ in TYPES:
        if type_ in n.replace(" ", "_"):
            return type_
    return "autre"


def classer_par_ia(texte: str, cle: str, modele_id: str, contexte: str = "",
                   envoyer: Envoyer | None = None) -> tuple[str | None, dict]:
    """(type, {entree, sortie}) ; type None si l'appel échoue ou est refusé."""
    try:
        envoyer = envoyer or envoyeur_sdk(cle)
        rep = envoyer(requete(texte, modele_id, contexte))
    except Exception:
        return None, {"entree": 0, "sortie": 0}
    usage = {"entree": int(rep.get("entree") or 0), "sortie": int(rep.get("sortie") or 0)}
    if rep.get("stop") == "refusal":
        return None, usage
    return interpreter(rep.get("texte", "")), usage


def cout_usd(modele_id: str, entree: int, sortie: int) -> float:
    pe, ps = PRIX.get(modele_id, (0.0, 0.0))
    return (entree * pe + sortie * ps) / 1_000_000
