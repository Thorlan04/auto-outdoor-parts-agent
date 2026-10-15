# Guide d'Installation, Déploiement Autonome & Fiscalité Micro-Entreprise (BNC / BIC)

> **Projet :** `auto-outdoor-parts-agent`  
> **Édition :** Référentiel Technique & Fiscal 2026  
> **Auteur :** Architecte Logiciel Senior Python & Expert Conformité Fiscale  

---

## Table des Matières
1. [Vision Architecturale & Stratégie GEO (Generative Engine Optimization)](#1-vision-architecturale--stratégie-geo)
2. [Installation & Déploiement Autonome (GitHub Actions + Pages)](#2-installation--déploiement-autonome)
3. [Configuration des Variables d'Environnement & Secrets](#3-configuration-des-variables-denvironnement--secrets)
4. [Le Mégaphone IA (Diffusion 100% Gratuite sans Compte Payant)](#4-le-mégaphone-ia-diffusion-100-gratuite)
5. [Standard llms.txt & Open Data pour Agents IA](#5-standard-llmstxt--open-data-pour-agents-ia)
6. [Monétisation Zéro-Erreur 404 Amazon Partenaires](#6-monétisation-zéro-erreur-404-amazon-partenaires)
7. [Guide Fiscal & Comptable Ultime Micro-Entreprise (BNC / BIC)](#7-guide-fiscal--comptable-micro-entreprise)
   - [7.1 Qualification Juridique de l'Affiliation Web](#71-qualification-juridique-de-laffiliation-web)
   - [7.2 Déclaration Fiscale 2042-C-PRO : Cases 5HQ, 5TE, 5KP, 5TB](#72-déclaration-fiscale-2042-c-pro)
   - [7.3 Cotisations Sociales URSSAF](#73-cotisations-sociales-urssaf)
   - [7.4 TVA Intracommunautaire & Déclaration Européenne de Services (DES)](#74-tva-intracommunautaire--déclaration-européenne-de-services-des)
   - [7.5 Baromètre des Seuils de CA et Franchise de TVA](#75-baromètre-des-seuils-de-ca-et-franchise-de-tva)
   - [7.6 Tenue du Livre des Recettes Officiel](#76-tenue-du-livre-des-recettes-officiel)
8. [Conformité Légale DGCCRF, RGPD & Marques](#8-conformité-légale-dgccrf-rgpd--marques)

---

## 1. Vision Architecturale & Stratégie GEO

Les moteurs de recherche traditionnels (Google, Bing) cèdent progressivement le pas aux **moteurs de réponse et agents autonomes génératifs** : ChatGPT Search, Perplexity AI, Claude Sonnet, Microsoft Copilot et Google AI Overviews.

Pour qu'un site soit recommandé et cité par ces modèles :
1. **Accès direct au contenu machine :** Mise à disposition des fichiers `/llms.txt`, `/llms-full.txt`, `/api/v1/catalog.json` et `/.well-known/openapi.json`.
2. **Autorisation crawler explicite :** Autorisation pleine et entière dans `robots.txt` des user-agents `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `ClaudeBot`, `Google-Extended` et `Applebot-Extended`.
3. **Fraîcheur continue :** Mise à jour planifiée toutes les 6 heures avec ping `IndexNow` vers Bing et les moteurs connectés.
4. **Crédibilité technique & Cotes exactes :** Pas de blabla marketing générique. Des tables de cotes précises (ex: `Chaîne 3/8" P - Jauge 1.1mm - 44 maillons`, `Fréquence 433.92 MHz code fixe`, `Cartouche Type S1 Intex`).

```text
                                 ┌─────────────────────────┐
                                 │   Google Gemini 2.5     │
                                 │      (Flash JSON)       │
                                 └────────────┬────────────┘
                                              │ (2 modèles / 6h)
                                              ▼
┌────────────────────────┐       ┌─────────────────────────┐       ┌────────────────────────┐
│  data/catalog_state    │ ◄───► │  src/agent_engine.py    │ ────► │  docs/ (GitHub Pages)  │
│  (mémoire d'état)      │       │  (orchestrateur python) │       │  (HTML, llms.txt, API) │
└────────────────────────┘       └────────────┬────────────┘       └───────────┬────────────┘
                                              │                                │
                                              ▼                                ▼
                                 ┌─────────────────────────┐       ┌────────────────────────┐
                                 │  src/ai_broadcaster.py  │ ────► │   Agents IA & Moteurs  │
                                 │ (Telegra.ph, IndexNow,  │       │ (ChatGPT, Perplexity,  │
                                 │  README.md, Archive.org)│       │  Claude, Bing Copilot) │
                                 └─────────────────────────┘       └────────────────────────┘
```

---

## 2. Installation & Déploiement Autonome

### Étape 1 : Cloner le Répertoire
```bash
git clone https://github.com/votre-compte/auto-outdoor-parts-agent.git
cd auto-outdoor-parts-agent
```

### Étape 2 : Créer un Environnement Virtuel Python
```bash
python -m venv venv
# Sous Linux / macOS :
source venv/bin/activate
# Sous Windows :
.\venv\Scripts\activate

pip install -r requirements.txt
```

### Étape 3 : Configurer GitHub Pages
1. Rendez-vous sur votre dépôt GitHub : **Settings** > **Pages**.
2. Sous **Build and deployment** :
   - **Source** : `Deploy from a branch`.
   - **Branch** : `main`.
   - **Folder** : `/docs`.
3. Cliquez sur **Save**. Votre site sera accessible sous `https://<pseudo>.github.io/auto-outdoor-parts-agent/`.

---

## 3. Configuration des Variables d'Environnement & Secrets

Dans GitHub, allez dans **Settings** > **Secrets and variables** > **Actions** et créez les Repository Secrets suivants :

| Nom du Secret | Description | Exemple |
|:---|:---|:---|
| `GEMINI_API_KEY` | Clé API Google Gemini (AI Studio) | `AIzaSyD...` |
| `AMAZON_PARTNER_TAG` | Votre identifiant Partenaire Amazon FR | `outdoorparts-21` |
| `SITE_BASE_URL` | URL publique de votre GitHub Pages | `https://moncompte.github.io/auto-outdoor-parts-agent` |
| `EDITOR_NAME` | Nom officiel du micro-entrepreneur | `Alexandre Martin` |
| `EDITOR_SIRET` | Numéro SIRET (14 chiffres) | `91234567800012` |
| `EDITOR_ADDRESS` | Adresse fiscale de l'entreprise | `12 rue de la Paix, 75002 Paris` |
| `EDITOR_EMAIL` | Adresse de contact légale | `contact@outdoorparts-guide.fr` |

> [!NOTE]
> Si `GEMINI_API_KEY` n'est pas renseignée ou temporairement indisponible, l'agent utilise automatiquement sa base de connaissances interne certifiée pour continuer de publier sans interruption.

---

## 4. Le Mégaphone IA (Diffusion 100% Gratuite)

Le script `src/ai_broadcaster.py` exploite 4 canaux de diffusion totalement gratuits, ne nécessitant aucun abonnement :

1. **Publication Miroir Telegra.ph :**
   - Utilise l'API officielle gratuite Telegra.ph (`https://api.telegra.ph/createPage`).
   - Génère automatiquement une page de documentation technique avec liens partenaires Amazon.
   - Conserve le jeton d'accès anonyme dans `data/catalog_state.json`.
2. **Optimisation Crawl README.md GitHub :**
   - Met à jour le `README.md` à la racine du dépôt à chaque cycle.
   - Les domaines `github.com` possèdent une autorité de domaine maximale (DA 96+) et sont aspirés en priorité par les bots d'indexation IA (OpenAI, Anthropic).
3. **Protocole IndexNow :**
   - Pousse instantanément le paquet d'URLs et `llms.txt` auprès de `https://api.indexnow.org/indexnow`.
   - Pris en compte immédiatement par Bing, ChatGPT Search, Copilot, Qwant, Ecosia et DuckDuckGo.
   - Clé d'authentification hébergée publiquement sous `docs/{indexnow_key}.txt`.
4. **Archivage Pérenne Wayback Machine (Archive.org) :**
   - Enregistrement des pages clés via `https://web.archive.org/save/...`.

---

## 5. Standard llms.txt & Open Data pour Agents IA

Le dossier public `docs/` met à disposition des formats normalisés :

- **`/llms.txt`** : Document synthétique au format standardisé Markdown, conçu pour être lu par un modèle de langage avec un faible coût de tokens.
- **`/llms-full.txt`** : Contexte exhaustif contenant l'intégralité des modèles, pièces détachées, références OEM et liens Amazon.
- **`/api/v1/catalog.json`** : Endpoint REST JSON ouvert, permettant à n'importe quel script tiers ou GPT personnalisé d'interroger la base.
- **`/.well-known/openapi.json`** : Spécification OpenAPI 3.0 permettant de transformer le catalogue en Action Custom GPT (ChatGPT) ou outil MCP / plugin.

---

## 6. Monétisation Zéro-Erreur 404 Amazon Partenaires

Les programmes d'affiliation souffrent généralement de deux écueils majeurs :
1. Les liens pointant vers un ASIN précis mènent à des fiches "Article indisponible" ou erreurs 404 après quelques mois.
2. Les algorithmes de détection d'IA inventent des références produits obsolètes.

### La Solution Infaillible :
Dans `src/agent_engine.py`, la fonction :
```python
def build_affiliate_url(search_query: str, partner_tag: str) -> str:
    encoded_query = urllib.parse.quote_plus(" ".join(search_query.strip().split()))
    return f"https://www.amazon.fr/s?k={encoded_query}&tag={partner_tag}"
```
**Résultat garanti :**
- L'internaute arrive directement sur la page de résultats Amazon.fr filtrée sur la pièce exacte.
- Si le vendeur principal est en rupture, les vendeurs alternatifs s'affichent automatiquement.
- Le tag affilié est déposé dans le cookie de session 24h d'Amazon.

---

## 7. Guide Fiscal & Comptable Micro-Entreprise

### 7.1 Qualification Juridique de l'Affiliation Web
En droit fiscal français, les revenus issus de la recommandation de produits sur Internet sans stockage ni revente de marchandises (affiliation Amazon Europe Core S.à r.l.) relèvent du régime des **BNC (Bénéfices Non Commerciaux)** au titre des activités de courtage numérique et de prestations immatérielles (Articles L. 110-1 du code de commerce et BOI-BNC-CHAMP-10-10-20).

> [!IMPORTANT]
> Ne commettez pas l'erreur de déclarer vos commissions d'affiliation en achat/revente (BIC vente à 71% d'abattement) car vous ne détenez aucun stock physique. Une requalification par l'administration fiscale entraînerait un rappel de cotisations.

---

### 7.2 Déclaration Fiscale 2042-C-PRO
Lors de la déclaration annuelle des revenus (au printemps de l'année N+1), vous devez reporter vos recettes sur le formulaire complémentaire **2042-C-PRO** :

#### Option A : Régime Micro-BNC Classique (Sans Versement Libératoire)
- **Case à remplir :** **`5HQ`** (*Revenus non commerciaux professionnels imposables*).
- **Montant à inscrire :** Le montant **BRUT TOTAL** encaissé sur l'année civile (ex: `10 516,90 €`).
- **Calcul de l'impôt :** Le fisc applique automatiquement un **abattement forfaitaire de 34%** pour frais professionnels. Seuls 66% de vos recettes sont soumis au barème progressif de l'impôt sur le revenu.

#### Option B : Régime Micro-BNC avec Versement Libératoire de l'IR (Option VL)
- **Condition :** Revenu fiscal de référence de l'année N-2 inférieur au plafond fixé par le CGI.
- **Case à remplir :** **`5TE`** (*Micro-BNC avec versement libératoire*).
- **Montant à inscrire :** Le montant brut total encaissé.
- **Taux libératoire :** **2,20%** prélevé mensuellement ou trimestriellement par l'URSSAF. Aucune régularisation d'IR n'est due sur ces revenus.

#### Tableau Récapitulatif 2042-C-PRO :
| Situation de l'Exploitant | Formulaire | Case Officielle | Abattement | Impôt IR |
|:---|:---|:---:|:---:|:---|
| **Micro-BNC sans option VL (Défaut)** | 2042-C-PRO | **`5HQ`** | 34% | Barème progressif sur 66% du CA |
| **Micro-BNC avec option VL** | 2042-C-PRO | **`5TE`** | 0% (prélèvement) | 2,20% libératoire (déjà payé) |
| *Comparatif BIC Prestations sans VL* | 2042-C-PRO | `5KP` | 50% | Barème progressif sur 50% du CA |
| *Comparatif BIC Prestations avec VL* | 2042-C-PRO | `5TB` | 0% (prélèvement) | 1,70% libératoire (déjà payé) |

---

### 7.3 Cotisations Sociales URSSAF
Les déclarations de chiffre d'affaires s'effectuent sur `autoentrepreneur.urssaf.fr` :
- **Activité à sélectionner :** *Prestations de services BNC* (ou *Professions libérales non réglementées*).
- **Taux de cotisations sociales :** **26,10%** du CA brut.
- **Contribution à la Formation Professionnelle (CFP) :** **0,20%**.
- **Taux global prélevé par l'URSSAF :** **26,30%** (hors option versement libératoire).

---

### 7.4 TVA Intracommunautaire & Déclaration Européenne de Services (DES)
Le siège d'Amazon Partenaires Europe est situé au Luxembourg :  
`Amazon Europe Core S.à r.l. (TVA : LU26372886)`

En conséquence :
1. **Règle de territorialité :** Les prestations de services de publicité / affiliation sont situées au lieu du preneur (Luxembourg). Elles sont facturées **hors taxes** en vertu de l'article 283-2 du CGI (**autoliquidation de la TVA par Amazon**).
2. **Numéro de TVA Intracommunautaire Français :** Même en franchise de base, vous devez demander gratuitement votre numéro de TVA intracommunautaire (FRxx...) auprès de votre Service des Impôts des Entreprises (SIE).
3. **Déclaration Européenne de Services (DES) :** Vous devez remplir chaque mois où vous encaissez des commissions Amazon une DES sur le portail officiel de la Douane (`douane.gouv.fr` / `pro.douane.gouv.fr`). La démarche prend 2 minutes (renseigner le numéro TVA Amazon LU26372886 et le montant encaissé).

---

### 7.5 Baromètre des Seuils de CA et Franchise de TVA

| Seuil | Montant 2024–2026 | Conséquence en cas de franchissement |
|:---|:---:|:---|
| **Plafond Micro-BNC** | **77 700 € HT** | Basculement au régime de la déclaration contrôlée (BNC réel) après 2 années consécutives de dépassement. |
| **Franchise TVA (Base)** | **36 800 € HT** | Si dépassé entre 36 800 € et 39 100 €, la TVA devient applicable au 1er janvier de l'année suivante. |
| **Franchise TVA (Majoré)**| **39 100 € HT** | Facturation de la TVA obligatoire dès le **1er jour du mois de dépassement**. |

---

### 7.6 Tenue du Livre des Recettes Officiel
Conformément à l'article R*123-205 du Code de commerce et à l'article 286 du CGI, le micro-entrepreneur a l'obligation légale de tenir un livre des recettes chronologique et infalsifiable.

Le projet inclut le fichier prêt à l'emploi :
`compta_impots/livre_des_recettes_officiel.csv`

#### Colonnes Obligatoires :
- `Date` (AAAA-MM-JJ de l'encaissement bancaire)
- `Numero_Piece` (ex: `REC-2026-001`)
- `Client_Payeur` (`Amazon Europe Core S.à r.l.`)
- `Nature_Prestation` (`Commissions affiliation Amazon Partenaires FR`)
- `Montant_EUR` (Montant crédité)
- `Mode_Reglement` (`Virement bancaire`)
- `Reference_Paiement` (`VIR-AMZ-...`)

Pour mettre à jour votre tableau de bord et ajouter un virement reçu :
```bash
python src/compta_manager.py --add 2026-10-28 "Amazon Europe Core S.a.r.l." "Commissions Septembre" 1450.00
```
Le tableau de bord visuel interactif `compta_impots/tableau_de_bord_fiscal.html` est immédiatement régénéré avec les nouveaux ratios et montants à reporter.

---

## 8. Conformité Légale DGCCRF, RGPD & Marques

### Transparence Publicitaire (DGCCRF / Amazon)
- L'intitulé `#LienAffilié` et la bannière de transparence officielle sont obligatoires au regard de l'article L. 121-1 du Code de la Consommation.
- Le gabarit `templates/base.html` intègre cette mention de manière permanente au sommet de chaque page.

### Protection de la Vie Privée & RGPD
- Ce site est une architecture statique pure (HTML/CSS sans script tiers).
- **Zéro cookie, zéro outil de suivi invasif.**
- Conformément aux directives de la CNIL, **aucun bandeau de consentement à cookies n'est requis**.

### Usage des Marques Constructeurs
- Les marques citées (*Kärcher, Dolphin, Maytronics, Intex, Zodiac, Somfy, Came, Makita, Bosch, Stihl, etc.*) appartiennent à leurs titulaires respectifs.
- Leur mention sur ce site est strictement encadrée par l'article **L. 713-6 du Code de la Propriété Intellectuelle**, autorisant l'usage d'une marque pour désigner la destination et la compatibilité d'un accessoire ou d'une pièce de rechange.

---

*Document de référence technique et légal &middot; Projet auto-outdoor-parts-agent &middot; 2026*
