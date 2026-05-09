
import json, re
from pathlib import Path
from collections import Counter
from tqdm import tqdm

ANIMALS = [
    "golden retriever","labrador retriever","german shepherd","border collie",
    "yorkshire terrier","jack russell","cocker spaniel","shih tzu","maltese",
    "beagle","poodle","bulldog","chihuahua","husky","dalmatian","pomeranian",
    "rottweiler","doberman","boxer","dachshund","corgi","pug","great dane",
    "persian","siamese","maine coon","ragdoll","bengal","british shorthair",
    "tabby","tabby cat","calico","abyssinian","sphynx","burmese",
    "budgie","budgerigar","cockatiel","cockatoo","macaw","lovebird","finch",
    "guinea pig","gerbil","chinchilla","hedgehog","bearded dragon",
    "gecko","iguana","chameleon","tortoise","turtle","goldfish","betta",
    "dog","cat","pet","puppy","kitten","rabbit","bunny","bird","fish",
    "hamster","rat","mouse","duck","goose","chicken","horse","ferret",
    "retriever","terrier","spaniel","shepherd","collie","poodle",
    "chien","chat","lapin","oiseau","perruche","cochon d'inde","cobaye",
    "furet","tortue","lezard","serpent","cheval","perroquet","canari",
    "chaton","chiot",
]
SYMPTOMS = [
    "scratching","itching","pruritus","alopecia","hair loss",
    "vomiting","vomit","regurgitating","nausea","retching",
    "diarrhea","diarrhoea","loose stool","bloody stool","bloody diarrhea",
    "constipation","straining","bloated","distended",
    "not eating","refusing food","loss of appetite","anorexia","inappetence",
    "not drinking","excessive thirst","polydipsia","polyuria",
    "limping","lame","lameness","not bearing weight",
    "coughing","sneezing","wheezing","gasping","choking","gagging",
    "difficulty breathing","labored breathing","rapid breathing",
    "open mouth breathing","breathing fast","breathing rapidly","heavy breathing",
    "lethargy","lethargic","weak","weakness","tired","fatigue","sluggish",
    "seizure","convulsion","trembling","shaking","twitching",
    "collapse","collapsed","unconscious","unresponsive","not moving",
    "paralyzed","paralysis","bleeding","hemorrhage","blood","wound",
    "swollen","swelling","lump","bump","mass","growth","abscess",
    "discharge","runny nose","eye discharge","nasal discharge","watery eyes",
    "fever","high temperature","hypothermia","shivering",
    "weight loss","losing weight","thin","emaciated",
    "pain","painful","crying","whimpering","howling",
    "disoriented","confused","wobbly","ataxia","head tilt","circling",
    "jaundice","pale gums","blue gums","skin lesion","rash","hot spot",
    "dermatitis","mange","ear infection","ear mites","head shaking",
    "cloudy eye","red eye","squinting",
    "cannot fly","fell","falling","dropped","stumbling",
    "refuses to drink","refuses to eat","stopped eating","not active",
    "not playful","looks pale","seems weak","very weak",
    "vomissement","diarrhee","ne mange plus","ne boit plus","boite",
    "gratte","convulse","tremble","saigne","plaie","gonfle","fievre",
    "fatigue","faible","abattu","perd du poids","toux","eternue",
]
DURATIONS = [
    r"since (yesterday|this morning|last night|this afternoon|today|tonight)",
    r"since (monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
    r"since \d+ (hour|day|week|month|year)s?",
    r"since (a few|several|some|many) (hour|day|week|month|year)s?",
    r"since (last|this) (week|month|year|morning|evening|night|afternoon)",
    r"for (the past |the last )?\d+ (hour|day|week|month|year)s?",
    r"for (a few|several|some|many) (hour|day|week|month|year)s?",
    r"\d+ (hour|day|week|month|year)s? ago",
    r"(this|last) (morning|evening|night|week|month|year|afternoon)",
    r"(yesterday|today|tonight|last night|this morning|this evening)",
    r"(just|recently|suddenly|all of a sudden)",
    r"since (a while|some time|a long time)",
    r"depuis (hier|ce matin|hier soir|ce soir|aujourd'hui)",
    r"depuis \d+ (heure|jour|semaine|mois|an)s?",
    r"il y a \d+ (heure|jour|semaine|mois|an)s?",
]
BODY_PARTS = [
    "paw","paws","front paw","back paw","front leg","back leg","hind leg",
    "forelimb","hindlimb","leg","legs","foot","feet","claw","claws",
    "nail","nails","ear","ears","eye","eyes","nose","mouth","tongue",
    "teeth","tooth","gum","gums","jaw","muzzle","snout","whisker",
    "whiskers","face","head","skull","chin","neck","throat","chest",
    "breast","belly","abdomen","stomach","flank","back","spine",
    "shoulder","hip","pelvis","rib","ribs","tail","base of tail",
    "lung","lungs","heart","liver","kidney","kidneys","bladder",
    "intestine","bowel","colon","rectum","anus","uterus","ovary",
    "testicle","prostate","spleen","pancreas","thyroid",
    "lymph node","lymph nodes","skin","fur","coat","hair",
    "feather","feathers","scale","scales","cornea","retina",
    "iris","pupil","third eyelid","eyelid","wing","wings","beak","perch",
    "patte","pattes","oreille","oreilles","oeil","yeux","nez","bouche",
    "langue","dent","dents","gencive","machoire","cou","gorge",
    "poitrine","ventre","abdomen","dos","queue","peau","poil","poils",
    "griffe","griffes","poumon","coeur","foie","rein","reins",
]

