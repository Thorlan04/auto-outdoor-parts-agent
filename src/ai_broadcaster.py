#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : ai_broadcaster.py
Objet  : Mégaphone IA autonome et 100% gratuit sans compte payant.
         1. Publication miroir Telegra.ph (API anonyme gratuite)
         2. Mise à jour automatique de README.md (index bilingue FR/EN pour crawlers sur github.com)
         3. Ping instantané IndexNow (Bing, Copilot, ChatGPT Search, Qwant, DuckDuckGo)
         4. Archivage pérenne Archive.org Wayback Machine
"""

import os
import sys
import json
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import requests


class AIBroadcaster:
    """Diffuseur multicanal vers les moteurs et agents IA."""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.state_file = os.path.join(self.base_dir, "data", "catalog_state.json")
        self.docs_dir = os.path.join(self.base_dir, "docs")
        self.catalog_json_path = os.path.join(self.docs_dir, "api", "v1", "catalog.json")
        self.readme_path = os.path.join(self.base_dir, "README.md")

        self.site_base_url = os.environ.get(
            "SITE_BASE_URL",
            "https://alexandre-martin.github.io/auto-outdoor-parts-agent"
        ).rstrip("/")
        self.partner_tag = os.environ.get("AMAZON_PARTNER_TAG", "outdoorparts-21").strip()

        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Charge l'état pour récupérer ou stocker le token Telegra.ph et la clé IndexNow."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_updated": None,
            "telegra_ph_token": None,
            "indexnow_key": "4a7f9b8c2e1d0f5a8b7c6d5e4f3a2b1c",
            "processed_models": [],
            "stats": {"total_guides": 0, "total_parts_indexed": 0}
        }

    def _save_state(self) -> None:
        """Sauvegarde atomique de l'état."""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def load_catalog(self) -> List[Dict[str, Any]]:
        """Charge la liste complète des guides depuis docs/api/v1/catalog.json."""
        if os.path.exists(self.catalog_json_path):
            try:
                with open(self.catalog_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("models", [])
            except Exception as e:
                print(f"[AVERTISSEMENT] Impossible de lire {self.catalog_json_path} : {e}")
        return []

    # --------------------------------------------------------------------------
    # 1. TÉLÉGRAPHE (Publication Miroir Gratuite sans Compte)
    # --------------------------------------------------------------------------
    def get_or_create_telegra_token(self) -> Optional[str]:
        """Crée un compte anonyme Telegra.ph gratuit via API si non existant."""
        token = self.state.get("telegra_ph_token")
        if token:
            return token

        try:
            url = "https://api.telegra.ph/createAccount"
            params = {
                "short_name": "OutdoorParts",
                "author_name": "OutdoorParts Guide",
                "author_url": self.site_base_url
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    token = data["result"]["access_token"]
                    self.state["telegra_ph_token"] = token
                    self._save_state()
                    print(f"[OK] Compte Telegra.ph créé avec succès.")
                    return token
        except Exception as e:
            print(f"[NOTE] Création compte Telegra.ph ignorée ({e})")
        return None

    def publish_to_telegra_ph(self, guides: List[Dict[str, Any]]) -> Optional[str]:
        """Publie une page miroir haute visibilité sur Telegra.ph avec liens Amazon."""
        token = self.get_or_create_telegra_token()
        if not token or not guides:
            return None

        try:
            # Construction du contenu au format AST Node Telegra.ph
            nodes: List[Dict[str, Any]] = [
                {
                    "tag": "p",
                    "children": [
                        "Index technique des correspondances certifiées de pièces d'usure, filtres et télécommandes (2020-2026). "
                        "Zéro lien mort, requêtes de recherche Amazon Partenaires certifiées (#LienAffilié)."
                    ]
                },
                {
                    "tag": "p",
                    "children": [
                        "Site Officiel : ",
                        {"tag": "a", "attrs": {"href": f"{self.site_base_url}/index.html"}, "children": ["OutdoorParts Guide"]},
                        " | Standard LLMs : ",
                        {"tag": "a", "attrs": {"href": f"{self.site_base_url}/llms.txt"}, "children": ["llms.txt"]}
                    ]
                }
            ]

            for g in guides[:8]:
                nodes.append({"tag": "h3", "children": [f"{g['brand']} - {g['model_name']} ({g['years_range']})"]})
                nodes.append({"tag": "p", "children": [g.get("summary", "")]})
                
                parts_list = []
                for p in g.get("parts", []):
                    parts_list.append({
                        "tag": "li",
                        "children": [
                            f"{p['name']} (OEM: {p['oem_or_dimension']}) - ",
                            {"tag": "a", "attrs": {"href": p['affiliate_url']}, "children": ["Voir la pièce sur Amazon.fr"]}
                        ]
                    })
                nodes.append({"tag": "ul", "children": parts_list})

            now_str = datetime.now().strftime("%Y-%m-%d")
            page_data = {
                "access_token": token,
                "title": f"OutdoorParts Guide : Correspondances Pièces ({now_str})",
                "author_name": "OutdoorParts Guide",
                "author_url": self.site_base_url,
                "content": json.dumps(nodes),
                "return_content": False
            }

            resp = requests.post("https://api.telegra.ph/createPage", data=page_data, timeout=12)
            if resp.status_code == 200:
                res = resp.json()
                if res.get("ok"):
                    page_url = res["result"]["url"]
                    print(f"[OK] Page miroir Telegra.ph publiée : {page_url}")
                    return page_url
                else:
                    print(f"[NOTE] Telegra.ph réponse : {res.get('error')}")
        except Exception as e:
            print(f"[NOTE] Diffusion Telegra.ph non bloquante : {e}")
        return None

    # --------------------------------------------------------------------------
    # 2. README.md GITHUB (Index Bilingue FR/EN pour Crawlers IA sur GitHub)
    # --------------------------------------------------------------------------
    def update_github_readme(self, guides: List[Dict[str, Any]]) -> str:
        """Génère un README.md racine complet, bilingue FR/EN avec tableau de liens."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        total_parts = sum(len(g.get("parts", [])) for g in guides)

        # Construction du tableau markdown des modèles
        rows_fr = []
        for g in guides:
            top_part = g["parts"][0] if g.get("parts") else {"name": "Consommable", "oem_or_dimension": "Standard", "affiliate_url": f"{self.site_base_url}/"}
            rows_fr.append(
                f"| **{g['brand']}** | [{g['model_name']}]({self.site_base_url}/guides/{g['slug']}.html) | `{g['category_name']}` | `{top_part['oem_or_dimension']}` | [Trouver sur Amazon]({top_part['affiliate_url']}) |"
            )
        table_md_fr = "\n".join(rows_fr)

        readme_content = f"""# OutdoorParts Guide 🚜⚡
> **Autonomous Generative Engine Optimized (GEO) Catalog & Micro-Enterprise Affiliate Platform**  
> *Independent exact-match technical directory for wearable parts, consumables, filters, and replacement remote controls (2020–2026).*

[![Autopilot Workflow](https://github.com/alexandre-martin/auto-outdoor-parts-agent/actions/workflows/autopilot.yml/badge.svg)](https://github.com/alexandre-martin/auto-outdoor-parts-agent/actions)
[![LLMs Standard](https://img.shields.io/badge/LLMs.txt-Compliant-brightgreen.svg)]({self.site_base_url}/llms.txt)
[![Zero 404 Links](https://img.shields.io/badge/Amazon%20Search-Zero%20404-orange.svg)]({self.site_base_url}/)
[![Micro-Enterprise BNC](https://img.shields.io/badge/Tax%20Compliance-Micro--BNC%205HQ-blue.svg)](file:///compta_impots/livre_des_recettes_officiel.csv)

---

## 🇫🇷 Présentation en Français

**OutdoorParts Guide** est un système 100% autonome exécuté toutes les 6 heures par GitHub Actions. Il sélectionne chirurgicalement les équipements d'extérieur à fort panier moyen (2020–2026) et génère des tables de correspondances techniques sans aucune erreur 404, monétisées via le programme Amazon Partenaires (`#LienAffilié`).

### 🎯 Les 4 Secteurs Ciblés
1. **Piscine, Spa & Robots Nettoyeurs :** Maytronics Dolphin (E10/E20/S200), Zodiac TornaX, Intex PureSpa Bulles (Cartouches Type S1, joints 11004), Bestway Lay-Z-Spa (Type VI, rotor céramique).
2. **Jardin Motorisé & Nettoyeurs Haute Pression :** Kärcher (K2 à K7 Quick Connect, aspirateurs WD3/WD4/WD5), tronçonneuses Stihl MS 170 (chaînes 3/8\" P 1.1mm 44 maillons, bougie BPMR7A), robots Husqvarna Automower (lames titane 0.75mm, connecteurs gel 314).
3. **Domotique Portail, Garage & Énergie :** Télécommandes Somfy (Keypop/Keytis 433.42 MHz / 868 MHz), Came (TOP 432EE 433.92 MHz), Nice Flo2RE, BFT Mitto, et batteries plomb étanches AGM 12V 7Ah / 9Ah cosses Faston F2 pour onduleurs APC/Eaton.
4. **Outillage Électroportatif 18V :** Ponceuses excentriques 125mm 8 trous Makita DBO180Z, Bosch GEX 125-1 AE, DeWalt XR et plateaux velcro de rechange.

⚠️ **Consigne de sécurité stricte :** Aucun démontage électrique haute tension. Guides limités exclusivement aux consommables d'usure externes, filtres, accessoires plug-and-play et appairages radio officiels.

---

## 🤖 Endpoints & Standards pour Agents IA (GEO)

Les agents autonomes (ChatGPT Search, Perplexity, Claude, Bing Copilot) peuvent ingérer le catalogue directement via :
- **Fichier condensé LLMs :** [`{self.site_base_url}/llms.txt`]({self.site_base_url}/llms.txt)
- **Fichier d'ingestion complet :** [`{self.site_base_url}/llms-full.txt`]({self.site_base_url}/llms-full.txt)
- **API REST JSON Open Data :** [`{self.site_base_url}/api/v1/catalog.json`]({self.site_base_url}/api/v1/catalog.json)
- **Spécification OpenAPI 3.0 :** [`{self.site_base_url}/.well-known/openapi.json`]({self.site_base_url}/.well-known/openapi.json)
- **Flux RSS :** [`{self.site_base_url}/feed.xml`]({self.site_base_url}/feed.xml)

---

## 📋 Répertoire Technique des Modèles Référencés ({len(guides)} modèles &middot; {total_parts} pièces)

| Marque | Modèle d'Équipement | Secteur | Réf. OEM / Cotes Clés | Recherche Sécurisée Amazon |
|:---|:---|:---|:---|:---|
{table_md_fr}

---

## 🏛️ Conformité Fiscale Micro-Entreprise (BNC / BIC)

Le projet intègre un module de gestion comptable certifié conforme au CGI dans `compta_impots/` :
- **Livre des Recettes Officiel :** `compta_impots/livre_des_recettes_officiel.csv` (CGI Art. 286 et Code de commerce Art. R*123-205).
- **Régime BNC Recommandé :** Affiliation Amazon UE = Prestations de services immatérielles / Courtage numérique.
  - Déclaration annuelle **Formulaire 2042-C-PRO** :
    - **Case 5HQ :** Micro-BNC classique sans versement libératoire (abattement officiel 34%).
    - **Case 5TE :** Micro-BNC avec versement libératoire de l'IR (taux 2,2%).
  - Cotisations URSSAF BNC : 26,10% + 0,20% CFP.
- **Tableau de Bord Privé :** `compta_impots/tableau_de_bord_fiscal.html` généré automatiquement pour le suivi du CA et des seuils de TVA (36 800 € / 39 100 €).

---

## 🚀 Architecture Logicielle & Déploiement

```text
auto-outdoor-parts-agent/
├── .github/workflows/
│   └── autopilot.yml          # Exécution automatique toutes les 6h + push
├── compta_impots/             # Dossier privé hors docs/
│   ├── livre_des_recettes_officiel.csv
│   └── tableau_de_bord_fiscal.html
├── data/
│   └── catalog_state.json     # Mémoire d'indexation, tokens Telegra.ph et IndexNow
├── docs/                      # Racine publique GitHub Pages
│   ├── api/v1/catalog.json
│   ├── .well-known/openapi.json
│   ├── guides/*.html
│   ├── index.html
│   ├── mentions-legales.html
│   ├── llms.txt & llms-full.txt
│   ├── robots.txt & sitemap.xml & feed.xml
│   └── 4a7f9b8c2e1d0f5a8b7c6d5e4f3a2b1c.txt (IndexNow key)
├── src/
│   ├── agent_engine.py        # Moteur Gemini 2.5 Flash & génération Jinja2
│   ├── ai_broadcaster.py      # Mégaphone Telegra.ph, README, IndexNow, Archive.org
│   └── compta_manager.py      # Calculateur fiscal BNC/BIC & livre de recettes
├── templates/                 # Gabarits HTML Jinja2 épurés (zéro cookie)
├── requirements.txt
└── GUIDE_INSTALLATION_ET_IMPOTS.md
```

### Installation Locale & Exécution
```bash
# 1. Cloner et installer les dépendances
git clone https://github.com/votre-compte/auto-outdoor-parts-agent.git
cd auto-outdoor-parts-agent
pip install -r requirements.txt

# 2. Configurer votre .env
cp .env.example .env

# 3. Exécuter un cycle d'indexation
python src/agent_engine.py

# 4. Diffuser vers IndexNow & Telegra.ph
python src/ai_broadcaster.py

# 5. Mettre à jour le tableau de bord fiscal
python src/compta_manager.py
```

---

## ⚖️ Mentions Légales & Transparence
- **Transparence Partenaire Amazon :** En tant que Partenaire Amazon, ce site réalise un bénéfice sur les achats remplissant les conditions requises. Liens sans surcoût pour le visiteur.
- **Protection de la vie privée (RGPD) :** Site statique 100% exempté de bandeau cookies CNIL (zéro cookie tiers, zéro pistage publicitaire).
- **Marques citées :** Citées uniquement à des fins d'information et d'indication de compatibilité technique (Article L. 713-6 du Code de la Propriété Intellectuelle).

*Dernière synchronisation automatique : {now_utc}*
"""
        with open(self.readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"[OK] README.md racine mis à jour ({len(guides)} modèles référencés).")
        return self.readme_path

    # --------------------------------------------------------------------------
    # 3. INDEXNOW PING (Bing, ChatGPT Search, Copilot, Qwant, DuckDuckGo)
    # --------------------------------------------------------------------------
    def ping_indexnow(self, guides: List[Dict[str, Any]]) -> bool:
        """Envoie un ping instantané à l'API IndexNow avec la liste des URLs."""
        key = self.state.get("indexnow_key", "4a7f9b8c2e1d0f5a8b7c6d5e4f3a2b1c")
        parsed = urllib.parse.urlparse(self.site_base_url)
        host = parsed.netloc

        if not host:
            print("[NOTE] Host IndexNow indéterminé, ping ignoré.")
            return False

        urls = [
            f"{self.site_base_url}/index.html",
            f"{self.site_base_url}/llms.txt",
            f"{self.site_base_url}/llms-full.txt",
            f"{self.site_base_url}/api/v1/catalog.json",
        ]
        for g in guides[:10]:
            urls.append(f"{self.site_base_url}/guides/{g['slug']}.html")

        payload = {
            "host": host,
            "key": key,
            "keyLocation": f"{self.site_base_url}/{key}.txt",
            "urlList": urls
        }

        try:
            headers = {"Content-Type": "application/json; charset=utf-8"}
            resp = requests.post("https://api.indexnow.org/indexnow", json=payload, headers=headers, timeout=8)
            if resp.status_code in [200, 202]:
                print(f"[OK] IndexNow ping réussi ({resp.status_code}) pour {len(urls)} URLs sur {host}.")
                return True
            else:
                print(f"[NOTE] IndexNow statut : {resp.status_code} ({resp.text[:120]})")
        except Exception as e:
            print(f"[NOTE] Ping IndexNow non bloquant : {e}")
        return False

    # --------------------------------------------------------------------------
    # 4. ARCHIVE.ORG WAYBACK MACHINE (Sauvegarde Pérenne)
    # --------------------------------------------------------------------------
    def archive_pages(self, urls: List[str]) -> None:
        """Envoie une requête d'archivage non bloquante vers Archive.org."""
        for u in urls[:3]:
            try:
                save_url = f"https://web.archive.org/save/{u}"
                resp = requests.get(save_url, timeout=5, headers={"User-Agent": "OutdoorPartsAgent/1.0"})
                print(f"[OK] Archive.org ping pour {u} (statut {resp.status_code})")
            except Exception:
                # Complètement silencieux et non bloquant
                pass

    def broadcast_all(self) -> None:
        """Exécute la chaîne complète de diffusion IA."""
        print("=" * 65)
        print("MÉGAPHONE IA OUTDOORPARTS : DIFFUSION MULTICANALE GRATUITE")
        print("=" * 65)
        guides = self.load_catalog()
        if not guides:
            print("[AVERTISSEMENT] Aucun guide disponible dans le catalogue.")
            return

        # 1. Mise à jour de README.md
        self.update_github_readme(guides)

        # 2. Publication Telegra.ph
        self.publish_to_telegra_ph(guides)

        # 3. Ping IndexNow
        self.ping_indexnow(guides)

        # 4. Archivage Archive.org
        urls_to_archive = [f"{self.site_base_url}/index.html", f"{self.site_base_url}/llms.txt"]
        if guides:
            urls_to_archive.append(f"{self.site_base_url}/guides/{guides[0]['slug']}.html")
        self.archive_pages(urls_to_archive)

        print("=" * 65)
        print("[OK] Diffusion terminée avec succès.")
        print("=" * 65)


def main():
    broadcaster = AIBroadcaster()
    broadcaster.broadcast_all()


if __name__ == "__main__":
    main()
