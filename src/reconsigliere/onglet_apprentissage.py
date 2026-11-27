"""Onglet « Apprentissage » : ce que le programme a appris de tes corrections de compte.

Les données viennent de sorties/apprentissage.xlsx, écrit par chaque réconciliation (voir apprentissage.py).
Les boutons écrivent dans mes_corrections.xlsx (annuler, rétablir) ou dans le référentiel de l'exercice ouvert (reporter).
"""

from __future__ import annotations

from tkinter import messagebox, ttk

from . import apprentissage, config, corrections, exercices

COLONNES_REGLES = [("partenaire", "Partenaire", 140), ("compte", "Compte", 110), ("condition", "Condition", 220),
                   ("etat", "État", 105), ("fiabilite", "Fiabilité", 170), ("compte_reference", "Référentiel", 90),
                   ("explication", "Pourquoi", 300)]
COLONNES_ALERTES = [("niveau", "Niveau", 80), ("partenaire", "Partenaire", 150), ("message", "Message", 880)]
COULEURS = {apprentissage.ACTIVE: "#1f8a4c", apprentissage.CONDITIONNELLE: "#1f5f8a",
            apprentissage.EN_OBSERVATION: "#667085", apprentissage.SUSPENDUE: "#b35900",
            apprentissage.ANNULEE: "#98a2b3"}
EXPLICATION = (
    "Corrige le compte d'une transaction dans mes_corrections.xlsx (feuille transactions, colonne compte). "
    "Après {seuil} corrections identiques pour un partenaire, le programme applique seul ce compte aux transactions "
    "suivantes. Si tes corrections divergent, il cherche ce qui les sépare (date, mot du libellé, montant) ; "
    "s'il ne trouve pas, il suspend la règle et te prévient. Tout est recalculé à chaque réconciliation : "
    "supprimer une correction retire son effet.")


def _resume(r: dict) -> str:
    if not r:
        return ""
    n = lambda cle: int(r.get(cle) or 0)  # noqa: E731
    return (f"{n('corrections')} correction(s) de compte pour {n('partenaires')} partenaire(s) · "
            f"{n('actives')} règle(s) active(s) · {n('conditionnelles')} conditionnelle(s) · "
            f"{n('en_observation')} en observation · {n('suspendues')} suspendue(s) · {n('annulees')} annulée(s) · "
            f"appliquées à {n('appliquees')} transaction(s) · "
            f"{n('corrigees_par_rapport_au_referentiel')} proposition(s) du référentiel corrigée(s)")


