#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cheebo_high_scenarios.py  — Scénarios HIGH pour generate_cheebo_dataset.py
"""

HIGH = [

# ── 1. Vomissement avec sang – chien ────────────────────────────
{
"level":"HIGH","animal":"chien",
"symptoms":[
    "vomissement avec présence de sang rouge vif, 3 fois en 2 heures",
    "vomi teinté de sang, léthargie associée, anorexie",
    "hématémèse — sang dans le vomi, abdomen sensible au toucher",
    "vomissement sanglant depuis le matin, faiblesse, déshydratation",
    "vomi brun foncé (aspect marc de café), douleur abdominale",
],
"conditions":[
    "ulcère gastrique hémorragique, gastro-entérite hémorragique",
    "ingestion corps étranger avec lésion muqueuse, hémorragie digestive haute",
    "gastrite hémorragique, possible intoxication",
    "hémorragie digestive haute, ulcération, coagulopathie possible",
    "gastroentérite hémorragique, AHDS (Acute Hemorrhagic Diarrhea Syndrome)",
],
"cares":[
    "consultation vétérinaire aujourd'hui — bilan sanguin et échographie",
    "consultation urgente dans les 4h — analgésie et réhydratation IV",
    "consultation vétérinaire urgente — endoscopie possible",
    "consultation dans les heures — mise à jeun et traitement symptomatique",
    "consultation vétérinaire aujourd'hui — antiémétiques et protection gastrique",
],
"flags":[
    "sang en grande quantité, gencives pâles, effondrement",
    "vomissements répétés, déshydratation sévère, léthargie extrême",
    "saignement qui s'aggrave, choc hémorragique",
    "selles noires (méléna) associées, faiblesse extrême",
    "sang en jets, perte de connaissance",
],
"outputs":[
"""⚠️ **Situation préoccupante — Consultez aujourd'hui**

Je comprends votre inquiétude — elle est tout à fait justifiée. La présence de sang dans les vomissements nécessite une **évaluation vétérinaire urgente aujourd'hui**, même si votre chien semble relativement stable.

**Soins immédiats :**
• Mise à jeun complète — aucune nourriture pendant 12h
• Eau fraîche en petites quantités si votre chien peut avaler
• Ne donnez aucun médicament humain (ibuprofène, aspirine = dangereux)
• Gardez un échantillon du vomi (photo ou bocal) pour le vétérinaire

**Consultez aujourd'hui si :**
• Le sang est en grande quantité
• Votre chien est très faible ou ne se lève plus

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Hématémèse — Consultation urgente requise**

Je comprends votre inquiétude. Le sang dans les vomissements peut indiquer un ulcère gastrique, une gastrite sévère ou une ingestion de corps étranger blessant — **une consultation vétérinaire aujourd'hui est nécessaire**.

**Ce que vous pouvez faire en attendant :**
• Arrêtez toute alimentation
• Eau fraîche accessible en petites quantités
• Photographiez les vomissements si possible
• Notez la fréquence et la quantité de sang

**Consultez en urgence immédiate si :**
• Le saignement augmente
• Gencives pâles ou léthargie extrême
• Selles noires apparaissent (méléna)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Sang dans les vomissements — Attention requise**

Cette situation mérite une attention rapide. L'hématémèse peut avoir des causes diverses — ulcère, corps étranger, intoxication — et nécessite un **bilan vétérinaire dans la journée**.

**Actions immédiates :**
• Mise à jeun stricte
• Eau fraîche en petites quantités toutes les heures
• Aucun anti-douleur ni anti-inflammatoire maison
• Photo du vomi pour le vétérinaire

**Urgence immédiate si :**
• Sang en grande quantité ou en jets
• Animal qui s'effondre ou gencives pâles

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Hémorragie digestive — Consultez aujourd'hui**

Je comprends votre préoccupation. Un vomissement sanglant répété nécessite une **évaluation vétérinaire rapide** — les causes peuvent être graves (ulcère hémorragique, AHDS) mais traitables si pris à temps.

**En attendant la consultation :**
• Arrêt complet de l'alimentation
• Eau fraîche en très petites quantités
• Repos complet
• Surveillance toutes les 30 minutes

**Allez aux urgences immédiatement si :**
• Vomi entièrement rouge
• Gencives qui pâlissent
• Animal qui ne peut plus se lever

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Gastrite hémorragique — Consultation urgente**

Je comprends votre inquiétude. Les vomissements sanglants sont un symptôme qui ne doit pas être ignoré. Une **consultation vétérinaire aujourd'hui** est indispensable pour évaluer l'origine du saignement.

**Soins conservateurs en attendant :**
• Aucune nourriture pendant 12h minimum
• Eau fraîche disponible en petites quantités
• Repos et environnement calme
• Note de la fréquence et quantité des vomissements

**Signes nécessitant une consultation immédiate :**
• Saignement massif
• Léthargie sévère, animal prostré
• Selles noires ou rouges

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Vomissement sanglant — Évaluation nécessaire**

Cette situation nécessite une attention médicale dans la journée. Les vomissements avec sang peuvent signaler une **lésion de la muqueuse gastrique** qui, sans traitement, peut s'aggraver.

**Mesures immédiates :**
• Mise à jeun complète
• Eau fraîche en petites quantités
• Ne manipulez pas l'abdomen
• Gardez votre chien au calme

**Passez aux urgences si :**
• Volume de sang important
• Gencives pâles ou bleutées
• Faiblesse extrême

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Hématémèse répétée — Consultez rapidement**

Je vous entends. La répétition des vomissements sanglants indique une irritation ou une lésion de la paroi digestive qui nécessite une **prise en charge vétérinaire dans les heures**.

**En attendant la consultation :**
• Suppression totale de l'alimentation
• Eau fraîche accessible
• Surveillance étroite de l'état général
• Photo des vomissements pour le vétérinaire

