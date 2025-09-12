# PRD – Automatisation des soumissions







## **1. Contexte et problématique**



L’entreprise commercialise des équipements de coupe et de façonnage de tôle. Deux gammes principales existent : des machines haut de gamme coûtant entre 200 000 $ et 300 000 $, pour lesquelles on prépare une douzaine de soumissions par an, et des produits beaucoup moins chers (≈100 $), mais vendus en grand volume.

Aujourd’hui, la création de chaque soumission est chronophage : elle demande entre 20 et 40 minutes, même pour des produits standards. Ce processus mobilise environ 20 à 30 % du temps d’un employé qualifié, ce qui équivaut à un coût de 20 000 à 30 000 $ par année. De plus, la collecte des besoins clients est éparpillée entre les appels, les échanges par courriel et les discussions dans le chat interne, ce qui entraîne des erreurs, des oublis et un manque de cohérence. Enfin, bien que toutes les soumissions passées soient stockées dans Google Drive, elles ne sont pas exploitées efficacement comme base de référence, et donc l'employé effectuant les soumissions est toujours pris à faire ce travail cognitif élevé, au lieu de faire autre chose plus important.

Ce cumul entraîne une perte de temps, une utilisation sous-optimale des ressources humaines les plus coûteuses, et un frein à la croissance, car chaque nouvelle soumission devient une charge administrative lourde plutôt qu’une opportunité d'affiare fluide.



------



## **2. Objectif général et impact attendu**



L’objectif de ce projet est de réduire significativement le temps et le coût liés à la création des soumissions grâce à l’automatisation et à la standardisation. La solution doit permettre de :

- **Réduire le temps de création d’une soumission** (de 40 minutes à moins de 10 minutes). Un envoi plus rapide au client permet une satisfaction client plus élevé.
- **Diminuer le nombre d’erreurs** liées à la saisie manuelle des besoins clients.
- **Améliorer la qualité et la cohérence** des soumissions, avec un format uniforme et professionnel, peu importe qui les génère.
- **Permettre à des employés moins qualifiés** de préparer des soumissions grâce à un système guidé.
- **Projeter une image professionnelle** et standardisée auprès des clients.
- **Libérer du temps** pour les employés les plus chers de l’entreprise, afin qu’ils se consacrent à des tâches à plus forte valeur ajoutée comme le développement de marché, la négociation ou la relation client.

En somme, l’impact attendu est double : **une réduction claire des coûts internes et une amélioration de l’expérience client**, qui perçoit des soumissions rapides, claires et professionnels.



------

## 3. Solution et fonctionnalités (user story Epic)

---

### **Persona des utilisateurs**

- **Vendeurs** : premiers utilisateurs, responsables de collecter les besoins et de valider les soumissions.  
- **Employés de soutien** : moins qualifiés, mais capables d’utiliser le système pour générer des soumissions simples et soulager les vendeurs.  
- **Président / direction** : intéressés par la cohérence, la rapidité et l’impact financier (réduction des coûts et meilleure satisfaction client).  
- **Clients** : expriment leurs besoins via email, audio ou chat, et attendent des soumissions rapides et précises.  

---

## EPIC 3.1 — Collecte des besoins multicanal (Audio, Email, Chat)

#### User story 3.1.1 – Dictée audio des besoins (Vendeur)  
*En tant que vendeur, je veux pouvoir dicter les besoins du client par audio, afin que le système les transcrive et génère une soumission sans que j’aie à tout ressaisir.*  
- **Impact** : gain de temps immédiat après un rendez-vous, suppression des erreurs de retranscription manuelle.  
- **Features nécessaires** :  
  1. **Transcription audio → texte** *(AI/LLM)*  
     - Explication : convertit audio en texte clair (FR/EN, ponctuation).  
     - Requis : formats audio standards (.m4a/.wav), 5–10 min max, gestion coupures réseau.  
  2. **Détection de mots-clés techniques** *(AI/LLM)*  
     - Explication : identifie quantités, dimensions, options, délais.  
     - Requis : dictionnaire produits, seuil confiance, correction manuelle possible.  
  3. **Interface mobile enregistrement audio** *(UI, Dev)*  
     - Explication : bouton unique pour enregistrer/envoyer, retour visuel immédiat.  
     - Requis : upload en arrière-plan, réécoute rapide, rattachement client/opportunité.  

---

