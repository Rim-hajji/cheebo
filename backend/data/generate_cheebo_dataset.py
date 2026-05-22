#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_cheebo_dataset.py
Génère 2000 exemples d'entraînement au format Alpaca pour Cheebo Vet AI.
Usage : python generate_cheebo_dataset.py
        ou coller dans une cellule Google Colab.
"""

import random, json
from datasets import Dataset

random.seed(42)

INSTRUCTION = "Génère une réponse vétérinaire empathique et professionnelle en français"

# ═══════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════

def build_input(level, animal, symptom, condition, care, red_flag):
    return (
        f"Niveau d'urgence : {level}\n"
        f"Animal : {animal}\n"
        f"Symptômes détectés : {symptom}\n"
        f"Conditions possibles : {condition}\n"
        f"Soins recommandés : {care}\n"
        f"Signes d'alarme : {red_flag}"
    )

def expand(scenario):
    """Produit input_variants × output_variants enregistrements."""
    level   = scenario["level"]
    animal  = scenario["animal"]
    records = []
    for sym, cond, care, flag in zip(
        scenario["symptoms"], scenario["conditions"],
        scenario["cares"],    scenario["flags"]
    ):
        inp = build_input(level, animal, sym, cond, care, flag)
        for out in scenario["outputs"]:
            records.append({
                "instruction": INSTRUCTION,
                "input":       inp,
                "output":      out,
            })
    return records

# ═══════════════════════════════════════════════════════════════════
# SCÉNARIOS CRITICAL  (10 scénarios × 5 inputs × 10 outputs = 500)
# ═══════════════════════════════════════════════════════════════════

CRITICAL = [

# ── 1. Torsion gastrique – chien ────────────────────────────────
{
"level":"CRITICAL","animal":"chien",
"symptoms":[
    "vomissement, abdomen gonflé, agitation, tentatives de vomissement sans résultat",
    "abdomen dilaté, tentatives de vomissement improductives, prostration soudaine",
    "ventre gonflé anormalement, agitation extrême, hypersalivation abondante",
    "distension abdominale rapide, vomissements improductifs, détresse intense",
    "gonflement abdominal soudain, refus de se coucher, hypersalivation",
],
"conditions":[
    "torsion gastrique (GDV), dilatation-volvulus",
    "syndrome dilatation-volvulus gastrique (GDV)",
    "torsion gastrique, urgence chirurgicale immédiate",
    "dilatation volvulus, torsion d'estomac",
    "GDV — Gastric Dilatation-Volvulus, risque vital",
],
"cares":[
    "urgence chirurgicale immédiate",
    "intervention chirurgicale d'urgence dans les 2h",
    "urgence vétérinaire — chirurgie immédiate requise",
    "transfert immédiat en clinique d'urgence",
    "urgence absolue — stabilisation puis chirurgie d'urgence",
],
"flags":[
    "gencives pâles ou bleues, effondrement, choc hypovolémique",
    "muqueuses bleutées, perte de conscience, choc",
    "gencives blanches, collapsus cardiovasculaire",
    "teint des gencives gris ou blanc, effondrement soudain",
    "cyanose des muqueuses, défaillance multi-organes",
],
"outputs":[
"""🚨 **Situation critique — Agissez immédiatement**

Je comprends à quel point cette situation est angoissante. Les symptômes que vous décrivez sont caractéristiques d'une **torsion gastrique (GDV)** — une urgence vitale qui engage le pronostic de vie de votre chien.

**Actions immédiates :**
• Rendez-vous aux urgences vétérinaires MAINTENANT
• Ne donnez rien à manger ni à boire
• Gardez votre chien calme et allongé sur le côté
• Ne massez pas l'abdomen

**Signes d'alarme en route :**
• Gencives pâles, grises ou bleutées → signe de choc grave
• Effondrement soudain → appelez le vétérinaire depuis le véhicule

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence vitale — Ne perdez pas une seconde**

Cette situation m'inquiète beaucoup. Un abdomen qui gonfle rapidement avec des tentatives de vomissement sans résultat est le **signe classique d'une torsion gastrique**. Sans intervention chirurgicale rapide, le pronostic est très sombre.

**Ce que vous devez faire maintenant :**
• Allez aux urgences vétérinaires immédiatement — n'attendez pas
• Appelez la clinique en route pour les prévenir
• Évitez tout stress ou mouvement brusque pour votre chien
• Ne lui donnez aucun aliment ou médicament

**Surveiller en route :**
• La couleur des gencives (normales = rose vif)
• L'état de conscience de votre chien

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Torsion gastrique suspectée — Urgence chirurgicale**

Je comprends votre panique et vous avez raison de vous inquiéter. Les symptômes correspondent à une **GDV (Gastric Dilatation-Volvulus)**, une torsion de l'estomac qui nécessite une chirurgie dans les prochaines heures.

**Actions à effectuer immédiatement :**
• Dirigez-vous vers la clinique vétérinaire d'urgence la plus proche
• Prévenez-les par téléphone de votre arrivée
• Gardez votre chien immobile et au calme
• Aucune nourriture, aucune eau, aucun médicament

**Signal d'alarme absolu :**
• Gencives bleutées ou blanches = choc en cours → roulez vite

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Danger immédiat — Torsion gastrique**

Ce que vous décrivez — abdomen gonflé, vomissements improductifs, agitation — ressemble fortement à une **torsion gastrique**, l'une des urgences les plus graves en médecine vétérinaire. Votre chien a besoin d'une intervention chirurgicale d'urgence.

**Faites ceci maintenant :**
• Rendez-vous IMMÉDIATEMENT aux urgences vétérinaires
• Portez votre chien si possible plutôt que de le laisser marcher
• Appelez la clinique pour qu'elle prépare son équipe
• Ne donnez rien par la bouche

**Signes de détérioration rapide :**
• Effondrement ou faiblesse extrême
• Muqueuses qui changent de couleur (pâles/bleues)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **GDV — Chaque minute est précieuse**

Votre instinct est bon — cette situation est très grave. La combinaison gonflement abdominal, agitation et vomissements sans résultat est l'image typique de la **torsion gastrique**. C'est une urgence chirurgicale absolue.

**Protocole d'urgence :**
• Urgences vétérinaires MAINTENANT — ne différez pas
• Appelez en partant pour qu'ils se préparent
• Minimisez les mouvements de votre chien
• Aucune nourriture, aucun liquide, aucun médicament maison

**Points de vigilance pendant le trajet :**
• Gencives pâles ou bleues = choc installé
• Respiration rapide et superficielle = aggravation

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Alerte maximale — Torsion gastrique**

Vous avez raison d'être alarmé : les symptômes correspondent à une **urgence chirurgicale** — la torsion de l'estomac (GDV) est fatale sans intervention rapide.

**Ce que vous devez faire maintenant :**
• Urgences vétérinaires — sans délai
• Restez calme pour ne pas stresser davantage votre chien
• Étendez-le doucement sur le côté droit si possible
• Ne tentez aucun remède maison

**En route, surveillez :**
• La respiration (doit être régulière)
• La couleur des gencives (doivent rester roses)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Torsion d'estomac — Risque vital immédiat**

Un abdomen qui gonfle de façon visible avec des tentatives de vomissement infructueuses sont des signes quasi-certains de **torsion gastrique**. Sans chirurgie rapide, les chances de survie chutent drastiquement.

**Protocole immédiat :**
• Clinique vétérinaire d'urgence — maintenant
• Appelez pendant le trajet pour préparer l'équipe chirurgicale
• Gardez votre chien couché et immobile
• Zéro alimentation, zéro liquide, zéro médicament

**Critères d'aggravation :**
• Gencives qui pâlissent ou bleuissent
• Chien qui ne peut plus se lever seul

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Situation critique confirmée**

La distension abdominale associée aux vomissements improductifs évoque fortement une **dilatation-volvulus gastrique (GDV)**. Cette condition nécessite une chirurgie dans les 2 heures pour avoir une chance de survie.

**Actions immédiates requises :**
• Partez aux urgences vétérinaires IMMÉDIATEMENT
• Prévenez la clinique de votre arrivée imminente
• Ne donnez rien à votre chien par la bouche
• Minimisez ses efforts physiques pendant le transport

**Signaux d'alerte critiques :**
• Gencives blanches ou bleues → choc en cours
• Perte de connaissance → situation extrêmement grave

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence chirurgicale — GDV confirmée**

Ce que vous décrivez — gonflement rapide du ventre, agitation, incapacité à vomir malgré les efforts — sont les trois signes cardinaux de la **torsion gastrique**, une urgence qui peut être fatale en quelques heures.

**Ce qu'il faut faire :**
• Partez immédiatement aux urgences vétérinaires
• Téléphonez en route pour qu'ils soient prêts à votre arrivée
• Maintenez votre chien au calme, limitez ses mouvements
• N'essayez pas de le faire vomir

**Surveillance pendant le transport :**
• Couleur des gencives (rose = bien, pâle/bleue = choc)
• Niveau de conscience

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Danger vital — Agissez sans délai**

La distension abdominale rapide associée à des tentatives de vomissement infructueuses et à de l'agitation est le tableau clinique classique d'une **torsion gastrique (GDV)**. C'est une urgence chirurgicale qui n'attend pas.

**Protocole d'urgence :**
• Urgences vétérinaires — immédiatement
• Appelez pendant le trajet pour prévenir l'équipe
• Portez votre chien si sa taille le permet
• Aucune nourriture, aucune eau, aucun traitement maison

