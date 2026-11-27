"""Onglet « Documents » : ce qui a été importé, type par type, avec sources, contrôles et tableau.

Les données viennent de importation.catalogue (les classeurs de entrees/06_societe/imports).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .importation import catalogue
from .importation.classement import LIBELLES

TOUS = "Tous"
ONGLETS_TYPES = ["plan_comptable", "bilan", "compte_resultat", "grand_livre", "annexe", "autre"]
TITRES = {**LIBELLES, "autre": "Autres pages"}
METHODES = {"regles": "règles", "continuite": "suite", "ia": "IA", "manuel": "manuel",
            "a_verifier": "à vérifier", "illisible": "illisible"}
COLONNES_TABLE = {
    "plan_comptable": [("code", "Code", 80), ("nom", "Nom", 260), ("type", "Type", 160), ("exercice", "Exercice", 70),
                       ("source", "Source", 180)],
    "grand_livre": [("date", "Date", 88), ("compte", "Compte", 64), ("libelle_compte", "Nom du compte", 105),
                    ("piece", "Pièce", 120), ("partenaire", "Partenaire", 110), ("libelle", "Libellé", 140),
                    ("debit", "Débit", 85), ("credit", "Crédit", 85), ("source", "Source", 150)],
    "annexe": [("page", "Page", 50), ("texte", "Texte", 620), ("source", "Source", 150)],
    "autre": [("page", "Page", 50), ("texte", "Texte", 620), ("source", "Source", 150)],
}
MONTANTS = {"debit", "credit", "montant", "precedent"}


def _montant(v) -> str:
    return "" if v in (None, "") else f"{float(v):,.2f}".replace(",", "'")


def _texte(v, cle: str) -> str:
    if cle in MONTANTS:
        return _montant(v)
    if v is None:
        return ""
    if cle == "date" and len(str(v)) >= 10 and str(v)[4] == "-":  # 2024-01-05 → 05.01.2024
        a, m, j = str(v)[:10].split("-")
        return f"{j}.{m}.{a}"
    texte = " ".join(str(v).split())
    return texte[:300] + "…" if len(texte) > 300 else texte


class OngletDocuments:
    def __init__(self, parent, fenetre) -> None:
        self.f = fenetre
        self.imports: list[catalogue.Import] = []
        self.vues: dict[str, dict] = {}

        haut = ttk.Frame(parent)
        haut.pack(fill="x")
        fenetre.btn_importer = ttk.Button(haut, text="▶  Importer les documents", style="Grand.TButton",
                                          command=fenetre._importer)
        fenetre.btn_importer.pack(side="left")
        ttk.Button(haut, text="Réglages IA…", command=fenetre._reglages_ia).pack(side="left", padx=(8, 0))
        ttk.Button(haut, text="Dossier à importer", command=lambda: fenetre._ouvrir(
            fenetre.dossier / "entrees" / "07_documents" if fenetre.dossier else None)).pack(side="left", padx=(8, 0))
        ttk.Label(haut, text="Exercice").pack(side="left", padx=(20, 4))
        self.v_exercice = tk.StringVar(value=TOUS)
        self.cb_exercice = ttk.Combobox(haut, textvariable=self.v_exercice, values=[TOUS], width=8, state="readonly")
        self.cb_exercice.pack(side="left")
        self.cb_exercice.bind("<<ComboboxSelected>>", lambda _e: self.afficher())
        self.lbl_etat = ttk.Label(parent, style="Doux.TLabel", wraplength=860,
                                  text="Dépose tes documents dans « Dossier à importer », puis clique sur Importer.")
        self.lbl_etat.pack(anchor="w", pady=(6, 6))

        self.carnet = ttk.Notebook(parent)
        self.carnet.pack(fill="both", expand=True)
        self._construire_ensemble(self.carnet)
        self.pages_types: dict[str, dict] = {}
        for type_ in ONGLETS_TYPES:
            cadre = ttk.Frame(self.carnet, padding=(0, 8, 0, 0))
            self.carnet.add(cadre, text=f" {TITRES[type_]} ")
            self.pages_types[type_] = self._construire_type(cadre, type_)

    # ------------------------------------------------------------ vue d'ensemble

    def _construire_ensemble(self, carnet) -> None:
        cadre = ttk.Frame(carnet, padding=(0, 8, 0, 0))
        carnet.add(cadre, text=" Vue d'ensemble ")
        colonnes = [("fichier", "Fichier", 170), ("exercice", "Exercice", 60), ("pages", "Pages", 45),
                    ("sections", "Sections trouvées", 290), ("methodes", "Reconnu par", 150), ("etat", "État", 100)]
        self.arbre_ensemble = self._tableau(cadre, colonnes)
        self.arbre_ensemble.bind("<Double-1>", lambda _e: self._ouvrir_ensemble("html"))
        boutons = ttk.Frame(cadre)
        boutons.pack(anchor="w", pady=(6, 0))
        ttk.Button(boutons, text="Document source", command=lambda: self._ouvrir_ensemble("source")).pack(side="left")
        ttk.Button(boutons, text="Classeur", command=lambda: self._ouvrir_ensemble("classeur")).pack(side="left", padx=6)
        ttk.Button(boutons, text="Page lisible", command=lambda: self._ouvrir_ensemble("html")).pack(side="left")
        ttk.Label(cadre, style="Doux.TLabel",
                  text="Double-clic sur une ligne : page lisible du document. Les onglets suivants montrent chaque type.").pack(anchor="w", pady=(4, 0))
        self.ensemble_items: dict[str, catalogue.Import] = {}

    def _ouvrir_ensemble(self, quoi: str) -> None:
        choix = self.arbre_ensemble.selection()
        imp = self.ensemble_items.get(choix[0]) if choix else (self.imports[0] if self.imports else None)
        self._ouvrir_import(imp, quoi)

    def _ouvrir_import(self, imp, quoi: str) -> None:
        if imp is None:
            return
        self.f._ouvrir({"source": imp.chemin_source, "classeur": imp.classeur, "html": imp.html}[quoi])

    # ------------------------------------------------------------ onglet d'un type

    def _tableau(self, parent, colonnes, arbre: bool = False) -> ttk.Treeview:
        cadre = ttk.Frame(parent)
        cadre.pack(fill="both", expand=True)
        t = ttk.Treeview(cadre, columns=[c for c, _, _ in colonnes], show="tree headings" if arbre else "headings",
                         height=12)
        if arbre:
            t.heading("#0", text="Libellé")
            t.column("#0", width=520)
        for cle, titre, largeur in colonnes:
            t.heading(cle, text=titre)
            t.column(cle, width=largeur, anchor="e" if cle in MONTANTS else "w", stretch=False)
        vy = ttk.Scrollbar(cadre, orient="vertical", command=t.yview)
        vx = ttk.Scrollbar(cadre, orient="horizontal", command=t.xview)
        t.configure(yscrollcommand=vy.set, xscrollcommand=vx.set)
        t.grid(row=0, column=0, sticky="nsew")
        vy.grid(row=0, column=1, sticky="ns")
        vx.grid(row=1, column=0, sticky="ew")
        cadre.rowconfigure(0, weight=1)
        cadre.columnconfigure(0, weight=1)
        t.tag_configure("ecart", foreground="#b35900")
        t.tag_configure("total", font=("Segoe UI", 9, "bold"))
        return t

    def _construire_type(self, cadre, type_: str) -> dict:
        sources = ttk.Label(cadre, text="", wraplength=860, justify="left")
        sources.pack(anchor="w")
        controles = ttk.Frame(cadre)
        controles.pack(anchor="w", fill="x", pady=(4, 6))
        arbre = type_ in ("bilan", "compte_resultat")
        colonnes = [("montant", "Exercice", 110), ("precedent", "Exercice précédent", 130)] if arbre \
            else COLONNES_TABLE[type_]
        table = self._tableau(cadre, colonnes, arbre=arbre)
        boutons = ttk.Frame(cadre)
        boutons.pack(anchor="w", pady=(6, 0))
        page = {"sources": sources, "controles": controles, "table": table, "colonnes": colonnes,
                "arbre": arbre, "items": {}}
        for texte, quoi in [("Document source", "source"), ("Classeur", "classeur"), ("Page lisible", "html")]:
            ttk.Button(boutons, text=texte, command=lambda q=quoi, p=page: self._ouvrir_type(p, q)).pack(side="left", padx=(0, 6))
        return page

    def _ouvrir_type(self, page: dict, quoi: str) -> None:
        choix = page["table"].selection()
        imp = page["items"].get(choix[0]) if choix else None
        if imp is None and page.get("sources_imports"):
            imp = page["sources_imports"][0]
        self._ouvrir_import(imp, quoi)

    # ------------------------------------------------------------ remplissage

    def actualiser(self) -> None:
        self.imports = catalogue.charger(self.f.dossier) if self.f.dossier else []
        annees = [TOUS] + [str(a) for a in catalogue.exercices(self.imports)]
        self.cb_exercice.configure(values=annees)
        if self.v_exercice.get() not in annees:
            self.v_exercice.set(TOUS)
        self.afficher()

    def _exercice(self) -> int | None:
        v = self.v_exercice.get()
        return None if v == TOUS else int(v)

    def afficher(self) -> None:
        exercice = self._exercice()
        choisis = [i for i in self.imports if exercice is None or i.exercice == exercice]
        t = self.arbre_ensemble
        t.delete(*t.get_children())
        self.ensemble_items = {}
        for imp in choisis:
            methodes = ", ".join(f"{METHODES.get(m, m)} {n}" for m, n in imp.methodes.items())
            etat = "✓ OK" if imp.etat == "ok" else "⚠ à vérifier"
            item = t.insert("", "end", values=(imp.source, imp.exercice or "", imp.nb_pages, imp.resume_sections(),
                                               methodes, etat), tags=("ecart",) if imp.etat != "ok" else ())
            self.ensemble_items[item] = imp
        a_verifier = sum(1 for i in choisis if i.etat != "ok")
        self.lbl_etat.configure(text=f"{len(choisis)} document(s) importé(s)"
                                     + (f", {a_verifier} à vérifier." if a_verifier else ", tous OK.")
                                if choisis else "Aucun document importé pour l'instant.")
        for type_, page in self.pages_types.items():
            self._remplir_type(type_, page, catalogue.vue(self.imports, type_, exercice))
            n = len(page["table"].get_children())
            self.carnet.tab(ONGLETS_TYPES.index(type_) + 1, text=f" {TITRES[type_]} ({n}) " if n else f" {TITRES[type_]} ")

    def _remplir_type(self, type_: str, page: dict, v: dict) -> None:
        page["sources_imports"] = [s["import"] for s in v["sources"]]
        if v["sources"]:
            lignes = [f"• {s['fichier']} {s['pages']} (exercice {s['exercice']}) — reconnu par "
                      + ", ".join(f"{METHODES.get(m, m)} {n}" for m, n in s["methodes"].items())
                      for s in v["sources"]]
            page["sources"].configure(text="Sources :\n" + "\n".join(lignes))
        else:
            page["sources"].configure(text="Aucun document de ce type importé pour cet exercice.")
        for w in page["controles"].winfo_children():
            w.destroy()
        for c in v["controles"]:
            signe = {"ok": "✓", "info": "ℹ"}.get(c["resultat"], "⚠")
            couleur = {"ok": "#1a7f37", "info": "#57606a"}.get(c["resultat"], "#b35900")
            tk.Label(page["controles"], text=f"{signe} {c['controle']} : {c['detail']}", fg=couleur,
                     anchor="w", justify="left").pack(anchor="w")
        t = page["table"]
        t.delete(*t.get_children())
        page["items"] = {}
        par_fichier = {s["fichier"]: s["import"] for s in v["sources"]}

        def import_de(ligne):
            source = str(ligne.get("source") or "")
            return next((imp for nom, imp in par_fichier.items() if source.startswith(nom)), None)
        if page["arbre"]:
            def inserer(parent, noeuds):
                for n in noeuds:
                    item = t.insert(parent, "end", text=n["libelle"], open=True,
                                    values=(_montant(n["montant"]), _montant(n["precedent"])),
                                    tags=("total",) if n.get("groupe") or n.get("niveau") == 1 else ())
                    inserer(item, n["enfants"])
            for s in v["sources"]:
                racine = t.insert("", "end", text=f"{s['fichier']} {s['pages']}", open=True, tags=("total",))
                page["items"][racine] = s["import"]
                lignes = [l for l in v["lignes"] if import_de(l) is s["import"]]
                inserer(racine, catalogue.arbre(lignes))
            return
        for l in v["lignes"][:5000]:
            item = t.insert("", "end", values=[_texte(l.get(c), c) for c, _, _ in page["colonnes"]])
            page["items"][item] = import_de(l)


def construire(parent, fenetre) -> OngletDocuments:
    return OngletDocuments(parent, fenetre)
