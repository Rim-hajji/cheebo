"""
annotate_supplement_entities.py
================================
Annote automatiquement les entités NER dans les fichiers supplément :
  ANIMAL, SYMPTOM, BODY_PART, DUREE

Usage:
  py annotate_supplement_entities.py

Résultat : les fichiers supplément sont mis à jour avec les spans d'entités.
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent / "dataset_builder" / "data_real"

TARGETS = [
    BASE / "doctoagent_train_supplement.json",
    BASE / "doctoagent_train_supplement_v2.json",
]

# ──────────────────────────────────────────────────────────────────
# PATTERNS D'ENTITÉS
# Chaque pattern est (regex, label). On cherche dans le texte original
# avec re.IGNORECASE pour retrouver les offsets réels.
# ──────────────────────────────────────────────────────────────────

ANIMAL_REGEXES = [
    r"chien(?:ne)?s?",
    r"chiot(?:te)?s?",
    r"chat(?:te)?s?",
    r"chaton(?:ne)?s?",
    r"lapin(?:e)?s?",
    r"lapereau",
    r"hamster",
    r"perroquet",
    r"furet",
    r"perruche",
    r"canari",
    r"cacatoès",
    r"moineau",
    r"oiseau(?:x)?",
    r"\bara\b",
    r"tortue",
    r"reptile",
    r"lézard",
    r"serpent",
    r"gecko",
    r"cheval(?:ux)?",
    r"jument",
    r"poney",
    r"pouliche",
    r"cochon\s+d'inde",
    r"cobaye",
    r"\brat\b",
    r"rongeur",
    r"souris\b",
    r"cochon\s+d\'inde",
    r"poisson",
    r"chinchilla",
    r"hérisson",
    r"dinde",
    r"poule",
]

BODY_PART_REGEXES = [
    r"pattes?\s+arrière(?:s)?",
    r"pattes?\s+avant(?:s)?",
    r"patte(?:s)?",
    r"yeux",
    r"oeil",
    r"oreille(?:s)?",
    r"ventre",
    r"abdomen",
    r"gueule",
    r"bouche",
    r"\bdent(?:s)?\b",
    r"gencive(?:s)?",
    r"\bnez\b",
    r"museau",
    r"narine(?:s)?",
    r"\bpeau\b",
    r"\bdos\b",
    r"flanc(?:s)?",
    r"queue(?:s)?",
    r"coussinet(?:s)?",
    r"jambe(?:s)?",
    r"sabot(?:s)?",
    r"pied(?:s)?",
    r"\btête\b",
    r"crâne",
    r"\bcou\b",
    r"\bgorge\b",
    r"poitrine",
    r"\bfoie\b",
    r"\brein(?:s)?\b",
    r"cœur|coeur",
    r"poumon(?:s)?",
    r"vessie",
    r"mamelle(?:s)?",
    r"vulve",
    r"pupille(?:s)?",
    r"cornée",
    r"aile(?:s)?",
    r"pelage",
    r"fourrure",
    r"poil(?:s)?",
    r"plume(?:s)?",
    r"écaille(?:s)?",
    r"boulet(?:s)?",
    r"antérieur(?:s)?",
    r"postérieur(?:s)?",
    r"estomac",
    r"intestin(?:s)?",
]

DUREE_REGEXES = [
    # "depuis hier/ce matin/ce soir/..."
    r"depuis\s+(?:hier|avant-hier|ce\s+matin|ce\s+soir|ce\s+midi|cette\s+nuit|ce\s+week-?end|la\s+nuit)",
    # "depuis X jours/semaines/mois/heures/minutes"
    r"depuis\s+\d+\s+(?:jours?|semaines?|mois|heures?|minutes?|ans?)",
    # "depuis quelques/plusieurs jours/semaines..."
    r"depuis\s+(?:quelques|plusieurs|environ|plus\s+de|moins\s+de)\s+(?:\d+\s+)?(?:jours?|semaines?|mois|heures?|minutes?|ans?)",
    # "depuis longtemps / depuis peu / depuis toujours"
    r"depuis\s+(?:longtemps|peu|toujours|sa\s+naissance|son\s+adoption)",
    # "il y a / ya X min/h/jours..."
    r"(?:il\s+y\s+a|ya)\s+\d+\s+(?:jours?|semaines?|mois|heures?|minutes?|ans?|min\b|h\b)",
    # "ça fait / cela fait X"
    r"(?:ça|cela)\s+fait\s+\d+\s+(?:jours?|semaines?|mois|heures?|minutes?)",
    # "depuis la semaine dernière"
    r"depuis\s+(?:la\s+semaine|le\s+mois|l'an)\s+(?:dernière?|dernier|passée?|passé)",
    # short: "depuis 3j", "depuis 2h"
    r"depuis\s+\d+\s*(?:j\b|h\b|min\b|sem\b)",
    # "for X days/weeks" (English)
    r"for\s+(?:the\s+past\s+)?\d+\s+(?:days?|weeks?|months?|hours?|minutes?)",
    # "since yesterday/this morning" (English)
    r"since\s+(?:yesterday|this\s+morning|last\s+night|this\s+evening)",
]

SYMPTOM_REGEXES = [
    # alimentation
    r"(?:ne\s+|n')mange\s+(?:plus|pas|rien|guère)",
    r"refuse\s+(?:de\s+manger|sa\s+gamelle|(?:les|ses|la|le)\s+\w+)",
    r"n'a\s+plus\s+d'appétit",
    r"anorexique?",
    r"perte\s+d'appétit",
    r"(?:ne\s+|n')boit?\s+(?:plus|pas)",
    r"refuse\s+de\s+boire",
    r"vomit|vomissements?|régurgite|rend\b",
    r"diarrhée|selles?\s+molles?|colite",
    # respiration
    r"(?:ne\s+|n')respire?\s+(?:plus|pas|bien|normalement)",
    r"difficultés?\s+(?:à\s+)?respirer",
    r"détresse\s+respiratoire",
    r"halète|halètement",
    r"respiration\s+(?:sifflante|bruyante|difficile|superficielle|rapide)",
    r"langue\s+(?:bleue|violette|blanche)",
    r"muqueuses?\s+(?:bleues?|pâles?|blanches?)",
    # locomotion
    r"boite|claudique|boiterie|boitille",
    r"(?:ne\s+|n')(?:marche|se\s+lève|se\s+relève|peut\s+(?:pas|plus)\s+(?:marcher|bouger))",
    r"paralys[eé]|paralysie",
    r"(?:pattes?\s+)?(?:traîne|tombent|glissent)",
    r"tombe|chute|tombé",
    r"perd\s+(?:l')?équilibre",
    r"titube",
    r"ne\s+tient\s+(?:plus|pas)\s+(?:sur\s+ses\s+pattes?|debout)",
    # urgences
    r"convulse?|convulsions?|crises?\s+(?:convulsives?|épileptiques?)",
    r"inconscient|sans\s+connaissance|(?:ne\s+|n')répond\s+(?:plus|pas)",
    r"(?:a\s+)?perdu?\s+connaissance",
    r"saigne?|saignement|hémorragie|perd\s+du\s+sang",
    r"sang\s+(?:dans\s+les\s+urines?|frais|rouge)",
    r"vomit\s+(?:du\s+)?sang",
    # douleur
    r"gémit|crie\s+(?:de\s+douleur|de\s+peur)",
    r"souffre|souffrant",
    r"douleur|douloureux",
    r"semble\s+(?:avoir\s+)?(?:mal|souffrir)",
    # peau/pelage
    r"se\s+gratte|démangeaisons?|prurit",
    r"perd\s+(?:ses\s+)?(?:poils?|plumes?|fourrure)",
    r"alopécie",
    r"plaie|blessure|coupure|entaille|lacération|morsure",
    r"grosseur|masse|bosse|kyste|tumeur|abcès",
    r"gonfle?(?:ment)?|oedème|oedémateux",
    r"croûtes?|lésions?",
    # comportement
    r"(?:ne\s+|n')joue?\s+(?:plus|pas)",
    r"(?:se\s+)?cache(?:\s+sous)?",
    r"tremble(?:ments?)?",
    r"tourne\s+(?:en\s+cercle|en\s+rond|sur\s+lui-même)",
    r"tête\s+penchée?",
    r"abattu|prostré|léthargique|léthargie",
    r"fatigue?|fatigué",
    r"dort\s+(?:trop|beaucoup|excessivement)",
    r"agressive?|agressivité",
    r"pleure?\s+(?:la\s+nuit|beaucoup|tout\s+le\s+temps)",
    # urinaire
    r"(?:ne\s+|n')urine?\s+(?:plus|pas)",
    r"urines?\s+(?:fréquentes?|douloureuses?|par\s+petites?\s+quantités?|sanglantes?)",
    r"sang\s+dans\s+les\s+urines?",
    r"cystite",
    r"obstruction\s+urinaire",
    # divers
    r"maigrit|perd\s+du\s+poids|amaigrissement|perte\s+de\s+poids",
    r"bave|hypersalivation|salivation\s+excessive",
    r"éternue?|éternuements?",
    r"toux\s+(?:sèche|grasse|persistante|chronique)",
    r"tousse",
    r"fièvre",
    r"choc|état\s+de\s+choc",
    r"coma",
    r"plume\s+(?:ses\s+propres\s+)?plumes?",
    # anglais
    r"not\s+eating|loss\s+of\s+appetite|refusing\s+food",
    r"vomiting|throwing\s+up",
    r"diarrhea|loose\s+stools",
    r"limping|lame\b|difficulty\s+walking",
    r"seizure|convulsion|fit\b",
    r"bleeding|hemorrhage",
    r"not\s+breathing|difficulty\s+breathing",
    r"collapsed|unconscious",
    r"scratching|itching",
    r"losing\s+(?:weight|fur|feathers)",
    r"swollen|swelling",
    r"not\s+moving|paralyz",
    r"panting\b",
    r"dragging\s+(?:his|her|its)\s+(?:back\s+)?legs?",
    r"grinding\s+(?:his|her|its)\s+teeth",
]


def _find_spans(text: str, regexes: list[str], label: str) -> list[list]:
    spans = []
    for pat in regexes:
        try:
            for m in re.finditer(pat, text, re.IGNORECASE):
                spans.append([m.start(), m.end(), label])
        except re.error:
            pass
    return spans


def _remove_overlaps(spans: list[list]) -> list[list]:
    """
    Supprime les chevauchements : en cas de conflit, garde le span le plus long.
    En cas d'égalité de longueur, respecte la priorité d'ordre d'insertion.
    """
    if not spans:
        return []
    # Trier par position de début, puis par longueur décroissante
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    result = [spans[0]]
    for span in spans[1:]:
        last = result[-1]
        if span[0] < last[1]:
            # Chevauchement : garder le plus long
            if (span[1] - span[0]) > (last[1] - last[0]):
                result[-1] = span
        else:
            result.append(span)
    return sorted(result, key=lambda x: x[0])


def _priority_merge(all_spans: list[list]) -> list[list]:
    """
    Fusionne les spans de toutes les catégories en supprimant les chevauchements.
    Priorité : ANIMAL > DUREE > BODY_PART > SYMPTOM
    (Les spans ANIMAL et DUREE ne doivent pas être absorbés par SYMPTOM)
    """
    priority = {"ANIMAL": 0, "DUREE": 1, "BODY_PART": 2, "SYMPTOM": 3}
    all_spans.sort(key=lambda x: (x[0], -(x[1] - x[0]), priority.get(x[2], 9)))

    result = []
    for span in all_spans:
        if not result:
            result.append(span)
            continue
        last = result[-1]
        if span[0] < last[1]:
            # Chevauchement
            last_prio = priority.get(last[2], 9)
            cur_prio  = priority.get(span[2], 9)
            if cur_prio < last_prio:
                result[-1] = span  # remplacement prioritaire
            # sinon on ignore le nouveau span
        else:
            result.append(span)

    return sorted(result, key=lambda x: x[0])


def annotate(text: str) -> list[list]:
    """Retourne la liste des entités [start, end, label] pour un texte."""
    spans = []
    spans += _find_spans(text, ANIMAL_REGEXES,    "ANIMAL")
    spans += _find_spans(text, DUREE_REGEXES,     "DUREE")
    spans += _find_spans(text, BODY_PART_REGEXES, "BODY_PART")
    spans += _find_spans(text, SYMPTOM_REGEXES,   "SYMPTOM")
    return _priority_merge(spans)


def process_file(path: Path) -> None:
    if not path.exists():
        print(f"  [skip] Introuvable : {path}")
        return

    records = json.loads(path.read_text(encoding="utf-8"))
    annotated = 0
    for rec in records:
        text = rec.get("text", "")
        if not text:
            continue
        entities = annotate(text)
        rec["entities"] = entities
        if entities:
            annotated += 1

    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  OK : {path.name} ({len(records)} records, {annotated} annotés avec entités)")


def main():
    print("=" * 60)
    print("ANNOTATION AUTOMATIQUE DES ENTITÉS NER")
    print("=" * 60)
    for target in TARGETS:
        print(f"\n  Traitement : {target.name}")
        process_file(target)
    print("\n  TERMINÉ. Vérifiez les fichiers mis à jour.")
    print("  Conseil : relancez train_vetbert_ner.py après intégration des nouvelles données.")


if __name__ == "__main__":
    main()
