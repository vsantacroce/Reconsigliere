"""Fenêtre de Reconsigliere : choisir le dossier de travail, déposer les fichiers, lancer, ouvrir les résultats.

Lancement : Reconsigliere.bat (Windows), reconsigliere.sh (Ubuntu) ou python -m reconsigliere.fenetre
"""

from __future__ import annotations

import queue
import re
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__, config, installation

TITRE = "Reconsigliere"
NB_ETAPES = 5


class Fenetre:
    def __init__(self, racine_tk: tk.Tk) -> None:
        self.tk = racine_tk
        self.dossier: Path | None = None
        self.messages: queue.Queue = queue.Queue()
        self.en_cours = False

        racine_tk.title(f"{TITRE} — réconciliation bancaire")
        racine_tk.minsize(820, 720)
        racine_tk.geometry("900x800")
        self._style()
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

        # 1. Dossier de travail
        s1 = self._section(principal, "1. Dossier de travail")
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
        s2 = self._section(principal, "2. Dépose tes fichiers dans ces dossiers")
        self.compteurs: dict[str, ttk.Label] = {}
        self.boutons_dossiers: list[ttk.Button] = []
        ligne = 0
        for rel, titre, _ in installation.DOSSIERS:
            if titre is None or not rel.startswith("entrees"):
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
        s3 = self._section(principal, "3. Lancer", extensible=True)
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
        self.journal = tk.Text(journal_cadre, height=6, wrap="word", relief="flat",
                               font=("Consolas", 9) if sys.platform.startswith("win") else ("Monospace", 9),
                               background="#f6f7f9", state="disabled")
        barre = ttk.Scrollbar(journal_cadre, command=self.journal.yview)
        self.journal.configure(yscrollcommand=barre.set)
        self.journal.pack(side="left", fill="both", expand=True)
        barre.pack(side="right", fill="y")
        self.journal.tag_configure("erreur", foreground="#c2410c")

        # 4. Résultats
        s4 = self._section(principal, "4. Résultats")
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

        ttk.Label(principal, text=f"Version {__version__} · tes fichiers restent sur cet ordinateur.",
                  style="Doux.TLabel").pack(anchor="e")

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
        self.btn_ouvrir_dossier.state(["!disabled" if pret else "disabled"])
        for b in self.boutons_dossiers:
            b.state(["!disabled" if pret else "disabled"])
        for cle, (_, chemin) in self.boutons_resultats.items():
            existe = pret and chemin(self.dossier).exists()
            self.widgets_resultats[cle].state(["!disabled" if existe else "disabled"])
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
