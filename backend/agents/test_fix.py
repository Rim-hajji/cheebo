from rag_agent import rag_agent

tests = [
    {
        'text'     : 'Mon chat ne mange plus depuis 2 jours',
        'translated': 'My cat has not eaten for 2 days',
        'entities' : [
            {'text': 'cat', 'label': 'ANIMAL'},
            {'text': 'not eating', 'label': 'SYMPTOM'},
        ],
    },
    {
        'text'     : 'My dog snores loudly every night',
        'translated': '',
        'entities' : [
            {'text': 'dog', 'label': 'ANIMAL'},
            {'text': 'snores', 'label': 'SYMPTOM'},
        ],
    },
]

for t in tests:
    nlp = {
        'original_text' : t['text'],
        'translated_text': t['translated'],
        'entities'      : t['entities'],
    }
    result = rag_agent.get_advice_for_nlp(nlp)
    print('Texte    : ' + t['text'])
    print('Scenario : ' + result.title)
    print('Score    : ' + str(round(result.confidence, 2)))
    print('Qualite  : ' + result.match_quality.upper())
    print('Fallback : ' + str(result.is_fallback))
    print('-'*50)