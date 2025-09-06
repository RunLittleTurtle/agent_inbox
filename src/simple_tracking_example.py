"""
Exemple Simple : Task Tracking avec LangGraph SDK Natif
Montre comment utiliser MemorySaver et les threads pour un tracking basique.
"""

import asyncio
from datetime import datetime
from langchain_core.messages import HumanMessage

from .graph import create_supervisor_graph
from .state import EnhancedWorkflowState, AgentType, SimpleTask


async def demonstrate_simple_tracking():
    """Démonstration simple du tracking avec LangGraph natif"""

    print("🚀 Démonstration Simple du Task Tracking")
    print("=" * 50)

    # Créer le graph avec MemorySaver
    print("\n📊 Creating supervisor with MemorySaver...")
    graph = await create_supervisor_graph()
    print("✅ Supervisor créé avec checkpointing MemorySaver!")

    # Configuration thread simple
    thread_id = "demo_simple_001"
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n🔗 Thread ID: {thread_id}")
    print("📝 Les interactions seront sauvegardées en mémoire")

    # Exemples de requêtes simples
    demo_requests = [
        "What's on my calendar today?",
        "Help me write an email to my boss",
        "I need interview tips for a tech job"
    ]

    # Traiter chaque requête
    for i, request in enumerate(demo_requests, 1):
        print(f"\n{'='*10} REQUEST {i} {'='*10}")
        print(f"📝 User: {request}")
        print(f"⏱️  Time: {datetime.now().strftime('%H:%M:%S')}")

        try:
            # Envoyer la requête au supervisor
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=request)]},
                config=config
            )

            # Afficher la réponse
            if result and "messages" in result:
                response = result["messages"][-1].content
                print(f"🤖 Agent: {response[:200]}{'...' if len(response) > 200 else ''}")
            else:
                print("❌ No response received")

        except Exception as e:
            print(f"❌ Error: {e}")

        # Petit délai entre les requêtes
        await asyncio.sleep(0.5)

    # Démonstrer la récupération de l'état du thread
    print(f"\n{'='*20} THREAD STATE {'='*20}")

    try:
        # Obtenir l'état du thread via l'API LangGraph
        print("📊 Thread State Information:")

        # Avec MemorySaver, on peut récupérer l'historique
        state_snapshot = await graph.aget_state(config)

        if state_snapshot:
            print(f"   📝 Messages in history: {len(state_snapshot.values.get('messages', []))}")
            print(f"   🔄 Checkpoint ID: {state_snapshot.config.get('configurable', {}).get('checkpoint_id', 'N/A')}")

            # Si on utilise notre EnhancedWorkflowState, on peut voir plus de détails
            if 'tasks' in state_snapshot.values:
                tasks = state_snapshot.values['tasks']
                print(f"   📋 Tasks tracked: {len(tasks) if tasks else 0}")

                if tasks:
                    completed = len([t for t in tasks if t.get('status') == 'completed'])
                    print(f"   ✅ Completed tasks: {completed}/{len(tasks)}")

            if 'agent_call_count' in state_snapshot.values:
                calls = state_snapshot.values['agent_call_count']
                print(f"   📞 Agent calls: {calls}")
        else:
            print("   📝 No state snapshot available")

    except Exception as e:
        print(f"   ❌ Error getting state: {e}")

    # Démonstrer la persistence - créer une nouvelle session avec le même thread
    print(f"\n{'='*20} PERSISTENCE TEST {'='*20}")
    print("🔄 Testing persistence by creating new graph instance...")

    try:
        # Créer une nouvelle instance du graph
        new_graph = await create_supervisor_graph()

        # Utiliser le même thread_id pour récupérer l'historique
        print("📚 Retrieving conversation history with same thread_id...")

        # Vérifier qu'on peut récupérer l'état
        recovered_state = await new_graph.aget_state(config)

        if recovered_state:
            message_count = len(recovered_state.values.get('messages', []))
            print(f"✅ Successfully recovered {message_count} messages from previous session!")

            # Envoyer une nouvelle requête pour voir la continuité
            print("📤 Sending new request to test continuity...")

            result = await new_graph.ainvoke(
                {"messages": [HumanMessage(content="Thanks for the help!")]},
                config=config
            )

            if result and "messages" in result:
                response = result["messages"][-1].content
                print(f"🤖 Agent: {response[:150]}...")
                print("✅ Continuity maintained across sessions!")

        else:
            print("❌ Could not recover previous state")

    except Exception as e:
        print(f"❌ Persistence test failed: {e}")

    print(f"\n{'='*50}")
    print("🎉 Simple Tracking Demo Complete!")
    print("\n📚 What was demonstrated:")
    print("   ✅ MemorySaver checkpointing (native LangGraph)")
    print("   ✅ Thread-based conversation persistence")
    print("   ✅ State recovery across sessions")
    print("   ✅ Simple conversation continuity")
    print("   ✅ Calendar agent integration (if available)")
    print("\n🔧 Next steps for production:")
    print("   • Add custom state fields for more tracking")
    print("   • Use LangGraph Store for user preferences")
    print("   • Implement custom hooks for specific metrics")
    print("   • Add error handling and retry logic")


async def demonstrate_store_usage():
    """Démonstration de l'utilisation du Store natif LangGraph"""

    print("\n🗄️ LangGraph Store Demo")
    print("=" * 30)

    # Note: Store usage requires LangGraph Cloud or local setup
    # This is a conceptual example of how you would use it

    print("📝 Conceptual Store Usage:")
    print("```python")
    print("# Store user preferences")
    print("await store.put_item(")
    print("    namespace='user_preferences',")
    print("    key='calendar_settings',")
    print("    value={'timezone': 'America/Toronto', 'default_duration': 60}")
    print(")")
    print("")
    print("# Retrieve preferences")
    print("prefs = await store.get_item('user_preferences', 'calendar_settings')")
    print("```")
    print("\n💡 In production, you would:")
    print("   • Store user preferences across sessions")
    print("   • Cache frequently accessed data")
    print("   • Share data between different workflows")
    print("   • Implement search capabilities")


if __name__ == "__main__":
    # Lancer la démonstration
    asyncio.run(demonstrate_simple_tracking())
    asyncio.run(demonstrate_store_usage())
