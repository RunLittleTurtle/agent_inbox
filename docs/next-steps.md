# 🚀 NEXT STEPS - DÉPLOIEMENT LANGGRAPH PLATFORM

**Status:** ✅ Code prêt - En attente de déploiement
**Durée estimée:** 20-30 minutes

---

## ✅ CE QUI A ÉTÉ FAIT

### Code Modifications - **COMPLÉTÉ**
- ✅ `langgraph.json` configuré avec semantic search
- ✅ `requirements.txt` mis à jour avec `langgraph-checkpoint-postgres`
- ✅ `src/graph.py` modifié pour multi-tenant (`config.configurable`)
- ✅ Code testé et compile sans erreur
- ✅ PostgreSQL checkpointer installé localement

### Documentation Créée - **COMPLÉTÉ**
- ✅ `LANGGRAPH_DEPLOYMENT_2025.md` - Guide technique complet
- ✅ `DEPLOYMENT_READY_SUMMARY.md` - Résumé des changements
- ✅ `NEXT_STEPS.md` - Ce fichier (instructions étape par étape)

---

## 📋 CE QU'IL RESTE À FAIRE

### ÉTAPE 1: Test Local (5 min)

**Objectif:** Vérifier que le code fonctionne avant de déployer

```bash
# 1. Activer l'environnement virtuel
source .venv/bin/activate

# 2. Installer les dépendances (déjà fait, mais au cas où)
pip install -r requirements.txt

# 3. Démarrer le serveur local
langgraph dev
```

**Expected Output:**
```
Ready!
- API: http://localhost:2024
```

**Test le serveur:**
```bash
# Dans un nouveau terminal
curl http://localhost:2024/health

# Devrait retourner: {"status":"ok"}
```

**Si ça fonctionne:** ✅ Passer à l'étape 2
**Si erreur:** Voir section "Troubleshooting" en bas

---

### ÉTAPE 2: Commit & Push (2 min)

```bash
# 1. Vérifier les changements
git status

# Devrait montrer:
# modified: langgraph.json
# modified: requirements.txt
# modified: src/graph.py
# new file: LANGGRAPH_DEPLOYMENT_2025.md
# new file: DEPLOYMENT_READY_SUMMARY.md
# new file: NEXT_STEPS.md

# 2. Commit
git add langgraph.json requirements.txt src/graph.py
git add LANGGRAPH_DEPLOYMENT_2025.md DEPLOYMENT_READY_SUMMARY.md NEXT_STEPS.md

git commit -m "feat: multi-tenant LangGraph Platform deployment ready

- Add config.configurable support in all agents
- Add langgraph-checkpoint-postgres dependency
- Configure semantic search in langgraph.json
- Add comprehensive deployment documentation

Ready for production deployment on LangGraph Platform."

# 3. Push
git push origin main
```

**Vérification:**
```bash
git log -1  # Voir le dernier commit
```

---

### ÉTAPE 3: Déployer sur LangGraph Platform (10-15 min)

#### 3.1 - Accéder au Dashboard

1. Aller sur: **https://smith.langchain.com**
2. Login avec votre compte LangChain
3. Navigation: **LangGraph Platform** (menu de gauche)
4. Click: **Deployments**
5. Click: **+ New Deployment**

---

#### 3.2 - Configuration du Deployment

**Onglet: Git Repository**

| Field | Value |
|-------|-------|
| **Deployment Name** | `agent-inbox-production` |
| **Git Provider** | GitHub |
| **Repository** | Sélectionner votre repo |
| **Branch** | `main` |
| **Config File Path** | `langgraph.json` |

**Click: Next**

---

**Onglet: Deployment Settings**

| Field | Value | Notes |
|-------|-------|-------|
| **Deployment Type** | `Production` | Pour production stable 24/7 |
| | OU `Development` | Pour tests (moins cher) |
| **Automatic Updates** | ✅ Enabled | Re-deploy sur git push |
| **LangGraph Studio Access** | ✅ Enabled | Pour debugging |
| **LangSmith Tracing** | ✅ Enabled | Pour monitoring |

**Click: Next**

---

**Onglet: Environment Variables**

Ajouter les variables suivantes (click **Add Environment Variable** pour chaque):

#### Variables Requises:

| Key | Value | Type |
|-----|-------|------|
| `OPENAI_API_KEY` | `sk-proj-...` | Secret |
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | Secret |
| `LANGSMITH_API_KEY` | `lsv2_pt_...` | Secret |
| `LANGCHAIN_TRACING_V2` | `true` | Plain |
| `LANGCHAIN_PROJECT` | `agent-inbox` | Plain |

#### Variables Optionnelles (MCP Servers):