class OngletApprentissage:
    def __init__(self, parent, fenetre) -> None:
        self.f = fenetre
        self.regles: dict[str, dict] = {}

        haut = ttk.Frame(parent)
        haut.pack(fill="x")
        ttk.Button(haut, text="Mes corrections", command=lambda: fenetre._ouvrir(
            config.FICHIER_CORRECTIONS if fenetre.dossier else None)).pack(side="left")
        ttk.Button(haut, text="Détail (Excel)", command=lambda: fenetre._ouvrir(
            apprentissage.fichier_sortie() if fenetre.dossier else None)).pack(side="left", padx=(8, 0))
        self.lbl_etat = ttk.Label(haut, style="Doux.TLabel", text="")
        self.lbl_etat.pack(side="left", padx=(16, 0))
        self.lbl_resume = ttk.Label(parent, text="", wraplength=840, justify="left", style="Chemin.TLabel")
        self.lbl_resume.pack(anchor="w", pady=(8, 2))
        self.lbl_aide = ttk.Label(parent, text=EXPLICATION.format(seuil=config.SEUIL_REGLE), style="Doux.TLabel",
                                  wraplength=840, justify="left")
        self.lbl_aide.pack(anchor="w", pady=(0, 8))

        cadre_regles = fenetre._section(parent, "Règles apprises", extensible=True)
        self.arbre_regles = self._tableau(cadre_regles, COLONNES_REGLES, hauteur=6)
        for etat, couleur in COULEURS.items():
            self.arbre_regles.tag_configure(etat, foreground=couleur)
        self.lbl_regle = ttk.Label(cadre_regles, text="Clique sur une règle pour voir son détail.", style="Doux.TLabel",
                                   wraplength=840, justify="left")
        self.lbl_regle.pack(anchor="w", pady=(6, 0))
        self.arbre_regles.bind("<<TreeviewSelect>>", lambda _e: self._detail_regle())
        boutons = ttk.Frame(cadre_regles)
        boutons.pack(anchor="w", pady=(6, 0))
        ttk.Button(boutons, text="Annuler la règle", command=self._annuler).pack(side="left")
        ttk.Button(boutons, text="Rétablir la règle", command=self._retablir).pack(side="left", padx=6)
        ttk.Button(boutons, text="Reporter dans l'exercice ouvert", command=self._reporter).pack(side="left")

        cadre_alertes = fenetre._section(parent, "Alertes", extensible=True)
        self.arbre_alertes = self._tableau(cadre_alertes, COLONNES_ALERTES, hauteur=4)
        self.arbre_alertes.tag_configure(apprentissage.ATTENTION, foreground="#b35900")
        self.lbl_alerte = ttk.Label(cadre_alertes, text="Clique sur une alerte pour la lire en entier.", style="Doux.TLabel",
                                    wraplength=840, justify="left")
        self.lbl_alerte.pack(anchor="w", pady=(6, 0))
        self.arbre_alertes.bind("<<TreeviewSelect>>", lambda _e: self._detail_alerte())

    def _detail_regle(self) -> None:
        choix = self.arbre_regles.selection()
        r = self.regles.get(choix[0]) if choix else None
        if not r:
            return
        morceaux = [f"{r.get('partenaire')} → {r.get('compte')}", r.get("condition") or "", f"état : {r.get('etat')}",
                    f"fiabilité : {r.get('fiabilite')}", f"référentiel : {r.get('compte_reference') or 'aucun'}",
                    r.get("explication") or ""]
        self.lbl_regle.configure(text=" · ".join(m for m in morceaux if m), style="TLabel")

    def _detail_alerte(self) -> None:
        choix = self.arbre_alertes.selection()
        if choix:
            self.lbl_alerte.configure(text=self.arbre_alertes.item(choix[0], "values")[2], style="TLabel")

    def _tableau(self, parent, colonnes, hauteur: int) -> ttk.Treeview:
        cadre = ttk.Frame(parent)
        cadre.pack(fill="both", expand=True)
        t = ttk.Treeview(cadre, columns=[c for c, _, _ in colonnes], show="headings", height=hauteur)
        for cle, titre, largeur in colonnes:
            t.heading(cle, text=titre)
            t.column(cle, width=largeur, anchor="w", stretch=cle in ("explication", "message"))
        vy = ttk.Scrollbar(cadre, orient="vertical", command=t.yview)
        vx = ttk.Scrollbar(cadre, orient="horizontal", command=t.xview)
        t.configure(yscrollcommand=vy.set, xscrollcommand=vx.set)
        t.grid(row=0, column=0, sticky="nsew")
        vy.grid(row=0, column=1, sticky="ns")
        vx.grid(row=1, column=0, sticky="ew")
        cadre.rowconfigure(0, weight=1)
        cadre.columnconfigure(0, weight=1)
        return t

    # ------------------------------------------------------------ affichage

    def actualiser(self) -> None:
        for arbre in (self.arbre_regles, self.arbre_alertes):
            arbre.delete(*arbre.get_children())
        self.regles.clear()
        self.lbl_regle.configure(text="Clique sur une règle pour voir son détail.", style="Doux.TLabel")
        self.lbl_alerte.configure(text="Clique sur une alerte pour la lire en entier.", style="Doux.TLabel")
        if self.f.dossier is None:
            return
        try:
            donnees = apprentissage.lire_sortie()
        except Exception as e:  # noqa: BLE001 - fichier abîmé ou ouvert : l'onglet reste utilisable
            self.lbl_etat.configure(text=f"Lecture impossible de sorties/apprentissage.xlsx : {e}")
            return
        if donnees is None:
            self.lbl_etat.configure(text="Lance une réconciliation pour calculer ce que le programme a appris.")
            self.lbl_resume.configure(text="")
            return
        self.lbl_etat.configure(text=f"Calculé le {donnees['calcule_le']} (relance la réconciliation pour mettre à jour)")
        self.lbl_resume.configure(text=_resume(donnees["resume"]))
        for r in donnees["regles"]:
            ident = self.arbre_regles.insert("", "end", values=[r.get(c) or "" for c, _, _ in COLONNES_REGLES],
                                             tags=(r.get("etat") or "",))
            self.regles[ident] = r
        for a in donnees["alertes"]:
            self.arbre_alertes.insert("", "end", values=[a.get(c) or "" for c, _, _ in COLONNES_ALERTES],
                                      tags=(a.get("niveau") or "",))

    def _choisie(self) -> tuple[str, dict] | None:
        choix = self.arbre_regles.selection()
        if not choix:
            messagebox.showinfo("Apprentissage", "Choisis d'abord une règle dans la liste.", parent=self.f.tk)
            return None
        return choix[0], self.regles[choix[0]]

    def _marquer(self, ident: str, texte: str) -> None:
        valeurs = list(self.arbre_regles.item(ident, "values"))
        valeurs[[c for c, _, _ in COLONNES_REGLES].index("etat")] = texte
        self.arbre_regles.item(ident, values=valeurs)

    # ------------------------------------------------------------ actions

    def _annuler(self) -> None:
        choisie = self._choisie()
        if choisie is None:
            return
        ident, r = choisie
        try:
            corrections.annuler_regle(str(r["partenaire"]), str(r["compte"]))
        except PermissionError:
            messagebox.showerror("Apprentissage", "Ferme mes_corrections.xlsx dans Excel, puis réessaie.", parent=self.f.tk)
            return
        self._marquer(ident, "annulée au prochain lancement")

    def _retablir(self) -> None:
        choisie = self._choisie()
        if choisie is None:
            return
        ident, r = choisie
        try:
            corrections.retablir_regle(str(r["partenaire"]), str(r["compte"]))
        except PermissionError:
            messagebox.showerror("Apprentissage", "Ferme mes_corrections.xlsx dans Excel, puis réessaie.", parent=self.f.tk)
            return
        self._marquer(ident, "rétablie au prochain lancement")

    def _reporter(self) -> None:
        choisie = self._choisie()
        if choisie is None:
            return
        _ident, r = choisie
        compte = str(r["compte"])
        if r.get("etat") != apprentissage.ACTIVE or "/" in compte:
            messagebox.showinfo("Apprentissage", "Seule une règle active à un seul compte peut être reportée dans le "
                                                 "référentiel. Une règle conditionnelle reste dans l'apprentissage.",
                                parent=self.f.tk)
            return
        annee = exercices.exercice_courant()
        if annee is None:
            messagebox.showinfo("Apprentissage", "Aucun exercice construit : construis-le d'abord dans l'Assistant société.",
                                parent=self.f.tk)
            return
        if not messagebox.askyesno("Apprentissage", f"Inscrire dans le référentiel {annee} : {r['partenaire']} → {compte} ?\n"
                                                    "Le changement est daté et motivé dans l'onglet Changements.",
                                   parent=self.f.tk):
            return
        try:
            apprentissage.reporter(str(r["partenaire"]), compte, int(r.get("corrections") or 0), annee)
        except (ValueError, exercices.ExerciceVerrouille, exercices.ExerciceAbsent, PermissionError) as e:
            messagebox.showerror("Apprentissage", str(e), parent=self.f.tk)
            return
        messagebox.showinfo("Apprentissage", f"Reporté dans le référentiel {annee}.", parent=self.f.tk)


def construire(parent, fenetre) -> OngletApprentissage:
    return OngletApprentissage(parent, fenetre)
