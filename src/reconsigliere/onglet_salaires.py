"""Onglet « Salaires » : réconciliation des salaires par exercice et par employé, pour la fiduciaire.

1. choisir l'exercice ; 2. lire le classeur de paie (met la fiche à jour) ; 3. générer l'Excel, l'ouvrir ou l'enregistrer ailleurs.
Le tableau montre la synthèse de l'exercice et, en dessous, les restes de l'année précédente.
"""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import config, installation, salaires
from .salaires import fiche, reconciliation

TITRE = "Salaires"
COLONNES = [("employe", "Employé", 220), ("du", "Dû", 110), ("paye", "Payé dans l'année", 120),
            ("reporte", "Reporté", 125), ("paye_suivant", "Payé l'année suivante", 125), ("ecart", "Écart", 95)]
COLONNES_RESTES = [("employe", "Employé", 230), ("reporte", "Reporté", 140), ("paye", "Payé", 125),
                   ("ecart", "Écart", 95)]


def _chf(x) -> str:
    return f"{x:,.2f}".replace(",", "'") if isinstance(x, (int, float)) else ""


class OngletSalaires:
    def __init__(self, parent, fenetre) -> None:
        self.f = fenetre
        self.resultat: dict | None = None

        s1 = fenetre._section(parent, "1. Année et classeur de paie")
        ligne = ttk.Frame(s1)
        ligne.pack(fill="x")
        ttk.Label(ligne, text="Année").pack(side="left")
        self.choix = ttk.Combobox(ligne, state="readonly", width=7)
        self.choix.pack(side="left", padx=(6, 12))
        self.choix.bind("<<ComboboxSelected>>", lambda _e: self._afficher())
        ttk.Button(ligne, text="Lire le classeur de paie", command=self._lire).pack(side="left")
        ttk.Button(ligne, text="Ouvrir la fiche", command=self._ouvrir_fiche).pack(side="left", padx=(8, 0))
        ttk.Button(ligne, text="Ouvrir le dossier",
                   command=lambda: fenetre._ouvrir(config.DOSSIER_SALAIRES if fenetre.dossier else None)
                   ).pack(side="left", padx=(8, 0))
        self.lbl_lecture = ttk.Label(s1, style="Doux.TLabel", wraplength=840, justify="left",
                                     text="Dépose ton classeur de paie (forme du classeur 2025) dans entrees › 08_salaires, "
                                          "puis clique sur « Lire le classeur de paie ».")
        self.lbl_lecture.pack(anchor="w", pady=(6, 0))

        s2 = fenetre._section(parent, "2. Excel pour la fiduciaire")
        ttk.Button(s2, text="Générer", style="Grand.TButton", command=self._generer).pack(side="left")
        ttk.Button(s2, text="Ouvrir", command=self._ouvrir_resultat).pack(side="left", padx=(8, 0))
        ttk.Button(s2, text="Enregistrer sous…", command=self._enregistrer_sous).pack(side="left", padx=(8, 0))
        self.lbl_resultat = ttk.Label(s2, style="Doux.TLabel", text="", wraplength=420, justify="left")
        self.lbl_resultat.pack(side="left", padx=(12, 0))

        self.lbl_resume = ttk.Label(parent, style="Chemin.TLabel", text="", wraplength=880, justify="left")
        self.lbl_resume.pack(anchor="w", pady=(0, 6))
        self.cadre_synthese = fenetre._section(parent, "Synthèse de l'année", extensible=True)
        self.arbre = self._tableau(self.cadre_synthese, COLONNES, 11)
        self.cadre_restes = fenetre._section(parent, "Restes de l'année précédente")
        self.arbre_restes = self._tableau(self.cadre_restes, COLONNES_RESTES, 5)

    def _tableau(self, parent, colonnes, hauteur: int) -> ttk.Treeview:
        cadre = ttk.Frame(parent)
        cadre.pack(fill="both", expand=True)
        t = ttk.Treeview(cadre, columns=[c for c, _, _ in colonnes], show="headings", height=hauteur)
        for cle, titre, largeur in colonnes:
            t.heading(cle, text=titre)
            t.column(cle, width=largeur, anchor="w" if cle == "employe" else "e", stretch=cle == "employe")
        t.tag_configure("ecart", foreground="#b35900")
        t.tag_configure("total", font=("Segoe UI", 9, "bold"))
        vy = ttk.Scrollbar(cadre, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=vy.set)
        t.grid(row=0, column=0, sticky="nsew")
        vy.grid(row=0, column=1, sticky="ns")
        cadre.rowconfigure(0, weight=1)
        cadre.columnconfigure(0, weight=1)
        return t

    # ------------------------------------------------------------ données

    def _annee(self) -> int | None:
        v = self.choix.get()
        return int(v) if v.isdigit() else None

    def actualiser(self) -> None:
        if self.f.dossier is None:
            return
        try:
            annees = salaires.exercices_disponibles()
        except OSError:
            annees = []
        courant = self._annee()
        self.choix.configure(values=[str(a) for a in annees])
        if annees:
            self.choix.set(str(courant if courant in annees else annees[-1]))
        else:
            self.choix.set("")
            self.lbl_lecture.configure(text="Aucun classeur de paie ni fiche pour l'instant : dépose ton classeur de paie "
                                            "(forme du classeur 2025) dans entrees › 08_salaires.")
        self._afficher()

    def _afficher(self) -> None:
        for arbre in (self.arbre, self.arbre_restes):
            arbre.delete(*arbre.get_children())
        self.cadre_restes.pack_forget()
        self.lbl_resume.configure(text="")
        annee = self._annee()
        if annee is None:
            return
        try:
            fiche_n = fiche.lire(annee)
            if fiche_n is None:
                self.lbl_resume.configure(text=f"Pas encore de fiche {annee} : clique sur « Lire le classeur de paie ».")
                return
            r = reconciliation.resume(annee, fiche_n, fiche.lire(annee - 1), fiche.lire(annee + 1))
        except Exception as e:  # noqa: BLE001 - fiche abîmée ou ouverte : l'onglet reste utilisable
            self.lbl_resume.configure(text=f"Lecture impossible de la fiche {annee} : {e}")
            return
        self.resultat = r
        t = r["total"]
        self.lbl_resume.configure(text=(
            f"Reste à régler sur {annee} : {_chf(t['ecart'])} CHF · {len(r['points'])} point(s) à vérifier "
            f"(feuille « Points à vérifier » de l'Excel)"))
        self.cadre_synthese.configure(text=f"Synthèse {annee} (orange : écart à vérifier)")
        for c, titre in (("paye", f"Payé en {annee}"), ("reporte", f"Reporté à {annee + 1}"),
                         ("paye_suivant", f"Payé en {annee + 1}"), ("du", f"Dû {annee}")):
            self.arbre.heading(c, text=titre)
        for ligne in r["lignes"]:
            self.arbre.insert("", "end", values=[ligne["employe"]] + [_chf(ligne[c]) for c, _, _ in COLONNES[1:]],
                              tags=("ecart",) if ligne["ecart"] else ())
        self.arbre.configure(height=min(len(r["lignes"]) + 1, 11))
        self.arbre.insert("", "end", values=["Total"] + [_chf(t[c]) for c, _, _ in COLONNES[1:]], tags=("total",))
        if r["restes_prec"] is not None:
            self.cadre_restes.pack(fill="x", pady=(0, 10))
            self.cadre_restes.configure(text=f"Restes {annee - 1} payés en {annee}")
            self.arbre_restes.heading("reporte", text=f"Reporté de {annee - 1}")
            self.arbre_restes.heading("paye", text=f"Payé en {annee}")
            for x in r["restes_prec"]:
                self.arbre_restes.insert("", "end", values=[x["employe"], _chf(x["reporte"]), _chf(x["paye"]),
                                                            _chf(x["ecart"])], tags=("ecart",) if x["ecart"] else ())

    # ------------------------------------------------------------ boutons

    def _exige(self) -> int | None:
        if self.f.dossier is None:
            messagebox.showinfo(TITRE, "Choisis d'abord le dossier de travail (onglet Réconciliation).", parent=self.f.tk)
            return None
        annee = self._annee()
        if annee is None:
            messagebox.showinfo(TITRE, "Dépose ton classeur de paie (forme du classeur 2025) dans entrees › 08_salaires, "
                                       "puis reviens sur cet onglet.", parent=self.f.tk)
        return annee

    def _lire(self) -> None:
        annee = self._exige()
        if annee is None:
            return
        try:
            b = salaires.lire_classeur(annee)
        except (salaires.ClasseurAbsent, salaires.FormatInconnu, salaires.FichierOuvert) as e:
            messagebox.showerror(TITRE, str(e), parent=self.f.tk)
            return
        texte = (f"{Path(b['classeur']).name} lu : {b['ajoutes']} virement(s) nouveau(x), {b['retires']} retiré(s), "
                 f"{b['gardees']} correction(s) gardée(s), {b['manuels']} ligne(s) ajoutée(s) à la main.")
        if b["controles"]:
            texte += f" {len(b['controles'])} écart(s) avec « Versé selon PAYE » : voir les points à vérifier."
        self.lbl_lecture.configure(text=texte)
        self._afficher()

    def _generer(self) -> None:
        annee = self._exige()
        if annee is None:
            return
        try:
            chemin, _ = salaires.generer(annee)
        except (salaires.ClasseurAbsent, salaires.FormatInconnu, salaires.FichierOuvert) as e:
            messagebox.showerror(TITRE, str(e), parent=self.f.tk)
            return
        self.lbl_resultat.configure(text=f"{chemin.name} écrit le {date.today():%d.%m.%Y}.")
        self._afficher()

    def _ouvrir_fiche(self) -> None:
        annee = self._annee()
        self.f._ouvrir(fiche.chemin_fiche(annee) if annee and self.f.dossier else None)

    def _ouvrir_resultat(self) -> None:
        annee = self._annee()
        self.f._ouvrir(reconciliation.chemin_sortie(annee) if annee and self.f.dossier else None)

    def _enregistrer_sous(self) -> None:
        annee = self._exige()
        if annee is None:
            return
        source = reconciliation.chemin_sortie(annee)
        if not source.exists():
            messagebox.showinfo(TITRE, "Clique d'abord sur « Générer ».", parent=self.f.tk)
            return
        cible = filedialog.asksaveasfilename(parent=self.f.tk, title="Enregistrer l'Excel de réconciliation",
                                             initialfile=source.name, defaultextension=".xlsx",
                                             filetypes=[("Classeur Excel", "*.xlsx")])
        if not cible:
            return
        try:
            shutil.copy2(source, cible)
        except PermissionError:
            messagebox.showerror(TITRE, f"Ferme {Path(cible).name} dans Excel, puis recommence.", parent=self.f.tk)
            return
        except OSError as e:
            messagebox.showerror(TITRE, f"Enregistrement impossible :\n{e}", parent=self.f.tk)
            return
        self.lbl_resultat.configure(text=f"Copié dans {cible}")
        if messagebox.askyesno(TITRE, "Copie enregistrée. L'ouvrir maintenant ?", parent=self.f.tk):
            installation.ouvrir(Path(cible))


def construire(parent, fenetre) -> OngletSalaires:
    return OngletSalaires(parent, fenetre)
