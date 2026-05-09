"""
DoctoAgent — KB Tools + External Tools
========================================
Outils appelables par les agents LLM via LangChain tool calling.

Deux catégories d'outils :
  1. Outils KB internes  : accès ciblé à la base de connaissances vétérinaire
  2. Outils externes     : recherche web (DuckDuckGo) et encyclopédique (Wikipedia)
     → permettent aux agents d'aller chercher des informations absentes de la KB

Initialisation : appeler init_kb(kb_data) au démarrage de l'orchestrateur.

Auteur : Rim Hajji — PFE 2026
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger("doctoagent.tools")

# ──────────────────────────────────────────────────────────────────
# BASE DE CONNAISSANCES (injectée au démarrage)
# ──────────────────────────────────────────────────────────────────
_KB: dict = {}


def init_kb(kb_data: dict) -> None:
    """Injecte la KB vétérinaire dans les outils. Appelée une seule fois."""
    global _KB
    _KB = kb_data
    logger.info(f"KB injectée dans les outils : {len(_KB)} entrées")


# ──────────────────────────────────────────────────────────────────
# OUTILS DE RECHERCHE KB
# ──────────────────────────────────────────────────────────────────

@tool
def list_kb_symptoms() -> str:
    """
    Liste toutes les catégories de symptômes disponibles dans la base
    de connaissances vétérinaire. À appeler en premier pour trouver
    les clés valides avant d'utiliser les autres outils.
    """
    keys = list(_KB.keys())
    return json.dumps(keys, ensure_ascii=False)


@tool
def get_symptom_info(symptom_key: str) -> str:
    """
    Récupère l'entrée complète d'un symptôme dans la base de connaissances :
    causes possibles, red flags, conseils maison et évolution attendue.

    symptom_key : clé exacte (ex: 'vomissement', 'diarrhée', 'toux').
    Utiliser list_kb_symptoms() pour trouver les clés valides.
    """
    entry = _KB.get(symptom_key)
    if not entry:
        available = list(_KB.keys())[:8]
        return (
            f"Symptôme '{symptom_key}' non trouvé. "
            f"Clés disponibles (extrait) : {available}. "
            f"Appelle list_kb_symptoms() pour la liste complète."
        )
    return json.dumps(entry, ensure_ascii=False, indent=2)


@tool
def get_possible_causes(symptom_key: str) -> str:
    """
    Retourne la liste des causes médicales possibles pour un symptôme donné,
    telles que documentées dans la base de connaissances vétérinaire.

    symptom_key : clé exacte du symptôme.
    """
    entry = _KB.get(symptom_key, {})
    causes = entry.get("causes_possibles", [])
    if not causes:
        return f"Aucune cause documentée pour '{symptom_key}'."
    return json.dumps(causes, ensure_ascii=False)


@tool
def get_red_flags(symptom_key: str) -> str:
    """
    Retourne les signaux d'alarme (red flags) d'un symptôme : signes
    indiquant une situation grave nécessitant une consultation vétérinaire
    immédiate.

    symptom_key : clé exacte du symptôme.
    """
    entry = _KB.get(symptom_key, {})
    flags = entry.get("red_flags", [])
    if not flags:
        return f"Aucun red flag documenté pour '{symptom_key}'."
    return json.dumps(flags, ensure_ascii=False)


@tool
def get_home_care(symptom_key: str) -> str:
    """
    Retourne les conseils de soin à domicile pour un symptôme donné :
    actions concrètes que le propriétaire peut faire chez lui.

    symptom_key : clé exacte du symptôme.
    """
    entry = _KB.get(symptom_key, {})
    care = entry.get("conseils_maison", [])
    if not care:
        return f"Aucun conseil maison pour '{symptom_key}'."
    return json.dumps(care, ensure_ascii=False)


@tool
def get_evolution_timeline(symptom_key: str) -> str:
    """
    Retourne l'évolution temporelle attendue d'un symptôme si non traité :
    ce qui risque de se passer à 24h, 48h, 1 semaine, etc.

    symptom_key : clé exacte du symptôme.
    """
    entry = _KB.get(symptom_key, {})
    evolution = entry.get("evolution_attendue", {})
    if not evolution:
        return f"Pas d'évolution documentée pour '{symptom_key}'."
    return json.dumps(evolution, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────────
# OUTILS VÉTÉRINAIRES PARTENAIRES
# ──────────────────────────────────────────────────────────────────

PARTNER_VETS = [
    {
        "id"         : "vet_001",
        "name"       : "Clinique Vétérinaire El Menzah",
        "phone"      : "+216 71 234 567",
        "address"    : "Rue des Roses, El Menzah 6, Tunis",
        "specialties": ["urgences 24/7", "chirurgie", "médecine interne"],
        "available"  : True,
        "emergency"  : True,
    },
    {
        "id"         : "vet_002",
        "name"       : "Cabinet Vétérinaire Les Berges du Lac",
        "phone"      : "+216 71 345 678",
        "address"    : "Les Berges du Lac II, Tunis",
        "specialties": ["urgences", "dermatologie", "ophtalmologie"],
        "available"  : True,
        "emergency"  : True,
    },
    {
        "id"         : "vet_003",
        "name"       : "VetCare Centre — Ariana",
        "phone"      : "+216 71 456 789",
        "address"    : "Avenue de la République, Ariana",
        "specialties": ["chirurgie orthopédique", "neurologie"],
        "available"  : True,
        "emergency"  : False,
    },
    {
        "id"         : "vet_004",
        "name"       : "Clinique NAC & Exotiques — La Marsa",
        "phone"      : "+216 71 567 890",
        "address"    : "Avenue Habib Bourguiba, La Marsa, Tunis",
        "specialties": ["NAC (lapins, oiseaux, reptiles)", "chirurgie exotique", "urgences NAC"],
        "available"  : True,
        "emergency"  : True,
    },
    {
        "id"         : "vet_005",
        "name"       : "Centre Vétérinaire Sfax Sud",
        "phone"      : "+216 74 123 456",
        "address"    : "Route de Tunis Km 3, Sfax",
        "specialties": ["médecine interne", "échographie", "cardiologie"],
        "available"  : True,
        "emergency"  : False,
    },
    {
        "id"         : "vet_006",
        "name"       : "Polyclinique Vétérinaire Sousse",
        "phone"      : "+216 73 234 567",
        "address"    : "Avenue Ibn Khaldoun, Sousse",
        "specialties": ["urgences 24/7", "oncologie", "imagerie médicale"],
        "available"  : True,
        "emergency"  : True,
    },
]


@tool
def find_partner_vets(emergency_only: bool = False) -> str:
    """
    Trouve les vétérinaires partenaires Cheebo disponibles.
    Paramètre emergency_only : si True, retourne uniquement les cliniques
    avec service d'urgence 24/7. Si False, retourne tous les vétérinaires
    disponibles.
    """
    vets = [v for v in PARTNER_VETS if v["available"]]
    if emergency_only:
        vets = [v for v in vets if v["emergency"]]
    if not vets:
        return "Aucun vétérinaire partenaire disponible pour le moment."
    return json.dumps(vets, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────────
# OUTILS EXTERNES — Web Search + Wikipedia
# ──────────────────────────────────────────────────────────────────

@tool
def web_search_vet(query: str) -> str:
    """
    Effectue une recherche web sur DuckDuckGo pour obtenir des informations
    vétérinaires actualisées. À utiliser quand la base de connaissances interne
    ne contient pas d'informations suffisantes sur un symptôme, une maladie
    ou un traitement.

    query : question ou mots-clés vétérinaires (ex: 'gastroentérite hémorragique
            chien traitement', 'intoxication paracétamol chat signes cliniques').
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        # Préfixer la requête pour rester dans le domaine vétérinaire
        vet_query = f"vétérinaire {query}" if "vét" not in query.lower() else query
        with DDGS() as ddgs:
            results = list(ddgs.text(vet_query, max_results=3))
        if not results:
            return f"Aucun résultat web trouvé pour '{query}'."
        formatted = []
        for r in results:
            formatted.append(
                f"[{r.get('title', '')}]\n"
                f"{r.get('body', '')}\n"
                f"Source : {r.get('href', '')}"
            )
        return "\n\n---\n\n".join(formatted)
    except Exception as e:
        logger.warning(f"web_search_vet erreur : {e}")
        return f"Recherche web indisponible : {e}"


@tool
def search_wikipedia_vet(topic: str) -> str:
    """
    Recherche une maladie, un symptôme ou un concept vétérinaire/médical
    sur Wikipédia (en français en priorité, puis en anglais si absent).
    Utile pour les maladies rares ou les termes techniques absents de la KB.

    topic : nom de la maladie ou du concept (ex: 'parvovirose', 'leishmaniose',
            'syndrome de dilatation-torsion gastrique').
    """
    import urllib.request
    import urllib.parse

    def _fetch(lang: str, term: str) -> str:
        url = (
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
            + urllib.parse.quote(term.replace(" ", "_"))
        )
        req = urllib.request.Request(url, headers={"User-Agent": "DoctoAgent/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        extract = data.get("extract", "")
        if not extract:
            raise ValueError("Page vide")
        title = data.get("title", term)
        return f"[Wikipedia {lang.upper()} — {title}]\n{extract[:600]}"

    try:
        return _fetch("fr", topic)
    except Exception:
        pass
    try:
        return _fetch("en", topic)
    except Exception as e:
        logger.warning(f"search_wikipedia_vet erreur : {e}")
        return f"Wikipedia indisponible pour '{topic}'."


# ──────────────────────────────────────────────────────────────────
# OUTILS DE PREMIERS SECOURS ET ESPÈCES
# ──────────────────────────────────────────────────────────────────

@tool
def get_first_aid_steps(emergency_type: str) -> str:
    """
    Retourne les étapes de premiers secours immédiats pour une urgence vétérinaire.
    À utiliser pour guider le propriétaire pendant le transport vers le vétérinaire.

    emergency_type : type d'urgence parmi :
        'intoxication', 'convulsion', 'coup_de_chaleur', 'hemorragie',
        'etouffement', 'choc', 'fracture', 'noyade'
    """
    FIRST_AID = {
        "intoxication": {
            "titre": "Intoxication suspectée",
            "urgence": "CRITIQUE",
            "etapes": [
                "1. Identifier et conserver l'emballage ou la plante responsable.",
                "2. NE PAS faire vomir sans avis vétérinaire — contre-indiqué pour acides, bases, hydrocarbures.",
                "3. NE PAS donner de lait, eau salée, huile ou charbon actif sans prescription.",
                "4. Si contact cutané : rincer à l'eau courante 10–15 min sans frotter.",
                "5. Garder l'animal au calme, à l'abri de la chaleur et du froid.",
                "6. Appeler le vétérinaire ou le centre antipoison IMMÉDIATEMENT.",
                "7. Transport urgent en portant l'animal sans lui faire faire d'efforts.",
            ],
            "a_eviter": ["Faire vomir sans instruction vétérinaire", "Donner du lait ou des aliments", "Attendre l'apparition de symptômes"],
        },
        "convulsion": {
            "titre": "Crise convulsive",
            "urgence": "CRITIQUE",
            "etapes": [
                "1. Chronométrer la durée de la crise dès le début.",
                "2. Éloigner tous les objets dangereux autour de l'animal.",
                "3. Ne PAS mettre les mains dans la gueule — risque de morsure sévère.",
                "4. Ne PAS retenir l'animal — risque de blessure.",
                "5. Baisser la luminosité et réduire le bruit au maximum.",
                "6. Filmer la crise si possible (aide diagnostique pour le vétérinaire).",
                "7. Si la crise dure > 5 minutes : urgence vitale — transport immédiat.",
                "8. Après la crise : garder l'animal dans un endroit calme et sombre, surveiller.",
            ],
            "a_eviter": ["Mettre un objet dans la bouche", "Tenir fermement l'animal", "Allumer les lumières ou faire du bruit"],
        },
        "coup_de_chaleur": {
            "titre": "Coup de chaleur (hyperthermie)",
            "urgence": "CRITIQUE",
            "etapes": [
                "1. Déplacer l'animal IMMÉDIATEMENT vers un endroit frais et à l'ombre.",
                "2. Mouiller le corps avec de l'eau TIÈDE (jamais glacée — vasoconstriction).",
                "3. Ventiler activement avec un éventail, climatisation ou courant d'air.",
                "4. Placer des linges humides sur les coussinets, l'aine et les aisselles.",
                "5. Si conscient : proposer de l'eau fraîche à boire en petites quantités.",
                "6. Appeler le vétérinaire pendant le refroidissement.",
                "7. Transport vers la clinique dès stabilisation partielle.",
                "8. Surveiller la température rectale — objectif < 39.5°C avant transport.",
            ],
            "a_eviter": ["Immerger dans l'eau froide ou glacée", "Donner de l'aspirine ou paracétamol", "Laisser seul sans surveillance"],
        },
        "hemorragie": {
            "titre": "Hémorragie externe",
            "urgence": "HAUTE",
            "etapes": [
                "1. Porter des gants si disponibles.",
                "2. Appliquer une compression directe et ferme avec une compresse stérile ou tissu propre.",
                "3. Maintenir la pression SANS retirer le pansement (si imbibé, en ajouter un par-dessus).",
                "4. Si membre : élever légèrement la zone blessée au-dessus du niveau du cœur.",
                "5. Ne jamais utiliser de garrot sauf en dernier recours.",
                "6. Si garrot indispensable : noter l'heure exacte de pose — signaler au vétérinaire.",
                "7. Garder l'animal couché et au chaud — le choc hémorragique peut survenir rapidement.",
                "8. Transport en urgence vers le vétérinaire en maintenant la compression.",
            ],
            "a_eviter": ["Retirer la compresse imbibée de sang", "Appliquer des poudres ou herbes", "Laisser l'animal marcher si la plaie est sur un membre"],
        },
        "etouffement": {
            "titre": "Corps étranger — étouffement",
            "urgence": "CRITIQUE",
            "etapes": [
                "1. Ouvrir la gueule et inspecter visuellement — retirer l'objet si visible et accessible.",
                "2. Ne PAS effectuer de balayage aveugle (risque d'enfoncer l'objet).",
                "3. Si l'animal est inconscient : tenter de retirer l'objet en inclinant la tête vers le bas.",
                "4. Manœuvre de Heimlich : placer les deux mains sous l'abdomen juste derrière les côtes, compressions brèves et fermes vers le haut et l'avant (3–5 fois).",
                "5. Pour petits animaux : tenir tête en bas et donner 4–5 claques entre les omoplates.",
                "6. Alterner compressions abdominales et claques dans le dos.",
                "7. Transport en urgence immédiate — ne pas attendre la résolution complète.",
            ],
            "a_eviter": ["Balayage aveugle de la gueule", "Donner de l'eau à boire", "Attendre si l'animal continue à respirer difficilement"],
        },
        "choc": {
            "titre": "État de choc",
            "urgence": "CRITIQUE",
            "etapes": [
                "1. Allonger l'animal sur le côté dans une position confortable.",
                "2. Couvrir d'une couverture pour maintenir la chaleur corporelle.",
                "3. Surélever légèrement l'arrière-train (sauf si trauma thoracique ou respiratoire).",
                "4. Ne RIEN donner par voie orale.",
                "5. Si hémorragie visible : comprimer la plaie.",
                "6. Parler à l'animal doucement pour le rassurer — éviter tout stress supplémentaire.",
                "7. Transport immédiat en urgence — le choc est fatal sans réanimation intraveineuse.",
                "8. Signaler au vétérinaire : prise de médicaments, piqûre récente, traumatisme.",
            ],
            "a_eviter": ["Donner à manger ou boire", "Laisser l'animal debout ou se déplacer", "Retarder le transport"],
        },
        "fracture": {
            "titre": "Fracture suspectée",
            "urgence": "HAUTE",
            "etapes": [
                "1. Immobiliser l'animal — limiter tout mouvement du membre suspect.",
                "2. Ne PAS tenter de remettre l'os en place.",
                "3. Ne PAS poser d'attelle improvisée — peut couper la circulation.",
                "4. Si fracture ouverte (os visible) : recouvrir avec une compresse stérile humide sans comprimer.",
                "5. Transporter sur une surface rigide et plate (planche, carton épais).",
                "6. Maintenir l'animal au chaud et au calme.",
                "7. Ne rien donner à manger ou boire (anesthésie chirurgicale probable).",
                "8. Signaler le mécanisme du traumatisme au vétérinaire.",
            ],
            "a_eviter": ["Tenter de réduire la fracture manuellement", "Laisser l'animal marcher sur le membre", "Administrer des analgésiques humains"],
        },
        "noyade": {
            "titre": "Quasi-noyade",
            "urgence": "CRITIQUE",
            "etapes": [
                "1. Sortir l'animal de l'eau en sécurisant d'abord votre propre sécurité.",
                "2. Tenir l'animal tête vers le bas pour faciliter l'écoulement de l'eau des voies aériennes.",
                "3. Donner 4–5 claques fermes dans le dos entre les omoplates.",
                "4. Si l'animal est inconscient et ne respire pas : commencer la réanimation.",
                "   — Fermer la gueule et souffler dans les narines (1 souffle toutes 3 secondes).",
                "   — Si pas de pouls : compressions cardiaques (100–120/min, 1/3 de la largeur thoracique).",
                "5. Sécher et réchauffer l'animal dès que possible.",
                "6. Transport urgent chez le vétérinaire MÊME si l'animal semble rétabli — œdème pulmonaire différé possible.",
                "7. Surveiller la respiration en continu pendant le transport.",
            ],
            "a_eviter": ["Considérer l'animal sauvé si il respire à nouveau — œdème secondaire possible", "Secouer l'animal vigoureusement", "Retarder le transport si l'animal paraît stable"],
        },
    }
    key = emergency_type.lower().strip()
    result = FIRST_AID.get(key)
    if not result:
        return json.dumps({"erreur": f"Type '{emergency_type}' non reconnu.", "types_disponibles": list(FIRST_AID.keys())}, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_toxic_foods(species: str) -> str:
    """
    Retourne la liste des aliments toxiques pour une espèce animale donnée,
    avec le niveau de danger et les effets cliniques principaux.

    species : espèce parmi 'dog', 'cat', 'rabbit', 'bird', 'hamster', 'guinea_pig'
    """
    TOXIC_FOODS = {
        "dog": {
            "espece": "Chien",
            "aliments_toxiques": [
                {"aliment": "Chocolat (théobromine)", "danger": "CRITIQUE", "effets": "Vomissements, arythmie cardiaque, convulsions, mort. Chocolat noir > lait > blanc."},
                {"aliment": "Raisin et raisins secs", "danger": "CRITIQUE", "effets": "Insuffisance rénale aiguë soudaine — toute dose peut être mortelle."},
                {"aliment": "Xylitol (édulcorant)", "danger": "CRITIQUE", "effets": "Hypoglycémie sévère, insuffisance hépatique aiguë. Présent dans chewing-gums, beurre de cacahuète sans sucre, médicaments."},
                {"aliment": "Oignon, ail, poireau, ciboulette", "danger": "ÉLEVÉ", "effets": "Anémie hémolytique — destruction des globules rouges. Cuit ou cru, en poudre ou frais."},
                {"aliment": "Macadamia", "danger": "MODÉRÉ", "effets": "Faiblesse des membres postérieurs, hyperthermie, tremblements, vomissements."},
                {"aliment": "Avocat (perséine)", "danger": "MODÉRÉ", "effets": "Vomissements, diarrhée, oedème. Le noyau présente aussi un risque d'obstruction."},
                {"aliment": "Alcool (éthanol)", "danger": "CRITIQUE", "effets": "Dépression du SNC, hypoglycémie, acidose, coma."},
                {"aliment": "Caféine (café, thé, boissons énergisantes)", "danger": "ÉLEVÉ", "effets": "Tachycardie, tremblements, convulsions."},
                {"aliment": "Sel en excès", "danger": "MODÉRÉ", "effets": "Hypernatrémie, vomissements, convulsions, mort."},
                {"aliment": "Os cuits (volaille)", "danger": "ÉLEVÉ", "effets": "Esquilles pouvant perforer l'œsophage ou l'intestin."},
            ],
        },
        "cat": {
            "espece": "Chat",
            "aliments_toxiques": [
                {"aliment": "Paracétamol (acétaminophène)", "danger": "CRITIQUE", "effets": "Méthémoglobinémie, nécrose hépatique — UNE seule comprimé peut tuer un chat."},
                {"aliment": "Oignon, ail, poireau", "danger": "CRITIQUE", "effets": "Anémie hémolytique sévère — le chat est plus sensible que le chien."},
                {"aliment": "Lys (toutes espèces : Lilium, Hemerocallis)", "danger": "CRITIQUE", "effets": "Insuffisance rénale aiguë foudroyante — même le pollen ou l'eau du vase."},
                {"aliment": "Raisin et raisins secs", "danger": "CRITIQUE", "effets": "Insuffisance rénale aiguë."},
                {"aliment": "Alcool", "danger": "CRITIQUE", "effets": "Coma, mort même en petites quantités."},
                {"aliment": "Chocolat", "danger": "ÉLEVÉ", "effets": "Théobromine — arythmie, convulsions."},
                {"aliment": "Xylitol", "danger": "ÉLEVÉ", "effets": "Hypoglycémie, toxicité hépatique."},
                {"aliment": "Foie en excès", "danger": "MODÉRÉ", "effets": "Hypervitaminose A — déformations osseuses, anorexie."},
            ],
        },
        "rabbit": {
            "espece": "Lapin",
            "aliments_toxiques": [
                {"aliment": "Avocat", "danger": "CRITIQUE", "effets": "Perséine — insuffisance cardiaque, mort."},
                {"aliment": "Chocolat", "danger": "CRITIQUE", "effets": "Toxicité cardiaque et neurologique."},
                {"aliment": "Oignon, ail, poireau", "danger": "CRITIQUE", "effets": "Anémie hémolytique."},
                {"aliment": "Rhubarbe", "danger": "CRITIQUE", "effets": "Acide oxalique — insuffisance rénale."},
                {"aliment": "Chou en excès, brocoli, choux-fleur", "danger": "MODÉRÉ", "effets": "Ballonnements, stase digestive — à limiter fortement."},
                {"aliment": "Pomme de terre (crue)", "danger": "ÉLEVÉ", "effets": "Solanine — toxicité neurologique."},
                {"aliment": "Bonbons et sucre raffiné", "danger": "ÉLEVÉ", "effets": "Déséquilibre flore intestinale, entérotoxémie."},
            ],
        },
        "bird": {
            "espece": "Oiseaux (perroquet, canari, perruche)",
            "aliments_toxiques": [
                {"aliment": "Avocat", "danger": "CRITIQUE", "effets": "Perséine — cardiotoxicité, mort rapide."},
                {"aliment": "Chocolat", "danger": "CRITIQUE", "effets": "Théobromine/caféine — mort possible."},
                {"aliment": "Sel", "danger": "ÉLEVÉ", "effets": "Déshydratation, insuffisance rénale."},
                {"aliment": "Oignon, ail", "danger": "ÉLEVÉ", "effets": "Anémie hémolytique."},
                {"aliment": "Pomme (pépins)", "danger": "ÉLEVÉ", "effets": "Cyanure dans les pépins — toxicité neurologique."},
                {"aliment": "Caféine, alcool", "danger": "CRITIQUE", "effets": "Arythmie, mort."},
                {"aliment": "Téflon surchauffé (PTFE)", "danger": "CRITIQUE", "effets": "Vapeurs mortelles pour les oiseaux à très faible concentration."},
            ],
        },
        "hamster": {
            "espece": "Hamster",
            "aliments_toxiques": [
                {"aliment": "Oignon, ail", "danger": "CRITIQUE", "effets": "Anémie hémolytique."},
                {"aliment": "Chocolat, caféine", "danger": "CRITIQUE", "effets": "Toxicité cardiaque — fatal même en petite quantité."},
                {"aliment": "Amandes amères", "danger": "CRITIQUE", "effets": "Cyanure."},
                {"aliment": "Agrumes (oranges, citrons)", "danger": "MODÉRÉ", "effets": "Acidité — problèmes digestifs, diarrhée."},
                {"aliment": "Tomate (feuilles, tiges)", "danger": "ÉLEVÉ", "effets": "Solanine — toxicité neurologique."},
                {"aliment": "Sel et aliments salés", "danger": "ÉLEVÉ", "effets": "Déshydratation, insuffisance rénale."},
            ],
        },
        "guinea_pig": {
            "espece": "Cochon d'Inde",
            "aliments_toxiques": [
                {"aliment": "Avocat", "danger": "CRITIQUE", "effets": "Perséine — cardiotoxicité."},
                {"aliment": "Chocolat", "danger": "CRITIQUE", "effets": "Fatal même en très petite quantité."},
                {"aliment": "Oignon, ail, poireau", "danger": "CRITIQUE", "effets": "Anémie hémolytique."},
                {"aliment": "Rhubarbe (feuilles et tige)", "danger": "CRITIQUE", "effets": "Acide oxalique — insuffisance rénale aiguë."},
                {"aliment": "Pomme de terre crue", "danger": "ÉLEVÉ", "effets": "Solanine."},
                {"aliment": "Chou en excès", "danger": "MODÉRÉ", "effets": "Ballonnements, stase digestive."},
            ],
        },
    }
    key = species.lower().strip()
    result = TOXIC_FOODS.get(key)
    if not result:
        return json.dumps({"erreur": f"Espèce '{species}' non reconnue.", "especes_disponibles": list(TOXIC_FOODS.keys())}, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_species_vulnerabilities(species: str) -> str:
    """
    Retourne les vulnérabilités de santé spécifiques à l'espèce et les
    conditions médicales les plus fréquentes à surveiller.

    species : espèce parmi 'dog', 'cat', 'rabbit', 'bird', 'hamster',
              'guinea_pig', 'turtle', 'ferret'
    """
    VULNERABILITIES = {
        "dog": {
            "espece": "Chien",
            "esperance_de_vie": "10–15 ans selon la taille",
            "vulnerabilites_principales": [
                "Dilatation-torsion gastrique (races profondes : bouvier, dogue, grand danois) — URGENCE VITALE",
                "Dysplasie de la hanche (labrador, berger allemand, golden retriever)",
                "Maladies cardiaques valvulaires (cavalier King Charles — MVD précoce)",
                "Épilepsie idiopathique (border collie, berger belge, labrador)",
                "Allergies atopiques et maladies de la peau (bouledogue, shar-peï, dalmatien)",
                "Obésité et diabète secondaire (labrador, beagle)",
                "Hernies discales (teckel, pékinois, beagle)",
                "Parvovirose et maladie de Carré (chiots non vaccinés)",
            ],
            "signes_specifiques_urgence": [
                "Abdomen ballonné + tentatives de vomir infructueuses → torsion gastrique",
                "Effondrement soudain → choc ou arrêt cardiaque",
                "Boiterie postérieure soudaine → hernie discale ou embolie",
            ],
        },
        "cat": {
            "espece": "Chat",
            "esperance_de_vie": "14–20 ans (chats d'intérieur), 7–12 ans (extérieur)",
            "vulnerabilites_principales": [
                "Insuffisance rénale chronique (IRC) — affecte 30–40% des chats > 10 ans",
                "Hyperthyroïdie (chat > 8 ans — très fréquente)",
                "Obstruction urétrale (mâle — URGENCE VITALE)",
                "Lipidose hépatique (anorexie > 48h — particulier au chat)",
                "Cardiomyopathie hypertrophique (HCM) — maine coon, ragdoll, persan",
                "Leucémie féline (FeLV) et immunodéficience féline (FIV)",
                "Diabète sucré (type 2 — mâle castré en surpoids)",
                "Asthme félin (surtout en ville, chats d'appartement)",
            ],
            "signes_specifiques_urgence": [
                "Respiration gueule ouverte → urgence respiratoire absolue",
                "Cri aigu + paralysie des postérieurs → thrombose aortique",
                "Position de squattage sans uriner → obstruction urétrale CRITIQUE",
            ],
        },
        "rabbit": {
            "espece": "Lapin",
            "esperance_de_vie": "8–12 ans",
            "vulnerabilites_principales": [
                "Stase digestive / Iléus (toute douleur, stress ou manque de foin) — URGENCE VITALE",
                "Maladie VHD (Viral Haemorrhagic Disease) — mortelle, vaccin indispensable",
                "Myxomatose — mortelle sans vaccination",
                "Maladies dentaires (malocclusion, spurs) — fréquentes chez les races naines",
                "Pasteurellose respiratoire (snuffles)",
                "Encephalitozoon cuniculi (parasite neurologique)",
                "Cancer utérin (lapines non stérilisées > 2 ans — 80% d'incidence)",
            ],
            "signes_specifiques_urgence": [
                "Absence de crottes + ventre ballonné → stase digestive urgente",
                "Torticolis, roulade, nystagmus → E. cuniculi ou otite profonde",
                "Paralysie des postérieurs → fracture vertébrale (manipulation inadaptée)",
            ],
        },
        "bird": {
            "espece": "Oiseaux (perroquet, perruche, canari, cockatiel)",
            "esperance_de_vie": "5–80 ans selon l'espèce",
            "vulnerabilites_principales": [
                "Psittacose (Chlamydophila psittaci) — zoonotique, transmissible à l'humain",
                "Aspergillose pulmonaire (champignon — stress, immunodépression)",
                "PBFD (Psittacine Beak and Feather Disease)",
                "Méga-bactérie (Macrorhabdus ornithogaster) — canaris surtout",
                "Carence en vitamine A (alimentation en graines exclusivement)",
            ],
            "signes_specifiques_urgence": [
                "Gonflement, plumes ébouriffées → détresse sévère — urgence",
                "Dyspnée ou respiration à queue → urgence respiratoire",
                "Œuf bloqué (femelle) → dystocie — urgence",
            ],
        },
        "hamster": {
            "espece": "Hamster",
            "esperance_de_vie": "2–3 ans",
            "vulnerabilites_principales": [
                "Wet tail (entérite proliférative — Lawsonia intracellularis) — mortel en 24–48h",
                "Diabète (hamster Campbell — prédisposition génétique)",
                "Abcès dentaires (fréquents)",
                "Tumeurs cutanées et mélanomes",
                "Déshydratation rapide (très petite taille)",
            ],
            "signes_specifiques_urgence": [
                "Selles liquides + queue mouillée + prostration → wet tail, urgence en heures",
                "Joues gonflées asymétriques → abcès dentaire ou impaction",
                "Torpeur prolongée hors hibernation → hypoglycémie ou hypothermie",
            ],
        },
        "guinea_pig": {
            "espece": "Cochon d'Inde",
            "esperance_de_vie": "4–8 ans",
            "vulnerabilites_principales": [
                "Carence en vitamine C (scorbut — le cobaye ne synthétise pas la vitamine C)",
                "Stase digestive (comme le lapin — urgence vitale)",
                "Malocclusion dentaire (dents qui poussent toute la vie)",
                "Pneumonie bactérienne (Bordetella, Streptococcus)",
                "Pododermatite (maladie des pattes — sol inadapté, obésité)",
                "Gale sarcoptique (très fréquente, prurit intense)",
            ],
            "signes_specifiques_urgence": [
                "Gencives pâles + faiblesse + poils ternes → carence en vitamine C avancée",
                "Absence de crottes + position voûtée → stase digestive urgente",
                "Prurit intense + croûtes → gale sarcoptique (traitement urgent)",
            ],
        },
        "turtle": {
            "espece": "Tortue (terrestre et aquatique)",
            "esperance_de_vie": "30–100+ ans selon l'espèce",
            "vulnerabilites_principales": [
                "Carence en UVB (rachitisme, ramollissement de la carapace)",
                "Carence en vitamine A (problèmes oculaires, respiratoires)",
                "Pneumonie (hibernation mal conduite, refroidissement)",
                "Obstruction intestinale (substrat ingéré, corps étranger)",
                "Shell rot (infections fongiques/bactériennes de la carapace)",
            ],
            "signes_specifiques_urgence": [
                "Carapace molle ou qui sonne creux → carence UVB avancée",
                "Yeux gonflés fermés + respiration sifflante → urgence pneumonie/carence A",
                "Femelle qui creuse partout sans pondre → dystocie",
            ],
        },
        "ferret": {
            "espece": "Furet",
            "esperance_de_vie": "6–10 ans",
            "vulnerabilites_principales": [
                "Insulinome (tumeur des cellules bêta — très fréquente après 3 ans)",
                "Maladie surrénalienne (hyperplasie ou tumeur — perte de poils, vulve gonflée)",
                "Lymphome (fréquent après 4 ans)",
                "Cardiomyopathie dilatée",
                "Obstruction intestinale par corps étranger (caoutchouc, mousse — furets très curieux)",
            ],
            "signes_specifiques_urgence": [
                "Faiblesse postérieure + tremblements + hypersalivation → crise hypoglycémique (insulinome)",
                "Alopécie symétrique + vulve gonflée (femelle) → maladie surrénalienne",
                "Vomissements + arrêt transit + douleur abdominale → corps étranger",
            ],
        },
    }
    key = species.lower().strip()
    result = VULNERABILITIES.get(key)
    if not result:
        return json.dumps({"erreur": f"Espèce '{species}' non reconnue.", "especes_disponibles": list(VULNERABILITIES.keys())}, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_vaccination_schedule(species: str, age_months: int = 0) -> str:
    """
    Retourne le calendrier vaccinal recommandé pour une espèce donnée,
    adapté à l'âge de l'animal si précisé.

    species    : 'dog', 'cat', 'rabbit', 'ferret'
    age_months : âge de l'animal en mois (0 = inconnu → programme complet affiché)
    """
    SCHEDULES = {
        "dog": {
            "espece": "Chien",
            "vaccins_essentiels": [
                {"age": "6–8 semaines", "vaccin": "DHPPi (Carré, Hépato, Parvo, Parainfluenza) — 1ère injection"},
                {"age": "10–12 semaines", "vaccin": "DHPPi rappel + Leptospirose 1ère injection"},
                {"age": "14–16 semaines", "vaccin": "DHPPi rappel + Leptospirose rappel + Rage (obligatoire)"},
                {"age": "12–16 mois", "vaccin": "Rappel annuel complet (DHPPi + Lepto + Rage)"},
                {"age": "Adulte annuel", "vaccin": "Rappel DHPPi + Leptospirose + Rage selon législation locale"},
            ],
            "vaccins_optionnels": [
                "Bordetella bronchiseptica (toux du chenil) — si contact avec d'autres chiens",
                "Piroplasmose (Babesia) — si zone endémique de tiques",
                "Leishmaniose — si zone méditerranéenne endémique",
            ],
            "note": "La Rage est obligatoire pour les déplacements internationaux (passeport vétérinaire requis).",
        },
        "cat": {
            "espece": "Chat",
            "vaccins_essentiels": [
                {"age": "8 semaines", "vaccin": "Typhus (PRC) : Panleucopénie, Rhinotrachéite, Calicivirus — 1ère injection"},
                {"age": "12 semaines", "vaccin": "PRC rappel + Leucémie féline (FeLV) 1ère injection (si chat extérieur)"},
                {"age": "16 semaines", "vaccin": "PRC 3ème injection + FeLV rappel + Rage (si extérieur/voyage)"},
                {"age": "12–16 mois", "vaccin": "Rappel annuel PRC + FeLV (si extérieur)"},
                {"age": "Adulte annuel", "vaccin": "Rappel PRC tous les 1–3 ans selon le vaccin (modifié vivant = 3 ans)"},
            ],
            "vaccins_optionnels": [
                "Chlamydophila felis — si chat en collectivité ou chatterie",
                "FIV — disponible dans certains pays (non disponible en Europe)",
            ],
            "note": "Les chats d'intérieur strict peuvent avoir un protocole allégé — à discuter avec le vétérinaire.",
        },
        "rabbit": {
            "espece": "Lapin",
            "vaccins_essentiels": [
                {"age": "5–6 semaines", "vaccin": "VHD-1 (Maladie Hémorragique Virale classique) — 1ère injection"},
                {"age": "8–9 semaines", "vaccin": "Myxomatose + VHD-2 (nouveau variant) — combiné ou séparé"},
                {"age": "3 mois", "vaccin": "Rappel VHD-1 si primo-vaccination précoce"},
                {"age": "Annuel", "vaccin": "Rappel VHD-1 + Myxomatose + VHD-2 — obligatoire chaque année"},
            ],
            "vaccins_optionnels": [],
            "note": "Les lapins extérieurs ou en contact avec des moustiques doivent être vaccinés sans exception. La VHD et la myxomatose sont mortelles sans vaccination.",
        },
        "ferret": {
            "espece": "Furet",
            "vaccins_essentiels": [
                {"age": "8 semaines", "vaccin": "Maladie de Carré (Distemper) — 1ère injection"},
                {"age": "11 semaines", "vaccin": "Maladie de Carré — rappel"},
                {"age": "14 semaines", "vaccin": "Maladie de Carré — 3ème injection + Rage"},
                {"age": "Annuel", "vaccin": "Rappel Carré + Rage"},
            ],
            "vaccins_optionnels": [
                "Grippe (influenza) — si contact humain avec grippe saisonnière",
            ],
            "note": "Le furet est sensible à la grippe humaine et à la maladie de Carré. Ces vaccinations sont indispensables.",
        },
    }
    key = species.lower().strip()
    result = SCHEDULES.get(key)
    if not result:
        return json.dumps({"erreur": f"Espèce '{species}' non reconnue.", "especes_disponibles": list(SCHEDULES.keys())}, ensure_ascii=False)

    if age_months > 0:
        result["age_actuel_mois"] = age_months
        if age_months < 3:
            result["statut_vaccinal"] = "Primo-vaccination en cours — vérifier le calendrier avec le vétérinaire."
        elif age_months < 12:
            result["statut_vaccinal"] = "Jeune animal — s'assurer que la primo-vaccination est complète."
        else:
            result["statut_vaccinal"] = "Animal adulte — rappels annuels à maintenir."

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_breed_specific_risks(breed: str) -> str:
    """
    Retourne les risques de santé spécifiques à une race canine ou féline,
    avec les examens de dépistage recommandés.

    breed : nom de la race en français ou anglais
    (ex: 'labrador', 'berger allemand', 'golden retriever', 'bulldog',
         'maine coon', 'persan', 'teckel', 'carlin', 'yorkshire')
    """
    BREED_RISKS = {
        "labrador": {
            "race": "Labrador Retriever",
            "risques_principaux": [
                "Dysplasie de la hanche et du coude (dépistage radiographique recommandé avant reproduction)",
                "Obésité — prédisposition génétique forte (gène POMC)",
                "Myopathie du labrador (forme musculaire héréditaire)",
                "Rétinopathie progressive (PRA) et cataracte héréditaire",
                "Epilepsie idiopathique",
            ],
            "depistages_recommandes": ["Radiographie hanches/coudes à 12 mois", "Examen ophtalmologique annuel", "Test ADN PRA", "Pesée mensuelle"],
            "age_moyen_detection": "2–5 ans pour les dysplasies, 3–7 ans pour les maladies oculaires",
        },
        "berger allemand": {
            "race": "Berger Allemand (German Shepherd)",
            "risques_principaux": [
                "Dysplasie de la hanche (très fréquente — dépistage obligatoire avant reproduction)",
                "Myélopathie dégénérative (DM) — paralysie progressive des postérieurs après 7 ans",
                "Dilatation-torsion gastrique (thorax profond)",
                "Pancréatite exocrine (insuffisance pancréatique exocrine — IPE)",
                "Hémangiosarcome splénique",
            ],
            "depistages_recommandes": ["Radiographie hanches à 12 mois", "Test ADN DM", "Alimentation en 2 repas (prévention DTG)", "Échographie abdominale annuelle après 8 ans"],
            "age_moyen_detection": "1–3 ans pour la hanche, 7–14 ans pour la DM",
        },
        "golden retriever": {
            "race": "Golden Retriever",
            "risques_principaux": [
                "Cancer (taux le plus élevé de toutes les races : lymphome, hémangiosarcome, ostéosarcome)",
                "Dysplasie de la hanche et du coude",
                "Maladies cardiaques (sténose sous-aortique — SAS)",
                "Hypothyroïdie",
                "Hypersensibilités cutanées et allergies alimentaires",
            ],
            "depistages_recommandes": ["Échographie abdominale annuelle après 6 ans", "Radiographie hanches/coudes", "ECG et auscultation cardiaque", "Bilan thyroïdien annuel après 5 ans"],
            "age_moyen_detection": "5–8 ans pour les cancers, 1–2 ans pour les dysplasies",
        },
        "bulldog": {
            "race": "Bouledogue Anglais / Bulldog",
            "risques_principaux": [
                "Syndrome brachycéphale obstructif (BOAS) — difficultés respiratoires chroniques",
                "Dermatite des plis cutanés (infection fréquente dans les plis du museau)",
                "Dysplasie de la hanche sévère",
                "Hémivértèbres et anomalies de la queue (queue en tire-bouchon)",
                "Coups de chaleur — TRÈS vulnérable (ne peut pas thermoréguler normalement)",
            ],
            "depistages_recommandes": ["Évaluation BOAS vétérinaire", "Nettoyage quotidien des plis", "Radiographie hanche", "Éviter tout exercice par temps chaud"],
            "age_moyen_detection": "Dès 6 mois–2 ans pour le BOAS",
        },
        "maine coon": {
            "race": "Maine Coon",
            "risques_principaux": [
                "Cardiomyopathie hypertrophique (HCM) — forme héréditaire très fréquente (mutation MYH7 et MYBPC3)",
                "Dysplasie de la hanche",
                "Polykystose rénale (PKD) — moins fréquente que chez le persan",
                "Spinal Muscular Atrophy (SMA) — atrophie musculaire spinale héréditaire",
            ],
            "depistages_recommandes": ["Échocardiographie tous les 1–2 ans à partir de 2 ans", "Test ADN HCM, SMA", "Radiographie hanche", "Créatinine/SDMA annuel après 7 ans"],
            "age_moyen_detection": "2–6 ans pour la HCM",
        },
        "persan": {
            "race": "Persan",
            "risques_principaux": [
                "Polykystose rénale (PKD) — 40% des persans porteurs si non testés",
                "Syndrome brachycéphale (difficultés respiratoires, larmoiement chronique)",
                "Maladies dentaires (malocclusion sévère)",
                "Cardiomyopathie hypertrophique (HCM)",
                "Dermatophytose (teigne) — pelage long favorise la prolifération",
            ],
            "depistages_recommandes": ["Test ADN PKD (obligatoire avant reproduction)", "Échocardiographie annuelle après 3 ans", "Bilan rénal annuel après 5 ans", "Nettoyage facial et oculaire quotidien"],
            "age_moyen_detection": "3–7 ans pour la PKD (kystes visibles en échographie)",
        },
        "teckel": {
            "race": "Teckel (Dachshund)",
            "risques_principaux": [
                "Hernie discale thoraco-lombaire (Hansen type I) — 25% des teckels affectés",
                "Acanthosis nigricans (hyperpigmentation axillaire — race-spécifique)",
                "Surdité congénitale (teckels à robe mouchetée dapple)",
                "Luxation de la rotule",
                "Hypothyroïdie",
            ],
            "depistages_recommandes": ["Éviter escaliers et sauts (prévention hernie)", "IRM si signes neurologiques", "Audiométrie si robe dapple", "Contrôle thyroïdien après 5 ans"],
            "age_moyen_detection": "3–7 ans pour les hernies discales",
        },
        "carlin": {
            "race": "Carlin (Pug)",
            "risques_principaux": [
                "Syndrome brachycéphale obstructif sévère (BOAS) — le plus touché des brachycéphales",
                "Encéphalite du carlin (PDE) — maladie neurologique fatale, génétique",
                "Hémivertèbres et anomalies rachidiennes",
                "Dermatite des plis sévère",
                "Coups de chaleur — extrêmement vulnérable",
                "Luxation de la rotule",
            ],
            "depistages_recommandes": ["Évaluation BOAS obligatoire", "IRM si signes neurologiques", "Nettoyage quotidien des plis", "Activité physique limitée et sans chaleur"],
            "age_moyen_detection": "Dès 1 an pour le BOAS, 2–7 ans pour la PDE",
        },
        "yorkshire": {
            "race": "Yorkshire Terrier",
            "risques_principaux": [
                "Luxation de la rotule (grades I à IV — très fréquente)",
                "Hépatite chronique active et shunt portosystémique",
                "Hypoglycémie néonatale (chiots)",
                "Trachée hypoplasique (collapsus trachéal)",
                "Maladies dentaires (dents de lait persistantes)",
            ],
            "depistages_recommandes": ["Radiographie rotule", "Bilan hépatique annuel", "Utiliser harnais (jamais collier)", "Extraction dents de lait si persistantes après 6 mois"],
            "age_moyen_detection": "6 mois–3 ans pour la rotule, 2–5 ans pour le shunt",
        },
    }
    key = breed.lower().strip().replace("-", " ").replace("_", " ")
    # Recherche exacte puis partielle
    result = BREED_RISKS.get(key)
    if not result:
        for k, v in BREED_RISKS.items():
            if k in key or key in k:
                result = v
                break
    if not result:
        return json.dumps({
            "erreur": f"Race '{breed}' non reconnue.",
            "races_disponibles": list(BREED_RISKS.keys()),
            "conseil": "Utilisez get_species_vulnerabilities(species) pour des informations générales par espèce.",
        }, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────────────
# EXPORTS (groupes par agent)
# ──────────────────────────────────────────────────────────────────

# ContextRAGAgent : tous les outils KB — fetch tout en une seule passe
# Le LLM décide quels outils appeler selon les symptômes détectés
RAG_CONTEXT_TOOLS = [
    get_possible_causes, get_symptom_info, get_red_flags,
    get_home_care, get_evolution_timeline,
    get_first_aid_steps, get_species_vulnerabilities,
    get_vaccination_schedule, get_breed_specific_risks, get_toxic_foods,
]

# PredictionAgent : web uniquement (KB déjà dans _kb_context)
PREDICTION_TOOLS = [web_search_vet, search_wikipedia_vet]

# CareAgent : plus de KB tools (données dans _kb_context)
CARE_TOOLS       = []

# ValidationAgent : vérification KB uniquement
VALIDATION_TOOLS = [list_kb_symptoms, get_symptom_info, get_red_flags]

# EmergencyAgent : runtime uniquement (vétérinaires + urgences web)
EMERGENCY_TOOLS  = [
    find_partner_vets, get_first_aid_steps, get_toxic_foods, web_search_vet,
]

# RecommendationAgent (unifié care+emergency+recommendation) : urgences + web
RESPONSE_TOOLS = [
    find_partner_vets, get_first_aid_steps, get_toxic_foods, web_search_vet,
]