#### User story 3.1.2 – Analyse des emails clients (Client)  
*En tant que client, je veux que mes besoins exprimés par email soient directement analysés et intégrés dans la soumission, afin que je n’aie pas à répéter les mêmes informations.*  
- **Impact** : compréhension globale du besoin du client, réduction des frictions dans la communication et meilleure satisfaction client.  
- **Features nécessaires** :  
  4. **Connecteur email (MCP)** *(Dev)*  
     - Explication : lit mails entrants + pièces jointes.  
     - Requis : OAuth Gmail/IMAP, filtres domaine/dossier, quotas.  
  5. **Extraction automatique besoins (emails)** *(AI/LLM)*  
     - Explication : résume et structure les demandes.  
     - Requis : exclure réponses en quote, OCR si PJ PDF, score de confiance.  
  6. **Mapping vers champs standardisés** *(Workflow)*  
     - Explication : normalise données vers schéma `client/produit/options`.  
     - Requis : schéma JSON validé, champs obligatoires, fallback par défaut.  

---

#### User story 3.1.3 – Détection et guidage dans le chat (Vendeur et employé de soutien)  
*En tant que vendeur, je veux que le système m’aide à rédiger et détecter les besoins que j’ai écrits dans l’interface chat, me guide et me propose automatiquement des options.*  
- **Impact** : capture d’information sans effort supplémentaire, évite les oublis.  
- **Features nécessaires** :  
  7. **Interface chat intégrée (desktop)** *(UI, Dev)*  
     - Explication : fil unique par opportunité avec commandes.  
     - Requis : threads par client, slash-commands (`/soumission`), permissions basiques.  
  8. **Détection temps réel besoins (chat)** *(AI/LLM)*  
     - Explication : extrait infos utiles dès saisie du vendeur.  
     - Requis : déclenchement à l’envoi, anti-bruit, suggestions discrètes.  

---

## EPIC 3.2 — Réutilisation des soumissions passées (Google Drive)

#### User story 3.2.1 – Gabarits issus de l’historique (Vendeur)  
*En tant que vendeur, je veux que le système analyse les soumissions passées pour me proposer un gabarit adapté au nouveau client.*  
- **Impact** : cohérence accrue, capitalisation du savoir de l’entreprise, réduction du temps de rédaction.  
- **Features nécessaires** :  
  10. **Connecteur Google Drive (MCP)** *(Dev)*  
      - Explication : accès dossiers de soumissions.  
      - Requis : OAuth sécurisé, restriction par dossier.  
  11. **Moteur de recherche sémantique (RAG)** *(AI/LLM)*  
      - Explication : retrouve soumissions comparables.  
      - Requis : indexation texte PDF/DOCX, filtres client/produit/date.  
  12. **Générateur gabarit dynamique** *(AI/LLM, Workflow)*  
      - Explication : compose gabarit avec clauses standard.  
      - Requis : variables surlignées, sources citées, validation manuelle.  

---

#### User story 3.2.2 – Archivage et indexation automatique (Vendeur)  
*En tant que vendeur, je veux que toutes mes soumissions soient automatiquement sauvegardées et indexées, afin de les retrouver facilement plus tard.*  
- **Impact** : meilleure traçabilité, facilité à retrouver des soumissions similaires.  
- **Features nécessaires** :  
  13. **Archivage automatique Drive** *(Workflow)*  
      - Explication : enregistre version finale automatiquement.  
      - Requis : nom standardisé (Client_Date), sous-dossier client.  
  14. **Indexation + tagging (+ notes)** *(Workflow, Dev)*  
      - Explication : tag client/produit/statut + champ notes.  
      - Requis : manifest JSON, MAJ tags au changement statut.  
  15. **Recherche rapide historique** *(AI/LLM, MCP)*  
      - Explication : recherche hybride mots-clés + sémantique.  
      - Requis : latence < 2s, aperçu résultats, pagination.  

---

## EPIC 3.3 — Génération et validation automatique

#### User story 3.3.1 – Génération par employé de soutien  
*En tant qu’employé, je veux pouvoir générer une soumission pré-remplie automatiquement afin de la transmettre au responsable pour validation.*  
- **Impact** : démocratisation de la tâche, allègement de la charge des employés les plus qualifiés.  
- **Features nécessaires** :  
  16. **Gabarit standardisé soumission** *(Dev)*  
      - Explication : modèles DOCX/PDF avec branding.  
      - Requis : variables `${client}`, `${prix}`, mise en page simple.  
  17. **Assistant de remplissage auto** *(AI/LLM)*  
      - Explication : pré-remplit prix/specs/conditions.  
      - Requis : règles simples de calcul, drapeaux incertitude.  
  18. **Workflow validation + notifications** *(Workflow, UI)*  
      - Explication : états `brouillon → en revue → approuvé`.  
      - Requis : assignation reviewer, relances automatiques.  

