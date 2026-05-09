from transformers import pipeline

print('Chargement XLM-RoBERTa Sentiment (premiere fois ~470MB)...')

sentiment = pipeline(
    'sentiment-analysis',
    model='cardiffnlp/twitter-xlm-roberta-base-sentiment'
)

print('Modele charge !\n')

tests = [
    # Cas vétérinaires positifs
    'My dog is so happy and playing all day',
    'My cat is feeling much better after the medication',
    'Update : my puppy is recovering well',
    'Mon chat est tres heureux et joue beaucoup',

    # Cas vétérinaires négatifs
    'My dog is suffering and crying in pain',
    'I am worried my cat might die',
    'My rabbit collapsed and I am devastated',
    'Mon chien souffre beaucoup et ne mange plus',

    # Cas neutres / questions
    'Should I take my dog to the vet?',
    'Just a normal day with my pet',
    'My cat has been vomiting since yesterday',

    # Cas critiques
    'URGENT my dog ate poison please help',
    'My cat is having a seizure right now',
]

print('=' * 60)
print('TEST SENTIMENT XLM-ROBERTA')
print('=' * 60)

for text in tests:
    result = sentiment(text)[0]
    label  = result['label']
    score  = round(result['score'], 2)

    # Mapper label au format DoctoAgent (0-100)
    if label.lower() == 'positive':
        sentiment_score = 70 + int(score * 30)
    elif label.lower() == 'negative':
        sentiment_score = 30 - int(score * 30)
    else:
        sentiment_score = 50

    print(f'\n[{label.upper()}] (conf: {score})')
    print(f'  Text   : {text[:65]}')
    print(f'  Score  : {sentiment_score}/100')