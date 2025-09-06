# Enhanced Multi-Agent System avec Task Tracking et Persistence

## 🚀 Nouvelles Fonctionnalités Implémentées

Cette itération apporte des améliorations majeures inspirées des meilleures pratiques LangGraph :

### ✨ Task Tracking Automatique
- **Suivi complet** : Chaque interaction d'agent est trackée automatiquement
- **Métriques de performance** : Temps d'exécution, niveau de confiance, outils utilisés  
- **Statuts en temps réel** : PENDING → IN_PROGRESS → COMPLETED/FAILED
- **Contexte préservé** : Lien entre requête utilisateur et résultat agent

### 💾 Persistence et Checkpointing  
- **SQLite intégré** : Base de données locale pour toutes les données
- **Checkpoints LangGraph** : État sauvegardé à chaque étape
- **Récupération d'état** : Reprendre une conversation après redémarrage
- **Historique complet** : Toutes les interactions sont préservées

### 🧠 Système de Mémoire Long-terme
- **Namespaces organisés** : `workflow`, `routing`, `user_preferences`
- **Recherche sémantique** : Retrouver des informations par tags/contenu
- **Accès comptabilisé** : Statistiques d'utilisation de la mémoire
- **Nettoyage automatique** : Gestion intelligente de l'espace

### 📊 Analytics et Monitoring
- **Métriques par agent** : Nombre d'appels, taux de succès, temps d'exécution
- **Résumés de workflow** : Vue d'ensemble de tous les processus
- **Détection d'erreurs** : Tracking et reporting automatique des échecs
- **Tendances historiques** : Évolution des performances dans le temps

## 🏗️ Architecture du Système

```
src/
├── state.py              # États améliorés avec task tracking
├── checkpointer.py       # Persistence SQLite avec LangGraph
├── agent_hooks.py        # Hooks automatiques pour suivi
├── graph.py              # Supervisor amélioré (MODIFIÉ)
├── usage_example.py      # Exemples d'utilisation
└── calendar_agent/       # Agent existant (COMPATIBLE)
    ├── state.py
    ├── calendar_orchestrator.py
    └── booking_node.py
```

## 🔧 Comment Ça Marche

### 1. Task Tracking Automatique

Chaque agent est maintenant instrumenté avec des hooks :

```python
# AVANT (graph.py)
calendar_agent = create_react_agent(model, tools, prompt)

# MAINTENANT (graph.py)  
calendar_agent = create_react_agent(
    model, tools, prompt,
    state_modifier=create_task_tracking_wrapper(AgentType.CALENDAR_AGENT)
)
hook_manager.register_agent_hooks(AgentType.CALENDAR_AGENT)
```

### 2. État Enrichi avec Métriques

```python
# Nouvel état EnhancedWorkflowState
state = EnhancedWorkflowState(
    messages=[...],              # Messages LangGraph standards
    tasks=[...],                 # Tâches avec statut et métriques
    agent_outputs=[...],         # Sorties d'agents enrichies
    memories=[...],              # Mémoire long-terme
    workflow_complete=False,     # État global du workflow
    total_execution_time=15.3    # Métriques de performance
)
```

### 3. Persistence Transparente

```python
# Configuration avec persistence
config = {
    "configurable": {
        "thread_id": "user_session_123",  # Identifiant unique
        "checkpoint_ns": "production"      # Namespace optionnel
    }
}

# Le checkpointer sauvegarde automatiquement
result = await graph.ainvoke({"messages": [...]}, config=config)

# Récupération automatique lors du redémarrage
# L'état est restauré depuis la dernière sauvegarde
```

### 4. Mémoire Long-terme

```python
# Ajout automatique en mémoire via les hooks
state_manager.add_memory(
    thread_id="user_session_123",
    namespace="workflow",
    key="calendar_booking_2025_01_15",
    content={
        "user_request": "Schedule meeting with John",
        "result": "Meeting booked successfully",  
        "confidence": 0.95
    },
    tags=["calendar", "booking", "john"]
)

# Recherche dans la mémoire
memories = state_manager.search_memories(
    thread_id, 
    namespace="workflow", 
    tags=["calendar", "booking"]
)
```

## 🎯 Utilisation Pratique

### Démarrage du Système Amélioré

