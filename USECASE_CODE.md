# 📊 Code PlantUML - Diagramme des Cas d'Usage

## 🎯 Diagramme UML des Cas d'Usage - Cheebo Healthcare

```plantuml
@startuml Cheebo_Healthcare_UseCases
!theme plain
skinparam backgroundColor #0D0820
skinparam actorBackgroundColor #7B56E2
skinparam usecaseBackgroundColor #1A1232
skinparam arrowColor #9A7BF2
skinparam fontColor #F0EEF8

' ========== ACTEURS ==========
actor "👤 Propriétaire d'Animal" as USER
actor "🤖 Assistant IA Cheebo" as AI
actor "🏥 Vétérinaire Partenaire" as VET
actor "📱 Système Mobile" as SYSTEM
participant "🗄️ MongoDB" as DB
participant "⚙️ FastAPI Backend" as BACKEND

' ========== RECTANGLE DE L'APPLICATION ==========
rectangle "Cheebo Healthcare Application" {

  ' ========== USECASE DASHBOARD ==========
  usecase "Consulter Dashboard" as UC_DASHBOARD
  usecase "Afficher Statistiques" as UC_STATS
  usecase "Lancer Consultation" as UC_LAUNCH_CHAT
  usecase "Voir Vétérinaires Urgence" as UC_EMERGENCY_VETS
  usecase "Appeler Vétérinaire" as UC_CALL_VET

  ' ========== USECASE CHAT ==========
  usecase "Démarrer Chat" as UC_START_CHAT
  usecase "Envoyer Message" as UC_SEND_MSG
  usecase "Utiliser Reconnaissance Vocale" as UC_STT
  usecase "Recevoir Réponse IA" as UC_RECEIVE_AI
  usecase "Voir Vétérinaires Recommandés" as UC_SHOW_VETS
  usecase "Charger Session Antérieure" as UC_LOAD_SESSION
  usecase "Sauvegarder Conversation" as UC_SAVE_CHAT

  ' ========== USECASE HISTORIQUE ==========
  usecase "Consulter Historique" as UC_HISTORY
  usecase "Filtrer Consultations" as UC_FILTER
  usecase "Charger Détails Consultation" as UC_DETAIL_CHAT
  usecase "Synchroniser avec MongoDB" as UC_SYNC_HISTORY

  ' ========== USECASE MEDICAMENTS ==========
  usecase "Ouvrir Pilulier" as UC_MEDICATIONS
  usecase "Ajouter Médicament Manuel" as UC_ADD_MED_MANUAL
  usecase "Scanner Boîte (OCR)" as UC_SCAN_OCR
  usecase "Programmer Rappel" as UC_SCHEDULE_REMINDER
  usecase "Activer/Désactiver Médicament" as UC_TOGGLE_MED
  usecase "Supprimer Médicament" as UC_DELETE_MED
  usecase "Recevoir Rappel" as UC_RECEIVE_REMINDER
  usecase "Déterminer Danger Médicament" as UC_DANGER_CHECK
  usecase "Suggérer Complétion Formulaire" as UC_SUGGEST_MED

  ' ========== USECASE ARTICLES ==========
  usecase "Consulter Articles" as UC_ARTICLES
  usecase "Filtrer par Catégorie" as UC_FILTER_ARTICLES
  usecase "Lire Article Détaillé" as UC_READ_ARTICLE

  ' ========== USECASE PROFIL & PARAMETRES ==========
  usecase "Gérer Profil" as UC_PROFILE
  usecase "Configurer Paramètres" as UC_SETTINGS
  usecase "Gérer Notifications" as UC_NOTIFICATIONS

  ' ========== USECASE SYSTEME ==========
  usecase "Synchroniser Données" as UC_SYNC_DATA
  usecase "Utiliser Cache Local" as UC_CACHE
  usecase "Afficher Erreur Connexion" as UC_OFFLINE
}

' ========== RELATIONS UTILISATEUR ==========
USER --> UC_DASHBOARD : utilise
USER --> UC_START_CHAT : utilise
USER --> UC_HISTORY : utilise
USER --> UC_MEDICATIONS : utilise
USER --> UC_ARTICLES : utilise
USER --> UC_PROFILE : utilise
USER --> UC_SETTINGS : utilise

' ========== RELATIONS DASHBOARD ==========
UC_DASHBOARD --> UC_STATS : inclut
UC_DASHBOARD --> UC_LAUNCH_CHAT : inclut
UC_DASHBOARD --> UC_EMERGENCY_VETS : inclut
UC_EMERGENCY_VETS --> UC_CALL_VET : inclut

' ========== RELATIONS CHAT ==========
UC_START_CHAT --> UC_SEND_MSG : inclut
UC_START_CHAT --> UC_STT : inclut
UC_SEND_MSG --> UC_RECEIVE_AI : suit
UC_START_CHAT --> UC_SHOW_VETS : inclut
UC_SHOW_VETS --> UC_CALL_VET : inclut
UC_START_CHAT --> UC_LOAD_SESSION : inclut
UC_SEND_MSG --> UC_SAVE_CHAT : déclenche

' ========== RELATIONS HISTORIQUE ==========
UC_HISTORY --> UC_FILTER : inclut
UC_HISTORY --> UC_DETAIL_CHAT : inclut
UC_HISTORY --> UC_SYNC_HISTORY : inclut

' ========== RELATIONS MEDICAMENTS ==========
UC_MEDICATIONS --> UC_ADD_MED_MANUAL : inclut
UC_MEDICATIONS --> UC_SCAN_OCR : inclut
UC_SCAN_OCR --> UC_DANGER_CHECK : déclenche
UC_SCAN_OCR --> UC_SUGGEST_MED : déclenche
UC_ADD_MED_MANUAL --> UC_SCHEDULE_REMINDER : suit
UC_MEDICATIONS --> UC_TOGGLE_MED : inclut
UC_MEDICATIONS --> UC_DELETE_MED : inclut
UC_SCHEDULE_REMINDER --> UC_RECEIVE_REMINDER : suit

' ========== RELATIONS ARTICLES ==========
UC_ARTICLES --> UC_FILTER_ARTICLES : inclut
UC_ARTICLES --> UC_READ_ARTICLE : inclut

' ========== RELATIONS BACKEND ==========
UC_RECEIVE_AI --> AI : demande
AI --> BACKEND : traite
UC_SAVE_CHAT --> DB : stocke
UC_LOAD_SESSION --> DB : récupère
UC_SYNC_HISTORY --> DB : récupère
UC_SYNC_DATA --> BACKEND : synchronise
UC_SYNC_DATA --> DB : synchronise

' ========== RELATIONS OFFLINE ==========
UC_SYNC_DATA --> UC_CACHE : utilise si déconnecté
UC_SYNC_DATA --> UC_OFFLINE : déclenche alerte

' ========== RELATIONS NOTIFICATIONS ==========
UC_RECEIVE_REMINDER --> SYSTEM : utilise
SYSTEM --> USER : notifie

' ========== RELATIONS APPELS ==========
UC_CALL_VET --> VET : appelle
UC_CALL_VET --> SYSTEM : utilise service téléphone

@enduml
```

