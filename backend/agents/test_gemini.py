
import google.generativeai as genai

# Remplace par TA cle ici
API_KEY = 'AIzaSyDsXZxDOJyj8d3DQJ_C0PU9htRnIQ6NDM0'

genai.configure(api_key=API_KEY)

# Lister les modeles disponibles
print('Modeles disponibles :')
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print('  - ' + model.name)

# Test simple
print('\nTest de generation...')
model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content('Dis bonjour en francais et en arabe en 2 phrases courtes.')
print('\nReponse Gemini :')
print(response.text)