dur_patterns = [re.compile(p, re.IGNORECASE) for p in DURATIONS]
animals_s    = sorted(set(ANIMALS),    key=len, reverse=True)
symptoms_s   = sorted(set(SYMPTOMS),   key=len, reverse=True)
body_s       = sorted(set(BODY_PARTS), key=len, reverse=True)

def spans_overlap(existing, start, end):
    return any(not (end <= s or start >= e) for s, e, _ in existing)

def annotate(text):
    entities = []
    for kw in animals_s:
        for m in re.finditer(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
            if not spans_overlap(entities, m.start(), m.end()):
                entities.append([m.start(), m.end(), "ANIMAL"])
    for kw in symptoms_s:
        for m in re.finditer(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
            if not spans_overlap(entities, m.start(), m.end()):
                entities.append([m.start(), m.end(), "SYMPTOM"])
    for pat in dur_patterns:
        for m in pat.finditer(text):
            if not spans_overlap(entities, m.start(), m.end()):
                entities.append([m.start(), m.end(), "DUREE"])
    for kw in body_s:
        for m in re.finditer(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
            if not spans_overlap(entities, m.start(), m.end()):
                entities.append([m.start(), m.end(), "BODY_PART"])
    entities.sort(key=lambda x: x[0])
    return entities

# ── Corriger UNIQUEMENT le test set ──────────────────────────────
path = Path("../data/doctoagent_test_clean.json")

with open(path, encoding="utf-8") as f:
    data = json.load(f)

print(f"Test set : {len(data)} records")
print("Re-annotation avec listes enrichies...")

stats_before = Counter()
stats_after  = Counter()

for r in tqdm(data):
    for e in r.get("entities", []):
        stats_before[e[2]] += 1
    r["entities"] = annotate(r["text"])
    for e in r["entities"]:
        stats_after[e[2]] += 1

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nEntites AVANT :")
for label in ["ANIMAL","SYMPTOM","DUREE","BODY_PART"]:
    print(f"  {label:<12} : {stats_before.get(label,0)}")

print(f"\nEntites APRES :")
for label in ["ANIMAL","SYMPTOM","DUREE","BODY_PART"]:
    print(f"  {label:<12} : {stats_after.get(label,0)}")

print(f"\nTest set corrige ! Lance maintenant :")
print(f"  py eval_ner_hybrid.py")
