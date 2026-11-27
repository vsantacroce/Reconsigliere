"""Fenêtre de Reconsigliere : choisir le dossier de travail, déposer les fichiers, lancer, ouvrir les résultats.

Lancement : Reconsigliere.bat (Windows), reconsigliere.sh (Ubuntu) ou python -m reconsigliere.fenetre
"""

from __future__ import annotations

import os
import queue
import re
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from datetime import date

from . import __version__, config, exercices, installation, societe
from . import onglet_apprentissage as onglet_apprentissage_module
from . import onglet_documents as onglet_documents_module
from . import onglets_societe

try:  # construit par le fil Salaires ; tant qu'il n'existe pas, l'onglet affiche une phrase
    from . import onglet_salaires as onglet_salaires_module
except ImportError:
    onglet_salaires_module = None

TITRE = "Reconsigliere"
NB_ETAPES = 5


class Fenetre:
    def __init__(self, racine_tk: tk.Tk) -> None:
        self.tk = racine_tk
        self.dossier: Path | None = None
        self.messages: queue.Queue = queue.Queue()
        self.en_cours = False

        racine_tk.title(f"{TITRE} — réconciliation et état de la société")
        self._icone()
        self._style()
        echelle = max(1.0, float(racine_tk.tk.call("tk", "scaling")) / (96 / 72))
        racine_tk.minsize(min(round(820 * echelle), racine_tk.winfo_screenwidth() - 40),
                          min(round(640 * echelle), racine_tk.winfo_screenheight() - 80))
        racine_tk.geometry(onglets_societe.geometrie(racine_tk.winfo_screenwidth(),
                                                     racine_tk.winfo_screenheight(), echelle))
        self._construire()

        memorise = installation.dossier_memorise()
        if memorise and memorise.is_dir():
            self._utiliser(memorise)
        else:
            self._actualiser()
            racine_tk.after(400, self._premier_lancement)

        racine_tk.bind("<FocusIn>", lambda _e: self._actualiser_compteurs())
        racine_tk.after(100, self._lire_messages)

    # ------------------------------------------------------------ construction

    def _icone(self) -> None:
        dossier = Path(__file__).resolve().parents[2] / "windows"
        try:
            if sys.platform.startswith("win") and (dossier / "reconsigliere.ico").exists():
                self.tk.iconbitmap(default=str(dossier / "reconsigliere.ico"))
            elif (dossier / "reconsigliere.png").exists():
                self._image_icone = tk.PhotoImage(file=str(dossier / "reconsigliere.png"))
                self.tk.iconphoto(True, self._image_icone)
        except tk.TclError:
            pass

    def _style(self) -> None:
        style = ttk.Style(self.tk)
        if sys.platform.startswith("win") and "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Titre.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Doux.TLabel", foreground="#667085")
        style.configure("Chemin.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Grand.TButton", font=("Segoe UI", 12, "bold"), padding=(16, 10))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Vert.Horizontal.TProgressbar", background="#1f8a4c", troughcolor="#e4e7ec")
        style.configure("Explication.TLabel", font=("Segoe UI", 11), foreground="#344054")
        # Carnet sans rangée d'onglets : la barre de boutons (deux lignes) la remplace.
        style.layout("SansOnglets.TNotebook.Tab", [])
        style.configure("SansOnglets.TNotebook", borderwidth=0, tabmargins=0)
        style.configure("Onglet.TRadiobutton", font=("Segoe UI", 11), padding=(10, 7), anchor="center",
                        background="#e4e7ec", foreground="#1d2939", indicatorsize=0, indicatormargin=0,
                        relief="flat")
        style.layout("Onglet.TRadiobutton", [("Radiobutton.padding", {"sticky": "nswe", "children": [
            ("Radiobutton.label", {"sticky": "nswe"})]})])
        style.map("Onglet.TRadiobutton",
                  background=[("selected", "#1d4ed8"), ("active", "#cbd5e1")],
                  foreground=[("selected", "#ffffff")],
                  font=[("selected", ("Segoe UI", 11, "bold"))])

    def _section(self, parent, titre: str, extensible: bool = False) -> ttk.Labelframe:
        cadre = ttk.Labelframe(parent, text=titre, padding=10, style="Section.TLabelframe")
        cadre.pack(fill="both" if extensible else "x", expand=extensible, pady=(0, 10))
        return cadre

    def _construire(self) -> None:
        principal = ttk.Frame(self.tk, padding=16)
        principal.pack(fill="both", expand=True)

        ttk.Label(principal, text=TITRE, style="Titre.TLabel").pack(anchor="w")
        ttk.Label(principal, style="Doux.TLabel",
                  text="Le consigliere de ta compta : il rapproche tes transactions, tes factures et ta comptabilité.").pack(anchor="w", pady=(0, 12))

        barre = ttk.Frame(principal)
        barre.pack(fill="x", pady=(0, 8))
        self.barre_onglets = barre
        self.onglets = ttk.Notebook(principal, style="SansOnglets.TNotebook")
        self.onglets.pack(fill="both", expand=True)
        self.v_onglet = tk.StringVar()
        self.cadres: dict[str, ttk.Frame] = {}
        for i, (cle, titre) in enumerate(onglets_societe.ONGLETS):
            page = ttk.Frame(self.onglets, padding=(0, 4, 0, 0))
            self.onglets.add(page, text=titre)
            explication = ttk.Label(page, text=onglets_societe.EXPLICATIONS[cle], style="Explication.TLabel",
                                    wraplength=900, justify="left")
            explication.pack(fill="x", anchor="w", pady=(0, 8))
            explication.bind("<Configure>", lambda e: e.widget.configure(wraplength=max(200, e.width - 10)))
            cadre = ttk.Frame(page)
            cadre.pack(fill="both", expand=True)
            self.cadres[cle] = cadre
            ligne, colonne = divmod(i, onglets_societe.ONGLETS_PAR_LIGNE)
            ttk.Radiobutton(barre, text=titre, value=str(page), variable=self.v_onglet, style="Onglet.TRadiobutton",
                            command=lambda p=page: self.onglets.select(p)).grid(
                row=ligne, column=colonne, sticky="nsew", padx=(0, 4), pady=(0, 4))
        for c in range(onglets_societe.ONGLETS_PAR_LIGNE):
            barre.columnconfigure(c, weight=1, uniform="onglets")
        self.onglets.bind("<<NotebookTabChanged>>", lambda _e: self._onglet_change())

        onglet_reco = self.cadres["reconciliation"]
        self.documents = onglet_documents_module.construire(self.cadres["documents"], self)
        self.apprentissage = onglet_apprentissage_module.construire(self.cadres["apprentissage"], self)
        if onglet_salaires_module is not None:
            self.salaires = onglet_salaires_module.construire(self.cadres["salaires"], self)
        else:
            self.salaires = None
            ttk.Label(self.cadres["salaires"], style="Doux.TLabel", wraplength=900, justify="left",
                      text="Cette partie est en cours de fabrication : elle arrivera dans une prochaine mise à jour.").pack(
                anchor="w")
        self._construire_societe(self.cadres["brevets"])
        self.projets = onglets_societe.OngletTableau(
            self.cadres["projets"], onglets_societe.COLONNES_PROJETS, onglets_societe.remplir_projets,
            boutons=[("Modifier les projets (Excel)", self._ouvrir_classeur_societe)])
        self.revenus = onglets_societe.OngletTableau(
            self.cadres["revenus"], onglets_societe.COLONNES_REVENUS, onglets_societe.remplir_revenus,
            boutons=[("Modifier les revenus (Excel)", self._ouvrir_classeur_societe)])
        self.plan = onglets_societe.OngletTableau(
            self.cadres["plan"], onglets_societe.COLONNES_REFERENTIEL["PlanComptable"],
            lambda annee: onglets_societe.lignes_referentiel(annee, "PlanComptable"), avec_annee=True,
            boutons=[("Voir les listes de l'année (Excel)", self._voir_referentiel)])
        self.partenaires = onglets_societe.OngletTableau(
            self.cadres["partenaires"], onglets_societe.COLONNES_REFERENTIEL["Partenaires"],
            lambda annee: onglets_societe.lignes_referentiel(annee, "Partenaires"), avec_annee=True,
            boutons=[("Voir les listes de l'année (Excel)", self._voir_referentiel)])
        self._construire_exercices(self.cadres["annee"])
        self.actualisations = {
            "documents": lambda: self.documents.actualiser(),
            "apprentissage": lambda: self.apprentissage.actualiser(),
            "salaires": lambda: getattr(self.salaires, "actualiser", lambda: None)(),
            "brevets": self._actualiser_societe,
            "projets": lambda: self.projets.actualiser(),
            "revenus": lambda: self.revenus.actualiser(),
            "plan": lambda: self.plan.actualiser(),
            "partenaires": lambda: self.partenaires.actualiser(),
            "annee": self._actualiser_exercices,
        }
        principal_reco = self._page_defilante(onglet_reco)

        # 1. Dossier de travail
        s1 = self._section(principal_reco, "1. Dossier de travail")
        self.lbl_dossier = ttk.Label(s1, text="Aucun dossier choisi", style="Chemin.TLabel",
                                     wraplength=480)
        self.lbl_dossier.grid(row=0, column=0, sticky="w")
        boutons1 = ttk.Frame(s1)
        boutons1.grid(row=0, column=1, sticky="e")
        ttk.Button(boutons1, text="Choisir l'emplacement…", command=self._choisir).pack(side="left", padx=(0, 6))
        self.btn_ouvrir_dossier = ttk.Button(boutons1, text="Ouvrir",
                                             command=lambda: self._ouvrir(self.dossier))
        self.btn_ouvrir_dossier.pack(side="left")
        self.lbl_etat_dossier = ttk.Label(s1, style="Doux.TLabel", text="")
        self.lbl_etat_dossier.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        s1.columnconfigure(0, weight=1)

        # 2. Fichiers à déposer
        s2 = self._section(principal_reco, "2. Dépose tes fichiers dans ces dossiers")
        self.compteurs: dict[str, ttk.Label] = {}
        self.boutons_dossiers: list[ttk.Button] = []
        ligne = 0
        for rel, titre, _ in installation.DOSSIERS:
            if titre is None or not rel.startswith("entrees") or rel == societe.NOM_DOSSIER:
                continue
            ttk.Label(s2, text=titre).grid(row=ligne, column=0, sticky="w", pady=2)
            ttk.Label(s2, text=rel.replace("/", " › "), style="Doux.TLabel").grid(row=ligne, column=1, sticky="w", padx=12)
            compteur = ttk.Label(s2, text="—", width=14, anchor="e")
            compteur.grid(row=ligne, column=2, sticky="e")
            self.compteurs[rel] = compteur
            bouton = ttk.Button(s2, text="Ouvrir", width=8,
                                command=lambda r=rel: self._ouvrir(self.dossier / r if self.dossier else None))
            bouton.grid(row=ligne, column=3, padx=(10, 0))
            self.boutons_dossiers.append(bouton)
            ligne += 1
        s2.columnconfigure(1, weight=1)

        # 3. Lancer
        s3 = self._section(principal_reco, "3. Lancer", extensible=True)
        haut = ttk.Frame(s3)
        haut.pack(fill="x")
        self.btn_lancer = ttk.Button(haut, text="▶  Lancer la réconciliation", style="Grand.TButton",
                                     command=self._lancer)
        self.btn_lancer.pack(side="left")
        droite = ttk.Frame(haut)
        droite.pack(side="left", fill="x", expand=True, padx=(14, 0))
        self.lbl_etape = ttk.Label(droite, text="Prêt.", style="Doux.TLabel")
        self.lbl_etape.pack(anchor="w")
        self.progression = ttk.Progressbar(droite, maximum=NB_ETAPES, mode="determinate",
                                           style="Vert.Horizontal.TProgressbar")
        self.progression.pack(fill="x", pady=(4, 0))

        journal_cadre = ttk.Frame(s3)
        journal_cadre.pack(fill="both", expand=True, pady=(10, 0))
        self.journal = tk.Text(journal_cadre, height=4, wrap="word", relief="flat",
                               font=("Consolas", 9) if sys.platform.startswith("win") else ("Monospace", 9),
                               background="#f6f7f9", state="disabled")
        barre = ttk.Scrollbar(journal_cadre, command=self.journal.yview)
        self.journal.configure(yscrollcommand=barre.set)
        self.journal.pack(side="left", fill="both", expand=True)
        barre.pack(side="right", fill="y")
        self.journal.tag_configure("erreur", foreground="#c2410c")

        # 4. Résultats
        s4 = self._section(principal_reco, "4. Résultats")
        self.lbl_resume = ttk.Label(s4, text="Aucun résultat pour l'instant.", style="Doux.TLabel", wraplength=700)
        self.lbl_resume.pack(anchor="w", pady=(0, 8))
        boutons4 = ttk.Frame(s4)
        boutons4.pack(anchor="w")
        self.boutons_resultats = {
            "html": ("Rapport (page)", lambda d: d / "sorties" / "reconciliation.html"),
            "xlsx": ("Rapport (Excel)", lambda d: d / "sorties" / "reconciliation.xlsx"),
            "a_compta": ("Pièces à comptabiliser", lambda d: d / "sorties" / "a_comptabiliser"),
            "renommes": ("Toutes les pièces renommées", lambda d: d / "sorties" / "pdf_renommes"),
            "corrections": ("Mes corrections", lambda d: d / "entrees" / "05_mes_corrections" / "mes_corrections.xlsx"),
        }
        self.widgets_resultats: dict[str, ttk.Button] = {}
        for cle, (texte, chemin) in self.boutons_resultats.items():
            b = ttk.Button(boutons4, text=texte, command=lambda c=chemin: self._ouvrir(c(self.dossier)))
            b.pack(side="left", padx=(0, 6))
            self.widgets_resultats[cle] = b

        commit = os.environ.get("RECONSIGLIERE_COMMIT", "")
        version = f"Version {__version__}" + (f" ({commit}, mise à jour automatique)" if commit else "")
        ttk.Label(principal, text=f"{version} · tes fichiers restent sur cet ordinateur.",
                  style="Doux.TLabel").pack(side="bottom", anchor="e", pady=(6, 0), before=self.barre_onglets)

    def _page_defilante(self, parent) -> ttk.Frame:
        """Cadre qui défile verticalement quand l'écran est trop petit (affichage agrandi de Windows)."""
        fond = ttk.Style(self.tk).lookup("TFrame", "background") or "#dcdad5"
        toile = tk.Canvas(parent, highlightthickness=0, borderwidth=0, background=fond)
        defil = ttk.Scrollbar(parent, orient="vertical", command=toile.yview)
        interieur = ttk.Frame(toile)
        fenetre_id = toile.create_window((0, 0), window=interieur, anchor="nw")
        toile.configure(yscrollcommand=defil.set)

        def ajuster(_e=None) -> None:
            toile.itemconfigure(fenetre_id, width=toile.winfo_width())
            toile.configure(scrollregion=toile.bbox("all"))
            if interieur.winfo_reqheight() > toile.winfo_height():
                defil.pack(side="right", fill="y")
            else:
                defil.pack_forget()
                toile.yview_moveto(0)

        interieur.bind("<Configure>", ajuster)
        toile.bind("<Configure>", ajuster)
        toile.bind("<Enter>", lambda _e: toile.bind_all(
            "<MouseWheel>", lambda e: toile.yview_scroll(-1 if e.delta > 0 else 1, "units")))
        toile.bind("<Leave>", lambda _e: toile.unbind_all("<MouseWheel>"))
        toile.pack(side="left", fill="both", expand=True)
        return interieur

    def _construire_societe(self, parent) -> None:
        haut = self._section(parent, "Brevets en chiffres")
        self.tuiles: dict[str, ttk.Label] = {}
        intitules = [
            ("familles", "Familles de brevets actives"),
            ("depots", "Dépôts actifs"),
            ("capitalisable", "Coûts brevets capitalisables (CHF)"),
            ("charge", "Coûts brevets en charge (CHF)"),
        ]
        for i, (cle, texte) in enumerate(intitules):
            cadre = ttk.Frame(haut, padding=(0, 0, 18, 6))
            cadre.grid(row=i // 2, column=i % 2, sticky="w")
            valeur = ttk.Label(cadre, text="—", style="Titre.TLabel")
            valeur.pack(anchor="w")
            ttk.Label(cadre, text=texte, style="Doux.TLabel").pack(anchor="w")
            self.tuiles[cle] = valeur
        for c in range(2):
            haut.columnconfigure(c, weight=1)

        milieu = self._section(parent, "Brevets par famille", extensible=True)
        colonnes = ("famille", "titre", "statut", "pays", "capitalisable", "charge")
        self.arbre = ttk.Treeview(milieu, columns=colonnes, show="headings", height=6)
        for col, texte, largeur, ancre in [
                ("famille", "Famille", 130, "w"), ("titre", "Titre", 300, "w"), ("statut", "Statut", 150, "w"),
                ("pays", "Pays", 90, "w"), ("capitalisable", "Capitalisable", 100, "e"), ("charge", "Charge", 90, "e")]:
            self.arbre.heading(col, text=texte)
            self.arbre.column(col, width=largeur, anchor=ancre, stretch=(col == "titre"))
        self.arbre.pack(fill="both", expand=True)
        self.lbl_attention = ttk.Label(milieu, text="", wraplength=760, justify="left", foreground="#c2410c")
        self.lbl_attention.pack(anchor="w", pady=(8, 0))

        bas = self._section(parent, "Mettre à jour")
        self.lbl_societe = ttk.Label(bas, style="Doux.TLabel", wraplength=760, justify="left", text="")
        self.lbl_societe.pack(anchor="w", pady=(0, 8))
        boutons = ttk.Frame(bas)
        boutons.pack(anchor="w")
        self.boutons_societe = [
            ttk.Button(boutons, text="Ajouter au journal…", command=self._ajouter_journal),
            ttk.Button(boutons, text="Tableau de bord (page)", command=self._ouvrir_tableau_de_bord),
            ttk.Button(boutons, text="Projets, revenus, journal (Excel)", command=self._ouvrir_classeur_societe),
            ttk.Button(boutons, text="Dossier société",
                       command=lambda: self._ouvrir(societe.dossier_societe() if self.dossier else None)),
        ]
        for b in self.boutons_societe:
            b.pack(side="left", padx=(0, 6))

    def _construire_exercices(self, parent) -> None:
        haut = self._section(parent, "Année")
        ligne = ttk.Frame(haut)
        ligne.pack(fill="x")
        ttk.Label(ligne, text="Année :").pack(side="left")
        self.v_exercice = tk.StringVar()
        self.cb_exercice = ttk.Combobox(ligne, textvariable=self.v_exercice, width=8, state="readonly")
        self.cb_exercice.pack(side="left", padx=(6, 12))
        self.cb_exercice.bind("<<ComboboxSelected>>", lambda _e: self._actualiser_exercices())
        self.lbl_statut_exercice = ttk.Label(ligne, text="", style="Chemin.TLabel")
        self.lbl_statut_exercice.pack(side="left")
        self.lbl_compteurs_exercice = ttk.Label(haut, text="", style="Doux.TLabel", wraplength=760, justify="left")
        self.lbl_compteurs_exercice.pack(anchor="w", pady=(6, 0))
        self.lbl_alerte_exercice = ttk.Label(haut, text="", foreground="#c2410c", wraplength=760, justify="left")
        self.lbl_alerte_exercice.pack(anchor="w")

        milieu = self._section(parent, "Modifications demandées pendant l'année", extensible=True)
        colonnes = ("date", "action", "liste", "cle", "champ", "avant", "apres", "motif")
        self.arbre_changements = ttk.Treeview(milieu, columns=colonnes, show="headings", height=7)
        for col, texte, largeur in [("date", "Date", 85), ("action", "Action", 90), ("liste", "Liste", 100),
                                    ("cle", "Élément", 110), ("champ", "Champ", 80), ("avant", "Avant", 110),
                                    ("apres", "Après", 110), ("motif", "Motif", 180)]:
            self.arbre_changements.heading(col, text=texte)
            self.arbre_changements.column(col, width=largeur, anchor="w", stretch=(col == "motif"))
        self.arbre_changements.pack(fill="both", expand=True)

        bas = self._section(parent, "Que faire avec cette année")
        b1 = ttk.Frame(bas)
        b1.pack(anchor="w")
        b2 = ttk.Frame(bas)
        b2.pack(anchor="w", pady=(6, 0))
        self.boutons_exercices = [
            ttk.Button(b1, text="Demander une modification…", command=self._demander_changement),
            ttk.Button(b1, text="Écarts avec l'année précédente…", command=self._voir_ecarts),
            ttk.Button(b1, text="Suggestions depuis les fichiers…", command=self._voir_suggestions),
            ttk.Button(b2, text="Voir les listes de l'année (Excel)", command=self._voir_referentiel),
            ttk.Button(b2, text="Construire depuis les fichiers…", command=self._construire_exercice),
            ttk.Button(b2, text="Valider et verrouiller…", command=self._valider_exercice),
            ttk.Button(b2, text="Rouvrir…", command=self._rouvrir_exercice),
        ]
        for b in self.boutons_exercices:
            b.pack(side="left", padx=(0, 6))

    # ------------------------------------------------------------ exercices

    def _annee(self) -> int | None:
        v = self.v_exercice.get().strip()
        return int(v) if v.isdigit() else None

    def _actualiser_exercices(self) -> None:
        if self.dossier is None:
            return
        annees = exercices.lister()
        self.cb_exercice.configure(values=[str(a) for a in annees])
        if self._annee() not in annees:
            courant = exercices.exercice_courant()
            self.v_exercice.set(str(courant) if courant else "")
        self.arbre_changements.delete(*self.arbre_changements.get_children())
        annee = self._annee()
        if annee is None:
            self.lbl_statut_exercice.configure(text="Aucune année pour l'instant.")
            self.lbl_compteurs_exercice.configure(
                text="Dépose le plan comptable et le grand livre normalisés dans entrees › 06_societe › imports › "
                     "AAAA, puis clique sur « Construire depuis les fichiers… » pour créer la première année.")
            self.lbl_alerte_exercice.configure(text="")
            return
        try:
            r = exercices.resume(annee)
        except Exception as e:  # noqa: BLE001
            self.lbl_alerte_exercice.configure(text=f"Lecture impossible : {e}")
            return
        if r["statut"] == exercices.VALIDE:
            jour = r["valide_le"][:10].split("-")
            self.lbl_statut_exercice.configure(text=f"🔒 Validée et verrouillée le {'.'.join(reversed(jour))}")
        else:
            self.lbl_statut_exercice.configure(text="Ouverte : les modifications sont possibles")
        self.lbl_compteurs_exercice.configure(
            text=" · ".join(f"{nom} : {n}" for nom, n in r["compteurs"].items()))
        alertes = [a for a in (exercices.verifier(x) for x in annees) if a]
        self.lbl_alerte_exercice.configure(text="\n".join(f"• {a}" for a in alertes))
        for c in r["changements"]:
            jour = str(c.get("date") or "")[:10]
            self.arbre_changements.insert("", "end", values=(
                ".".join(reversed(jour.split("-"))) if jour else "", c.get("action", ""),
                exercices.NOMS_LISTES.get(c.get("liste"), c.get("liste", "")), c.get("cle", ""),
                c.get("champ", "") or "", "" if c.get("avant") is None else c.get("avant"),
                "" if c.get("apres") is None else c.get("apres"), c.get("motif", "")))

    def _construire_exercice(self) -> None:
        if self.dossier is None:
            return
        imports = societe.dossier_societe() / "imports"
        proposees = sorted(int(p.name) for p in imports.iterdir() if p.is_dir() and p.name.isdigit()) \
            if imports.exists() else []
        defaut = next((a for a in proposees if a not in exercices.lister()), date.today().year - 1)
        annee = simpledialog.askinteger(
            TITRE, "Construire le référentiel de quel exercice ?\n\n"
                   "Reconsigliere lit entrees › 06_societe › imports › AAAA (plan comptable et grand livre),\n"
                   "ton classeur des brevets (état au 31.12) et societe.xlsx (projets, revenus).",
            initialvalue=defaut, minvalue=2000, maxvalue=2100, parent=self.tk)
        if annee is None:
            return
        ecraser = False
        if exercices.fichier_referentiel(annee).exists():
            if exercices.est_valide(annee):
                messagebox.showwarning(TITRE, f"L'exercice {annee} est validé et verrouillé.", parent=self.tk)
                return
            n = len(exercices.lire(annee)["Changements"])
            if not messagebox.askyesno(
                    TITRE, f"Le référentiel {annee} existe déjà"
                           + (f" et contient {n} changement(s), qui seront effacés" if n else "")
                           + ".\n\nLe reconstruire depuis les fichiers ?", parent=self.tk):
                return
            ecraser = True
        try:
            compteurs = exercices.construire(annee, ecraser_changements=ecraser)
        except PermissionError:
            messagebox.showerror(TITRE, "Un fichier est ouvert dans Excel. Ferme-le puis réessaie.", parent=self.tk)
            return
        self.v_exercice.set(str(annee))
        self._actualiser_exercices()
        details = "\n".join(f"{exercices.NOMS_LISTES[n]} : {v}" for n, v in compteurs.items())
        messagebox.showinfo(TITRE, f"Référentiel {annee} construit.\n\n{details}\n\n"
                                   "Contrôle-le avec « Voir le référentiel », puis valide-le.", parent=self.tk)

    def _demander_changement(self) -> None:
        annee = self._annee()
        if annee is None:
            messagebox.showinfo(TITRE, "Construis d'abord un exercice.", parent=self.tk)
            return
        if exercices.est_valide(annee):
            messagebox.showwarning(TITRE, f"L'exercice {annee} est validé et verrouillé.\n"
                                          "Choisis l'exercice ouvert, ou rouvre celui-ci avec un motif.", parent=self.tk)
            return
        Changement(self.tk, annee, on_fin=self._actualiser_exercices)

    def _voir_ecarts(self) -> None:
        annee = self._annee()
        if annee is None:
            return
        precedents = [a for a in exercices.lister() if a < annee]
        if not precedents:
            messagebox.showinfo(TITRE, f"Aucun exercice avant {annee} : rien à comparer.", parent=self.tk)
            return
        Ecarts(self.tk, annee, precedents[-1], exercices.ecarts(annee, precedents[-1]))

    def _voir_suggestions(self) -> None:
        annee = self._annee()
        if annee is None:
            return
        if exercices.est_valide(annee):
            messagebox.showinfo(TITRE, f"L'exercice {annee} est validé et verrouillé.", parent=self.tk)
            return
        try:
            lignes = exercices.suggestions(annee)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(TITRE, f"Lecture impossible : {e}", parent=self.tk)
            return
        if not lignes:
            messagebox.showinfo(TITRE, f"Les fichiers ne montrent rien de nouveau pour {annee}.", parent=self.tk)
            return

        def appliquer(choisis, motif: str) -> bool:
            try:
                for e in choisis:
                    exercices.appliquer(annee, e, motif)
            except (ValueError, exercices.ExerciceVerrouille) as err:
                messagebox.showwarning(TITRE, str(err), parent=self.tk)
                return False
            except PermissionError:
                messagebox.showerror(TITRE, "Le référentiel est ouvert dans Excel. Ferme-le puis réessaie.",
                                     parent=self.tk)
                return False
            self._actualiser_exercices()
            return True

        Ecarts(self.tk, annee, None, lignes, on_appliquer=appliquer)

    def _voir_referentiel(self) -> None:
        annee = self._annee()
        if annee is None:
            return
        config.DOSSIER_SORTIES.mkdir(parents=True, exist_ok=True)
        try:
            copie = exercices.copier_vers(annee, config.DOSSIER_SORTIES / f"referentiel_{annee}_lecture.xlsx")
        except PermissionError:
            messagebox.showerror(TITRE, "La copie précédente est ouverte dans Excel. Ferme-la puis réessaie.",
                                 parent=self.tk)
            return
        self._ouvrir(copie)

    def _valider_exercice(self) -> None:
        annee = self._annee()
        if annee is None or exercices.est_valide(annee):
            return
        alerte = next((a for a in (exercices.verifier(x) for x in exercices.lister()) if a), None)
        if alerte:
            messagebox.showwarning(TITRE, alerte, parent=self.tk)
            return
        n = len(exercices.lire(annee)["Changements"])
        e = exercices.ecarts(annee)
        if not messagebox.askyesno(
                TITRE, f"Valider et verrouiller l'exercice {annee} ?\n\n"
                       f"{n} changement(s) demandé(s), {len(e)} écart(s) avec l'exercice précédent.\n\n"
                       f"Après validation, {annee} ne peut plus être modifié sans être rouvert avec un motif.\n"
                       f"L'exercice {annee + 1} s'ouvrira comme copie s'il n'existe pas encore.", parent=self.tk):
            return
        suivant = exercices.valider(annee)
        if suivant:
            self.v_exercice.set(str(suivant))
        self._actualiser_exercices()

    def _rouvrir_exercice(self) -> None:
        annee = self._annee()
        if annee is None or not exercices.est_valide(annee):
            return
        motif = simpledialog.askstring(TITRE, f"Pourquoi rouvrir l'exercice {annee} ?\n"
                                              "Le motif reste dans l'historique.", parent=self.tk)
        if not motif or not motif.strip():
            return
        exercices.rouvrir(annee, motif)
        self._actualiser_exercices()

    # ------------------------------------------------------------ société

    def _actualiser_societe(self) -> dict | None:
        if self.dossier is None:
            return None
        try:
            societe.creer_modele_si_absent()
            donnees = societe.synthese(societe.charger())
        except Exception as e:  # noqa: BLE001 - l'erreur doit apparaître dans la fenêtre
            self.lbl_attention.configure(text=f"Lecture impossible : {e}")
            return None
        c = donnees["compteurs"]
        self.tuiles["familles"].configure(text=f"{c['familles_actives']} / {c['familles']}")
        self.tuiles["depots"].configure(text=f"{c['depots_actifs']} (+{c['entrees_annoncees']})")
        self.tuiles["capitalisable"].configure(text=societe.format_chf(c["capitalisable"]))
        self.tuiles["charge"].configure(text=societe.format_chf(c["charge"]))
        self.arbre.delete(*self.arbre.get_children())
        for f in donnees["familles"]:
            self.arbre.insert("", "end", values=(
                f["famille"], f["titre"], f["statut"], ", ".join(f["pays"]),
                societe.format_chf(f["capitalisable"]), societe.format_chf(f["charge"])))
        self.lbl_attention.configure(
            text="\n".join(f"• {p}" for p in donnees["attention"]) if donnees["attention"] else "")
        fichiers = ", ".join(donnees["fichiers"]) or "aucun"
        self.lbl_societe.configure(
            text=f"Fichiers lus dans entrees › 06_societe : {fichiers}. Dépose-y ton classeur des brevets ; "
                 "tiens les projets, les revenus et le journal dans societe.xlsx.")
        return donnees

    def _ouvrir_classeur_societe(self) -> None:
        if self.dossier is None:
            return
        self._ouvrir(societe.creer_modele_si_absent())

    def _ouvrir_tableau_de_bord(self) -> None:
        if self.dossier is None:
            return
        try:
            donnees, chemin = societe.actualiser()
        except PermissionError as e:
            messagebox.showerror(TITRE, f"Fichier ouvert dans un autre programme :\n{e.filename or e}", parent=self.tk)
            return
        self._ouvrir(chemin)

    def _ajouter_journal(self) -> None:
        if self.dossier is None:
            return
        Journal(self.tk, on_valider=self._enregistrer_journal)

    def _enregistrer_journal(self, quand: date, categorie: str, evenement: str, lien: str,
                             montant: float | None) -> bool:
        try:
            societe.ajouter_au_journal(quand, categorie, evenement, lien, montant)
        except PermissionError:
            messagebox.showerror(TITRE, "societe.xlsx est ouvert dans Excel.\nFerme-le puis réessaie.", parent=self.tk)
            return False
        self._actualiser_societe()
        return True

    # ------------------------------------------------------------ dossier de travail

    def _premier_lancement(self) -> None:
        propose = installation.dossier_propose()
        if messagebox.askyesno(
                TITRE,
                "Bienvenue.\n\nReconsigliere a besoin d'un dossier de travail pour ranger tes relevés, "
                f"tes factures et les résultats.\n\nLe créer ici ?\n{propose}\n\n"
                "Réponds Non pour choisir un autre emplacement.", parent=self.tk):
            self._installer(propose)
        else:
            self._choisir()

    def _choisir(self) -> None:
        depart = self.dossier.parent if self.dossier else installation.dossier_propose().parent
        choix = filedialog.askdirectory(parent=self.tk, initialdir=str(depart), mustexist=True,
                                        title="Où installer le dossier de travail de Reconsigliere ?")
        if not choix:
            return
        cible = installation.resoudre(Path(choix))
        if not installation.est_installe(cible) and not messagebox.askyesno(
                TITRE, f"Reconsigliere va créer ses dossiers ici :\n\n{cible}\n\nContinuer ?", parent=self.tk):
            return
        self._installer(cible)

    def _installer(self, cible: Path) -> None:
        try:
            crees = installation.creer_dossiers(cible)
        except OSError as e:
            messagebox.showerror(TITRE, f"Impossible de créer les dossiers :\n{e}", parent=self.tk)
            return
        self._utiliser(cible)
        if crees:
            self._ecrire(f"Dossiers créés dans {cible}\n")
            installation.ouvrir(cible / "entrees")

    def _utiliser(self, cible: Path) -> None:
        installation.creer_dossiers(cible)
        self.dossier = Path(cible)
        config.definir_racine(cible)
        installation.memoriser(cible)
        self._actualiser()

    # ------------------------------------------------------------ état de l'interface

    def _actualiser(self) -> None:
        pret = self.dossier is not None
        self.lbl_dossier.configure(text=str(self.dossier) if pret else "Aucun dossier choisi")
        self.lbl_etat_dossier.configure(
            text="Les dossiers d'entrée et de sortie sont en place." if pret
            else "Choisis un emplacement : les dossiers d'entrée et de sortie y seront créés.")
        etat = "!disabled" if pret and not self.en_cours else "disabled"
        self.btn_lancer.state([etat])
        self.btn_importer.state([etat])
        self.btn_ouvrir_dossier.state(["!disabled" if pret else "disabled"])
        for b in self.boutons_dossiers:
            b.state(["!disabled" if pret else "disabled"])
        for cle, (_, chemin) in self.boutons_resultats.items():
            existe = pret and chemin(self.dossier).exists()
            self.widgets_resultats[cle].state(["!disabled" if existe else "disabled"])
        for b in self.boutons_societe:
            b.state(["!disabled" if pret else "disabled"])
        for b in self.boutons_exercices:
            b.state(["!disabled" if pret else "disabled"])
        self._onglet_change()
        self._actualiser_compteurs()

    def _actualiser_compteurs(self) -> None:
        for rel, lbl in self.compteurs.items():
            if self.dossier is None:
                lbl.configure(text="—")
                continue
            n = installation.compter_fichiers(self.dossier / rel)
            lbl.configure(text="vide" if n == 0 else f"{n} fichier{'s' if n > 1 else ''}")

    def _ouvrir(self, chemin: Path | None) -> None:
        if chemin is None:
            return
        if not Path(chemin).exists():
            messagebox.showinfo(TITRE, f"Introuvable pour l'instant :\n{chemin}", parent=self.tk)
            return
        try:
            installation.ouvrir(chemin)
        except OSError as e:
            messagebox.showerror(TITRE, f"Impossible d'ouvrir :\n{chemin}\n\n{e}", parent=self.tk)

    def _ecrire(self, texte: str, tag: str | None = None) -> None:
        self.journal.configure(state="normal")
        self.journal.insert("end", texte, tag)
        self.journal.see("end")
        self.journal.configure(state="disabled")

    # ------------------------------------------------------------ traitement

    def _lancer(self) -> None:
        if self.en_cours or self.dossier is None:
            return
        transactions = installation.compter_fichiers(self.dossier / "entrees" / "02_transactions_a_reconcilier")
        if transactions == 0:
            messagebox.showwarning(
                TITRE, "Le dossier « Transactions bancaires » est vide.\n\n"
                       "Dépose au moins un Excel ou CSV de transactions, puis relance.", parent=self.tk)
            return
        self.en_cours = True
        self.progression.configure(value=0)
        self.lbl_etape.configure(text="Démarrage…")
        self.journal.configure(state="normal")
        self.journal.delete("1.0", "end")
        self.journal.configure(state="disabled")
        self._actualiser()
        threading.Thread(target=self._traiter, daemon=True).start()

    def _traiter(self) -> None:
        from .__main__ import main  # import tardif : pandas se charge pendant que la fenêtre s'affiche
        try:
            resultat = main(log=lambda texte: self.messages.put(("log", texte)))
            self.messages.put(("fin", resultat))
        except PermissionError as e:
            self.messages.put(("erreur",
                               "Un fichier est ouvert dans un autre programme, probablement Excel.\n"
                               f"Ferme-le puis relance.\n\nDétail : {e.filename or e}"))
        except Exception:  # noqa: BLE001 - toute erreur doit apparaître dans la fenêtre
            self.messages.put(("erreur", traceback.format_exc()))

    def _lire_messages(self) -> None:
        try:
            while True:
                genre, contenu = self.messages.get_nowait()
                if genre == "log":
                    self._ecrire(contenu + "\n")
                    etape = re.match(r"(\d)/5 (.*)", contenu)
                    if etape:
                        self.progression.configure(value=int(etape.group(1)) - 1)
                        self.lbl_etape.configure(text=f"Étape {etape.group(1)} sur {NB_ETAPES} : {etape.group(2)}")
                elif genre == "fin":
                    self._terminer(contenu)
                elif genre == "fin_import":
                    self._terminer_import(contenu)
                elif genre == "choix":
                    page, proposition, reponse, evenement = contenu
                    reponse["type"] = self._demander_type(page, proposition)
                    evenement.set()
                elif genre == "erreur":
                    self.en_cours = False
                    self.lbl_etape.configure(text="Arrêté sur une erreur.")
                    self._ecrire("\n" + contenu + "\n", "erreur")
                    self._actualiser()
                    messagebox.showerror(TITRE, contenu.strip().splitlines()[-1] if "Traceback" in contenu
                                         else contenu, parent=self.tk)
        except queue.Empty:
            pass
        self.tk.after(100, self._lire_messages)

    def _terminer(self, resultat: dict) -> None:
        self.en_cours = False
        self.progression.configure(value=NB_ETAPES)
        self.lbl_etape.configure(text="Terminé.")
        statuts = resultat.get("statuts", {})
        total = sum(statuts.values())
        details = " · ".join(f"{s} : {n}" for s, n in sorted(statuts.items(), key=lambda x: -x[1]))
        self.lbl_resume.configure(
            text=f"{total} transaction(s). {details}. PDF sans transaction : {resultat.get('orphelins', 0)}.")
        self._actualiser()


    # ------------------------------------------------------------ import de documents

    def _importer(self) -> None:
        if self.en_cours or self.dossier is None:
            return
        if installation.compter_fichiers(self.dossier / "entrees" / "07_documents") == 0:
            messagebox.showwarning(
                TITRE, "Le dossier « Documents à importer » est vide.\n\n"
                       "Dépose un bilan, un grand livre, un plan comptable… (PDF, photo ou Excel), puis relance.",
                parent=self.tk)
            return
        self.en_cours = True
        self.progression.configure(mode="indeterminate")
        self.progression.start(12)
        self.lbl_etape.configure(text="Import des documents…")
        self.documents.lbl_etat.configure(text="Import en cours… le détail s'affiche dans le journal de l'onglet Réconciliation.")
        self._actualiser()
        threading.Thread(target=self._traiter_import, daemon=True).start()

    def _choisir_type(self, page, proposition):
        """Appelé depuis le fil de travail : la question est posée par la fenêtre, puis on attend."""
        reponse, evenement = {}, threading.Event()
        self.messages.put(("choix", (page, proposition, reponse, evenement)))
        evenement.wait()
        return reponse.get("type")

    def _traiter_import(self) -> None:
        from .importation import pipeline
        try:
            resultats = pipeline.importer_dossier(self.dossier, choisir=self._choisir_type,
                                                  log=lambda texte: self.messages.put(("log", texte)))
            self.messages.put(("fin_import", resultats))
        except PermissionError as e:
            self.messages.put(("erreur", "Un fichier est ouvert dans un autre programme, probablement Excel.\n"
                                         f"Ferme-le puis relance.\n\nDétail : {e.filename or e}"))
        except Exception:  # noqa: BLE001
            self.messages.put(("erreur", traceback.format_exc()))

    def _demander_type(self, page, proposition) -> str | None:
        from .importation.classement import LIBELLES
        fenetre = tk.Toplevel(self.tk)
        fenetre.title(f"{TITRE} : page {page.numero} à classer")
        fenetre.transient(self.tk)
        fenetre.grab_set()
        cadre = ttk.Frame(fenetre, padding=12)
        cadre.pack(fill="both", expand=True)
        ttk.Label(cadre, wraplength=520,
                  text=f"Je n'ai pas reconnu la page {page.numero}. Que contient-elle ?").pack(anchor="w")
        apercu = tk.Text(cadre, height=14, width=80, wrap="word", relief="flat", background="#f6f7f9")
        apercu.insert("1.0", page.texte[:1500])
        apercu.configure(state="disabled")
        apercu.pack(fill="both", expand=True, pady=8)
        choix = tk.StringVar(value=LIBELLES.get(proposition or "autre", "Autre"))
        ttk.Combobox(cadre, textvariable=choix, values=list(LIBELLES.values()), state="readonly").pack(anchor="w")
        resultat = {"type": None}

        def valider():
            resultat["type"] = next(k for k, v in LIBELLES.items() if v == choix.get())
            fenetre.destroy()
        boutons = ttk.Frame(cadre)
        boutons.pack(anchor="e", pady=(10, 0))
        ttk.Button(boutons, text="Passer", command=fenetre.destroy).pack(side="left", padx=(0, 6))
        ttk.Button(boutons, text="Valider", command=valider).pack(side="left")
        self.tk.wait_window(fenetre)
        return resultat["type"]

    def _onglet_change(self) -> None:
        """Surligne le bouton de l'onglet affiché et l'actualise (repéré par son cadre, pas par sa position)."""
        courant = self.onglets.select()
        self.v_onglet.set(courant)
        if self.dossier is None or not hasattr(self, "actualisations"):
            return
        for cle, cadre in self.cadres.items():
            if str(cadre.master) == courant and cle in self.actualisations:
                self.actualisations[cle]()
                return

    def _terminer_import(self, resultats: list[dict]) -> None:
        self.en_cours = False
        self.progression.stop()
        self.progression.configure(mode="determinate", value=NB_ETAPES)
        self.lbl_etape.configure(text="Import terminé.")
        if not resultats:
            texte = "Aucun nouveau document : ceux du dossier ont déjà été importés."
        else:
            alertes = sum(1 for r in resultats for c in r["controles"] if c["resultat"] != "ok")
            ia_pages = sum(r["appels_ia"] for r in resultats)
            texte = (f"{len(resultats)} document(s) importé(s). Pages envoyées à l'IA : {ia_pages}. "
                     f"Points à vérifier : {alertes}. Le détail est dans l'onglet Documents.")
        self.lbl_resume.configure(text=texte)
        self._actualiser()
        self.documents.actualiser()
        self.documents.lbl_etat.configure(text=texte)

    def _reglages_ia(self) -> None:
        from .importation import ia
        reglages = installation.lire_reglages()
        fenetre = tk.Toplevel(self.tk)
        fenetre.title(f"{TITRE} : réglages IA")
        fenetre.transient(self.tk)
        fenetre.grab_set()
        cadre = ttk.Frame(fenetre, padding=12)
        cadre.pack(fill="both", expand=True)
        ttk.Label(cadre, wraplength=460, text=(
            "L'IA ne sert qu'aux pages que Reconsigliere n'a pas reconnues seul. Elle reçoit un extrait "
            "de 2000 caractères au plus. Sans clé, ces pages te sont demandées.")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(cadre, text="Clé API Anthropic").grid(row=1, column=0, sticky="w", pady=(10, 0))
        cle = tk.StringVar(value=reglages.get("cle_api_anthropic", ""))
        ttk.Entry(cadre, textvariable=cle, show="•", width=46).grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Label(cadre, text="Modèle").grid(row=2, column=0, sticky="w", pady=(6, 0))
        modele = tk.StringVar(value=reglages.get("modele_ia", ia.MODELE_DEFAUT))
        ttk.Combobox(cadre, textvariable=modele, values=list(ia.MODELES), state="readonly",
                     width=12).grid(row=2, column=1, sticky="w", pady=(6, 0))

        def enregistrer():
            installation.ecrire_reglage("cle_api_anthropic", cle.get().strip())
            installation.ecrire_reglage("modele_ia", modele.get())
            fenetre.destroy()
        ttk.Button(cadre, text="Enregistrer", command=enregistrer).grid(row=3, column=1, sticky="e", pady=(12, 0))


class Journal(tk.Toplevel):
    """Petite fenêtre pour ajouter un événement au journal de la société."""

    def __init__(self, parent: tk.Tk, on_valider) -> None:
        super().__init__(parent)
        self.title("Ajouter au journal")
        self.transient(parent)
        self.resizable(False, False)
        self.on_valider = on_valider
        cadre = ttk.Frame(self, padding=14)
        cadre.pack(fill="both", expand=True)
        self.v_date = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        self.v_categorie = tk.StringVar(value=societe.CATEGORIES_JOURNAL[0])
        self.v_evenement = tk.StringVar()
        self.v_lien = tk.StringVar()
        self.v_montant = tk.StringVar()
        champs = [
            ("Date (JJ.MM.AAAA)", ttk.Entry(cadre, textvariable=self.v_date, width=14)),
            ("Catégorie", ttk.Combobox(cadre, textvariable=self.v_categorie, values=societe.CATEGORIES_JOURNAL, width=18)),
            ("Événement", ttk.Entry(cadre, textvariable=self.v_evenement, width=50)),
            ("Lien (brevet, projet, client…)", ttk.Entry(cadre, textvariable=self.v_lien, width=30)),
            ("Montant CHF (facultatif)", ttk.Entry(cadre, textvariable=self.v_montant, width=14)),
        ]
        for i, (texte, champ) in enumerate(champs):
            ttk.Label(cadre, text=texte).grid(row=i, column=0, sticky="w", pady=3, padx=(0, 10))
            champ.grid(row=i, column=1, sticky="w", pady=3)
        boutons = ttk.Frame(cadre)
        boutons.grid(row=len(champs), column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(boutons, text="Annuler", command=self.destroy).pack(side="right")
        ttk.Button(boutons, text="Enregistrer", command=self._valider).pack(side="right", padx=(0, 6))
        champs[2][1].focus_set()
        self.bind("<Return>", lambda _e: self._valider())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _valider(self) -> None:
        quand = societe._date(self.v_date.get())
        if quand is None:
            messagebox.showwarning(TITRE, "Date invalide : écris-la sous la forme 26.11.2026.", parent=self)
            return
        evenement = self.v_evenement.get().strip()
        if not evenement:
            messagebox.showwarning(TITRE, "Décris l'événement.", parent=self)
            return
        montant_texte = self.v_montant.get().strip()
        montant = societe._montant(montant_texte) if montant_texte else None
        if self.on_valider(quand, self.v_categorie.get().strip(), evenement, self.v_lien.get().strip(), montant):
            self.destroy()


class Changement(tk.Toplevel):
    """Demande de changement : ajout, modification ou retrait d'un élément d'une liste du référentiel."""

    def __init__(self, parent: tk.Tk, annee: int, on_fin) -> None:
        super().__init__(parent)
        self.title(f"Demander un changement — exercice {annee}")
        self.transient(parent)
        self.annee, self.on_fin = annee, on_fin
        self.listes = exercices.lire(annee)
        self.noms = {v: k for k, v in exercices.NOMS_LISTES.items()}
        cadre = ttk.Frame(self, padding=14)
        cadre.pack(fill="both", expand=True)
        self.v_liste = tk.StringVar(value=exercices.NOMS_LISTES["Brevets"])
        self.v_action = tk.StringVar(value="modification")
        self.v_cle = tk.StringVar()
        self.v_date = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        self.v_motif = tk.StringVar()
        ttk.Label(cadre, text="Liste").grid(row=0, column=0, sticky="w", pady=3)
        cb = ttk.Combobox(cadre, textvariable=self.v_liste, values=list(self.noms), state="readonly", width=20)
        cb.grid(row=0, column=1, sticky="w")
        ttk.Label(cadre, text="Action").grid(row=1, column=0, sticky="w", pady=3)
        ca = ttk.Combobox(cadre, textvariable=self.v_action, values=exercices.ACTIONS, state="readonly", width=20)
        ca.grid(row=1, column=1, sticky="w")
        ttk.Label(cadre, text="Élément").grid(row=2, column=0, sticky="w", pady=3)
        self.cb_cle = ttk.Combobox(cadre, textvariable=self.v_cle, width=40)
        self.cb_cle.grid(row=2, column=1, sticky="w")
        self.champs = ttk.Labelframe(cadre, text="Valeurs", padding=8)
        self.champs.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 8))
        ttk.Label(cadre, text="Date du changement").grid(row=4, column=0, sticky="w", pady=3)
        ttk.Entry(cadre, textvariable=self.v_date, width=14).grid(row=4, column=1, sticky="w")
        ttk.Label(cadre, text="Motif").grid(row=5, column=0, sticky="w", pady=3)
        ttk.Entry(cadre, textvariable=self.v_motif, width=50).grid(row=5, column=1, sticky="w")
        boutons = ttk.Frame(cadre)
        boutons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(boutons, text="Fermer", command=self.destroy).pack(side="right")
        ttk.Button(boutons, text="Enregistrer", command=self._valider).pack(side="right", padx=(0, 6))
        self.v_valeurs: dict[str, tk.StringVar] = {}
        self.entrees: list[ttk.Entry] = []
        cb.bind("<<ComboboxSelected>>", lambda _e: self._rafraichir(True))
        ca.bind("<<ComboboxSelected>>", lambda _e: self._rafraichir(False))
        self.cb_cle.bind("<<ComboboxSelected>>", lambda _e: self._remplir())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._rafraichir(True)

    def _liste(self) -> str:
        return self.noms[self.v_liste.get()]

    def _rafraichir(self, liste_changee: bool) -> None:
        liste = self._liste()
        cle, colonnes = exercices.LISTES[liste]
        self.cb_cle.configure(values=[str(l.get(cle)) for l in self.listes[liste] if l.get(cle) not in (None, "")])
        if liste_changee:
            self.v_cle.set("")
            for w in self.champs.winfo_children():
                w.destroy()
            self.v_valeurs = {}
            self.entrees = []
            for i, col in enumerate(c for c in colonnes if c != cle):
                ttk.Label(self.champs, text=col).grid(row=i, column=0, sticky="w", padx=(0, 10), pady=1)
                v = tk.StringVar()
                e = ttk.Entry(self.champs, textvariable=v, width=44)
                e.grid(row=i, column=1, sticky="w", pady=1)
                self.v_valeurs[col] = v
                self.entrees.append(e)
        retrait = self.v_action.get() == "retrait"
        for e in self.entrees:
            e.state(["disabled" if retrait else "!disabled"])
        self._remplir()

    def _remplir(self) -> None:
        liste = self._liste()
        cle, _ = exercices.LISTES[liste]
        ligne = next((l for l in self.listes[liste] if str(l.get(cle)) == self.v_cle.get()), None)
        self._origine = {}
        for col, v in self.v_valeurs.items():
            valeur = "" if ligne is None or ligne.get(col) is None else str(ligne.get(col))
            if self.v_action.get() == "ajout":
                valeur = ""
            v.set(valeur)
            self._origine[col] = valeur

    def _valider(self) -> None:
        quand = societe._date(self.v_date.get())
        if quand is None:
            messagebox.showwarning(TITRE, "Date invalide : écris-la sous la forme 15.03.2025.", parent=self)
            return
        action = self.v_action.get()
        valeurs = {}
        if action != "retrait":
            for col, v in self.v_valeurs.items():
                texte = v.get().strip()
                if action == "ajout" and texte or action == "modification" and texte != self._origine.get(col, ""):
                    valeurs[col] = texte or None
        try:
            exercices.demander_changement(self.annee, action, self._liste(), self.v_cle.get(), valeurs,
                                          self.v_motif.get(), quand)
        except (ValueError, exercices.ExerciceVerrouille) as e:
            messagebox.showwarning(TITRE, str(e), parent=self)
            return
        except PermissionError:
            messagebox.showerror(TITRE, "Le référentiel est ouvert dans Excel. Ferme-le puis réessaie.", parent=self)
            return
        self.listes = exercices.lire(self.annee)
        self.v_motif.set("")
        self._rafraichir(False)
        self.on_fin()
        messagebox.showinfo(TITRE, "Changement enregistré.", parent=self)


class Ecarts(tk.Toplevel):
    """Liste des écarts entre deux exercices."""

    def __init__(self, parent: tk.Tk, annee: int, reference: int | None, lignes, on_appliquer=None) -> None:
        super().__init__(parent)
        suggestions = on_appliquer is not None
        self.title(f"Suggestions pour {annee}" if suggestions else f"Écarts entre {reference} et {annee}")
        self.transient(parent)
        self.geometry("860x460")
        self.lignes, self.on_appliquer = list(lignes), on_appliquer
        cadre = ttk.Frame(self, padding=12)
        cadre.pack(fill="both", expand=True)
        entete = (f"{len(lignes)} différence(s) entre les fichiers déposés et le référentiel {annee}. "
                  "Sélectionne celles à appliquer (Ctrl ou Maj pour plusieurs)." if suggestions
                  else f"{len(lignes)} écart(s) entre {reference} et {annee}.")
        ttk.Label(cadre, text=entete, style="Chemin.TLabel", wraplength=820).pack(anchor="w", pady=(0, 8))
        colonnes = ("liste", "cle", "nature", "champ", "avant", "apres")
        self.arbre = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                  selectmode="extended" if suggestions else "browse")
        avant, apres = ("Référentiel", "Fichiers") if suggestions else (f"En {reference}", f"En {annee}")
        for col, texte, largeur in [("liste", "Liste", 100), ("cle", "Élément", 120), ("nature", "Nature", 95),
                                    ("champ", "Champ", 85), ("avant", avant, 210), ("apres", apres, 210)]:
            self.arbre.heading(col, text=texte)
            self.arbre.column(col, width=largeur, anchor="w")
        self._remplir()
        self.arbre.pack(fill="both", expand=True)
        bas = ttk.Frame(cadre)
        bas.pack(fill="x", pady=(8, 0))
        ttk.Button(bas, text="Fermer", command=self.destroy).pack(side="right")
        if suggestions:
            self.v_motif = tk.StringVar(value="Selon les fichiers déposés")
            ttk.Label(bas, text="Motif :").pack(side="left")
            ttk.Entry(bas, textvariable=self.v_motif, width=40).pack(side="left", padx=(6, 6))
            ttk.Button(bas, text="Appliquer la sélection", command=self._appliquer).pack(side="left")

    def _remplir(self) -> None:
        self.arbre.delete(*self.arbre.get_children())
        for i, e in enumerate(self.lignes):
            self.arbre.insert("", "end", iid=str(i), values=(
                exercices.NOMS_LISTES.get(e.liste, e.liste), e.cle, e.nature, e.champ,
                "" if e.avant is None else e.avant, "" if e.apres is None else e.apres))

    def _appliquer(self) -> None:
        choix = [self.lignes[int(i)] for i in self.arbre.selection()]
        if not choix:
            messagebox.showinfo(TITRE, "Sélectionne au moins une ligne.", parent=self)
            return
        if not self.v_motif.get().strip():
            messagebox.showwarning(TITRE, "Indique un motif.", parent=self)
            return
        if self.on_appliquer(choix, self.v_motif.get()):
            self.lignes = [e for e in self.lignes if e not in choix]
            self._remplir()


def _nettete_windows() -> None:
    """Évite une fenêtre floue sur les écrans haute résolution de Windows."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001
            pass


def lancer() -> None:
    _nettete_windows()
    racine = tk.Tk()
    Fenetre(racine)
    racine.mainloop()


if __name__ == "__main__":
    lancer()
