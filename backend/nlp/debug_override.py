
CRITICAL_KEYWORDS = [
    'urgent', 'urgence', 'blesse', 'saigne', 'sang', 'hemorragie',
    'respire plus', 'au secours', 'inconscient', 'paralyse',
    'convulse', 'grave', 'empoisonne', 'avale du poison',
    'emergency', 'wounded', 'unconscious', 'seizure', 'convuls',
    'poison', 'collapse', 'bleeding', 'dying', 'not breathing',
    'bloat', 'hit by car', 'critical', 'severe',
    'paralyz', 'help urgent', 'rush to vet',
]

tests = [
    'Should I take my dog to the vet for vomiting once?',
    'My budgie fell from his perch and cannot fly tonight',
    'Yorkshire terrier has a swollen paw after playing',
    'Mon chat vomit du sang depuis hier soir',
]

for text in tests:
    found = [kw for kw in CRITICAL_KEYWORDS if kw in text.lower()]
    print('Text  : ' + text[:60])
    print('Found : ' + str(found))
    print()
