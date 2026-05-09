
import json, random
from pathlib import Path
from collections import Counter, defaultdict

# 50 phrases ask_advice diversifiees et naturelles
NEW_ASK_ADVICE = [
    # Depuis Reddit style
    "My cat has been sneezing a lot, should I be worried or is it just allergies?",
    "My dog ate a small piece of chocolate, do I need to go to the vet?",
    "How do I know if my rabbit is just tired or actually sick?",
    "My puppy cries at night, is this normal or should I see a vet?",
    "My senior cat lost some weight recently, when should I be concerned?",
    "Is it okay to give my dog Pepto-Bismol for an upset stomach?",
    "My dog got stung by a bee, what should I watch for?",
    "My cat scratches the furniture, is this a health issue or just behavior?",
    "My hamster is sleeping more than usual, should I take him to the vet?",
    "My dog ate some grass and vomited once, should I call the vet?",
    "Is it normal for my cat to drink more water in summer?",
    "My rabbit thumps a lot, is that a sign of stress or pain?",
    "My dog has been licking his paws a lot lately, what could it be?",
    "Is it safe to give my cat CBD oil for anxiety?",
    "My kitten has a small bump on her back, should I get it checked?",
    "My dog whines when I leave, is that separation anxiety or something medical?",
    "Is it okay if my cat eats a small amount of dog food by mistake?",
    "My bird is molting, is that normal or should I be worried?",
    "My dog gets car sick, what can I give him?",
    "My cat has been hiding more than usual, when should I worry?",

    # Depuis PetEVAL style (clinique)
    "Owner asking if follow-up blood test is necessary after recovery.",
    "Client enquiring whether second dose of antibiotics is required.",
    "Owner wants to know if weight loss in senior pet warrants investigation.",
    "Querying whether annual dental cleaning is recommended for this breed.",
    "Client asking if outdoor access is safe after recent vaccination.",
    "Owner asking whether mild limping after exercise needs attention.",
    "Requesting advice on appropriate diet for pet with kidney issues.",
    "Client asking if lethargy after neutering is expected.",
    "Owner querying whether ear cleaning at home is safe.",
    "Asking for guidance on managing arthritis pain at home.",

    # Questions mixtes FR/EN
    "Mon chien a mangé quelque chose dans le jardin, dois-je aller chez le vétérinaire ?",
    "Est-ce normal que mon chat dorme autant en hiver ?",
    "Mon lapin ne mange pas ses granulés, dois-je m'inquiéter ?",
    "Peut-on donner du paracétamol à un chien pour la douleur ?",
    "Mon chiot a eu ses vaccins hier et il semble fatigué, c'est normal ?",

    # Questions specifiques races
    "My French Bulldog breathes loudly, is that normal for the breed?",
    "My Dachshund has back pain sometimes, when should I see a vet?",
    "My Persian cat has eye discharge daily, is that normal?",
    "My Labrador eats everything he finds, should I be worried?",
    "My Siamese cat is very vocal, is that a health sign or just personality?",

    # Questions soins a domicile
    "How do I properly clean my dog's wound at home?",
    "Can I use hydrogen peroxide to clean my cat's cut?",
    "How do I give my cat a pill without stressing him?",
    "What is the best way to remove a tick from my dog?",
    "How do I know if my dog's stitches are healing properly?",
    "Is it safe to put Neosporin on my dog's wound?",
    "How do I help my dog lose weight safely?",
    "What home remedies help with dog constipation?",
    "How do I know if my cat is getting enough water?",
    "What signs tell me my pet is recovering well after surgery?",
]

random.seed(42)

data_path = Path("C:/Users/rim hajji/Desktop/module_docto_agent/dataset_builder/data_real/doctoagent_clean.json")
with open(data_path, encoding="utf-8") as f:
    data = json.load(f)

names = {0:"describe_symptom", 1:"ask_advice", 2:"emergency", 3:"follow_up"}

dist = Counter(r["intent"] for r in data)
print("Distribution avant :")
for i,n in names.items():
    print(f"  {n:<20} : {dist.get(i,0)}")

# Ajouter les nouvelles phrases
new_records = []
for phrase in NEW_ASK_ADVICE:
    new_records.append({
        "text"    : phrase,
        "intent"  : 1,
        "urgency" : "LOW",
        "entities": [],
        "source"  : "manual_ask_advice_diverse",
        "language": "en",
    })

data.extend(new_records)
print(f"\nAjoute : {len(new_records)} phrases diversifiees")
print(f"ask_advice total : {dist.get(1,0) + len(new_records)}")

# Re-equilibrer sur urgency uniquement (ne pas toucher l'intent)
# Garder toutes les classes intent
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

dist2 = Counter(r["intent"] for r in data)
print(f"\nDistribution finale :")
for i,n in names.items():
    print(f"  {n:<20} : {dist2.get(i,0)}")

print(f"\nTotal dataset : {len(data)}")
print(f"\nLance : py train_all_models_v2.py --fast --task intent")