---

## 📝 Comment utiliser ce code

### Option 1: PlantUML en ligne
1. Allez sur [plantuml.com/plantuml](https://www.plantuml.com/plantuml/uml/)
2. Collez le code ci-dessus
3. Générez le diagramme

### Option 2: VS Code avec extension PlantUML
1. Installez l'extension "PlantUML" par jgraph
2. Créez un fichier `.puml`
3. Collez le code
4. Appuyez sur `Alt+D` pour prévisualiser

### Option 3: Ligne de commande
```bash
java -jar plantuml.jar USECASE_DIAGRAM.puml
```

---

## 🎨 Légende des Couleurs

- **Acteurs (rose violet)** - Entités externes ou utilisateurs
- **Cas d'usage (bleu fonc)** - Fonctionnalités du système
- **Inclut →** - Le cas d'usage comprend ce sous-cas
- **Suit →** - Dépendance séquentielle

---

## 📊 Résumé des Cas d'Usage

### Par Module:

| Module | Nombre de Cas | Exemples |
|--------|---------------|----------|
| Dashboard | 5 | Stats, Urgences, Appels |
| Chat | 7 | Messages, IA, Sessions |
| Historique | 4 | Filtrage, Détails, Sync |
| Médicaments | 9 | Ajout, OCR, Rappels |
| Articles | 3 | Lecture, Filtrage |
| Profil/Paramètres | 3 | Configuration |
| Système | 3 | Sync, Cache, Offline |
| **TOTAL** | **34** | |