```python
from src.graph import create_supervisor_graph
from src.state import state_manager

# Créer le supervisor amélioré
graph = await create_supervisor_graph()

# Configuration avec persistence
config = {"configurable": {"thread_id": "user_001"}}

# Utilisation normale - tracking automatique
result = await graph.ainvoke(
    {"messages": [HumanMessage("Schedule a meeting tomorrow")]}, 
    config=config
)

# Voir les métriques
summary = state_manager.get_workflow_summary("user_001")
print(f"Tasks completed: {summary['completed_tasks']}")
print(f"Success rate: {summary['success_rate']:.2%}")
```

### Exemple avec l'Agent Calendrier

Votre agent calendrier existant fonctionne **exactement pareil** mais avec des capacités enrichies :

```python
# Requête utilisateur normale
user_input = "Schedule a meeting with alice@company.com for tomorrow 2 PM"

# Le supervisor route vers calendar_agent (comme avant)
# NOUVEAU : Task tracking automatique
# NOUVEAU : État sauvegardé en SQLite  
# NOUVEAU : Mémoire long-terme mise à jour
# NOUVEAU : Métriques de performance enregistrées

result = await graph.ainvoke({"messages": [HumanMessage(user_input)]}, config)

# Accès aux nouvelles informations
task_info = state_manager.get_state("user_001")
print(f"Calendar tasks: {len(task_info.get_tasks_by_agent(AgentType.CALENDAR_AGENT))}")
```

## 📈 Monitoring et Analytics

### Métriques Disponibles

```python
# Résumé global du workflow
summary = state_manager.get_workflow_summary(thread_id)
# {
#   "total_tasks": 15,
#   "completed_tasks": 13, 
#   "failed_tasks": 2,
#   "success_rate": 0.87,
#   "total_execution_time": 45.2,
#   "agent_call_count": {"calendar_agent": 8, "email_agent": 5, "job_search_agent": 2}
# }

# Historique des checkpoints
history = enhanced_checkpointer.get_enhanced_state_history(thread_id)
for checkpoint in history:
    print(f"Checkpoint {checkpoint['checkpoint_id']}: {checkpoint['task_summary']}")

# Recherche dans la mémoire
recent_bookings = state_manager.search_memories(
    thread_id, 
    namespace="workflow", 
    tags=["calendar", "booking"]
)
```

### Dashboard de Performance

```python  
# Métriques par agent
state = state_manager.get_state(thread_id)

for agent_type in AgentType:
    tasks = state.get_tasks_by_agent(agent_type)
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    
    if tasks:
        avg_confidence = sum(t.confidence for t in completed) / len(completed)
        print(f"{agent_type.value}: {len(completed)}/{len(tasks)} completed (confidence: {avg_confidence:.2f})")
```

## 🔄 Migration depuis l'Ancienne Version

### 1. Code Existant Compatible

Votre code existant fonctionne **sans changement** :

```python
# Ce code fonctionne toujours exactement pareil
from src.graph import create_supervisor_graph

graph = await create_supervisor_graph() 
result = await graph.ainvoke({"messages": [...]})
```

### 2. Nouvelles Fonctionnalités Optionnelles  

Pour utiliser les nouvelles fonctionnalités, ajoutez simplement un `thread_id` :

```python
# Avant : aucune persistence
result = await graph.ainvoke({"messages": [...]})

# Maintenant : avec persistence automatique
config = {"configurable": {"thread_id": "user_001"}}
result = await graph.ainvoke({"messages": [...]}, config=config)
```

### 3. Accès aux Métriques

```python
# Nouveaux : accès aux métriques et état enrichi  
from src.state import state_manager

summary = state_manager.get_workflow_summary(thread_id)
memories = state_manager.search_memories(thread_id, namespace="workflow")
```

## 🎯 Cas d'Usage Concrets

### 1. Suivi de Conversations Multi-Sessions

```python
# Session 1 : Utilisateur demande un rendez-vous
config = {"configurable": {"thread_id": "patient_john_doe"}}
await graph.ainvoke({"messages": [HumanMessage("Need a doctor appointment")]}, config)

# [Application redémarre]

# Session 2 : Même utilisateur revient
# L'état est automatiquement restauré avec :
# - Historique des messages
# - Tâches précédentes  
# - Mémoire des interactions
# - Préférences utilisateur
```

### 2. Analytics de Performance

