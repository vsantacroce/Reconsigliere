# Pipeline d'import de documents — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (exécution native retenue). Étapes en cases à cocher.

**Goal:** importer un document quelconque, classer ses pages, regrouper les sections, extraire des tableaux normalisés et écrire un classeur + une page HTML.
**Architecture:** paquet `src/reconsigliere/importation/` en modules à responsabilité unique ; règles locales d'abord, IA (Haiku) en secours sur extraits courts ; branchement CLI et fenêtre.
**Tech Stack:** Python 3.12, pypdf, pandas, openpyxl, Tesseract/pdftoppm optionnels, API Messages Anthropic via `urllib` (aucune dépendance nouvelle).
**Spec:** `docs/superpowers/specs/2026-11-26-pipeline-import-design.md`

## Global Constraints
- Aucune dépendance Python nouvelle ; tests `python -m unittest discover -s tests`, données fictives uniquement.
- Types : `bilan`, `compte_resultat`, `grand_livre`, `plan_comptable`, `annexe`, `autre`.
- Modèle IA réglable : `haiku` → `claude-haiku-5-5` (défaut), `sonnet` → `claude-sonnet-5-5` ; réglage `modele_ia` ou variable `RECONSIGLIERE_MODELE`. Extrait ≤ 2000 caractères, `max_tokens` 5.
- Sorties : `entrees/06_societe/imports/AAAA/<nom>.xlsx`, `sorties/imports/<nom>.html` ; jamais `exercices/`.
- Colonnes et règles de format : section « Format de sortie » de la spec.

## Review Focus
- PDF scanné sans Tesseract : pages marquées illisibles, import qui continue (test dans Task 1).
- Grand livre de plusieurs pages sans titre après la première : rattaché par continuité (Task 3).
- Montants suisses « 1'234.50 », négatifs « -89.90 » et colonnes débit/crédit vides (Task 4).
- Page indécise sans clé API : type `autre`, méthode `a_verifier`, aucun appel réseau (Task 5).
- Comptes à zéros initiaux ou sous-comptes « 0100 », « 227101 » gardés en texte (Task 4, Task 6).

---

### Task 1: Pages (`importation/pages.py`)
**Produces:** `@dataclass Page(numero:int, texte:str, tableau:pd.DataFrame|None=None, lisible:bool=True)` ; `lire_pages(chemin:Path, ocr=None) -> list[Page]` (ocr : callable(Path)->str injectable).
- [ ] Tests : PDF généré à 2 pages → 2 pages avec texte ; xlsx à 2 feuilles → 2 pages avec `tableau` ; CSV → 1 page ; page PDF vide sans OCR → `lisible=False`.
- [ ] Implémenter (pypdf par page ; OCR via pdftoppm+tesseract si page < 40 car.) ; tests verts ; commit.

### Task 2: Classement (`importation/classement.py`)
**Produces:** `TYPES` ; `classer(page:Page) -> tuple[str|None, float, bool]` = (type ou None, score, titre_fort).
- [ ] Tests : textes fictifs de bilan, compte de résultat, grand livre, plan comptable, annexe → bon type et `titre_fort=True` ; page de chiffres sans mots-clés → None ; DataFrame avec en-têtes Date/Compte/Débit/Crédit → grand_livre.
- [ ] Implémenter ; commit.

### Task 3: Continuité (`importation/continuite.py`)
**Produces:** `@dataclass Section(type:str, pages:list[Page], methode:str)` ; `regrouper(pages, classements) -> list[tuple[Page,str|None,str]]` (type, méthode `regles|continuite|indecis`) et `en_sections(pages_typees) -> list[Section]`.
- [ ] Tests : [GL titre, GL suite « Report », GL suite sans signe mais lignes date+montant] → une section grand_livre ; [Bilan, Compte de résultat] → deux sections ; page indécise sans signe → indecis.
- [ ] Implémenter ; commit.

### Task 4: Extracteurs (`importation/extracteurs.py`)
**Produces:** `extraire(section:Section, exercice:int, source:str) -> dict[str, list[dict]]` clés `plancomptable|grandlivre|bilan|compteresultat|annexe`.
- [ ] Tests : plan comptable texte et Excel (code « 0100 » texte) ; grand livre texte (« 01.02.2024 1020 Banque BILL/2024/02/0001 Fournisseur SA Facture 1'200.00 ») et Excel débit/crédit ; bilan avec deux colonnes de montants et niveaux ; signe négatif gardé.
- [ ] Implémenter ; commit.

### Task 5: IA en secours (`importation/ia.py`)
**Produces:** `cle_api() -> str|None` ; `modele() -> str` ; `classer_par_ia(texte:str, cle:str, modele:str, envoyer=None) -> tuple[str|None, dict]` (type, usage tokens ; envoyer injectable) ; `banc.py` : `comparer(modeles, cle, envoyer=None) -> list[dict]` sur 12 pages ambiguës fictives (justesse, tokens entrée/sortie par modèle), lancé par `python -m reconsigliere banc-ia`.
- [ ] Tests : extrait tronqué à 2000 car. dans la requête, modèle `claude-haiku-5-5` ; réponse « Grand livre » → grand_livre ; réponse inconnue → autre ; erreur réseau → None ; `banc.comparer` avec envoyer simulé → justesse 100 % et tokens additionnés.
- [ ] Implémenter (urllib, en-têtes `x-api-key`, `anthropic-version: 2023-06-01`) ; commit.

### Task 6: Pipeline, contrôles et sorties (`importation/pipeline.py`, `importation/sorties.py`)
**Produces:** `importer(chemin:Path, racine:Path, choisir=None, ia=True) -> dict` (choisir : callable(page)->str pour le choix manuel) ; écrit xlsx + html ; retourne chemins, sections, contrôles, nb pages IA.
- [ ] Tests : PDF fictif « bilan + compte de résultat + grand livre 2 pages » → xlsx dans `entrees/06_societe/imports/2024/` avec onglets attendus, `compte` en texte, débit/crédit non signés, `pages` complet, contrôle « grand livre équilibré » OK ; aucun appel IA.
- [ ] Implémenter ; commit.

### Task 7: Branchement CLI et fenêtre, documentation
- [ ] `python -m reconsigliere importer FICHIER... [--sans-ia]` ; bouton « Importer des documents… » dans la fenêtre (choix manuel par liste pour les pages indécises sans clé) ; dossier `entrees/07_documents` créé à l'installation.
- [ ] README, CHANGEMENTS 0.5.0 ; suite complète verte ; commit, push, PR.
