# Carte des modules

_Page générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

Une flèche A → B veut dire « A utilise B » : changer B peut changer le comportement de A.

```mermaid
flowchart LR
  m___main__["__main__"]
  m_apprentissage["apprentissage"]
  m_chargement["chargement"]
  m_config["config"]
  m_corrections["corrections"]
  m_exercices["exercices"]
  m_fenetre["fenetre"]
  m_installation["installation"]
  m_onglet_apprentissage["onglet_apprentissage"]
  m_onglet_documents["onglet_documents"]
  m_onglet_salaires["onglet_salaires"]
  m_onglets_societe["onglets_societe"]
  m_outils["outils"]
  m_pdf_extraction["pdf_extraction"]
  m_rapprochement["rapprochement"]
  m_societe["societe"]
  m_sorties["sorties"]
  subgraph importation
  m_importation__banc["banc"]
  m_importation__catalogue["catalogue"]
  m_importation__classement["classement"]
  m_importation__continuite["continuite"]
  m_importation__extracteurs["extracteurs"]
  m_importation__ia["ia"]
  m_importation__pages["pages"]
  m_importation__pipeline["pipeline"]
  m_importation__sorties["sorties"]
  end
  subgraph salaires
  m_salaires__fiche["fiche"]
  m_salaires__lecture_paie["lecture_paie"]
  m_salaires__reconciliation["reconciliation"]
  end
  subgraph windows
  m_windows__demarrer["demarrer"]
  end
  m___main__ --> m_apprentissage
  m___main__ --> m_chargement
  m___main__ --> m_config
  m___main__ --> m_corrections
  m___main__ --> m_exercices
  m___main__ --> m_importation__banc
  m___main__ --> m_importation__ia
  m___main__ --> m_importation__pipeline
  m___main__ --> m_installation
  m___main__ --> m_pdf_extraction
  m___main__ --> m_rapprochement
  m___main__ --> m_sorties
  m_apprentissage --> m_config
  m_apprentissage --> m_exercices
  m_apprentissage --> m_outils
  m_apprentissage --> m_rapprochement
  m_chargement --> m_config
  m_chargement --> m_outils
  m_corrections --> m_config
  m_corrections --> m_outils
  m_exercices --> m_societe
  m_fenetre --> m___main__
  m_fenetre --> m_config
  m_fenetre --> m_exercices
  m_fenetre --> m_importation__classement
  m_fenetre --> m_importation__ia
  m_fenetre --> m_importation__pipeline
  m_fenetre --> m_installation
  m_fenetre --> m_onglet_apprentissage
  m_fenetre --> m_onglet_documents
  m_fenetre --> m_onglet_salaires
  m_fenetre --> m_onglets_societe
  m_fenetre --> m_societe
  m_importation__banc --> m_importation__ia
  m_importation__catalogue --> m_importation__classement
  m_importation__catalogue --> m_importation__sorties
  m_importation__catalogue --> m_outils
  m_importation__classement --> m_importation__pages
  m_importation__classement --> m_outils
  m_importation__continuite --> m_importation__classement
  m_importation__continuite --> m_importation__pages
  m_importation__continuite --> m_outils
  m_importation__extracteurs --> m_importation__classement
  m_importation__extracteurs --> m_importation__continuite
  m_importation__extracteurs --> m_importation__pages
  m_importation__extracteurs --> m_outils
  m_importation__ia --> m_importation__classement
  m_importation__ia --> m_installation
  m_importation__ia --> m_outils
  m_importation__pages --> m_config
  m_importation__pages --> m_outils
  m_importation__pages --> m_pdf_extraction
  m_importation__pipeline --> m_config
  m_importation__pipeline --> m_importation__classement
  m_importation__pipeline --> m_importation__continuite
  m_importation__pipeline --> m_importation__extracteurs
  m_importation__pipeline --> m_importation__ia
  m_importation__pipeline --> m_importation__pages
  m_importation__pipeline --> m_importation__sorties
  m_importation__pipeline --> m_outils
  m_importation__sorties --> m_importation__classement
  m_importation__sorties --> m_outils
  m_onglet_apprentissage --> m_apprentissage
  m_onglet_apprentissage --> m_config
  m_onglet_apprentissage --> m_corrections
  m_onglet_apprentissage --> m_exercices
  m_onglet_documents --> m_importation__catalogue
  m_onglet_documents --> m_importation__classement
  m_onglet_salaires --> m_config
  m_onglet_salaires --> m_installation
  m_onglet_salaires --> m_salaires__fiche
  m_onglet_salaires --> m_salaires__reconciliation
  m_onglets_societe --> m_exercices
  m_onglets_societe --> m_societe
  m_pdf_extraction --> m_config
  m_pdf_extraction --> m_outils
  m_rapprochement --> m_config
  m_rapprochement --> m_outils
  m_salaires__fiche --> m_config
  m_salaires__lecture_paie --> m_config
  m_salaires__lecture_paie --> m_salaires__fiche
  m_salaires__reconciliation --> m_config
  m_salaires__reconciliation --> m_salaires__fiche
  m_societe --> m_config
  m_societe --> m_installation
  m_sorties --> m_config
  m_sorties --> m_outils
  m_sorties --> m_rapprochement
```