**Urgence immédiate si :**
• Sang abondant ou en augmentation
• Animal qui s'effondre
• Apparition de selles noires

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Saignement digestif — Bilan vétérinaire nécessaire**

Cette situation mérite une consultation vétérinaire aujourd'hui. Les vomissements sanguinolents peuvent indiquer un **ulcère gastrique, une gastroentérite hémorragique ou une ingestion de corps étranger**.

**Ce que vous pouvez faire :**
• Arrêtez l'alimentation immédiatement
• Eau fraîche en petites quantités toutes les heures
• Notez : fréquence des vomissements, quantité de sang, couleur
• Pas de médicaments humains

**Urgence absolue si :**
• Saignement qui augmente
• Gencives pâles ou grises
• Prostration

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Sang dans le vomi — Surveillance étroite**

Je comprends votre inquiétude. La présence de sang dans les vomissements est un signe qui mérite une **attention médicale dans la journée** — la cause peut aller de l'ulcère bénin à la lésion sévère.

**Actions à prendre :**
• Mise à jeun stricte
• Eau fraîche en petites gorgées
• Repos total
• Photographie du vomi pour le vétérinaire

**Consultez en urgence si :**
• Saignement abondant ou rouge vif
• Faiblesse marquée
• Selles deviennent noires

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Gastrite hémorragique suspectée — Consultez aujourd'hui**

Je vous entends et votre inquiétude est justifiée. Des vomissements répétés avec sang nécessitent un **examen vétérinaire dans les heures qui viennent** — un traitement précoce améliore significativement le pronostic.

**En attendant la consultation :**
• Jeûne complet
• Eau fraîche accessible
• Surveillance des selles (selles noires = méléna = urgence)
• Notez l'évolution toutes les 30 minutes