| Key | Value | Type |
|-----|-------|------|
| `RUBE_MCP_SERVER` | `https://rube.app/mcp` | Plain |
| `RUBE_AUTH_TOKEN` | `eyJ...` | Secret |
| `PIPEDREAM_MCP_SERVER` | Votre URL Pipedream | Plain |

#### Variables System:

| Key | Value | Type |
|-----|-------|------|
| `ENVIRONMENT` | `production` | Plain |
| `LOG_LEVEL` | `INFO` | Plain |
| `USER_TIMEZONE` | `America/Toronto` | Plain |

**Click: Next**

---

**Onglet: Review & Deploy**

- Vérifier tous les paramètres
- Click: **Create Deployment**

---

#### 3.3 - Attendre le Build

**Dashboard → Deployments → agent-inbox-production**

**Build Stages:**
1. 🟡 **Building** - Installation des dépendances (~2-3 min)
2. 🟡 **Starting** - Démarrage du serveur (~30 sec)
3. 🟢 **Running** - Déployé avec succès!

**Surveiller les logs:**
- Click sur votre deployment
- Onglet **Build Logs**
- Vérifier qu'il n'y a pas d'erreur

**Temps total:** ~3-5 minutes

---

### ÉTAPE 4: Vérification Post-Deployment (5 min)

#### 4.1 - Obtenir l'URL de Deployment

**Dashboard → Your Deployment → Overview**

**Copier:**
- **Deployment URL** (exemple: `https://agent-inbox-prod-abc123.langchain.app`)

**Sauvegarder cette URL** - vous en aurez besoin pour les API routes frontend!

---

#### 4.2 - Test 1: Health Check

```bash
curl https://YOUR-DEPLOYMENT-URL/health
```

**Expected:**
```json
{"status":"ok"}
```

✅ **Success:** Le serveur répond!

---

#### 4.3 - Test 2: Message de Test

**Remplacer:**
- `YOUR-DEPLOYMENT-URL` avec votre URL
- `YOUR_LANGSMITH_API_KEY` avec votre clé
- `YOUR_OPENAI_KEY` avec une clé de test
- `YOUR_ANTHROPIC_KEY` avec une clé de test

```bash
curl -X POST https://YOUR-DEPLOYMENT-URL/runs/stream \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_LANGSMITH_API_KEY" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [
        {"role": "user", "content": "Hello, what is 2+2?"}
      ]
    },
    "config": {
      "configurable": {
        "openai_api_key": "YOUR_OPENAI_KEY",
        "anthropic_api_key": "YOUR_ANTHROPIC_KEY",
        "user_id": "test_user_123"
      }
    }
  }'
```

**Expected:**
- Stream of Server-Sent Events (SSE)
- Final message avec la réponse de l'agent: "4"

✅ **Success:** L'agent répond correctement!

---

#### 4.4 - Test 3: LangSmith Traces

1. Aller sur: **https://smith.langchain.com**
2. Click: **Projects** (menu de gauche)
3. Sélectionner: `agent-inbox`
4. Vérifier: Le test apparaît dans les traces

**Ce que vous devriez voir:**
- Trace avec `user_id: test_user_123`
- Nodes exécutés (supervisor, agents)
- Temps d'exécution
- Token usage

✅ **Success:** Monitoring fonctionne!

---

### ÉTAPE 5: Configurer dans Vercel (5 min)

**Pour chaque UI (agent-chat-ui-2, agent-inbox, config-app):**

1. Dashboard Vercel → Sélectionner le projet
2. Settings → Environment Variables
3. Add Variable:

```bash
LANGGRAPH_API_URL=https://YOUR-DEPLOYMENT-URL
```

4. Select Environments:
   - ✅ Production
   - ✅ Preview
   - ✅ Development

5. Click: **Save**

**Répéter pour les 3 UIs.**

---

## 🎉 SUCCÈS!

### ✅ Ce qui est maintenant déployé:

- ✅ Backend LangGraph Platform actif 24/7
- ✅ PostgreSQL persistence (automatic)
- ✅ Thread management (automatic)
- ✅ Semantic search enabled
- ✅ LangSmith tracing enabled
- ✅ Multi-tenant ready (config.configurable)
- ✅ Auto-scaling enabled

### 📊 Capacités:

| Feature | Status |
|---------|--------|
| **Users simultanés** | Illimité (auto-scaling) |
| **Threads par user** | Illimité |
| **Persistence** | PostgreSQL managed |
| **Monitoring** | LangSmith traces |
| **Coût** | $39/mo (100K nodes inclus) |

---

## 🔗 PROCHAINE ÉTAPE: Intégration Frontend