```python
# Analyser les performances du calendar agent
state = state_manager.get_state(thread_id)
calendar_tasks = state.get_tasks_by_agent(AgentType.CALENDAR_AGENT)

booking_tasks = [t for t in calendar_tasks if "booking" in t.description.lower()]
success_rate = len([t for t in booking_tasks if t.status == TaskStatus.COMPLETED]) / len(booking_tasks)

print(f"Calendar booking success rate: {success_rate:.2%}")

# Temps d'exécution moyen
avg_time = sum(t.duration for t in booking_tasks if t.duration) / len(booking_tasks)
print(f"Average booking time: {avg_time:.1f} seconds")
```

### 3. Mémoire Long-terme Intelligente

```python
# Le système se souvient automatiquement des préférences
state_manager.add_memory(
    thread_id="user_001",
    namespace="user_preferences", 
    key="meeting_defaults",
    content={
        "default_duration": 60,
        "preferred_time": "afternoon",
        "timezone": "America/Toronto"
    },
    tags=["preferences", "calendar"]
)

# Utilisation automatique dans les futures interactions
preferences = state_manager.get_memory(thread_id, "user_preferences", "meeting_defaults")
```

## 🚀 Lancer le Système

### Test Complet

```bash
# Lancer les exemples de démonstration
cd src/
python usage_example.py
```

### Intégration dans Votre App

```python
from src.graph import create_supervisor_graph
from src.state import state_manager

# Initialisation (une seule fois)
graph = await create_supervisor_graph()

# Utilisation avec persistence
async def handle_user_request(user_id: str, message: str):
    config = {"configurable": {"thread_id": user_id}}
    
    result = await graph.ainvoke(
        {"messages": [HumanMessage(message)]}, 
        config=config
    )
    
    # Métriques automatiquement disponibles
    summary = state_manager.get_workflow_summary(user_id)
    
    return {
        "response": result["messages"][-1].content,
        "metrics": summary
    }
```

## 📊 Bases de Données Créées

Le système créé automatiquement plusieurs bases SQLite :

- `checkpoints.db` : Checkpoints LangGraph et snapshots d'état
- `memory_store.db` : Mémoire long-terme avec recherche
- `agent_data.db` : Tasks, outputs d'agents, et analytics

Ces fichiers sont créés automatiquement dans le répertoire de travail.

## 🔧 Configuration

### Variables d'Environnement

```bash
# Existing (unchanged)
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
USER_TIMEZONE=America/Toronto
PIPEDREAM_MCP_SERVER=your_server_url

# Nouvelles (optionnelles)
DATABASE_PATH=./agent_databases/     # Chemin des bases de données
CHECKPOINT_RETENTION_DAYS=30         # Rétention des checkpoints
MEMORY_CLEANUP_INTERVAL=7            # Nettoyage automatique
```

### Personnalisation

```python
# Personnaliser le système de persistence
from src.checkpointer import EnhancedSQLiteCheckpointer
from src.state import StateManager, PersistenceManager

# Checkpointer personnalisé
custom_checkpointer = EnhancedSQLiteCheckpointer(db_path="custom_checkpoints.db")

# Manager de state personnalisé  
custom_persistence = PersistenceManager(db_path="custom_agent_data.db")
custom_state_manager = StateManager(persistence=custom_persistence)
```

## 🎉 Résumé des Améliorations

| Fonctionnalité | Avant | Maintenant |
|---------------|-------|------------|
| **Task Tracking** | ❌ Aucun | ✅ Automatique avec métriques |
| **Persistence** | ❌ État perdu au redémarrage | ✅ SQLite avec récupération |
| **Mémoire Long-terme** | ❌ Aucune | ✅ Système complet avec recherche |
| **Analytics** | ❌ Aucune métrique | ✅ Métriques détaillées par agent |
| **Error Tracking** | ❌ Basique | ✅ Tracking complet avec contexte |
| **Multi-session** | ❌ Sessions isolées | ✅ Continuité entre sessions |
| **Performance** | ❌ Aucune mesure | ✅ Temps d'exécution et confiance |
| **Supervisor Intelligence** | ✅ Routing basique | ✅ Oversight avec historique |

Le système reste **100% compatible** avec votre code existant tout en ajoutant ces capacités avancées. Votre agent calendrier continue de fonctionner exactement pareil, mais avec des superpowers de tracking et persistence ! 🚀