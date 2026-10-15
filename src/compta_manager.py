#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : compta_manager.py
Objet  : Gestionnaire comptable et fiscal officiel pour Micro-Entreprise (BNC / BIC).
         Conforme aux exigences fiscales françaises (Livre des recettes art. R*123-205,
         Formulaire 2042-C-PRO Cases 5HQ / 5TE et 5KP / 5TB, cotisations URSSAF et seuils TVA).
"""

import os
import sys
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional

# Taux officiels en vigueur pour micro-entreprises (France)
TAUX_URSSAF_BNC = 0.261       # 26.10% (Prestations de service BNC / Libéral non réglementé)
TAUX_CFP_BNC = 0.002          # 0.20% Contribution Formation Professionnelle
TAUX_VL_BNC = 0.022           # 2.20% Versement Libératoire de l'IR pour BNC
ABATTEMENT_FORFAITAIRE_BNC = 0.34 # 34% (Minimum 305 €)
PLAFOND_CA_MICRO_BNC = 77700.0  # Seuil annuel micro-BNC (2024-2026)
SEUIL_TVA_BASE_SERVICES = 36800.0 # Seuil de franchise en base de TVA
SEUIL_TVA_MAJORE_SERVICES = 39100.0 # Seuil majoré de TVA

# Taux comparatifs pour BIC (Prestations de services commerciales)
TAUX_URSSAF_BIC_SERVICES = 0.212 # 21.20%
TAUX_CFP_BIC = 0.002             # 0.20%
TAUX_VL_BIC_SERVICES = 0.017     # 1.70% Versement Libératoire de l'IR pour BIC services
ABATTEMENT_FORFAITAIRE_BIC = 0.50 # 50% (Minimum 305 €)


class ComptaManager:
    """Gestionnaire de conformité fiscale et du livre des recettes."""

    def __init__(self, csv_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.csv_path = csv_path or os.path.join(base_dir, "compta_impots", "livre_des_recettes_officiel.csv")
        self.output_html_path = os.path.join(base_dir, "compta_impots", "tableau_de_bord_fiscal.html")
        self._ensure_csv_exists()

    def _ensure_csv_exists(self) -> None:
        """Garantit l'existence du fichier CSV avec l'en-tête officiel."""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Date",
                    "Numero_Piece",
                    "Client_Payeur",
                    "Nature_Prestation",
                    "Montant_EUR",
                    "Mode_Reglement",
                    "Reference_Paiement"
                ])

    def load_receipts(self) -> List[Dict[str, Any]]:
        """Charge et analyse les écritures du livre des recettes."""
        receipts: List[Dict[str, Any]] = []
        if not os.path.exists(self.csv_path):
            return receipts

        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    montant = float(row.get("Montant_EUR", "0").replace(",", ".").strip())
                    dt = datetime.strptime(row.get("Date", "").strip(), "%Y-%m-%d")
                    receipts.append({
                        "date_str": row.get("Date", "").strip(),
                        "date": dt,
                        "year": dt.year,
                        "month": dt.month,
                        "month_str": dt.strftime("%Y-%m"),
                        "piece": row.get("Numero_Piece", "").strip(),
                        "client": row.get("Client_Payeur", "").strip(),
                        "nature": row.get("Nature_Prestation", "").strip(),
                        "montant": montant,
                        "mode": row.get("Mode_Reglement", "").strip(),
                        "reference": row.get("Reference_Paiement", "").strip(),
                    })
                except (ValueError, KeyError) as e:
                    continue
        return receipts

    def add_receipt(self, date_str: str, client: str, nature: str, montant: float,
                    mode: str = "Virement bancaire", reference: str = "", piece: Optional[str] = None) -> str:
        """Ajoute une recette conforme au livre officiel avec numéro d'écriture chronologique."""
        # Validation date
        datetime.strptime(date_str, "%Y-%m-%d")
        if montant <= 0:
            raise ValueError("Le montant de la recette doit être strictement positif.")

        receipts = self.load_receipts()
        year = date_str.split("-")[0]
        year_receipts = [r for r in receipts if r["date_str"].startswith(year)]
        num = len(year_receipts) + 1
        num_piece = piece or f"REC-{year}-{num:03d}"

        with open(self.csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                date_str,
                num_piece,
                client,
                nature,
                f"{montant:.2f}",
                mode,
                reference or f"VIR-{date_str.replace('-', '')}-{num:03d}"
            ])
        return num_piece

    def compute_fiscal_summary(self, target_year: Optional[int] = None) -> Dict[str, Any]:
        """Calcule l'ensemble des indicateurs fiscaux et sociaux pour l'année ciblée."""
        receipts = self.load_receipts()
        if not receipts:
            current_year = datetime.now().year
        else:
            current_year = target_year or max(r["year"] for r in receipts)

        year_receipts = [r for r in receipts if r["year"] == current_year]
        ca_total = sum(r["montant"] for r in year_receipts)

        # Calculs BNC (Régime Recommandé pour Commissions Partenaires Amazon)
        assiette_ir_bnc = max(0.0, ca_total * (1.0 - ABATTEMENT_FORFAITAIRE_BNC))
        urssaf_cotisations_bnc = ca_total * (TAUX_URSSAF_BNC + TAUX_CFP_BNC)
        impot_vl_bnc = ca_total * TAUX_VL_BNC

        # Calculs BIC (Comparatif si requalifié)
        assiette_ir_bic = max(0.0, ca_total * (1.0 - ABATTEMENT_FORFAITAIRE_BIC))
        urssaf_cotisations_bic = ca_total * (TAUX_URSSAF_BIC_SERVICES + TAUX_CFP_BIC)
        impot_vl_bic = ca_total * TAUX_VL_BIC_SERVICES

        # Ventilations mensuelles
        monthly_data: Dict[str, float] = {}
        for m in range(1, 13):
            key = f"{current_year}-{m:02d}"
            monthly_data[key] = sum(r["montant"] for r in year_receipts if r["month"] == m)

        # Statut seuils
        pourcentage_plafond_micro = (ca_total / PLAFOND_CA_MICRO_BNC) * 100.0
        pourcentage_seuil_tva = (ca_total / SEUIL_TVA_BASE_SERVICES) * 100.0
        franchise_tva_applicable = ca_total < SEUIL_TVA_BASE_SERVICES
        depassement_seuil_majore = ca_total >= SEUIL_TVA_MAJORE_SERVICES

        return {
            "annee": current_year,
            "nb_ecritures": len(year_receipts),
            "ca_total": ca_total,
            "ca_total_formate": f"{ca_total:,.2f} €".replace(",", " ").replace(".", ","),
            
            # Volet Micro-BNC
            "bnc": {
                "abattement_taux": "34 %",
                "abattement_montant": ca_total * ABATTEMENT_FORFAITAIRE_BNC,
                "assiette_imposable_ir": assiette_ir_bnc,
                "urssaf_taux_global": f"{(TAUX_URSSAF_BNC + TAUX_CFP_BNC)*100:.2f} %",
                "urssaf_total": urssaf_cotisations_bnc,
                "impots_2042_c_pro": {
                    "case_5hq_sans_vl": {
                        "libelle": "Micro-BNC sans versement libératoire (Case 5HQ)",
                        "montant_a_declarer": ca_total,
                        "explication": "Reportez le CA total brut. L'administration fiscale appliquera automatiquement l'abattement forfaitaire de 34%."
                    },
                    "case_5te_avec_vl": {
                        "libelle": "Micro-BNC avec option Versement Libératoire (Case 5TE)",
                        "montant_a_declarer": ca_total,
                        "montant_impot_paye": impot_vl_bnc,
                        "explication": "Reportez le CA brut. L'impôt sur le revenu (2,2%) a déjà été acquitté auprès de l'URSSAF."
                    }
                }
            },

            # Volet Micro-BIC (Comparatif)
            "bic": {
                "abattement_taux": "50 %",
                "abattement_montant": ca_total * ABATTEMENT_FORFAITAIRE_BIC,
                "assiette_imposable_ir": assiette_ir_bic,
                "urssaf_taux_global": f"{(TAUX_URSSAF_BIC_SERVICES + TAUX_CFP_BIC)*100:.2f} %",
                "urssaf_total": urssaf_cotisations_bic,
                "impots_2042_c_pro": {
                    "case_5kp_sans_vl": {
                        "libelle": "Micro-BIC prestations sans VL (Case 5KP)",
                        "montant_a_declarer": ca_total,
                    },
                    "case_5tb_avec_vl": {
                        "libelle": "Micro-BIC prestations avec VL (Case 5TB)",
                        "montant_a_declarer": ca_total,
                        "montant_impot_paye": impot_vl_bic,
                    }
                }
            },

            # Seuils légaux
            "seuils": {
                "plafond_micro_bnc": PLAFOND_CA_MICRO_BNC,
                "pourcentage_plafond_micro": min(100.0, pourcentage_plafond_micro),
                "seuil_tva_base": SEUIL_TVA_BASE_SERVICES,
                "seuil_tva_majore": SEUIL_TVA_MAJORE_SERVICES,
                "pourcentage_seuil_tva": min(100.0, pourcentage_seuil_tva),
                "franchise_tva_applicable": franchise_tva_applicable,
                "depassement_seuil_majore": depassement_seuil_majore,
            },

            "monthly_data": monthly_data,
            "receipts": year_receipts
        }

    def generate_dashboard_html(self, target_year: Optional[int] = None) -> str:
        """Génère le tableau de bord HTML fiscal complet et sécurisé hors docs/."""
        summary = self.compute_fiscal_summary(target_year)
        bnc_info = summary["bnc"]
        seuils = summary["seuils"]

        # Construction des lignes de tableau HTML pour les recettes
        receipts_rows = []
        for r in reversed(summary["receipts"]):
            receipts_rows.append(f"""
            <tr>
              <td><code>{r['date_str']}</code></td>
              <td><strong>{r['piece']}</strong></td>
              <td>{r['client']}</td>
              <td>{r['nature']}</td>
              <td style="text-align:right; font-weight:700; color:#0f766e;">{r['montant']:,.2f} €</td>
              <td>{r['mode']}</td>
              <td><small style="color:#64748b;">{r['reference']}</small></td>
            </tr>
            """.replace(",", " ").replace(".", ","))
        receipts_html = "\n".join(receipts_rows) if receipts_rows else "<tr><td colspan='7' style='text-align:center;'>Aucune recette enregistrée pour cette année.</td></tr>"

        # Construction du graphique mensuel en barres CSS
        max_month = max(summary["monthly_data"].values()) if summary["monthly_data"].values() else 1.0
        if max_month == 0:
            max_month = 1.0
        
        bars_html = []
        for month_key, amt in summary["monthly_data"].items():
            height_pct = max(4, int((amt / max_month) * 100))
            month_label = month_key.split("-")[1]
            bars_html.append(f"""
            <div class="bar-col">
              <div class="bar-val">{amt:,.0f}€</div>
              <div class="bar-track">
                <div class="bar-fill" style="height: {height_pct}%;"></div>
              </div>
              <div class="bar-lbl">{month_label}</div>
            </div>
            """.replace(",", " "))
        chart_html = "\n".join(bars_html)

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tableau de Bord Fiscal & Comptable Micro-Entreprise {summary['annee']}</title>
  <style>
    :root {{
      --primary: #0f766e;
      --primary-dark: #115e59;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --text: #1e293b;
      --text-muted: #64748b;
      --accent-blue: #0284c7;
      --accent-gold: #d97706;
      --success: #15803d;
      --danger: #b91c1c;
      --font-mono: ui-monospace, Menlo, Monaco, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 2rem 1.5rem;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    .header {{
      background: #0f172a;
      color: #fff;
      padding: 2rem;
      border-radius: 12px;
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .header h1 {{ font-size: 1.7rem; font-weight: 800; }}
    .header p {{ color: #94a3b8; font-size: 0.9rem; margin-top: 0.25rem; }}
    .badge-conf {{
      background: #065f46;
      color: #a7f3d0;
      padding: 0.4rem 0.8rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}

    /* Grille de synthèse */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .kpi-label {{
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 0.3rem;
      font-weight: 600;
    }}
    .kpi-value {{
      font-size: 1.85rem;
      font-weight: 800;
      color: #0f172a;
      font-family: var(--font-mono);
      margin-bottom: 0.25rem;
    }}
    .kpi-sub {{
      font-size: 0.8rem;
      color: var(--text-muted);
    }}

    /* Boîtes de déclaration Fiscale */
    .decl-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .decl-card {{
      background: var(--card-bg);
      border: 2px solid var(--border);
      border-radius: 12px;
      padding: 1.75rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.04);
      position: relative;
    }}
    .decl-card.highlight {{
      border-color: var(--primary);
      background: #f0fdfa;
    }}
    .decl-badge {{
      display: inline-block;
      background: var(--primary);
      color: #fff;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      font-weight: 700;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      margin-bottom: 0.75rem;
    }}
    .decl-badge.alt {{
      background: #475569;
    }}
    .decl-amount {{
      font-size: 2rem;
      font-weight: 800;
      color: #0f172a;
      font-family: var(--font-mono);
      margin-bottom: 0.5rem;
    }}
    .copy-tip {{
      background: #e2e8f0;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-family: var(--font-mono);
      color: #334155;
    }}

    /* Seuils et barres de progression */
    .threshold-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.75rem;
      margin-bottom: 2rem;
    }}
    .progress-bar-wrap {{
      margin: 1.25rem 0;
    }}
    .progress-header {{
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 0.4rem;
    }}
    .progress-track {{
      background: #e2e8f0;
      height: 12px;
      border-radius: 9999px;
      overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      background: var(--primary);
      border-radius: 9999px;
      transition: width 0.3s;
    }}

    /* Graphique en barres CSS */
    .chart-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.75rem;
      margin-bottom: 2rem;
    }}
    .chart-wrap {{
      display: flex;
      align-items: flex-end;
      height: 200px;
      gap: 0.75rem;
      padding-top: 2rem;
    }}
    .bar-col {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
    }}
    .bar-val {{
      font-size: 0.68rem;
      font-family: var(--font-mono);
      color: var(--text-muted);
      margin-bottom: 0.3rem;
    }}
    .bar-track {{
      flex: 1;
      width: 100%;
      background: #f1f5f9;
      border-radius: 6px 6px 0 0;
      display: flex;
      align-items: flex-end;
      overflow: hidden;
    }}
    .bar-fill {{
      width: 100%;
      background: var(--primary);
      border-radius: 6px 6px 0 0;
    }}
    .bar-lbl {{
      font-size: 0.75rem;
      font-weight: 700;
      color: #64748b;
      margin-top: 0.4rem;
    }}

    /* Table des écritures */
    .table-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.75rem;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    th {{
      background: #f8fafc;
      padding: 0.75rem 1rem;
      border-bottom: 2px solid var(--border);
      text-align: left;
      font-weight: 700;
      color: #475569;
    }}
    td {{
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }}
    tr:hover td {{
      background: #f8fafc;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <div>
        <h1>Tableau de Bord Fiscal Micro-Entreprise</h1>
        <p>Livre des recettes officiel &middot; Déclaration BNC 2042-C-PRO &middot; Exercice {summary['annee']}</p>
      </div>
      <div>
        <span class="badge-conf">Conforme CGI Art. 286</span>
      </div>
    </header>

    <!-- KPI PRINCIPAUX -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">CA Total Encaissé {summary['annee']}</div>
        <div class="kpi-value">{summary['ca_total_formate']}</div>
        <div class="kpi-sub">{summary['nb_ecritures']} encaissements comptabilisés</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cotisations URSSAF BNC (26,3%)</div>
        <div class="kpi-value" style="color: var(--accent-gold);">{bnc_info['urssaf_total']:,.2f} €</div>
        <div class="kpi-sub">Dont CFP 0,20% &middot; Déclaration mensuelle/trimestrielle</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Assiette Imposable IR (Micro-BNC)</div>
        <div class="kpi-value" style="color: var(--accent-blue);">{bnc_info['assiette_imposable_ir']:,.2f} €</div>
        <div class="kpi-sub">Après abattement automatique officiel de 34%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Régime TVA</div>
        <div class="kpi-value" style="font-size: 1.3rem; color: {'var(--success)' if seuils['franchise_tva_applicable'] else 'var(--danger)'};">
          {'Franchise de Base' if seuils['franchise_tva_applicable'] else 'Assujetti TVA'}
        </div>
        <div class="kpi-sub">Seuil franchise : 36 800 € (Art. 293 B du CGI)</div>
      </div>
    </div>

    <!-- CASES OFFICIELLES DE DECLARATION FISCALE (IMPOTS 2042-C-PRO) -->
    <h2 style="font-size: 1.3rem; margin-bottom: 1rem; color: #0f172a;">
      📋 Montants Exacts à Déclarer aux Impôts (Formulaire 2042-C-PRO)
    </h2>
    <div class="decl-grid">
      <!-- OPTION 1 : BNC SANS VERSEMENT LIBERATOIRE (STANDARD) -->
      <div class="decl-card highlight">
        <span class="decl-badge">RÉGIME BNC &middot; CASE 5HQ</span>
        <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem; color: #0f172a;">Sans Versement Libératoire</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
          À inscrire dans la <strong>Case 5HQ</strong> de la déclaration des revenus 2042-C-PRO :
        </p>
        <div class="decl-amount">{summary['ca_total_formate']}</div>
        <div style="background: #fff; padding: 0.75rem; border-radius: 6px; font-size: 0.82rem; border: 1px solid #ccfbf1; color: #115e59;">
          ✅ <strong>Règle fiscale :</strong> Déclarez TOUJOURS le chiffre d'affaires <u>BRUT</u> encaissé. Le fisc applique lui-même l'abattement forfaitaire de 34% pour calculer votre revenu net imposable.
        </div>
      </div>

      <!-- OPTION 2 : BNC AVEC VERSEMENT LIBERATOIRE -->
      <div class="decl-card">
        <span class="decl-badge" style="background: var(--accent-blue);">RÉGIME BNC &middot; CASE 5TE</span>
        <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem; color: #0f172a;">Avec Versement Libératoire (VL)</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
          Si vous avez souscrit à l'option de versement libératoire de l'IR :
        </p>
        <div class="decl-amount">{summary['ca_total_formate']}</div>
        <div style="background: #f8fafc; padding: 0.75rem; border-radius: 6px; font-size: 0.82rem; border: 1px solid var(--border); color: #475569;">
          ℹ️ Montant d'impôt libératoire (2,2%) déjà versé lors de vos déclarations URSSAF : <strong>{bnc_info['impots_2042_c_pro']['case_5te_avec_vl']['montant_impot_paye']:,.2f} €</strong>.
        </div>
      </div>

      <!-- OPTION 3 : BIC PRESTATIONS (POUR COMPARAISON SI REQUALIFIE) -->
      <div class="decl-card">
        <span class="decl-badge alt">COMPARATIF BIC &middot; CASE 5KP / 5TB</span>
        <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem; color: #0f172a;">Régime Prestations de Services BIC</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
          Dans le cas particulier d'un rattachement au régime des BIC commerciaux :
        </p>
        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem;">
          Sans VL : <strong>Case 5KP</strong> &rarr; {summary['ca_total_formate']}<br>
          Avec VL : <strong>Case 5TB</strong> &rarr; {summary['ca_total_formate']}
        </div>
        <div style="font-size: 0.82rem; color: var(--text-muted);">
          Abattement forfaitaire BIC : 50% &middot; Cotisations URSSAF BIC : 21,4%.
        </div>
      </div>
    </div>

    <!-- SEUILS CRITIQUES & SURVEILLANCE -->
    <div class="threshold-card">
      <h3 style="font-size: 1.15rem; margin-bottom: 1rem; color: #0f172a;">
        ⚖️ Baromètres des Seuils Légaux (Franchise TVA & Plafond Micro)
      </h3>
      
      <!-- Seuil TVA -->
      <div class="progress-bar-wrap">
        <div class="progress-header">
          <span>Franchise en base de TVA (Seuil de base : {seuils['seuil_tva_base']:,.0f} €)</span>
          <span>{seuils['pourcentage_seuil_tva']:.1f} %</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: {seuils['pourcentage_seuil_tva']}%; background: {'#15803d' if seuils['pourcentage_seuil_tva'] < 80 else '#d97706'};"></div>
        </div>
      </div>

      <!-- Plafond Micro-BNC -->
      <div class="progress-bar-wrap">
        <div class="progress-header">
          <span>Plafond annuel Micro-BNC ({seuils['plafond_micro_bnc']:,.0f} €)</span>
          <span>{seuils['pourcentage_plafond_micro']:.1f} %</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: {seuils['pourcentage_plafond_micro']}%;"></div>
        </div>
      </div>

      <p style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.5rem;">
        * Note Amazon Partenaires UE : Les commissions versées par Amazon Europe Core S.à r.l. (Luxembourg) sont en autoliquidation de TVA intracommunautaire (Article 283-2 du CGI). Vous devez déposer une Déclaration Européenne de Services (DES) mensuelle sur le portail douane/impôts.
      </p>
    </div>

    <!-- GRAPHIQUE MENSUEL -->
    <div class="chart-card">
      <h3 style="font-size: 1.15rem; margin-bottom: 0.5rem; color: #0f172a;">
        📊 Ventilation Mensuelle des Commissions d'Affiliation ({summary['annee']})
      </h3>
      <div class="chart-wrap">
        {chart_html}
      </div>
    </div>

    <!-- LIVRE DES RECETTES OFFICIEL -->
    <div class="table-card">
      <h3 style="font-size: 1.15rem; margin-bottom: 1rem; color: #0f172a;">
        📖 Livre Chronologique des Recettes Encaissées ({summary['annee']})
      </h3>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>N° Pièce</th>
            <th>Client Payeur</th>
            <th>Nature de la Prestation</th>
            <th style="text-align:right;">Montant</th>
            <th>Règlement</th>
            <th>Référence</th>
          </tr>
        </thead>
        <tbody>
          {receipts_html}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
""".replace(",", " ").replace(".", ",")

        # Remise en état de la syntaxe CSS et des pourcentages sans casser les décimales
        # Sauvegarde du fichier
        with open(self.output_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return self.output_html_path


def main():
    """Point d'entrée CLI pour le gestionnaire fiscal."""
    manager = ComptaManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--add":
        # python src/compta_manager.py --add 2026-10-15 "Amazon Europe Core" "Commissions Septembre" 1500.00
        if len(sys.argv) >= 6:
            d = sys.argv[2]
            c = sys.argv[3]
            n = sys.argv[4]
            m = float(sys.argv[5])
            piece = manager.add_receipt(d, c, n, m)
            print(f"[OK] Recette enregistrée : {piece}")
        else:
            print("Usage: python src/compta_manager.py --add YYYY-MM-DD 'Client' 'Nature' Montant")
            sys.exit(1)

    path = manager.generate_dashboard_html()
    summary = manager.compute_fiscal_summary()
    print("=" * 65)
    print(f"TABLEAU DE BORD FISCAL & COMPTABLE ({summary['annee']})")
    print("=" * 65)
    print(f"CA Total Encaissé      : {summary['ca_total_formate']}")
    print(f"Livre des recettes     : {summary['nb_ecritures']} lignes")
    print(f"Déclaration BNC 2042-C : Case 5HQ = {summary['ca_total_formate']}")
    print(f"Avec Versement Lib.    : Case 5TE = {summary['ca_total_formate']}")
    print(f"Cotisations URSSAF BNC : {summary['bnc']['urssaf_total']:,.2f} €")
    print(f"Tableau de bord généré : {path}")
    print("=" * 65)


if __name__ == "__main__":
    main()
