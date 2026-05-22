#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cheebo_finetuning_dataset.py
============================
Génère 2000 exemples pour fine-tuner LLaMA 3 8B sur Cheebo (assistant vétérinaire).

Usage Google Colab :
    !python cheebo_finetuning_dataset.py
    # variables train_dataset / test_dataset disponibles ensuite
"""

import json, random
from pathlib import Path

random.seed(42)

INSTRUCTION_FR = (
    "Tu es Cheebo, un assistant vétérinaire IA. Analyse les symptômes décrits "
    "et fournis une réponse structurée avec le niveau d'urgence, les causes possibles, "
    "les soins immédiats recommandés et les signes d'alarme. "
    "Rappelle toujours de consulter un vétérinaire."
)

INSTRUCTION_EN = (
    "You are Cheebo, a veterinary AI assistant. Analyze the described symptoms "
    "and provide a structured response with the urgency level, possible causes, "
    "recommended immediate care, and warning signs. "
    "Always remind the user to consult a veterinarian."
)

DISCLAIMER_FR = "_Ces conseils ne remplacent pas l'avis d'un vétérinaire._"
DISCLAIMER_EN = "_These recommendations do not replace professional veterinary advice._"

# kept for backward compatibility
INSTRUCTION = INSTRUCTION_FR
DISCLAIMER   = DISCLAIMER_FR

# ─── Scénarios ────────────────────────────────────────────────────────────────
# Chaque scénario : level, animal, condition, symptoms×5, conditions×5, cares×5, flags×5

SCENARIOS = [
    # ══════════════════════════════════════════════════════════════════════════
    #  CRITIQUE 🚨 (10 scénarios)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Torsion gastrique (GDV)",
        "symptoms": [
            "ventre ballonné, tentatives vaines de vomir",
            "abdomen distendu et douloureux, salivation excessive",
            "ventre gonflé, agitation extrême, incapacité à vomir",
            "ballonnement abdominal sévère, gémissements, détresse",
            "estomac gonflé, échec de vomissement, prostration",
        ],
        "conditions": [
            "Torsion/dilatation gastrique (GDV), urgence chirurgicale absolue",
            "Syndrome de dilatation-torsion gastrique, pronostic vital engagé",
            "GDV — torsion de l'estomac, nécessite chirurgie d'urgence",
            "Dilatation-volvulus gastrique, risque de choc en quelques heures",
            "Torsion gastrique aiguë, urgence vitale immédiate",
        ],
        "cares": [
            "Ne rien donner par la bouche. Transport immédiat aux urgences vétérinaires.",
            "Aucune nourriture ni eau. Partir en urgence chez le vétérinaire maintenant.",
            "Zéro alimentation. Aller aux urgences vétérinaires dans les 30 minutes.",
            "Interdire tout aliment/liquide. Consultation vétérinaire d'urgence immédiate.",
            "Rien par voie orale. Transport urgent — chaque minute compte.",
        ],
        "flags": [
            "Gencives blanches ou bleues, effondrement, mort en quelques heures sans chirurgie",
            "Muqueuses pâles, collapsus, décès possible si non opéré rapidement",
            "Lèvres/gencives décolorées, état de choc, survie < 6h sans intervention",
            "Choc cardiogénique, perte de connaissance, pronostic fatal sans chirurgie urgente",
            "Cyanose des muqueuses, choc septique imminent, urgence absolue",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chat mâle", "condition": "Obstruction urinaire féline",
        "symptoms": [
            "crie en essayant d'uriner, abdomen tendu",
            "ne peut pas uriner depuis 24h, cri de douleur",
            "allers-retours à la litière sans uriner, vocalises",
            "bloqué urinaire, abdomen ballonné, léthargique",
            "tentatives répétées d'urination sans résultat, douleur abdominale",
        ],
        "conditions": [
            "Obstruction urinaire complète, risque de rupture vésicale et d'insuffisance rénale aiguë",
            "Blocage urétral chez le chat mâle — urgence vétérinaire absolue",
            "Uroblock complet, toxémie urémique en développement",
            "Occlusion urétrale, rein en surpression, pronostic vital < 48h",
            "Obstruction urétrale totale, rétention urinaire sévère",
        ],
        "cares": [
            "Ne jamais tenter de presser la vessie. Urgences vétérinaires immédiatement.",
            "Transport d'urgence chez le vétérinaire. Aucune pression sur l'abdomen.",
            "Aller aux urgences vétérinaires maintenant — délai fatal < 24h supplémentaires.",
            "Consultation vétérinaire d'urgence sans délai. Ne pas masser l'abdomen.",
            "Urgence absolue : clinique vétérinaire immédiatement, nuit et jour.",
        ],
        "flags": [
            "Vomissements, collapsus, mort par urémie si non débloqué dans les 24-48h",
            "Prostration totale, hypothermie, insuffisance rénale irréversible",
            "Choc urémique, bradycardie, arrêt cardiaque possible",
            "Convulsions, coma urémique, pronostic fatal sans sondage immédiat",
            "Décompensation cardiaque, décès en quelques heures sans intervention",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Intoxication au chocolat",
        "symptoms": [
            "a mangé du chocolat noir, vomit et tremble",
            "ingestion de chocolat il y a 1h, agitation et tachycardie",
            "a volé du chocolat, convulsions légères et hyperactivité",
            "chocolat ingéré, diarrhée et muscles qui tremblent",
            "a mangé du cacao en poudre, vomissements et hyperthermie",
        ],
        "conditions": [
            "Intoxication à la théobromine, risque de convulsions et d'arythmie cardiaque",
            "Toxicose au chocolat — théobromine et caféine cardiotoxiques",
            "Empoisonnement au chocolat, seuil toxique potentiellement atteint",
            "Intoxication chocolat sévère, système nerveux central et cardiaque affectés",
            "Toxicité théobromine aiguë, risque vital selon quantité ingérée",
        ],
        "cares": [
            "Appeler le vétérinaire immédiatement avec type/quantité de chocolat mangé.",
            "Urgences vétérinaires maintenant. Apporter l'emballage du chocolat.",
            "Induction de vomissement UNIQUEMENT si conseillée par le vétérinaire.",
            "Contacter la clinique vétérinaire d'urgence avec le poids du chien et la quantité ingérée.",
            "Aller aux urgences. Ne pas attendre l'apparition de symptômes graves.",
        ],
        "flags": [
            "Convulsions, arythmie cardiaque, hyperthermie > 40°C, mort possible",
            "Tachycardie sévère, état de mal épileptique, insuffisance cardiaque",
            "Collapsus, coma, arrêt cardiorespiratoire si dose létale ingérée",
            "Tremblements incontrôlables, perte de conscience, pronostic sombre sans traitement",
            "Fibrillation ventriculaire, hyperthermie maligne, décès en quelques heures",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Détresse respiratoire sévère",
        "symptoms": [
            "respiration très difficile, lèvres bleues, incapable de rester debout",
            "halète avec effort intense, gencives violacées, épuisement total",
            "respiration abdominale forcée, cyanose, tête baissée",
            "suffocation visible, langue bleue, effort respiratoire maximal",
            "dyspnée sévère, posture en chien de fusil, asphyxie progressive",
        ],
        "conditions": [
            "Détresse respiratoire aiguë sévère — pneumothorax, épanchement ou obstruction",
            "Insuffisance respiratoire critique, hypoxie cérébrale en cours",
            "Dyspnée d'urgence — œdème pulmonaire ou obstruction des voies aériennes",
            "Détresse respiratoire extrême, saturation en O2 effondrée",
            "Crise asphyxique, causes multiples (épanchement, pneumonie sévère, corps étranger)",
        ],
        "cares": [
            "Maintenir le chien calme. Urgences vétérinaires immédiatement — oxygénothérapie nécessaire.",
            "Ne pas stresser l'animal. Transport immédiat aux urgences — chaque seconde compte.",
            "Garder le chien en position semi-assise. Clinique d'urgence maintenant.",
            "Éviter tout effort. Urgences vétérinaires — risque de mort par asphyxie.",
            "Minimum de manipulation. Transport en urgence — oxygène vital sous 15 minutes.",
        ],
        "flags": [
            "Cyanose totale, arrêt respiratoire, mort cérébrale en 4-6 minutes",
            "Perte de connaissance, arrêt cardio-respiratoire imminent",
            "Collapsus, agonisation, pronostic fatal sans oxygénothérapie d'urgence",
            "Convulsions hypoxiques, choc cardiovasculaire, mort en quelques minutes",
            "Arrêt respiratoire, dommages cérébraux irréversibles, décès imminent",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Coup de chaleur",
        "symptoms": [
            "laissé en voiture au soleil, halètement excessif, ne répond plus",
            "exposition à la chaleur intense, T° > 41°C, prostration totale",
            "exercice par 35°C, effondrement soudain, gencives rouge vif",
            "hyperthermie post-exercice, vomissements, démarche vacillante",
            "chaleur extrême, confusion, salive épaisse, muqueuses sèches",
        ],
        "conditions": [
            "Coup de chaleur (hyperthermie maligne) — dommages organiques multiples en cours",
            "Hyperthermie sévère > 41°C, risque de CIVD et défaillance multi-organes",
            "Insolation grave, coagulation intravasculaire disséminée possible",
            "Coup de chaleur d'exercice, rhabdomyolyse et insuffisance rénale",
            "Choc thermique aigu, cerveau, reins et foie menacés simultanément",
        ],
        "cares": [
            "Refroidir avec eau tiède (pas froide) sur cou/aisselles. Urgences vétérinaires immédiatement.",
            "Humidifier le pelage avec eau tempérée. Transport urgent en voiture climatisée.",
            "Poser des compresses d'eau fraîche sur les pattes. Clinique d'urgence sans délai.",
            "Refroidissement progressif (eau 20-22°C). Ventilateur. Urgences dans les 20 minutes.",
            "Ne pas immerger dans l'eau froide. Refroidir doucement. Vétérinaire en urgence.",
        ],
        "flags": [
            "Convulsions, saignements, CIVD, mort en quelques heures sans réanimation",
            "Coma, insuffisance rénale aiguë, choc hémorragique, pronostic sombre",
            "Défaillance multi-organes, dommages cérébraux irréversibles, décès",
            "Arrêt cardiaque, coagulation intravasculaire, mort probable > 41,5°C",
            "Anurie, convulsions, collapsus vasculaire, pronostic fatal sans soins intensifs",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "lapin", "condition": "Stase digestive avancée",
        "symptoms": [
            "n'a pas mangé depuis 48h, aucun crottin depuis hier soir",
            "abdomen très gonflé, ne bouge plus, refus total de nourriture",
            "stase totale, douleur abdominale, grince des dents (bruxisme)",
            "transit intestinal arrêté, lapin prostré et en hypothermie",
            "plus de crottins depuis 36h, posture voûtée, grincements dentaires",
        ],
        "conditions": [
            "Stase digestive totale — iléus paralytique, risque de mort en < 24h",
            "Occlusion intestinale chez le lapin, gaz accumulés, nécrose possible",
            "Stase GI avancée, intoxication par gaz de fermentation intestinale",
            "Iléus sévère, muqueuses digestives en souffrance, pronostic réservé",
            "Arrêt digestif complet, risque de choc endotoxémique imminent",
        ],
        "cares": [
            "Urgences vétérinaires immédiatement — le lapin peut mourir en quelques heures.",
            "Ne rien forcer oralement. Transport en urgence chez le vétérinaire.",
            "Clinique d'urgence maintenant. Réchauffer doucement pendant le transport.",
            "Aucune automédication. Vétérinaire urgentiste dans l'heure qui suit.",
            "Garder le lapin au chaud. Urgences vétérinaires sans délai.",
        ],
        "flags": [
            "Mort par endotoxémie en < 24h, aucune marge pour attendre",
            "Nécrose intestinale, choc septique, décès inévitable sans traitement",
            "Hypothermie terminale, collapsus cardiovasculaire, pronostic fatal",
            "Douleur abdominale insupportable, convulsions, mort certaine sans soins",
            "Perforation intestinale, péritonite, décès imminent",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Convulsions prolongées (état de mal épileptique)",
        "symptoms": [
            "crise de convulsions depuis plus de 5 minutes sans s'arrêter",
            "épilepsie en cluster — 3 crises répétées en 2 heures",
            "convulsions continues, perd conscience entre les crises",
            "état de mal épileptique, corps rigide, mouvements involontaires",
            "crises répétées sans récupération complète entre elles, bave abondante",
        ],
        "conditions": [
            "État de mal épileptique — dommages cérébraux permanents si > 30 minutes",
            "Épilepsie en cluster ou status epilepticus, urgence neurologique absolue",
            "Convulsions prolongées — hyperthermie cérébrale et nécrose neuronale",
            "Crises continues non contrôlées, risque de coma post-ictal prolongé",
            "Status epilepticus, décompensation cérébrale progressive",
        ],
        "cares": [
            "Ne pas mettre les doigts dans la bouche. Écarter les obstacles. Urgences vétérinaires.",
            "Protéger la tête avec un coussin. Obscurcir la pièce. Transport d'urgence immédiat.",
            "Chronométrer la crise. Si > 5 min : urgences vétérinaires maintenant.",
            "Calme total autour du chien. Aucun liquide oral. Clinique d'urgence.",
            "Ne pas retenir le chien. Noter l'heure de début. Vétérinaire en urgence.",
        ],
        "flags": [
            "Hyperthermie > 41°C, coma, lésions cérébrales irréversibles, mort",
            "Arrêt respiratoire intercritique, œdème cérébral, décès probable",
            "Status > 30 min → nécrose neuronale, coma irréversible",
            "Détresse respiratoire post-ictale, aspiration de vomissements, pneumonie",
            "Choc thermorégulateur, acidose métabolique, défaillance multi-organes",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chienne", "condition": "Pyomètre ouvert/fermé",
        "symptoms": [
            "écoulement purulent vulvaire depuis 3 jours, abattement et polydipsie",
            "pertes malodorantes de la vulve, ne mange plus, boit énormément",
            "pyomètre suspecté — ventre gonflé, fièvre, léthargie extrême",
            "écoulements jaune-verdâtres, vomissements, déshydratation visible",
            "abdomen tendu et douloureux, dépression sévère, suintements vaginaux",
        ],
        "conditions": [
            "Pyomètre (ouvert ou fermé) — sepsis utérin, urgence chirurgicale absolue",
            "Infection utérine grave, risque de rupture et de péritonite fatale",
            "Pyomètre avec endotoxémie, reins en insuffisance aiguë",
            "Suppuration utérine, choc septique en développement rapide",
            "Pyomètre fermé — distension utérine, risque de rupture imminent",
        ],
        "cares": [
            "Urgences vétérinaires immédiatement — chirurgie (ovario-hystérectomie) nécessaire.",
            "Transport d'urgence. Aucun antipyrétique sans avis vétérinaire.",
            "Clinique vétérinaire d'urgence. Ne pas tenter de drainer soi-même.",
            "Vétérinaire dans l'heure — le pyomètre fermé peut se rompre à tout moment.",
            "Consultation urgente. Stabilisation IV puis chirurgie rapide indispensable.",
        ],
        "flags": [
            "Rupture utérine, péritonite, choc septique, mort en quelques heures",
            "Insuffisance rénale aiguë, CIVD, pronostic fatal sans chirurgie d'urgence",
            "Septicémie généralisée, défaillance multi-organes, décès imminent",
            "Choc endotoxémique irréversible, mortalité > 80% sans intervention rapide",
            "Anurie, hypothermie, collapsus vasculaire, décès probable",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Polytraumatisme / Accident de la route",
        "symptoms": [
            "renversé par une voiture, ne peut plus marcher, saigne abondamment",
            "accident de voiture, fractures multiples suspectées, état de choc",
            "traumatisme crânien après chute grave, inconscient ou semi-conscient",
            "écrasé par un véhicule, douleur extrême, hémorragie interne possible",
            "polytraumatisé, respiration irrégulière, hémorragie externe visible",
        ],
        "conditions": [
            "Polytraumatisme — hémorragie interne, fractures, traumatisme crânien",
            "Choc traumatique, hémorragie interne et/ou externe, urgence vitale absolue",
            "Trauma thoracique, pneumothorax et hémothorax possibles",
            "Fractures multiples, atteinte médullaire possible, choc hypovolémique",
            "Traumatisme grave multisystémique, pronostic immédiat très réservé",
        ],
        "cares": [
            "Improviser une civière (planche). Ne pas plier le rachis. Urgences vétérinaires.",
            "Comprimer les plaies hémorragiques avec un linge propre. Transport d'urgence immédiat.",
            "Minimiser les mouvements de la colonne. Clinique d'urgence dans les 15 minutes.",
            "Réchauffer avec une couverture. Urgences vétérinaires — soins intensifs nécessaires.",
            "Ne pas retirer d'objets plantés dans les plaies. Urgence vétérinaire immédiate.",
        ],
        "flags": [
            "Choc hémorragique, arrêt cardiorespiratoire, mort en quelques minutes",
            "Hémorragie interne massive, choc irréversible, décès imminent",
            "Traumatisme médullaire, paralysie permanente, instabilité hémodynamique",
            "Tamponnade cardiaque, pneumothorax sous tension, mort par asphyxie",
            "Collapsus vasculaire, CIVD post-traumatique, pronostic fatal",
        ],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chat", "condition": "Intoxication antigel / paracétamol",
        "symptoms": [
            "a léché de l'antigel (éthylène glycol), vomit et titube",
            "exposition au paracétamol (1 comprimé humain), détresse respiratoire",
            "ingestion d'antigel, gencives brunes, lèvres cyanosées",
            "paracétamol accidentel, œdème facial et méthémoglobinémie visible",
            "ingestion produit ménager toxique, prostration et muqueuses sombres",
        ],
        "conditions": [
            "Intoxication à l'éthylène glycol — insuffisance rénale aiguë en < 12h",
            "Toxicose au paracétamol chez le chat — méthémoglobinémie mortelle",
            "Empoisonnement antigel, cristaux d'oxalate se formant dans les reins",
            "Intoxication paracétamol, atteinte hépatique et hypoxie tissulaire sévère",
            "Toxicité aiguë sévère, reins et/ou foie en défaillance rapide",
        ],
        "cares": [
            "Urgences vétérinaires MAINTENANT. Le chat n'a que quelques heures.",
            "Transport immédiat — antidote (N-acétylcystéine) disponible uniquement en clinique.",
            "Ne pas induire de vomissement sans avis vétérinaire. Urgences dans les 30 minutes.",
            "Clinique vétérinaire d'urgence — chaque heure perdue réduit les chances de survie.",
            "Appeler le vétérinaire en route. Apporter l'emballage du produit ingéré.",
        ],
        "flags": [
            "Insuffisance rénale irréversible en < 12h, mort certaine sans traitement immédiat",
            "Méthémoglobinémie, coma, arrêt respiratoire, décès en quelques heures",
            "Anurie, oligurie, coma urémique, pronostic fatal",
            "Nécrose tubulaire rénale, convulsions, mort en 24-72h sans antidote",
            "Détresse respiratoire extrême, hypoxie cérébrale, décès imminent",
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    #  ÉLEVÉ ⚠️ (7 scénarios)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chien", "condition": "Vomissement avec sang (hématémèse)",
        "symptoms": [
            "vomit du sang rouge vif depuis ce matin",
            "vomissements avec traces de sang brun ('marc de café')",
            "vomi 4 fois en 2h avec du sang, très abattu",
            "vomissement hémorragique, abdomen sensible à la palpation",
            "hématémèse répétée, déshydratation visible, gencives pâles",
        ],
        "conditions": [
            "Hématémèse — ulcère gastrique, gastro-entérite hémorragique, corps étranger",
            "Vomissement sanglant — atteinte de la muqueuse gastrique, coagulopathie possible",
            "Gastrite hémorragique ou ulcère perforant, urgence digestive",
            "Saignement gastro-intestinal actif — bilan vétérinaire rapide nécessaire",
            "Hématémèse avec suspicion d'intoxication ou de trouble de coagulation",
        ],
        "cares": [
            "Jeûne hydrique strict. Consultation vétérinaire dans les 2 heures.",
            "Ne rien donner par la bouche. Vétérinaire aujourd'hui impérativement.",
            "Garder un échantillon du vomi. Consultation d'urgence recommandée.",
            "Aucun médicament humain. Clinique vétérinaire dans les 3 heures.",
            "Repos complet, aucune alimentation. Vétérinaire dans la journée.",
        ],
        "flags": [
            "Vomissements incessants, choc hémorragique, gencives blanches",
            "Anémie aiguë, état de choc, collapsus cardiovasculaire",
            "Sang en grande quantité, perte de conscience, urgence vitale",
            "Perforation gastrique, péritonite, douleur abdominale aiguë",
            "Pâleur extrême, détresse, choc hypovolémique imminent",
        ],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "lapin", "condition": "Anorexie > 12h",
        "symptoms": [
            "n'a pas mangé depuis hier soir, crottins rares et petits",
            "refuse tout aliment depuis 14h, moins de crottins que d'habitude",
            "anorexie complète depuis 12h, lapin moins actif qu'à l'ordinaire",
            "plus d'appétit depuis ce matin, ventre légèrement ballonné",
            "n'a pas touché son foin depuis 15h, posture légèrement voûtée",
        ],
        "conditions": [
            "Début de stase digestive — peut devenir critique en quelques heures",
            "Anorexie chez le lapin — iléus débutant, intervention vétérinaire rapide nécessaire",
            "Stase GI précoce, transit en ralentissement, douleur abdominale probable",
            "Hypomotilité intestinale, accumulation de gaz, risque de stase totale",
            "Arrêt alimentaire dangereux chez le lapin — vétérinaire dans la journée",
        ],
        "cares": [
            "Proposer du foin frais et de l'eau fraîche. Vétérinaire si pas d'amélioration en 2h.",
            "Massage abdominal doux. Consulter le vétérinaire dans les 4 heures.",
            "Stimuler le transit avec du persil frais. Clinique vétérinaire ce jour.",
            "Garder au chaud. Vétérinaire si anorexie persiste au-delà de 12 heures.",
            "Surveiller les crottins. Consultation vétérinaire d'urgence si aggravation.",
        ],
        "flags": [
            "Aucun crottin depuis 24h, abdomen distendu, intervention immédiate",
            "Prostration totale, hypothermie, stase fatale en cours",
            "Ballonnement sévère, douleur abdominale, nécrose intestinale",
            "Lapin en décubitus latéral, hypothermie, urgence vitale absolue",
            "Bruxisme sévère, grincements continus, douleur insupportable",
        ],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chien", "condition": "Boiterie sévère sans appui",
        "symptoms": [
            "ne pose plus la patte arrière droite depuis ce matin, douleur visible",
            "boiterie totale du membre antérieur gauche après une chute",
            "refus total d'appuyer sur la patte, gonflement visible du membre",
            "membre postérieur pendant, cri aigu à la palpation",
            "claudication complète, œdème et chaleur localisée sur la patte",
        ],
        "conditions": [
            "Fracture, luxation ou rupture ligamentaire — examen radiographique urgent",
            "Traumatisme osseux ou articulaire sévère, douleur aiguë intense",
            "Lésion orthopédique grave — LCC rompu, fracture ou luxation de hanche",
            "Atteinte neurologique ou vasculaire possible, membre en ischémie",
            "Dysplasie sévère décompensée ou fracture pathologique",
        ],
        "cares": [
            "Immobiliser le membre sans forcer. Vétérinaire dans les 4 heures.",
            "Ne pas masser ni plier la patte. Consultation orthopédique urgente.",
            "Porter le chien pour éviter l'appui. Radio et bilan vétérinaire ce jour.",
            "Garder le chien au repos strict. Clinique vétérinaire dans les 3 heures.",
            "Éviter toute manipulation du membre. Vétérinaire rapidement.",
        ],
        "flags": [
            "Patte froide, bleue ou insensible — urgence vasculaire ou neurologique",
            "Fracture ouverte, os visible, hémorragie locale importante",
            "Douleur insupportable, choc, prostration totale de l'animal",
            "Nécrose ischémique du membre, perte possible sans traitement rapide",
            "Paralysie progressive, atteinte médullaire suspectée",
        ],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chien", "condition": "Fièvre élevée (> 40°C)",
        "symptoms": [
            "température 40,5°C, abattu et refus de manger depuis hier",
            "fièvre 40,8°C mesurée à domicile, vomissement et prostration",
            "hyperthermie, gencives rouge vif, soif excessive",
            "T° 40,2°C, tremblements, n'est pas sorti depuis 24h",
            "fièvre persistante depuis 2 jours, apathie totale",
        ],
        "conditions": [
            "Hyperthermie infectieuse — pyodermite, leptospirose, distemper possible",
            "Fièvre bactérienne ou virale, infection systémique en cours",
            "Syndrome fébrile — bilan vétérinaire urgent pour identifier la cause",
            "Sepsis débutant ou infection focale, fièvre persistante",
            "Fièvre d'origine indéterminée nécessitant bilan sanguin urgent",
        ],
        "cares": [
            "Compresses d'eau fraîche sur les pattes. Vétérinaire dans les 4 heures.",
            "Hydrater avec de l'eau fraîche. Consultation vétérinaire ce jour.",
            "Ne pas donner d'aspirine ni paracétamol. Clinique vétérinaire rapidement.",
            "Garder au frais. Vétérinaire si fièvre > 40°C persiste plus de 4h.",
            "Maintenir l'hydratation. Bilan vétérinaire dans la journée.",
        ],
        "flags": [
            "Fièvre > 41°C, convulsions, choc septique imminent",
            "Prostration totale, gencives pâles, défaillance multi-organes",
            "Méningite, encéphalite, état de mal fébrile",
            "Endocardite, septicémie, choc toxi-infectieux",
            "Insuffisance rénale aiguë, CIVD, pronostic vital engagé",
        ],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chien", "condition": "Plaie profonde / morsure",
        "symptoms": [
            "morsure profonde par un autre chien, plaie béante au niveau du cou",
            "plaie par coupure sur métal rouillé, saigne abondamment",
            "morsure à la cuisse, tissu sous-cutané visible, hématome important",
            "lacération profonde post-bagarre, bords de plaie irréguliers",
            "plaie punctiforme profonde après morsure, érythème autour",
        ],
        "conditions": [
            "Plaie pénétrante avec risque infectieux élevé — bactéries anaérobies, tétanos",
            "Morsure profonde, lésions sous-cutanées possibles, abcès à prévoir",
            "Traumatisme pénétrant, perforation viscérale possible si localisation thoracique",
            "Infection polymicrobienne, pasteurella, staphylocoque, sepsis local",
            "Lacération complexe nécessitant suture et antibiothérapie systémique",
        ],
        "cares": [
            "Rincer à l'eau propre, ne pas fermer la plaie. Vétérinaire dans les 3 heures.",
            "Comprimer le saignement. Consultation vétérinaire urgente ce jour.",
            "Nettoyer à la chlorhexidine diluée. Clinique vétérinaire rapidement.",
            "Éviter antiseptiques agressifs (alcool, eau oxygénée). Vétérinaire pour suture.",
            "Couvrir la plaie avec un linge propre. Bilan vétérinaire dans les 4 heures.",
        ],
        "flags": [
            "Saignement artériel pulsatile, choc hémorragique imminent",
            "Infection fulminante, fasciite nécrosante, choc septique",
            "Atteinte des viscères, abdomen ouvert — urgence chirurgicale",
            "Gangrène gazeuse, tissu noir et malodorant, pronostic sombre",
            "Septicémie post-morsure, fièvre > 40°C, prostration totale",
        ],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chat", "condition": "Détresse respiratoire modérée",
        "symptoms": [
            "respire la bouche ouverte depuis 1h, tête basse",
            "respiration rapide et laborieuse, halète légèrement",
            "flancs qui se soulèvent vite au repos, semble essoufflé",
            "dyspnée modérée, posture en sphinx forcé, bruits respiratoires audibles",
            "toux sèche répétée avec effort respiratoire visible",
        ],
        "conditions": [
            "Détresse respiratoire modérée — asthme félin, épanchement pleural débutant",
            "Dyspnée par asthme, bronchite féline ou cardiopathie décompensée",
            "Épanchement pleural modéré, empyème ou chylothorax",
            "Pneumonie bactérienne ou virale avec impact respiratoire significatif",
            "Thrombo-embolie pulmonaire ou bronchospasme sévère",
        ],
        "cares": [
            "Calmer le chat, pièce fraîche. Vétérinaire dans les 2 heures.",
            "Minimiser le stress. Consultation vétérinaire urgente ce jour.",
            "Aucun effort physique. Transport doux en urgence chez le vétérinaire.",
            "Éviter la chaleur et l'agitation. Clinique vétérinaire rapidement.",
            "Position confortable. Vétérinaire si respiration ne s'améliore pas en 30 min.",
        ],
        "flags": [
            "Gencives bleues, cyanose — urgence respiratoire vitale immédiate",
            "Perte de connaissance, arrêt respiratoire, mort en quelques minutes",
            "Détresse extrême, épuisement total, choc hypoxique",
            "Cyanose et efforts ventilatoires maximaux, asphyxie imminente",
            "Apnée, arrêt cardiorespiratoire, décès sans oxygène immédiat",
        ],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chien", "condition": "Infection oculaire sévère",
        "symptoms": [
            "œil rouge avec pus épais, garde l'œil fermé en permanence",
            "ulcère cornéen visible, larmoiement abondant et douleur à l'œil",
            "œil très enflé, sécrétions jaune-verdâtres abondantes",
            "conjonctivite purulente sévère, troisième paupière très visible",
            "photophobie intense, gratte l'œil constamment, cornée opaque",
        ],
        "conditions": [
            "Conjonctivite purulente sévère ou ulcère cornéen, risque de perforation",
            "Uvéite aiguë ou kératite ulcérative, urgence ophtalmologique vétérinaire",
            "Infection bactérienne oculaire profonde, glaucome secondaire possible",
            "Proptose débutante ou œil enflammé, examen en urgence nécessaire",
            "Panophtalmie débutante, risque de perte définitive de l'œil",
        ],
        "cares": [
            "Rincer l'œil à l'eau saline stérile. Vétérinaire dans les 4 heures.",
            "Ne pas frotter l'œil. Consultation ophtalmologique vétérinaire ce jour.",
            "Éviter lumière vive. Clinique vétérinaire rapidement pour collyre adapté.",
            "Pas de gouttes oculaires humaines. Vétérinaire aujourd'hui.",
            "Compresses de sérum physiologique. Urgence vétérinaire dans les 3 heures.",
        ],
        "flags": [
            "Perforation cornéenne, humeur vitrée visible, perte de l'œil imminente",
            "Proptose totale, globe luxé, urgence chirurgicale ophtalmologique",
            "Glaucome aigu, douleur maximale, cécité irréversible sans traitement",
            "Panophtalmie, œil à énucléer, choc douloureux",
            "Cécité définitive si traitement retardé de plus de 24h",
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    #  MODÉRÉ 📋 (5 scénarios)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "MODÉRÉ 📋", "animal": "chien", "condition": "Vomissement répété sans sang",
        "symptoms": [
            "vomit 3 fois depuis ce matin mais sans sang ni sang",
            "vomissements bilieux à jeun, principalement le matin",
            "vomit après chaque repas depuis 2 jours consécutifs",
            "régurgitations fréquentes, contenu alimentaire non digéré",
            "nausées visibles, vomit de la mousse blanche depuis hier",
        ],
        "conditions": [
            "Gastrite aiguë simple, indigestion ou changement alimentaire brutal",
            "Syndrome de vomissement bilieux, estomac resté vide trop longtemps",
            "Indiscrétion alimentaire, irritation gastrique bénigne",
            "Intolérance alimentaire ou début d'entérite virale légère",
            "Reflux gastro-œsophagien, mégaœsophage débutant",
        ],
        "cares": [
            "Jeûne 12-24h puis réintroduire riz/poulet cuit. Vétérinaire si pas d'amélioration.",
            "Petits repas fréquents de nourriture bland. Consulter si vomissements > 48h.",
            "Hydratation orale douce. Vétérinaire si abattement ou sang apparaît.",
            "Pause alimentaire 12h puis reprise progressive. Clinique si dégradation.",
            "Riz blanc et eau fraîche. Consultation si vomissements persistent plus de 2 jours.",
        ],
        "flags": [
            "Sang dans les vomissements, prostration, déshydratation sévère",
            "Ventre ballonné, douleur abdominale, suspicion d'occlusion intestinale",
            "Vomissements > 5 fois/jour, choc, pâleur des muqueuses",
            "Corps étranger ingéré, obstruction intestinale, urgence chirurgicale",
            "Fièvre > 39,5°C, abattement sévère, refus total de boire",
        ],
    },
    {
        "level": "MODÉRÉ 📋", "animal": "chien", "condition": "Infection auriculaire (otite externe)",
        "symptoms": [
            "secoue la tête fréquemment, gratte l'oreille droite sans arrêt",
            "oreille rouge et malodorante, dépôts brunâtres dans le conduit",
            "douleur à la palpation de l'oreille, penche la tête d'un côté",
            "sécrétions noires dans l'oreille, gémit quand on la touche",
            "conduit auditif gonflé et rouge, prurit auriculaire intense",
        ],
        "conditions": [
            "Otite externe bactérienne ou à levures (Malassezia pachydermatis)",
            "Otite parasitaire (acariens Otodectes cynotis) ou surinfection mixte",
            "Surinfection bactérienne post-corps étranger (épillet dans l'oreille)",
            "Otite chronique décompensée, hyperplasie du conduit auditif",
            "Otite externe récidivante, atopie sous-jacente probable",
        ],
        "cares": [
            "Nettoyage avec solution auriculaire vétérinaire. Vétérinaire dans la semaine.",
            "Ne pas insérer de coton-tige. Consultation vétérinaire pour traitement adapté.",
            "Éviter l'eau dans l'oreille. Clinique vétérinaire pour bilan cytologique.",
            "Nettoyage doux de l'entrée du conduit. Vétérinaire pour collyre auriculaire.",
            "Pas d'automédication. Vétérinaire pour identifier l'agent pathogène responsable.",
        ],
        "flags": [
            "Otite moyenne ou interne, perte d'équilibre, syndrome de Horner",
            "Tympan perforé, douleur neurologique, tête penchée en permanence",
            "Abcès péri-auriculaire, fasciite, chirurgie nécessaire",
            "Surdité unilatérale, nystagmus, atteinte vestibulaire",
            "Infection profonde de l'os pétreux, hospitalisation et chirurgie requises",
        ],
    },
    {
        "level": "MODÉRÉ 📋", "animal": "chien", "condition": "Dermatite / Perte de poils (alopécie)",
        "symptoms": [
            "perd ses poils par plaques rondes, se gratte beaucoup",
            "zones rouges et squameuses sur le ventre et les pattes",
            "démangeaisons intenses, se mordille les pattes en permanence",
            "alopécie diffuse avec peau irritée, lèche la queue constamment",
            "boutons et croûtes sur le dos, dermite visible à l'œil nu",
        ],
        "conditions": [
            "Dermatite atopique, allergie alimentaire ou environnementale",
            "Teigne (dermatophytose) contagieuse à l'humain",
            "Démodécie localisée ou généralisée, immunodépression sous-jacente",
            "Dermatite de contact, réaction à un produit ménager ou shampooing",
            "Pyodermite superficielle ou folliculite bactérienne",
        ],
        "cares": [
            "Shampooing doux hypoallergénique. Vétérinaire pour diagnostic différentiel.",
            "Éviter les allergènes suspects. Consultation dermatologique vétérinaire.",
            "Ne pas gratter les plaques. Clinique vétérinaire pour grattage cutané.",
            "Antihistaminiques vétérinaires si prescrits. Consultation dans la semaine.",
            "Isoler si teigne suspectée. Vétérinaire pour examen de Wood et culture fongique.",
        ],
        "flags": [
            "Surinfection bactérienne sévère, abcès sous-cutané, cellulite",
            "Perte de poils généralisée, automutilation intense, pyodermite profonde",
            "Teigne étendue non traitée, propagation aux autres animaux et aux humains",
            "Démodécie généralisée avec immunosuppression critique",
            "Dermite avec fièvre, choc septique d'origine cutanée",
        ],
    },
    {
        "level": "MODÉRÉ 📋", "animal": "chien", "condition": "Toux persistante",
        "symptoms": [
            "tousse depuis 5 jours, toux productive avec expectorations",
            "toux sèche et répétée après effort physique, abattement modéré",
            "toux nocturne importante, dort mal, respiration légèrement accélérée",
            "toux avec mucus, mouvement des flancs visible à chaque quinte",
            "tousse en buvant ou mangeant, régurgitations nasales",
        ],
        "conditions": [
            "Trachéobronchite infectieuse (maladie de Carré, toux du chenil)",
            "Bronchite chronique, collapsus trachéal (notamment races naines)",
            "Pneumonie bactérienne débutante, bronchopneumonie virale",
            "Insuffisance cardiaque gauche débutante avec œdème pulmonaire",
            "Corps étranger dans les voies respiratoires, fistule oro-nasale",
        ],
        "cares": [
            "Éviter l'effort, remplacer le collier par un harnais. Vétérinaire dans la semaine.",
            "Humidifier l'air de la pièce. Consultation vétérinaire si toux > 7 jours.",
            "Isoler des autres chiens (toux de chenil très contagieuse). Vétérinaire.",
            "Garder au repos. Clinique vétérinaire pour radiographie thoracique.",
            "Éviter fumée et irritants atmosphériques. Vétérinaire pour bilan respiratoire.",
        ],
        "flags": [
            "Toux avec sang (hémoptysie) — urgence respiratoire absolue",
            "Détresse respiratoire, cyanose, incapacité à respirer normalement",
            "Pneumonie sévère, fièvre > 40°C, abattement total",
            "Œdème pulmonaire aigu, orthopnée, urgence cardiaque",
            "Corps étranger obstructif, asphyxie, toux explosive et détresse",
        ],
    },
    {
        "level": "MODÉRÉ 📋", "animal": "chat", "condition": "Perte d'appétit modérée",
        "symptoms": [
            "mange la moitié de sa ration habituelle depuis 3 jours",
            "moins d'enthousiasme pour la gamelle, perd du poids légèrement",
            "snobe les croquettes mais accepte encore les friandises",
            "anorexie partielle depuis 4 jours, boit toujours normalement",
            "appétit réduit de moitié, se couche plus que d'habitude",
        ],
        "conditions": [
            "Anorexie partielle — stress, changement alimentaire, affection dentaire",
            "Lipidose hépatique débutante si anorexie > 3-5 jours chez le chat obèse",
            "Affection rénale chronique (IRC), douleur buccale, ou hyperthyroïdie",
            "Gastrite légère, parasiose intestinale, infestation féline",
            "Dépression/anxiété féline, changement d'environnement récent",
        ],
        "cares": [
            "Réchauffer la nourriture pour stimuler l'appétit. Vétérinaire si > 3 jours.",
            "Proposer différents aliments appétents. Consultation vétérinaire dans la semaine.",
            "Vérifier la bouche (douleur dentaire possible). Clinique si anorexie persiste.",
            "Réduire le stress environnemental. Vétérinaire pour bilan si > 5 jours.",
            "Nourriture humide plus appétente. Vétérinaire si perte de poids visible.",
        ],
        "flags": [
            "Ictère (jaunisse), vomissements associés, dépression sévère",
            "Anorexie totale > 48h — lipidose hépatique urgente",
            "Déshydratation sévère, prostration totale, urgence vétérinaire",
            "Perte de poids rapide (> 10% en 2 semaines), lymphome suspecté",
            "Fièvre persistante, douleur abdominale, péritonite infectieuse féline (FIP)",
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    #  FAIBLE ✅ (5 scénarios)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "FAIBLE ✅", "animal": "chat", "condition": "Vomissement herbe / Boule de poils",
        "symptoms": [
            "vomit de l'herbe digérée ce matin, se porte bien après",
            "régurgite une boule de poils, comportement normal ensuite",
            "a mangé de l'herbe à chat et vomit, joue normalement après",
            "expulse des poils en toussant légèrement, mange normalement",
            "vomissement unique de mousse avec poils, actif et alerte après",
        ],
        "conditions": [
            "Comportement naturel d'auto-purge — vomissement d'herbe normal chez le chat",
            "Trichobézoard (boule de poils) — normal si < 1 fois par semaine",
            "Réflexe éméto-purgatif physiologique, pas de maladie sous-jacente",
            "Expulsion normale de poils ingérés lors du toilettage quotidien",
            "Régurgitation post-ingestion d'herbe, comportement instinctif sain",
        ],
        "cares": [
            "Proposer de l'herbe à chat ou malt anti-boules de poils. Pas d'urgence.",
            "Brosser quotidiennement pour réduire les poils ingérés. Surveillance simple.",
            "Alimentation riche en fibres ou produit anti-hairball. RAS si rare.",
            "Herbe à chat en pot. Vétérinaire uniquement si > 1 fois par semaine.",
            "Surveiller la fréquence. Consultation si vomissements > 2 fois par semaine.",
        ],
        "flags": [
            "Vomissements > 3 fois par semaine, perte de poids, sang dans vomissures",
            "Obstruction par boule de poils, constipation sévère, urgence vétérinaire",
            "Léthargie associée aux vomissements, anorexie prolongée",
            "Mucus ou sang dans les vomissements, changement de comportement",
            "Vomissements chroniques quotidiens — bilan vétérinaire nécessaire",
        ],
    },
    {
        "level": "FAIBLE ✅", "animal": "chat", "condition": "Éternuements occasionnels",
        "symptoms": [
            "éternue 2-3 fois par jour depuis hier, yeux clairs et secs",
            "quelques éternuements matinaux, mange et joue parfaitement normalement",
            "éternuements légers post-changement de litière, sans mucus",
            "éternue parfois mais aucun signe de malaise associé",
            "éternuements isolés, nez légèrement humide, comportement normal",
        ],
        "conditions": [
            "Irritation nasale bénigne — poussière, litière parfumée, pollens saisonniers",
            "Rhinite légère passagère, sans atteinte de l'état général",
            "Réaction à un irritant ménager (spray, désodorisant, fumée de tabac)",
            "Début de rhinite virale bénigne (calicivirus ou herpès félin débutant)",
            "Irritation des voies nasales supérieures, auto-résolutive probable sous 48h",
        ],
        "cares": [
            "Changer de litière (sans parfum). Aérer le logement. Surveiller 48h.",
            "Éviter aérosols et fumée. Vétérinaire si éternuements > 1 semaine.",
            "Litière non poussiéreuse. Observation simple, pas de traitement nécessaire.",
            "Nettoyer les narines avec une compresse humide. Surveiller l'évolution.",
            "Ventiler la pièce. Consulter si apparition de mucus ou d'œil rouge.",
        ],
        "flags": [
            "Mucus épais et purulent, sang au nez, perte d'appétit — consultation vétérinaire",
            "Fièvre, abattement, yeux collés — coryza félin possible",
            "Éternuements > 10/jour avec dyspnée — urgence respiratoire",
            "Masse nasale suspecte, épistaxis unilatérale — biopsie nécessaire",
            "Coryza sévère avec ulcères buccaux — traitement antiviral urgent",
        ],
    },
    {
        "level": "FAIBLE ✅", "animal": "chien", "condition": "Selles molles passagères",
        "symptoms": [
            "selles un peu molles ce matin après avoir mangé des restes de table",
            "diarrhée légère depuis hier, mange et boit parfaitement normalement",
            "fèces moins formées que d'habitude, une seule fois aujourd'hui",
            "selles molles après changement de croquettes, comportement normal",
            "transit un peu perturbé, 2 selles molles dans la journée",
        ],
        "conditions": [
            "Indiscrétion alimentaire — selles molles passagères sans gravité",
            "Sensibilité digestive post-changement de nourriture trop rapide",
            "Colite légère transitoire ou stress digestif bénin",
            "Sensibilité intestinale bénigne, auto-résolutive en 24-48h",
            "Irritation colique passagère sans cause infectieuse identifiée",
        ],
        "cares": [
            "Riz blanc et poulet bouilli 24-48h. Surveiller l'évolution de près.",
            "Jeûne 12h puis nourriture bland. Vétérinaire si diarrhée > 48h.",
            "Probiotiques vétérinaires. Consultation si sang ou mucus apparaît.",
            "Hydratation suffisante. Pas d'urgence si l'animal reste vif et alerte.",
            "Transition alimentaire plus progressive à l'avenir. Surveiller sur 24h.",
        ],
        "flags": [
            "Sang dans les selles, vomissements associés, urgence vétérinaire immédiate",
            "Diarrhée > 48h avec abattement, déshydratation visible, fièvre",
            "Diarrhée explosive et répétée, parvovirus possible (chiot non vacciné)",
            "Mucus en grande quantité, selles noires (méléna), urgence digestive",
            "Douleur abdominale, ventre gonflé, obstruction intestinale possible",
        ],
    },
    {
        "level": "FAIBLE ✅", "animal": "chien", "condition": "Légère prise de poids",
        "symptoms": [
            "a grossi de 2 kg en 6 mois, mange plus que sa ration prescrite",
            "prise de poids progressive, moins d'envie de jouer qu'avant",
            "ventre légèrement arrondi, l'on ne sent plus facilement les côtes",
            "surpoids modéré constaté, sédentarité installée depuis cet hiver",
            "a pris du poids après stérilisation, moins actif qu'avant l'opération",
        ],
        "conditions": [
            "Obésité légère à modérée — surconsommation calorique et sédentarité",
            "Prise de poids post-stérilisation, métabolisme ralenti",
            "Surpoids sans cause endocrinienne — déséquilibre apport/dépense calorique",
            "Obésité débutante, facteur de risque d'arthrose, diabète, cardiopathie",
            "Excès pondéral lié à l'âge et à la baisse naturelle d'activité physique",
        ],
        "cares": [
            "Réduire les rations de 10-15%. Augmenter les promenades progressivement.",
            "Alimentation contrôlée + bilan vétérinaire pour écarter hypothyroïdie.",
            "Croquettes 'light' vétérinaires. Supprimer les friandises. Exercice régulier.",
            "Peser hebdomadairement. Consulter le vétérinaire pour plan amaigrissant.",
            "Jeux actifs quotidiens. Vétérinaire pour évaluation nutritionnelle complète.",
        ],
        "flags": [
            "Prise de poids rapide sans changement alimentaire — hypothyroïdie, Cushing",
            "Œdème, distension abdominale, ascite — urgence cardiaque ou hépatique",
            "Diabète sucré, polyurie et polydipsie associées à la prise de poids",
            "Obésité morbide, boiterie sévère, difficultés respiratoires au repos",
            "Gonflement abdominal rapide, masse palpable abdominale, tumeur suspectée",
        ],
    },
    {
        "level": "FAIBLE ✅", "animal": "chien", "condition": "Grattage léger / Prurit bénin",
        "symptoms": [
            "se gratte derrière les oreilles plusieurs fois par jour",
            "grattage des pattes avant après promenade en herbe haute",
            "se frotte le museau sur les tapis depuis quelques jours",
            "légère irritation cutanée entre les doigts, se lèche les pattes",
            "quelques boutons au niveau de l'aine, gratte occasionnellement",
        ],
        "conditions": [
            "Prurit léger — allergie saisonnière, contact avec herbe ou pollens",
            "Démangeaison post-promenade, irritant environnemental bénin",
            "Sensibilité cutanée légère, folliculite débutante sans gravité",
            "Réaction allergique légère de contact, dépendante de l'exposition",
            "Irritation cutanée bénigne liée à la chaleur ou à la transpiration",
        ],
        "cares": [
            "Bain à l'eau fraîche après les promenades. Surveiller pendant 1 semaine.",
            "Antihistaminique vétérinaire si disponible. Consulter si aggravation.",
            "Éviter l'herbe haute. Rincer les pattes après chaque sortie. Observation.",
            "Shampooing apaisant à l'avoine colloïdale. Vétérinaire si plaques rouges.",
            "Surveiller l'évolution. Consultation si grattage s'intensifie en 5 jours.",
        ],
        "flags": [
            "Plaies ouvertes par le grattage, infection cutanée secondaire",
            "Perte de poils rapide et diffuse, dermatite sévère, urgence dermatologique",
            "Allergie systémique, œdème facial, choc anaphylactique",
            "Parasites visibles (puces, tiques), infestation généralisée",
            "Dermatite profonde, abcès sous-cutané, consultation vétérinaire urgente",
        ],
    },
]

# ─── Génération des outputs (5 FR + 5 EN = 10 variantes par scénario) ─────────

# Correspondances niveau FR → EN
_LEVEL_EN = {
    "CRITIQUE 🚨": "CRITICAL 🚨",
    "ÉLEVÉ ⚠️":    "HIGH ⚠️",
    "MODÉRÉ 📋":   "MODERATE 📋",
    "FAIBLE ✅":   "LOW ✅",
}

def make_outputs(sc):
    """Retourne liste de (output_text, lang) — 5 français + 5 anglais."""
    lvl  = sc["level"]
    anim = sc["animal"]
    cond = sc["condition"]
    A    = anim.capitalize()

    # ── Français ──────────────────────────────────────────────────────────────
    if "CRITIQUE" in lvl:
        emoji      = "🚨"
        delai_fr   = "dans les 30 prochaines minutes"
        urgence_fr = "CRITIQUE — consultation vétérinaire IMMÉDIATE requise"
    elif "ÉLEVÉ" in lvl:
        emoji      = "⚠️"
        delai_fr   = "dans les 2 à 4 heures"
        urgence_fr = "ÉLEVÉ — consultation vétérinaire dans les 2-4 heures"
    elif "MODÉRÉ" in lvl:
        emoji      = "📋"
        delai_fr   = "dans la journée"
        urgence_fr = "MODÉRÉ — consultation vétérinaire recommandée aujourd'hui"
    else:
        emoji      = "✅"
        delai_fr   = "sous 48-72h si pas d'amélioration"
        urgence_fr = "FAIBLE — surveillance à domicile possible"

    fr = [
        (f"{emoji} **Niveau d'urgence : {lvl}**\n\n"
         f"**Analyse pour {anim} :**\n"
         f"• Condition suspectée : {cond}\n"
         f"• Urgence : {urgence_fr}\n\n"
         f"**Actions immédiates :**\n"
         f"• Surveiller attentivement l'état général\n"
         f"• Contacter un vétérinaire {delai_fr}\n"
         f"• Ne pas administrer de médicaments humains\n\n"
         f"{DISCLAIMER_FR}"),

        (f"{emoji} **{lvl} — {A}**\n\n"
         f"**Condition identifiée :** {cond}\n\n"
         f"**Que faire ?**\n"
         f"1. Rester calme et observer attentivement l'animal\n"
         f"2. Contacter le vétérinaire {delai_fr}\n"
         f"3. Ne donner aucun médicament sans prescription vétérinaire\n\n"
         f"**Signes à surveiller :** tout changement rapide de l'état général\n\n"
         f"{DISCLAIMER_FR}"),

        (f"## {emoji} Cheebo — Analyse vétérinaire\n\n"
         f"**Urgence :** {lvl}\n"
         f"**Patient :** {A}\n"
         f"**Diagnostic probable :** {cond}\n\n"
         f"**Recommandations :**\n"
         f"• Appeler la clinique vétérinaire {delai_fr}\n"
         f"• Garder l'animal au calme et au chaud\n"
         f"• Noter l'évolution des symptômes avec l'heure\n\n"
         f"{DISCLAIMER_FR}"),

        (f"{emoji} Niveau **{lvl}** détecté.\n\n"
         f"Votre {anim} présente des signes compatibles avec : **{cond}**.\n\n"
         f"**Conduite à tenir :**\n"
         f"- Consultation vétérinaire {delai_fr}\n"
         f"- Limiter l'activité physique de l'animal\n"
         f"- Aucun traitement maison sans avis professionnel\n\n"
         f"{DISCLAIMER_FR}"),

        (f"**{emoji} Cheebo vous informe :**\n\n"
         f"Niveau d'urgence évalué à **{lvl}** pour votre {anim}.\n\n"
         f"Cause probable : {cond}.\n\n"
         f"**Ce qu'il faut faire maintenant :**\n"
         f"→ Contacter un vétérinaire {delai_fr}\n"
         f"→ Ne pas tenter de traiter à domicile\n"
         f"→ Observer l'évolution et noter tout changement\n\n"
         f"{DISCLAIMER_FR}"),
    ]

    # ── English ───────────────────────────────────────────────────────────────
    lvl_en = _LEVEL_EN.get(lvl, lvl)

    if "CRITIQUE" in lvl:
        delai_en   = "within the next 30 minutes"
        urgence_en = "CRITICAL — IMMEDIATE veterinary consultation required"
    elif "ÉLEVÉ" in lvl:
        delai_en   = "within 2 to 4 hours"
        urgence_en = "HIGH — veterinary consultation within 2-4 hours"
    elif "MODÉRÉ" in lvl:
        delai_en   = "today"
        urgence_en = "MODERATE — veterinary consultation recommended today"
    else:
        delai_en   = "within 48-72h if no improvement"
        urgence_en = "LOW — home monitoring is possible"

    en = [
        (f"{emoji} **Urgency Level: {lvl_en}**\n\n"
         f"**Analysis for {anim}:**\n"
         f"• Suspected condition: {cond}\n"
         f"• Urgency: {urgence_en}\n\n"
         f"**Immediate actions:**\n"
         f"• Monitor the animal's general condition carefully\n"
         f"• Contact a veterinarian {delai_en}\n"
         f"• Do not administer human medications\n\n"
         f"{DISCLAIMER_EN}"),

        (f"{emoji} **{lvl_en} — {A}**\n\n"
         f"**Identified condition:** {cond}\n\n"
         f"**What to do?**\n"
         f"1. Stay calm and observe the animal carefully\n"
         f"2. Contact the veterinarian {delai_en}\n"
         f"3. Do not give any medication without veterinary prescription\n\n"
         f"**Warning signs:** any rapid change in general condition\n\n"
         f"{DISCLAIMER_EN}"),

        (f"## {emoji} Cheebo — Veterinary Analysis\n\n"
         f"**Urgency:** {lvl_en}\n"
         f"**Patient:** {A}\n"
         f"**Probable diagnosis:** {cond}\n\n"
         f"**Recommendations:**\n"
         f"• Call the veterinary clinic {delai_en}\n"
         f"• Keep the animal calm and warm\n"
         f"• Record symptom progression with timestamps\n\n"
         f"{DISCLAIMER_EN}"),

        (f"{emoji} **{lvl_en}** level detected.\n\n"
         f"Your {anim} shows signs consistent with: **{cond}**.\n\n"
         f"**Action plan:**\n"
         f"- Veterinary consultation {delai_en}\n"
         f"- Limit the animal's physical activity\n"
         f"- No home treatment without professional advice\n\n"
         f"{DISCLAIMER_EN}"),

        (f"**{emoji} Cheebo alert:**\n\n"
         f"Urgency level assessed as **{lvl_en}** for your {anim}.\n\n"
         f"Probable cause: {cond}.\n\n"
         f"**What to do right now:**\n"
         f"→ Contact a veterinarian {delai_en}\n"
         f"→ Do not attempt home treatment\n"
         f"→ Monitor the situation and note any changes\n\n"
         f"{DISCLAIMER_EN}"),
    ]

    # Retourner (texte, langue) pour chaque output
    return [(t, "fr") for t in fr] + [(t, "en") for t in en]

# ─── Génération de tous les enregistrements ───────────────────────────────────

def build_input_text(sc, i):
    return (
        f"Niveau d'urgence : {sc['level']}\n"
        f"Animal : {sc['animal']}\n"
        f"Symptômes détectés : {sc['symptoms'][i]}\n"
        f"Conditions possibles : {sc['conditions'][i]}\n"
        f"Soins recommandés : {sc['cares'][i]}\n"
        f"Signes d'alarme : {sc['flags'][i]}"
    )

print("Génération des exemples…")
all_records = []
for sc in SCENARIOS:
    outputs = make_outputs(sc)   # liste de (texte, lang)
    for i in range(5):
        inp = build_input_text(sc, i)
        for out, lang in outputs:
            instruction = INSTRUCTION_FR if lang == "fr" else INSTRUCTION_EN
            all_records.append({"instruction": instruction, "input": inp, "output": out})

random.shuffle(all_records)
print(f"  Exemples bruts générés : {len(all_records)}")

# ─── Ajustement à exactement 2000 ────────────────────────────────────────────

TARGET = 2000
if len(all_records) < TARGET:
    deficit = TARGET - len(all_records)
    all_records.extend(random.choices(all_records, k=deficit))
    random.shuffle(all_records)
    print(f"  Complété à {TARGET} ({deficit} exemples dupliqués aléatoirement)")
else:
    all_records = all_records[:TARGET]
    print(f"  Tronqué à {TARGET}")

print(f"Dataset final : {len(all_records)} exemples ✅")

# ─── Sauvegarde JSON ──────────────────────────────────────────────────────────

out_path = Path("cheebo_dataset_2000.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)
print(f"\nDataset sauvegardé → {out_path.resolve()}")

# ─── HuggingFace Dataset (train/test split) ───────────────────────────────────

try:
    from datasets import Dataset

    dataset      = Dataset.from_list(all_records)
    split        = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split["train"]
    test_dataset  = split["test"]

    print(f"\nEntraînement : {len(train_dataset)} exemples ✅")
    print(f"Test         : {len(test_dataset)} exemples ✅")

    ex = random.choice(all_records)
    print("\n── Exemple aléatoire ──")
    print("INPUT  :", ex["input"][:300])
    print("OUTPUT :", ex["output"][:300])

    import builtins
    builtins.train_dataset = train_dataset
    builtins.test_dataset  = test_dataset
    builtins.final_dataset = dataset

except ImportError:
    print("\n'datasets' non installé — JSON uniquement.")
    print(f"Chemin : {out_path.resolve()}")
