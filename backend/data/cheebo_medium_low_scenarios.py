#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cheebo_medium_low_scenarios.py — Scénarios MEDIUM et LOW pour generate_cheebo_dataset.py
"""

MEDIUM = [

# ── 1. Vomissement répété sans sang – chien ──────────────────────
{
"level":"MEDIUM","animal":"chien",
"symptoms":[
    "vomissements 2-3 fois par jour depuis 2 jours, sans sang, appétit diminué",
    "vomissement récurrent depuis hier, nourriture non digérée, légère léthargie",
    "épisodes de vomissements quotidiens depuis 3 jours, selles normales",
    "vomit chaque matin à jeun, bile jaune, mange normalement le reste du temps",
    "vomissements répétés après les repas depuis 2 jours, pas de sang, actif",
],
"conditions":[
    "gastrite chronique, syndrome du vomissement biliaire, indigestion",
    "sensibilité alimentaire, gastrite, trouble de la motilité gastrique",
    "reflux gastro-œsophagien, changement alimentaire, parasites",
    "gastrite à jeun (bile), alimentation inadaptée",
    "trouble digestif fonctionnel, sensibilité alimentaire",
],
"cares":[
    "consultation vétérinaire dans les 2-3 jours — régime et antiémétiques",
    "diète digestive + consultation si pas d'amélioration en 48h",
    "surveillance 48h + consultation si persistance",
    "fractionner les repas + consultation vétérinaire sous 48h",
    "alimentation adaptée + vétérinaire si pas d'amélioration",
],
"flags":[
    "sang dans les vomissements, déshydratation, léthargie sévère",
    "vomissements > 5 fois/jour, anorexie totale",
    "perte de poids rapide, selles noires",
    "abdomen douloureux, fièvre associée",
    "aggravation rapide, prostration",
],
"outputs":[
"""📋 **Surveillance recommandée**

Je comprends votre inquiétude. Des vomissements répétés sans sang chez un chien actif peuvent indiquer une **gastrite légère ou une sensibilité alimentaire**. Un suivi attentif pendant 48h est raisonnable avant la consultation.

**Soins à domicile :**
• Diète stricte pendant 12-24h (eau fraîche uniquement)
• Reprise avec riz blanc + poulet bouilli en petites quantités
• Fractionner en 3-4 petits repas au lieu de 2 grands
• Pas de friandises ni restes de table

**Consultez le vétérinaire dans les 2-3 jours si :**
• Les vomissements persistent ou augmentent
• Votre chien devient léthargique
• Apparition de sang

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Gastrite légère probable — Surveillance 48h**

Je vous entends. Des vomissements répétés sans sang et avec un appétit conservé évoquent une **gastrite légère ou un syndrome biliaire** qui répond généralement bien aux mesures diététiques.

**Ce que vous pouvez faire :**
• Diète 12-24h puis reprise progressive (riz + poulet)
• Fractionner les repas (4 fois par jour)
• Eau fraîche disponible en permanence
• Éviter les changements alimentaires brusques

**Consultez le vétérinaire si :**
• Pas d'amélioration après 48h
• Apparition de sang dans le vomi
• Léthargie ou anorexie totale

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Trouble digestif — Mesures diététiques recommandées**

Je comprends votre préoccupation. Les vomissements répétés sans sang ni aggravation majeure peuvent souvent être gérés à domicile avec des mesures diététiques appropriées pendant 48 heures.

**Soins immédiats :**
• Diète 12h puis alimentation légère fractionnée
• Riz + poulet bouilli sans sel ni épices
• 4 petits repas par jour
• Eau fraîche accessible en permanence

**Consultez si pas d'amélioration en 48h ou si :**
• Apparition de sang
• Forte léthargie
• Plus de 5 vomissements par jour

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Vomissements répétés — Diète et surveillance**

Je vous entends. La répétition des vomissements sans autres signes graves justifie une **période de surveillance de 48h** avec mesures diététiques avant la consultation vétérinaire.

**Régime digestif :**
• Jeûne 12h puis riz + poulet bouilli
• Repas fractionnés (3-4 fois par jour)
• Pas de nourriture grasse, sucrée ou épicée
• Eau fraîche en permanence

**Consultez si :**
• Pas d'amélioration en 48h
• Sang dans les vomissements
• Perte d'appétit totale

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Gastrite fonctionnelle — Surveillance recommandée**

Je comprends votre inquiétude. Des vomissements de bile à jeun sont souvent le signe d'un **syndrome biliaire** qui peut être amélioré en fractionnant les repas et en donnant un repas léger le soir.

**Mesures pratiques :**
• Petite quantité de nourriture le soir avant le coucher
• Fractionner les repas en 3-4 fois par jour
• Alimentation digestive légère pendant 3-5 jours
• Eau fraîche disponible

**Consultez le vétérinaire si :**
• Pas d'amélioration en 3-4 jours
• Apparition d'autres symptômes

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Vomissements chroniques légers — Régime adapté**

Je vous entends. Les vomissements répétés sans sang qui persistent depuis 2-3 jours nécessitent une **alimentation digestive** et une surveillance attentive.

**Soins à domicile :**
• Alimentation hypoallergénique ou digestive vétérinaire
• Repas fractionnés (4 fois/jour)
• Pas de friandises
• Eau fraîche disponible

**Consultation dans les 2-3 jours si pas d'amélioration.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Problème digestif récurrent — Consultez dans 48h**

Je comprends votre préoccupation. Des vomissements répétés sur plusieurs jours méritent une **consultation vétérinaire dans les 48 heures** pour identifier la cause précise et adapter le traitement.

**En attendant :**
• Diète légère fractionnée
• Eau fraîche disponible
• Évitez les changements alimentaires

**Consultez le vétérinaire dans les 2 jours.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Indigestion récurrente — Mesures simples**

Je vous entends. Des vomissements répétés peuvent souvent être contrôlés par des mesures simples avant de nécessiter une consultation vétérinaire.

**Soins immédiats :**
• Diète 12h puis alimentation légère
• Riz + poulet bouilli en petites quantités
• 4 petits repas par jour
• Surveillance de l'évolution

**Consultez si pas d'amélioration en 48h.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Gastrite légère — Régime et repos**

Je comprends votre inquiétude. Une gastrite légère répond bien au repos digestif et à une alimentation adaptée — des mesures que vous pouvez commencer dès maintenant.

**Ce que vous pouvez faire :**
• Diète 12-24h
• Reprise avec alimentation légère fractionnée
• Eau fraîche disponible
• Pas de friandises pendant 5 jours

**Consultez dans 48h si pas d'amélioration.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Vomissements sans gravité immédiate — Surveillez 48h**

Je vous entends. Des vomissements répétés sans sang ni urgence immédiate peuvent être surveillés à domicile pendant 48 heures avec des mesures diététiques appropriées.

**Mesures pratiques :**
• Diète légère fractionnée
• Riz + poulet bouilli
• Eau fraîche en permanence
• Surveillance de l'état général