---

#### User story 3.3.2 – Standardisation de la direction  
*En tant que dirigeant, je veux m’assurer que toutes les soumissions sont standardisées et professionnelles, peu importe qui les rédige.*  
- **Impact** : meilleure image externe, plus grande confiance dans la qualité des documents.  
- **Features nécessaires** :  
  19. **Bibliothèque modèles validés** *(Workflow)*  
      - Explication : catalogue officiel approuvé direction.  
      - Requis : rôles/droits, versionning modèles.  
  20. **Mise en page uniforme** *(UI, Dev)*  
      - Explication : applique logos/disclaimers automatiquement.  
      - Requis : pack polices/logos, test PDF pixel-perfect.  

---

#### User story 3.3.3 – Personnalisation minimale (Vendeur)  
*En tant que vendeur, je veux pouvoir personnaliser le texte d’introduction ou les conditions de vente avant l’envoi, afin d’adapter le ton au client.*  
- **Impact** : humanisation, maintien de la relation client.  
- **Features nécessaires** :  
  22. **Éditeur chat canvas** *(UI)*  
      - Explication : édition légère avant export.  
      - Requis : undo/redo, historique, sections verrouillées.  
  23. **Champs libres intro/conclusion** *(UI, Workflow)*  
      - Explication : zones pour personnalisation texte.  
      - Requis : longueur limitée, prévisualisation.  

---

#### User story 3.3.4 – Validation par collègue (Employé/Vendeur)  
*En tant qu’employé, je veux pouvoir réviser une soumission avant envoi.*  
- **Impact** : amélioration de la qualité, validation croisée.  
- **Features nécessaires** :  
  24. **Workflow relecture interne** *(Workflow)*  
      - Explication : demande de review à un collègue.  
      - Requis : @mentions, statut « OK/À corriger ».  
  25. **Notifications email/chat** *(UI, Dev)*  
      - Explication : alertes assignation/relecture.  
      - Requis : canaux configurables, logs d’envoi.  

---

## EPIC 3.4 — Assistance intelligente (Upsell, Argumentaire, Coaching)

#### User story 3.4.1 – Recommandations d’upsell (Vendeur)  
*En tant que vendeur, je veux que le système, via l’interface de chat, me propose des opportunités d’upsell basées sur le contexte et sur des cas similaires dans les soumissions passées.*  
- **Impact** :  
  - Augmentation du panier moyen grâce à des suggestions ciblées.  
  - Aide directe au vendeur (il devient coaché par l’outil en temps réel).  
  - Standardisation des pratiques de vente.  
  - Amélioration de l’expérience client grâce à des suggestions pertinentes.  
- **Features nécessaires** :  
  26. **Moteur recommandation upsell** *(AI/LLM)*  
      - Explication : propose upsells basés sur cas passés.  
      - Requis : justification + sources, seuil de confiance.  
  27. **Analyse contextuelle temps réel** *(AI/LLM)*  
      - Explication : déclenche upsell selon contexte chat.  
      - Requis : règles activation, anti-spam.  
  28. **Suggestions arguments vente** *(AI/LLM)*  
      - Explication : snippets prêts à insérer.  
      - Requis : ton pro, 2–3 lignes, variables client.  
  29. **Interface chat enrichie (panneau latéral)** *(UI, Dev)*  
      - Explication : panneau dédié upsell/arguments.  
      - Requis : insertion 1-clic, drag-&-drop, tracking clics.  

---

# 📑 Synthèse des features

1. Transcription audio → texte  
2. Détection de mots-clés techniques  
3. Interface mobile enregistrement audio  
4. Connecteur email (MCP)  
5. Extraction automatique besoins (emails)  
6. Mapping vers champs standardisés  
7. Interface chat intégrée (desktop)  
8. Détection temps réel besoins (chat)  
10. Connecteur Google Drive (MCP)  
11. Moteur de recherche sémantique (RAG)  
12. Générateur gabarit dynamique  
13. Archivage automatique Drive  
14. Indexation + tagging (+ notes)  
15. Recherche rapide historique  
16. Gabarit standardisé soumission  
17. Assistant de remplissage auto  
18. Workflow validation + notifications  
19. Bibliothèque modèles validés  
20. Mise en page uniforme  
22. Éditeur chat canvas  
23. Champs libres intro/conclusion  
24. Workflow relecture interne  
25. Notifications email/chat  
26. Moteur recommandation upsell  
27. Analyse contextuelle temps réel  
28. Suggestions arguments vente  
29. Interface chat enrichie (panneau latéral)  

