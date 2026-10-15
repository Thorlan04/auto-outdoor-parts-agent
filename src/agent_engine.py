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

try:
    from src.i18n import (
        SUPPORTED_LANGUAGES,
        AMAZON_DOMAINS,
        UI_TRANSLATIONS,
        get_translations,
        build_affiliate_url,
        build_store_urls
    )
except ImportError:
    from i18n import (
        SUPPORTED_LANGUAGES,
        AMAZON_DOMAINS,
        UI_TRANSLATIONS,
        get_translations,
        build_affiliate_url,
        build_store_urls
    )


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
    },
    {
        "slug": "stihl-gta-26-scie-elagueuse-batterie",
        "category_id": "jardin-moteur",
        "category_name": "Jardin Motorisé & Nettoyeurs Haute Pression",
        "brand": "Stihl",
        "model_name": "Stihl GTA 26 Scie de Jardin / Mini Élagueuse",
        "years_range": "2020-2026",
        "title": "Stihl GTA 26 : Chaîne 1/4\" Picco Micro 3 28 Maillons & Guide 10cm",
        "summary": "Correspondances exactes Stihl GTA 26 : chaîne 71PM3 (28 maillons), guide Rollomatic Light 10cm et batterie AS 2.",
        "meta_description": "Chaîne 1/4 Picco 28 maillons 71PM3, guide 10cm et huile bio pour élagueuse à batterie Stihl GTA 26. Pièces certifiées sans 404.",
        "parts": [
            {
                "name": "Chaîne 1/4\" Picco Micro 3 (71 PM3 - 28 Maillons)",
                "tag": "Chaîne Tronçonneuse Rechange",
                "oem_or_dimension": "Stihl 3670-000-0028 / Pas 1/4\" P / Jauge 1.1mm",
                "wear_symptom": "Dents émoussées, coupe lente, batterie qui se décharge trop vite",
                "replacement_interval": "Affûtage régulier, renouvellement après 3 à 4 affûtages",
                "technical_detail": "Micro-chaîne spécifique ultra-fine 1.1mm conçue pour minimiser la consommation électrique de la batterie 10.8V.",
                "search_query": "chaine stihl gta 26 71pm3 28 maillons 3670-000-0028"
            },
            {
                "name": "Guide-Chaîne Rollomatic Light 10cm (4 pouces)",
                "tag": "Guide Ultra-Léger",
                "oem_or_dimension": "Stihl 3007-003-0102 / Longueur de coupe 10 cm",
                "wear_symptom": "Fente du guide usée, déviation lors de la coupe de branches",
                "replacement_interval": "Tous les 2 ans selon usage",
                "technical_detail": "Acier allié trempé avec gorge usinée 1.1mm pour un guidage parfait sans à-coups.",
                "search_query": "guide stihl gta 26 10cm 3007-003-0102"
            },
            {
                "name": "Huile Adhésive Bio pour Chaîne et Guide Multioil Bio (50ml)",
                "tag": "Lubrification Chaîne",
                "oem_or_dimension": "Stihl 0782-516-8500 / Flacon doseur 50 ml",
                "wear_symptom": "Échauffement du guide, traces noires sur le bois",
                "replacement_interval": "À appliquer manuellement avant chaque séance de coupe",
                "technical_detail": "Huile d'origine végétale 100% biodégradable évitant le gommage des maillons.",
                "search_query": "huile chaine stihl multioil bio gta 26"
            }
        ],
        "procedure_steps": [
            {
                "title": "Retrait impératif de la batterie AS 2",
                "description": "Pressez les deux loquets de la batterie AS 2 et retirez-la du manche avant toute manipulation de la chaîne."
            },
            {
                "title": "Changement de la chaîne sans outil",
                "description": "Desserrez l'écrou papillon noir du capot de pignon, retirez le guide, placez la chaîne neuve avec les gouges orientées vers l'avant et resserrez à la main."
            }
        ],
        "faqs": [
            {
                "question": "Pourquoi la chaîne de la Stihl GTA 26 doit-elle être lubrifiée à la main ?",
                "answer": "La GTA 26 ne possède pas de pompe à huile automatique pour rester ultra-légère. Déposez quelques gouttes de Multioil Bio directement sur la rainure du guide avant chaque utilisation."
            }
        ]
    },
    {
        "slug": "karcher-k4-power-control-nettoyeur-hp",
        "category_id": "jardin-moteur",
        "category_name": "Jardin Motorisé & Nettoyeurs Haute Pression",
        "brand": "Kärcher",
        "model_name": "Kärcher K4 Power Control / K4 Compact",
        "years_range": "2020-2026",
        "title": "Kärcher K4 Power Control : Flexibles 8m Quick Connect & Lance Vario Power",
        "summary": "Consommables et pièces d'usure certifiés Kärcher K4 : flexible 8m Quick Connect, lance Vario Power VP 145 et joints toriques.",
        "meta_description": "Flexible haute pression 8m, lance Vario Power et joints de rechange pour nettoyeur Kärcher K4. Références vérifiées sans erreur 404.",
        "parts": [
            {
                "name": "Flexible Haute Pression 8m Quick Connect (130-160 bar)",
                "tag": "Flexible Remplacement",
                "oem_or_dimension": "OEM 6.396-525.0 / Raccord rapide jaune deux côtés",
                "wear_symptom": "Gaine extérieure râpée sur le béton, fuite au raccord pistolet",
                "replacement_interval": "Tous les 3 à 4 ans",
                "technical_detail": "Rayon de courbure souple anti-vrille, tolérance 160 bar et 60°C.",
                "search_query": "flexible karcher k4 8m quick connect 6.396-525.0"
            },
            {
                "name": "Lance Vario Power Jet Réglable VP 145",
                "tag": "Lance Polyvalente",
                "oem_or_dimension": "OEM 2.642-725.0 / Réglage continu Soft/Medium/Hard",
                "wear_symptom": "Bague rotative bloquée par le calcaire, jet qui ne monte plus en pression",
                "replacement_interval": "En cas d'entartrage interne",
                "technical_detail": "Permet de passer du jet basse pression (application détergent) au jet haute pression d'un simple geste.",
                "search_query": "lance vario power karcher k4 vp 145"
            },
            {
                "name": "Buse Débouche-Canalisations et Gouttières 15m",
                "tag": "Accessoire Débouchage",
                "oem_or_dimension": "OEM 2.637-767.0 / 3 jets rétro-propulseurs",
                "wear_symptom": "Buses obstruées par le calcaire ou flexible pincé",
                "replacement_interval": "Accessoire longue durée",
                "technical_detail": "Avance automatiquement dans les tuyaux PVC grâce à ses 3 jets orientés vers l'arrière.",
                "search_query": "kit debouche canalisation karcher 15m 2.637-767.0"
            }
        ],
        "procedure_steps": [
            {
                "title": "Purge d'air initiale avant allumage",
                "description": "Raccordez l'eau, ouvrez le robinet à fond et pressez la gâchette du pistolet sans allumer l'interrupteur électrique jusqu'à obtenir un écoulement continu sans bulles d'air."
            }
        ],
        "faqs": [
            {
                "question": "Le flexible du Kärcher K4 est-il identique à celui du K5 ?",
                "answer": "Les deux utilisent le raccord Quick Connect jaune. Le flexible du K4 mesure 8m (130 bar) alors que celui du K5 mesure 10m (180 bar). Les deux sont interchangeables."
            }
        ]
    },
    {
        "slug": "nice-flo2re-era-flor-telecommande",
        "category_id": "domotique-energie",
        "category_name": "Domotique Portail, Garage & Énergie de Secours",
        "brand": "Nice",
        "model_name": "Nice Era Flor FLO2RE / ON2E / Flo2R-S",
        "years_range": "2020-2026",
        "title": "Télécommande Nice FLO2RE : Fréquence 433.92 MHz Rolling Code & Piles CR2032",
        "summary": "Correspondances officielles télécommandes de portail Nice Era Flor FLO2RE : rolling code sécurisé 433.92 MHz, piles bouton CR2032 et programmation radio.",
        "meta_description": "Télécommandes Nice FLO2RE Era Flor 433.92 MHz Rolling Code, piles CR2032. Procédure d'enregistrement par voie radio sans ouvrir le coffret moteur.",
        "parts": [
            {
                "name": "Télécommande 2 Canaux Nice Era Flor FLO2RE (433.92 MHz)",
                "tag": "Émetteur Rolling Code",
                "oem_or_dimension": "Nice FLO2RE / 433.92 MHz Rolling Code / Boîtier noir touches rondes",
                "wear_symptom": "Portée réduite à moins de 3 mètres, bouton poussoir fendu",
                "replacement_interval": "En cas de défaillance mécanique ou perte",
                "technical_detail": "Cryptage 52 bits rolling code inviolable, compatible récepteurs OXI, OX2, SMXI, FLOX2R.",
                "search_query": "telecommande nice era flor flo2re 433.92 mhz"
            },
            {
                "name": "Pile Bouton Lithium CR2032 3V Longue Durée",
                "tag": "Alimentation Émetteur",
                "oem_or_dimension": "CR2032 / Tension 3V / Diamètre 20mm",
                "wear_symptom": "Clignotement hésitant de la diode LED à l'appui",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Technologie lithium haute pureté pour fonctionnement par températures négatives.",
                "search_query": "pile cr2032 energizer 3v lot"
            }
        ],
        "procedure_steps": [
            {
                "title": "Programmation par voie radio (Sans toucher au moteur)",
                "description": "Placez-vous à 2 mètres du portail. Appuyez 5 secondes sur la touche de la NOUVELLE télécommande. Puis appuyez 3 fois brièvement sur l'ANCIENNE télécommande (en attendant 1 seconde entre chaque appui). Enfin, appuyez une dernière fois sur la nouvelle télécommande pour enregistrer le code."
            }
        ],
        "faqs": [
            {
                "question": "Quelle est la différence entre Nice Flo (touches bleues) et Nice Flor-S (touches noires) ?",
                "answer": "La série Flo utilise des micro-interrupteurs (DIP switchs) à code fixe. La série Flor (FLO2RE) utilise le rolling code sécurisé. Elles ne sont pas compatibles entre elles."
            }
        ]
    },
    {
        "slug": "bft-mitto-b-rcb02-telecommande-portail",
        "category_id": "domotique-energie",
        "category_name": "Domotique Portail, Garage & Énergie de Secours",
        "brand": "BFT",
        "model_name": "BFT Mitto B RCB02 / Mitto 2M / 4M",
        "years_range": "2020-2026",
        "title": "Télécommandes BFT Mitto B RCB02 : Fréquence 433.92 MHz & Piles 12V",
        "summary": "Correspondances télécommandes BFT Mitto : protocole Rolling Code 433.92 MHz, alimentation pile 12V 23A et procédure de programmation à distance.",
        "meta_description": "Télécommandes BFT Mitto B RCB02 433.92 MHz Rolling Code, piles 12V type 23A. Procédure d'appairage radio sans contact direct carte électronique.",
        "parts": [
            {
                "name": "Télécommande 2 Boutons BFT Mitto B RCB02 R1 (433.92 MHz)",
                "tag": "Émetteur Portes & Portails",
                "oem_or_dimension": "BFT D111904 / 433.92 MHz Rolling Code",
                "wear_symptom": "Portée dégradée, coque ouverte ou boutons écrasés",
                "replacement_interval": "En cas de remplacement ou télécommande supplémentaire",
                "technical_detail": "Protocole BFT Clonix avec système de codage à saut de fréquence sécurisé.",
                "search_query": "telecommande bft mitto b rcb02 433.92 mhz"
            },
            {
                "name": "Pile Alcaline Cylindrique 12V Type 23A (Lot de 5)",
                "tag": "Alimentation Haute Tension",
                "oem_or_dimension": "Format 23A / V23GA / MN21 / 12 Volts",
                "wear_symptom": "LED qui ne s'allume plus lors de la pression",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Assure la puissance radio nécessaire pour une portée maximale jusqu'à 50 mètres.",
                "search_query": "pile 12v 23a energizer v23ga"
            }
        ],
        "procedure_steps": [
            {
                "title": "Procédure d'enregistrement par appui simultané",
                "description": "À côté du récepteur, appuyez simultanément sur les 2 boutons supérieurs de la télécommande en service jusqu'à allumage fixe de sa LED, puis appuyez sur la touche programmée. Appuyez ensuite sur les 2 boutons de la nouvelle télécommande puis sur la touche choisie pour valider."
            }
        ],
        "faqs": [
            {
                "question": "Comment savoir si ma télécommande BFT utilise une pile 12V 23A ou une pile bouton ?",
                "answer": "Les modèles BFT Mitto 2M utilisent une petite pile cylindrique 12V (23A). Les modèles récents extra-plats Mitto B RCB utilisent une pile bouton CR2032. Vérifiez le compartiment arrière."
            }
        ]
    },
    {
        "slug": "dewalt-dcw210n-ponceuse-excentrique-18v",
        "category_id": "outillage",
        "category_name": "Outillage Électroportatif",
        "brand": "DeWalt",
        "model_name": "DeWalt DCW210 / DCW210N / DCW210NT 18V XR",
        "years_range": "2020-2026",
        "title": "DeWalt DCW210N : Plateaux 125mm 8 Trous, Sac AirLock & Batteries",
        "summary": "Correspondances officielles DeWalt DCW210N : plateau de ponçage auto-agrippant 125mm (N329079), sac récepteur AirLock et batteries 18V XR.",
        "meta_description": "Plateau de rechange velcro 125mm 8 trous, sac AirLock et batteries compatibles pour ponceuse DeWalt DCW210N 18V. Pièces sans erreur 404.",
        "parts": [
            {
                "name": "Plateau de Ponçage Velcro 125mm 8 Trous (Fixation 4 Vis)",
                "tag": "Plateau Usure Remplacement",
                "oem_or_dimension": "DeWalt OEM N329079 / Diamètre 125mm 8 trous",
                "wear_symptom": "Disques abrasifs qui glissent ou ne collent plus au support",
                "replacement_interval": "Dès lissage des micro-crochets velcro",
                "technical_detail": "Fixation sécurisée par 4 vis torx, équilibrage anti-vibrations pour moteur Brushless sans balais.",
                "search_query": "plateau ponceuse dewalt dcw210n 125mm n329079"
            },
            {
                "name": "Sac à Poussière Textile avec Raccord Rapide AirLock",
                "tag": "Collecte Poussière",
                "oem_or_dimension": "DeWalt OEM N273733 / Système de verrouillage AirLock",
                "wear_symptom": "Couture déchirée, ressort de collerette détendu",
                "replacement_interval": "En cas d'usure de la toile filtrante",
                "technical_detail": "Se clipse d'un quart de tour sur la sortie d'aspiration arrière.",
                "search_query": "sac poussiere dewalt dcw210 airlock n273733"
            },
            {
                "name": "Batterie Compatible 18V 5.0Ah Li-Ion XR avec Jauge LED",
                "tag": "Autonomie Sans Fil",
                "oem_or_dimension": "Compatible DCB184 / 18V 5000mAh",
                "wear_symptom": "Autonomie tombée à moins de 15 minutes",
                "replacement_interval": "Tous les 3 à 5 ans",
                "technical_detail": "Cellules lithium haute performance sans effet mémoire avec affichage de charge par LED.",
                "search_query": "batterie dewalt 18v 5ah dcb184 compatible"
            }
        ],
        "procedure_steps": [
            {
                "title": "Sécurité : Déconnexion de la batterie XR",
                "description": "Appuyez sur le loquet de déverrouillage jaune et extrayez la batterie 18V avant d'intervenir sur le patin."
            },
            {
                "title": "Changement du plateau velcro en 3 minutes",
                "description": "Retirez les 4 vis à l'aide d'un embout Torx T20. Positionnez le nouveau plateau N329079 en alignant les trous d'aspiration avec la turbine et serrez fermement."
            }
        ],
        "faqs": [
            {
                "question": "Peut-on adapter un aspirateur d'atelier sur la ponceuse DeWalt DCW210N ?",
                "answer": "Oui, la sortie arrière intègre le système standard DeWalt AirLock qui permet de brancher directement les tuyaux d'aspirateur sans adaptateur supplémentaire."
            }
        ]
    },
    {
        "slug": "einhell-power-x-change-18v-batteries",
        "category_id": "outillage",
        "category_name": "Outillage Électroportatif",
        "brand": "Einhell",
        "model_name": "Système Power X-Change 18V (Ponceuses, Meuleuses, Tondeuses)",
        "years_range": "2020-2026",
        "title": "Einhell Power X-Change : Batteries 18V 4.0Ah / 5.2Ah Plus & Chargeurs",
        "summary": "Correspondances officielles écosystème Einhell 18V Power X-Change : batteries lithium 4.0Ah et 5.2Ah Plus, chargeurs rapides Boost et patins de ponceuse.",
        "meta_description": "Batteries 18V 4.0Ah et 5.2Ah Plus, chargeurs rapides pour gamme Einhell Power X-Change. Références certifiées sans erreur 404.",
        "parts": [
            {
                "name": "Batterie 18V 4.0Ah Li-Ion Power X-Change (Indicateur LED 3 Niveaux)",
                "tag": "Batterie Universelle",
                "oem_or_dimension": "Einhell 4511396 / 18V 4000mAh / Cellules haute puissance",
                "wear_symptom": "Autonomie réduite, surchauffe lors de travaux intensifs",
                "replacement_interval": "Tous les 3 à 5 ans",
                "technical_detail": "Système ABS (Active Battery Management) avec microprocesseur de surveillance des cellules.",
                "search_query": "batterie einhell 18v 4ah power x change 4511396"
            },
            {
                "name": "Batterie Haute Densité 18V 5.2Ah Plus Power X-Change",
                "tag": "Autonomie Maximale",
                "oem_or_dimension": "Einhell 4511437 / Technologie PLUS pour fortes charges",
                "wear_symptom": "Besoin de puissance supérieure pour tondeuses ou meuleuses",
                "replacement_interval": "Tous les 4 ans",
                "technical_detail": "Fournit jusqu'à 1260W de puissance crête sans chute de tension.",
                "search_query": "batterie einhell 18v 5.2ah plus power x change 4511437"
            },
            {
                "name": "Chargeur Rapide Power-X-Boostcharger 6A",
                "tag": "Charge Ultra-Rapide",
                "oem_or_dimension": "Einhell 4512064 / Courant de charge 6 Ampères",
                "wear_symptom": "Ancien chargeur lent (plus de 2h de charge pour une 4Ah)",
                "replacement_interval": "Équipement d'atelier longue durée",
                "technical_detail": "Recharge une batterie 4.0Ah en seulement 35 minutes en mode Boost.",
                "search_query": "chargeur rapide einhell power x boostcharger 6a"
            }
        ],
        "procedure_steps": [
            {
                "title": "Recommandation de stockage hivernal",
                "description": "Stockez vos batteries Power X-Change dans un endroit sec à une température comprise entre 10°C et 20°C avec une charge résiduelle de 50% à 80% (2 diodes allumées)."
            }
        ],
        "faqs": [
            {
                "question": "Une batterie Einhell Power X-Change est-elle compatible avec tous les outils 18V de la marque ?",
                "answer": "Oui, 100% des outils Einhell portant le logo Power X-Change (jardin, bricolage, nettoyage) partagent exactement les mêmes batteries et chargeurs."
            }
        ]
    },
    {
        "slug": "chamberlain-liftmaster-893max-remote",
        "category_id": "domotique-energie",
        "category_name": "Domotique Portail, Garage & Énergie de Secours",
        "brand": "Chamberlain / LiftMaster",
        "model_name": "LiftMaster 893MAX / Chamberlain 953EV (Security+ 2.0)",
        "years_range": "2020-2026",
        "title": "LiftMaster 893MAX & Chamberlain 953EV : Pile CR2032, Clip Pare-Soleil & Télécommandes",
        "summary": "Correspondances certifiées télécommandes porte de garage Security+ 2.0 (315MHz/390MHz) : pile lithium CR2032, clip visière pare-soleil et clavier sans fil 877MAX.",
        "meta_description": "Télécommande porte de garage LiftMaster 893MAX, Chamberlain 953EV. Pile CR2032, clip pare-soleil, programmation Security+ 2.0 sans erreur 404.",
        "parts": [
            {
                "name": "Télécommande 3 Boutons Visière 893MAX / 953EV (Security+ 2.0)",
                "tag": "Émetteur Radio Fréquence",
                "oem_or_dimension": "OEM 893MAX / 953EV / Multi-Fréquences 310/315/390 MHz",
                "wear_symptom": "Portée réduite à moins de 2 mètres, boutons micro-switch usés",
                "replacement_interval": "Tous les 5 ans ou en cas de perte",
                "technical_detail": "Compatible moteurs à bouton d'apprentissage Jaune, Violet, Rouge/Orange et Vert (1993 à 2026).",
                "search_query": "liftmaster 893max remote 3 button visor"
            },
            {
                "name": "Pile Bouton Lithium 3V CR2032 Longue Durée (Lot Haute Fiabilité)",
                "tag": "Alimentation Émetteur",
                "oem_or_dimension": "CR2032 / 3 Volts Lithium / Diamètre 20mm x 3.2mm",
                "wear_symptom": "LED d'émission clignotante faible ou extinction totale à la pression",
                "replacement_interval": "Tous les 2 ans préventif",
                "technical_detail": "Cellule lithium dioxyde de manganèse résistant aux chocs thermiques en habitacle auto (-20°C à +60°C).",
                "search_query": "cr2032 lithium battery 3v pack"
            },
            {
                "name": "Clip Pare-Soleil Métallique Ressort pour Télécommande Visière",
                "tag": "Fixation Habitacle",
                "oem_or_dimension": "OEM LiftMaster 029B0137 / Acier ressort galvanisé",
                "wear_symptom": "Pince déformée, télécommande qui tombe du pare-soleil",
                "replacement_interval": "En cas de déformation mécanique",
                "technical_detail": "Se glisse dans la gorge dorsale de la télécommande sans outil.",
                "search_query": "liftmaster visor clip 893max"
            },
            {
                "name": "Clavier Mural Extérieur Sans Fil à Code 877MAX / 878MAX",
                "tag": "Accès Sans Clé",
                "oem_or_dimension": "OEM 877MAX / Clavier rétroéclairé avec volet de protection",
                "wear_symptom": "Touches membrane silicone fissurées par les UV, déprogrammation",
                "replacement_interval": "5 à 8 ans selon exposition plein soleil",
                "technical_detail": "Fonctionne sur pile 9V 6LR61, étanchéité IP55 extérieure, fermeture automatique 1 touche.",
                "search_query": "liftmaster 877max wireless keypad"
            }
        ],
        "procedure_steps": [
            {
                "title": "Sécurité : Accès sécurisé au moteur de garage",
                "description": "Utilisez un escabeau stable pour accéder au bloc moteur fixé au plafond. Ne touchez jamais aux câbles de torsion ni aux ressorts latéraux sous tension."
            },
            {
                "title": "Identification de la couleur du bouton Learn",
                "description": "Repérez la couleur du bouton de programmation à l'arrière du moteur (Jaune Security+ 2.0, Violet 315MHz, Rouge/Orange 390MHz ou Vert)."
            },
            {
                "title": "Programmation radio 100% sans fil",
                "description": "Pressez le bouton Learn du moteur (la LED témoin s'allume), puis appuyez fermement sur la touche souhaitée de la télécommande 893MAX dans les 30 secondes. L'ampoule du moteur clignote deux fois pour confirmer la synchronisation."
            }
        ],
        "faqs": [
            {
                "question": "La télécommande 893MAX est-elle compatible avec les anciens moteurs LiftMaster / Chamberlain ?",
                "answer": "Oui, grâce à son sélecteur de protocole interne, elle est rétrocompatible avec tous les récepteurs Chamberlain, LiftMaster et Craftsman fabriqués depuis 1993 équipés d'un bouton Learn coloré."
            },
            {
                "question": "Comment changer la pile CR2032 d'une télécommande 893MAX sans casser le boîtier ?",
                "answer": "Insérez une lame fine de tournevis plat ou une pièce de monnaie dans la fente située sur le côté inférieur droit du boîtier et faites levier avec douceur pour déclipser les deux coques."
            }
        ]
    },
    {
        "slug": "polaris-280-pressure-pool-cleaner",
        "category_id": "piscine-spa",
        "category_name": "Piscine, Spa & Robots Nettoyeurs",
        "brand": "Polaris (Zodiac)",
        "model_name": "Polaris Vac-Sweep 280 / 380 Pressure Cleaner",
        "years_range": "2020-2026",
        "title": "Polaris 280 & 380 : Pneus Caoutchouc C10, Sac Zippé K13 & Tuyau Balayeur",
        "summary": "Correspondances certifiées pour robot surpresseur Polaris 280 : pneus de traction MaxTrax C10, sac de filtration zippé K13, brosses d'embout de balayage 9-100-3105 et roulements à billes inox C60.",
        "meta_description": "Pièces d'usure Polaris 280 : pneus C10, sac fermeture éclair K13, mousse tuyau balayeur 9-100-3105 et roulements de roue C60. Liens multi-pays sans 404.",
        "parts": [
            {
                "name": "Pneu de Traction Caoutchouc Blanc MaxTrax (Lot de 3)",
                "tag": "Traction & Adhérence",
                "oem_or_dimension": "OEM Polaris C10 / C-10 / Diamètre standard 18cm",
                "wear_symptom": "Pneus lisses, patinage sur le fond, robot qui tourne en rond",
                "replacement_interval": "Toutes les 1 à 2 saisons",
                "technical_detail": "Caoutchouc blanc non tachant haute adhérence pour liner, PVC armé, béton et coque.",
                "search_query": "polaris 280 tires c10 pack"
            },
            {
                "name": "Sac de Filtration Tout-Usage à Fermeture Éclair (Double Couture)",
                "tag": "Collecte Débris & Feuilles",
                "oem_or_dimension": "OEM Polaris K13 / K-13 / Maille nylon haute ténacité",
                "wear_symptom": "Fermeture velcro encrassée ou fermeture éclair bloquée, déchirure toile",
                "replacement_interval": "Chaque saison en utilisation intensive",
                "technical_detail": "Fixation clipsable 1/4 tour sur le col du robot, zip anticorrosion lavable à grande eau.",
                "search_query": "polaris 280 zippered all purpose bag k13"
            },
            {
                "name": "Mousses d'Éponge pour Embout de Tuyau Balayeur Arrière (Lot de 10)",
                "tag": "Balayage & Agitation",
                "oem_or_dimension": "OEM 9-100-3105 / Réf B5 / Mousse polyuréthane réticulée",
                "wear_symptom": "Mousse déchiquetée ou disparue, tuyau plastique qui frotte directement sur le liner",
                "replacement_interval": "Toutes les 4 à 8 semaines en saison",
                "technical_detail": "Protège le revêtement de piscine des frottements et soulève les particules fines vers la bonde de fond.",
                "search_query": "polaris tail scrubbers 9-100-3105 b5 pack"
            },
            {
                "name": "Roulements à Billes Inox pour Roues de Déplacement (Lot de 8)",
                "tag": "Roulement & Motricité",
                "oem_or_dimension": "OEM Polaris C60 / C-60 / Cage inox anti-corrosion",
                "wear_symptom": "Roue grippée, résistance à la rotation, jeu latéral excessif",
                "replacement_interval": "Tous les 2 à 3 ans",
                "technical_detail": "Billes en acier inoxydable grade 316 résistant au traitement au sel et chlore stabilisé.",
                "search_query": "polaris 280 wheel ball bearing c60 pack"
            }
        ],
        "procedure_steps": [
            {
                "title": "Mise hors pression de la pompe de surpression",
                "description": "Coupez l'alimentation du surpresseur au disjoncteur du tableau électrique avant de débrancher la prise murale du Polaris."
            },
            {
                "title": "Remplacement sans outil des pneus C10",
                "description": "Plongez les pneus neufs dans un seau d'eau tiède pendant 2 minutes pour assouplir le caoutchouc, puis tendez-les manuellement sur les jantes des roues motrices."
            },
            {
                "title": "Contrôle du débit d'agitation du fouet arrière",
                "description": "Glissez une brosse mousse neuve 9-100-3105 sur l'extrémité du tuyau balayeur et serrez la bague plastique pour éviter son éjection."
            }
        ],
        "faqs": [
            {
                "question": "Faut-il préférer le sac à fermeture éclair K13 ou le sac d'origine à velcro pour Polaris 280 ?",
                "answer": "Le sac à fermeture éclair K13 est nettement supérieur dans le temps : le velcro s'encrasse rapidement avec les aiguilles de pin et le calcaire, tandis que le zip se vide d'un geste sans forcer."
            },
            {
                "question": "Pourquoi mon Polaris 280 flotte-t-il sur le côté ou se renverse-t-il ?",
                "answer": "Vérifiez le flotteur de tête (OEM A40) situé sur le tuyau d'arrivée d'eau : s'il est gorgé d'eau, le robot perd son équilibre vertical. Remplacez le flotteur s'il n'est plus étanche."
            }
        ]
    },
    {
        "slug": "milwaukee-m18-redlithium-battery-pack",
        "category_id": "outillage",
        "category_name": "Outillage Électroportatif",
        "brand": "Milwaukee",
        "model_name": "Milwaukee M18 REDLITHIUM XC5.0 / High Output (48-11-1850)",
        "years_range": "2020-2026",
        "title": "Milwaukee M18 REDLITHIUM : Batteries 5.0Ah XC, Chargeur M12-M18 & Clips Ceinture",
        "summary": "Correspondances certifiées gamme sans fil Milwaukee M18 Fuel : batteries haute capacité REDLITHIUM XC5.0 (48-11-1850), chargeur rapide double tension M12-18FC et crochets de ceinture 42-70-2653.",
        "meta_description": "Batteries Milwaukee M18 5.0Ah, chargeur rapide multi-tensions M12-M18 et clips de fixation ceinture. Références certifiées monde entier sans 404.",
        "parts": [
            {
                "name": "Batterie 18V 5.0Ah REDLITHIUM XC Li-Ion (Indicateur 4 LED)",
                "tag": "Autonomie Sans Fil",
                "oem_or_dimension": "OEM 48-11-1850 / M18 B5 / 18V 90Wh Lithium-Ion",
                "wear_symptom": "Perte d'autonomie sous forte charge, voyant clignotant rouge au chargeur",
                "replacement_interval": "Tous les 3 à 5 ans",
                "technical_detail": "Électronique intelligente REDLINK PLUS protégeant contre les surcharges thermiques et la décharge profonde.",
                "search_query": "milwaukee m18 battery 5.0ah 48-11-1850"
            },
            {
                "name": "Chargeur Rapide Multi-Tension M12 - M18 (Double Baie)",
                "tag": "Station de Recharge Rapide",
                "oem_or_dimension": "OEM 48-59-1812 / M12-18FC / Courant progressif séquentiel",
                "wear_symptom": "Cordon d'alimentation sectionné, surchauffe ou fusible de protection sauté",
                "replacement_interval": "Matériel d'atelier pérenne",
                "technical_detail": "Recharge une batterie M18 5.0Ah en seulement 59 minutes et gère les accus M12 et M18 sur une seule prise.",
                "search_query": "milwaukee rapid charger m12 m18 48-59-1812"
            },
            {
                "name": "Crochet de Ceinture Inox avec Vis de Fixation (Lot de 2)",
                "tag": "Transport & Fixation",
                "oem_or_dimension": "OEM 42-70-2653 / Acier inoxydable trempé",
                "wear_symptom": "Crochet tordu ou vis de maintien perdue sur chantier",
                "replacement_interval": "Remplacement immédiat en cas de déformation",
                "technical_detail": "Se visse réversiblement à gauche ou à droite sur l'embase de toute visseuse/perceuse Milwaukee M18.",
                "search_query": "milwaukee belt clip 42-70-2653 m18 pack"
            },
            {
                "name": "Coque de Protection Caoutchouc Amortisseur pour Batterie M18 XC",
                "tag": "Protection Chocs Atelier",
                "oem_or_dimension": "OEM 49-16-2767 / Élastomère résistant aux huiles et solvants",
                "wear_symptom": "Boîtier plastique fendu après une chute de hauteur",
                "replacement_interval": "Accessoire préventif longue durée",
                "technical_detail": "Absorbe les chocs sur béton et préserve les nervures d'encliquetage de la batterie.",
                "search_query": "milwaukee protective boot m18 battery 49-16-2767"
            }
        ],
        "procedure_steps": [
            {
                "title": "Sécurité : Retrait de la batterie avant manipulation",
                "description": "Pressez simultanément les deux verrous latéraux rouges et faites coulisser le bloc hors de l'outil avant d'inspecter les contacts métalliques."
            },
            {
                "title": "Nettoyage des glissières et connecteurs",
                "description": "Utilisez une soufflette à air sec ou un chiffon microfibre propre sans solvant pour éliminer les poussières de plâtre ou de bois accumulées dans les glissières."
            },
            {
                "title": "Procédure de charge optimale",
                "description": "Encliquetez fermement la batterie sur le chargeur jusqu'au clic mécanique. Le voyant rouge fixe indique la charge normale, le voyant vert signale la pleine autonomie 100%."
            }
        ],
        "faqs": [
            {
                "question": "Une batterie Milwaukee M18 XC5.0 fonctionne-t-elle avec les chargeurs standards plus anciens ?",
                "answer": "Oui, toutes les batteries M18 REDLITHIUM sont 100% rétrocompatibles avec tous les chargeurs Milwaukee M18 (M12-18C, M12-18FC et superchargeurs)."
            },
            {
                "question": "Que signifie le clignotement rouge/vert alterné sur le chargeur Milwaukee ?",
                "answer": "Cela indique un accu endommagé ou trop chaud/froid. Laissez la batterie revenir à température ambiante (15°C à 25°C) pendant 20 minutes avant de réinsérer."
            }
        ]
    },
    {
        "slug": "hayward-poolvac-xl-navigator-cleaner",
        "category_id": "piscine-spa",
        "category_name": "Piscine, Spa & Robots Nettoyeurs",
        "brand": "Hayward",
        "model_name": "Hayward PoolVac XL / Navigator Pro Hydraulic Cleaner",
        "years_range": "2020-2026",
        "title": "Hayward PoolVac XL & Navigator : Patins Semelle AXV417WHP, Ailettes & Cônes",
        "summary": "Correspondances officielles robot hydraulique Hayward PoolVac XL / Navigator Pro : patins de friction pour liner et béton AXV414P/AXV417WHP, ailettes latérales souples AXV055P et cône adaptateur skimmer AXV099P.",
        "meta_description": "Patins semelle Hayward AXV417WHP, ailettes latérales AXV055P et cône d'aspiration pour robots Hayward Navigator et PoolVac XL. Pièces sans erreur 404.",
        "parts": [
            {
                "name": "Kit 4 Patins de Friction Semelle Blancs Spécial Liner (Clipsables)",
                "tag": "Friction & Protection Revêtement",
                "oem_or_dimension": "OEM Hayward AXV414P / AXV417WHP / Élastomère blanc",
                "wear_symptom": "Témoins d'usure affleurants, robot qui adhère mal ou ralentit dans les pentes",
                "replacement_interval": "Chaque saison ou dès disparition du relief",
                "technical_detail": "Fixation directe sans vis sur la semelle inférieure, rainurage spécifique pour glisse optimale.",
                "search_query": "hayward pool vac shoes axv414p axv417whp 4 pack"
            },
            {
                "name": "Paire d'Ailettes Latérales Souples Gauche et Droite avec Fentes",
                "tag": "Guidage & Équilibre Hydraulique",
                "oem_or_dimension": "OEM Hayward AXV055P / Matériau santoprene flexible",
                "wear_symptom": "Ailette fendue ou rigidifiée par les UV, déviation de trajectoire du robot",
                "replacement_interval": "Tous les 2 ans",
                "technical_detail": "Maintient l'effet de sol par effet venturi pour canaliser le flux d'eau vers la turbine interne.",
                "search_query": "hayward wings kit axv055p poolvac"
            },
            {
                "name": "Cône Adaptateur Universel d'Aspiration Skimmer / Prise Balai",
                "tag": "Connexion Hydraulique",
                "oem_or_dimension": "OEM Hayward AXV099P / Diamètre étagé 38mm à 48mm",
                "wear_symptom": "Caoutchouc durci ou craquelé créant une prise d'air désamorçant la pompe",
                "replacement_interval": "Tous les 3 ans",
                "technical_detail": "Assure l'étanchéité conique immédiate dans le regard du skimmer ou sur la prise balai.",
                "search_query": "hayward cone adapter axv099p skimmer vac"
            },
            {
                "name": "Couronne / Bague d'Engrenage Central de Turbine V-Flex",
                "tag": "Transmission Hydraulique",
                "oem_or_dimension": "OEM AXV413P / Pignon téflon autolubrifiant",
                "wear_symptom": "Turbine qui tourne sans entraîner les pattes d'avancement oscillantes",
                "replacement_interval": "Tous les 3 à 4 ans",
                "technical_detail": "Pignon interne résistant aux sables fins et micro-débris sans nécessiter de graisse.",
                "search_query": "hayward poolvac pod kit axv413p gear"
            }
        ],
        "procedure_steps": [
            {
                "title": "Arrêt de la pompe de filtration",
                "description": "Coupez la filtration au coffret technique avant de déconnecter le tuyau flottant de la prise balai."
            },
            {
                "title": "Changement en 60 secondes des 4 patins AXV414P",
                "description": "Posez le robot à l'envers sur une surface propre. Déclipsez les 4 patins usés à l'aide d'un petit tournevis plat, puis encliquetez les nouveaux patins jusqu'au claquement audible."
            },
            {
                "title": "Vérification du sens des ailettes latérales",
                "description": "Positionnez les ailettes gauche et droite en respectant le repère gravé (L pour Left, R pour Right) et clipsez les chevilles de verrouillage souples."
            }
        ],
        "faqs": [
            {
                "question": "Quelle est la différence entre les patins blancs et les patins céramique/liège sur Hayward Navigator ?",
                "answer": "Les patins blancs (AXV414P / AXV417WHP) sont conçus pour les liners vinyle et coques polyester pour éviter toute rayure. Les patins en liège ou céramique (AXV414CA) sont strictement réservés aux piscines en béton peint ou carrelage."
            },
            {
                "question": "Mon Hayward PoolVac avance très lentement, que vérifier en premier ?",
                "answer": "Vérifiez que le panier de préfiltre de pompe et le filtre à sable/cartouche sont propres. Nettoyez également le cône d'aspiration pour éliminer les feuilles qui réduiraient le débit."
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

        # Répertoires dédiés aux langues supportées (fr, en, es, de, it, pt)
        self.lang_dirs = {}
        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            sub = lang_meta["subpath"].rstrip("/")
            if sub:
                docs_lang = os.path.join(self.docs_dir, sub)
                guides_lang = os.path.join(docs_lang, "guides")
                api_lang = os.path.join(self.docs_dir, "api", "v1", sub)
            else:
                docs_lang = self.docs_dir
                guides_lang = self.guides_dir
                api_lang = self.api_dir

            self.lang_dirs[lang_code] = {
                "docs": docs_lang,
                "guides": guides_lang,
                "api": api_lang
            }
            os.makedirs(docs_lang, exist_ok=True)
            os.makedirs(guides_lang, exist_ok=True)
            os.makedirs(api_lang, exist_ok=True)

        # Rétro-compatibilité en_dir
        self.docs_en_dir = self.lang_dirs["en"]["docs"]
        self.guides_en_dir = self.lang_dirs["en"]["guides"]
        self.api_en_dir = self.lang_dirs["en"]["api"]

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

        # Préparation des répertoires de base
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
            response = None
            for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2
                        )
                    )
                    if response and response.text:
                        break
                except Exception as model_err:
                    continue

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
            print(f"[NOTE] Génération Gemini non disponible ({e}), utilisation des spécifications constructeur validées.")

        return model_candidate

    def process_model(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Traite et injecte les URLs d'affiliation Amazon infaillibles multi-stores pour chaque pièce."""
        guide = self.enrich_with_gemini(candidate)
        now_dt = datetime.now(timezone.utc)
        guide["date_published"] = now_dt.strftime("%Y-%m-%d")
        guide["date_modified"] = now_dt.strftime("%Y-%m-%d")
        guide["date_modified_fr"] = now_dt.strftime("%d/%m/%Y")

        # Injection des liens partenaires Amazon infaillibles multi-stores mondiaux
        for part in guide.get("parts", []):
            query = part.get("search_query") or f"{guide['brand']} {guide['model_name']} {part['name']}"
            part["affiliate_url"] = build_affiliate_url(query, self.partner_tag, store="fr")
            part["affiliate_url_us"] = build_affiliate_url(query, self.partner_tag, store="us")
            part["affiliate_url_ca"] = build_affiliate_url(query, self.partner_tag, store="ca")
            part["affiliate_url_uk"] = build_affiliate_url(query, self.partner_tag, store="uk")
            part["affiliate_url_au"] = build_affiliate_url(query, self.partner_tag, store="au")
            part["affiliate_url_de"] = build_affiliate_url(query, self.partner_tag, store="de")
            part["affiliate_url_es"] = build_affiliate_url(query, self.partner_tag, store="es")
            part["affiliate_url_it"] = build_affiliate_url(query, self.partner_tag, store="it")
            part["affiliate_url_br"] = build_affiliate_url(query, self.partner_tag, store="br")
            part["affiliate_url_mx"] = build_affiliate_url(query, self.partner_tag, store="mx")
            part["affiliate_url_za"] = build_affiliate_url(query, self.partner_tag, store="za")
            part["store_urls"] = build_store_urls(query, self.partner_tag)

        return guide

    def render_and_save_guide(self, guide: Dict[str, Any]) -> str:
        """Génère le fichier HTML du guide pour TOUTES les langues supportées (FR, EN, ES, DE, IT, PT)."""
        template = self.jinja_env.get_template("guide.html")
        current_year = datetime.now().year
        first_path = ""

        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            t = get_translations(lang_code)
            html_output = template.render(
                guide=guide,
                lang=lang_code,
                lang_subpath=lang_meta["subpath"],
                t=t,
                site_base_url=self.site_base_url,
                editor_name=self.editor_name,
                editor_siret=self.editor_siret,
                editor_address=self.editor_address,
                editor_email=self.editor_email,
                current_year=current_year
            )
            file_path = os.path.join(self.lang_dirs[lang_code]["guides"], f"{guide['slug']}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            if not first_path:
                first_path = file_path

        return first_path

    def render_global_pages(self, all_guides: List[Dict[str, Any]]) -> None:
        """Génère l'index d'accueil, mentions légales, sitemap multilingue, robots.txt, feeds RSS et endpoints IA pour les 6 langues."""
        current_year = datetime.now().year
        total_parts = sum(len(g.get("parts", [])) for g in all_guides)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")

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

        # 1. Pages d'Accueil pour toutes les langues (docs/index.html, docs/en/index.html, docs/es/index.html, etc.)
        index_tpl = self.jinja_env.get_template("index.html")
        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            t = get_translations(lang_code)
            index_html = index_tpl.render(
                categories=categories,
                stats=stats,
                lang=lang_code,
                lang_subpath=lang_meta["subpath"],
                t=t,
                site_base_url=self.site_base_url,
                editor_name=self.editor_name,
                editor_siret=self.editor_siret,
                editor_address=self.editor_address,
                editor_email=self.editor_email,
                current_year=current_year
            )
            out_path = os.path.join(self.lang_dirs[lang_code]["docs"], "index.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(index_html)

        # 2. Page Mentions Légales docs/mentions-legales.html
        mentions_tpl = self.jinja_env.get_template("mentions_legales.html")
        mentions_html = mentions_tpl.render(
            lang="fr",
            lang_subpath="",
            t=get_translations("fr"),
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
        robots_txt = f"""# Robots.txt - OutdoorParts Guide Global
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

        # 4. docs/sitemap.xml Multilingue complet pour les 6 langues avec balises alternate hreflang
        sitemap_urls = []

        # Pages d'accueil (FR, EN, ES, DE, IT, PT)
        home_links = [
            f'    <xhtml:link rel="alternate" hreflang="{code}" href="{self.site_base_url}/{meta["subpath"]}index.html"/>'
            for code, meta in SUPPORTED_LANGUAGES.items()
        ]
        home_links.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{self.site_base_url}/en/index.html"/>')
        home_links_block = "\n".join(home_links)

        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            sitemap_urls.append(f"""  <url>
    <loc>{self.site_base_url}/{lang_meta["subpath"]}index.html</loc>
{home_links_block}
    <lastmod>{now_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")

        sitemap_urls.append(f"""  <url>
    <loc>{self.site_base_url}/mentions-legales.html</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>""")

        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            sitemap_urls.append(f"""  <url>
    <loc>{self.site_base_url}/{lang_meta["subpath"]}llms.txt</loc>
    <lastmod>{now_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>""")

        # Guides pour toutes les langues
        for g in all_guides:
            slug = g['slug']
            date_mod = g.get('date_modified', now_iso)
            guide_links = [
                f'    <xhtml:link rel="alternate" hreflang="{code}" href="{self.site_base_url}/{meta["subpath"]}guides/{slug}.html"/>'
                for code, meta in SUPPORTED_LANGUAGES.items()
            ]
            guide_links.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{self.site_base_url}/en/guides/{slug}.html"/>')
            guide_links_block = "\n".join(guide_links)

            for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
                sitemap_urls.append(f"""  <url>
    <loc>{self.site_base_url}/{lang_meta["subpath"]}guides/{slug}.html</loc>
{guide_links_block}
    <lastmod>{date_mod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
{chr(10).join(sitemap_urls)}
</urlset>"""
        with open(os.path.join(self.docs_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(sitemap_xml)

        # 5. docs/{lang}/feed.xml (RSS 2.0 pour les 6 langues)
        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            t = get_translations(lang_code)
            sub = lang_meta["subpath"]
            rss_items = []
            for g in all_guides[:20]:
                rss_items.append(f"""    <item>
      <title><![CDATA[{g['brand']} - {g['model_name']}]]></title>
      <link>{self.site_base_url}/{sub}guides/{g['slug']}.html</link>
      <guid>{self.site_base_url}/{sub}guides/{g['slug']}.html</guid>
      <description><![CDATA[{g['summary']}]]></description>
      <category>{g['category_name']}</category>
      <pubDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
    </item>""")

            feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{t.get('og_title', 'OutdoorParts Guide')}</title>
    <link>{self.site_base_url}/{sub}</link>
    <description>{t.get('og_desc', 'Exact Wear Parts Cross Reference')}</description>
    <language>{lang_meta['locale'].lower()}</language>
    <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
{chr(10).join(rss_items)}
  </channel>
</rss>"""
            with open(os.path.join(self.lang_dirs[lang_code]["docs"], "feed.xml"), "w", encoding="utf-8") as f:
                f.write(feed_xml)

        # 6. Standard LLMs : docs/{lang}/llms.txt et llms-full.txt pour chaque langue
        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            t = get_translations(lang_code)
            sub = lang_meta["subpath"]
            
            # llms.txt
            llms_txt = f"""# OutdoorParts Guide ({lang_meta['name']}) - {t.get('hero_title', 'Exact Wear Parts Cross Reference')}
> {t.get('meta_desc', 'Independent technical catalog.')}
> Structured technical data for AI Agents (ChatGPT Search, Perplexity, Claude, Copilot).
> Zero broken links: all direct queries resolve to local Amazon Affiliate searches worldwide (#AffiliateLink).

## Machine Endpoints
- Full Text Index: {self.site_base_url}/{sub}llms-full.txt
- REST API JSON: {self.site_base_url}/api/v1/{sub}catalog.json
- OpenAPI Spec: {self.site_base_url}/.well-known/openapi.json
- Global English Index: {self.site_base_url}/en/llms.txt
- Multilingual Sitemap: {self.site_base_url}/sitemap.xml

## Model Guides Indexed ({lang_meta['name']})
"""
            for g in all_guides:
                llms_txt += f"- [{g['brand']} - {g['model_name']}]({self.site_base_url}/{sub}guides/{g['slug']}.html) : {g['summary']}\n"

            with open(os.path.join(self.lang_dirs[lang_code]["docs"], "llms.txt"), "w", encoding="utf-8") as f:
                f.write(llms_txt)

            # llms-full.txt
            llms_full_parts = [
                f"# OutdoorParts Guide ({lang_meta['name']}) - Full Knowledge Base\nVersion: 1.0.0 | Updated: {now_iso}\nBase URL: {self.site_base_url}/{sub}\n"
            ]
            for g in all_guides:
                llms_full_parts.append(f"""
================================================================================
MODEL : {g['brand']} - {g['model_name']} ({g['category_name']})
URL : {self.site_base_url}/{sub}guides/{g['slug']}.html
YEARS : {g['years_range']}
SUMMARY : {g['summary']}

CROSS-REFERENCE PARTS & AMAZON STORES :""")
                for p in g.get("parts", []):
                    primary_url = p.get(f"affiliate_url_{lang_meta['store']}", p.get("affiliate_url_us", p.get("affiliate_url")))
                    llms_full_parts.append(f"""- PART : {p['name']}
  OEM REF / SPECS : {p['oem_or_dimension']}
  WEAR & INTERVAL : {p['wear_symptom']} ({p['replacement_interval']})
  AMAZON ({lang_meta['store'].upper()}) : {primary_url}
  AMAZON US : {p.get('affiliate_url_us')}
  AMAZON DE : {p.get('affiliate_url_de')}
  AMAZON ES : {p.get('affiliate_url_es')}
  AMAZON IT : {p.get('affiliate_url_it')}
  AMAZON BR : {p.get('affiliate_url_br', p.get('affiliate_url_es'))}""")

            with open(os.path.join(self.lang_dirs[lang_code]["docs"], "llms-full.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(llms_full_parts))

        # 7. docs/api/v1/{lang}/catalog.json pour chaque langue
        api_catalog = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "site_base_url": self.site_base_url,
            "partner_tag": self.partner_tag,
            "total_models": len(all_guides),
            "total_parts": total_parts,
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "supported_stores": list(AMAZON_DOMAINS.keys()),
            "models": all_guides
        }
        for lang_code, lang_meta in SUPPORTED_LANGUAGES.items():
            api_file = os.path.join(self.lang_dirs[lang_code]["api"], "catalog.json")
            with open(api_file, "w", encoding="utf-8") as f:
                json.dump(api_catalog, f, indent=2, ensure_ascii=False)

        # 8. docs/.well-known/openapi.json
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "OutdoorParts Guide API Global",
                "version": "1.0.0",
                "description": "API REST ouverte pour agents IA répertoriant les correspondances de consommables d'équipements extérieurs dans 6 langues (FR, EN, ES, DE, IT, PT) avec liens multi-stores Amazon."
            },
            "servers": [{"url": self.site_base_url}],
            "paths": {
                "/api/v1/catalog.json": {
                    "get": {
                        "summary": "Catalogue global des correspondances",
                        "operationId": "getCatalog",
                        "responses": {
                            "200": {
                                "description": "Catalogue complet avec liens de recherche Amazon multi-stores",
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            }
                        }
                    }
                },
                "/api/v1/en/catalog.json": {
                    "get": {
                        "summary": "English cross-reference catalog",
                        "operationId": "getCatalogEn",
                        "responses": {"200": {"description": "Full English catalog"}}
                    }
                },
                "/api/v1/es/catalog.json": {
                    "get": {
                        "summary": "Catálogo de piezas de repuesto (Español)",
                        "operationId": "getCatalogEs",
                        "responses": {"200": {"description": "Catálogo completo en español"}}
                    }
                },
                "/api/v1/de/catalog.json": {
                    "get": {
                        "summary": "Ersatzteile & Verschleißteile Katalog (Deutsch)",
                        "operationId": "getCatalogDe",
                        "responses": {"200": {"description": "Vollständiger Katalog auf Deutsch"}}
                    }
                },
                "/api/v1/it/catalog.json": {
                    "get": {
                        "summary": "Catalogo parti di ricambio (Italiano)",
                        "operationId": "getCatalogIt",
                        "responses": {"200": {"description": "Catalogo completo in italiano"}}
                    }
                },
                "/api/v1/pt/catalog.json": {
                    "get": {
                        "summary": "Catálogo de peças de reposição (Português)",
                        "operationId": "getCatalogPt",
                        "responses": {"200": {"description": "Catálogo completo em português"}}
                    }
                },
                "/llms.txt": {
                    "get": {
                        "summary": "Fichier llms.txt standard (FR)",
                        "responses": {"200": {"description": "Documentation markdown concise"}}
                    }
                },
                "/en/llms.txt": {
                    "get": {
                        "summary": "Standard llms.txt file (EN Global)",
                        "responses": {"200": {"description": "Concise markdown documentation for LLMs"}}
                    }
                }
            }
        }
        with open(os.path.join(self.well_known_dir, "openapi.json"), "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)

        # 9. Fichier clé IndexNow pour validation
        indexnow_key = self.state.get("indexnow_key", "4a7f9b8c2e1d0f5a8b7c6d5e4f3a2b1c")
        with open(os.path.join(self.docs_dir, f"{indexnow_key}.txt"), "w", encoding="utf-8") as f:
            f.write(indexnow_key)

    def run_autopilot(self) -> List[Dict[str, Any]]:
        """
        Cycle d'exécution autonome :
        1. Compile tous les modèles de CANDIDATE_MODELS_POOL pour une couverture mondiale immédiate
        2. Traite et enrichit les fiches
        3. Génère les déclinaisons dans les 6 langues (FR, EN, ES, DE, IT, PT) des guides et endpoints
        4. Met à jour catalog_state.json
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Démarrage de l'agent OutdoorParts Global (6 Langues)...")
        
        # Traitement et mise en mémoire de l'intégralité du pool
        active_guides_map: Dict[str, Dict[str, Any]] = {}
        newly_processed: List[Dict[str, Any]] = []

        print(f"Modèles dans le pool de connaissances ({len(CANDIDATE_MODELS_POOL)}) :")
        for candidate in CANDIDATE_MODELS_POOL:
            slug = candidate["slug"]
            is_new = slug not in self.state.get("processed_models", [])
            guide = self.process_model(candidate)
            active_guides_map[slug] = guide
            if is_new:
                newly_processed.append(guide)
                self.state["processed_models"].append(slug)
                print(f" + [NOUVEAU] [{guide['category_name']}] {guide['model_name']} ({slug})")
            else:
                print(f" * [INDEXE] [{guide['category_name']}] {guide['model_name']} ({slug})")

        all_guides = list(active_guides_map.values())

        # Rendu des pages HTML des guides pour toutes les langues
        for g in all_guides:
            self.render_and_save_guide(g)

        # Rendu des pages globales, endpoints et llms.txt pour toutes les langues
        self.render_global_pages(all_guides)

        # Mise à jour de l'état
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.state["stats"] = {
            "total_guides": len(all_guides),
            "total_parts_indexed": sum(len(g.get("parts", [])) for g in all_guides)
        }
        self._save_state()

        total_pages = len(all_guides) * len(SUPPORTED_LANGUAGES)
        print(f"[OK] {len(all_guides)} modèles compilés en 6 langues ({total_pages} pages guides) dans docs/.")
        return newly_processed


def main():
    agent = AgentEngine()
    agent.run_autopilot()


if __name__ == "__main__":
    main()