**En surveillant attentivement :**
• Gencives : doivent rester roses et humides
• Respiration : doit rester régulière

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 2. Obstruction urinaire – chat mâle ─────────────────────────
{
"level":"CRITICAL","animal":"chat",
"symptoms":[
    "tentatives d'uriner sans résultat, cris de douleur, abdomen tendu",
    "position d'uriner répétée mais rien ne sort, vocalises, abdomen douloureux",
    "incapacité à uriner, agitation, léchage intense de la zone génitale",
    "anurie complète depuis 12h, vomissements, prostration",
    "blocage urinaire, cris en tentant d'uriner, ventre dur au toucher",
],
"conditions":[
    "obstruction urinaire complète — urgence absolue",
    "blocage urétral, calculs vésicaux ou bouchon muqueux",
    "urétrostase complète, risque d'hyperkaliémie et arrêt cardiaque",
    "obstruction des voies urinaires basses, risque rénal aigu",
    "syndrome d'obstruction urétrale féline (FLUTD sévère)",
],
"cares":[
    "urgence vétérinaire immédiate — sondage urinaire nécessaire",
    "consultation d'urgence dans l'heure — sondage et hospitalisation",
    "urgence absolue — déblocage sous anesthésie requis",
    "intervention vétérinaire immédiate — perfusion et sondage",
    "urgence vitale — sans sondage sous 2h risque de mort",
],
"flags":[
    "gencives pâles, vomissements répétés, arrêt cardiaque possible",
    "hyperkaliémie → arythmie cardiaque, perte de conscience",
    "léthargie extrême, corps froid, choc",
    "absence totale d'urine >12h → insuffisance rénale aiguë",
    "convulsions, collapsus → stade terminal",
],
"outputs":[
"""🚨 **Obstruction urinaire — Urgence vitale**

Je comprends votre inquiétude et elle est totalement justifiée. Un chat mâle qui ne peut pas uriner est en danger de mort. Le blocage de l'urètre entraîne une accumulation de toxines dans le sang qui peut provoquer un **arrêt cardiaque en quelques heures**.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT — chaque heure compte
• Ne massez pas l'abdomen
• Ne lui donnez aucun médicament
• Gardez-le au calme pendant le transport

**Signes d'aggravation en route :**
• Vomissements répétés
• Gencives pâles ou bleutées
• Perte de connaissance → situation extrêmement grave

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Blocage urétral — Urgence absolue**

Ce que vous décrivez est l'une des urgences les plus graves chez le chat. Un chat mâle qui ne peut pas uriner risque de mourir d'**hyperkaliémie** (excès de potassium) provoquant un arrêt du cœur.

**Ce que vous devez faire maintenant :**
• Partez aux urgences vétérinaires IMMÉDIATEMENT
• Appelez pour les prévenir de votre arrivée
• Ne tentez pas de lui faire boire plus d'eau
• Ne lui donnez aucun antidouleur maison

**Critères d'urgence extrême :**
• Anurie depuis >12h → toxicité rénale grave
• Corps qui se refroidit → choc installé

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urétrostase — Danger immédiat**

Cette situation est une urgence vétérinaire absolue. L'impossibilité d'uriner chez un chat mâle provoque une accumulation de toxines qui **peut être fatale en moins de 24 heures** sans sondage vétérinaire.

**Actions immédiates :**
• Clinique vétérinaire d'urgence — sans délai
• Signalez immédiatement "chat mâle qui ne peut pas uriner"
• Ne lui donnez rien par la bouche
• Transportez-le dans une caisse fermée pour le calmer

**Signaux de gravité extrême :**
• Vomissements répétés = toxines dans le sang
• Gencives pâles = choc en cours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Blocage urinaire — Risque de mort imminent**

Je comprends votre détresse. Cette situation est une urgence absolue. Le blocage urinaire complet chez un chat mâle provoque une **intoxication interne rapide** par accumulation d'urée et de potassium.

**Protocole d'urgence :**
• Urgences vétérinaires — maintenant, pas dans une heure
• Dites-leur "chat mâle en obstruction urinaire complète"
• Gardez-le au chaud pendant le transport
• Pas de médicaments, pas de massage abdominal

**En route, observez :**
• Respiration (doit rester régulière)
• État de conscience (doit rester éveillé)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Obstruction féline — Toutes les minutes comptent**

Un chat mâle incapable d'uriner est en danger de mort. L'accumulation d'urine dans la vessie et les toxines dans le sang peuvent provoquer un **arrêt cardiaque par hyperkaliémie** dans les prochaines heures.

**Actions vitales :**
• Urgences vétérinaires IMMÉDIATEMENT
• Signalez la situation par téléphone pendant le trajet
• Ne tentez pas de pression sur l'abdomen
• Zéro médicament, zéro traitement maison

**Signes que la situation empire :**
• Vomissements = intoxication en cours
• Froid aux pattes = choc circulatoire

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence — Blocage urétral complet**

Ce que vous décrivez nécessite une intervention vétérinaire immédiate. Sans sondage urinaire rapide, votre chat risque de mourir d'**insuffisance rénale aiguë et d'arythmie cardiaque** causées par l'accumulation de potassium.

**Faites ceci sans attendre :**
• Urgences vétérinaires — maintenant
• Expliquez "mon chat ne peut pas uriner depuis plusieurs heures"
• Évitez tout stress supplémentaire pendant le transport
• Ne lui donnez aucun aliment ni liquide supplémentaire

**Signes très graves à surveiller :**
• Prostration totale = toxémie avancée
• Convulsions = stade terminal

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Rétention urinaire féline — Urgence chirurgicale**

Je vous comprends et votre alarme est justifiée. Le blocage des voies urinaires est une urgence létale chez le chat mâle. **Sans intervention sous 2 à 4 heures**, les risques de décès sont très élevés.

**Ce qu'il faut faire :**
• Clinique vétérinaire d'urgence — immédiatement
• Appelez pour qu'ils anticipent votre arrivée
• Transportez-le dans sa caisse habituelle
• Aucun médicament, même antidouleur

**Pendant le transport, vérifiez :**
• Qu'il reste conscient et réactif
• Que sa respiration reste régulière

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Blocage urinaire — Situation critique**

Cette situation ne peut pas attendre. Un chat mâle en obstruction urinaire complète développe une **hyperkaliémie mortelle** qui peut arrêter le cœur en quelques heures.

**Actions immédiates requises :**
• Partez aux urgences vétérinaires MAINTENANT
• Signalez par téléphone "chat mâle — anurie complète"
• Gardez-le immobile et au calme
• Pas de massage, pas de médicament

**Critères d'aggravation :**
• Vomissements fréquents = toxines accumulées
• Corps qui se refroidit = choc en cours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Anurie féline — Danger de mort**

Je comprends votre panique. Ce que vous décrivez est une urgence absolue. Le blocage urinaire chez le chat mâle est **fatal sans sondage vétérinaire rapide** — les toxines s'accumulent dans le sang et provoquent une défaillance cardiaque.

**Ce qu'il faut faire immédiatement :**
• Urgences vétérinaires — sans délai aucun
• Informez-les par téléphone en route
• Ne tentez pas de lui faire uriner par pression
• Transport calme dans une caisse fermée

**Surveillance pendant le trajet :**
• Conscience : doit rester éveillé
• Respiration : doit rester stable

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Obstruction urinaire totale — Agissez immédiatement**

Votre instinct est correct — c'est une urgence. Un chat mâle qui tente d'uriner sans y parvenir souffre d'un **blocage urétral** qui peut entraîner la mort par arrêt cardiaque en quelques heures.

**Protocole d'urgence :**
• Clinique vétérinaire d'urgence MAINTENANT
• Appelez pour qu'ils préparent le matériel de sondage
• Gardez votre chat dans une caisse stable pendant le trajet
• Aucune intervention maison

**En route :**
• Gencives roses = encore stable
• Gencives pâles/bleues = choc → accélérez

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 3. Intoxication au chocolat – chien ─────────────────────────
{
"level":"CRITICAL","animal":"chien",
"symptoms":[
    "ingestion chocolat noir 100g, agitation, vomissements",
    "a mangé du chocolat noir, tremblements, hyperactivité",
    "ingestion chocolat pâtissier 80g, hypersalivation, agitation",
    "consommation chocolat 150g, vomissements, tachycardie",
    "ingestion cacao pur, diarrhée, tremblements musculaires",
],
"conditions":[
    "intoxication à la théobromine, toxique pour les chiens",
    "empoisonnement au chocolat, théobromine = cardiotoxique et neurotoxique",
    "intoxication théobromine/caféine, risque de convulsions",
    "toxicose au chocolat, dose potentiellement létale selon le poids",
    "empoisonnement au cacao, action stimulante sur le système nerveux",
],
"cares":[
    "urgence vétérinaire immédiate — induction du vomissement possible sous 2h",
    "consultation d'urgence — charbon activé et surveillance cardiaque",
    "urgence vétérinaire — décontamination gastrique si ingestion récente",
    "intervention immédiate — calcul de dose toxique selon le poids",
    "urgence absolue — hospitalisation et monitoring cardiaque requis",
],
"flags":[
    "tremblements, convulsions, arythmie cardiaque",
    "hyperthermie, tachycardie, crises convulsives",
    "raideur musculaire, épilepsie, arrêt cardiaque",
    "agitation extrême, dilatation pupilles, convulsions",
    "coma, défaillance cardiaque, mort subite",
],
"outputs":[
"""🚨 **Intoxication au chocolat — Urgence immédiate**

Cette situation est sérieuse. Le chocolat noir contient de la **théobromine**, une substance très toxique pour les chiens. La dose ingérée peut être dangereuse selon le poids de votre chien.

**Actions immédiates :**
• Appelez un vétérinaire d'urgence MAINTENANT
• Notez l'heure exacte d'ingestion et le poids de votre chien
• Conservez l'emballage du chocolat (% cacao)
• Ne tentez PAS de faire vomir sans avis vétérinaire

**Signes d'intoxication à surveiller :**
• Tremblements ou rigidité musculaire
• Convulsions — signe très grave
• Rythme cardiaque rapide ou irrégulier

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Empoisonnement au chocolat — Agissez maintenant**

Je comprends votre inquiétude — elle est tout à fait justifiée. La **théobromine** du chocolat noir est un poison puissant pour les chiens, agissant sur le cœur et le système nerveux.

**Ce que vous devez faire immédiatement :**
• Contactez un vétérinaire d'urgence — indiquez le poids du chien et la quantité ingérée
• Si l'ingestion date de moins de 2h, le vétérinaire peut induire le vomissement
• Gardez l'emballage du chocolat
• Ne donnez ni lait ni eau en grande quantité

**Signes d'urgence absolue :**
• Convulsions → appelez le 15 vétérinaire en roulant
• Perte de conscience → transport immédiat

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Toxicose au chocolat — Danger confirmé**

Le chocolat noir et le cacao sont **très toxiques pour les chiens** — la théobromine perturbe le rythme cardiaque et le système nerveux. La quantité ingérée peut être critique selon le poids de votre animal.

**Actions à effectuer immédiatement :**
• Urgences vétérinaires — maintenant
• Informez-les du poids du chien, de la quantité et du % de cacao
• Si <2h depuis l'ingestion, le vétérinaire peut provoquer le vomissement
• Ne tentez pas de faire vomir seul (risque d'aspiration)

**Symptômes qui indiquent une aggravation :**
• Tremblements incontrôlables
• Rythme cardiaque rapide ou irrégulier
• Crises convulsives

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Intoxication — Consultez un vétérinaire d'urgence**

Je comprends votre panique. L'ingestion de chocolat noir est une **urgence vétérinaire réelle** chez le chien. La théobromine est métabolisée lentement par les chiens, prolongeant l'intoxication.

**Faites ceci maintenant :**
• Appelez immédiatement un vétérinaire ou une ligne d'urgence vétérinaire
• Donnez ces informations : poids du chien, quantité de chocolat, heure d'ingestion, % cacao
• Ne donnez aucun aliment ou remède maison
• Surveillez l'apparition de tremblements ou d'agitation

**Signaux d'alarme :**
• Convulsions → urgence vitale absolue
• Arythmie cardiaque visible (pouls rapide et irrégulier)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Chocolat ingéré — Urgence toxicologique**

Cette situation nécessite une action immédiate. Le chocolat, et surtout le chocolat noir ou pâtissier, contient des concentrations élevées de **théobromine et de caféine**, toutes deux toxiques pour le chien.

**Protocole immédiat :**
• Urgences vétérinaires MAINTENANT
• Apportez l'emballage du chocolat (taux de cacao crucial)
• Notez l'heure précise de l'ingestion
• Pas d'eau en grande quantité, pas de lait, pas de vomissement forcé

**Symptômes critiques à surveiller :**
• Tremblements → toxicité neurologique
• Convulsions → urgence absolue
• Pouls très rapide → toxicité cardiaque

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Poisoning chocolat — Ne tardez pas**

Votre réactivité est essentielle. La **théobromine** du chocolat noir agit comme un stimulant cardiaque et nerveux chez le chien — la dose ingérée peut dépasser le seuil toxique selon le poids de votre animal.

**Actions immédiates :**
• Contactez les urgences vétérinaires sans attendre
• Calculez : poids du chien + grammes ingérés = information vitale pour le vétérinaire
• Ne provoquez pas le vomissement sans instruction médicale
• Gardez votre chien au calme et sous surveillance

**Seuils d'alarme :**
• Tremblements = toxicité neurologique installée
• Convulsions = urgence absolue → clinique immédiate
• Pouls > 150/min = toxicité cardiaque

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Intoxication théobromine — Situation grave**

Je comprends l'urgence. Le chocolat noir est l'un des poisons les plus fréquents chez le chien. La **théobromine** qu'il contient est cardiotoxique et neurotoxique — les symptômes peuvent s'aggraver sur 6 à 12 heures.

**Ce que vous devez faire :**
• Urgences vétérinaires IMMÉDIATEMENT
• Informez le vétérinaire : poids, quantité de chocolat, % cacao, heure d'ingestion
• Si l'ingestion est récente (<2h), une décontamination gastrique est possible
• Ne donnez rien d'autre par la bouche

**Surveillance étroite :**
• Tremblements musculaires = signe de toxicité neurologique
• Convulsions = urgence vitale
• Hyperthermie (animal très chaud) = agravation

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Toxicité au cacao — Intervention urgente requise**

Vous avez bien fait de réagir rapidement. L'ingestion de chocolat ou de cacao est une **urgence vétérinaire** — la théobromine peut provoquer des convulsions et des arythmies cardiaques en quelques heures.

**Actions à prendre immédiatement :**
• Appelez un vétérinaire d'urgence maintenant
• Mentionnez : poids du chien, quantité ingérée, type de chocolat, heure
• N'induisez pas le vomissement seul
• Ne donnez aucun médicament humain

**Signes d'aggravation :**
• Agitation croissante → toxicité en hausse
• Tremblements → intervention urgente
• Perte de connaissance → urgence absolue

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Empoisonnement au chocolat — Danger pour votre chien**

Je comprends votre alarme. Le chocolat noir contient des concentrations élevées de **théobromine** — une molécule que les chiens éliminent beaucoup plus lentement que les humains, entraînant une accumulation toxique.

**Protocole d'urgence :**
• Clinique vétérinaire d'urgence — immédiatement
• Emportez l'emballage ou notez le % de cacao
• Pesez ou estimez le poids de votre chien
• Aucun traitement maison

**Points de surveillance :**
• Tremblements ou rigidité = toxicité neurologique
• Rythme cardiaque rapide et irrégulier = toxicité cardiaque
• Convulsions = urgence absolue

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Ingestion de chocolat — Urgence confirmée**

Cette situation mérite une action immédiate. La **théobromine** et la caféine présentes dans le chocolat noir sont des stimulants cardiaques et nerveux que les chiens ne peuvent pas éliminer efficacement.

**Faites ceci maintenant :**
• Urgences vétérinaires MAINTENANT
• Information clé à donner : poids du chien + grammes ingérés + % cacao
• Si < 2h depuis l'ingestion : le vétérinaire peut induire le vomissement
• Maintenez votre chien calme et sous surveillance constante

**Évolution possible sans traitement :**
• 1-2h : agitation, hypersalivation
• 3-6h : tremblements, tachycardie
• 6-12h : convulsions, arythmie → urgence vitale

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 4. Détresse respiratoire sévère – chien ─────────────────────
{
"level":"CRITICAL","animal":"chien",
"symptoms":[
    "difficultés respiratoires sévères, bouche ouverte au repos, halètement excessif",
    "respiration laborieuse, gencives bleutées, incapacité à se coucher",
    "orthopnée, respiration abdominale, cyanose légère des muqueuses",
    "dyspnée sévère, nuque tendue, respiration sifflante",
    "détresse respiratoire, mouvements respiratoires exagérés, panique",
],
"conditions":[
    "épanchement pleural, pneumonie sévère, œdème pulmonaire",
    "insuffisance cardiaque congestive, épanchement pleural",
    "trachéite obstructive, corps étranger dans les voies respiratoires",
    "coup de chaleur avec atteinte pulmonaire, BPCO sévère",
    "hernie diaphragmatique traumatique, pneumothorax",
],
"cares":[
    "urgence vétérinaire immédiate — oxygénothérapie requise",
    "consultation d'urgence — ponction pleurale possible",
    "transport d'urgence — chien doit rester en position assise",
    "urgence respiratoire — ne pas allonger l'animal",
    "clinique d'urgence — monitoring respiratoire et cardiaque",
],
"flags":[
    "gencives bleues ou blanches, perte de conscience",
    "cyanose complète, effondrement, arrêt respiratoire",
    "muqueuses grises, choc anoxique",
    "respiration agonique, perte de connaissance",
    "silence respiratoire, collapsus",
],
"outputs":[
"""🚨 **Détresse respiratoire — Urgence vitale**

Cette situation est extrêmement grave. Des difficultés respiratoires au repos chez un chien indiquent une **urgence vitale** qui nécessite une intervention immédiate. Sans oxygène suffisant, les organes vitaux sont en danger.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT — ne perdez pas une seconde
• Gardez votre chien en position assise ou debout — ne l'allongez pas
• Maintenez-le dans un endroit frais et aéré
• Évitez tout effort ou stress pendant le transport

**Signe critique absolu :**
• Gencives bleues ou blanches → appelez le vétérinaire depuis le véhicule en roulant

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Insuffisance respiratoire — Agissez immédiatement**

Je comprends votre panique — cette situation est une urgence absolue. Un chien qui respire avec difficulté au repos, la gueule ouverte, est en **détresse respiratoire sévère** et risque l'arrêt respiratoire.

**Ce que vous devez faire maintenant :**
• Partez aux urgences vétérinaires IMMÉDIATEMENT
• Ne l'allongez pas — gardez-le en position naturelle (assis ou debout)
• Ouvrez les fenêtres du véhicule pour l'aération
• Appelez la clinique pour qu'ils préparent l'oxygène

**Signaux de détérioration critique :**
• Gencives qui bleuissent → urgence absolue
• Effondrement ou perte de conscience → roulez vite

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Dyspnée sévère — Urgence respiratoire**

Ce que vous décrivez m'inquiète énormément. Une respiration laborieuse avec gencives bleutées est un signe de **manque d'oxygène grave** — les organes vitaux ne reçoivent pas assez d'oxygène.

**Actions immédiates :**
• Clinique vétérinaire d'urgence — maintenant
• Position assise ou debout — ne jamais allonger un chien en détresse respiratoire
• Environnement frais et calme pendant le transport
• Appelez en route pour préparer l'équipe d'urgence

**Critères d'alarme :**
• Gencives grises ou blanches = hypoxie sévère
• Silence respiratoire soudain = arrêt respiratoire → massage cardiaque si formé

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence — Détresse respiratoire confirmée**

Votre instinct d'urgence est justifié. Les signes que vous décrivez — respiration difficile, bouche ouverte, halètement au repos — indiquent que votre chien n'arrive pas à oxygéner suffisamment son organisme. C'est une **urgence vitale**.

**Faites ceci maintenant :**
• Urgences vétérinaires IMMÉDIATEMENT
• Ne stressez pas votre chien — restez calme
• Position assise maintenue pendant le transport
• Fenêtres ouvertes pour l'aération maximale

**En route — signes critiques :**
• Gencives bleues → roulez aussi vite que possible en sécurité
• Chien qui s'effondre → portez-le directement dans la clinique

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Crise respiratoire — Toutes les secondes comptent**

Je comprends votre alarme et elle est parfaitement justifiée. Un chien en détresse respiratoire peut passer d'une situation difficile à un **arrêt respiratoire** très rapidement. Chaque minute compte.

**Protocole d'urgence :**
• Urgences vétérinaires — sans délai
• Gardez-le assis ou debout — allongé, il suffoque encore plus
• Minimisez son stress — parlez-lui calmement
• Appelez la clinique depuis le véhicule

**Surveiller absolument :**
• Couleur des gencives : roses = stable, bleues = critique
• Niveau de conscience : doit rester éveillé

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Détresse respiratoire grave — Intervention urgente**

Cette situation ne supporte aucun délai. Un chien qui respire la gueule ouverte au repos est en **hypoxie** — manque d'oxygène grave. L'épanchement pleural ou l'insuffisance cardiaque sont des causes fréquentes.

**Actions vitales :**
• Urgences vétérinaires MAINTENANT
• Position : assis ou debout, jamais allongé sur le côté
• Fenêtres du véhicule ouvertes
• Appelez pour signaler la détresse respiratoire

**Signaux d'aggravation :**
• Gencives grises ou bleues → accélérez
• Respiration agonique → arrêt imminent

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Oxygénation insuffisante — Urgence absolue**

Je comprends votre détresse. Ce que vous décrivez est une **urgence vétérinaire de premier degré**. La détresse respiratoire peut évoluer vers un arrêt cardiorespiratoire en quelques minutes.

**Ce qu'il faut faire :**
• Urgences vétérinaires IMMÉDIATEMENT
• Ne contraignez pas votre chien — laissez-le trouver sa position de confort
• Aération maximale pendant le transport
• Signalez "chien en détresse respiratoire" en arrivant

**Pendant le transport :**
• Gencives roses = encore stable
• Gencives bleues ou grises = situation critique imminente

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Pneumothorax ou épanchement — Urgence respiratoire**

Votre réactivité peut sauver la vie de votre chien. La détresse respiratoire que vous décrivez peut être causée par de l'eau autour des poumons (épanchement pleural) ou une insuffisance cardiaque — les deux nécessitent une **intervention vétérinaire immédiate**.

**Actions immédiates :**
• Clinique d'urgence — maintenant
• Position assise pendant tout le trajet
• Pas d'effort, pas de stress
• Appelez pour qu'ils préparent l'oxygène et le matériel de ponction

**Signaux critiques en route :**
• Gencives bleues → accélérez prudemment
• Effondrement → entrez directement dans la clinique

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Insuffisance respiratoire sévère — Danger immédiat**

Cette situation m'inquiète énormément. Un chien qui respire avec effort au repos, avec des muqueuses bleutées, est en train de **manquer d'oxygène** — ses organes vitaux sont en danger.

**Protocole immédiat :**
• Urgences vétérinaires — sans attendre
• Maintenez une position assise ou debout
• Environnement frais, calme, aéré
• Signalez la cyanose (gencives bleues) à votre arrivée

**Évolution sans traitement :**
• Minutes : aggravation de la cyanose
• 10-20 min : perte de connaissance
• 30 min : arrêt cardiorespiratoire

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Crise respiratoire canine — Urgence vitale**

Je comprends votre panique. Des difficultés à respirer au repos avec la gueule ouverte chez un chien est un **signal d'alarme de premier ordre**. Sans apport d'oxygène médical rapide, la situation peut évoluer vers un arrêt cardiorespiratoire.

**Ce que vous devez faire :**
• Urgences vétérinaires IMMÉDIATEMENT — appelez en partant
• Position assise ou debout pendant tout le trajet
• Évitez l'effort physique et le stress
• Fenêtres ouvertes pour maximiser l'oxygène ambiant

**Signal d'arrêt :**
• Gencives bleues ou grises → urgence maximale
• Chien inconscient → portez-le directement au service d'urgence

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 5. Coup de chaleur – chien ───────────────────────────────────
{
"level":"CRITICAL","animal":"chien",
"symptoms":[
    "halètement excessif, hyperthermie, gencives rouges, prostration après exposition à la chaleur",
    "corps brûlant au toucher, confusion, salivation excessive, après enfermement en voiture",
    "température >41°C, vomissements, désorientation, exposition soleil intense",
    "halètement intense, faiblesse soudaine, yeux injectés, après exercice intense par temps chaud",
    "hyperthermie extrême, convulsions, perte d'équilibre, coup de chaleur",
],
"conditions":[
    "coup de chaleur (hyperthermie) — urgence vitale",
    "hyperthermie grave, risque de défaillance multi-organes",
    "coup de chaleur classique ou d'exercice, température critique",
    "thermorégulation défaillante, risque de CIVD et choc",
    "hyperthermie maligne, atteinte cérébrale et rénale imminente",
],
"cares":[
    "refroidissement immédiat + urgence vétérinaire",
    "refroidissement actif + transport d'urgence immédiat",
    "urgence absolue — refroidissement puis clinique immédiatement",
    "refroidissement progressif + perfusion intraveineuse urgente",
    "intervention immédiate — hypothermie contrôlée en clinique",
],
"flags":[
    "convulsions, diarrhée sanglante, coma — défaillance multi-organes",
    "perte de conscience, gencives grises, CIVD",
    "saignement spontané, anurie, coma",
    "choc hémorragique, insuffisance rénale aiguë",
    "arrêt cardiorespiratoire, œdème cérébral",
],
"outputs":[
"""🚨 **Coup de chaleur — Urgence vitale immédiate**

Je comprends votre panique — et vous avez raison d'agir maintenant. Le coup de chaleur peut tuer un chien en quelques dizaines de minutes. **Chaque seconde compte**.

**Actions immédiates (en parallèle) :**
• Appelez les urgences vétérinaires pendant que vous refroidissez votre chien
• Refroidissement IMMÉDIAT : eau froide (pas glacée) sur le corps, ventilateur
• Enlevez-le de la source de chaleur — endroit frais et aéré
• Proposez de l'eau fraîche à boire s'il est conscient

**Ce qu'il ne faut PAS faire :**
• Ne couvrez pas votre chien
• N'utilisez pas d'eau glacée (choc thermique)
• Ne forçez pas l'eau s'il ne peut pas avaler

**Signes de gravité extrême :**
• Convulsions ou coma → urgence absolue

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Hyperthermie canine — Agissez maintenant**

Cette situation est une urgence vitale. Un chien dont la température corporelle dépasse 41°C risque des **lésions cérébrales et une défaillance multi-organes** irréversibles en quelques minutes.

**Protocole d'urgence en deux temps :**

**1. Refroidissement immédiat :**
• Eau fraîche (pas glacée) sur tout le corps
• Ventilateur ou air conditionné
• Pattes dans l'eau froide

**2. Transport d'urgence :**
• Clinique vétérinaire — maintenant, pendant le refroidissement
• Appelez pour qu'ils préparent perfusion et monitoring

**Ne jamais :**
• Couvrir l'animal
• Utiliser de l'eau glacée

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Coup de chaleur — Danger de mort imminent**

Ce que vous décrivez est une **urgence absolue**. L'hyperthermie chez le chien détruit les protéines cérébrales et provoque une cascade de défaillances organiques — cœur, reins, foie, cerveau.

**Faites ces deux choses simultanément :**
• Appelez les urgences vétérinaires MAINTENANT
• Refroidissez votre chien : eau froide sur la nuque, les aisselles, l'aine

**Pendant le transport :**
• Fenêtres ouvertes ou climatisation à fond
• Eau fraîche sur le corps en continu
• Ne l'enveloppez pas dans une serviette humide chaude

**Signal critique :**
• Convulsions ou inconscience → transport immédiat sans délai supplémentaire

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Hyperthermie maligne — Refroidissez et foncez**

Votre réactivité peut sauver la vie de votre chien. Le coup de chaleur est l'une des urgences vétérinaires les plus rapidement mortelles — les **lésions organiques** commencent dès 41°C.

**Actions immédiates :**
• Sortez-le de la source de chaleur MAINTENANT
• Eau fraîche (pas glacée) sur tout le corps — pattes, ventre, nuque
• Appelez les urgences vétérinaires pendant le refroidissement
• Transport vers la clinique dès que possible

**À éviter absolument :**
• Eau glacée ou glace directe → choc thermique
• Serviette chaude autour du corps
• Forcer l'eau s'il est inconscient

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Coup de chaleur — Urgence maximale**

Je vous entends. Cette situation est une **urgence vitale de premier degré**. Sans refroidissement immédiat et prise en charge vétérinaire, le pronostic vital est très sombre.

**Protocole en parallèle :**
• Refroidissement : eau fraîche sur nuque, aisselles, aine + ventilateur
• Appel : urgences vétérinaires PENDANT le refroidissement
• Transport : dès les premières minutes de refroidissement

**Ce qui peut tuer en quelques minutes :**
• Température > 43°C → lésions cérébrales irréversibles
• Convulsions → défaillance neurologique

**Ne pas :**
• Attendre que la température baisse seule
• Utiliser de la glace pilée

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Thermorégulation défaillante — Agissez en urgence**

Je comprends votre alarme. Un chien exposé à la chaleur avec ces symptômes est en **danger de mort immédiat**. Le coup de chaleur peut tuer en moins de 30 minutes sans intervention.

**Étapes simultanées :**
1. Eau fraîche sur tout le corps (pas glacée)
2. Appel aux urgences vétérinaires
3. Transport immédiat

**Points essentiels :**
• Évitez le soleil direct pendant le transport
• Climatisation à fond dans le véhicule
• Ne couvrez pas l'animal

**Signes terminaux :**
• Coma → urgence vitale absolue
• Saignement spontané → choc hémorragique

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Hyperthermie grave — Intervention immédiate**

Vous avez raison d'agir immédiatement. Un coup de chaleur non traité dans les premières minutes peut entraîner des **lésions irréversibles** au cerveau, aux reins et au foie.

**Refroidissement d'urgence :**
• Eau fraîche (pas glacée) sur pattes, ventre, nuque, aisselles
• Ventilateur ou air conditionné
• Endroit ombragé et aéré

**Transport d'urgence :**
• Clinique vétérinaire MAINTENANT — appelez en route
• Continuez le refroidissement pendant le transport

**Signes que la situation empire :**
• Convulsions → urgence absolue
• Corps qui ne se refroidit pas → intoxication thermique avancée

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Coup de chaleur confirmé — Toutes les minutes comptent**

Cette situation est grave. Les organes de votre chien sont en train de souffrir de la chaleur excessive. **Chaque minute sans refroidissement augmente les dommages irréversibles**.

**Protocole d'urgence :**
• Eau froide (pas glacée) sur tout le corps immédiatement
• Urgences vétérinaires — appelez en commençant le refroidissement
• Placez-le dans un endroit frais et aéré
• Transport dès que possible

**Ne faites pas :**
• Glace directe sur la peau (vasoconstriction → contre-productive)
• Attendre que ça passe seul
• Le forcer à avaler s'il est somnolent

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Hyperthermie canine — Danger de défaillance multi-organes**

Je comprends votre détresse. Le coup de chaleur provoque une réaction en chaîne : cerveau, reins, foie, cœur — tous les organes sont touchés simultanément. **L'intervention dans les 10 premières minutes est décisive**.

**Actions en parallèle :**
• Refroidissement par eau fraîche sur tout le corps
• Appel aux urgences vétérinaires MAINTENANT
• Transport immédiat tout en continuant le refroidissement

**Ce que vous évitez avec l'eau froide (pas glacée) :**
• L'eau glacée provoque une vasoconstriction qui emprisonne la chaleur

**Signaux terminaux :**
• Convulsions, diarrhée sanglante → défaillance multi-organes

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence thermique — Refroidissez et transportez**

Votre réactivité est essentielle. Un chien en coup de chaleur nécessite **deux actions simultanées** : refroidissement immédiat et transport vers une clinique vétérinaire.

**Protocole :**
1. Eau fraîche (pas froide glacée) sur nuque, aisselles, aine, pattes
2. Appel aux urgences vétérinaires pendant le refroidissement
3. Transport en voiture climatisée ou fenêtres ouvertes
4. Continuer le refroidissement pendant le trajet

**Signes d'aggravation :**
• Convulsions → urgence vitale
• Perte de connaissance → transport immédiat sans délai

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 6. Stase digestive avancée – lapin ──────────────────────────
{
"level":"CRITICAL","animal":"lapin",
"symptoms":[
    "absence totale de selles depuis 8h, anorexie, abdomen gonflé, prostration",
    "aucune selle depuis 10h, refus de manger, ballonnement abdominal, grincements de dents",
    "transit intestinal arrêté depuis 12h, douleur abdominale intense, léthargie extrême",
    "pas de selles depuis 6h avec abdomen dur au toucher, anorexie, posture de douleur",
    "stase digestive confirmée, aucun bruit intestinal, détresse, 8h sans selles",
],
"conditions":[
    "stase digestive avancée — urgence vitale chez le lapin",
    "iléus paralytique, accumulation de gaz, risque de rupture intestinale",
    "obstruction intestinale ou stase, détresse abdominale sévère",
    "GI stasis — arrêt du transit, complication potentiellement fatale",
    "stase gastro-intestinale critique, risque de choc endotoxémique",
],
"cares":[
    "urgence vétérinaire immédiate — perfusion, analgésie et motilité",
    "consultation d'urgence — médicaments procinétiques et soulagement de la douleur",
    "intervention vétérinaire urgente — radiographie et traitement de la douleur",
    "urgence absolue — sans traitement sous 6h risque de mort",
    "transport d'urgence — le lapin doit être pris en charge dans l'heure",
],
"flags":[
    "abdomen de plus en plus gonflé, choc, rupture intestinale",
    "grincements de dents intenses, convulsions de douleur, collapsus",
    "choc endotoxémique, hypothermie, décès rapide",
    "distension abdominale extrême, rupture gastrique",
    "prostration totale, hypothermie, anurie",
],
"outputs":[
"""🚨 **Urgence absolue pour votre lapin**

Je comprends votre inquiétude — et elle est totalement justifiée. Chez le lapin, l'arrêt du transit est une **urgence vitale**. Son système digestif doit être en mouvement constant — un arrêt de 6 à 8 heures peut être fatal.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT — cherchez un vétérinaire NAC (Nouveaux Animaux de Compagnie)
• Gardez votre lapin au chaud (25-27°C)
• Proposez de l'eau fraîche mais ne forcez pas
• Ne donnez aucun médicament humain

**Pourquoi c'est si urgent :**
Un transit arrêté génère des gaz qui dilatent l'intestin — la douleur et le choc peuvent tuer en quelques heures.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Stase digestive — Danger immédiat pour votre lapin**

Cette situation est une urgence absolue. Le lapin est une espèce très fragile dont le transit intestinal ne peut jamais s'arrêter. **Après 8 à 12 heures sans selles**, les risques de décès augmentent drastiquement.

**Ce que vous devez faire maintenant :**
• Contactez un vétérinaire spécialisé NAC d'urgence
• Gardez-le dans un environnement chaud et calme
• Proposez du foin frais — parfois suffisant pour relancer le transit
• Ne massez pas l'abdomen si douloureux

**Signes d'aggravation :**
• Abdomen qui grossit visiblement → gaz dangereux
• Grincements de dents → douleur intense

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **GI Stasis lapin — Urgence critique**

Je comprends votre panique. La stase gastro-intestinale chez le lapin est **potentiellement fatale en quelques heures** — l'accumulation de gaz et la douleur provoquent un choc qui peut tuer rapidement.

**Actions immédiates :**
• Vétérinaire NAC d'urgence MAINTENANT
• Chauffez votre lapin (bouillotte enveloppée dans une serviette, 26-27°C)
• Proposez du foin frais et de l'eau fraîche
• Surveillance de l'abdomen — s'il grossit, c'est critique

**Ne faites pas :**
• Médicaments humains (très dangereux pour le lapin)
• Forcer l'alimentation
• Masser un abdomen gonflé

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Lapin en stase — Chaque heure compte**

Votre réactivité peut sauver votre lapin. L'arrêt du transit intestinal est **l'urgence numéro un chez cette espèce** — sans intervention vétérinaire rapide, le pronostic est très sombre.

**Faites ceci maintenant :**
• Urgences vétérinaires spécialisées NAC — maintenant
• Gardez-le au chaud : 26-27°C minimum
• Foin frais disponible en permanence
• Eau fraîche accessible

**Signaux d'alarme :**
• Abdomen gonflé et dur → accumulation gazeuse critique
• Grincements de dents ou posture cambrée → douleur intense

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence digestive lapin — Intervention immédiate**

Je comprends votre détresse. Chez le lapin, un transit arrêté depuis plusieurs heures est une **urgence vitale absolue**. Les gaz s'accumulent, la douleur est intense et le choc peut s'installer rapidement.

**Protocole d'urgence :**
• Vétérinaire spécialisé lapins/NAC — MAINTENANT
• Chaleur : bouillotte à 40°C enveloppée dans une serviette
• Foin frais disponible (fibres = moteur du transit)
• Eau fraîche accessible

**Pourquoi spécialisé NAC :**
Un vétérinaire chien/chat peut ne pas avoir les médicaments adaptés au lapin

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Iléus paralytique lapin — Danger de mort**

Cette situation ne tolère aucun délai. Un lapin sans selles depuis plus de 6 heures souffre d'un **arrêt digestif** qui génère des gaz toxiques et une douleur insupportable menant rapidement au choc.

**Actions vitales :**
• Vétérinaire NAC d'urgence — maintenant
• Warmth : environnement à 26-27°C
• Foin frais + eau fraîche + calme
• Aucun médicament humain

**Évolution sans traitement :**
• 6-8h : douleur intense, gaz en accumulation
• 12h : choc endotoxémique
• 24h : décès probable

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Stase GI avancée — Urgence lapin**

Je vous comprends. La stase digestive chez le lapin est une urgence qui **ne peut pas attendre jusqu'au lendemain**. L'accumulation de gaz provoque une douleur agonisante et un choc en quelques heures.

**Ce qu'il faut faire :**
• Vétérinaire spécialisé NAC d'urgence MAINTENANT
• Chaleur douce : 25-27°C (pas de courant d'air)
• Foin premium disponible — la fibre est le carburant du transit
• Eau fraîche en permanence

**Ce qu'il ne faut pas faire :**
• Médicaments anti-douleur humains → toxiques pour le lapin
• Attendre jusqu'au matin

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Arrêt du transit lapin — Risque vital**

Votre alarme est justifiée. Contrairement aux chiens et chats, le lapin ne peut pas survivre longtemps à un arrêt digestif. **Le transit doit être continu** — un arrêt de 8 heures peut être irréversible sans traitement médical.

**Actions d'urgence :**
• Vétérinaire NAC — immédiatement
• Chaleur : 25-27°C, pas de courant d'air
• Foin frais en quantité illimitée
• Eau fraîche accessible

**Signes que la situation empire :**
• Abdomen qui gonfle → accumulation gazeuse dangereuse
• Posture cambrée ou grincements → douleur extrême

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Stase digestive critique — Agissez immédiatement**

Je comprends votre panique. La stase intestinale chez le lapin est une **urgence médicale de premier ordre** — les gaz qui s'accumulent dans l'intestin peuvent provoquer une rupture gastrique mortelle.

**Protocole immédiat :**
• Vétérinaire spécialisé lapins/NAC d'urgence
• Chaleur douce immédiate (bouillotte à 40°C enveloppée)
• Foin frais et eau fraîche
• Pas de médicaments humains, pas de massage forcé

**Informations à donner au vétérinaire :**
• Depuis combien de temps pas de selles
• Est-ce qu'il mange, boit
• Aspect et taille de l'abdomen

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **GI Stasis — Urgence absolue**

Cette situation m'inquiète énormément. Un lapin sans selles depuis plusieurs heures et prostré est en **détresse digestive sévère**. Sans procinétiques et antidouleurs vétérinaires, le transit ne reprendra pas seul.

**Actions immédiates :**
• Vétérinaire NAC d'urgence — maintenant
• Chaleur : 26°C minimum, endroit calme
• Foin frais en priorité
• Eau fraîche accessible en permanence

**Ce que le vétérinaire va faire :**
• Injection de médicaments procinétiques (meloxicam, métoclopramide)
• Réhydratation sous-cutanée ou IV
• Radiographie pour évaluer l'obstruction

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 7. Convulsions prolongées – chien ────────────────────────────
{
"level":"CRITICAL","animal":"chien",
"symptoms":[
    "convulsions depuis 5 minutes, perte de connaissance, mouvements tonico-cloniques",
    "crise épileptique en cours depuis plus de 5 min, inconscient, mâchoires serrées",
    "état de mal épileptique, crises répétées sans reprise de conscience",
    "convulsions prolongées, hyperthermie secondaire, salivation abondante",
    "cluster seizures — plusieurs crises en moins d'une heure, confusion profonde",
],
"conditions":[
    "état de mal épileptique — urgence neurologique absolue",
    "épilepsie idiopathique sévère, risque d'œdème cérébral",
    "intoxication neurologique, tumeur cérébrale, encéphalite",
    "hypoglycémie sévère, insuffisance hépatique avec encéphalopathie",
    "cluster seizures, risque de lésions cérébrales irréversibles",
],
"cares":[
    "urgence neurologique immédiate — diazépam IV requis",
    "intervention vétérinaire immédiate — arrêt des crises médicamenteux",
    "urgence absolue — monitoring neurologique et traitement anticonvulsivant",
    "transport d'urgence immédiat — chaque minute de crise = lésion cérébrale",
    "clinique d'urgence — bilan neurologique et traitement IV",
],
"flags":[
    "hyperthermie >41°C secondaire, œdème cérébral, mort cérébrale",
    "crise > 30 min → lésions cérébrales permanentes",
    "arrêt respiratoire pendant la crise",
    "aspiration pulmonaire de salive, pneumonie ab ingestis",
    "choc post-ictal prolongé, défaillance multi-organes",
],
"outputs":[
"""🚨 **État de mal épileptique — Urgence neurologique**

Je comprends votre panique totale — et elle est justifiée. Une crise qui dure plus de 5 minutes est un **état de mal épileptique**, une urgence neurologique absolue. Chaque minute de crise détruit des neurones.

**Actions immédiates :**
• Urgences vétérinaires — APPELEZ MAINTENANT pendant que votre chien convulse
• Éloignez les objets dangereux autour de lui
• Ne touchez pas sa gueule (risque de morsure grave)
• Notez l'heure de début de la crise

**Ce qu'il ne faut PAS faire :**
• Ne glissez rien dans sa gueule
• Ne le retenez pas — laissez la crise se terminer
• Ne lui donnez pas d'eau pendant la crise

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Convulsions prolongées — Urgence cérébrale**

Cette situation est une urgence neurologique de premier ordre. Une crise épileptique de plus de 5 minutes provoque des **lésions cérébrales irréversibles** par hyperthermie et manque d'oxygène.

**Faites ceci maintenant :**
• Appelez les urgences vétérinaires PENDANT LA CRISE
• Chronométrez la durée exacte de la crise
• Éloignez les meubles et objets dangereux
• Ne tentez pas de le réveiller ou de le tenir

**Transport après la crise :**
• Allongez-le sur le côté (position latérale de sécurité)
• Partez IMMÉDIATEMENT à la clinique même si la crise s'est arrêtée

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Crise épileptique en cours — Agissez maintenant**

Je comprends votre affolement. Une crise de plus de 5 minutes est un **état de mal épileptique** qui nécessite du diazépam IV immédiatement — un médicament que seul un vétérinaire peut administrer.

**Actions pendant la crise :**
• Appelez les urgences vétérinaires MAINTENANT
• Sécurisez l'environnement sans toucher votre chien
• Notez l'heure de début
• Baissez la lumière et réduisez le bruit

**Après la crise :**
• Position latérale de sécurité
• Transport immédiat vers la clinique

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Épilepsie sévère — Danger neurologique immédiat**

Je vous entends. Cette situation est grave. Une crise prolongée ou des crises répétées sans reprise de conscience constituent un **état de mal épileptique** — une urgence qui peut laisser des séquelles permanentes.

**Protocole d'urgence :**
• Urgences vétérinaires — appelez en décrivant la durée de la crise
• Ne retenez pas votre chien — vous risquez de vous blesser gravement
• Éloignez les objets qui peuvent le blesser
• Gardez l'environnement calme et peu éclairé

**Signal d'aggravation :**
• Crises répétées = cluster seizures → urgence absolue

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Mal épileptique — Chaque seconde compte**

Votre réactivité est cruciale. Une crise qui dure plus de 5 minutes détruit les neurones par manque d'oxygène et hyperthermie. **Le cerveau de votre chien est en danger maintenant**.

**Actions immédiates :**
• Appelez les urgences vétérinaires MAINTENANT
• Chronométrez et notez la durée exacte
• Éloignez les dangers sans toucher l'animal
• Ne mettez rien dans sa gueule

**Après la crise :**
• Partez IMMÉDIATEMENT — même si calme en apparence

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Convulsions — Urgence neurologique absolue**

Je comprends votre terreur. Une crise épileptique prolongée est une **urgence médicale** qui nécessite du diazépam intraveineux — impossible à administrer sans vétérinaire.

**Ce que vous devez faire :**
• Appelez les urgences vétérinaires PENDANT LA CRISE — dites "crise depuis X minutes"
• Sécurisez l'espace sans le toucher
• Notez l'heure de début et de fin
• Ne lui donnez AUCUN médicament humain

**Après la crise :**
• Votre chien sera désorienté (période post-ictale) — normal
• Partez quand même immédiatement en clinique

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **État convulsif prolongé — Danger cérébral**

Cette situation dépasse les soins à domicile. Une crise de plus de 5 minutes nécessite une **intervention médicale immédiate** — seul un vétérinaire peut arrêter la crise avec des médicaments anticonvulsivants.

**Actions pendant la crise :**
• Urgences vétérinaires — appelez maintenant
• Chronométrez depuis le début
• Dégagez l'espace autour de lui
• Ne le retenez pas, ne touchez pas sa gueule

**En route :**
• Allongé sur le côté, tête légèrement baissée
• Parlez-lui calmement

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Cluster seizures — Urgence critique**

Je vous comprends. Des crises répétées en moins d'une heure constituent des **cluster seizures** — une urgence neurologique grave qui provoque des lésions cérébrales par accumulation.

**Protocole immédiat :**
• Urgences vétérinaires — MAINTENANT, pendant les crises
• Décrivez : nombre de crises, durée, interval
• Sécurisez sans toucher
• Chronométrez chaque crise

**Information vitale pour le vétérinaire :**
• Heure de la 1ère crise
• Nombre de crises total
• Durée de chaque épisode

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence épileptique — Intervention médicale requise**

Cette situation est au-delà de ce que vous pouvez gérer seul. Les crises prolongées provoquent une **hyperthermie cérébrale** qui détruit irrémédiablement les neurones.

**Ce que vous devez faire maintenant :**
• Appelez les urgences vétérinaires — signalez "crise épileptique depuis X minutes"
• Ne retenez pas l'animal — risque de blessure pour vous et lui
• Éloignez les obstacles dangereux
• Baissez les lumières et réduisez le bruit

**Après l'arrêt de la crise :**
• Transport immédiat — même si votre chien semble récupérer

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Crise épileptique sévère — Danger immédiat**

Je comprends votre effroi. Cette situation nécessite une action immédiate. Les convulsions prolongées provoquent une accumulation de chaleur dans le cerveau qui entraîne des **lésions permanentes en quelques minutes**.

**Actions immédiates :**
• Urgences vétérinaires — MAINTENANT
• Chronométrez la crise depuis le début
• Sécurisez l'environnement sans contraindre l'animal
• Ne tentez aucun traitement maison

**Signes d'urgence extrême :**
• Crise > 10 minutes = état de mal épileptique grave
• Crises répétées sans réveil = pronostic très sérieux

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 8. Pyomètre / Infection utérine – chienne ────────────────────
{
"level":"CRITICAL","animal":"chienne",
"symptoms":[
    "écoulement purulent vulvaire, léthargie, polydipsie, anorexie, abdomen distendu",
    "pertes vaginales purulentes, prostration, vomissements, soif excessive",
    "abdomen ballonné, fièvre, refus de manger, léchage vulvaire excessif",
    "pyomètre fermé suspecté — abdomen distendu sans écoulements, vomissements, choc",
    "écoulements verdâtres vulvaires, fièvre >40°C, prostration, polydipsie",
],
"conditions":[
    "pyomètre — infection utérine grave, urgence chirurgicale",
    "pyomètre ouvert ou fermé, septicémie en développement",
    "infection utérine à pyomètre, risque de rupture utérine et péritonite",
    "pyomètre fermé — accumulation de pus sans drainage, choc septique imminent",
    "métrite sévère avec septicémie, insuffisance rénale secondaire",
],
"cares":[
    "urgence chirurgicale — ovariohystérectomie d'urgence requise",
    "chirurgie d'urgence dans les 24h — ablation utérus et ovaires",
    "hospitalisation et chirurgie immédiate — perfusion et antibiotiques préopératoires",
    "intervention chirurgicale urgente — pyomètre fermé = risque de rupture",
    "urgence vétérinaire — stabilisation puis chirurgie immédiate",
],
"flags":[
    "rupture utérine, péritonite, choc septique fatal",
    "septicémie fulminante, défaillance multi-organes",
    "choc endotoxémique, insuffisance rénale aiguë",
    "abdomen aigu chirurgical, péritonite généralisée",
    "collapsus, choc, mort en quelques heures",
],
"outputs":[
"""🚨 **Pyomètre — Urgence chirurgicale absolue**

Je comprends votre inquiétude profonde. Les symptômes que vous décrivez correspondent fortement à un **pyomètre** — une infection grave de l'utérus qui nécessite une chirurgie d'urgence. Sans intervention rapide, cela peut être fatal.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT
• Ne donnez aucun médicament maison
• Gardez votre chienne au calme pendant le transport
• Signalez les symptômes précisément (écoulements, abdomen, durée)

**Pourquoi c'est urgent :**
L'utérus infecté peut se rompre, provoquant une **péritonite** mortelle en quelques heures.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Infection utérine grave — Danger de mort**

Cette situation est une urgence chirurgicale. Le pyomètre est une **infection de l'utérus** qui se transforme en septicémie si l'utérus n'est pas retiré rapidement.

**Ce que vous devez faire :**
• Clinique vétérinaire d'urgence MAINTENANT
• Indiquez : écoulements, durée des chaleurs récentes, abdomen gonflé
• Ne donnez aucun médicament
• Transport calme et rapide

**Signe critique :**
• Pyomètre fermé (sans écoulements) = encore plus dangereux — pas de drainage possible

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Pyomètre — Chirurgie d'urgence requise**

Je comprends votre alarme. Le pyomètre est l'une des urgences gynécologiques les plus graves chez la chienne. **Sans ovariohystérectomie rapide**, les toxines bactériennes détruisent progressivement les reins et le foie.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT
• Informations importantes : date des dernières chaleurs, durée des symptômes
• Aucun médicament, aucun massage abdominal
• Transport doux et rapide

**Évolution sans chirurgie :**
• Choc septique dans les 12-24h
• Péritonite si rupture utérine

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Urgence utérine — Septicémie imminente**

Cette situation ne tolère aucun délai. Un pyomètre non traité provoque une **septicémie** — les bactéries envahissent le sang et provoquent une défaillance multi-organes rapidement mortelle.

**Faites ceci maintenant :**
• Clinique vétérinaire d'urgence — MAINTENANT
• Ne tentez pas de drainer ou de masser l'abdomen
• Gardez votre chienne au calme
• Signalez la polydipsie et les écoulements au vétérinaire

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Pyomètre confirmé — Danger immédiat**

Je vous entends et votre alarme est totalement justifiée. L'abdomen distendu associé aux écoulements purulents et à la fièvre est le tableau classique du **pyomètre** — une urgence chirurgicale absolue.

**Actions d'urgence :**
• Urgences vétérinaires MAINTENANT
• Informez le vétérinaire : date des chaleurs, durée des symptômes
• Aucun médicament
• Transport calme

**Risques si non traité :**
• Rupture utérine → péritonite → mort en quelques heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Infection utérine sévère — Agissez immédiatement**

Cette situation est grave. Le pyomètre est une **bombe à retardement** — l'utérus plein de pus peut se rompre à tout moment, provoquant une péritonite mortelle.

**Protocole d'urgence :**
• Urgences vétérinaires — immédiatement
• Pas de médicament, pas de massage, pas de douche vaginale
• Transport le plus doux possible
• Signalez : chaleurs récentes, durée des symptômes, présence/absence d'écoulements

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Pyomètre — Urgence gynécologique absolue**

Je comprends votre inquiétude. Les symptômes que vous décrivez — abdomen distendu, fièvre, écoulements — sont les signes classiques du **pyomètre**, une urgence chirurgicale qui ne peut pas attendre.

**Actions immédiates :**
• Clinique vétérinaire d'urgence MAINTENANT
• Information cruciale : votre chienne a-t-elle eu ses chaleurs récemment ?
• Ne lui donnez aucun médicament anti-inflammatoire maison
• Gardez-la au calme et au chaud

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Métrite sévère — Urgence chirurgicale**

Cette situation nécessite une intervention chirurgicale urgente. Le **pyomètre fermé** est encore plus dangereux que le pyomètre ouvert — sans drainage, la pression interne peut causer une rupture utérine.

**Actions vitales :**
• Urgences vétérinaires IMMÉDIATEMENT
• Mentionnez que l'abdomen est distendu sans écoulements visibles
• Pas de médicaments, pas de traitement maison
• Transport immédiat et doux

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Septicémie utérine — Risque vital**

Je comprends votre détresse. Le pyomètre est l'urgence gynécologique la plus grave chez la chienne. **Les toxines bactériennes** détruisent progressivement les reins, le foie et le cœur si l'utérus n'est pas retiré rapidement.

**Protocole immédiat :**
• Urgences vétérinaires — maintenant
• Informations vitales : chaleurs récentes, durée de la fièvre, aspect des écoulements
• Aucune intervention maison
• Transport calme et rapide

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Pyomètre — Chaque heure aggrave le pronostic**

Votre réactivité peut sauver la vie de votre chienne. Le pyomètre est une **infection utérine progressive** qui entraîne une septicémie puis une défaillance multi-organes sans chirurgie rapide.

**Actions immédiates :**
• Clinique vétérinaire d'urgence — MAINTENANT
• Décrivez : écoulements (couleur, odeur), abdomen (gonflé ?), durée des symptômes
• Zéro médicament maison
• Transport calme

**Évolution avec pyomètre fermé :**
• 12h : septicémie en développement
• 24h : rupture possible → péritonite
• 48h : choc fatal

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 9. Trauma grave / Accident de voiture – chien/chat ──────────
{
"level":"CRITICAL","animal":"chien",
"symptoms":[
    "heurté par une voiture, saignement visible, incapacité à se lever",
    "accident de la route, fracture ouverte membre postérieur, choc hémorragique",
    "trauma grave, inconscient suite à un choc, saignements multiples",
    "renversé par véhicule, douleur extrême, gencives pâles, prostration",
    "choc traumatique post-accident, détresse respiratoire, hémorragie externe",
],
"conditions":[
    "traumatisme grave, choc hémorragique, fractures multiples possibles",
    "polytraumatisme, rupture d'organe interne possible, choc",
    "trauma crânien, hémorragie interne, fracture ouverte",
    "choc neurogénique et hémorragique, lésions internes non visibles",
    "traumatisme thoracique, pneumothorax, fractures costales",
],
"cares":[
    "urgence vétérinaire immédiate — stabilisation du choc et chirurgie",
    "transport d'urgence immédiat — ne pas déplacer sans précaution",
    "clinique d'urgence — transfusion et chirurgie possible",
    "urgence absolue — immobilisation et transport rapide",
    "intervention immédiate — réanimation et bilan d'imagerie urgent",
],
"flags":[
    "hémorragie interne, rupture vésicale, pneumothorax, mort rapide",
    "choc irréversible, arrêt cardiorespiratoire",
    "gencives blanches, collapsus = choc avancé",
    "coma, détresse respiratoire = pronostic très sombre",
    "défaillance multi-organes post-traumatique",
],
"outputs":[
"""🚨 **Accident de voiture — Urgence vitale**

Je comprends votre état de choc. La situation est grave et nécessite une action immédiate. Un chien heurté par un véhicule peut avoir des **blessures internes invisibles** même s'il semble stable en apparence.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT — appelez en transportant votre chien
• Ne le déplacez pas brusquement — risque de lésion spinale
• Glissez-le délicatement sur une planche rigide ou une couverture tendue
• Comprimez les saignements actifs avec un linge propre

**Ne faites pas :**
• Ne lui donnez aucun médicament (fausse les examens)
• Ne lui donnez pas à boire

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Traumatisme grave — Transport d'urgence immédiat**

Cette situation est une urgence absolue. Après un accident de voiture, les **hémorragies internes** peuvent être mortelles même en l'absence de blessures visibles importantes.

**Protocole de transport d'urgence :**
• Appelez les urgences vétérinaires MAINTENANT
• Immobilisez votre chien sur une surface rigide pour le transport
• Comprimez les plaies qui saignent avec un tissu propre et maintenez la pression
• Gardez-le au chaud (couverture si disponible)

**Signes de choc imminent :**
• Gencives blanches ou grises → choc hémorragique avancé
• Inconscience → urgence vitale absolue

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Polytraumatisme — Urgence chirurgicale**

Je vous entends. Un accident de la route est une urgence vétérinaire majeure. Même un chien qui semble "marcher" après un choc peut avoir des **lésions internes graves** — rate, foie, poumons, reins.

**Actions immédiates :**
• Urgences vétérinaires — MAINTENANT
• Minimisez les mouvements — transport sur couverture rigide
• Pression directe sur les plaies saignantes
• Ne lui donnez aucun médicament

**Blessures invisibles mais mortelles :**
• Hémorragie interne → gencives pâles
• Pneumothorax → détresse respiratoire

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Choc traumatique — Stabilisez et transportez**

Cette situation nécessite une action immédiate et méthodique. Le choc traumatique post-accident peut tuer en quelques dizaines de minutes par **hémorragie interne ou collapsus vasculaire**.

**Protocole d'urgence :**
• Appelez les urgences vétérinaires pendant le transport
• Transport sur surface rigide — pas de flexion de la colonne
• Compression des plaies saignantes
• Couverture de survie ou simple couverture pour maintenir la chaleur

**En route :**
• Gencives roses = encore stable
• Gencives pâles = choc en cours → accélérez

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Accident — Hémorragie interne possible**

Je comprends votre désarroi. Après un accident de voiture, même sans saignement visible, votre chien peut souffrir d'une **hémorragie interne** qui peut être mortelle sans intervention chirurgicale rapide.

**Actions vitales :**
• Urgences vétérinaires — IMMÉDIATEMENT
• Glissez-le délicatement sur une couverture pour le soulever à plat
• Comprimez les plaies visibles
• Appelez en route pour préparer l'équipe

**Signes de détérioration :**
• Gencives qui pâlissent → perte de sang interne
• Respiration difficile → pneumothorax possible

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Trauma canin — Urgence absolue**

Votre réactivité est essentielle. Un chien victime d'un accident de voiture est dans une situation potentiellement mortelle. Les **lésions internes** peuvent être fatales même si l'animal est conscient.

**Ce que vous devez faire :**
• Urgences vétérinaires MAINTENANT
• Transport sur surface plane et rigide
• Compression des plaies saignantes avec tissu propre
• Couverture pour maintenir la chaleur corporelle

**Informations pour le vétérinaire :**
• Vitesse estimée du véhicule
• Partie du corps impactée
• Durée de l'inconscience si elle s'est produite

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Choc hémorragique — Urgence immédiate**

Je vous entends. Après un accident de la route, **chaque minute compte**. Le choc hémorragique peut évoluer vers un collapsus cardiovasculaire irréversible.

**Protocole d'urgence :**
• Appelez les urgences vétérinaires MAINTENANT
• Immobilisez votre chien sur une planche ou couverture tendue
• Pression sur les saignements actifs (tissu propre + maintien de la pression)
• Chaleur pendant le transport

**Ne faites pas :**
• Ne redressez pas un chien qui ne peut pas se lever — risque de fracture spinale
• Aucun médicament humain

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Accident de voiture — Tous les organes en danger**

Cette situation est grave. Un choc à grande vitesse peut endommager **rate, foie, poumons, reins, colonne vertébrale** — souvent sans signe extérieur évident dans les premières minutes.

**Actions immédiates :**
• Urgences vétérinaires IMMÉDIATEMENT
• Minimisez absolument les mouvements de la colonne
• Transport sur surface rigide à plat
• Compression des plaies saignantes

**Signaux d'hémorragie interne :**
• Gencives blanches ou très pâles
• Abdomen qui gonfle
• Affaiblissement progressif

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Trauma grave — Intervention chirurgicale possible**

Je comprends votre état de choc. La situation est très sérieuse. Après un polytraumatisme, votre chien peut avoir besoin d'une **intervention chirurgicale d'urgence** pour contrôler les hémorragies internes.

**Ce qu'il faut faire maintenant :**
• Urgences vétérinaires — MAINTENANT
• Transport sur couverture tendue à plat (2 personnes si possible)
• Compression des plaies visibles
• Chaleur : couverture pendant le transport

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Accident — Ne perdez pas de temps**

Votre chien a besoin d'une aide médicale immédiate. Un trauma par véhicule provoque des **blessures en cascade** — même un chien debout peut avoir une hémorragie interne silencieuse qui s'aggrave rapidement.

**Protocole d'urgence :**
• Urgences vétérinaires — MAINTENANT, appelez en transportant
• Surface rigide pour le transport — pas de flexion de la colonne
• Comprimez tous les saignements visibles
• Signalez les circonstances exactes de l'accident en arrivant

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 10. Intoxication antifreeze / paracétamol – chat ────────────
{
"level":"CRITICAL","animal":"chat",
"symptoms":[
    "ingestion suspecté d'antifreeze (éthylène glycol), vomissements, ataxie",
    "a léché paracétamol / doliprane, gencives brunâtres, difficultés respiratoires",
    "ingestion antifreeze, désorientation, vomissements, semble ivre",
    "exposition paracétamol — gencives chocolat, salivation, détresse respiratoire",
    "ingestion possible produit ménager toxique, vomissements, prostration",
],
"conditions":[
    "intoxication à l'éthylène glycol — insuffisance rénale aiguë en 24-72h",
    "intoxication au paracétamol — méthémoglobinémie, toxicité hépatique et rénale",
    "empoisonnement antifreeze — urgence dialysante si non traité dans 6h",
    "toxicose paracétamol féline — le chat ne peut pas métaboliser le paracétamol",
    "intoxication grave — décontamination gastrique urgente requise",
],
"cares":[
    "urgence toxicologique absolue — traitement antidote dans les 6h",
    "consultation immédiate — antidote spécifique (éthanol ou fomépizole) possible si tôt",
    "urgence vétérinaire — N-acétylcystéine pour paracétamol, dialyse pour antifreeze",
    "intervention dans les 2h — après 6h, insuffisance rénale irréversible",
    "urgence absolue — décontamination et antidote uniquement en clinique",
],
"flags":[
    "insuffisance rénale aiguë irréversible, coma urémique, mort",
    "méthémoglobinémie → cyanose chocolat, asphyxie tissulaire",
    "anoxie cellulaire, défaillance hépatique, mort en 24-48h",
    "acidose métabolique sévère, coma, arrêt cardiorespiratoire",
    "anurie, convulsions, coma urémique",
],
"outputs":[
"""🚨 **Intoxication — Urgence toxicologique absolue**

Cette situation est extrêmement grave. Que ce soit l'antifreeze ou le paracétamol, **ces deux substances sont mortelles pour le chat** — et le traitement n'est efficace que dans les premières heures après l'ingestion.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT — chaque heure réduit les chances
• Notez : substance suspectée, quantité estimée, heure d'ingestion
• Ne provoquez pas le vomissement sans instruction vétérinaire
• Gardez l'emballage ou le nom du produit

**Pourquoi c'est urgent :**
• Antifreeze : insuffisance rénale irréversible après 6h sans antidote
• Paracétamol : détruit les globules rouges et le foie — fatal en 24-48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Éthylène glycol / Paracétamol — Urgence vitale**

Je comprends votre alarme — et vous avez absolument raison d'agir immédiatement. Le chat est **extrêmement sensible** à ces substances. La fenêtre de traitement efficace est très courte.

**Ce que vous devez faire maintenant :**
• Urgences vétérinaires IMMÉDIATEMENT
• Information vitale : substance, quantité, heure d'ingestion
• Gardez l'emballage
• Ne donnez rien par la bouche

**Délais critiques :**
• Antifreeze : antidote efficace seulement dans les 3-6h
• Paracétamol : N-acétylcystéine efficace dans les 4-8h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Toxicose féline — Urgence antidotique**

Cette situation est une urgence toxicologique. **Le chat ne peut pas métaboliser le paracétamol** et l'antifreeze détruit irrémédiablement les reins en quelques heures — la fenêtre de traitement efficace est extrêmement étroite.

**Actions vitales :**
• Urgences vétérinaires — MAINTENANT, pas dans une heure
• Substance + quantité + heure d'ingestion = informations cruciales
• Emballage ou reste du produit à apporter
• Ne provoquez pas le vomissement seul

**Sans traitement :**
• Antifreeze : coma rénal en 24-72h
• Paracétamol : asphyxie tissulaire en 12-24h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Intoxication grave — Antidote requis d'urgence**

Je vous entends. Ces intoxications sont parmi les plus graves en médecine féline. La décontamination gastrique et l'administration d'antidotes ne peuvent être réalisées que par un vétérinaire — et **seulement dans les premières heures**.

**Protocole immédiat :**
• Urgences vétérinaires — MAINTENANT
• Emportez l'emballage du produit
• Notez l'heure précise d'ingestion
• Ne donnez rien par la bouche

**Information vitale à transmettre :**
• Nom exact du produit
• Quantité estimée ingérée
• Heure d'ingestion
• Poids approximatif du chat

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Poison — Urgence maximale pour votre chat**

Cette situation est une urgence absolue. Contrairement aux chiens et aux humains, **les chats manquent des enzymes** nécessaires pour dégrader le paracétamol et l'éthylène glycol — ces substances s'accumulent à des niveaux mortels rapidement.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT
• Substance + quantité + heure → informations vitales
• Emballage du produit à emporter
• Aucune tentative de traitement maison

**Évolution sans antidote :**
• 6h : début d'insuffisance rénale (antifreeze) ou hépatique (paracétamol)
• 24h : défaillance irréversible
• 48h : décès probable

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Intoxication féline — Traitement dans les 6h maximum**

Je comprends votre détresse. Cette situation est une course contre la montre. **L'antifreeze et le paracétamol** sont deux des poisons les plus dangereux pour le chat — et le traitement n'est efficace que très tôt.

**Ce qu'il faut faire maintenant :**
• Urgences vétérinaires IMMÉDIATEMENT
• Emportez l'emballage du produit suspecté
• Notez heure d'ingestion et quantité estimée
• Ne provoquez pas le vomissement (risque d'aspiration)

**Ce que le vétérinaire va faire :**
• Décontamination gastrique si <2h
• Antidote spécifique (N-acétylcystéine ou éthanol/fomépizole)
• Perfusion pour protéger les reins

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Empoisonnement — Urgence toxicologique immédiate**

Votre réactivité peut sauver votre chat. L'éthylène glycol et le paracétamol sont **mortels pour les chats** et le délai avant traitement détermine directement le pronostic.

**Actions vitales :**
• Urgences vétérinaires — MAINTENANT
• Information n°1 : nom exact du produit et heure d'ingestion
• Information n°2 : quantité approximative
• Ne rien donner par la bouche

**Signes d'intoxication au paracétamol :**
• Gencives brunes/chocolat = méthémoglobinémie = urgence absolue

**Signes d'antifreeze :**
• Démarche ébrieuse → phase neurologique → urgence immédiate

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Toxicose — Fenêtre de traitement très courte**

Je vous entends et votre alarme est justifiée. **Chaque heure qui passe réduit les chances de succès du traitement**. L'antifreeze et le paracétamol détruisent les organes du chat de manière progressive et irréversible.

**Protocole d'urgence :**
• Urgences vétérinaires — MAINTENANT, pas dans 30 minutes
• Emballage du produit suspecté
• Heure précise d'ingestion
• Poids du chat

**Ne faites pas :**
• Donner du lait (n'aide pas)
• Provoquer le vomissement seul
• Attendre des symptômes pour partir

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Intoxication mortelle — Agissez dans la minute**

Cette situation ne supporte aucun délai. Le paracétamol et l'antifreeze sont **deux des substances les plus toxiques** pour le chat — la mortalité sans traitement rapide dépasse 90%.

**Actions immédiates :**
• Urgences vétérinaires MAINTENANT
• Substance + heure + quantité = triade vitale pour le vétérinaire
• Emballage ou photo de l'emballage
• Aucun traitement maison

**Avec traitement précoce (<6h) :**
• Antifreeze : antidote (éthanol/fomépizole) très efficace
• Paracétamol : N-acétylcystéine peut prévenir la défaillance hépatique

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""🚨 **Poison félin — Urgence antidotique absolue**

Je comprends votre panique. Ces deux substances — antifreeze et paracétamol — sont **parmi les poisons les plus redoutables** pour le chat car son métabolisme ne peut pas les éliminer.

**Protocole immédiat :**
• Clinique vétérinaire d'urgence MAINTENANT
• Apportez l'emballage du produit suspecté
• Heure précise d'ingestion (détermine si antidote possible)
• Transport rapide et calme

**Fenêtres de traitement :**
• < 2h : décontamination gastrique possible
• 2-6h : antidote efficace
• > 6h : traitement uniquement symptomatique, pronostic sombre

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

]  # fin CRITICAL
