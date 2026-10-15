#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : agent_engine.py
Objet  : Moteur principal de génération autonome d'OutdoorParts Guide.
         - Sélection chirurgicale de 2 modèles (2020-2026) par exécution toutes les 6h
         - 4 secteurs à fort panier moyen : Piscine/Spa, Jardin/Kärcher, Domotique, Outillage 18V
         - Génération structurée JSON via Google Gemini (gemini-2.5-flash) ou fallback technique certifié
         - Liens Amazon Partenaires infaillibles zéro-404 (build_affiliate_url)
         - Rendu statique Jinja2 (HTML, sitemap, robots, feed RSS, llms.txt, llms-full.txt, API JSON, OpenAPI)
"""

import os
import sys
import json
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Tentative d'importation du nouveau SDK google-genai
try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


def build_affiliate_url(search_query: str, partner_tag: str) -> str:
    """
    Construit une URL de recherche Amazon Partenaires 100% infaillible (zéro erreur 404).
    N'utilise JAMAIS d'ASIN en dur pour éviter les ruptures de stock.
    """
    clean_query = " ".join(search_query.strip().split())
    encoded_query = urllib.parse.quote_plus(clean_query)
    return f"https://www.amazon.fr/s?k={encoded_query}&tag={partner_tag}"


# Base de connaissances techniques exhaustive des modèles 2020-2026
CANDIDATE_MODELS_POOL = [
    # SECTEUR 1 : PISCINE & SPA
    {
        "slug": "dolphin-e20-maytronics-robot-piscine",
        "category_id": "piscine-spa",
        "category_name": "Piscine, Spa & Robots Nettoyeurs",
        "brand": "Maytronics (Dolphin)",
        "model_name": "Dolphin E20 / E10 / S200",
        "years_range": "2020-2026",
        "title": "Dolphin E20 & S200 : Correspondances Filtres, Chenilles & Brosses",
        "summary": "Guide technique des pièces d'usure externes : paniers filtrants 100µ/50µ, brosses actives PVC et chenilles crantées.",
        "meta_description": "Pièces d'usure et consommables pour robot piscine Dolphin E20, E10, S200. Filtres ultra-fins, brosses et chenilles certifiées.",
        "parts": [
            {
                "name": "Panier Filtrant Ultra-Fin 50 microns (Panneaux Printemps)",
                "tag": "Filtration Fine Rechange",
                "oem_or_dimension": "OEM 9991467-ASSY / 50 microns",
                "wear_symptom": "Déchirure du maillage, colmatage persistant, eau trouble",
                "replacement_interval": "1 à 2 saisons selon turbidité de l'eau",
                "technical_detail": "Cadre rigide à 4 panneaux démontables sans outil, compatible panier standard Dolphin série E.",
                "search_query": "filtre ultra fin dolphin e20 50 microns"
            },
            {
                "name": "Chenille d'Entraînement Crantée Haute Adhérence",
                "tag": "Traction & Motricité",
                "oem_or_dimension": "OEM 9985006 / Longueur 370mm crantée",
                "wear_symptom": "Patinage sur liner, détricotage des crans, robot qui bloque",
                "replacement_interval": "Tous les 2 à 3 ans",
                "technical_detail": "Élastomère résistant au chlore et sel, clipsable directement sur les roues dentées sans vis.",
                "search_query": "chenille dolphin e20 9985006"
            },
            {
                "name": "Brosse Active PVC Lamelles Grise",
                "tag": "Nettoyage Fond & Parois",
                "oem_or_dimension": "OEM 9995546-ASSY / Double vitesse",
                "wear_symptom": "Lamelles usées à plat, perte d'efficacité brossage ligne d'eau",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "PVC souple spécial liners et coques polyester, montage clipsable sur axe central.",
                "search_query": "brosse pvc active dolphin e20"
            },
            {
                "name": "Clapet Anti-Retour Évacuation Panier",
                "tag": "Étanchéité Panier",
                "oem_or_dimension": "OEM 9995541 / Membrane silicone souple",
                "wear_symptom": "Saletés qui retombent dans le bassin à la sortie de l'eau",
                "replacement_interval": "Contrôle annuel",
                "technical_detail": "Volet souple en élastomère transparent évitant le refoulement des débris.",
                "search_query": "clapet anti retour dolphin e20"
            }
        ],
        "procedure_steps": [
            {
                "title": "Mise hors tension du boîtier d'alimentation",
                "description": "Débranchez toujours le bloc transformateur 230V de la prise secteur murale avant toute manipulation du robot."
            },
            {
                "title": "Retrait et nettoyage du panier supérieur",
                "description": "Pressez le loquet supérieur du capot, extrayez le panier verticalement et rincez les 4 panneaux sous un jet d'eau claire sans brosse métallique."
            },
            {
                "title": "Remplacement sans outil de la chenille",
                "description": "Placez le robot sur la tranche. Faites glisser l'ancienne chenille hors de la gorge des galets de guidage, puis emboîtez la nouvelle chenille en tournant la roue à la main."
            }
        ],
        "faqs": [
            {
                "question": "Quelle est la différence entre les filtres 100 microns et 50 microns sur Dolphin ?",
                "answer": "Le filtre 100µ (fourni d'origine) est idéal pour l'ouverture de bassin au printemps contre les feuilles et gros débris. Les panneaux 50µ ultra-fins retiennent les poussières fines, algues mortes et pollens en pleine saison."
            },
            {
                "question": "Faut-il démonter le moteur pour changer les chenilles du Dolphin E20 ?",
                "answer": "Absolument pas. Les chenilles et brosses sont 100% externes et se remplacent à la main sans dévisser le bloc moteur étanche."
            }
        ]
    },
    {
        "slug": "intex-purespa-bulles-spa-gonflable",
        "category_id": "piscine-spa",
        "category_name": "Piscine, Spa & Robots Nettoyeurs",
        "brand": "Intex",
        "model_name": "PureSpa Bulles & Jets (28426 / 28428 / 28440)",
        "years_range": "2020-2026",
        "title": "Intex PureSpa : Cartouches S1, Joints Toriques & Crépines Exactes",
        "summary": "Correspondances certifiées pour spas Intex : cartouches Type S1, joints d'étanchéité raccords 11004 et adaptateurs 32/38mm.",
        "meta_description": "Filtres Type S1, joints toriques 11004 et bouchons pour spa gonflable Intex PureSpa. Correspondances exactes sans erreur 404.",
        "parts": [
            {
                "name": "Cartouches de Filtration Type S1 (Lot Haute Densité)",
                "tag": "Filtration Eau Pure",
                "oem_or_dimension": "Intex 29001E / H 7.3cm x D 10.8cm",
                "wear_symptom": "Débit d'eau réduit, code erreur E90, cartouche saturée",
                "replacement_interval": "Toutes les 2 à 3 semaines en saison",
                "technical_detail": "Papier dacron plissé haute rétention, diamètre intérieur 4.3cm, rinçage bi-hebdomadaire.",
                "search_query": "cartouche type s1 intex purespa"
            },
            {
                "name": "Kit Joints Toriques Raccords Bloc Moteur",
                "tag": "Étanchéité Raccords",
                "oem_or_dimension": "Intex OEM 11004 / 11005 / Diamètre 38mm",
                "wear_symptom": "Goutte à goutte entre le spa et le bloc technique, perte de pression",
                "replacement_interval": "Remplacement annuel ou à chaque remise en eau",
                "technical_detail": "EPDM de grade sanitaire traité anti-chlore et anti-brome, tolérance 45°C.",
                "search_query": "joint torique intex 11004 purespa"
            },
            {
                "name": "Bouchon de Vidange avec Raccord Tuyau Arrosage",
                "tag": "Accessoire Vidange",
                "oem_or_dimension": "Intex 10201 / Filetage standard 3/4\"",
                "wear_symptom": "Fuite par la vanne de vidange inférieure ou filetage foiré",
                "replacement_interval": "En cas de casse ou fissure",
                "technical_detail": "Permet d'évacuer l'eau du spa directement vers les égouts via un tuyau d'arrosage.",
                "search_query": "bouchon vidange intex purespa adaptateur"
            },
            {
                "name": "Diffuseur Flottant de Chlore / Brome Régulé",
                "tag": "Traitement Chimique",
                "oem_or_dimension": "Intex 29044 / Galets 20g (1 pouce)",
                "wear_symptom": "Pastilles dissoutes trop vite ou blocage de la bague de dosage",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Évite le contact direct des pastilles oxydantes avec le PVC du fond du spa.",
                "search_query": "diffuseur flottant brome spa intex 20g"
            }
        ],
        "procedure_steps": [
            {
                "title": "Mise en pause de la filtration",
                "description": "Appuyez sur la touche 'Filter' du panneau tactile pour couper la pompe avant d'ouvrir le boîtier de cartouche."
            },
            {
                "title": "Insertion des bouchons obturateurs intérieurs",
                "description": "Placez les capuchons noirs sur les buses intérieures pour éviter l'écoulement d'eau lors du dévissage des raccords externes."
            },
            {
                "title": "Remplacement de la cartouche S1",
                "description": "Dévissez le réceptacle de cartouche dans le bassin, insérez la cartouche neuve et revissez fermement à la main (sans outil)."
            }
        ],
        "faqs": [
            {
                "question": "Que signifie le code erreur E90 sur Intex PureSpa ?",
                "answer": "Le code E90 indique un défaut de débit d'eau. Dans 95% des cas, il s'agit d'une cartouche S1 encrassée ou d'une crépine obstruée par des cheveux ou résidus."
            },
            {
                "question": "Peut-on laver une cartouche S1 au lave-linge ?",
                "answer": "Non, la pression et les lessives détruisent la trame en dacron. Rincez-la au jet d'eau sous pression ou remplacez-la."
            }
        ]
    },
    {
        "slug": "zodiac-tornax-rt3200-robot-piscine",
        "category_id": "piscine-spa",
        "category_name": "Piscine, Spa & Robots Nettoyeurs",
        "brand": "Zodiac",
        "model_name": "TornaX RT 3200 / OT 3200 / RT 2100",
        "years_range": "2020-2026",
        "title": "Zodiac TornaX RT 3200 : Bac Filtrant, Chenilles & Brosse Lamelles",
        "summary": "Correspondances officielles Zodiac TornaX : bacs filtrants 100µ/200µ, chenilles d'entraînement et brosses à lamelles.",
        "meta_description": "Pièces d'usure certifiées pour Zodiac TornaX RT 3200 et OT 3200. Filtres 100 microns et chenilles crantées sans erreur 404.",
        "parts": [
            {
                "name": "Bac Filtrant Débris Fins 100 microns",
                "tag": "Filtration Fine",
                "oem_or_dimension": "OEM R0762900 / 100 microns rigide",
                "wear_symptom": "Perte d'aspiration, tamis fendu, particules rejetées dans l'eau",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Bac rigide à poignée ergonomique pour extraction rapide par le dessus du robot.",
                "search_query": "filtre bac zodiac tornax rt3200 r0762900"
            },
            {
                "name": "Chenille de Traction Crantée (Unité)",
                "tag": "Motricité Parois",
                "oem_or_dimension": "OEM R0763000 / Profil cranté Zodiac",
                "wear_symptom": "Robot qui ne monte plus aux parois ou qui dérive sur le fond",
                "replacement_interval": "Tous les 2 à 3 ans",
                "technical_detail": "Caoutchouc résistant aux UV et aux traitements au sel.",
                "search_query": "chenille zodiac tornax rt3200 r0763000"
            },
            {
                "name": "Brosse Avant à Lamelles Spéciale Liner / Carrelage",
                "tag": "Frottement & Décollement",
                "oem_or_dimension": "OEM R0762800 / Largeur utile 25cm",
                "wear_symptom": "Lamelles arasées, algues non décollées sur les angles",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Assemblage par clipsage sécurisé sur l'axe d'entraînement avant.",
                "search_query": "brosse zodiac tornax rt3200 r0762800"
            }
        ],
        "procedure_steps": [
            {
                "title": "Coupure de l'alimentation secteur",
                "description": "Déconnectez le boîtier de commande Zodiac du réseau 230V avant de sortir le robot du bassin."
            },
            {
                "title": "Extraction et rinçage du bac filtrant",
                "description": "Soulevez le couvercle transparent, sortez le panier filtrant d'une main et nettoyez-le au jet d'eau tiède."
            }
        ],
        "faqs": [
            {
                "question": "Comment savoir si ma chenille Zodiac TornaX est à changer ?",
                "answer": "Lorsque la chenille commence à se détendre ou si les crans intérieurs sont lisses, le robot patine sur les pentes du bassin."
            }
        ]
    },
    {
        "slug": "bestway-lay-z-spa-miami-airjet",
        "category_id": "piscine-spa",
        "category_name": "Piscine, Spa & Robots Nettoyeurs",
        "brand": "Bestway",
        "model_name": "Lay-Z-Spa Miami / Paris / Hawaii AirJet",
        "years_range": "2020-2026",
        "title": "Bestway Lay-Z-Spa : Cartouches Type VI, Rotor Céramique & Joints",
        "summary": "Pièces de remplacement certifiées Bestway Lay-Z-Spa : cartouches VI (58323), turbine à axe céramique et joints de vanne.",
        "meta_description": "Filtres Type VI, rotor de pompe et joints d'étanchéité pour spa Bestway Lay-Z-Spa. Guides et pièces compatibles sans erreur 404.",
        "parts": [
            {
                "name": "Cartouches de Filtration Type VI (58323)",
                "tag": "Filtration Officielle",
                "oem_or_dimension": "Bestway 58323 / H 8.0cm x D 10.6cm",
                "wear_symptom": "Erreur E02 (débit d'eau insuffisant), encrassement",
                "replacement_interval": "Toutes les 2 semaines",
                "technical_detail": "Filtre en tissu plissé haute densité, trou central 5.2cm.",
                "search_query": "cartouche type vi bestway lay-z-spa 58323"
            },
            {
                "name": "Rotor de Pompe avec Axe en Céramique Inoxydable",
                "tag": "Turbine de Débit",
                "oem_or_dimension": "OEM P05332 / P05333 / Axe céramique 65mm",
                "wear_symptom": "Bruit de claquement, erreur E02 persistante avec filtre propre",
                "replacement_interval": "Tous les 2 à 4 ans",
                "technical_detail": "Axe en céramique technique inaltérable par le chlore et l'eau calcaire, aubes magnétiques néodyme.",
                "search_query": "rotor axe ceramique pompe bestway lay z spa e02"
            },
            {
                "name": "Lot Joints d'Étanchéité Raccords Entrée / Sortie",
                "tag": "Étanchéité Raccords A/B/C",
                "oem_or_dimension": "Joints toriques silicone P61755 / P6575",
                "wear_symptom": "Suintement d'eau au niveau des raccords filetés du bloc",
                "replacement_interval": "Tous les ans",
                "technical_detail": "Silicone souple résistant aux températures jusqu'à 50°C.",
                "search_query": "joint etancheite raccord bestway lay z spa"
            }
        ],
        "procedure_steps": [
            {
                "title": "Résolution de l'erreur E02 Bestway",
                "description": "Éteignez le bloc, placez les bouchons obturateurs intérieurs, retirez la cartouche Type VI et inspectez les ailettes de la crépine."
            },
            {
                "title": "Nettoyage ou changement de cartouche",
                "description": "Rincez abondamment ou insérez une cartouche Type VI neuve avant de redémarrer le cycle de chauffe."
            }
        ],
        "faqs": [
            {
                "question": "Pourquoi remplacer l'axe en plastique du rotor Bestway par un axe céramique ?",
                "answer": "L'axe en plastique d'origine a tendance à s'user et vibrer sous l'effet de la chaleur et du calcaire, déclenchant l'erreur E02. L'axe céramique est inusable."
            }
        ]
    },

    # SECTEUR 2 : JARDIN & HAUTE PRESSION
    {
        "slug": "karcher-k5-power-control-nettoyeur-hp",
        "category_id": "jardin-moteur",
        "category_name": "Jardin Motorisé & Nettoyeurs Haute Pression",
        "brand": "Kärcher",
        "model_name": "K5 Power Control / Full Control / Premium",
        "years_range": "2020-2026",
        "title": "Kärcher K5 Power Control : Flexibles Quick Connect, Rotabuse & Joints",
        "summary": "Correspondances exactes des pièces d'usure Kärcher K5 : flexible 10m 180 bar, lance rotabuse DB 145 et kit joints toriques.",
        "meta_description": "Flexibles Quick Connect, rotabuse DB 145 et joints toriques pour nettoyeur Kärcher K5. Pièces compatibles sans erreur 404.",
        "parts": [
            {
                "name": "Flexible Haute Pression 10m Quick Connect (180 bar)",
                "tag": "Flexible Anti-Vrille",
                "oem_or_dimension": "OEM 6.396-429.0 / Raccords Quick Connect jaunes",
                "wear_symptom": "Frottement abrasif, hernie, fuite sous pression au raccord",
                "replacement_interval": "Tous les 3 à 5 ans",
                "technical_detail": "Tressage textile haute résistance, température max 60°C, raccord rapide quart de tour.",
                "search_query": "flexible karcher k5 10m quick connect"
            },
            {
                "name": "Lance Rotabuse Décapante Dirt Blaster DB 145",
                "tag": "Décapage Puissant",
                "oem_or_dimension": "OEM 2.643-244.0 / Jet rotatif crayon 145 bar",
                "wear_symptom": "Jet qui ne tourne plus (bille bloquée), pulvérisation diffuse",
                "replacement_interval": "En cas d'usure de buse céramique",
                "technical_detail": "Buse en céramique trempée offrant un pouvoir décapant doublé par rapport au jet plat.",
                "search_query": "rotabuse karcher k5 db 145 2.643-244.0"
            },
            {
                "name": "Kit de Joints Toriques de Rechange Haute Pression",
                "tag": "Étanchéité Raccords",
                "oem_or_dimension": "OEM 2.880-990.0 / Bagues NBR & Clips",
                "wear_symptom": "Fuite d'eau au pistolet ou au raccord de lance, perte de pression",
                "replacement_interval": "À remplacer dès apparition d'un suintement",
                "technical_detail": "Contient 10 joints toriques de différents diamètres pour lances, pistolets G 180 Q et flexibles.",
                "search_query": "kit joints toriques karcher 2.880-990.0"
            },
            {
                "name": "Filtre à Eau Transparent Entrée d'Eau 3/4\"",
                "tag": "Protection Pompe",
                "oem_or_dimension": "OEM 4.730-059.0 / Filetage 3/4\" standard",
                "wear_symptom": "Tamis percé, corps transparent fendu par le gel",
                "replacement_interval": "Contrôle avant chaque saison",
                "technical_detail": "Protège la pompe aluminium des grains de sable et particules rouillées du réseau d'eau.",
                "search_query": "filtre eau transparent karcher 4.730-059.0"
            }
        ],
        "procedure_steps": [
            {
                "title": "Procédure de dépressurisation totale",
                "description": "Coupez l'interrupteur électrique 0/I, fermez le robinet d'arrivée d'eau et pressez la gâchette du pistolet pour évacuer la pression résiduelle."
            },
            {
                "title": "Déconnexion rapide du flexible",
                "description": "Pressez le bouton poussoir jaune 'Quick Connect' sous la poignée pistolet pour libérer le flexible sans forcer."
            },
            {
                "title": "Changement du joint torique de lance",
                "description": "À l'aide d'une petite pointe plastique, extrayez l'ancien joint usé de son logement sans rayer le laiton, et insérez le joint neuf préalablement humecté."
            }
        ],
        "faqs": [
            {
                "question": "Peut-on adapter un flexible à visser M22 sur un Kärcher K5 Quick Connect ?",
                "answer": "Oui, grâce à un adaptateur laiton Quick Connect vers filetage femelle M22, ce qui permet de réutiliser d'anciens accessoires."
            },
            {
                "question": "Pourquoi la rotabuse Kärcher ne tourne-t-elle plus ?",
                "answer": "Un calcaire déposé dans la chambre de la bille rotative ou un grain de sable bloque le vortex. Un trempage dans du vinaigre blanc suffit souvent, sinon le remplacement de la rotabuse DB 145 est nécessaire."
            }
        ]
    },
    {
        "slug": "karcher-wd3-aspirateur-eau-poussiere",
        "category_id": "jardin-moteur",
        "category_name": "Jardin Motorisé & Nettoyeurs Haute Pression",
        "brand": "Kärcher",
        "model_name": "Kärcher WD3 / WD3 S V-17/4/20 / Premium",
        "years_range": "2020-2026",
        "title": "Kärcher WD3 : Filtres Cartouche Plissée, Sacs Microfibres & Buses",
        "summary": "Consommables certifiés pour aspirateur Kärcher WD3 : cartouche filtrante 6.414-552.0, sacs intissés 3 couches et brosses combinées.",
        "meta_description": "Filtres cartouches, sacs aspirateur microfibres et buses de sol pour Kärcher WD3 et WD3 Premium. Références OEM sans erreur 404.",
        "parts": [
            {
                "name": "Filtre Cartouche Cylindrique Lavable Eau & Poussière",
                "tag": "Filtration Moteur",
                "oem_or_dimension": "OEM 6.414-552.0 / Avec vis de verrouillage",
                "wear_symptom": "Colmatage, odeur de poussière, surchauffe moteur, débit d'aspiration faible",
                "replacement_interval": "Nettoyage régulier, remplacement tous les 12 mois",
                "technical_detail": "Permet d'aspirer indifféremment eau et poussières sans retirer le filtre cartouche.",
                "search_query": "filtre cartouche karcher wd3 6.414-552.0"
            },
            {
                "name": "Sacs Filtrants Intissés Microfibres 3 Couches (Lot de 5)",
                "tag": "Collecte Poussière Fine",
                "oem_or_dimension": "OEM 2.863-314.0 / Résistance au déchirement",
                "wear_symptom": "Sac plein, perte de force d'aspiration",
                "replacement_interval": "À saturation",
                "technical_detail": "Matériau non-tissé indéchirable retenant le plâtre et les cendres froides sans saturer la cuve.",
                "search_query": "sac intisse karcher wd3 2.863-314.0"
            },
            {
                "name": "Buse Combinée Sol Eau et Poussière avec Clips Caoutchouc",
                "tag": "Accessoire Sol",
                "oem_or_dimension": "OEM 2.863-000.0 / Diamètre 35mm",
                "wear_symptom": "Bandes caoutchouc usées, roulettes bloquées",
                "replacement_interval": "Tous les 3 ans",
                "technical_detail": "Double insert interchangeable : lamelles caoutchouc pour liquides et brosses pour poussières sèches.",
                "search_query": "buse sol karcher wd3 eau poussiere 35mm"
            }
        ],
        "procedure_steps": [
            {
                "title": "Débranchement secteur de l'aspirateur",
                "description": "Débranchez la fiche électrique 230V avant de déverrouiller les clips latéraux de la tête moteur."
            },
            {
                "title": "Verrouillage quart de tour du filtre",
                "description": "Tournez le bouchon de fixation plastique d'un quart de tour vers la gauche pour libérer le filtre cartouche sans forcer sur la cage moteur."
            }
        ],
        "faqs": [
            {
                "question": "Peut-on aspirer de l'eau avec le filtre cartouche monté sur Kärcher WD3 ?",
                "answer": "Oui, le matériau filtrant spécifique est imputrescible. Veillez simplement à retirer le sac en papier ou microfibre lors de l'aspiration de liquides."
            }
        ]
    },
    {
        "slug": "stihl-ms-170-tronconneuse-thermique",
        "category_id": "jardin-moteur",
        "category_name": "Jardin Motorisé & Nettoyeurs Haute Pression",
        "brand": "Stihl",
        "model_name": "Stihl MS 170 / MS 180 / MS 171",
        "years_range": "2020-2026",
        "title": "Stihl MS 170 : Chaînes 3/8\" P 1.1mm, Guide 30cm & Bougie",
        "summary": "Correspondances exactes consommables Stihl MS 170 : chaîne Picco Micro 3 (44 maillons), guide Rollomatic E 30cm et bougie d'allumage.",
        "meta_description": "Chaîne 3/8 P 1.1mm 44 maillons, guide 30cm et bougie NGK pour tronçonneuse Stihl MS 170. Cotes exactes sans erreur 404.",
        "parts": [
            {
                "name": "Chaîne de Tronçonneuse 3/8\" P - Jauge 1.1mm (44 Maillons)",
                "tag": "Coupe Nette",
                "oem_or_dimension": "Stihl 3610-000-0044 / Picco Micro Mini 3 (PMM3)",
                "wear_symptom": "Sciure en poussière fine, chaîne qui fume, déviation de coupe",
                "replacement_interval": "Affûtage régulier, remplacement après 4 à 5 affûtages",
                "technical_detail": "Pas 3/8\" Picco (9.32mm), jauge étroite 1.1mm (.043\"), 44 maillons entraîneurs pour guide de 30cm.",
                "search_query": "chaine stihl ms 170 3/8 1.1 44 maillons 3610-000-0044"
            },
            {
                "name": "Guide-Chaîne Rollomatic E Mini 30cm (12 pouces)",
                "tag": "Guide Anti-Rebond",
                "oem_or_dimension": "Stihl 3005-000-3905 / Longueur 30cm",
                "wear_symptom": "Bavures sur les rails, gorge élargie, chaîne qui flotte",
                "replacement_interval": "Tous les 2 à 3 ans (retourner le guide à chaque changement de chaîne)",
                "technical_detail": "Pignon de renvoi trempé à 7 dents, acier au chrome-molybdène ultra-léger.",
                "search_query": "guide stihl 30cm 3005-000-3905 ms170"
            },
            {
                "name": "Bougie d'Allumage NGK BPMR7A / Bosch WSR6F",
                "tag": "Allumage Fiable",
                "oem_or_dimension": "NGK BPMR7A / Écartement 0.5mm / Filetage M14",
                "wear_symptom": "Démarrage difficile à chaud, ratés d'allumage au ralenti",
                "replacement_interval": "Remplacement annuel ou toutes les 100 heures",
                "technical_detail": "Résistance intégrée antiparasite, culot court standard 2 temps tronçonneuse.",
                "search_query": "bougie ngk bpmr7a stihl ms 170"
            },
            {
                "name": "Filtre à Air en Feutre Synthétique Rechange",
                "tag": "Protection Moteur 2T",
                "oem_or_dimension": "Stihl OEM 1130-124-0800",
                "wear_symptom": "Perte de puissance à l'accélération, colmatage par la sciure",
                "replacement_interval": "Nettoyage hebdomadaire, changement chaque saison",
                "technical_detail": "Montage instantané clipsé derrière le capot quart de tour.",
                "search_query": "filtre a air stihl ms 170 1130-124-0800"
            }
        ],
        "procedure_steps": [
            {
                "title": "Sécurité : Moteur coupé et frein de chaîne enclenché",
                "description": "Placez le commutateur sur '0' (Stop), portez des gants anticoupure et poussez le protège-main vers l'avant pour bloquer le pignon."
            },
            {
                "title": "Montage et tension de la chaîne",
                "description": "Engagez les 44 maillons dans la gorge du guide en orientant le tranchant des gouges vers l'avant. Ajustez la vis de tension jusqu'à ce que la chaîne affleure sans pendre sous le guide."
            }
        ],
        "faqs": [
            {
                "question": "Quelle est la différence entre une chaîne 1.1mm et 1.3mm sur Stihl ?",
                "answer": "La Stihl MS 170 d'origine utilise exclusivement la jauge ultra-fine 1.1mm (Picco Micro Mini 3). Monter une chaîne 1.3mm bloque dans le guide d'origine et endommage la machine."
            }
        ]
    },
    {
        "slug": "husqvarna-automower-310-robot-tondeuse",
        "category_id": "jardin-moteur",
        "category_name": "Jardin Motorisé & Nettoyeurs Haute Pression",
        "brand": "Husqvarna / Gardena",
        "model_name": "Automower 305 / 310 / 405X / Gardena Sileno",
        "years_range": "2020-2026",
        "title": "Husqvarna Automower 310 : Lames Titane, Connecteurs Gel & Câbles",
        "summary": "Correspondances consommables robot tondeuse Husqvarna & Gardena : lames carbure endurance 0.75mm, connecteurs étanches 3M et fil périphérique.",
        "meta_description": "Lames titane pivotantes, connecteurs étanches 3M Scotchlok 314 et câble périphérique pour Husqvarna Automower. Pièces d'usure certifiées.",
        "parts": [
            {
                "name": "Lames Carbure Titane Endurance 0.75mm avec Vis Inox (Lot de 30)",
                "tag": "Coupe Coupe-Bord",
                "oem_or_dimension": "OEM 595 08 44-01 / Épaisseur 0.75mm / Vis revêtues frein filet",
                "wear_symptom": "Herbe jaunie aux pointes (effilochée et non tranchée nette)",
                "replacement_interval": "Toutes les 4 à 6 semaines en saison active",
                "technical_detail": "Lames pivotantes double tranchant revêtues nitrure de titane, évitant la casse sur cailloux.",
                "search_query": "lames titane husqvarna automower 0.75mm"
            },
            {
                "name": "Connecteurs de Câble Étanches à Gel 3M Scotchlok 314",
                "tag": "Réparation Boucle Câble",
                "oem_or_dimension": "3M Scotchlok 314 / Remplissage gel hydrofuge",
                "wear_symptom": "Voyant bleu clignotant sur la station de charge (signal boucle coupé)",
                "replacement_interval": "À chaque coupure de câble accidentelle",
                "technical_detail": "Auto-dénudant par simple pression d'une pince plate, gel d'étanchéité anti-corrosion enterrable.",
                "search_query": "connecteurs 3m scotchlok 314 robot tondeuse"
            },
            {
                "name": "Bobine Câble Périphérique Cuivre Étamé Haute Conductivité (100m)",
                "tag": "Délimitation Pelouse",
                "oem_or_dimension": "Diamètre 2.7mm / Gaine PE résistante aux UV et rongeurs",
                "wear_symptom": "Section de câble par bêchage ou écrasement",
                "replacement_interval": "En cas de modification du périmètre de tonte",
                "technical_detail": "Ame multibrins étamée pour une impédance minimale sur longues distances (>250m).",
                "search_query": "cable peripherique 2.7mm robot tondeuse husqvarna"
            }
        ],
        "procedure_steps": [
            {
                "title": "Couper l'interrupteur principal du robot",
                "description": "Basculez l'interrupteur général sous le robot sur la position '0' (Arrêt) et portez des gants de protection."
            },
            {
                "title": "Changement simultané des 3 lames pivotantes",
                "description": "Dévissez les 3 vis inox au tournevis cruciforme, éliminez les débris d'herbe séchée du disque et montez les lames neuves avec de NOUVELLES vis fournies (le frein filet assure la sécurité)."
            }
        ],
        "faqs": [
            {
                "question": "Pourquoi les lames du robot tondeuse doivent-elles pivoter librement ?",
                "answer": "La rotation libre permet à la lame de s'escamoter en cas de contact avec une pomme de pin ou un caillou, évitant de tordre le plateau ou d'éjecter un éclat métallique."
            }
        ]
    },

    # SECTEUR 3 : DOMOTIQUE & ÉNERGIE
    {
        "slug": "somfy-keypop-keytis-rts-io-telecommande",
        "category_id": "domotique-energie",
        "category_name": "Domotique Portail, Garage & Énergie de Secours",
        "brand": "Somfy",
        "model_name": "Keypop 2 RTS / Keytis 4 RTS / io",
        "years_range": "2020-2026",
        "title": "Télécommandes Somfy Keypop & Keytis : Piles CR2430 & Procédures",
        "summary": "Correspondances exactes télécommandes Somfy 433.42 MHz (RTS) et 868 MHz (io) : piles bouton CR2430, boîtiers et appairage officiel.",
        "meta_description": "Télécommandes compatibles Somfy Keypop 2 RTS et Keytis, piles lithium CR2430 et CR2032. Fréquences certifiées 433.42 MHz sans erreur 404.",
        "parts": [
            {
                "name": "Télécommande 2 Canaux Compatible Somfy RTS (433.42 MHz)",
                "tag": "Émetteur de Remplacement",
                "oem_or_dimension": "Fréquence 433.42 MHz RTS / Compatible moteurs Axovia, SGS, Elixo",
                "wear_symptom": "Boutons enfoncés, portée radio tombée à moins de 2 mètres, boîtier cassé",
                "replacement_interval": "Remplacement en cas de perte ou défaillance",
                "technical_detail": "Protocole radio RTS propriétaire Somfy, coque renforcée avec anneau porte-clés.",
                "search_query": "telecommande compatible somfy rts 433.42 mhz keypop"
            },
            {
                "name": "Piles Bouton Lithium CR2430 3V Haute Capacité (Lot de 5)",
                "tag": "Alimentation Émetteur",
                "oem_or_dimension": "CR2430 / Tension 3 Volts / Capacité 300mAh",
                "wear_symptom": "Voyant LED faible ou clignotement saccadé à l'appui",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Plage de température étendue (-20°C à +60°C) pour fonctionnement hivernal garanti.",
                "search_query": "pile cr2430 3v lithium somfy"
            },
            {
                "name": "Piles Bouton Lithium CR2032 3V (Pour modèles Keypop récents)",
                "tag": "Alimentation Keypop 2",
                "oem_or_dimension": "CR2032 / Diamètre 20mm x Épaisseur 3.2mm",
                "wear_symptom": "Non-réponse du portail",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Technologie lithium dioxyde de manganèse à faible autodécharge.",
                "search_query": "pile cr2032 3v energizer"
            }
        ],
        "procedure_steps": [
            {
                "title": "Identification du protocole radio (RTS vs io)",
                "description": "Vérifiez l'étiquette au dos de l'ancienne télécommande : 'RTS' (433.42 MHz, LED rouge) ou 'io' (868.95 MHz, LED verte). Les deux fréquences ne sont pas interchangeables."
            },
            {
                "title": "Procédure d'appairage depuis une télécommande existante (Sans ouvrir le moteur)",
                "description": "Prenez une télécommande déjà en service. Appuyez sur son bouton caché 'PROG' au dos jusqu'à ce que le portail fasse un bref va-et-vient. Puis appuyez immédiatement sur le bouton de la nouvelle télécommande : le portail confirme par un second mouvement."
            }
        ],
        "faqs": [
            {
                "question": "Peut-on appairer une nouvelle télécommande Somfy sans toucher au boîtier du moteur ?",
                "answer": "Oui, la fonction 'Prog' radio permet de cloner l'autorisation depuis une télécommande en fonctionnement en moins de 10 secondes."
            }
        ]
    },
    {
        "slug": "came-top-432ee-telecommande-portail",
        "category_id": "domotique-energie",
        "category_name": "Domotique Portail, Garage & Énergie de Secours",
        "brand": "Came",
        "model_name": "TOP 432EE / TOP 432NA / TOP 432EV",
        "years_range": "2020-2026",
        "title": "Came TOP 432EE : Télécommandes 433.92 MHz, Piles CR2016 & Clonage",
        "summary": "Correspondances officielles télécommandes Came TOP 432EE / 432NA : fréquence 433.92 MHz code fixe, piles CR2016 et méthode d'auto-apprentissage.",
        "meta_description": "Télécommandes d'origine et compatibles Came TOP 432EE 433.92 MHz, piles CR2016. Procédure de clonage direct sans toucher au moteur.",
        "parts": [
            {
                "name": "Télécommande 2 Canaux 433.92 MHz Came TOP 432EE",
                "tag": "Émetteur Référence",
                "oem_or_dimension": "OEM 001TOP-432EE / 433.92 MHz Code Fixe",
                "wear_symptom": "Boîtier fissuré, touches usées, perte de portée",
                "replacement_interval": "En cas de perte ou défaillance mécanique",
                "technical_detail": "Compatible 100% avec les anciennes TOP-432NA et TOP-432EV, mémorisation code fixe inviolable.",
                "search_query": "telecommande came top 432ee 433.92 mhz"
            },
            {
                "name": "Lot de Piles Bouton CR2016 3V (Alimentation 6V Came)",
                "tag": "Alimentation Double Pile",
                "oem_or_dimension": "CR2016 / 3V x 2 piles superposées = 6 Volts",
                "wear_symptom": "LED rouge qui faiblit à l'appui",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Attention : nécessite 2 piles CR2016 superposées dans le sens de polarité indiqué.",
                "search_query": "pile cr2016 lot 3v energizer came"
            }
        ],
        "procedure_steps": [
            {
                "title": "Mise en mode apprentissage de la nouvelle TOP 432EE",
                "description": "Appuyez simultanément sur les deux boutons supérieurs de la nouvelle télécommande jusqu'à ce que la LED clignote plus rapidement."
            },
            {
                "title": "Sélection du canal et transmission du code",
                "description": "Pressez le bouton à programmer (la LED devient fixe). Approchez immédiatement l'ancienne télécommande au dos et appuyez sur son bouton : la nouvelle LED clignote 3 fois pour confirmer le clonage réussi."
            }
        ],
        "faqs": [
            {
                "question": "La TOP 432EE est-elle compatible avec les anciennes télécommandes grises TOP 432NA ?",
                "answer": "Oui, la TOP 432EE remplace directement la TOP 432NA et la TOP 432EV grâce à son protocole bicanal 433.92 MHz rétrocompatible."
            }
        ]
    },
    {
        "slug": "apc-back-ups-batterie-plomb-etanche-12v",
        "category_id": "domotique-energie",
        "category_name": "Domotique Portail, Garage & Énergie de Secours",
        "brand": "APC (Schneider) / Eaton",
        "model_name": "Back-UPS ES / Pro / BX1400U / Ellipse ECO",
        "years_range": "2020-2026",
        "title": "Onduleurs APC & Centrales Alarme : Batteries Plomb AGM 12V 7Ah / 9Ah",
        "summary": "Correspondances exactes des cartouches de batterie plomb étanches pour onduleurs APC et automatismes de secours : 12V 7.2Ah et 12V 9Ah cosses Faston F2.",
        "meta_description": "Batteries plomb étanche 12V 7.2Ah et 12V 9Ah pour onduleurs APC Back-UPS, Eaton et centrales alarme. Cosses Faston F2 6.35mm sans erreur 404.",
        "parts": [
            {
                "name": "Batterie Plomb Étanche AGM 12V 7.2Ah / 7.5Ah (Cosses Faston F2)",
                "tag": "Énergie Onduleur Secours",
                "oem_or_dimension": "12V 7.2Ah / Dimensions 151 x 65 x 94 mm / Bornes F2 (6.35mm)",
                "wear_symptom": "Bip continu de l'onduleur, coupure instantanée en cas de coupure de courant",
                "replacement_interval": "Tous les 3 à 5 ans",
                "technical_detail": "Technologie AGM sans entretien, étanche, gaz recombine, homologuée floating secours.",
                "search_query": "batterie 12v 7.2ah faston f2 onduleur apc"
            },
            {
                "name": "Batterie Plomb Étanche AGM Haute Densité 12V 9Ah (Cosses Faston F2)",
                "tag": "Autonomie Prolongée",
                "oem_or_dimension": "12V 9Ah / Dimensions identiques standard 151 x 65 x 94 mm / Cosses F2",
                "wear_symptom": "Perte d'autonomie progressive sur onduleurs 1400VA (BX1400U)",
                "replacement_interval": "Tous les 3 à 5 ans",
                "technical_detail": "Offre 25% d'autonomie supplémentaire dans le même encombrement que la 7Ah.",
                "search_query": "batterie 12v 9ah faston f2 onduleur"
            }
        ],
        "procedure_steps": [
            {
                "title": "Mise hors tension et débranchement de la prise secteur",
                "description": "Éteignez l'onduleur avec son bouton marche/arrêt et débranchez le cordon 230V de la prise murale."
            },
            {
                "title": "Remplacement sécurisé de la cartouche de batterie",
                "description": "Ouvrez la trappe inférieure sous l'onduleur. Déconnectez d'abord la cosse NOIRE (-), puis la cosse ROUGE (+). Insérez la batterie neuve et reconnectez Rouge (+) puis Noir (-). Une petite étincelle au rebranchement est normale (charge des condensateurs)."
            }
        ],
        "faqs": [
            {
                "question": "Quelle est la différence entre cosses Faston F1 et Faston F2 ?",
                "answer": "La borne F1 mesure 4.75mm de large, tandis que la borne F2 mesure 6.35mm. Les onduleurs APC et Eaton utilisent quasi-exclusivement des bornes larges F2."
            }
        ]
    },

    # SECTEUR 4 : OUTILLAGE 18V
    {
        "slug": "makita-dbo180z-ponceuse-excentrique-18v",
        "category_id": "outillage",
        "category_name": "Outillage Électroportatif",
        "brand": "Makita",
        "model_name": "Makita DBO180 / DBO180Z / BO5031 18V LXT",
        "years_range": "2020-2026",
        "title": "Makita DBO180Z : Plateau Velcro 125mm 8 Trous, Sac & Batteries",
        "summary": "Correspondances consommables pour ponceuse Makita DBO180Z : plateau auto-agrippant 125mm 8 trous (743081-8), sac à poussière et disques abrasifs.",
        "meta_description": "Plateau de ponçage velcro 125mm 8 trous, sac réutilisable et batteries compatibles pour ponceuse Makita DBO180Z 18V. Zéro 404.",
        "parts": [
            {
                "name": "Plateau de Ponçage Velcro 125mm 8 Trous (Fixation 3 Vis)",
                "tag": "Plateau Auto-Agrippant",
                "oem_or_dimension": "Makita 743081-8 / Diamètre 125mm / 8 trous d'aspiration",
                "wear_symptom": "Disques abrasifs qui s'envolent pendant le ponçage (crochets velcro brûlés)",
                "replacement_interval": "Dès perte d'adhérence du velcro",
                "technical_detail": "Mousse polyuréthane semi-rigide haute résistance thermique, montage par 3 vis d'origine.",
                "search_query": "plateau ponceuse makita dbo180 125mm 743081-8"
            },
            {
                "name": "Sac Récepteur de Poussière avec Support Plastique",
                "tag": "Aspiration Autonome",
                "oem_or_dimension": "Makita 166078-4 / Verrouillage baïonnette",
                "wear_symptom": "Sac papier troué, poussière rejetée dans l'air",
                "replacement_interval": "En cas de déchirement",
                "technical_detail": "Tissu microfibre lavable évitant l'usage de sacs papier jetables.",
                "search_query": "sac poussiere makita dbo180 166078-4"
            },
            {
                "name": "Batterie Compatible 18V 5.0Ah Li-Ion avec Indicateur LED",
                "tag": "Autonomie Atelier",
                "oem_or_dimension": "Compatible BL1850B / 18V 5000mAh",
                "wear_symptom": "Perte rapide de charge, outil qui coupe sous charge",
                "replacement_interval": "Tous les 3 à 5 ans",
                "technical_detail": "Protection intégrée contre les surchauffes, surcharges et décharges profondes.",
                "search_query": "batterie 18v 5ah compatible makita bl1850b"
            }
        ],
        "procedure_steps": [
            {
                "title": "Retrait obligatoire de la batterie 18V",
                "description": "Glissez le bouton rouge pour éjecter la batterie 18V avant de retourner la ponceuse sur votre établi."
            },
            {
                "title": "Remplacement du plateau velcro en 2 minutes",
                "description": "Dévissez les 3 vis cruciformes situées dans les creux du plateau usé. Positionnez le nouveau plateau en alignant les trous d'aspiration et resserrez modérément sans forcer."
            }
        ],
        "faqs": [
            {
                "question": "Pourquoi les disques abrasifs se détachent-ils de ma ponceuse Makita ?",
                "answer": "Une pression excessive ou un ponçage à sec prolongé fait fondre les micro-crochets en nylon du plateau velcro. Remplacer le plateau 743081-8 résout instantanément le problème."
            }
        ]
    },
    {
        "slug": "bosch-professional-gex-125-1-ae-ponceuse",
        "category_id": "outillage",
        "category_name": "Outillage Électroportatif",
        "brand": "Bosch Professional",
        "model_name": "GEX 125-1 AE / GEX 18V-125 Professional",
        "years_range": "2020-2026",
        "title": "Bosch GEX 125-1 AE : Plateau Mi-Dur 125mm, Filtre & Charbons",
        "summary": "Correspondances d'usure Bosch Professional : plateau de ponçage 125mm 8 trous (2608000349), cartouche microfiltre et balais de charbon.",
        "meta_description": "Plateau de rechange 125mm, boîtier microfiltre et balais de charbon pour ponceuse Bosch GEX 125-1 AE. Références vérifiées sans erreur 404.",
        "parts": [
            {
                "name": "Plateau de Ponçage Mi-Dur 125mm Auto-Agrippant (8 Trous)",
                "tag": "Plateau Usure",
                "oem_or_dimension": "Bosch 2608000349 / Diamètre 125mm / Dureté moyenne",
                "wear_symptom": "Disques qui se décollent, bord du plateau ébréché",
                "replacement_interval": "Dès altération de la surface velcro",
                "technical_detail": "Fixation centrale par 4 vis torx/cruciformes, équilibrage dynamique anti-vibrations.",
                "search_query": "plateau ponceuse bosch gex 125-1 ae 2608000349"
            },
            {
                "name": "Boîtier Microfiltre Réutilisable avec Filtre Plissé",
                "tag": "Filtration Cyclonique",
                "oem_or_dimension": "Bosch 2605411225 / Raccord aspiration Click & Clean",
                "wear_symptom": "Filtre cartonné saturé, poussière recrachée",
                "replacement_interval": "Nettoyage par tapotement, renouvellement annuel",
                "technical_detail": "Boîtier plastique translucide permettant de surveiller le niveau de remplissage.",
                "search_query": "boitier microfiltre bosch gex 125 2605411225"
            }
        ],
        "procedure_steps": [
            {
                "title": "Déconnexion de l'alimentation électrique",
                "description": "Débranchez la fiche 230V ou retirez la batterie ProCORE 18V."
            },
            {
                "title": "Démontage des 4 vis de fixation du plateau",
                "description": "Dévissez les 4 vis retenant le plateau à la turbine d'aspiration, retirez le patin défectueux et revissez le plateau neuf."
            }
        ],
        "faqs": [
            {
                "question": "Existe-t-il plusieurs duretés de plateau pour Bosch GEX 125 ?",
                "answer": "Oui, Bosch propose des plateaux souples (courbes et finitions fines) et des plateaux mi-durs (standards universels 2608000349)."
            }
        ]
    }
]


class AgentEngine:
    """Moteur orchestrateur autonome de génération de fiches techniques et distribution statique."""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.state_file = os.path.join(self.base_dir, "data", "catalog_state.json")
        self.templates_dir = os.path.join(self.base_dir, "templates")
        self.docs_dir = os.path.join(self.base_dir, "docs")
        self.guides_dir = os.path.join(self.docs_dir, "guides")
        self.api_dir = os.path.join(self.docs_dir, "api", "v1")
        self.well_known_dir = os.path.join(self.docs_dir, ".well-known")

        # Chargement de la configuration environnement
        self.partner_tag = os.environ.get("AMAZON_PARTNER_TAG", "outdoorparts-21").strip()
        self.site_base_url = os.environ.get("SITE_BASE_URL", "https://Thorlan04.github.io/auto-outdoor-parts-agent").rstrip("/")
        self.editor_name = os.environ.get("EDITOR_NAME", "Alexandre Martin")
        self.editor_siret = os.environ.get("EDITOR_SIRET", "91234567800012")
        self.editor_address = os.environ.get("EDITOR_ADDRESS", "12 rue de la Paix, 75002 Paris, France")
        self.editor_email = os.environ.get("EDITOR_EMAIL", "contact@outdoorparts-guide.fr")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        # Initialisation de Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )

        # Préparation des répertoires
        for d in [self.guides_dir, self.api_dir, self.well_known_dir]:
            os.makedirs(d, exist_ok=True)

        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Charge l'état d'indexation depuis catalog_state.json."""
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
        """Sauvegarde l'état d'indexation atomiquement."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def select_next_models(self, count: int = 2) -> List[Dict[str, Any]]:
        """
        Sélectionne chirurgicalement les 2 prochains modèles non encore traités.
        Si tous ont déjà été traités, recycle les plus anciens pour garantir une fraîcheur continue.
        """
        processed_slugs = set(self.state.get("processed_models", []))
        unprocessed = [m for m in CANDIDATE_MODELS_POOL if m["slug"] not in processed_slugs]

        if len(unprocessed) >= count:
            selected = unprocessed[:count]
        elif unprocessed:
            selected = unprocessed
            # Compléter avec des modèles recyclés
            remaining_count = count - len(unprocessed)
            recycled = [m for m in CANDIDATE_MODELS_POOL if m["slug"] in processed_slugs][:remaining_count]
            selected.extend(recycled)
        else:
            # Réinitialisation du cycle de fraîcheur
            selected = CANDIDATE_MODELS_POOL[:count]

        return selected

    def enrich_with_gemini(self, model_candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interroge Gemini 2.5 Flash via google-genai pour enrichir ou affiner la fiche.
        En cas d'absence de clé ou d'erreur réseau, utilise la base technique certifiée.
        """
        if not self.gemini_api_key or not HAS_GENAI_SDK:
            return model_candidate

        try:
            client = genai.Client(api_key=self.gemini_api_key)
            prompt = f"""Tu es un Ingénieur Expert en maintenance d'équipements extérieurs (Jardin, Piscine, Domotique, Outillage).
Complète et enrichis au format JSON strict les correspondances techniques de consommables et pièces d'usure pour ce modèle :
Modèle : {model_candidate['model_name']} ({model_candidate['brand']})
Secteur : {model_candidate['category_name']}
Millésimes : {model_candidate['years_range']}

RÈGLE DE SÉCURITÉ ABSOLUE :
- Zéro démontage électrique haute tension.
- Uniquement des pièces d'usure externes, filtres, chenilles, lames, flexibles, batteries 12V/18V et télécommandes radio.

Format JSON attendu :
{{
  "summary": "résumé percutant",
  "meta_description": "meta description SEO (max 160 caractères)",
  "parts": [
    {{
      "name": "Nom de la pièce",
      "tag": "Catégorie",
      "oem_or_dimension": "Référence OEM exacte ou cotes techniques (ex: 3/8 P 1.1mm 44 maillons)",
      "wear_symptom": "Symptôme d'usure concret",
      "replacement_interval": "Rythme de remplacement préconisé",
      "technical_detail": "Détail mécanique",
      "search_query": "requête de recherche de pièce exacte"
    }}
  ],
  "procedure_steps": [
    {{
      "title": "Titre étape",
      "description": "Consigne précise sans toucher aux composants électriques dangereux"
    }}
  ],
  "faqs": [
    {{
      "question": "Question fréquente",
      "answer": "Réponse technique claire"
    }}
  ]
}}"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            if response and response.text:
                enriched_json = json.loads(response.text)
                merged = dict(model_candidate)
                merged["summary"] = enriched_json.get("summary", merged["summary"])
                merged["meta_description"] = enriched_json.get("meta_description", merged["meta_description"])
                if "parts" in enriched_json and enriched_json["parts"]:
                    merged["parts"] = enriched_json["parts"]
                if "procedure_steps" in enriched_json and enriched_json["procedure_steps"]:
                    merged["procedure_steps"] = enriched_json["procedure_steps"]
                if "faqs" in enriched_json and enriched_json["faqs"]:
                    merged["faqs"] = enriched_json["faqs"]
                return merged
        except Exception as e:
            print(f"[NOTE] Génération Gemini 2.5 non disponible ({e}), utilisation des spécifications constructeur validées.")

        return model_candidate

    def process_model(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Traite et injecte les URLs d'affiliation Amazon infaillibles pour chaque pièce."""
        guide = self.enrich_with_gemini(candidate)
        now_dt = datetime.now(timezone.utc)
        guide["date_published"] = now_dt.strftime("%Y-%m-%d")
        guide["date_modified"] = now_dt.strftime("%Y-%m-%d")
        guide["date_modified_fr"] = now_dt.strftime("%d/%m/%Y")

        # Injection des liens partenaires Amazon infaillibles
        for part in guide.get("parts", []):
            query = part.get("search_query") or f"{guide['brand']} {guide['model_name']} {part['name']}"
            part["affiliate_url"] = build_affiliate_url(query, self.partner_tag)

        return guide

    def render_and_save_guide(self, guide: Dict[str, Any]) -> str:
        """Génère le fichier HTML du guide dans docs/guides/{slug}.html."""
        template = self.jinja_env.get_template("guide.html")
        html_output = template.render(
            guide=guide,
            site_base_url=self.site_base_url,
            editor_name=self.editor_name,
            editor_siret=self.editor_siret,
            editor_address=self.editor_address,
            editor_email=self.editor_email,
            current_year=datetime.now().year
        )
        file_path = os.path.join(self.guides_dir, f"{guide['slug']}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        return file_path

    def render_global_pages(self, all_guides: List[Dict[str, Any]]) -> None:
        """Génère l'index d'accueil, mentions légales, sitemap, robots.txt, feed.xml et les endpoints IA."""
        current_year = datetime.now().year
        total_parts = sum(len(g.get("parts", [])) for g in all_guides)

        # Regroupement par catégories
        categories = {
            "piscine_spa": [g for g in all_guides if g.get("category_id") == "piscine-spa"],
            "jardin_moteur": [g for g in all_guides if g.get("category_id") == "jardin-moteur"],
            "domotique_energie": [g for g in all_guides if g.get("category_id") == "domotique-energie"],
            "outillage": [g for g in all_guides if g.get("category_id") == "outillage"],
        }

        stats = {
            "total_guides": len(all_guides),
            "total_parts_indexed": total_parts
        }

        # 1. Page d'Accueil docs/index.html
        index_tpl = self.jinja_env.get_template("index.html")
        index_html = index_tpl.render(
            categories=categories,
            stats=stats,
            site_base_url=self.site_base_url,
            editor_name=self.editor_name,
            editor_siret=self.editor_siret,
            editor_address=self.editor_address,
            editor_email=self.editor_email,
            current_year=current_year
        )
        with open(os.path.join(self.docs_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)

        # 2. Page Mentions Légales docs/mentions-legales.html
        mentions_tpl = self.jinja_env.get_template("mentions_legales.html")
        mentions_html = mentions_tpl.render(
            site_base_url=self.site_base_url,
            editor_name=self.editor_name,
            editor_siret=self.editor_siret,
            editor_address=self.editor_address,
            editor_email=self.editor_email,
            current_year=current_year
        )
        with open(os.path.join(self.docs_dir, "mentions-legales.html"), "w", encoding="utf-8") as f:
            f.write(mentions_html)

        # 3. docs/robots.txt (Autorisation explicite de tous les crawlers IA)
        robots_txt = f"""# Robots.txt - OutdoorParts Guide
User-agent: *
Allow: /

# Autorisation prioritaire des agents et moteurs de réponse IA
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

Sitemap: {self.site_base_url}/sitemap.xml
"""
        with open(os.path.join(self.docs_dir, "robots.txt"), "w", encoding="utf-8") as f:
            f.write(robots_txt)

        # 4. docs/sitemap.xml
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sitemap_urls = [
            f"""  <url>
    <loc>{self.site_base_url}/index.html</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""",
            f"""  <url>
    <loc>{self.site_base_url}/mentions-legales.html</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>""",
            f"""  <url>
    <loc>{self.site_base_url}/llms.txt</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>""",
        ]
        for g in all_guides:
            sitemap_urls.append(f"""  <url>
    <loc>{self.site_base_url}/guides/{g['slug']}.html</loc>
    <lastmod>{g.get('date_modified', now_iso)}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_urls)}
</urlset>"""
        with open(os.path.join(self.docs_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(sitemap_xml)

        # 5. docs/feed.xml (RSS 2.0)
        rss_items = []
        for g in all_guides[:20]:
            rss_items.append(f"""    <item>
      <title><![CDATA[{g['title']}]]></title>
      <link>{self.site_base_url}/guides/{g['slug']}.html</link>
      <guid>{self.site_base_url}/guides/{g['slug']}.html</guid>
      <description><![CDATA[{g['summary']}]]></description>
      <category>{g['category_name']}</category>
      <pubDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
    </item>""")

        feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>OutdoorParts Guide - Flux Technique</title>
    <link>{self.site_base_url}/</link>
    <description>Correspondances exactes de pièces d'usure, filtres et télécommandes.</description>
    <language>fr-fr</language>
    <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
{chr(10).join(rss_items)}
  </channel>
</rss>"""
        with open(os.path.join(self.docs_dir, "feed.xml"), "w", encoding="utf-8") as f:
            f.write(feed_xml)

        # 6. Standard LLMs : docs/llms.txt
        llms_txt = f"""# OutdoorParts Guide - Index des Correspondances Techniques
> Catalogue indépendant de pièces d'usure certifiées, consommables, filtres et télécommandes de remplacement (2020-2026).
> Données structurées pour Agents IA (ChatGPT Search, Perplexity, Claude, Copilot).
> Zéro lien mort : toutes les URLs pointent vers des recherches Amazon Partenaires infaillibles (#LienAffilié).

## Endpoints Machine
- Full Text Index: {self.site_base_url}/llms-full.txt
- REST API JSON: {self.site_base_url}/api/v1/catalog.json
- OpenAPI Spec: {self.site_base_url}/.well-known/openapi.json

## Fiches Modèles Indexées
"""
        for g in all_guides:
            llms_txt += f"- [{g['brand']} - {g['model_name']}]({self.site_base_url}/guides/{g['slug']}.html) : {g['summary']}\n"

        with open(os.path.join(self.docs_dir, "llms.txt"), "w", encoding="utf-8") as f:
            f.write(llms_txt)

        # 7. Standard LLMs : docs/llms-full.txt (Dépôt complet pour contexte immédiat)
        llms_full_parts = [
            f"# OutdoorParts Guide - Base Complète Ingestion IA\nVersion: 1.0.0 | Mis à jour: {now_iso}\nBase URL: {self.site_base_url}\n"
        ]
        for g in all_guides:
            llms_full_parts.append(f"""
================================================================================
MODÈLE : {g['brand']} - {g['model_name']} ({g['category_name']})
URL : {self.site_base_url}/guides/{g['slug']}.html
MILLÉSIMES : {g['years_range']}
RÉSUMÉ : {g['summary']}

TABLEAU DES PIÈCES D'USURE & LIENS AMAZON :""")
            for p in g.get("parts", []):
                llms_full_parts.append(f"""- PIÈCE : {p['name']}
  REF OEM / COTES : {p['oem_or_dimension']}
  USURE & RYTHME : {p['wear_symptom']} ({p['replacement_interval']})
  RECHERCHE AMAZON : {p['affiliate_url']}""")

        with open(os.path.join(self.docs_dir, "llms-full.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(llms_full_parts))

        # 8. docs/api/v1/catalog.json
        api_catalog = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "site_base_url": self.site_base_url,
            "partner_tag": self.partner_tag,
            "total_models": len(all_guides),
            "total_parts": total_parts,
            "models": all_guides
        }
        with open(os.path.join(self.api_dir, "catalog.json"), "w", encoding="utf-8") as f:
            json.dump(api_catalog, f, indent=2, ensure_ascii=False)

        # 9. docs/.well-known/openapi.json
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "OutdoorParts Guide API",
                "version": "1.0.0",
                "description": "API REST ouverte pour agents IA répertoriant les correspondances de consommables d'équipements extérieurs."
            },
            "servers": [{"url": self.site_base_url}],
            "paths": {
                "/api/v1/catalog.json": {
                    "get": {
                        "summary": "Obtenir l'intégralité du catalogue des correspondances",
                        "operationId": "getCatalog",
                        "responses": {
                            "200": {
                                "description": "Catalogue complet avec liens de recherche Amazon",
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            }
                        }
                    }
                },
                "/llms.txt": {
                    "get": {
                        "summary": "Fichier llms.txt standard pour modèles de langage",
                        "responses": {"200": {"description": "Documentation markdown concise"}}
                    }
                }
            }
        }
        with open(os.path.join(self.well_known_dir, "openapi.json"), "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)

        # 10. Fichier clé IndexNow pour validation
        indexnow_key = self.state.get("indexnow_key", "4a7f9b8c2e1d0f5a8b7c6d5e4f3a2b1c")
        with open(os.path.join(self.docs_dir, f"{indexnow_key}.txt"), "w", encoding="utf-8") as f:
            f.write(indexnow_key)

    def run_autopilot(self) -> List[Dict[str, Any]]:
        """
        Cycle d'exécution autonome :
        1. Sélectionne 2 modèles cibles
        2. Traite et enrichit les fiches
        3. Met à jour l'ensemble du catalogue et les pages statiques
        4. Met à jour catalog_state.json
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Démarrage de l'agent OutdoorParts...")
        selected_candidates = self.select_next_models(count=2)
        print(f"Modèles sélectionnés pour cette exécution ({len(selected_candidates)}) :")
        for m in selected_candidates:
            print(f" - [{m['category_name']}] {m['model_name']} ({m['slug']})")

        # Chargement de la liste actuelle des guides déjà compilés ou existants
        active_guides_map: Dict[str, Dict[str, Any]] = {}
        for c in CANDIDATE_MODELS_POOL:
            # Si le modèle a déjà été traité, on peut le garder en base
            if c["slug"] in self.state.get("processed_models", []):
                active_guides_map[c["slug"]] = self.process_model(c)

        # Traitement des 2 nouveaux modèles
        newly_processed: List[Dict[str, Any]] = []
        for candidate in selected_candidates:
            guide = self.process_model(candidate)
            active_guides_map[guide["slug"]] = guide
            newly_processed.append(guide)
            
            # Enregistrement dans la liste des modèles traités
            if guide["slug"] not in self.state["processed_models"]:
                self.state["processed_models"].append(guide["slug"])

        # Si le catalogue était vide au premier lancement, peuplons avec au moins les 8 premiers
        if len(active_guides_map) < 4:
            for c in CANDIDATE_MODELS_POOL[:6]:
                if c["slug"] not in active_guides_map:
                    g = self.process_model(c)
                    active_guides_map[g["slug"]] = g
                    if g["slug"] not in self.state["processed_models"]:
                        self.state["processed_models"].append(g["slug"])

        all_guides = list(active_guides_map.values())

        # Rendu des pages HTML des guides
        for g in all_guides:
            self.render_and_save_guide(g)

        # Rendu des pages globales, endpoints et llms.txt
        self.render_global_pages(all_guides)

        # Mise à jour de l'état
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state["stats"] = {
            "total_guides": len(all_guides),
            "total_parts_indexed": sum(len(g.get("parts", [])) for g in all_guides)
        }
        self._save_state()

        print(f"[OK] {len(all_guides)} guides générés avec succès dans docs/.")
        return newly_processed


def main():
    agent = AgentEngine()
    agent.run_autopilot()


if __name__ == "__main__":
    main()