**Consultez le vétérinaire si aggravation ou persistance.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 2. Infection auriculaire – chien ─────────────────────────────
{
"level":"MEDIUM","animal":"chien",
"symptoms":[
    "secouements de tête fréquents, grattage de l'oreille, odeur nauséabonde",
    "oreille rouge et chaude, sécrétions marron/noires, douleur à la palpation",
    "otite externe, inclinaison de la tête, gémissements au toucher de l'oreille",
    "grattage intensif d'une oreille, cérumen abondant et foncé, odeur",
    "écoulement auriculaire purulent, oreille gonflée, sensible, inclinaison",
],
"conditions":[
    "otite externe bactérienne ou levurienne (Malassezia)",
    "otite à Malassezia, surinfection bactérienne secondaire",
    "otite chronique, corps étranger (épillet), parasites (otodecte)",
    "otite mixte bactérie/levure, allergie sous-jacente",
    "otite sévère, risque d'otite moyenne",
],
"cares":[
    "consultation vétérinaire dans les 2-3 jours — otoscope et traitement",
    "vétérinaire dans les 48h — prélèvement cytologique et traitement adapté",
    "consultation sous 48h — nettoyage auriculaire et traitement antifongique/antibiotique",
    "vétérinaire dans les 2 jours — identification du germe et traitement ciblé",
    "consultation dans les 2-3 jours — traitement topique adapté",
],
"flags":[
    "otite moyenne, perforation du tympan, signes neurologiques",
    "paralysie faciale, vestibulaire, syndrome de Horner",
    "douleur extrême, tête inclinée en permanence, perte d'équilibre",
    "signes centraux : nystagmus, ataxie",
    "hématome auriculaire si grattage excessif",
],
"outputs":[
"""📋 **Otite — Consultation dans les 2-3 jours**

Je comprends votre inquiétude. Une oreille rouge, malodorante et douloureuse est généralement due à une **otite externe** bactérienne ou levurienne qui nécessite un traitement vétérinaire adapté.

**Soins à domicile en attendant :**
• Ne nettoyez pas l'oreille avec des cotons-tiges (aggrave l'infection)
• Utilisez un nettoyant auriculaire vétérinaire doux si vous en avez
• Empêchez votre chien de se gratter (collerette si nécessaire)
• Consultez le vétérinaire dans les 2-3 jours

**Consultez rapidement si :**
• Votre chien tient la tête inclinée en permanence
• Perte d'équilibre ou yeux qui bougent seuls (nystagmus)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Otite externe — Traitement vétérinaire nécessaire**

Je vous entends. Les sécrétions malodorantes et la douleur auriculaire indiquent une **infection de l'oreille** qui nécessite un traitement adapté à l'agent infectieux identifié (levure, bactérie ou les deux).

**En attendant la consultation :**
• Pas de coton-tige dans le conduit
• Nettoyant auriculaire vétérinaire si disponible
• Collerette si grattage intense
• Consultation vétérinaire dans les 48-72h

**Urgence si :**
• Tête inclinée en permanence
• Perte d'équilibre
• Douleur extrême à la palpation

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Infection auriculaire — Consultez sous 48h**

Je comprends votre préoccupation. Une otite externe non traitée peut s'étendre à l'oreille moyenne (**otite moyenne**) et causer des complications neurologiques graves — une consultation dans les 48 heures est recommandée.

**Soins immédiats :**
• Ne nettoyez pas avec des cotons-tiges
• Nettoyant auriculaire doux vétérinaire si disponible
• Collerette pour éviter le grattage
• Consultation vétérinaire dans les 48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Otite à levures probable — Traitement nécessaire**

Je vous entends. Des sécrétions marron/noires malodorantes évoquent une **otite à Malassezia** (levure) qui nécessite un traitement antifongique auriculaire prescrit par un vétérinaire.

**En attendant :**
• Pas de coton-tige
• Nettoyant auriculaire vétérinaire si disponible
• Collerette si grattage
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Otite chronique — Consultation recommandée**

Je comprends votre inquiétude. Une otite qui dure ou revient régulièrement indique souvent une **allergie sous-jacente** ou un problème anatomique qui nécessite une investigation plus approfondie.

**Soins immédiats :**
• Nettoyant auriculaire vétérinaire doux
• Collerette pour protéger l'oreille
• Pas de cotons-tiges

**Consultez le vétérinaire dans les 2-3 jours** pour identifier la cause sous-jacente.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Infection d'oreille — Soins et consultation**

Je vous entends. Une otite avec sécrétions et douleur nécessite un **examen otoscopique** pour visualiser le tympan et identifier l'agent infectieux avant de prescrire le traitement adapté.

**En attendant :**
• Nettoyant auriculaire vétérinaire (pas de coton-tige)
• Collerette si grattage intense
• Consultation vétérinaire dans les 48-72h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Otite externe — Ne pas négliger**

Je comprends votre préoccupation. Une otite non traitée peut chronifier et s'étendre à l'oreille moyenne — une consultation vétérinaire dans les 2-3 jours permettra d'éviter ces complications.

**Soins à domicile :**
• Nettoyant auriculaire vétérinaire doux
• Pas de cotons-tiges
• Collerette si grattage
• Consultation vétérinaire sous 48-72h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Otite bactérienne/levurienne — Traitement adapté requis**

Je vous entends. Une otite avec odeur et sécrétions colorées nécessite un **prélèvement cytologique** pour identifier le germe et choisir le traitement antibiotique ou antifongique approprié.

**En attendant la consultation :**
• Nettoyant auriculaire vétérinaire
• Pas de cotons-tiges
• Collerette si nécessaire
• Consultation dans les 48-72h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Oreille infectée — Consultez dans les 2 jours**

Je comprends votre inquiétude. L'infection auriculaire nécessite un traitement topique spécifique qui ne peut être prescrit qu'après un examen vétérinaire avec otoscope.

**Soins à domicile :**
• Nettoyant auriculaire vétérinaire doux si disponible
• Collerette pour protéger l'oreille
• Pas de cotons-tiges
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Otite — Prévenir les complications**

Je vous entends. Une otite traitée rapidement guérit bien — mais négligée, elle peut mener à une **otite chronique** difficile à traiter. Une consultation dans les 2-3 jours est recommandée.

**Soins immédiats :**
• Nettoyant auriculaire vétérinaire
• Collerette si grattage intense
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 3. Démangeaisons / Perte de poils – chien ────────────────────
{
"level":"MEDIUM","animal":"chien",
"symptoms":[
    "grattage intense depuis 1 semaine, perte de poils localisée, peau rouge",
    "démangeaisons chroniques, plaques sans poils, peau épaissie",
    "frottement du visage, léchage des pattes, rougeur cutanée diffuse",
    "perte de poils en plaques, peau squameuse, grattage intense",
    "dermatite diffuse, grattage nocturne, peau irritée, odeur cutanée",
],
"conditions":[
    "dermatite allergique, atopie, allergie alimentaire",
    "démodécie, gale sarcoptique, teigne",
    "allergie aux puces, dermatite de contact",
    "hypothyroïdie, syndrome de Cushing, dermatite séborrhéique",
    "allergie environnementale, dermatite atopique",
],
"cares":[
    "consultation vétérinaire dans les 2-3 jours — bilan dermatologique",
    "vétérinaire sous 48h — test d'allergie et traitement antiparasitaire",
    "consultation dans les 2-3 jours — raclage cutané et bilan hormonal",
    "vétérinaire cette semaine — identification cause et traitement adapté",
    "consultation dermatologique vétérinaire — dans les 3-5 jours",
],
"flags":[
    "plaies ouvertes, infection cutanée secondaire, pyodermite",
    "gale sarcoptique contagieuse à l'humain",
    "dépression immunitaire, malnutrition sévère",
    "prolifération bactérienne grave, cellulite",
    "automutilation, blessures profondes",
],
"outputs":[
"""📋 **Problème cutané — Consultation dans les 2-3 jours**

Je comprends votre inquiétude. Des démangeaisons intenses avec perte de poils peuvent indiquer plusieurs causes : **allergie, parasites (puces, gale, démodécie) ou trouble hormonal**. Un examen dermatologique permettra d'identifier la cause.

**Soins à domicile en attendant :**
• Vérifiez la présence de puces dans le pelage (peigne fin)
• Antiparasitaire à jour si ce n'est pas le cas
• Pas de cortisone humaine (masque les symptômes)
• Évitez les produits irritants (shampoing, parfum)

**Consultez le vétérinaire dans les 2-3 jours.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Dermatite — Bilan vétérinaire recommandé**

Je vous entends. Des grattages intenses et une perte de poils nécessitent un **diagnostic précis** car les causes sont nombreuses : allergie, parasites, champignons, problème hormonal.

**En attendant la consultation :**
• Antiparasitaire préventif si non à jour
• Shampoing doux (sans parfum ni colorant)
• Collerette si l'animal se blesse
• Consultation vétérinaire dans les 48-72h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Allergie cutanée probable — Consultez cette semaine**

Je comprends votre préoccupation. Le frottement du visage et le léchage des pattes sont des signes classiques d'**atopie** (allergie environnementale) — une condition courante mais qui nécessite un traitement vétérinaire adapté.

**Soins immédiats :**
• Antiparasitaire à jour
• Shampoing doux
• Pas de produits parfumés
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Alopécie et prurit — Diagnostic nécessaire**

Je vous entends. Des plaques sans poils avec grattage peuvent indiquer une **gale, une démodécie, une teigne ou une allergie** — des diagnostics très différents nécessitant des traitements spécifiques.

**En attendant :**
• Antiparasitaire préventif
• Shampoing doux
• Évitez le contact avec d'autres animaux (gale possible)
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Dermatose — Consultation recommandée**

Je comprends votre inquiétude. Une dermatite diffuse avec grattage nocturne mérite une **investigation vétérinaire** pour identifier la cause (allergie, Cushing, hypothyroïdie) et adapter le traitement.

**Soins à domicile :**
• Antiparasitaire à jour
• Bain doux avec shampoing hypoallergénique
• Pas de cortisone humaine
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Prurit chronique — Bilan dermatologique**

Je vous entends. Des démangeaisons chroniques avec perte de poils localisée nécessitent un **bilan dermatologique vétérinaire** incluant raclage cutané et éventuellement tests allergologiques.

**En attendant :**
• Antiparasitaire préventif
• Shampoing doux sans irritant
• Consultation vétérinaire dans les 3-5 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Allergie aux puces probable — Traitez et consultez**

Je comprends votre préoccupation. La dermatite allergique aux puces (DAPP) est la cause la plus fréquente de démangeaisons chez le chien — vérifiez si votre chien est à jour dans son antiparasitaire.

**Soins immédiats :**
• Antiparasitaire anti-puces adapté au poids
• Traitement de l'environnement (spray maison)
• Shampoing doux
• Consultation vétérinaire si pas d'amélioration en 1 semaine

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Dermatite allergique — Consultez dans les 2-3 jours**

Je vous entends. Le frottement, le léchage et les rougeurs cutanées évoquent une **réaction allergique** qui nécessite d'identifier l'allergène (alimentaire, environnemental, puces) pour traiter efficacement.

**En attendant :**
• Antiparasitaire à jour
• Régime hypoallergénique (si allergie alimentaire suspectée)
• Shampoing doux
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Perte de poils — Investigation nécessaire**

Je comprends votre inquiétude. Une perte de poils en plaques peut avoir de nombreuses causes — **démodécie, teigne, hypothyroïdie, Cushing** — un examen vétérinaire avec éventuellement des analyses de sang permettra de faire le diagnostic.

**Soins à domicile :**
• Antiparasitaire préventif
• Pas de shampoing agressif
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Dermatite chronique — Traitement à adapter**

Je vous entends. Une dermatite qui dure depuis plus d'une semaine avec perte de poils nécessite un **diagnostic vétérinaire précis** pour éviter qu'elle ne s'aggrave ou ne s'infecte.

**Soins immédiats :**
• Antiparasitaire à jour
• Shampoing hypoallergénique doux
• Collerette si plaies ouvertes
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 4. Toux persistante – chien ──────────────────────────────────
{
"level":"MEDIUM","animal":"chien",
"symptoms":[
    "toux sèche persistante depuis 5 jours, active, mange bien",
    "toux en épisodes, surtout le matin et au réveil, pas de fièvre",
    "toux productive depuis 3 jours, mucus blanc, léger abattement",
    "toux nocturne récurrente, tirage trachéal, appétit conservé",
    "toux après exercice, légère dyspnée à l'effort, pas au repos",
],
"conditions":[
    "trachéobronchite infectieuse (toux du chenil), Bordetella",
    "collapsus trachéal, irritation chronique, allergie respiratoire",
    "bronchite chronique, infection virale, parasites pulmonaires",
    "reflux gastro-œsophagien avec toux, allergie saisonnière",
    "bronchopneumonie débutante, vers pulmonaires (Angiostrongylus)",
],
"cares":[
    "consultation vétérinaire dans les 2-3 jours — auscultation et traitement",
    "vétérinaire sous 48h — radiographie si toux productive",
    "consultation dans les 2-3 jours — antibiotiques si toux du chenil",
    "vétérinaire cette semaine — évaluation respiratoire et traitement adapté",
    "consultation dans les 3 jours — coproscopie si vers pulmonaires suspects",
],
"flags":[
    "détresse respiratoire, muqueuses bleutées",
    "sang dans les expectorations, fièvre élevée",
    "pneumonie, collapsus trachéal sévère",
    "perte de poids rapide, fatigue extrême",
    "toux productive abondante avec fièvre",
],
"outputs":[
"""📋 **Toux persistante — Consultation dans les 2-3 jours**

Je comprends votre inquiétude. Une toux qui dure plus de 5 jours chez un chien actif peut indiquer une **toux du chenil** (Bordetella) ou une irritation trachéale qui nécessite une évaluation vétérinaire.

**Soins à domicile :**
• Harnais au lieu du collier (réduit la pression trachéale)
• Environnement humide et sans fumée
• Limiter l'exercice intense
• Pas de collier serré

**Consultez le vétérinaire dans les 2-3 jours si :**
• La toux ne s'améliore pas
• Apparition de fièvre ou d'abattement
• Difficultés respiratoires

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Toux du chenil possible — Consultation recommandée**

Je vous entends. Une toux sèche après un contact avec d'autres chiens évoque fortement une **toux du chenil** (trachéobronchite infectieuse) — contagieuse mais généralement bénigne avec traitement.

**En attendant la consultation :**
• Harnais au lieu du collier
• Évitez le contact avec d'autres chiens (contagieux)
• Environnement calme et humide
• Consultation vétérinaire dans les 48-72h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Bronchite légère — Suivi recommandé**

Je comprends votre préoccupation. Une toux productive légère depuis 3 jours peut indiquer une **bronchite virale ou bactérienne** qui nécessite une évaluation vétérinaire et parfois des antibiotiques.

**Soins immédiats :**
• Harnais au lieu du collier
• Humidification de l'air (bol d'eau chaude dans la pièce)
• Limiter les efforts physiques
• Consultation vétérinaire dans les 48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Toux récurrente — Bilan respiratoire nécessaire**

Je vous entends. Une toux nocturne récurrente peut indiquer un **collapsus trachéal** (fréquent chez certaines races) ou un problème cardiaque — une consultation vétérinaire avec auscultation est recommandée.

**En attendant :**
• Harnais (jamais de collier)
• Évitez l'excitation excessive
• Environnement calme
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Toux à l'effort — Évaluation recommandée**

Je comprends votre préoccupation. Une toux apparaissant à l'effort peut indiquer un **problème cardiaque ou pulmonaire débutant** qui mérite une auscultation et éventuellement une radiographie thoracique.

**Soins immédiats :**
• Réduire l'intensité des exercices
• Harnais au lieu du collier
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Irritation trachéale — Mesures et consultation**

Je vous entends. Une toux sèche persistante peut indiquer une irritation de la trachée — un **harnais au lieu du collier** est la première mesure recommandée pour réduire la pression sur les voies respiratoires.

**Soins à domicile :**
• Harnais obligatoire
• Humidification de l'air
• Pas de tabac ni de parfums dans la pièce
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Toux chronique — Consultez cette semaine**

Je comprends votre inquiétude. Une toux qui dure depuis plus de 5 jours sans amélioration nécessite une **évaluation vétérinaire avec auscultation** pour déterminer si elle est d'origine infectieuse, allergique ou anatomique.

**En attendant :**
• Harnais
• Environnement sans fumée
• Limiter les efforts
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Vers pulmonaires possibles — Consultez sous 3 jours**

Je vous entends. Si votre chien mange des limaces ou des escargots, une toux persistante peut indiquer une infestation par **Angiostrongylus** (vers pulmonaires) — une coproscopie vétérinaire permettra de le confirmer.

**En attendant :**
• Empêchez votre chien de manger des limaces/escargots
• Antiparasitaire si non récent
• Consultation vétérinaire dans les 3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Allergie respiratoire — Mesures simples**

Je comprends votre préoccupation. Une toux saisonnière peut indiquer une **allergie aux pollens** — des mesures simples peuvent améliorer la situation en attendant la consultation.

**Soins immédiats :**
• Réduire les sorties aux heures de fort pollen
• Nettoyer les pattes après les promenades
• Évitez la fumée et les parfums
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Toux — Évaluation vétérinaire recommandée**

Je vous entends. Une toux persistante depuis plusieurs jours mérite une **évaluation vétérinaire avec auscultation** pour en identifier la cause et choisir le traitement adapté.

**En attendant :**
• Harnais au lieu du collier
• Environnement calme et humide
• Limiter les exercices intenses
• Consultation vétérinaire dans les 2-3 jours

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 5. Perte d'appétit modérée – chat ────────────────────────────
{
"level":"MEDIUM","animal":"chat",
"symptoms":[
    "mange 50% de sa ration habituelle depuis 3 jours, mais boit normalement",
    "moins d'appétit depuis 2 jours, actif, pas de vomissement",
    "anorexie partielle depuis hier, boit, comportement normal",
    "mange peu depuis 3 jours mais boit et utilise la litière normalement",
    "appétit diminué de moitié depuis 2 jours, léger abattement, pas de fièvre",
],
"conditions":[
    "stress, changement d'environnement, préférence alimentaire",
    "infection débutante, douleur dentaire, problème rénal léger",
    "chaleur, changement de saison, allergie alimentaire",
    "anxiété, territoire perturbé, compétition alimentaire",
    "trouble digestif léger, parasites intestinaux",
],
"cares":[
    "surveillance 48h — si persistance, consultation vétérinaire",
    "vétérinaire si anorexie totale ou > 48h",
    "consultation dans les 3 jours si pas d'amélioration",
    "stimuler l'appétit + consultation si persistance 48h",
    "bilan vétérinaire si anorexie persiste > 2 jours",
],
"flags":[
    "anorexie totale > 24h — risque de lipidose hépatique chez le chat",
    "léthargie sévère, vomissements, perte de poids rapide",
    "ictère (jaunisse), soif excessive",
    "anurie ou dysurie associée",
    "prostration, fièvre élevée",
],
"outputs":[
"""📋 **Appétit diminué — Surveillez 48h**

Je comprends votre inquiétude pour votre chat. Une diminution modérée de l'appétit depuis 2-3 jours chez un chat actif peut avoir de nombreuses causes bénignes — **stress, préférence alimentaire, chaleur**.

**Ce que vous pouvez faire :**
• Proposez des aliments différents (boîte, sachets appétents)
• Réchauffez légèrement la nourriture pour accentuer l'odeur
• Environnement calme et sans stress
• Surveillez pendant 48h

**Consultez le vétérinaire si :**
• Anorexie totale pendant plus de 24h
• Apparition de vomissements ou léthargie
• Jaunissement de la peau ou des yeux

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Anorexie partielle — Surveillance recommandée**

Je vous entends. Un chat qui mange moins depuis 2-3 jours mais qui reste actif et boit normalement peut simplement traverser une **phase de caprice ou de stress** — une surveillance de 48h est raisonnable.

**Mesures à prendre :**
• Variez les aliments proposés
• Réchauffez la nourriture pour la rendre plus appétissante
• Endroit calme pour manger
• Évitez tout changement brutal dans l'environnement

**Consultez le vétérinaire si :**
• Anorexie totale > 24h (lipidose hépatique possible)
• Vomissements ou léthargie associés

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Manque d'appétit — Stimulation et surveillance**

Je comprends votre préoccupation. Un chat qui mange peu depuis 2-3 jours sans autres symptômes peut répondre à des mesures simples de **stimulation de l'appétit** avant de nécessiter une consultation.

**Stimulation de l'appétit :**
• Nourriture humide chaude (plus odorante)
• Petites quantités fréquentes
• Aliments différents (thon, saumon en boîte)
• Endroit calme et sécurisé

**Urgence si anorexie totale > 24h** (risque de lipidose hépatique).

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Caprice ou trouble léger — Observez 48h**

Je vous entends. Un chat qui mange moins sans autres symptômes est souvent en phase de **sélectivité alimentaire ou de stress** — une surveillance de 48h est généralement appropriée.

**Ce que vous pouvez faire :**
• Variez les aliments
• Nourriture légèrement réchauffée
• Calme et tranquillité autour de la gamelle
• Consultez si anorexie totale > 24h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Appétit réduit — Consultez si persistance**

Je comprends votre inquiétude. Une diminution d'appétit de 50% chez un chat actif et qui boit normalement est souvent **bénigne** — mais mérite surveillance pour ne pas évoluer vers une anorexie complète.

**Actions immédiates :**
• Nourriture humide appétissante
• Réchauffez légèrement
• Endroit calme pour manger
• Consultation vétérinaire si persistance > 48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Anorexie partielle féline — 48h de surveillance**

Je vous entends. Une réduction modérée de l'appétit chez un chat actif peut s'améliorer seule. La priorité est de **prévenir une anorexie totale** qui pourrait entraîner une lipidose hépatique.

**Mesures immédiates :**
• Nourriture variée et appétissante
• Portions petites et fréquentes
• Eau fraîche accessible
• Consultation si pas d'amélioration en 48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Inappétence — Stimulez et surveillez**

Je comprends votre inquiétude. Un chat qui mange peu sans autres symptômes peut être stimulé par des **aliments hautement appétents** (nourriture humide chaude, thon en boîte) avant de nécessiter une consultation.

**Soins à domicile :**
• Nourriture humide légèrement chaude
• Aliments différents et appétissants
• Calme et tranquillité
• Surveillance pendant 48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Anorexie légère — Consultez dans les 3 jours**

Je vous entends. Une anorexie partielle qui dure plus de 2-3 jours chez un chat mérite une **consultation vétérinaire** pour exclure une douleur dentaire, une infection débutante ou un problème rénal.

**En attendant :**
• Nourriture humide appétissante
• Réchauffée légèrement
• Eau fraîche accessible
• Consultation dans les 2-3 jours si pas d'amélioration

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Caprice alimentaire — Mesures simples**

Je comprends votre préoccupation. Avant de consulter, quelques mesures simples peuvent stimuler l'appétit de votre chat et résoudre une **inappétence passagère**.

**Essayez :**
• Nourriture différente de la marque habituelle
• Légèrement réchauffée au micro-ondes (5 secondes)
• Petites quantités plusieurs fois par jour
• Consultez si aucune amélioration en 48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""📋 **Appétit réduit — Vigilance recommandée**

Je vous entends. Une réduction d'appétit chez le chat nécessite une **surveillance attentive** car il peut développer rapidement une lipidose hépatique si l'anorexie s'installe.

**Actions immédiates :**
• Stimulez l'appétit (nourriture chaude et variée)
• Surveillez la consommation quotidienne
• Consultez le vétérinaire si anorexie totale > 24h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

]  # fin MEDIUM

# ─────────────────────────────────────────────────────────────────
LOW = [

# ── 1. Vomissement herbe – chat ──────────────────────────────────
{
"level":"LOW","animal":"chat",
"symptoms":[
    "vomissement d'herbe, 1-2 fois par semaine, mange normalement après",
    "régurgitation d'herbe et de poils, comportement normal, actif",
    "avale de l'herbe et vomit, sans autre symptôme, appétit conservé",
    "vomit de l'herbe le matin, mange normalement le reste du temps",
    "ingestion d'herbe suivie de vomissement, boit et mange normalement",
],
"conditions":[
    "comportement normal — élimination naturelle des poils ingérés",
    "régurgitation physiologique — mécanisme naturel de nettoyage digestif",
    "comportement instinctif d'élimination des irritants gastriques",
    "réflexe naturel de purge — comportement tout à fait normal chez le chat",
    "mécanisme d'autopurge — vomissement d'herbe est un comportement sain",
],
"cares":[
    "surveillance simple — aucun traitement nécessaire si comportement isolé",
    "pas de traitement — herbe à chat disponible si souhaité",
    "surveillance — consultez si vomissements quotidiens ou avec sang",
    "aucune action requise — comportement naturel et sain",
    "pas de consultation nécessaire — surveillance des signes d'alarme suffisante",
],
"flags":[
    "vomissements quotidiens, présence de sang, perte de poids",
    "anorexie associée, léthargie, perte de poids",
    "vomissements très fréquents ou avec sang",
    "corps étranger possible (ficelle, plastique)",
    "vomissements persistants associés à une perte d'appétit",
],
"outputs":[
"""✅ **Rien d'inquiétant pour le moment**

Rassurez-vous — vomir de l'herbe occasionnellement est un **comportement tout à fait normal** chez le chat. C'est un mécanisme naturel pour éliminer les poils ingérés lors de la toilette et les irritants digestifs.

**Pas d'inquiétude si :**
• Il mange et boit normalement après
• Il reste actif et joueur
• Les vomissements restent occasionnels (1-2 fois par semaine maximum)

**Consultez si vous observez :**
• Vomissements quotidiens ou très fréquents
• Présence de sang dans les vomissements
• Perte de poids ou léthargie associée

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Comportement naturel — Pas d'inquiétude**

Je vous rassure — l'ingestion d'herbe et les vomissements occasionnels qui s'ensuivent sont un **comportement instinctif et sain** chez le chat. Il utilise l'herbe comme aide naturelle à la purge digestive.

**C'est normal si :**
• Cela arrive 1-2 fois par semaine maximum
• Votre chat mange normalement après
• Son comportement général est inchangé

**Consultez si :**
• Cela devient quotidien
• Présence de sang
• Votre chat perd du poids

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Autopurge physiologique — Aucun traitement requis**

Rassurez-vous ! Ce que vous décrivez est un **comportement tout à fait normal et sain** chez le chat. Les chats ingèrent de l'herbe pour faciliter l'élimination des poils avalés lors de leur toilette.

**Vous pouvez :**
• Proposer de l'herbe à chat (blé germé, herbe spéciale chat) en pot
• C'est sans risque et souvent très apprécié

**Surveillez simplement :**
• La fréquence des vomissements (quotidien = à évaluer)
• La présence éventuelle de sang

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Normal — Mécanisme de purge naturel**

Je vous rassure. Vomir de l'herbe est un **réflexe naturel** que les chats utilisent pour expulser les poils et irritants digestifs. Ce comportement, pratiqué 1 à 2 fois par semaine, est tout à fait sain.

**Aucune action nécessaire si :**
• Appétit et comportement normaux après le vomissement
• Fréquence occasionnelle (pas quotidienne)

**Consultez si :**
• Vomissements quotidiens
• Sang dans les vomissements
• Perte de poids

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Comportement sain — Aucun traitement**

Soyez rassuré(e). L'ingestion d'herbe suivie de vomissements est un **comportement evolutivement sain** chez le chat — son ancêtre sauvage faisait de même pour purger son système digestif.

**Ce que vous pouvez faire :**
• Proposer de l'herbe à chat cultivée en pot (plus saine que l'herbe de jardin)
• Observer que l'appétit reste normal après

**Consultez si vomissements très fréquents ou sang.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Purge naturelle — Aucune inquiétude**

Je vous rassure entièrement. Votre chat utilise l'herbe comme un **outil naturel de purge digestive** — c'est un comportement instinctif parfaitement normal chez l'espèce féline.

**Aucune consultation nécessaire si :**
• Fréquence 1-2 fois par semaine
• Appétit normal après
• Comportement inchangé

**Pensez à proposer de l'herbe à chat en pot** — c'est plus sûr que l'herbe de jardin traitée.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Tout va bien — Comportement normal**

Rassurez-vous. Ce comportement est **absolument normal** chez le chat. Il ingère de l'herbe volontairement pour stimuler le vomissement et expulser les poils accumulés dans son estomac.

**Pas d'inquiétude si :**
• Occasionnel (1-2 fois/semaine)
• Appétit conservé
• Comportement normal

**Astuce :** proposez de l'herbe à chat en pot intérieur pour éviter l'herbe traitée du jardin.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Réflexe naturel — Aucune action requise**

Je vous rassure — votre chat va bien. L'ingestion d'herbe et les vomissements qui suivent constituent un **mécanisme d'autoentretien digestif** tout à fait normal et sain chez le chat.

**Ce comportement est normal :**
• 1-2 fois par semaine maximum
• Après la toilette (élimination des poils)
• Sans autre symptôme associé

**Consultez uniquement si :** vomissements quotidiens ou présence de sang.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Comportement instinctif — Aucune inquiétude**

Soyez rassuré(e). Ce que vous observez chez votre chat est un **comportement parfaitement normal** — il utilise l'herbe pour faciliter l'expulsion des poils ingérés et nettoyer son système digestif.

**C'est sain si :**
• Cela reste occasionnel
• L'appétit est conservé après
• Pas d'autres symptômes

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Purge digestive — Comportement sain**

Je vous rassure entièrement. Votre chat utilise l'herbe comme une aide naturelle à la purge — c'est un **comportement instinctif sain** que pratiquent la grande majorité des chats.

**Aucune action requise** si :
• Appétit normal après le vomissement
• Comportement inchangé
• Fréquence occasionnelle

**Proposez de l'herbe à chat en pot** si vous souhaitez lui offrir une herbe sûre et non traitée.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 2. Éternuements occasionnels – chat ──────────────────────────
{
"level":"LOW","animal":"chat",
"symptoms":[
    "éternuements 2-3 fois par jour, pas de sécrétions, comportement normal",
    "éternuements occasionnels depuis quelques jours, mange et boit normalement",
    "série d'éternuements le matin, sans fièvre ni sécrétions",
    "éternuements ponctuels après exposition à la poussière, comportement normal",
    "quelques éternuements par jour, nez légèrement humide, actif et joueur",
],
"conditions":[
    "irritation nasale légère, allergie saisonnière, poussière",
    "rhinite légère passagère, irritant inhalé",
    "allergie environnementale légère, pollen, poussière",
    "irritation des voies nasales supérieures — pas d'infection",
    "réaction légère à un irritant ambiant (produit ménager, parfum)",
],
"cares":[
    "surveillance simple — aérer et dépoussiérer l'environnement",
    "réduire les irritants ambiants + surveillance 48-72h",
    "aucun traitement — surveillance des signes d'alarme",
    "améliorer la ventilation + consultation si persistance > 1 semaine",
    "aucune action requise sauf si persistance ou aggravation",
],
"flags":[
    "écoulements nasaux colorés (jaune/vert), fièvre, perte d'appétit",
    "calicivirus/herpèsvirus félin — éternuements + yeux + fièvre",
    "corps étranger dans le nez, éternuements en jets",
    "écoulements sanguins, difficultés respiratoires",
    "chlamydiose, coryza — éternuements persistants + conjonctivite",
],
"outputs":[
"""✅ **Éternuements occasionnels — Aucune inquiétude immédiate**

Je vous rassure. Des éternuements ponctuels sans sécrétions colorées ni fièvre sont généralement causés par une **irritation légère des voies nasales** — poussière, produit ménager, pollen. C'est bénin dans la grande majorité des cas.

**Ce que vous pouvez faire :**
• Aérez régulièrement la pièce où vit votre chat
• Réduisez les produits parfumés ou désinfectants forts
• Pas de litière parfumée
• Dépoussiérez régulièrement

**Consultez le vétérinaire si :**
• Les éternuements persistent plus de 1 semaine
• Apparition de sécrétions colorées (jaunes/vertes)
• Fièvre ou perte d'appétit associées

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Irritation nasale légère — Surveillance simple**

Je vous rassure. Des éternuements occasionnels chez un chat actif et qui mange bien sont rarement le signe d'une maladie grave. Il s'agit probablement d'une **irritation nasale légère** due à l'environnement.

**Mesures simples :**
• Aérez les pièces régulièrement
• Évitez les sprays ménagers près de votre chat
• Litière non parfumée
• Surveillance pendant 48-72h

**Consultez si :**
• Sécrétions colorées
• Perte d'appétit
• Fièvre

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Éternuements passagers — Pas d'inquiétude**

Soyez rassuré(e). Des éternuements quelques fois par jour sans autre symptôme chez un chat actif sont le plus souvent causés par un **irritant ambiant** — poussière, pollen, produit ménager — et se résolvent spontanément.

**Actions préventives :**
• Aérez bien les pièces
• Évitez les produits parfumés
• Changez la litière vers une variété non parfumée

**Consultez si persistance > 1 semaine ou apparition de sécrétions.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Allergie légère probable — Aucun traitement urgent**

Je vous rassure. Des éternuements saisonniers chez un chat qui va bien par ailleurs évoquent une **allergie légère aux pollens ou à la poussière** — bénigne et souvent transitoire.

**Ce que vous pouvez faire :**
• Aérer tôt le matin (moins de pollen)
• Passer l'aspirateur régulièrement
• Évitez de fumer à l'intérieur

**Consultez si les éternuements persistent > 1 semaine ou s'aggravent.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Éternuements réactionnels — Surveillance**

Je vous rassure. Des éternuements après exposition à la poussière sont une **réaction normale** des voies nasales à un irritant — c'est le mécanisme de défense naturel de l'organisme.

**Mesures simples :**
• Dépoussiérez régulièrement l'environnement
• Aérez les pièces quotidiennement
• Pas de produits parfumés à proximité

**Consultez si persistance > 1 semaine.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Rhinite légère — Pas d'urgence**

Je vous rassure. Une légère rhinite passagère avec éternuements occasionnels est courante chez les chats, surtout en période de changement de saison — c'est **bénin et souvent transitoire**.

**Soins simples :**
• Aérez la pièce
• Nettoyez délicatement le nez si nécessaire (coton humide)
• Surveillance pendant 48-72h

**Consultez si sécrétions colorées ou fièvre.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Irritant inhalé — Aucune action urgente**

Soyez rassuré(e). Des éternuements après une exposition à un parfum ou un produit ménager sont une **réaction normale et passagère** — votre chat va bien.

**Actions simples :**
• Aérez bien la pièce
• Évitez les produits parfumés à l'avenir
• Surveillance pendant 24-48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Éternuements bénins — Surveillance suffisante**

Je vous rassure. Des éternuements ponctuels sans fièvre ni sécrétions chez un chat actif et qui mange bien nécessitent seulement une **surveillance simple**.

**Ce que vous pouvez faire :**
• Améliorer la ventilation
• Réduire les irritants (fumée, parfums, litière parfumée)
• Surveiller pendant 48-72h

**Consultez si aggravation ou persistance > 1 semaine.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Allergie environnementale légère — Pas d'urgence**

Je vous rassure. Des éternuements réactionnels à l'environnement chez un chat par ailleurs en bonne santé sont bénins — il s'agit d'une **réaction immunitaire normale aux allergènes ambiants**.

**Mesures utiles :**
• Aération régulière
• Litière non parfumée
• Pas de sprays ménagers à proximité
• Surveillance pendant 1 semaine

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Éternuements — Aucune urgence médicale**

Je vous rassure. Des éternuements occasionnels sans autres symptômes chez un chat actif sont dans la très grande majorité des cas bénins — poussière, pollen ou irritant transitoire.

**Mesures simples :**
• Aérez les pièces
• Réduisez les irritants ambiants
• Surveillez pendant 48-72h

**Consultez si persistance > 1 semaine ou apparition de sécrétions colorées.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 3. Selles molles passagères – chien ─────────────────────────
{
"level":"LOW","animal":"chien",
"symptoms":[
    "selles légèrement molles depuis 24h, appétit conservé, actif",
    "diarrhée légère 1-2 fois aujourd'hui, mange normalement, boit bien",
    "selles moles sans sang depuis hier, comportement normal, actif",
    "légère modification des selles (plus molles), pas de sang, actif et joueur",
    "selles semi-liquides 2 fois ce matin, appétit normal, comportement inchangé",
],
"conditions":[
    "changement alimentaire récent, stress, indigestion passagère",
    "sensibilité alimentaire légère, parasites intestinaux légers",
    "transition alimentaire trop rapide, repas inhabituel",
    "stress (voyages, visite, bruit), changement d'eau",
    "indigestion légère, corps étranger non obstructif",
],
"cares":[
    "régime fade 24h + surveillance",
    "alimentation légère + eau fraîche + surveillance 48h",
    "aucun traitement — surveillance 24-48h",
    "diète légère puis reprise progressive",
    "surveillance 48h — consultation si persistance ou aggravation",
],
"flags":[
    "sang dans les selles, diarrhée > 48h, déshydratation",
    "vomissements associés, léthargie, fièvre",
    "chiot < 3 mois — risque vital de déshydratation rapide",
    "méléna (selles noires), hématochézie",
    "diarrhée profuse et répétée, collapsus",
],
"outputs":[
"""✅ **Diarrhée légère passagère — Pas d'inquiétude immédiate**

Rassurez-vous. Des selles légèrement molles pendant 24 heures chez un chien actif et qui mange bien sont souvent causées par un **changement alimentaire ou un léger stress** — elles se résolvent généralement seules avec quelques mesures simples.

**Soins à domicile :**
• Diète légère : riz blanc + poulet bouilli pendant 24h
• Eau fraîche disponible en permanence
• Pas de friandises ni restes de table
• Reprise progressive de l'alimentation habituelle

**Consultez si :**
• Sang dans les selles
• Diarrhée > 48h
• Vomissements ou léthargie associés

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Selles molles — Mesures simples suffisantes**

Je vous rassure. Une diarrhée légère et ponctuelle chez un chien actif et qui se comporte normalement nécessite seulement un **régime alimentaire léger** pendant 24 heures.

**Mesures simples :**
• Riz blanc + poulet bouilli sans assaisonnement
• Eau fraîche abondante
• Pas de changement alimentaire supplémentaire
• Surveillance pendant 48h

**Consultez si :**
• Diarrhée persistante > 48h
• Sang dans les selles
• Votre chien devient léthargique

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Indigestion légère — Régime et surveillance**

Soyez rassuré(e). Des selles molles passagères chez un chien actif qui mange bien sont bénignes et se résolvent généralement en 24-48h avec un régime alimentaire adapté.

**Régime recommandé :**
• Riz blanc + poulet bouilli (sans sel, sans épices)
• Petites quantités fréquentes
• Eau fraîche en permanence
• Probiotiques vétérinaires si disponibles

**Consultez si persistance > 48h ou apparition de sang.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Diarrhée légère — Pas d'urgence**

Je vous rassure. Des selles semi-liquides ponctuelles chez un chien actif et qui boit bien sont dans la grande majorité des cas **bénignes et transitoires** — elles se résolvent avec quelques mesures diététiques.

**Soins à domicile :**
• Alimentation légère (riz + poulet)
• Eau fraîche abondante
• Surveillance pendant 48h

**Consultez si aggravation, sang ou léthargie.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Sensibilité alimentaire passagère — Régime**

Je vous rassure. Une modification des selles après un repas inhabituel ou un stress est courante et bénigne — un **régime légère de 24h** permettra généralement à l'intestin de récupérer.

**Mesures simples :**
• Riz + poulet bouilli
• Eau fraîche
• Évitez les friandises pendant 2-3 jours

**Consultez si diarrhée persistante > 48h.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Trouble digestif bénin — Surveillance suffisante**

Soyez rassuré(e). Des selles légèrement molles chez un chien actif ne nécessitent pas de consultation immédiate — un **régime alimentaire doux** pendant 24 heures est généralement suffisant.

**Régime adapté :**
• Riz blanc + poulet bouilli
• Eau fraîche disponible
• Pas de graisses ni épices
• Surveillance 48h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Diarrhée légère — Régime fade**

Je vous rassure. Des selles molles sans sang chez un chien actif sont bénignes dans la grande majorité des cas — un régime fade pendant 24-48h suffit généralement.

**Soins simples :**
• Riz + poulet bouilli pendant 24h
• Eau fraîche abondante
• Reprise progressive après amélioration

**Consultez si sang ou persistance > 48h.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Intestin sensible — Pas d'urgence**

Je vous rassure. Des selles molles ponctuelles chez un chien par ailleurs en bonne santé sont courantes et bénignes — elles se résolvent spontanément ou avec un régime léger.

**Ce que vous pouvez faire :**
• Alimentation légère 24h (riz + poulet)
• Eau fraîche disponible
• Surveillance de l'évolution

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Modification légère des selles — Aucune urgence**

Soyez rassuré(e). Une légère modification des selles pendant 24 heures chez un chien actif est **très courante et généralement sans gravité** — souvent liée à un changement alimentaire ou à un stress passager.

**Mesures simples :**
• Régime riz + poulet 24h
• Eau fraîche abondante
• Surveillance

**Consultez si sang ou diarrhée > 48h.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Selles molles — Mesures diététiques suffisantes**

Je vous rassure. Des selles légèrement molles sans autres symptômes chez un chien actif nécessitent seulement un **régime alimentaire léger** pendant 24 heures.

**Régime recommandé :**
• Riz blanc + poulet bouilli
• Eau fraîche disponible en permanence
• Pas de friandises

**Consultez si persistance ou aggravation.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 4. Légère prise de poids – chien ────────────────────────────
{
"level":"LOW","animal":"chien",
"symptoms":[
    "prise de poids de 1-2 kg en 3 mois, actif, mange normalement",
    "léger surpoids, côtes peu palpables, actif et en bonne santé",
    "prise de poids progressive depuis 6 mois, alimentation inchangée",
    "embonpoint léger, moins d'activité physique depuis l'hiver",
    "légère surcharge pondérale, côtes palpables avec effort, actif",
],
"conditions":[
    "surpoids modéré lié à l'alimentation ou à la sédentarité",
    "embonpoint post-castration, sédentarité hivernale",
    "surpoids alimentaire, portions excessives ou friandises trop fréquentes",
    "prise de poids physiologique, alimentation non adaptée à l'âge",
    "surpoids modéré, possible hypothyroïdie si progression rapide",
],
"cares":[
    "réduire les portions + augmenter l'exercice + consultation annuelle",
    "régime alimentaire adapté + exercice physique régulier",
    "alimentation spéciale poids + promenades quotidiennes",
    "consultation vétérinaire pour programme de perte de poids adapté",
    "bilan thyroïdien si prise de poids inexpliquée + régime",
],
"flags":[
    "prise de poids rapide inexpliquée — hypothyroïdie, Cushing",
    "abdomen fortement distendu, ascite",
    "essoufflement à l'effort, problème cardiaque",
    "prise de poids > 20% du poids idéal — consultation urgente",
    "léthargie sévère, perte de poils associée — trouble hormonal",
],
"outputs":[
"""✅ **Surpoids modéré — Mesures préventives simples**

Je comprends votre préoccupation. Une légère prise de poids chez un chien actif peut souvent être gérée avec des **mesures simples** avant de nécessiter une consultation vétérinaire.

**Mesures à prendre :**
• Réduisez les portions de 10-15%
• Limitez les friandises (comptez-les dans la ration quotidienne)
• Augmentez la durée des promenades de 10-15 minutes
• Alimentation "light" si votre chien est castré

**Consultez le vétérinaire lors de la prochaine visite annuelle** pour un plan de gestion du poids adapté.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Embonpoint léger — Régime et exercice**

Je vous rassure. Un léger surpoids sans autres symptômes peut souvent être corrigé par des **ajustements simples** de l'alimentation et de l'activité physique.

**Actions simples :**
• Réduire les portions de 10-15%
• Arrêter ou limiter sévèrement les friandises
• Promenades quotidiennes plus longues
• Alimentation "light" ou "senior" selon l'âge

**Consultez si :** prise de poids rapide inexpliquée ou léthareige associée.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Prise de poids modérée — Ajustements nécessaires**

Je comprends votre inquiétude. Un léger surpoids chez un chien actif peut être corrigé en **ajustant l'alimentation et l'exercice** — pas besoin de consultation urgente.

**Ce que vous pouvez faire :**
• Peser précisément les repas (pas "à vue")
• Réduire de 10-15%
• Supprimer les friandises
• 2 promenades/jour d'au moins 30 minutes

**Consultez si pas d'amélioration après 2 mois de régime.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Surpoids post-castration — Fréquent et gérable**

Je vous rassure. La prise de poids après castration est très fréquente chez les chiens — les besoins énergétiques diminuent de 20-30%. Un **ajustement des portions** est souvent suffisant.

**Mesures recommandées :**
• Alimentation "light" spéciale chien castré
• Réduire les portions de 20%
• Exercice régulier maintenu
• Consultation annuelle pour suivi du poids

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Sédentarité hivernale — Reprendre l'activité**

Je comprends votre préoccupation. Un léger surpoids dû à une réduction d'activité hivernale est courant — la **reprise de l'exercice** au printemps suffit généralement à corriger la situation.

**Actions simples :**
• Augmenter progressivement l'exercice
• Réduire légèrement les portions
• Supprimer les friandises

**Consultez si prise de poids inexpliquée ou rapide.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Embonpoint — Corriger l'alimentation**

Je vous rassure. Un léger surpoids sans autres symptômes se corrige généralement bien avec des **ajustements alimentaires simples** sans nécessiter de consultation urgente.

**Ce que vous pouvez faire :**
• Pesez précisément les portions
• Réduire de 10-15%
• Limiter les friandises
• Exercice quotidien régulier

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Surpoids léger — Plan de gestion simple**

Je comprends votre préoccupation. Un léger surpoids chez un chien actif peut être géré efficacement avec un **plan simple** d'alimentation et d'exercice.

**Plan recommandé :**
• Alimentation mesurée précisément
• Réduction de 10-15% des portions
• Suppression des friandises
• Promenades quotidiennes

**Consultez le vétérinaire lors de la prochaine visite pour un suivi.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Prise de poids — Mesures préventives**

Je vous rassure. Un léger surpoids sans symptômes associés peut être corrigé par des **mesures alimentaires simples** — pas besoin de consultation urgente.

**Mesures simples :**
• Réduire les portions de 10-15%
• Exercice quotidien régulier
• Limiter les friandises
• Alimentation adaptée à l'âge

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Embonpoint léger — Ajustements nécessaires**

Je comprends votre inquiétude. Un léger surpoids est gérable avec des ajustements simples. La priorité est de **mesurer précisément les portions** plutôt que de les estimer à vue.

**Actions immédiates :**
• Pesez les repas avec une balance
• Réduire de 10-15% si nécessaire
• Exercice quotidien régulier
• Bilan vétérinaire annuel pour suivi

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Surpoids modéré — Prévention des complications**

Je vous rassure. Un léger surpoids bien géré n'entraîne pas de complications — l'important est d'agir **maintenant** pour éviter une obésité plus difficile à traiter.

**Plan simple :**
• Peser les portions
• Réduire de 10-15%
• Exercice régulier
• Consultation annuelle pour suivi du poids idéal

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 5. Grattage léger – chien ────────────────────────────────────
{
"level":"LOW","animal":"chien",
"symptoms":[
    "grattage occasionnel derrière les oreilles, peau saine, pas de rougeur",
    "se gratte 2-3 fois par jour, pelage en bon état, pas de lésions",
    "grattage ponctuel du ventre, peau normale, actif et joueur",
    "léger grattage saisonnier, pas de perte de poils, peau rose saine",
    "se gratte de temps en temps, pas de rougeur ni de plaie, comportement normal",
],
"conditions":[
    "grattage physiologique normal, légère irritation cutanée passagère",
    "réaction légère aux pollens ou à l'environnement",
    "irritation cutanée minime, poil en croissance",
    "grattage comportemental, léger inconfort passager",
    "réaction légère à un shampoing ou produit de soin",
],
"cares":[
    "surveillance simple — antiparasitaire à jour",
    "aucune action requise — surveillance des signes d'alarme",
    "vérifier antiparasitaire + surveillance",
    "aucun traitement nécessaire si peau saine",
    "surveillance 1-2 semaines — consultation si aggravation",
],
"flags":[
    "plaies ouvertes, perte de poils, peau très rouge",
    "grattage intense nocturne, lésions cutanées",
    "gale sarcoptique (aggravation rapide, très contagieux)",
    "infections cutanées secondaires, pyodermite",
    "automutilation, détresse comportementale",
],
"outputs":[
"""✅ **Grattage occasionnel — Aucune inquiétude**

Rassurez-vous. Un grattage ponctuel chez un chien dont la peau est saine et le pelage en bon état est parfaitement **normal** — c'est souvent une légère irritation transitoire ou une réaction à l'environnement.

**Ce que vous pouvez vérifier :**
• L'antiparasitaire est-il à jour ? (contre les puces)
• Y a-t-il des puces dans le pelage ? (peigne fin)
• Avez-vous changé un shampoing ou produit de soin récemment ?

**Consultez si :**
• Le grattage devient intense et fréquent
• Apparition de rougeurs ou de plaies
• Perte de poils

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Prurit léger — Surveillance simple**

Je vous rassure. Un grattage occasionnel sans lésions cutanées visibles est généralement bénin et transitoire — souvent lié à un **irritant environnemental passager** (poussière, pollen, produit ménager).

**Mesures simples :**
• Vérifiez que l'antiparasitaire est à jour
• Examinez la peau (pas de rougeur, pas de pustules ?)
• Évitez les produits parfumés au contact du chien

**Consultez si aggravation ou lésions cutanées.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Grattage physiologique — Aucun traitement**

Je vous rassure. Un grattage ponctuel de 2-3 fois par jour chez un chien actif et dont la peau est saine est dans la très grande majorité des cas **bénin** — c'est souvent une simple réaction légère à l'environnement.

**Vérifiez simplement :**
• Antiparasitaire à jour
• Peau saine (pas de rougeur)
• Pas de puces dans le pelage

**Consultez si le grattage s'intensifie ou si des lésions apparaissent.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Irritation cutanée légère — Aucune urgence**

Je vous rassure. Un grattage saisonnier léger chez un chien dont la peau est saine et le pelage intact est **bénin** — il peut s'agir d'une légère allergie aux pollens de saison.

**Ce que vous pouvez faire :**
• Vérifiez l'antiparasitaire
• Brossage régulier pour éliminer les allergènes du pelage
• Surveillance pendant 1-2 semaines

**Consultez si aggravation.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Grattage bénin — Surveillance suffisante**

Soyez rassuré(e). Un grattage occasionnel sans lésions cutanées chez un chien actif ne nécessite pas de consultation immédiate — une **surveillance simple** pendant 1-2 semaines est appropriée.

**Ce à vérifier :**
• Antiparasitaire à jour
• Peau saine et pelage intact
• Pas de changement alimentaire ou de produits de soin récent

**Consultez si le grattage s'intensifie.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Prurit mineur — Aucun traitement urgent**

Je vous rassure. Un grattage ponctuel chez un chien dont la peau est rose et saine est **physiologiquement normal** — pas besoin de consultation urgente.

**Vérifiez :**
• Antiparasitaire à jour
• Peau sans rougeur ni lésion
• Pas de puces

**Consultez si aggravation ou plaies.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Grattage léger — Normal et bénin**

Je vous rassure. Des grattages ponctuels sans lésions ni perte de poils sont **normaux** chez un chien sain — c'est souvent une réaction à une légère irritation passagère.

**Actions simples :**
• Vérifiez l'antiparasitaire
• Examinez la peau
• Surveillance pendant 1-2 semaines

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Grattage saisonnier — Surveillance**

Je comprends votre préoccupation. Un grattage léger en période pollinique est courant et bénin — c'est souvent une **réaction allergique légère et transitoire** aux pollens.

**Mesures simples :**
• Brossage régulier après les promenades
• Évitez les promenades aux heures de fort pollen
• Antiparasitaire à jour

**Consultez si le grattage s'intensifie.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Prurit léger passager — Aucune urgence**

Soyez rassuré(e). Un grattage de temps en temps chez un chien dont la peau et le pelage sont en bon état ne nécessite pas de consultation urgente — c'est souvent une **irritation bénigne et transitoire**.

**Vérifications simples :**
• Antiparasitaire à jour
• Peau saine sans rougeur
• Pas de changement dans l'environnement

**Consultez si aggravation.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""✅ **Grattage — Aucune intervention nécessaire**

Je vous rassure. Un grattage ponctuel sans lésions chez un chien actif est **bénin dans la très grande majorité des cas** — une surveillance simple pendant quelques jours est suffisante.

**Vérifiez simplement :**
• Antiparasitaire à jour
• Peau saine
• Pas de puces

**Consultez si grattage intense, plaies ou perte de poils.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

]  # fin LOW
