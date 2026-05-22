#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cheebo_multitask_dataset.py
===========================
Génère 2000 exemples multi-tâches pour fine-tuner LLaMA 3.1 8B Instruct.

5 tâches — un seul modèle remplace tous les agents DoctoAgent :
  T1 (400) — Réponse vétérinaire finale      → SynthesisAgent
  T2 (400) — Normalisation des symptômes     → ValidationAgent
  T3 (400) — Prédiction conditions           → PredictionAgent
  T4 (400) — Recommandations de soins        → RecommendationAgent
  T5 (400) — Validation médicale cohérence   → ValidationAgent audit

IMPORTANT : utiliser unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit (pas le modèle base)

Usage Google Colab :
    exec(open('cheebo_multitask_dataset.py').read())
"""

import json, random
from pathlib import Path

random.seed(42)

DISCLAIMER = "_Ces conseils ne remplacent pas l'avis d'un vétérinaire._"

# ── Instructions par tâche ────────────────────────────────────────────────────

INSTR = {
    "T1": (
        "Tu es Cheebo, assistant vétérinaire IA DoctoAgent. "
        "Analyse les symptômes décrits et génère une réponse vétérinaire structurée "
        "avec niveau d'urgence, causes possibles, soins immédiats et signes d'alarme. "
        "Inclus toujours le disclaimer de fin."
    ),
    "T2": (
        "Tu es l'agent de normalisation DoctoAgent. "
        "Extrais et normalise les informations médicales du texte libre. "
        "Réponds UNIQUEMENT avec un JSON valide, sans texte autour."
    ),
    "T3": (
        "Tu es l'agent de prédiction DoctoAgent. "
        "À partir des symptômes normalisés, identifie les associations conditions-symptômes probables. "
        "Réponds UNIQUEMENT avec un JSON valide, sans texte autour."
    ),
    "T4": (
        "Tu es l'agent de recommandations DoctoAgent. "
        "Génère un plan de soins adapté à la condition et à l'espèce animale. "
        "Réponds UNIQUEMENT avec un JSON valide, sans texte autour."
    ),
    "T5": (
        "Tu es l'agent de validation médicale DoctoAgent. "
        "Vérifie la cohérence entre les symptômes et le niveau d'urgence suggéré. "
        "Corrige si le niveau est incorrect. "
        "Réponds UNIQUEMENT avec un JSON valide, sans texte autour."
    ),
}

# ══════════════════════════════════════════════════════════════════════════════
#  TÂCHE 1 — Réponse vétérinaire (8 scénarios × 5 inputs × 10 outputs = 400)
# ══════════════════════════════════════════════════════════════════════════════

T1_SCENARIOS = [
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Torsion gastrique (GDV)",
        "symptoms":    ["ventre ballonné, tentatives vaines de vomir",
                        "abdomen distendu et douloureux, salivation excessive",
                        "ventre gonflé, agitation extrême, incapacité à vomir",
                        "ballonnement abdominal sévère, gémissements",
                        "estomac gonflé, prostration totale"],
        "conditions":  ["Torsion/dilatation gastrique (GDV), urgence chirurgicale absolue",
                        "Syndrome de dilatation-torsion gastrique, pronostic vital engagé",
                        "GDV — torsion de l'estomac, chirurgie d'urgence",
                        "Dilatation-volvulus gastrique, risque de choc",
                        "Torsion gastrique aiguë, urgence vitale"],
        "cares":       ["Ne rien donner. Transport immédiat aux urgences vétérinaires.",
                        "Aucune nourriture ni eau. Urgences vétérinaires maintenant.",
                        "Zéro alimentation. Urgences dans les 30 minutes.",
                        "Interdire tout aliment. Consultation d'urgence immédiate.",
                        "Rien par voie orale. Chaque minute compte."],
        "flags":       ["Gencives blanches ou bleues, effondrement, mort sans chirurgie",
                        "Muqueuses pâles, collapsus, décès si non opéré rapidement",
                        "Gencives décolorées, choc, survie < 6h sans intervention",
                        "Choc cardiogénique, perte de connaissance, pronostic fatal",
                        "Cyanose des muqueuses, choc septique imminent"],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chat mâle", "condition": "Obstruction urinaire",
        "symptoms":    ["crie en essayant d'uriner, abdomen tendu",
                        "ne peut pas uriner depuis 24h, douleur",
                        "allers-retours litière sans uriner, vocalises",
                        "bloqué urinaire, abdomen ballonné, léthargique",
                        "tentatives d'urination sans résultat, douleur abdominale"],
        "conditions":  ["Obstruction urinaire complète, risque d'insuffisance rénale aiguë",
                        "Blocage urétral — urgence vétérinaire absolue",
                        "Uroblock complet, toxémie urémique",
                        "Occlusion urétrale, pronostic vital < 48h",
                        "Obstruction urétrale totale, rétention sévère"],
        "cares":       ["Ne jamais presser la vessie. Urgences vétérinaires immédiatement.",
                        "Transport d'urgence. Aucune pression abdominale.",
                        "Urgences vétérinaires maintenant — délai fatal.",
                        "Consultation d'urgence sans délai.",
                        "Urgence absolue : clinique vétérinaire, nuit et jour."],
        "flags":       ["Vomissements, collapsus, mort par urémie en 24-48h",
                        "Prostration, hypothermie, insuffisance rénale irréversible",
                        "Choc urémique, bradycardie, arrêt cardiaque",
                        "Convulsions, coma urémique, pronostic fatal",
                        "Décompensation cardiaque, décès sans sondage"],
    },
    {
        "level": "CRITIQUE 🚨", "animal": "chien", "condition": "Intoxication au chocolat",
        "symptoms":    ["a mangé du chocolat noir, vomit et tremble",
                        "ingestion chocolat il y a 1h, agitation et tachycardie",
                        "a volé du chocolat, convulsions légères",
                        "chocolat ingéré, diarrhée et tremblements",
                        "a mangé du cacao, vomissements et hyperthermie"],
        "conditions":  ["Intoxication à la théobromine, arythmie cardiaque possible",
                        "Toxicose au chocolat — théobromine cardiotoxique",
                        "Empoisonnement au chocolat, seuil toxique atteint",
                        "Intoxication sévère, SNC et cœur affectés",
                        "Toxicité théobromine aiguë, risque vital"],
        "cares":       ["Appeler le vétérinaire avec type et quantité de chocolat.",
                        "Urgences vétérinaires. Apporter l'emballage.",
                        "Vomissement UNIQUEMENT si conseillé par le vétérinaire.",
                        "Clinique d'urgence avec poids du chien et quantité ingérée.",
                        "Urgences. Ne pas attendre les symptômes graves."],
        "flags":       ["Convulsions, arythmie, hyperthermie > 40°C, mort",
                        "Tachycardie sévère, état de mal épileptique",
                        "Collapsus, coma, arrêt cardiorespiratoire",
                        "Tremblements incontrôlables, perte de conscience",
                        "Fibrillation ventriculaire, décès en quelques heures"],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chien", "condition": "Vomissement avec sang",
        "symptoms":    ["vomit du sang rouge vif depuis ce matin",
                        "vomissements avec sang brun type marc de café",
                        "vomi 4 fois avec du sang, très abattu",
                        "vomissement hémorragique, abdomen sensible",
                        "hématémèse répétée, gencives pâles"],
        "conditions":  ["Hématémèse — ulcère gastrique ou corps étranger",
                        "Vomissement sanglant — atteinte muqueuse gastrique",
                        "Gastrite hémorragique, urgence digestive",
                        "Saignement GI actif, bilan vétérinaire rapide",
                        "Hématémèse avec suspicion de trouble de coagulation"],
        "cares":       ["Jeûne strict. Consultation vétérinaire dans 2 heures.",
                        "Rien par la bouche. Vétérinaire aujourd'hui.",
                        "Garder un échantillon du vomi. Urgence recommandée.",
                        "Aucun médicament humain. Clinique dans 3 heures.",
                        "Repos total. Vétérinaire dans la journée."],
        "flags":       ["Vomissements incessants, choc hémorragique, gencives blanches",
                        "Anémie aiguë, état de choc, collapsus cardiovasculaire",
                        "Sang en grande quantité, perte de conscience",
                        "Perforation gastrique, péritonite, douleur aiguë",
                        "Pâleur extrême, choc hypovolémique imminent"],
    },
    {
        "level": "ÉLEVÉ ⚠️", "animal": "chien", "condition": "Fièvre élevée > 40°C",
        "symptoms":    ["température 40,5°C, abattu depuis hier",
                        "fièvre 40,8°C, vomissement et prostration",
                        "hyperthermie, gencives rouge vif, soif excessive",
                        "T° 40,2°C, tremblements, inactif",
                        "fièvre 2 jours, apathie totale"],
        "conditions":  ["Hyperthermie infectieuse — leptospirose, distemper possible",
                        "Fièvre bactérienne, infection systémique",
                        "Syndrome fébrile — bilan urgent pour identifier la cause",
                        "Sepsis débutant ou infection focale",
                        "Fièvre d'origine indéterminée, bilan sanguin nécessaire"],
        "cares":       ["Compresses d'eau fraîche sur les pattes. Vétérinaire dans 4h.",
                        "Hydrater. Consultation vétérinaire ce jour.",
                        "Ni aspirine ni paracétamol. Clinique rapidement.",
                        "Garder au frais. Vétérinaire si fièvre > 40°C > 4h.",
                        "Maintenir hydratation. Bilan vétérinaire aujourd'hui."],
        "flags":       ["Fièvre > 41°C, convulsions, choc septique",
                        "Prostration totale, gencives pâles, défaillance multi-organes",
                        "Méningite, encéphalite, état de mal fébrile",
                        "Septicémie, choc toxi-infectieux",
                        "Insuffisance rénale aiguë, CIVD"],
    },
    {
        "level": "MODÉRÉ 📋", "animal": "chien", "condition": "Vomissement répété sans sang",
        "symptoms":    ["vomit 3 fois ce matin, sans sang",
                        "vomissements bilieux à jeun le matin",
                        "vomit après chaque repas depuis 2 jours",
                        "régurgitations fréquentes, contenu non digéré",
                        "nausées, vomit mousse blanche depuis hier"],
        "conditions":  ["Gastrite aiguë simple, indigestion",
                        "Syndrome bilieux, estomac vide trop longtemps",
                        "Indiscrétion alimentaire, irritation gastrique",
                        "Intolérance alimentaire ou entérite débutante",
                        "Reflux gastro-œsophagien"],
        "cares":       ["Jeûne 12-24h puis riz/poulet. Vétérinaire si pas d'amélioration.",
                        "Petits repas fréquents. Consulter si > 48h.",
                        "Hydratation douce. Vétérinaire si aggravation.",
                        "Pause 12h puis reprise progressive.",
                        "Riz blanc. Consultation si > 2 jours."],
        "flags":       ["Sang dans vomissements, prostration, déshydratation",
                        "Ventre ballonné, douleur, suspicion d'occlusion",
                        "Vomissements > 5/jour, choc, muqueuses pâles",
                        "Corps étranger, obstruction, urgence chirurgicale",
                        "Fièvre > 39,5°C, abattement sévère"],
    },
    {
        "level": "FAIBLE ✅", "animal": "chat", "condition": "Vomissement herbe / Boule de poils",
        "symptoms":    ["vomit de l'herbe ce matin, se porte bien après",
                        "régurgite une boule de poils, comportement normal",
                        "a mangé de l'herbe à chat et vomit, joue après",
                        "expulse des poils en toussant légèrement",
                        "vomissement unique de mousse avec poils"],
        "conditions":  ["Comportement naturel d'auto-purge, normal chez le chat",
                        "Trichobézoard (boule de poils) — normal si < 1/semaine",
                        "Réflexe éméto-purgatif physiologique",
                        "Expulsion normale de poils ingérés lors du toilettage",
                        "Régurgitation post-ingestion d'herbe, instinctif"],
        "cares":       ["Herbe à chat ou malt anti-boules de poils. Pas d'urgence.",
                        "Brosser quotidiennement. Surveillance simple.",
                        "Alimentation riche en fibres. RAS si rare.",
                        "Herbe à chat en pot. Vétérinaire si > 1/semaine.",
                        "Surveiller la fréquence. Consultation si > 2/semaine."],
        "flags":       ["Vomissements > 3/semaine, perte de poids, sang",
                        "Obstruction par boule de poils, constipation sévère",
                        "Léthargie associée, anorexie prolongée",
                        "Mucus ou sang dans les vomissements",
                        "Vomissements quotidiens chroniques"],
    },
    {
        "level": "FAIBLE ✅", "animal": "chien", "condition": "Grattage léger / Prurit bénin",
        "symptoms":    ["se gratte derrière les oreilles plusieurs fois par jour",
                        "grattage des pattes après promenade en herbe",
                        "se frotte le museau sur les tapis",
                        "légère irritation entre les doigts, se lèche les pattes",
                        "quelques boutons à l'aine, gratte occasionnellement"],
        "conditions":  ["Prurit léger — allergie saisonnière, contact pollens",
                        "Démangeaison post-promenade, irritant environnemental bénin",
                        "Sensibilité cutanée légère, folliculite débutante",
                        "Réaction allergique légère contact-dépendante",
                        "Irritation cutanée bénigne liée à la chaleur"],
        "cares":       ["Bain à l'eau fraîche après promenades. Surveiller 1 semaine.",
                        "Antihistaminique vétérinaire si disponible. Consulter si aggravation.",
                        "Éviter herbe haute. Rincer les pattes. Observation.",
                        "Shampooing apaisant à l'avoine. Vétérinaire si plaques.",
                        "Surveiller 5 jours. Consultation si intensification."],
        "flags":       ["Plaies ouvertes par grattage, infection secondaire",
                        "Perte de poils rapide, dermatite sévère",
                        "Allergie systémique, œdème facial, choc anaphylactique",
                        "Parasites visibles, infestation généralisée",
                        "Abcès sous-cutané, consultation urgente"],
    },
]

def _t1_make_outputs(sc):
    lvl, anim, cond = sc["level"], sc["animal"], sc["condition"]
    A = anim.capitalize()
    if "CRITIQUE" in lvl:
        emoji, delai = "🚨", "dans les 30 prochaines minutes"
        urgline = "CRITIQUE — consultation IMMÉDIATE requise"
    elif "ÉLEVÉ" in lvl:
        emoji, delai = "⚠️", "dans les 2 à 4 heures"
        urgline = "ÉLEVÉ — consultation dans les 2-4 heures"
    elif "MODÉRÉ" in lvl:
        emoji, delai = "📋", "dans la journée"
        urgline = "MODÉRÉ — consultation recommandée aujourd'hui"
    else:
        emoji, delai = "✅", "sous 48-72h si pas d'amélioration"
        urgline = "FAIBLE — surveillance à domicile possible"
    return [
        (f"{emoji} **Niveau d'urgence : {lvl}**\n\n**Analyse pour {anim} :**\n• Condition suspectée : {cond}\n• Urgence : {urgline}\n\n**Actions immédiates :**\n• Surveiller attentivement l'état général\n• Contacter un vétérinaire {delai}\n• Ne pas administrer de médicaments humains\n\n{DISCLAIMER}"),
        (f"{emoji} **{lvl} — {A}**\n\n**Condition identifiée :** {cond}\n\n**Que faire ?**\n1. Rester calme et observer l'animal\n2. Contacter le vétérinaire {delai}\n3. Aucun médicament sans prescription\n\n**Signes à surveiller :** tout changement rapide de l'état général\n\n{DISCLAIMER}"),
        (f"## {emoji} Cheebo — Analyse vétérinaire\n\n**Urgence :** {lvl}\n**Patient :** {A}\n**Diagnostic probable :** {cond}\n\n**Recommandations :**\n• Appeler la clinique vétérinaire {delai}\n• Garder l'animal au calme\n• Noter l'évolution des symptômes\n\n{DISCLAIMER}"),
        (f"{emoji} Niveau **{lvl}** détecté.\n\nVotre {anim} présente des signes compatibles avec : **{cond}**.\n\n**Conduite à tenir :**\n- Consultation vétérinaire {delai}\n- Limiter l'activité physique\n- Aucun traitement maison sans avis\n\n{DISCLAIMER}"),
        (f"**{emoji} {lvl}**\n\nVotre {anim} pourrait souffrir de : *{cond}*.\n\n**Priorité :** consulter le vétérinaire {delai}.\n\nEn attendant :\n✓ Repos complet\n✓ Accès à l'eau fraîche\n✓ Aucun médicament non prescrit\n\n{DISCLAIMER}"),
        (f"🔍 **Évaluation Cheebo**\n\n| Critère | Valeur |\n|---------|--------|\n| Urgence | {lvl} {emoji} |\n| Animal  | {A} |\n| Condition | {cond} |\n\n**Action requise {delai}**\n\n{DISCLAIMER}"),
        (f"**Analyse Cheebo** {emoji}\n\nNiveau : **{lvl}**\n\nLes symptômes correspondent à : {cond}.\n\n**Prochaines étapes :**\n1. Appeler votre vétérinaire\n2. Décrire précisément les symptômes\n3. Suivre les instructions du professionnel\n\n{DISCLAIMER}"),
        (f"{emoji} **Résultat de l'analyse**\n\n**Urgence :** {lvl}\n**Espèce :** {A}\n**Condition :** {cond}\n\nVotre {anim} nécessite une attention vétérinaire {delai}.\n\n**En attendant :**\n• Repos dans un endroit calme\n• Surveillance continue\n• Urgences si aggravation soudaine\n\n{DISCLAIMER}"),
        (f"**{emoji} Cheebo vous informe :**\n\nUrgence **{lvl}** pour votre {anim}.\n\nCause probable : {cond}.\n\n**À faire maintenant :**\n→ Contacter un vétérinaire {delai}\n→ Ne pas traiter à domicile\n→ Observer et noter les changements\n\n{DISCLAIMER}"),
        (f"## Rapport Cheebo {emoji}\n\n**Statut :** {lvl}\n**Animal :** {A}\n**Pathologie :** {cond}\n\nConsultation vétérinaire **{delai}**.\n\n**Conseils :**\n- Animal au calme\n- Eau fraîche si acceptée\n- Appeler la clinique\n\n{DISCLAIMER}"),
    ]

def _t1_build_input(sc, i):
    return (
        f"Niveau d'urgence : {sc['level']}\nAnimal : {sc['animal']}\n"
        f"Symptômes détectés : {sc['symptoms'][i]}\n"
        f"Conditions possibles : {sc['conditions'][i]}\n"
        f"Soins recommandés : {sc['cares'][i]}\n"
        f"Signes d'alarme : {sc['flags'][i]}"
    )

def build_t1():
    records = []
    for sc in T1_SCENARIOS:
        outputs = _t1_make_outputs(sc)
        for i in range(5):
            inp = _t1_build_input(sc, i)
            for out in outputs:
                records.append({"instruction": INSTR["T1"], "input": inp, "output": out})
    return records  # 8 × 5 × 10 = 400

# ══════════════════════════════════════════════════════════════════════════════
#  TÂCHE 2 — Normalisation des symptômes (20 scénarios × 5 textes = 100 × 4 variants = 400)
# ══════════════════════════════════════════════════════════════════════════════

T2_SCENARIOS = [
    {"texts": ["Mon chien vomit depuis hier soir", "Mon chien a des vomissements depuis hier", "Le chien vomissait depuis hier, c'est inquiétant", "Depuis hier soir mon chien vomit", "Mon chien a vomi plusieurs fois hier soir"],
     "out": {"symptoms_normalized": ["vomissement"], "animal": "chien", "duration": "depuis hier", "urgency_hint": "MODERATE", "language": "fr"}},
    {"texts": ["Mon chat ne mange plus depuis 2 jours", "Le chat a arrêté de manger depuis 2 jours", "Mon chat refuse sa gamelle depuis 2 jours", "Anorexie chez mon chat depuis 2 jours", "Mon chat n'a pas touché sa nourriture depuis 2 jours"],
     "out": {"symptoms_normalized": ["anorexie"], "animal": "chat", "duration": "depuis 2 jours", "urgency_hint": "HIGH", "language": "fr"}},
    {"texts": ["Mon lapin n'a plus de crottins depuis hier", "Le lapin n'a pas fait ses besoins depuis hier", "Mon lapin n'a plus produit de crottins depuis hier soir", "Absence de crottins chez mon lapin depuis hier", "Mon lapin a arrêté de faire des crottins hier"],
     "out": {"symptoms_normalized": ["absence_crottins", "anorexie_possible"], "animal": "lapin", "duration": "depuis hier", "urgency_hint": "HIGH", "language": "fr"}},
    {"texts": ["Mon chien a la diarrhée ce matin", "Mon chien fait de la diarrhée depuis ce matin", "Selles molles chez mon chien depuis ce matin", "Mon chien a des selles liquides ce matin", "Diarrhée chez mon chien depuis quelques heures"],
     "out": {"symptoms_normalized": ["diarrhée"], "animal": "chien", "duration": "depuis ce matin", "urgency_hint": "LOW", "language": "fr"}},
    {"texts": ["Mon chat tousse depuis 3 jours", "Toux persistante chez mon chat depuis 3 jours", "Mon chat tousse régulièrement depuis 3 jours", "Mon chat a une toux depuis 3 jours", "Le chat tousse depuis quelques jours"],
     "out": {"symptoms_normalized": ["toux"], "animal": "chat", "duration": "depuis 3 jours", "urgency_hint": "MODERATE", "language": "fr"}},
    {"texts": ["Mon chien boite de la patte avant droite", "Mon chien ne pose plus la patte avant droite", "Boiterie de la patte antérieure droite chez mon chien", "Mon chien claudique sur la patte avant droite", "Mon chien a du mal à appuyer sur sa patte avant droite"],
     "out": {"symptoms_normalized": ["boiterie"], "animal": "chien", "duration": "récent", "urgency_hint": "HIGH", "language": "fr"}},
    {"texts": ["Mon chat mâle essaie d'uriner sans succès", "Mon chat mâle va à la litière mais n'urine pas", "Mon chat mâle ne peut plus uriner", "Blocage urinaire chez mon chat mâle", "Mon chat mâle crie quand il essaie d'uriner"],
     "out": {"symptoms_normalized": ["rétention_urinaire", "douleur_miction"], "animal": "chat mâle", "duration": "récent", "urgency_hint": "CRITICAL", "language": "fr"}},
    {"texts": ["Mon chien a eu une convulsion ce matin", "Mon chien a fait une crise d'épilepsie", "Convulsions chez mon chien depuis ce matin", "Mon chien a tremblé et perdu connaissance", "Mon chien a eu des convulsions ce matin"],
     "out": {"symptoms_normalized": ["convulsion"], "animal": "chien", "duration": "ce matin", "urgency_hint": "CRITICAL", "language": "fr"}},
    {"texts": ["Le ventre de mon chien est très gonflé", "Mon chien a l'abdomen distendu", "Ventre ballonné chez mon chien", "Mon chien a le ventre dur et gonflé", "L'abdomen de mon chien est anormalement gonflé"],
     "out": {"symptoms_normalized": ["distension_abdominale"], "animal": "chien", "duration": "récent", "urgency_hint": "CRITICAL", "language": "fr"}},
    {"texts": ["Mon chat mange de l'herbe et vomit ensuite", "Mon chat ingère de l'herbe puis vomit", "Mon chat vomit après avoir mangé de l'herbe", "Mon chat a vomi de l'herbe ce matin", "Mon chat mange de l'herbe et régurgite"],
     "out": {"symptoms_normalized": ["vomissement_herbe"], "animal": "chat", "duration": "occasionnel", "urgency_hint": "LOW", "language": "fr"}},
    {"texts": ["Mon chien s'est blessé à la patte, il y a du sang", "Mon chien a une plaie ouverte à la patte", "Blessure avec saignement sur la patte de mon chien", "Mon chien a été mordu et saigne", "Mon chien a une coupure profonde qui saigne"],
     "out": {"symptoms_normalized": ["plaie_hémorragique", "blessure"], "animal": "chien", "duration": "récent", "urgency_hint": "HIGH", "language": "fr"}},
    {"texts": ["Mon chat a les yeux rouges et coule", "Les yeux de mon chat sont rouges et larmoyants", "Mon chat a un œil rouge avec des sécrétions", "Conjonctivite chez mon chat, yeux rouges", "Mon chat a les yeux irrités et rouges"],
     "out": {"symptoms_normalized": ["conjonctivite", "larmoiement"], "animal": "chat", "duration": "récent", "urgency_hint": "MODERATE", "language": "fr"}},
    {"texts": ["Mon chien a mangé du chocolat", "Mon chien a volé du chocolat dans la cuisine", "Mon chien a ingéré du chocolat il y a une heure", "Mon chien a mangé une tablette de chocolat", "Mon chien a consommé du chocolat accidentellement"],
     "out": {"symptoms_normalized": ["ingestion_toxique_chocolat"], "animal": "chien", "duration": "il y a 1h", "urgency_hint": "CRITICAL", "language": "fr"}},
    {"texts": ["Mon lapin est apathique et ne bouge plus", "Mon lapin est prostré et ne réagit plus", "Mon lapin est très lent et apathique depuis hier", "Mon lapin ne bouge plus et semble souffrir", "Le lapin est léthargique depuis hier soir"],
     "out": {"symptoms_normalized": ["apathie", "léthargie"], "animal": "lapin", "duration": "depuis hier", "urgency_hint": "HIGH", "language": "fr"}},
    {"texts": ["Mon chien se gratte beaucoup depuis quelques jours", "Mon chien se gratte en permanence", "Grattage intense chez mon chien depuis 3 jours", "Mon chien se gratte et se lèche les pattes", "Mon chien est très démangé depuis quelques jours"],
     "out": {"symptoms_normalized": ["prurit", "grattage"], "animal": "chien", "duration": "depuis quelques jours", "urgency_hint": "LOW", "language": "fr"}},
    {"texts": ["Mon chat éternue souvent depuis hier", "Éternuements répétés chez mon chat depuis hier", "Mon chat éternue plusieurs fois par jour", "Mon chat a des éternuements fréquents", "Mon chat éternue beaucoup depuis hier matin"],
     "out": {"symptoms_normalized": ["éternuements"], "animal": "chat", "duration": "depuis hier", "urgency_hint": "LOW", "language": "fr"}},
    {"texts": ["Mon chien perd ses poils par plaques", "Chute de poils anormale chez mon chien", "Mon chien a des zones sans poils", "Mon chien perd ses poils en plaques rondes", "Alopécie chez mon chien depuis 2 semaines"],
     "out": {"symptoms_normalized": ["alopécie", "perte_de_poils"], "animal": "chien", "duration": "depuis 2 semaines", "urgency_hint": "MODERATE", "language": "fr"}},
    {"texts": ["My dog has been vomiting since this morning", "My dog vomited several times today", "Dog vomiting since morning, worried", "My dog keeps vomiting today", "My dog has been throwing up since this morning"],
     "out": {"symptoms_normalized": ["vomissement"], "animal": "chien", "duration": "since this morning", "urgency_hint": "MODERATE", "language": "en"}},
    {"texts": ["My cat is not eating for 2 days", "Cat refused food for 2 days", "My cat hasn't eaten in 2 days", "Cat anorexia for 2 days", "My cat stopped eating 2 days ago"],
     "out": {"symptoms_normalized": ["anorexie"], "animal": "chat", "duration": "for 2 days", "urgency_hint": "HIGH", "language": "en"}},
    {"texts": ["My male cat can't urinate, crying in pain", "Male cat straining to urinate with no output", "My male cat is blocked and can't pee", "Cat urinary blockage, crying", "My male cat is trying to urinate but nothing comes out"],
     "out": {"symptoms_normalized": ["rétention_urinaire", "douleur_miction"], "animal": "chat mâle", "duration": "recent", "urgency_hint": "CRITICAL", "language": "en"}},
]

def build_t2():
    records = []
    for sc in T2_SCENARIOS:
        out_str = json.dumps(sc["out"], ensure_ascii=False)
        # 4 variants du même JSON (reformulations mineures)
        out_variants = [
            out_str,
            json.dumps(sc["out"], ensure_ascii=False, indent=2),
            json.dumps({k: v for k, v in sc["out"].items()}, ensure_ascii=False),
            json.dumps(sc["out"], ensure_ascii=False, separators=(',', ': ')),
        ]
        for text in sc["texts"]:
            for ov in out_variants[:5]:
                records.append({"instruction": INSTR["T2"], "input": text, "output": ov})
    return records[:400]

# ══════════════════════════════════════════════════════════════════════════════
#  TÂCHE 3 — Prédiction conditions (20 scénarios × 20 variants = 400)
# ══════════════════════════════════════════════════════════════════════════════

T3_SCENARIOS = [
    {"input": "Symptômes: [vomissement, diarrhée] | Animal: chien | Durée: 2 jours | Urgence: MODERATE",
     "out": {"possible_associations": [{"condition": "gastro-entérite", "frequency": "HIGH", "urgency_hint": "MODERATE", "requires_vet": True, "watch_for": "sang dans selles ou vomissements"}], "main_concern": "déshydratation possible", "watch_delay": "24-48h", "confidence": 0.82}},
    {"input": "Symptômes: [distension_abdominale, tentatives_vomissement] | Animal: chien | Durée: 2h | Urgence: CRITICAL",
     "out": {"possible_associations": [{"condition": "torsion gastrique (GDV)", "frequency": "HIGH", "urgency_hint": "CRITICAL", "requires_vet": True, "watch_for": "gencives blanches, collapsus"}], "main_concern": "urgence chirurgicale vitale", "watch_delay": "immédiat", "confidence": 0.95}},
    {"input": "Symptômes: [rétention_urinaire, douleur_miction] | Animal: chat mâle | Durée: 24h | Urgence: CRITICAL",
     "out": {"possible_associations": [{"condition": "obstruction urétrale", "frequency": "HIGH", "urgency_hint": "CRITICAL", "requires_vet": True, "watch_for": "vomissements, collapsus, urémie"}], "main_concern": "blocage urinaire — urgence vitale", "watch_delay": "immédiat", "confidence": 0.97}},
    {"input": "Symptômes: [toux, dyspnée_modérée] | Animal: chat | Durée: 3 jours | Urgence: HIGH",
     "out": {"possible_associations": [{"condition": "asthme félin", "frequency": "HIGH", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "cyanose, gencives bleues"}, {"condition": "épanchement pleural", "frequency": "MEDIUM", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "orthopnée, détresse respiratoire"}], "main_concern": "détresse respiratoire possible", "watch_delay": "2-4h", "confidence": 0.78}},
    {"input": "Symptômes: [anorexie, léthargie] | Animal: lapin | Durée: 12h | Urgence: HIGH",
     "out": {"possible_associations": [{"condition": "stase digestive débutante", "frequency": "HIGH", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "absence crottins, distension abdominale"}], "main_concern": "iléus débutant — dangereux chez le lapin", "watch_delay": "2-4h", "confidence": 0.88}},
    {"input": "Symptômes: [convulsion] | Animal: chien | Durée: 5min | Urgence: CRITICAL",
     "out": {"possible_associations": [{"condition": "état de mal épileptique", "frequency": "HIGH", "urgency_hint": "CRITICAL", "requires_vet": True, "watch_for": "hyperthermie, coma, lésions cérébrales"}], "main_concern": "urgence neurologique vitale", "watch_delay": "immédiat", "confidence": 0.94}},
    {"input": "Symptômes: [ingestion_toxique_chocolat] | Animal: chien | Durée: 1h | Urgence: CRITICAL",
     "out": {"possible_associations": [{"condition": "intoxication à la théobromine", "frequency": "HIGH", "urgency_hint": "CRITICAL", "requires_vet": True, "watch_for": "convulsions, arythmie, hyperthermie"}], "main_concern": "toxicose au chocolat — urgence selon quantité", "watch_delay": "immédiat", "confidence": 0.92}},
    {"input": "Symptômes: [vomissement_herbe] | Animal: chat | Durée: occasionnel | Urgence: LOW",
     "out": {"possible_associations": [{"condition": "comportement d'auto-purge normal", "frequency": "HIGH", "urgency_hint": "LOW", "requires_vet": False, "watch_for": "fréquence > 3/semaine, présence de sang"}], "main_concern": "comportement physiologique normal", "watch_delay": "72h si aggravation", "confidence": 0.90}},
    {"input": "Symptômes: [prurit, grattage] | Animal: chien | Durée: quelques jours | Urgence: LOW",
     "out": {"possible_associations": [{"condition": "allergie saisonnière ou de contact", "frequency": "HIGH", "urgency_hint": "LOW", "requires_vet": False, "watch_for": "plaies, perte de poils, infection cutanée"}], "main_concern": "prurit léger, surveillance recommandée", "watch_delay": "5-7 jours", "confidence": 0.75}},
    {"input": "Symptômes: [boiterie, douleur_membre] | Animal: chien | Durée: ce matin | Urgence: HIGH",
     "out": {"possible_associations": [{"condition": "fracture ou rupture ligamentaire", "frequency": "MEDIUM", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "membre froid, insensible, bleu"}, {"condition": "entorse sévère", "frequency": "HIGH", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "aggravation douleur, gonflement"}], "main_concern": "lésion orthopédique grave possible", "watch_delay": "2-4h", "confidence": 0.80}},
    {"input": "Symptômes: [anorexie] | Animal: chat | Durée: 3 jours | Urgence: MODERATE",
     "out": {"possible_associations": [{"condition": "lipidose hépatique débutante", "frequency": "MEDIUM", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "ictère, vomissements, prostration"}, {"condition": "affection dentaire", "frequency": "HIGH", "urgency_hint": "MODERATE", "requires_vet": True, "watch_for": "douleur buccale, hypersalivation"}], "main_concern": "anorexie prolongée dangereuse chez le chat", "watch_delay": "24h", "confidence": 0.72}},
    {"input": "Symptômes: [plaie_hémorragique, blessure] | Animal: chien | Durée: récent | Urgence: HIGH",
     "out": {"possible_associations": [{"condition": "plaie pénétrante avec risque infectieux", "frequency": "HIGH", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "saignement artériel, infection, choc"}], "main_concern": "risque infectieux et hémorragique", "watch_delay": "2-4h", "confidence": 0.88}},
    {"input": "Symptômes: [éternuements] | Animal: chat | Durée: depuis hier | Urgence: LOW",
     "out": {"possible_associations": [{"condition": "irritation nasale bénigne", "frequency": "HIGH", "urgency_hint": "LOW", "requires_vet": False, "watch_for": "mucus épais, fièvre, perte d'appétit"}], "main_concern": "éternuements bénins, surveillance simple", "watch_delay": "5-7 jours", "confidence": 0.85}},
    {"input": "Symptômes: [alopécie, perte_de_poils] | Animal: chien | Durée: 2 semaines | Urgence: MODERATE",
     "out": {"possible_associations": [{"condition": "dermatite atopique", "frequency": "HIGH", "urgency_hint": "MODERATE", "requires_vet": True, "watch_for": "surinfection, plaies"}, {"condition": "teigne (dermatophytose)", "frequency": "MEDIUM", "urgency_hint": "MODERATE", "requires_vet": True, "watch_for": "transmission humains, extension rapide"}], "main_concern": "diagnostic différentiel nécessaire", "watch_delay": "dans la semaine", "confidence": 0.70}},
    {"input": "Symptômes: [conjonctivite, larmoiement] | Animal: chat | Durée: récent | Urgence: MODERATE",
     "out": {"possible_associations": [{"condition": "conjonctivite infectieuse (herpès, chlamydia)", "frequency": "HIGH", "urgency_hint": "MODERATE", "requires_vet": True, "watch_for": "ulcère cornéen, sécrétions purulentes"}], "main_concern": "traitement local nécessaire", "watch_delay": "dans la journée", "confidence": 0.82}},
    {"input": "Symptômes: [vomissement, sang_vomissements] | Animal: chien | Durée: ce matin | Urgence: HIGH",
     "out": {"possible_associations": [{"condition": "hématémèse — ulcère gastrique ou corps étranger", "frequency": "HIGH", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "choc hémorragique, gencives blanches"}], "main_concern": "saignement GI actif", "watch_delay": "2-4h", "confidence": 0.87}},
    {"input": "Symptômes: [hyperthermie, prostration] | Animal: chien | Durée: après exercice | Urgence: CRITICAL",
     "out": {"possible_associations": [{"condition": "coup de chaleur", "frequency": "HIGH", "urgency_hint": "CRITICAL", "requires_vet": True, "watch_for": "convulsions, CIVD, défaillance multi-organes"}], "main_concern": "urgence thermique vitale", "watch_delay": "immédiat", "confidence": 0.93}},
    {"input": "Symptômes: [vomissement, diarrhea] | Animal: dog | Duration: 2 days | Urgency: MODERATE",
     "out": {"possible_associations": [{"condition": "gastroenteritis", "frequency": "HIGH", "urgency_hint": "MODERATE", "requires_vet": True, "watch_for": "blood in stool or vomit, dehydration"}], "main_concern": "possible dehydration", "watch_delay": "24-48h", "confidence": 0.82}},
    {"input": "Symptômes: [urinary_retention, pain] | Animal: male cat | Duration: 24h | Urgency: CRITICAL",
     "out": {"possible_associations": [{"condition": "urethral obstruction", "frequency": "HIGH", "urgency_hint": "CRITICAL", "requires_vet": True, "watch_for": "vomiting, collapse, uremia"}], "main_concern": "urinary blockage — life-threatening emergency", "watch_delay": "immediate", "confidence": 0.97}},
    {"input": "Symptômes: [lethargy, anorexia] | Animal: rabbit | Duration: 12h | Urgency: HIGH",
     "out": {"possible_associations": [{"condition": "GI stasis beginning", "frequency": "HIGH", "urgency_hint": "HIGH", "requires_vet": True, "watch_for": "no droppings, abdominal distension"}], "main_concern": "dangerous early ileus in rabbit", "watch_delay": "2-4h", "confidence": 0.88}},
]

def build_t3():
    records = []
    for sc in T3_SCENARIOS:
        out_str  = json.dumps(sc["out"], ensure_ascii=False)
        out_ind  = json.dumps(sc["out"], ensure_ascii=False, indent=2)
        variants = [out_str, out_ind, out_str, out_ind, out_str,
                    out_ind, out_str, out_ind, out_str, out_ind,
                    out_str, out_ind, out_str, out_ind, out_str,
                    out_ind, out_str, out_ind, out_str, out_ind]
        for ov in variants:
            records.append({"instruction": INSTR["T3"], "input": sc["input"], "output": ov})
    return records[:400]

# ══════════════════════════════════════════════════════════════════════════════
#  TÂCHE 4 — Recommandations de soins (20 scénarios × 20 variants = 400)
# ══════════════════════════════════════════════════════════════════════════════

T4_SCENARIOS = [
    {"input": "Condition: torsion gastrique (GDV) | Animal: chien | Urgence: CRITICAL",
     "out": {"immediate_care": ["aucune nourriture ni eau", "transport immédiat aux urgences vétérinaires", "ne pas presser l'abdomen"], "vet_needed": True, "delay": "dans les 30 minutes", "home_care_ok": False, "emergency_signs": ["gencives blanches", "collapsus"], "surgery_required": True}},
    {"input": "Condition: obstruction urétrale | Animal: chat mâle | Urgence: CRITICAL",
     "out": {"immediate_care": ["ne pas presser la vessie", "transport d'urgence chez le vétérinaire", "aucune manipulation abdominale"], "vet_needed": True, "delay": "immédiatement", "home_care_ok": False, "emergency_signs": ["vomissements", "prostration", "coma urémique"], "surgery_required": False}},
    {"input": "Condition: intoxication chocolat | Animal: chien | Urgence: CRITICAL",
     "out": {"immediate_care": ["appeler le vétérinaire avec quantité et type de chocolat", "apporter l'emballage", "ne pas induire vomissement sans conseil vétérinaire"], "vet_needed": True, "delay": "immédiatement", "home_care_ok": False, "emergency_signs": ["convulsions", "arythmie cardiaque"], "surgery_required": False}},
    {"input": "Condition: gastrite aiguë simple | Animal: chien | Urgence: MODERATE",
     "out": {"immediate_care": ["jeûne 12-24h", "réintroduire riz blanc et poulet cuit", "eau fraîche disponible"], "vet_needed": True, "delay": "sous 24-48h si pas d'amélioration", "home_care_ok": True, "emergency_signs": ["sang dans vomissements", "déshydratation sévère"], "surgery_required": False}},
    {"input": "Condition: stase digestive lapin | Animal: lapin | Urgence: HIGH",
     "out": {"immediate_care": ["foin frais en permanence", "eau fraîche", "massage abdominal doux", "maintenir au chaud"], "vet_needed": True, "delay": "dans les 4 heures", "home_care_ok": False, "emergency_signs": ["aucun crottin 24h", "abdomen distendu", "prostration"], "surgery_required": False}},
    {"input": "Condition: convulsion épileptique | Animal: chien | Urgence: CRITICAL",
     "out": {"immediate_care": ["chronométrer la crise", "protéger la tête", "écarter les objets dangereux", "ne pas mettre les doigts dans la bouche"], "vet_needed": True, "delay": "immédiatement si > 5 minutes", "home_care_ok": False, "emergency_signs": ["crise > 5 min", "hyperthermie", "coma"], "surgery_required": False}},
    {"input": "Condition: coup de chaleur | Animal: chien | Urgence: CRITICAL",
     "out": {"immediate_care": ["refroidir avec eau tiède (pas froide)", "compresses sur cou et aisselles", "voiture climatisée", "urgences vétérinaires"], "vet_needed": True, "delay": "immédiatement", "home_care_ok": False, "emergency_signs": ["convulsions", "perte de connaissance", "CIVD"], "surgery_required": False}},
    {"input": "Condition: hématémèse (vomissement avec sang) | Animal: chien | Urgence: HIGH",
     "out": {"immediate_care": ["jeûne hydrique strict", "garder échantillon du vomi", "aucun médicament humain"], "vet_needed": True, "delay": "dans les 2 heures", "home_care_ok": False, "emergency_signs": ["choc hémorragique", "gencives blanches", "collapsus"], "surgery_required": False}},
    {"input": "Condition: prurit léger saisonnier | Animal: chien | Urgence: LOW",
     "out": {"immediate_care": ["bain à l'eau fraîche après promenades", "rincer les pattes", "shampooing hypoallergénique"], "vet_needed": False, "delay": "sous 5-7 jours si pas d'amélioration", "home_care_ok": True, "emergency_signs": ["plaies ouvertes", "infection cutanée"], "surgery_required": False}},
    {"input": "Condition: vomissement herbe normal | Animal: chat | Urgence: LOW",
     "out": {"immediate_care": ["proposer herbe à chat", "brosser quotidiennement", "malt anti-boules de poils"], "vet_needed": False, "delay": "si > 2 fois par semaine", "home_care_ok": True, "emergency_signs": ["sang dans vomissements", "perte de poids"], "surgery_required": False}},
    {"input": "Condition: boiterie sévère (fracture suspectée) | Animal: chien | Urgence: HIGH",
     "out": {"immediate_care": ["immobiliser le membre sans forcer", "porter le chien", "éviter tout appui"], "vet_needed": True, "delay": "dans les 4 heures", "home_care_ok": False, "emergency_signs": ["membre froid ou insensible", "fracture ouverte"], "surgery_required": False}},
    {"input": "Condition: fièvre bactérienne > 40°C | Animal: chien | Urgence: HIGH",
     "out": {"immediate_care": ["compresses d'eau fraîche sur pattes", "hydrater", "ni aspirine ni paracétamol"], "vet_needed": True, "delay": "dans les 4 heures", "home_care_ok": False, "emergency_signs": ["fièvre > 41°C", "convulsions", "choc septique"], "surgery_required": False}},
    {"input": "Condition: éternuements bénins | Animal: chat | Urgence: LOW",
     "out": {"immediate_care": ["changer de litière (sans parfum)", "aérer le logement", "nettoyer les narines"], "vet_needed": False, "delay": "si > 1 semaine ou apparition mucus", "home_care_ok": True, "emergency_signs": ["mucus épais", "perte appétit", "fièvre"], "surgery_required": False}},
    {"input": "Condition: dermatite atopique | Animal: chien | Urgence: MODERATE",
     "out": {"immediate_care": ["shampooing hypoallergénique", "identifier et éviter allergènes", "antihistaminique vétérinaire si disponible"], "vet_needed": True, "delay": "dans la semaine", "home_care_ok": True, "emergency_signs": ["surinfection", "plaies profondes"], "surgery_required": False}},
    {"input": "Condition: anorexie partielle (chat) | Animal: chat | Urgence: MODERATE",
     "out": {"immediate_care": ["réchauffer la nourriture", "proposer nourriture humide", "réduire le stress"], "vet_needed": True, "delay": "si anorexie > 3 jours", "home_care_ok": True, "emergency_signs": ["ictère", "prostration totale", "anorexie totale > 48h"], "surgery_required": False}},
    {"input": "Condition: plaie profonde / morsure | Animal: chien | Urgence: HIGH",
     "out": {"immediate_care": ["rincer à l'eau propre", "comprimer saignement", "ne pas fermer la plaie", "éviter antiseptiques agressifs"], "vet_needed": True, "delay": "dans les 3 heures", "home_care_ok": False, "emergency_signs": ["saignement artériel", "choc septique"], "surgery_required": False}},
    {"input": "Condition: diarrhée légère post-alimentaire | Animal: chien | Urgence: LOW",
     "out": {"immediate_care": ["riz blanc et poulet 24-48h", "hydratation suffisante", "probiotiques vétérinaires"], "vet_needed": False, "delay": "si diarrhée > 48h", "home_care_ok": True, "emergency_signs": ["sang dans selles", "vomissements associés", "déshydratation"], "surgery_required": False}},
    {"input": "Condition: gastric dilation-volvulus | Animal: dog | Urgency: CRITICAL",
     "out": {"immediate_care": ["nothing by mouth", "immediate transport to emergency vet", "do not press abdomen"], "vet_needed": True, "delay": "within 30 minutes", "home_care_ok": False, "emergency_signs": ["white gums", "collapse", "shock"], "surgery_required": True}},
    {"input": "Condition: mild seasonal itching | Animal: dog | Urgency: LOW",
     "out": {"immediate_care": ["rinse paws after walks", "cool water bath", "hypoallergenic shampoo"], "vet_needed": False, "delay": "within 5-7 days if no improvement", "home_care_ok": True, "emergency_signs": ["open wounds", "skin infection"], "surgery_required": False}},
    {"input": "Condition: urinary blockage | Animal: male cat | Urgency: CRITICAL",
     "out": {"immediate_care": ["do not press bladder", "immediate emergency vet transport", "no abdominal manipulation"], "vet_needed": True, "delay": "immediately", "home_care_ok": False, "emergency_signs": ["vomiting", "collapse", "uremic coma"], "surgery_required": False}},
    {"input": "Condition: hairball vomiting | Animal: cat | Urgency: LOW",
     "out": {"immediate_care": ["provide cat grass", "daily brushing", "hairball prevention malt"], "vet_needed": False, "delay": "if more than twice per week", "home_care_ok": True, "emergency_signs": ["blood in vomit", "weight loss"], "surgery_required": False}},
]

def build_t4():
    records = []
    for sc in T4_SCENARIOS:
        out_str  = json.dumps(sc["out"], ensure_ascii=False)
        out_ind  = json.dumps(sc["out"], ensure_ascii=False, indent=2)
        for _ in range(20):
            ov = out_str if random.random() > 0.5 else out_ind
            records.append({"instruction": INSTR["T4"], "input": sc["input"], "output": ov})
    return records[:400]

# ══════════════════════════════════════════════════════════════════════════════
#  TÂCHE 5 — Validation médicale (20 scénarios × 20 = 400)
#  Mix : 10 cas corrects + 10 cas avec urgence incorrecte à corriger
# ══════════════════════════════════════════════════════════════════════════════

T5_SCENARIOS = [
    # Cas corrects (valid=True)
    {"input": "Symptômes: [distension_abdominale, vomissement] | Urgence suggérée: CRITICAL | Animal: chien",
     "out": {"valid": True, "corrected_urgency": "CRITICAL", "reason": "Torsion gastrique probable — urgence vitale confirmée", "confidence": 0.96, "flags_detected": ["distension abdominale", "tentatives vomissement"]}},
    {"input": "Symptômes: [rétention_urinaire] | Urgence suggérée: CRITICAL | Animal: chat mâle",
     "out": {"valid": True, "corrected_urgency": "CRITICAL", "reason": "Obstruction urétrale — urgence absolue confirmée", "confidence": 0.98, "flags_detected": ["rétention urinaire totale"]}},
    {"input": "Symptômes: [vomissement_herbe] | Urgence suggérée: LOW | Animal: chat",
     "out": {"valid": True, "corrected_urgency": "LOW", "reason": "Comportement physiologique normal — niveau LOW confirmé", "confidence": 0.91, "flags_detected": []}},
    {"input": "Symptômes: [éternuements_occasionnels] | Urgence suggérée: LOW | Animal: chat",
     "out": {"valid": True, "corrected_urgency": "LOW", "reason": "Irritation nasale bénigne — niveau LOW confirmé", "confidence": 0.88, "flags_detected": []}},
    {"input": "Symptômes: [convulsion_prolongée] | Urgence suggérée: CRITICAL | Animal: chien",
     "out": {"valid": True, "corrected_urgency": "CRITICAL", "reason": "État de mal épileptique — urgence neurologique vitale", "confidence": 0.97, "flags_detected": ["durée > 5 min", "risque hyperthermie"]}},
    {"input": "Symptômes: [boiterie_sévère_sans_appui] | Urgence suggérée: HIGH | Animal: chien",
     "out": {"valid": True, "corrected_urgency": "HIGH", "reason": "Fracture ou rupture ligamentaire probable — niveau HIGH confirmé", "confidence": 0.85, "flags_detected": ["non-appui total"]}},
    {"input": "Symptômes: [anorexie_partielle] | Urgence suggérée: MODERATE | Animal: chat",
     "out": {"valid": True, "corrected_urgency": "MODERATE", "reason": "Anorexie partielle < 3 jours — niveau MODERATE confirmé", "confidence": 0.80, "flags_detected": []}},
    {"input": "Symptômes: [prurit_léger] | Urgence suggérée: LOW | Animal: chien",
     "out": {"valid": True, "corrected_urgency": "LOW", "reason": "Prurit bénin saisonnier — niveau LOW confirmé", "confidence": 0.87, "flags_detected": []}},
    {"input": "Symptômes: [vomissement_sang] | Urgence suggérée: HIGH | Animal: chien",
     "out": {"valid": True, "corrected_urgency": "HIGH", "reason": "Hématémèse — urgence digestive HIGH confirmée", "confidence": 0.89, "flags_detected": ["sang dans vomissements"]}},
    {"input": "Symptômes: [ingestion_chocolat] | Urgence suggérée: CRITICAL | Animal: chien",
     "out": {"valid": True, "corrected_urgency": "CRITICAL", "reason": "Intoxication théobromine — urgence CRITICAL confirmée", "confidence": 0.93, "flags_detected": ["ingestion toxique"]}},
    # Cas incorrects — urgence sous-estimée (valid=False)
    {"input": "Symptômes: [absence_crottins_48h, distension_abdominale] | Urgence suggérée: LOW | Animal: lapin",
     "out": {"valid": False, "corrected_urgency": "CRITICAL", "reason": "Stase digestive totale chez le lapin — urgence vitale, LOW incorrect", "confidence": 0.95, "flags_detected": ["absence crottins 48h", "distension abdominale"]}},
    {"input": "Symptômes: [convulsion] | Urgence suggérée: MODERATE | Animal: chien",
     "out": {"valid": False, "corrected_urgency": "CRITICAL", "reason": "Toute convulsion chez le chien = CRITICAL minimum — MODERATE incorrect", "confidence": 0.97, "flags_detected": ["convulsion = urgence neurologique"]}},
    {"input": "Symptômes: [rétention_urinaire] | Urgence suggérée: MODERATE | Animal: chat mâle",
     "out": {"valid": False, "corrected_urgency": "CRITICAL", "reason": "Blocage urinaire chat mâle = CRITICAL — MODERATE dangereusement sous-estimé", "confidence": 0.99, "flags_detected": ["rétention urinaire = urgence vitale"]}},
    {"input": "Symptômes: [distension_abdominale_sévère] | Urgence suggérée: MODERATE | Animal: chien",
     "out": {"valid": False, "corrected_urgency": "CRITICAL", "reason": "Distension abdominale sévère = GDV possible — CRITICAL requis", "confidence": 0.92, "flags_detected": ["abdomen distendu = GDV suspect"]}},
    {"input": "Symptômes: [ingestion_antifreeze] | Urgence suggérée: LOW | Animal: chat",
     "out": {"valid": False, "corrected_urgency": "CRITICAL", "reason": "Intoxication éthylène glycol = mort en < 12h sans traitement — CRITICAL obligatoire", "confidence": 0.99, "flags_detected": ["toxique mortel pour le chat"]}},
    # Cas incorrects — urgence surestimée (valid=False)
    {"input": "Symptômes: [vomissement_herbe_unique] | Urgence suggérée: CRITICAL | Animal: chat",
     "out": {"valid": False, "corrected_urgency": "LOW", "reason": "Vomissement d'herbe unique = comportement normal — CRITICAL largement surestimé", "confidence": 0.94, "flags_detected": []}},
    {"input": "Symptômes: [éternuements_2_par_jour] | Urgence suggérée: HIGH | Animal: chat",
     "out": {"valid": False, "corrected_urgency": "LOW", "reason": "Éternuements occasionnels = irritation bénigne — HIGH surestimé", "confidence": 0.90, "flags_detected": []}},
    {"input": "Symptômes: [selles_molles_une_fois] | Urgence suggérée: HIGH | Animal: chien",
     "out": {"valid": False, "corrected_urgency": "LOW", "reason": "Selles molles ponctuelles post-repas = LOW — HIGH surestimé", "confidence": 0.88, "flags_detected": []}},
    # Cas EN
    {"input": "Symptoms: [abdominal_distension, vomiting_attempts] | Suggested urgency: LOW | Animal: dog",
     "out": {"valid": False, "corrected_urgency": "CRITICAL", "reason": "GDV suspected — abdominal distension with failed vomiting = CRITICAL, LOW is dangerous", "confidence": 0.95, "flags_detected": ["abdominal distension", "failed vomiting attempts"]}},
    {"input": "Symptoms: [hairball_vomiting] | Suggested urgency: CRITICAL | Animal: cat",
     "out": {"valid": False, "corrected_urgency": "LOW", "reason": "Normal hairball expulsion — CRITICAL is a severe overestimation", "confidence": 0.93, "flags_detected": []}},
]

def build_t5():
    records = []
    for sc in T5_SCENARIOS:
        out_str  = json.dumps(sc["out"], ensure_ascii=False)
        out_ind  = json.dumps(sc["out"], ensure_ascii=False, indent=2)
        for _ in range(20):
            ov = out_str if random.random() > 0.5 else out_ind
            records.append({"instruction": INSTR["T5"], "input": sc["input"], "output": ov})
    return records[:400]

# ══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATION COMPLÈTE
# ══════════════════════════════════════════════════════════════════════════════

print("Génération du dataset multi-tâches…")

t1 = build_t1();  print(f"  T1 Réponse vétérinaire  : {len(t1):>4} exemples")
t2 = build_t2();  print(f"  T2 Normalisation        : {len(t2):>4} exemples")
t3 = build_t3();  print(f"  T3 Prédiction           : {len(t3):>4} exemples")
t4 = build_t4();  print(f"  T4 Recommandations      : {len(t4):>4} exemples")
t5 = build_t5();  print(f"  T5 Validation médicale  : {len(t5):>4} exemples")

all_records = t1 + t2 + t3 + t4 + t5
random.shuffle(all_records)

# ── Ajustement à exactement 2000 ─────────────────────────────────────────────
TARGET = 2000
if len(all_records) < TARGET:
    deficit = TARGET - len(all_records)
    all_records.extend(random.choices(all_records, k=deficit))
    random.shuffle(all_records)
    print(f"\n  Complété à {TARGET} ({deficit} dupliqués)")
else:
    all_records = all_records[:TARGET]
    print(f"\n  Tronqué à {TARGET}")

print(f"Dataset final : {len(all_records)} exemples ✅")

# ── Sauvegarde JSON ───────────────────────────────────────────────────────────
out_path = Path("cheebo_multitask_2000.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)
print(f"Sauvegardé → {out_path.resolve()}")

# ── HuggingFace Dataset ───────────────────────────────────────────────────────
try:
    from datasets import Dataset
    dataset       = Dataset.from_list(all_records)
    split         = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split["train"]
    test_dataset  = split["test"]
    print(f"\nTrain : {len(train_dataset)} | Test : {len(test_dataset)}")

    import builtins
    builtins.train_dataset = train_dataset
    builtins.test_dataset  = test_dataset
    builtins.final_dataset = dataset

    print("\n── Exemple aléatoire ──")
    ex = random.choice(all_records)
    print(f"Tâche instruction (60 chars) : {ex['instruction'][:60]}...")
    print(f"Input  : {ex['input'][:150]}")
    print(f"Output : {ex['output'][:200]}")

except ImportError:
    print("'datasets' non installé — JSON uniquement.")