**Bilan que le vétérinaire va probablement faire :**
• Prise de sang
• Échographie abdominale
• Traitement antiémétique et gastroprotecteur

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 2. Anorexie lapin > 12h ──────────────────────────────────────
{
"level":"HIGH","animal":"lapin",
"symptoms":[
    "anorexie depuis 18h, selles rares et petites, légère léthargie",
    "refus de manger depuis 14h, moins de selles que d'habitude, calme inhabituel",
    "ne mange plus depuis hier soir, selles irrégulières, position cambrée",
    "anorexie 16h, rares selles, lapin moins actif que d'habitude",
    "refus du foin et légumes depuis 12h, quelques petites selles, apathie légère",
],
"conditions":[
    "début de stase digestive, douleur abdominale légère",
    "ralentissement du transit intestinal, possible début de stase GI",
    "hypomotilité gastro-intestinale, stress ou douleur dentaire possible",
    "stase GI débutante, facteur déclenchant : stress, changement alimentaire",
    "ralentissement digestif, possible malocclusion dentaire ou douleur",
],
"cares":[
    "consultation vétérinaire dans les 6h — procinétiques si stase confirmée",
    "vétérinaire NAC dans les 6-8h — bilan digestif et analgésie",
    "consultation NAC urgente — stimulation du transit nécessaire",
    "vétérinaire lapin dans la journée — évaluation dentaire et digestive",
    "consultation dans les 4-6h — réhydratation et motilité",
],
"flags":[
    "aucune selle depuis plus de 4h supplémentaires, abdomen gonflé",
    "grincements de dents, posture de douleur intense, abdomen dur",
    "stase avancée avec gaz, distension abdominale",
    "total arrêt du transit, détresse, urgence critique",
    "aucune selle en 6h + abdomen gonflé = urgence absolue",
],
"outputs":[
"""⚠️ **Situation préoccupante pour votre lapin**

Je comprends votre inquiétude pour votre lapin. Un refus de manger depuis 12 heures est un signal sérieux chez cette espèce — son transit doit être **continu et actif**. Un ralentissement précoce peut évoluer vers une stase complète.

**Soins à domicile en attendant :**
• Foin frais en grande quantité — la fibre est indispensable
• Eau fraîche accessible en permanence
• Chaleur douce : 24-26°C, pas de courant d'air
• Légère activité : encouragez-le à se déplacer doucement

**Consultez le vétérinaire NAC dans les 6h si :**
• Il refuse toujours de manger après 2-3h
• Les selles diminuent encore ou disparaissent
• Il adopte une position cambrée (signe de douleur)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Lapin anorexique — Attention requise**

Je vous entends. Un lapin qui ne mange pas depuis 12 à 18 heures commence à développer un ralentissement digestif qui peut rapidement devenir **une urgence**. Une consultation dans les 6 heures est recommandée.

**Ce que vous pouvez faire maintenant :**
• Foin premium disponible en permanence
• Eau fraîche — changez-la si nécessaire
• Température ambiante : 24-26°C
• Proposez ses légumes préférés (coriandre, persil) pour stimuler l'appétit

**Consultez rapidement si :**
• Pas d'amélioration dans 2-3h
• Abdomen qui gonfle légèrement
• Grincements de dents ou position cambrée

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Début de stase GI — Consultez dans les 6h**

Je comprends votre inquiétude. Chez le lapin, un refus de manger de 12 à 18 heures associé à une diminution des selles est le **signe précoce d'une stase gastro-intestinale**. Une intervention à ce stade permet souvent d'éviter une urgence critique.

**Mesures immédiates :**
• Foin frais en grande quantité (fibres = moteur digestif)
• Eau fraîche accessible
• Chaleur : 25°C minimum
• Encouragez-le à bouger doucement

**Passez en urgence si :**
• Aucune selle en 4h supplémentaires
• Abdomen qui gonfle ou devient dur
• Posture de douleur (ventre contre sol, dos cambré)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Ralentissement digestif lapin — Action requise**

Je comprends votre préoccupation. Le lapin est une espèce très fragile dont le transit ne doit jamais s'arrêter. Un refus de manger de 14 à 18 heures est un **signal d'alerte précoce** qu'il faut prendre au sérieux.

**Actions immédiates :**
• Foin frais illimité — priorité absolue
• Eau fraîche en permanence
• Chaleur douce et environnement calme
• Pas de changement alimentaire soudain

**Consultez le vétérinaire NAC dans les 6h :**
• Procinétiques (médicaments qui relancent le transit)
• Bilan abdominal
• Hydratation sous-cutanée si nécessaire

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Anorexie lapin — Surveillance urgente**

Je vous entends. Un lapin qui refuse de manger depuis 12 heures est en train de développer un **ralentissement digestif** qui peut rapidement devenir critique. Une consultation vétérinaire spécialisée NAC dans les 6 heures est recommandée.

**En attendant le vétérinaire :**
• Foin frais en grande quantité
• Eau fraîche
• Chaleur : 25-26°C
• Activité douce : sortez-le de sa cage pour qu'il se déplace

**Signes d'aggravation → passez en urgence :**
• Abdomen qui gonfle
• Grincements de dents
• Aucune selle depuis 4h supplémentaires

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Transit ralenti chez le lapin — Consultez aujourd'hui**

Cette situation mérite une attention rapide. Un lapin qui ne mange pas et produit peu de selles est en **hypomotilité digestive** — une étape qui précède souvent la stase complète.

**Soins immédiats :**
• Foin frais disponible en permanence
• Eau fraîche accessible
• Environnement chaud et calme
• Pas de changement de litière ou d'environnement

**Ne donnez pas :**
• Médicaments humains (toxiques pour le lapin)
• Alimentation forcée (peut aggraver la douleur)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Pré-stase lapin — Intervention précoce recommandée**

Je comprends votre préoccupation. Un lapin anorexique depuis 12 à 18 heures avec des selles irrégulières est en **début de ralentissement digestif**. Intervenir maintenant peut éviter une urgence critique dans les heures suivantes.

**Actions en attendant la consultation :**
• Foin premium : c'est la priorité absolue
• Eau fraîche en permanence
• Chaleur : 25°C minimum
• Mouvement léger pour stimuler le transit

**Consultez dans les 6h chez un vétérinaire NAC.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Lapin qui ne mange plus — Consultation dans les 6h**

Je vous entends. Cette situation demande une attention rapide. Chez le lapin, l'anorexie de plus de 12 heures peut évoluer vers une **stase digestive grave** si aucune mesure n'est prise.

**Soins à domicile :**
• Foin frais illimité
• Eau fraîche
• Température ambiante : 24-26°C
• Encouragez l'activité physique légère

**Signes qui nécessitent une urgence immédiate :**
• Aucune selle depuis 4-6h supplémentaires
• Abdomen gonflé ou dur
• Grincements de dents ou prostration

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Refus alimentaire lapin — Attention**

Je comprends votre inquiétude. Un lapin qui refuse de manger depuis plus de 12 heures développe progressivement une **hypomotilité digestive** qui, sans intervention, peut devenir une stase critique.

**Ce que vous devez faire maintenant :**
• Foin frais — priorité absolue, disponible en quantité illimitée
• Eau fraîche accessible en permanence
• Chaleur douce (25°C)
• Consultation NAC dans les 6h

**Information pour le vétérinaire :**
• Heure du dernier repas pris
• Quantité et aspect des selles actuelles
• Comportement général (actif, prostré, douloureux?)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Stase débutante chez le lapin — Agissez vite**

Je vous entends et votre inquiétude est justifiée. Un lapin qui n'a pas mangé depuis 12 à 18 heures est en **zone d'alerte**. Intervenir à ce stade précoce permet souvent d'éviter une urgence critique dans les heures suivantes.

**Actions immédiates :**
• Foin frais illimité (fibres = carburant du transit)
• Eau fraîche toujours disponible
• Chaleur douce et environnement calme
• Consultation vétérinaire NAC dans les 6h maximum

**Si dégradation :** urgences vétérinaires immédiatement.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 3. Boiterie sévère non-appui – chien ────────────────────────
{
"level":"HIGH","animal":"chien",
"symptoms":[
    "boiterie sévère, incapacité totale à poser la patte avant droite, douleur au toucher",
    "ne pose plus la patte arrière gauche, gémissements à la mobilisation, gonflement",
    "membre postérieur droit gonflé et chaud, boiterie complète, douleur intense",
    "patte avant gonflée, refus d'appui total, cri à la palpation",
    "boiterie aiguë soudaine, patte pendant, gonflement important, léchage intense",
],
"conditions":[
    "fracture, rupture ligamentaire, luxation articulaire",
    "rupture ligament croisé, fracture osseuse, luxation de hanche",
    "entorse sévère grade III, fracture de fatigue, dislocation",
    "trauma osseux, rupture tendineuse, fracture ouverte possible",
    "lésion articulaire sévère, fracture ou luxation rotule",
],
"cares":[
    "consultation vétérinaire aujourd'hui — radiographie nécessaire",
    "consultation urgente dans les 4h — immobilisation et antalgiques",
    "clinique vétérinaire aujourd'hui — bilan radiologique urgent",
    "vétérinaire aujourd'hui — évaluation orthopédique et imagerie",
    "consultation d'urgence — analgésie et immobilisation",
],
"flags":[
    "gonflement qui s'aggrave, chaleur intense, os visible",
    "déformation visible du membre, fracture ouverte, hémorragie",
    "perte totale de sensibilité du membre, choc",
    "plaie ouverte avec os visible, infection",
    "gonflement progressif rapide, ecchymose importante",
],
"outputs":[
"""⚠️ **Boiterie sévère — Consultez aujourd'hui**

Je comprends votre inquiétude. Une boiterie avec refus total d'appui peut indiquer une **fracture, une rupture ligamentaire ou une luxation** — des blessures qui nécessitent une imagerie et une prise en charge vétérinaire aujourd'hui.

**Soins immédiats :**
• Repos strict absolu — ne laissez pas votre chien marcher
• Si possible, portez-le pour se déplacer
• Glaçage de la zone (linge humide froid, 10 min max)
• Ne lui donnez aucun anti-douleur humain (ibuprofène = dangereux)

**Consultez aujourd'hui — ne pas attendre si :**
• Déformation visible du membre
• Gonflement qui augmente rapidement
• Plaie avec os visible

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Refus d'appui — Évaluation urgente nécessaire**

Je comprends votre préoccupation. Un chien qui ne pose plus du tout une patte souffre d'une **douleur significative** qui nécessite une radiographie pour en identifier la cause précise.

**Mesures immédiates :**
• Repos strict — aucun appui sur la patte
• Portez votre chien pour se déplacer
• Application de froid (15 min, enveloppé dans un tissu)
• Aucun médicament humain

**Consultez le vétérinaire aujourd'hui pour :**
• Radiographie
• Analgésie adaptée
• Immobilisation si fracture

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Lésion orthopédique — Consultation dans les 4h**

Cette situation nécessite une évaluation vétérinaire rapide. Un chien qui refuse tout appui depuis une blessure peut avoir une **fracture ou une rupture ligamentaire** — des lésions qui s'aggravent sans traitement approprié.

**Soins immédiats :**
• Immobilisation stricte — portez votre chien
• Glace enveloppée dans un tissu (10-15 min) sur la zone gonflée
• Environnement calme et reposant
• Pas d'ibuprofène ou aspirine

**Urgence immédiate si :**
• Déformation visible ou os qui pointe
• Plaie ouverte
• Gonflement extrêmement rapide

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Patte non fonctionnelle — Radiographie nécessaire**

Je vous entends. Un chien qui ne peut absolument pas poser une patte a besoin d'une **évaluation radiologique** pour exclure une fracture ou une luxation — ces lésions ne guérissent pas seules.

**En attendant la consultation :**
• Repos strict, aucun effort
• Portez votre chien pour se déplacer (même aux toilettes)
• Froid local : linge humide froid 10 minutes
• Pas de médicaments humains

**Information pour le vétérinaire :**
• Circonstances de la blessure (chute, collision, torsion)
• Depuis combien de temps
• Présence ou non de gonflement/chaleur

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Boiterie complète — Consultez aujourd'hui**

Je comprends votre inquiétude. Une boiterie soudaine avec refus d'appui total est souvent le signe d'une **lésion musculo-squelettique sévère** qui nécessite une imagerie vétérinaire dans la journée.

**Soins immédiats :**
• Repos absolu
• Transport en portant le chien
• Froid local si zone gonflée (10 min, tissu interposé)
• Aucun médicament humain anti-douleur

**Allez directement aux urgences si :**
• Déformation du membre
• Plaie avec os visible
• Chien en état de choc (gencives pâles, tremblements)

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Rupture ligamentaire ou fracture suspectée**

Je comprends votre préoccupation. Le refus d'appui total avec gonflement et douleur au toucher évoque fortement une **lésion structurelle sérieuse** du membre — radiographie indispensable.

**Actions immédiates :**
• Immobilisation complète du chien
• Portez-le pour tous les déplacements
• Froid local enveloppé dans un tissu
• Aucun médicament anti-douleur humain

**Consultez le vétérinaire aujourd'hui.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Trauma du membre — Évaluation vétérinaire urgente**

Je vous entends. Une patte gonflée, chaude et totalement non fonctionnelle après un traumatisme nécessite une **radiographie vétérinaire dans les heures**.

**Soins conservateurs :**
• Repos complet
• Transport en portant le chien
• Glaçage local 10-15 minutes
• Pas d'ibuprofène ni d'aspirine

**Ce que le vétérinaire va évaluer :**
• Radiographie pour fracture/luxation
• Palpation articulaire
• Traitement antalgique adapté

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Membre postérieur non fonctionnel — Consultez vite**

Cette situation mérite une attention médicale rapide. Un refus d'appui total peut indiquer une **rupture des ligaments croisés ou une fracture** — des conditions qui nécessitent souvent une chirurgie orthopédique.

**En attendant la consultation :**
• Repos absolu, portez votre chien
• Froid local si gonflé (tissu froid, 10 min max)
• Aucun médicament humain

**Urgence si :**
• Déformation visible
• Os visible ou plaie ouverte

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Boiterie sévère — Radiographie indispensable**

Je comprends votre préoccupation. Un chien qui refuse de poser une patte a probablement une **lésion osseuse ou articulaire** qui dépasse les soins à domicile. Une radiographie permettra de préciser le diagnostic.

**Soins immédiats :**
• Repos strict et immobilisation
• Transport porté
• Froid local si gonflement important
• Pas de médicaments anti-douleur humains

**Consultez le vétérinaire aujourd'hui.**

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Lésion osseuse ou articulaire suspectée — Urgence modérée**

Je vous entends. Cette situation nécessite une consultation vétérinaire dans la journée. Un refus total d'appui associé à un gonflement douloureux dépasse généralement la simple entorse légère.

**Actions immédiates :**
• Immobilisation stricte
• Portez votre chien pour tous ses déplacements
• Glaçage de la zone (10 minutes, tissu interposé)
• Aucun anti-inflammatoire humain

**Informations utiles pour le vétérinaire :**
• Circonstances de la blessure
• Evolution depuis l'apparition
• Présence de chaleur ou gonflement

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 4. Fièvre élevée – chien ─────────────────────────────────────
{
"level":"HIGH","animal":"chien",
"symptoms":[
    "température rectale 40.5°C, léthargie, perte d'appétit, frissons",
    "fièvre mesurée à 40.8°C, chien apathique, ne mange pas, nez sec",
    "hyperthermie 41°C, tremblements, refus alimentaire, prostration légère",
    "fièvre depuis hier soir (40.5°C), fatigue intense, yeux vitreux",
    "température 40.2°C, anorexie depuis 24h, boissons augmentées",
],
"conditions":[
    "infection bactérienne ou virale, réaction inflammatoire systémique",
    "sepsis débutant, infection focale, maladie infectieuse",
    "piroplasmose (tiques), leptospirose, ehrlichiose",
    "pneumonie, pyélonéphrite, prostatite (chien mâle)",
    "péritonite débutante, endocardite, infection profonde",
],
"cares":[
    "consultation vétérinaire aujourd'hui — bilan sanguin et NFS",
    "vétérinaire dans les heures — identification de la source infectieuse",
    "consultation urgente — antibiothérapie et fludothérapie si nécessaire",
    "vétérinaire aujourd'hui — sérologies tiques si exposition",
    "consultation dans les heures — bilan complet et traitement antipyrétique adapté",
],
"flags":[
    "température > 41.5°C → lésions organiques",
    "sepsis grave, choc septique",
    "convulsions liées à la fièvre",
    "détresse respiratoire associée",
    "anurie, gencives très pâles, collapsus",
],
"outputs":[
"""⚠️ **Fièvre élevée — Consultez aujourd'hui**

Je comprends votre inquiétude. Une fièvre à 40.5°C chez un chien avec léthargie et perte d'appétit indique une **infection ou inflammation sérieuse** qui mérite une consultation vétérinaire dans la journée.

**En attendant :**
• Eau fraîche accessible en permanence
• Endroit frais et confortable
• Ne donnez pas de médicaments humains contre la fièvre (paracétamol, ibuprofène = dangereux)
• Consultez le vétérinaire aujourd'hui

**Urgence immédiate si :**
• Fièvre > 41°C
• Gencives pâles ou convulsions

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Hyperthermie infectieuse — Évaluation urgente**

Je vous entends. Une fièvre à plus de 40°C avec anorexie et prostration chez un chien nécessite un **bilan sanguin** pour identifier la source infectieuse et démarrer le traitement approprié.

**En attendant la consultation :**
• Eau fraîche en quantité
• Endroit frais
• Pas d'anti-fièvre humain
• Consultation vétérinaire aujourd'hui

**Urgence si :**
• Fièvre > 41.5°C
• Convulsions
• Chien qui s'effondre

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Fièvre à 40.8°C — Bilan vétérinaire nécessaire**

Je comprends votre préoccupation. Une telle fièvre avec apathie indique une **réaction systémique à une infection** — bactérienne, virale ou parasitaire (tiques). Un bilan sanguin permettra d'orienter le traitement.

**Soins immédiats :**
• Eau fraîche disponible
• Endroit frais et calme
• Aucun médicament humain
• Consultation vétérinaire dans les heures

**Si votre chien a eu des contacts avec des tiques :** signalez-le au vétérinaire — piroplasmose possible.

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Température élevée — Consultez dans les heures**

Je vous entends. Une fièvre de 40 à 41°C chez un chien avec anorexie mérite une **consultation vétérinaire dans les heures**. La source de la fièvre peut aller d'une infection banale à une maladie grave.

**En attendant :**
• Eau fraîche accessible
• Endroit frais
• Pas d'antipyrétiques humains
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Fièvre infectieuse — Action requise**

Je comprends votre inquiétude. Une fièvre à 40-41°C avec apathie et anorexie indique que l'organisme de votre chien combat une **infection active**. Sans traitement adapté, certaines infections (piroplasmose, leptospirose) peuvent être mortelles.

**Actions immédiates :**
• Eau fraîche en permanence
• Endroit frais
• Pas de médicaments humains
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Hyperthermie — Consultation urgente**

Je vous entends. La fièvre élevée est un **signal d'alarme** qui indique que votre chien combat une infection. Un bilan sanguin permettra au vétérinaire d'identifier la cause et de choisir le traitement.

**En attendant :**
• Eau fraîche disponible
• Fraîcheur et repos
• Pas d'anti-fièvre humain
• Consultation vétérinaire dans les heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Fièvre et prostration — Évaluation médicale**

Je comprends votre préoccupation. Une fièvre de 40°C ou plus associée à de la prostration et une anorexie nécessite une **évaluation vétérinaire dans la journée**.

**Soins à domicile :**
• Eau fraîche disponible
• Endroit frais
• Pas de médicaments anti-fièvre humains
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Infection systémique probable — Consultez vite**

Je vous entends. Une fièvre persistante chez un chien indique généralement une **infection bactérienne ou parasitaire** qui nécessite un traitement prescrit par un vétérinaire.

**En attendant :**
• Eau fraîche accessible
• Environnement frais
• Aucun médicament humain
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Fièvre — Risque de leptospirose ou piroplasmose**

Je comprends votre inquiétude. Selon l'exposition de votre chien (eau stagnante, tiques), une fièvre avec anorexie peut indiquer une **leptospirose ou une piroplasmose** — traitables si diagnostiquées rapidement.

**En attendant :**
• Eau fraîche en quantité
• Endroit frais
• Consultation vétérinaire aujourd'hui — signalez les expositions récentes

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Température rectale élevée — Bilan urgent**

Je vous entends. Une température de 40.2 à 41°C avec anorexie et léthargie indique une **réaction fébrile significative** qui nécessite un bilan sanguin et une consultation vétérinaire dans la journée.

**Actions immédiates :**
• Eau fraîche disponible en permanence
• Endroit frais et confortable
• Pas de médicaments humains
• Consultation vétérinaire aujourd'hui

**Urgence si :**
• Fièvre > 41.5°C
• Gencives pâles ou convulsions

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 5. Plaie profonde / morsure – chien ─────────────────────────
{
"level":"HIGH","animal":"chien",
"symptoms":[
    "plaie par morsure profonde au cou, saignement actif, douleur intense",
    "lacération profonde membre antérieur, bord irréguliers, saignement modéré",
    "morsure de chien sur le flanc, plaie ouverte large, douleur à la palpation",
    "plaie punctiforme profonde thorax après morsure, possible pneumothorax",
    "traumatisme cutané profond après morsure, tissu visible, hématome",
],
"conditions":[
    "plaie par morsure profonde, risque d'infection septique, lésion tendineuse",
    "lacération traumatique, risque de complication infectieuse (Pasteurella)",
    "morsure profonde, risque d'atteinte vasculaire ou nerveuse",
    "plaie punctiforme thoracique, pneumothorax possible",
    "morsure avec écrasement tissulaire, nécrose secondaire possible",
],
"cares":[
    "consultation vétérinaire urgente — suture, antibiotiques",
    "consultation dans les 4h — nettoyage, suture et antibiothérapie",
    "clinique vétérinaire aujourd'hui — évaluation profondeur et traitement",
    "urgence vétérinaire — exploration de la plaie et suture sous anesthésie",
    "consultation urgente — irrigation, débridement et antibiotiques systémiques",
],
"flags":[
    "saignement artériel pulsatile, atteinte vasculaire",
    "détresse respiratoire si thorax impliqué, pneumothorax",
    "infection rapide, abcès profond, septicémie",
    "tissu nécrotique, gangrène gazeuse",
    "choc hémorragique, atteinte nerveuse",
],
"outputs":[
"""⚠️ **Plaie par morsure — Consultez aujourd'hui**

Je comprends votre inquiétude. Les plaies par morsure sont **trompeuses** — l'ouverture cutanée peut paraître petite mais les dommages en profondeur peuvent être importants. Une consultation vétérinaire dans les heures est nécessaire.

**Soins immédiats :**
• Lavez abondamment la plaie à l'eau propre (10 minutes minimum)
• Comprimez le saignement avec un linge propre
• Ne fermez pas la plaie avec du sparadrap (risque d'abcès)
• Consultez le vétérinaire aujourd'hui

**Urgence immédiate si :**
• Saignement artériel (rouge vif, pulsatile)
• Plaie thoracique avec difficultés respiratoires

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Morsure profonde — Évaluation urgente**

Je vous entends. Une morsure profonde nécessite toujours une **évaluation vétérinaire** — les plaies par morsure contiennent des bactéries virulentes qui provoquent des infections graves en 24-48h sans traitement.

**Premiers soins :**
• Lavage abondant à l'eau claire
• Compression du saignement
• Ne pas fermer la plaie
• Consultation vétérinaire dans les 4 heures

**Urgence immédiate si :**
• Saignement qui ne s'arrête pas
• Difficultés respiratoires (plaie thoracique)
• Chien en état de choc

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Lacération traumatique — Consultez dans les 4h**

Je comprends votre préoccupation. Une plaie profonde par morsure risque de développer une **infection sévère** si elle n'est pas correctement nettoyée, débridée et traitée par antibiotiques systémiques.

**Premiers soins immédiats :**
• Eau propre en abondance sur la plaie (10 minutes)
• Compression du saignement actif
• Pas de désinfectant fort (alcool = abîme les tissus)
• Consultation vétérinaire dans les 4h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Blessure par morsure — Action requise**

Je vous entends. Les plaies par morsure animale sont **souvent sous-estimées** — la pression de la mâchoire provoque des dommages profonds invisibles à la surface. Une consultation vétérinaire aujourd'hui est indispensable.

**Soins immédiats :**
• Lavage abondant à l'eau propre
• Compression douce sur le saignement
• Ne pas fermer la plaie
• Consultation vétérinaire dans les heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Plaie ouverte — Soins vétérinaires urgents**

Je comprends votre inquiétude. Une plaie ouverte après morsure nécessite une **prise en charge vétérinaire rapide** — sans suture et antibiotiques, le risque d'abcès profond est élevé.

**Premiers soins à domicile :**
• Lavage abondant à l'eau claire
• Compression du saignement avec linge propre
• Évitez l'alcool direct sur la plaie
• Consultez le vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Morsure — Infection quasi-certaine sans traitement**

Je vous entends. La gueule d'un chien contient des bactéries très virulentes. **Sans antibiothérapie vétérinaire**, une infection grave se développe généralement en 24 à 48 heures.

**Soins immédiats :**
• Lavage à l'eau claire pendant 10 minutes
• Compression douce
• Pas de fermeture de la plaie
• Consultation vétérinaire dans les 4h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Lacération profonde — Suture nécessaire**

Je comprends votre préoccupation. Une plaie ouverte et profonde nécessite une **exploration et une suture vétérinaire** dans les heures qui suivent — après 6-8h, le risque d'infection rend la suture primaire impossible.

**Premiers soins :**
• Eau propre en abondance (10 minutes)
• Compression du saignement
• Maintien d'un pansement propre
• Consultation vétérinaire rapidement

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Plaie punctiforme — Ne sous-estimez pas**

Je vous entends. Les plaies punctiformes par morsure sont les plus dangereuses — l'ouverture est petite mais les dommages en profondeur sont souvent importants.

**Soins immédiats :**
• Lavage abondant à l'eau claire
• Compression si saignement
• Consultation vétérinaire dans les 4h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Traumatisme par morsure — Consultation urgente**

Je comprends votre inquiétude. Les morsures animales nécessitent toujours une **évaluation vétérinaire** — la profondeur réelle est souvent sous-estimée.

**Actions immédiates :**
• Lavage à l'eau propre 10 minutes
• Compression du saignement
• Pas de fermeture maison
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Morsure profonde — Risque septique élevé**

Je vous entends. Une plaie par morsure non traitée dans les heures développera presque systématiquement une **infection bactérienne** qui peut nécessiter une hospitalisation.

**Premiers soins :**
• Eau propre abondante
• Compression du saignement
• Pansement propre pour le transport
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 6. Détresse respiratoire modérée – chat ──────────────────────
{
"level":"HIGH","animal":"chat",
"symptoms":[
    "respiration rapide et superficielle, halètement au repos, respiration bouche ouverte",
    "respiration abdominale visible, fréquence respiratoire élevée, fatigue",
    "tachypnée persistante, légère cyanose des muqueuses, faiblesse",
    "respiration sifflante, toux sèche répétée, effort respiratoire visible",
    "respiration bruyante, intolérance à l'effort, gencives légèrement violacées",
],
"conditions":[
    "bronchite asthmatiforme féline, épanchement pleural débutant",
    "asthme félin, pneumonie, insuffisance cardiaque compensée",
    "BPCO féline, épanchement pleural modéré",
    "asthme sévère, pneumonie bactérienne, pyothorax",
    "cardiomyopathie hypertrophique, épanchement pleural",
],
"cares":[
    "consultation vétérinaire aujourd'hui — radiographie thoracique",
    "consultation urgente — oxymétrie et bilan respiratoire",
    "vétérinaire dans les 4h — évaluation cardiaque et pulmonaire",
    "consultation vétérinaire rapide — possible bronchodilatateur",
    "consultation dans les heures — bilan thoracique et traitement",
],
"flags":[
    "gencives bleutées, effondrement, arrêt respiratoire",
    "cyanose complète, perte de conscience",
    "respiration agonique, collapsus",
    "silence respiratoire soudain, choc",
    "gencives grises, chute de la température",
],
"outputs":[
"""⚠️ **Difficultés respiratoires — Consultez aujourd'hui**

Je comprends votre inquiétude. Un chat qui respire rapidement avec effort au repos présente une **anomalie respiratoire** qui mérite une évaluation vétérinaire dans la journée.

**En attendant la consultation :**
• Placez votre chat dans un endroit frais et aéré
• Ne l'excitez pas ou ne le stressez pas
• Évitez les escaliers et les efforts physiques
• Pas de produits parfumés ou de fumée dans la pièce

**Urgence immédiate si :**
• Gencives qui bleuissent
• Chute soudaine ou inconscience

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Tachypnée féline — Évaluation urgente**

Je vous entends. Une respiration rapide et laborieuse au repos chez un chat n'est **jamais normale** — cela indique que son organisme travaille trop pour s'oxygéner. Une consultation dans les heures est nécessaire.

**Ce que vous pouvez faire :**
• Endroit frais, calme, bien aéré
• Ne stressez pas votre chat
• Pas d'effort physique
• Surveillance de la couleur des gencives

**Consultez en urgence immédiate si :**
• Gencives bleutées ou grises
• Aggravation nette de la respiration

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Asthme ou épanchement — Consultation dans les 4h**

Je comprends votre préoccupation. Les signes que vous décrivez évoquent un **asthme félin sévère ou un épanchement pleural** — deux causes fréquentes de détresse respiratoire modérée chez le chat.

**Soins immédiats :**
• Environnement frais et aéré
• Réduisez toute source de stress
• Évitez les produits parfumés et la fumée
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Respiration difficile chez le chat — Action rapide**

Je vous entends. Un chat qui respire avec effort visible ou qui ouvre la bouche pour respirer est en **difficulté respiratoire** — une consultation vétérinaire dans les heures est nécessaire.

**Actions immédiates :**
• Endroit frais, calme, bien ventilé
• Pas de stress ni d'excitation
• Surveillance des gencives (normales = rose pâle)
• Consultation vétérinaire dans les 4h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Tachypnée au repos — Consultez rapidement**

Cette situation mérite une attention médicale dans les heures. Une fréquence respiratoire élevée au repos peut indiquer de l'asthme, une **cardiomyopathie** ou un épanchement pleural.

**En attendant le vétérinaire :**
• Environnement frais et aéré
• Calme et absence de stress
• Comptez les mouvements respiratoires par minute (normal < 30/min)
• Consultation vétérinaire dans les 4h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Détresse respiratoire modérée — Évaluation nécessaire**

Je comprends votre inquiétude. Un chat qui respire rapidement et avec effort au repos a besoin d'un **bilan thoracique vétérinaire** — radiographie et oxymétrie permettront d'identifier la cause.

**Soins à domicile en attendant :**
• Endroit frais, calme
• Aucune source de stress
• Pas de parfums, fumée ou produits ménagers à proximité
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Problème respiratoire félin — Consultation urgente**

Je vous entends. Des difficultés respiratoires chez un chat ne doivent pas attendre plus de quelques heures avant une consultation. L'asthme félin peut s'aggraver très rapidement.

**Actions immédiates :**
• Environnement calme et bien aéré
• Température fraîche
• Pas d'effort, pas de stress
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Insuffisance respiratoire partielle — Consultez dans les 4h**

Je comprends votre préoccupation. Les signes que vous observez suggèrent que votre chat ne s'oxygène pas de manière optimale. Une **radiographie thoracique** permettra de voir si les poumons ou le cœur sont en cause.

**En attendant :**
• Endroit frais, calme, aéré
• Pas de stress
• Surveillance des gencives
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Respiration abdominale visible — Attention requise**

Je vous entends. Quand un chat utilise ses muscles abdominaux pour respirer, c'est le signe que ses muscles respiratoires normaux ne suffisent plus — cela indique une **charge respiratoire augmentée**.

**Soins immédiats :**
• Endroit frais et bien aéré
• Calme absolu
• Surveillance constante
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Asthme félin probable — Consultez aujourd'hui**

Je comprends votre inquiétude. Les signes respiratoires que vous décrivez sont caractéristiques de l'**asthme félin** ou d'un problème cardiaque — des conditions qui répondent bien au traitement si identifiées rapidement.

**En attendant la consultation :**
• Environnement calme, frais, sans fumée ni parfums
• Pas de stress ni d'agitation
• Surveillance de la couleur des gencives
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

# ── 7. Infection oculaire sévère – chien ────────────────────────
{
"level":"HIGH","animal":"chien",
"symptoms":[
    "œil rouge vif, sécrétions jaunes/vertes abondantes, œil à moitié fermé",
    "conjonctivite sévère bilatérale, écoulements purulents, douleur oculaire",
    "ulcère cornéen suspecté, photophobie, frottement intense de l'œil",
    "œil très rouge, aspect voilé de la cornée, larmoiement verdâtre",
    "infection oculaire sévère, gonflement des paupières, sécrétions épaisses",
],
"conditions":[
    "kératoconjonctivite infectieuse sévère, ulcère cornéen",
    "conjonctivite bactérienne purulente, possible kératite",
    "ulcère cornéen infecté, kératite bactérienne",
    "endophtalmie, kératoconjonctivite sèche (KCS) sévère",
    "conjonctivite purulente, abcès cornéen",
],
"cares":[
    "consultation vétérinaire aujourd'hui — collyres antibiotiques urgents",
    "vétérinaire dans les 4h — coloration fluorescéine et traitement",
    "consultation urgente — exploration oculaire et traitement adapté",
    "vétérinaire aujourd'hui — test de Schirmer et bilan oculaire",
    "consultation dans les heures — prévenir la perforation cornéenne",
],
"flags":[
    "perforation cornéenne, cécité permanente",
    "panophtalmie, perte de l'œil",
    "septicémie d'origine oculaire",
    "propagation infection au cerveau",
    "glaucome secondaire, cécité",
],
"outputs":[
"""⚠️ **Infection oculaire sévère — Consultez aujourd'hui**

Je comprends votre inquiétude. Des sécrétions purulentes importantes associées à une rougeur sévère indiquent une **infection bactérienne de l'œil** qui nécessite des collyres antibiotiques vétérinaires urgents.

**En attendant :**
• Nettoyez délicatement les sécrétions avec du sérum physiologique
• Empêchez votre chien de se frotter l'œil (collerette)
• Pas de collyres humains
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Conjonctivite purulente — Antibiotiques urgents**

Je vous entends. Des sécrétions jaunes ou vertes abondantes avec œil fermé indiquent une **infection bactérienne active** qui nécessite des collyres antibiotiques vétérinaires pour éviter les complications cornéennes.

**Soins immédiats :**
• Nettoyage délicat avec sérum physiologique
• Collerette si frottement
• Pas de collyre humain
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Kératoconjonctivite — Consultation urgente**

Je comprends votre préoccupation. Une infection oculaire sévère non traitée peut évoluer vers un **ulcère cornéen** ou une perforation — des complications graves qui peuvent entraîner la cécité.

**Actions immédiates :**
• Nettoyez les sécrétions avec sérum physiologique
• Collerette pour empêcher le frottement
• Pas de collyres humains
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Sécrétions purulentes oculaires — Traitement urgent**

Je vous entends. Une conjonctivite avec sécrétions purulentes abondantes indique une **infection bactérienne sévère** qui nécessite des antibiotiques spécifiques prescrits par un vétérinaire.

**En attendant :**
• Nettoyage délicat avec sérum physiologique tiède
• Collerette si l'animal se frotte
• Aucun collyre humain
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Infection oculaire — Ne pas négliger**

Je comprends votre inquiétude. Une infection oculaire sévère non traitée peut progresser vers une **kératite ulcérative** ou une endophtalmie — des complications graves menaçant la vision.

**Soins immédiats :**
• Sérum physiologique pour nettoyer délicatement
• Collerette pour protéger l'œil
• Pas de collyres humains
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Ulcère cornéen possible — Consultation urgente**

Je vous entends. Un œil rouge avec aspect voilé de la cornée peut indiquer un **ulcère cornéen infecté** — une urgence ophtalmique qui nécessite des collyres antibiotiques et cicatrisants spécifiques.

**Actions immédiates :**
• Collerette pour empêcher le frottement
• Pas de collyre humain
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Infection purulente de l'œil — Action requise**

Je comprends votre préoccupation. Des écoulements purulents avec œil fermé indiquent une **infection bactérienne sévère** qui ne se résoudra pas sans traitement antibiotique adapté.

**En attendant :**
• Nettoyage doux avec sérum physiologique
• Collerette si frottement
• Pas de collyres humains
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Kératite bactérienne — Consultez rapidement**

Je vous entends. Une infection cornéenne active peut progresser vers une **perforation** en quelques jours sans traitement approprié — une consultation vétérinaire dans les heures est nécessaire.

**Soins immédiats :**
• Sérum physiologique pour nettoyer
• Collerette élisabéthaine
• Aucun collyre humain
• Consultation vétérinaire dans les 4h

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Œil infecté — Collyres vétérinaires nécessaires**

Je comprends votre inquiétude. Une conjonctivite purulente sévère nécessite des **collyres antibiotiques vétérinaires** — les collyres humains ne sont pas adaptés et peuvent même être dangereux.

**En attendant :**
• Nettoyage délicat avec sérum physiologique
• Collerette pour protéger l'œil
• Consultation vétérinaire aujourd'hui

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",

"""⚠️ **Infection oculaire sévère — Consultez dans les 4h**

Je vous entends. Des sécrétions purulentes abondantes avec rougeur et douleur indiquent une **infection oculaire active** qui nécessite une évaluation vétérinaire et des collyres antibiotiques adaptés.

**Actions immédiates :**
• Nettoyage doux avec sérum physiologique
• Collerette pour éviter le frottement
• Pas de collyres humains
• Consultation vétérinaire dans les 4 heures

_Ces conseils ne remplacent pas l'avis d'un vétérinaire._""",
],
},

]  # fin HIGH
