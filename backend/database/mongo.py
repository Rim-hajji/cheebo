"""
Cheebo — MongoDB Connection (Motor async)
==========================================
Connexion à MongoDB locale via Motor (driver async).
Collections : conversations, analysis_logs, partner_vets, api_logs

URI par défaut : mongodb://localhost:27017/cheebo_db
Peut être surchargé via la variable d'environnement MONGO_URI.
"""

import logging
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("cheebo.database")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB",  "cheebo_db")

_client: AsyncIOMotorClient = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        logger.info(f"MongoDB connecté : {MONGO_URI}/{DB_NAME}")
    return _client


def get_db():
    return get_client()[DB_NAME]


# ── Raccourcis vers les collections ─────────────────────────────────
def conversations():
    return get_db()["conversations"]

def analysis_logs():
    return get_db()["analysis_logs"]

def partner_vets():
    return get_db()["partner_vets"]

def api_logs():
    return get_db()["api_logs"]

def medications():
    return get_db()["medications"]


# ── Initialisation (indexes + seed vets) ────────────────────────────
async def init_db():
    """Crée les index et insère les vets partenaires si la collection est vide."""
    db = get_db()

    # Index sur session_id pour les conversations
    await db["conversations"].create_index("session_id", unique=True)
    await db["conversations"].create_index("updated_at")

    # Index sur analysis_logs
    await db["analysis_logs"].create_index("session_id")
    await db["analysis_logs"].create_index("created_at")
    await db["analysis_logs"].create_index("urgency_level")
    await db["analysis_logs"].create_index("item_id")
    await db["analysis_logs"].create_index("source")

    # Index api_logs
    await db["api_logs"].create_index("created_at")

    # Index medications (pilulier)
    await db["medications"].create_index("petId")
    await db["medications"].create_index("status")
    await db["medications"].create_index([("petId", 1), ("status", 1)])

    # Seed des vétérinaires partenaires si vide
    count = await db["partner_vets"].count_documents({})
    if count == 0:
        await db["partner_vets"].insert_many([
            {
                "name"       : "Clinique Vétérinaire El Menzah",
                "phone"      : "+216 71 234 567",
                "address"    : "Rue des Roses, El Menzah 6, Tunis",
                "specialties": ["urgences 24/7", "chirurgie", "médecine interne"],
                "available"  : True,
                "emergency"  : True,
                "lat"        : 36.8520,
                "lng"        : 10.2070,
                "created_at" : datetime.now(timezone.utc),
            },
            {
                "name"       : "Cabinet Vétérinaire Les Berges du Lac",
                "phone"      : "+216 71 345 678",
                "address"    : "Les Berges du Lac II, Tunis",
                "specialties": ["urgences", "dermatologie", "ophtalmologie"],
                "available"  : True,
                "emergency"  : True,
                "lat"        : 36.8390,
                "lng"        : 10.2390,
                "created_at" : datetime.now(timezone.utc),
            },
            {
                "name"       : "VetCare Centre — Ariana",
                "phone"      : "+216 71 456 789",
                "address"    : "Avenue de la République, Ariana",
                "specialties": ["chirurgie orthopédique", "neurologie"],
                "available"  : True,
                "emergency"  : False,
                "lat"        : 36.8625,
                "lng"        : 10.1956,
                "created_at" : datetime.now(timezone.utc),
            },
        ])
        logger.info("Vétérinaires partenaires initialisés dans MongoDB")

    # Migration : ajouter les villes tunisiennes manquantes
    _extra_vets = [
        {
            "name"       : "Clinique Vétérinaire Monastir",
            "phone"      : "+216 73 123 456",
            "address"    : "Avenue Habib Bourguiba, Monastir",
            "specialties": ["médecine générale", "urgences 24/7"],
            "available"  : True,
            "emergency"  : True,
            "lat"        : 35.7784,
            "lng"        : 10.8316,
        },
        {
            "name"       : "Cabinet Vétérinaire Sousse",
            "phone"      : "+216 73 234 567",
            "address"    : "Avenue 14 Janvier, Sousse",
            "specialties": ["médecine générale", "dermatologie"],
            "available"  : True,
            "emergency"  : False,
            "lat"        : 35.8288,
            "lng"        : 10.6405,
        },
        {
            "name"       : "Clinique Vétérinaire Sfax",
            "phone"      : "+216 74 345 678",
            "address"    : "Route de la Soukra, Sfax",
            "specialties": ["chirurgie", "urgences", "médecine interne"],
            "available"  : True,
            "emergency"  : True,
            "lat"        : 34.7406,
            "lng"        : 10.7603,
        },
        {
            "name"       : "Cabinet Vétérinaire Nabeul",
            "phone"      : "+216 72 456 789",
            "address"    : "Avenue Habib Thameur, Nabeul",
            "specialties": ["médecine générale", "vaccination"],
            "available"  : True,
            "emergency"  : False,
            "lat"        : 36.4561,
            "lng"        : 10.7376,
        },
        {
            "name"       : "Clinique Vétérinaire Bizerte",
            "phone"      : "+216 72 567 890",
            "address"    : "Route de Tunis, Bizerte",
            "specialties": ["urgences", "chirurgie orthopédique"],
            "available"  : True,
            "emergency"  : True,
            "lat"        : 37.2746,
            "lng"        : 9.8739,
        },
        {
            "name"       : "VetClinic Hammamet",
            "phone"      : "+216 72 678 901",
            "address"    : "Avenue des Hôtels, Hammamet",
            "specialties": ["médecine générale", "ophtalmologie"],
            "available"  : True,
            "emergency"  : False,
            "lat"        : 36.4000,
            "lng"        : 10.6167,
        },
    ]
    for vet in _extra_vets:
        await db["partner_vets"].update_one(
            {"name": vet["name"]},
            {"$setOnInsert": {**vet, "created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    # Migration : ajouter lat/lng aux documents existants qui n'en ont pas
    _vet_coords = [
        ("El Menzah", 36.8520, 10.2070),
        ("Lac",       36.8390, 10.2390),
        ("Ariana",    36.8625, 10.1956),
    ]
    for name_key, lat, lng in _vet_coords:
        await db["partner_vets"].update_many(
            {"name": {"$regex": name_key}, "lat": {"$exists": False}},
            {"$set": {"lat": lat, "lng": lng}},
        )

    # Seed des articles — re-seed si les articles n'ont pas encore d'URL
    needs_seed = True
    if await db["articles"].count_documents({}) > 0:
        sample = await db["articles"].find_one({"url": {"$exists": True}})
        needs_seed = sample is None  # re-seed si aucun article n'a d'URL
    if needs_seed:
        await db["articles"].delete_many({})
        await db["articles"].insert_many([
            {
                "order": 1, "category": "Nutrition",
                "species": ["chien", "tous"],
                "title": "Bien nourrir son chien : les bases",
                "summary": "Une alimentation équilibrée est la première clé de la santé de votre chien. Découvrez les besoins nutritionnels essentiels, les aliments à éviter et comment choisir une croquette adaptée à l'âge et au poids de votre compagnon.",
                "tip": "Évitez oignons, raisins, chocolat et xylitol — toxiques pour les chiens.",
                "source": "ASPCA Animal Care",
                "url": "https://www.aspca.org/pet-care/dog-care/dog-nutrition-tips",
                "icon": "🥩",
            },
            {
                "order": 2, "category": "Nutrition",
                "species": ["chat", "tous"],
                "title": "L'alimentation du chat : carnivore strict",
                "summary": "Le chat est un carnivore obligatoire : il ne peut pas synthétiser certains acides aminés comme la taurine. Une alimentation trop végétale peut entraîner des carences graves. Comprendre les besoins spécifiques du chat pour bien le nourrir.",
                "tip": "Le chat a besoin d'eau fraîche en permanence — une fontaine peut augmenter ses apports hydriques.",
                "source": "ASPCA Animal Care",
                "url": "https://www.aspca.org/pet-care/cat-care/cat-nutrition-tips",
                "icon": "🐟",
            },
            {
                "order": 3, "category": "Vaccination",
                "species": ["chien", "chat", "tous"],
                "title": "Le calendrier vaccinal de votre animal",
                "summary": "La vaccination protège votre animal contre des maladies graves comme la parvovirose, la leucopénie ou la rage. Connaître le calendrier recommandé par les vétérinaires permet d'assurer une protection optimale dès le plus jeune âge.",
                "tip": "Primovaccination à 8 et 12 semaines pour chiot/chaton, rappel annuel ou triennal selon le vaccin.",
                "source": "WSAVA Vaccination Guidelines",
                "url": "https://wsava.org/global-guidelines/vaccination-guidelines/",
                "icon": "💉",
            },
            {
                "order": 4, "category": "Hygiène",
                "species": ["chien", "chat", "tous"],
                "title": "Hygiène dentaire : l'ennemi silencieux",
                "summary": "80% des chiens et 70% des chats développent une maladie parodontale avant l'âge de 3 ans. Un brossage régulier des dents réduit l'accumulation de tartre, la mauvaise haleine et prévient les infections qui peuvent atteindre les organes vitaux.",
                "tip": "Brossez les dents de votre animal 3 fois par semaine avec un dentifrice vétérinaire — jamais humain.",
                "source": "VCA Animal Hospitals",
                "url": "https://vcahospitals.com/know-your-pet/dental-disease-in-cats",
                "icon": "🦷",
            },
            {
                "order": 5, "category": "Antiparasitaires",
                "species": ["chien", "chat", "tous"],
                "title": "Vermifugation et antiparasitaires : quand et comment ?",
                "summary": "Les parasites internes (vers) et externes (puces, tiques) menacent la santé de votre animal et de votre famille. Un programme de prévention régulier et adapté au mode de vie de l'animal est essentiel toute l'année.",
                "tip": "Vermifuger tous les 3 à 6 mois selon l'exposition. Les antiparasitaires externes mensuels sont recommandés chez les animaux sortant à l'extérieur.",
                "source": "ESCCAP European Guidelines",
                "url": "https://www.esccap.org/guidelines/",
                "icon": "🔬",
            },
            {
                "order": 6, "category": "Bien-être",
                "species": ["chat", "tous"],
                "title": "Enrichissement environnemental pour le chat",
                "summary": "Un chat non stimulé peut développer stress, anxiété et comportements indésirables. Griffoirs, jeux interactifs, fenêtre avec vue, cachettes — un environnement enrichi maintient l'équilibre mental et physique de votre chat.",
                "tip": "15 minutes de jeu interactif quotidien suffisent à réduire significativement l'anxiété du chat d'appartement.",
                "source": "International Cat Care",
                "url": "https://icatcare.org/advice/play-and-toys/",
                "icon": "🎾",
            },
            {
                "order": 7, "category": "Bien-être",
                "species": ["chien", "tous"],
                "title": "Activité physique du chien : adapter à la race",
                "summary": "Les besoins en exercice varient énormément selon la race, l'âge et la santé du chien. Un border collie a besoin de 2h d'activité intense par jour, quand un bouledogue français se contente de 30 minutes. Trop peu d'exercice mène à l'obésité, trop en entraîne blessures et arthrose précoce.",
                "tip": "Évitez l'exercice intense après les repas — risque de dilatation-torsion gastrique chez les grandes races.",
                "source": "AKC Canine Health",
                "url": "https://www.akc.org/expert-advice/health/how-much-exercise-does-a-dog-need/",
                "icon": "🏃",
            },
            {
                "order": 8, "category": "Bien-être",
                "species": ["lapin", "tous"],
                "title": "Le lapin de compagnie : soins essentiels",
                "summary": "Le lapin est souvent sous-estimé comme animal de compagnie. Il nécessite du foin en quantité illimitée, de l'espace pour se déplacer, et une surveillance vétérinaire régulière. La stase digestive est son urgence numéro 1 : reconnaître les signes peut lui sauver la vie.",
                "tip": "Un lapin qui n'a pas produit de selles depuis 6-8h et refuse de manger doit être vu par un vétérinaire d'urgence.",
                "source": "House Rabbit Society",
                "url": "https://rabbit.org/care/",
                "icon": "🐰",
            },
            {
                "order": 9, "category": "Santé préventive",
                "species": ["chien", "chat", "tous"],
                "title": "Stérilisation : pourquoi et quand ?",
                "summary": "La stérilisation prévient certains cancers (mammaires, prostatiques), les infections utérines, et réduit les comportements indésirables liés aux hormones. Elle contribue également à réduire la surpopulation animale. Quelle est l'âge idéal selon l'espèce et la race ?",
                "tip": "Chez la chienne, la stérilisation avant le 1er cycle réduit le risque de cancer mammaire à moins de 0,5%.",
                "source": "ASPCA Animal Care",
                "url": "https://www.aspca.org/pet-care/general-pet-care/spayneuter-your-pet",
                "icon": "❤️",
            },
            {
                "order": 10, "category": "Santé préventive",
                "species": ["chien", "chat", "tous"],
                "title": "Hydratation : l'eau, premier médicament",
                "summary": "La déshydratation est l'une des causes les plus fréquentes de consultation vétérinaire. Un animal adulte a besoin de 50-70 ml d'eau par kg de poids corporel par jour. Encourager la boisson prévient les calculs urinaires, la constipation et les maladies rénales.",
                "tip": "Un chat boit rarement à côté de sa gamelle alimentaire — placez la source d'eau à distance.",
                "source": "VCA Animal Hospitals",
                "url": "https://vcahospitals.com/know-your-pet/water-requirements-and-fluid-balance-in-dogs",
                "icon": "💧",
            },
            {
                "order": 11, "category": "Comportement",
                "species": ["chat", "tous"],
                "title": "Reconnaître la douleur chez le chat",
                "summary": "Le chat dissimule instinctivement sa douleur — comportement hérité de ses ancêtres pour ne pas montrer de faiblesse aux prédateurs. Apprendre à reconnaître les signaux subtils (changement de posture, isolement, feulement inhabituel) peut permettre une prise en charge précoce.",
                "tip": "Un chat qui dort les yeux mi-fermés et ne réagit pas aux stimuli habituels peut signaler une douleur intense.",
                "source": "International Cat Care",
                "url": "https://icatcare.org/advice/how-to-tell-if-your-cat-is-in-pain/",
                "icon": "😿",
            },
            {
                "order": 12, "category": "Urgences",
                "species": ["chien", "chat", "tous"],
                "title": "Premiers secours : que faire en attendant le vétérinaire ?",
                "summary": "Connaître les gestes de premiers secours peut faire la différence entre la vie et la mort de votre animal. De la gestion d'une hémorragie à la position de sécurité en cas d'inconscience — les bases essentielles que tout propriétaire devrait connaître.",
                "tip": "Ne jamais donner d'ibuprofène, paracétamol ou aspirine à un animal — ces médicaments humains sont toxiques.",
                "source": "ASPCA Animal Care",
                "url": "https://www.aspca.org/pet-care/general-pet-care/emergency-care",
                "icon": "🚑",
            },
            {
                "order": 13, "category": "Santé préventive",
                "species": ["chien", "chat", "tous"],
                "title": "Visites vétérinaires préventives : pourquoi 2 fois par an ?",
                "summary": "Les animaux vieillissent 5 à 7 fois plus vite que les humains. Une visite annuelle équivaut à un bilan tous les 5-7 ans en médecine humaine. Des bilans semi-annuels permettent de détecter précocement les maladies chroniques, dentaires, et les variations de poids.",
                "tip": "Apportez toujours le carnet de santé et notez les changements de comportement observés depuis la dernière visite.",
                "source": "AAHA Preventive Care Guidelines",
                "url": "https://www.aaha.org/pet-owner-resources/",
                "icon": "🏥",
            },
            {
                "order": 14, "category": "Comportement",
                "species": ["chien", "tous"],
                "title": "Socialisation du chiot : la fenêtre critique",
                "summary": "Entre 3 et 14 semaines, le chiot traverse une période de socialisation déterminante pour son comportement futur. Des expositions positives aux humains, autres animaux, bruits et environnements pendant cette fenêtre réduisent les peurs et l'agressivité à l'âge adulte.",
                "tip": "Chaque nouvelle expérience positive à cet âge vaut des mois d'éducation adulte.",
                "source": "AVSAB Animal Behavior Guidelines",
                "url": "https://avsab.org/resources/",
                "icon": "🐕",
            },
            {
                "order": 15, "category": "Nutrition",
                "species": ["chien", "chat", "tous"],
                "title": "Aliments dangereux pour vos animaux",
                "summary": "De nombreux aliments courants sont toxiques ou dangereux pour les animaux de compagnie. Raisins, oignons, ail, chocolat, xylitol, avocat, macadamia, alcool — cette liste peut surprendre. Connaître ces dangers peut prévenir une intoxication grave.",
                "tip": "En cas d'ingestion suspecte, appelez immédiatement votre vétérinaire — certaines intoxications nécessitent un traitement dans les 2 premières heures.",
                "source": "ASPCA Animal Poison Control Center",
                "url": "https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants",
                "icon": "⚠️",
            },
        ])
        logger.info("Articles bien-être initialisés dans MongoDB (15 articles)")

    logger.info("MongoDB — index et seed OK")