| Module | Fichier | Lignes | Utilisé par |
|---|---|---|---|
| [__main__](modules/__main__.md) | `src/reconsigliere/__main__.py` | 152 | fenetre |
| [apprentissage](modules/apprentissage.md) | `src/reconsigliere/apprentissage.py` | 474 | __main__, onglet_apprentissage |
| [chargement](modules/chargement.md) | `src/reconsigliere/chargement.py` | 146 | __main__ |
| [config](modules/config.md) | `src/reconsigliere/config.py` | 69 | __main__, apprentissage, chargement, corrections, fenetre, importation.pages, importation.pipeline, onglet_apprentissage, onglet_salaires, pdf_extraction, rapprochement, salaires.fiche, salaires.lecture_paie, salaires.reconciliation, societe, sorties |
| [corrections](modules/corrections.md) | `src/reconsigliere/corrections.py` | 104 | __main__, onglet_apprentissage |
| [exercices](modules/exercices.md) | `src/reconsigliere/exercices.py` | 681 | __main__, apprentissage, fenetre, onglet_apprentissage, onglets_societe |
| [fenetre](modules/fenetre.md) | `src/reconsigliere/fenetre.py` | 1137 | — |
| [importation.banc](modules/importation/banc.md) | `src/reconsigliere/importation/banc.py` | 67 | __main__ |
| [importation.catalogue](modules/importation/catalogue.md) | `src/reconsigliere/importation/catalogue.py` | 230 | onglet_documents |
| [importation.classement](modules/importation/classement.md) | `src/reconsigliere/importation/classement.py` | 107 | fenetre, importation.catalogue, importation.continuite, importation.extracteurs, importation.ia, importation.pipeline, importation.sorties, onglet_documents |
| [importation.continuite](modules/importation/continuite.md) | `src/reconsigliere/importation/continuite.py` | 93 | importation.extracteurs, importation.pipeline |
| [importation.extracteurs](modules/importation/extracteurs.md) | `src/reconsigliere/importation/extracteurs.py` | 302 | importation.pipeline |
| [importation.ia](modules/importation/ia.md) | `src/reconsigliere/importation/ia.py` | 108 | __main__, fenetre, importation.banc, importation.pipeline |
| [importation.pages](modules/importation/pages.md) | `src/reconsigliere/importation/pages.py` | 147 | importation.classement, importation.continuite, importation.extracteurs, importation.pipeline |
| [importation.pipeline](modules/importation/pipeline.md) | `src/reconsigliere/importation/pipeline.py` | 179 | __main__, fenetre |
| [importation.sorties](modules/importation/sorties.md) | `src/reconsigliere/importation/sorties.py` | 125 | importation.catalogue, importation.pipeline |
| [installation](modules/installation.md) | `src/reconsigliere/installation.py` | 158 | __main__, fenetre, importation.ia, onglet_salaires, societe |
| [onglet_apprentissage](modules/onglet_apprentissage.md) | `src/reconsigliere/onglet_apprentissage.py` | 208 | fenetre |
| [onglet_documents](modules/onglet_documents.md) | `src/reconsigliere/onglet_documents.py` | 234 | fenetre |
| [onglet_salaires](modules/onglet_salaires.md) | `src/reconsigliere/onglet_salaires.py` | 221 | fenetre |
| [onglets_societe](modules/onglets_societe.md) | `src/reconsigliere/onglets_societe.py` | 194 | fenetre |
| [outils](modules/outils.md) | `src/reconsigliere/outils.py` | 79 | apprentissage, chargement, corrections, importation.catalogue, importation.classement, importation.continuite, importation.extracteurs, importation.ia, importation.pages, importation.pipeline, importation.sorties, pdf_extraction, rapprochement, sorties |
| [pdf_extraction](modules/pdf_extraction.md) | `src/reconsigliere/pdf_extraction.py` | 104 | __main__, importation.pages |
| [rapprochement](modules/rapprochement.md) | `src/reconsigliere/rapprochement.py` | 159 | __main__, apprentissage, sorties |
| [salaires.fiche](modules/salaires/fiche.md) | `src/reconsigliere/salaires/fiche.py` | 200 | onglet_salaires, salaires.lecture_paie, salaires.reconciliation |
| [salaires.lecture_paie](modules/salaires/lecture_paie.md) | `src/reconsigliere/salaires/lecture_paie.py` | 326 | — |
| [salaires.reconciliation](modules/salaires/reconciliation.md) | `src/reconsigliere/salaires/reconciliation.py` | 313 | onglet_salaires |
| [societe](modules/societe.md) | `src/reconsigliere/societe.py` | 648 | exercices, fenetre, onglets_societe |
| [sorties](modules/sorties.md) | `src/reconsigliere/sorties.py` | 100 | __main__ |
| [windows.demarrer](modules/windows/demarrer.md) | `windows/demarrer.pyw` | 196 | — |
