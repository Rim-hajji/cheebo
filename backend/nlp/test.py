import spacy
nlp = spacy.load('models_v2/ner_model_spacy/model-best')

tests = [
    'My golden retriever keeps scratching his ear',
    'The Persian cat refuses to drink water since Tuesday',
    'Urgent my budgie fell from his perch and cannot fly',
    'Yorkshire terrier has a swollen paw after playing outside',
    'My old tabby cat seems very weak and confused today',
    'budgie stopped eating and looks pale',
    'My rabbit has been limping since this morning',
    'The hamster is breathing very fast tonight',
]

correct = 0
total   = 0

expected = {
    0: ['ANIMAL','SYMPTOM','BODY_PART'],
    1: ['ANIMAL','SYMPTOM','DUREE'],
    2: ['ANIMAL','SYMPTOM'],
    3: ['ANIMAL','SYMPTOM','BODY_PART'],
    4: ['ANIMAL','SYMPTOM'],
    5: ['ANIMAL','SYMPTOM'],
    6: ['ANIMAL','SYMPTOM','DUREE'],
    7: ['ANIMAL','SYMPTOM','DUREE'],
}

for i, text in enumerate(tests):
    doc    = nlp(text)
    found  = [ent.label_ for ent in doc.ents]
    expect = expected[i]
    ok     = all(e in found for e in expect)
    total += len(expect)
    correct += sum(1 for e in expect if e in found)
    status = 'OK' if ok else 'PARTIEL'
    print(f'[{status}] {text[:55]}')
    print(f'  Attendu  : {expect}')
    print(f'  Detecte  : {found}')
    print()

print(f'Score approximatif : {correct}/{total} = {correct/total:.2f}')