Maintenant que le backend est déployé, vous pouvez:

1. **Créer les API routes** dans vos UIs Next.js (voir PRODUCTION_DEPLOYMENT_PLAN.md Epic 3)
2. **Implémenter le flow:** Clerk → Supabase → LangGraph
3. **Tester multi-tenant:** User 1 vs User 2 isolation
4. **Déployer sur Vercel**

**Documentation:**
- Voir: `PRODUCTION_DEPLOYMENT_PLAN.md` - Epics 2-6
- Pattern: `DEPLOYMENT_READY_SUMMARY.md` - Section "Intégration Frontend"

---

## 🆘 TROUBLESHOOTING

### Problème: `langgraph dev` ne démarre pas

**Symptômes:** Erreur au démarrage du serveur local

**Solutions:**
```bash
# 1. Vérifier la version Python
python --version  # Doit être 3.11+

# 2. Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall

# 3. Vérifier langgraph.json
cat langgraph.json  # Doit être valid JSON

# 4. Tester compilation Python
python -m py_compile src/graph.py
```

---

### Problème: Build échoue sur LangGraph Platform

**Symptômes:** Status "Failed" dans dashboard

**Debug:**
1. Click sur le deployment
2. Onglet **Build Logs**
3. Scroll en bas pour voir l'erreur

**Erreurs communes:**

**"Graph export 'graph' not found"**
```bash
# Vérifier dans src/graph.py:
# Doit avoir à la fin:
graph = create_graph()  # Ligne ~504
```

**"Invalid API key"**
```bash
# Vérifier dans Environment Variables:
# ANTHROPIC_API_KEY est bien configurée
# Tester la clé localement d'abord
```

**"Module not found"**
```bash
# Vérifier requirements.txt contient:
langgraph-checkpoint-postgres>=2.0.0
```

---

### Problème: Health check échoue (404 ou 500)

**Solutions:**

**404 Not Found:**
- Vérifier l'URL (copier depuis dashboard)
- Essayer: `https://YOUR-URL/health` (pas `/api/health`)

**500 Internal Server Error:**
- Check Build Logs pour erreurs
- Vérifier Environment Variables (surtout API keys)
- Essayer de re-deploy

---

### Problème: Agent ne répond pas (timeout)

**Symptômes:** Test curl timeout ou erreur

**Debug:**
```bash
# 1. Vérifier les clés API dans config.configurable
# 2. Tester les clés localement d'abord
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_OPENAI_KEY"

# 3. Check LangSmith traces pour voir où ça bloque
```

---

### Problème: Multi-tenant ne fonctionne pas

**Symptômes:** User 1 voit les données de User 2

**Causes:**
- `config.configurable` pas passé correctement
- Frontend API route ne passe pas les bonnes clés

**Vérification:**
```python
# Dans src/graph.py, vérifier les logs:
logger.info(f"Creating agents for user: {api_keys['user_id']}...")

# Les logs doivent montrer des user_id différents
```

---

## 📞 SUPPORT

### Documentation Interne
- 📖 `LANGGRAPH_DEPLOYMENT_2025.md` - Guide technique détaillé
- 📋 `PRODUCTION_DEPLOYMENT_PLAN.md` - Plan projet complet
- ✅ `DEPLOYMENT_READY_SUMMARY.md` - Résumé des changements

### Ressources Externes
- [LangGraph Platform Docs](https://langchain-ai.github.io/langgraph/cloud/)
- [LangGraph Discord](https://discord.gg/langchain)
- [LangSmith Support](https://smith.langchain.com)

### Contact
- Email: support@langchain.com
- Discord: https://discord.gg/langchain

---

## 📝 CHECKLIST FINALE

### Avant de commencer:
- [ ] Lire ce document en entier
- [ ] Avoir accès à LangSmith dashboard
- [ ] Avoir accès à GitHub
- [ ] Avoir toutes les API keys prêtes

### Déploiement:
- [ ] Test local réussi (`langgraph dev`)
- [ ] Code poussé sur GitHub
- [ ] Deployment créé sur LangGraph Platform
- [ ] Build status: "Running"
- [ ] Health check: `200 OK`
- [ ] Test message: Agent répond
- [ ] LangSmith traces: Visibles

### Post-deployment:
- [ ] Deployment URL sauvegardée
- [ ] URL configurée dans Vercel (3 UIs)
- [ ] Documentation lue

---

**🚀 Bon déploiement!**

Si vous avez des questions ou problèmes:
1. Vérifier section "Troubleshooting" ci-dessus
2. Consulter `LANGGRAPH_DEPLOYMENT_2025.md`
3. Poster sur Discord LangChain
