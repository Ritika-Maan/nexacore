# Hindsight Setup Guide

## What is Hindsight?

Hindsight is a **self-hosted** memory/knowledge service from Vectorize.io. It's NOT a hosted SaaS — you run it yourself via Docker.

## Understanding the Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Application                     │
│                  (nexacore-backend)                     │
│                                                         │
│    Uses HindsightClient to store/retrieve memories     │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP API calls
                   ↓
┌─────────────────────────────────────────────────────────┐
│              Hindsight Service (Self-Hosted)            │
│          ghcr.io/vectorize-io/hindsight:latest          │
│                                                         │
│  API: /v1/default/banks/{bank_id}/memories/...         │
│  - /recall  (search/query)                             │
│  - /retain  (create/write)                             │
│  - /list    (list/count)                               │
│                                                         │
│  Embedded PostgreSQL (/home/hindsight/.pg0)            │
└─────────────────────────────────────────────────────────┘
```

## Option 1: Local Development (Docker)

### Quick Start

1. **Set environment variables:**
   ```bash
   export GROQ_API_KEY=your-groq-key
   # OR export OPENAI_API_KEY=sk-xxx
   ```

2. **Run Hindsight:**
   ```bash
   docker run -it --pull always \
     --name hindsight \
     --restart unless-stopped \
     -p 8888:8888 \
     -p 9999:9999 \
     -e HINDSIGHT_API_LLM_PROVIDER=groq \
     -e HINDSIGHT_API_LLM_API_KEY=$GROQ_API_KEY \
     -v hindsight-data:/home/hindsight/.pg0 \
     ghcr.io/vectorize-io/hindsight:latest
   ```

3. **Access:**
   - API: `http://localhost:8888`
   - UI: `http://localhost:9999`

4. **Configure your app:**
   
   In `.env`:
   ```env
   HINDSIGHT_BACKEND=http
   HINDSIGHT_BASE_URL=http://localhost:8888
   HINDSIGHT_PROJECT=ramp-onboarding-demo
   # API key optional for local
   HINDSIGHT_API_KEY=
   ```

### Volume Mounting (CRITICAL!)

The `-v hindsight-data:/home/hindsight/.pg0` is **essential**. Without it:
- ❌ All memories are lost when container restarts
- ❌ Data resets on every redeploy

With it:
- ✅ Memories persist across restarts
- ✅ Data survives container updates

## Option 2: Production on Render

### Step 1: Create Hindsight Service

1. **Create new Web Service** on Render
2. **Configure:**
   - **Name:** `nexacore-hindsight`
   - **Runtime:** Docker
   - **Image URL:** `ghcr.io/vectorize-io/hindsight:latest`
   - **Region:** Same as your backend
   - **Instance Type:** 512MB minimum

3. **Environment Variables:**
   ```env
   HINDSIGHT_API_LLM_PROVIDER=groq
   HINDSIGHT_API_LLM_API_KEY=<your-groq-api-key>
   PORT=8888
   ```

4. **Add Persistent Disk (CRITICAL!):**
   - Name: `hindsight-data`
   - Mount Path: `/home/hindsight/.pg0`
   - Size: 1GB minimum
   
   **Without this disk, all memories are lost on every deploy!**

5. **Health Check:**
   - Path: `/health`
   - Port: 8888

6. **Deploy** and note the URL (e.g., `https://nexacore-hindsight.onrender.com`)

### Step 2: Configure Your Backend

Update your backend service environment variables:

```env
HINDSIGHT_BACKEND=http
HINDSIGHT_BASE_URL=https://nexacore-hindsight.onrender.com
HINDSIGHT_PROJECT=ramp-onboarding-demo
# API key optional for self-hosted
HINDSIGHT_API_KEY=
```

The paths are automatically set to:
- Search: `/v1/default/banks/ramp-onboarding-demo/memories/recall`
- Write: `/v1/default/banks/ramp-onboarding-demo/memories/retain`
- List: `/v1/default/banks/ramp-onboarding-demo/memories/list`

### Step 3: Redeploy Backend

After setting environment variables, trigger a redeploy. Your backend will now use the self-hosted Hindsight service!

## API Endpoints Reference

Hindsight uses `/v1/default/banks/{bank_id}/memories/` structure:

### Search/Recall Memories
```bash
POST /v1/default/banks/{bank_id}/memories/recall
Content-Type: application/json

{
  "query": "how do I get AWS access?",
  "top_k": 10,
  "filters": {
    "tags": ["team:platform", "type:access"],
    "namespace": "team/platform"
  }
}
```

### Write/Retain Memory
```bash
POST /v1/default/banks/{bank_id}/memories/retain
Content-Type: application/json

{
  "content": "AWS access requires approval from security team",
  "tags": ["team:platform", "type:access", "source:manual"],
  "metadata": {
    "namespace": "team/platform",
    "level": "team",
    "source": "onboarding-doc"
  }
}
```

### List Memories
```bash
GET /v1/default/banks/{bank_id}/memories/list
```

### Health Check
```bash
GET /health
```

## Common Issues & Solutions

### Issue 1: Memories Lost on Restart

**Symptom:** All data disappears when container restarts

**Cause:** No persistent volume mounted

**Fix:**
- **Docker:** Use `-v hindsight-data:/home/hindsight/.pg0`
- **Render:** Add persistent disk at mount path `/home/hindsight/.pg0`

### Issue 2: 404 on All Endpoints

**Symptom:** GET/POST to `/search`, `/records` returns 404

**Cause:** Using old endpoint paths (the code has been fixed)

**Fix:** Use the correct v1 API paths:
```env
HINDSIGHT_BASE_URL=https://your-hindsight.onrender.com
# Paths are auto-set, but you can override:
HINDSIGHT_SEARCH_PATH=/v1/default/banks/ramp-onboarding-demo/memories/recall
HINDSIGHT_WRITE_PATH=/v1/default/banks/ramp-onboarding-demo/memories/retain
```

### Issue 3: Backend Falls Back to Local

**Symptom:** Logs show "falling back to local store"

**Cause:** Hindsight service not reachable or health check fails

**Debug:**
```bash
# Test Hindsight health
curl https://your-hindsight.onrender.com/health

# Test search endpoint
curl -X POST https://your-hindsight.onrender.com/v1/default/banks/test/memories/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 1}'
```

### Issue 4: LLM Provider Errors

**Symptom:** Hindsight starts but can't process queries

**Cause:** Missing or invalid LLM API key

**Fix:** Set correct provider and key:
```env
# For Groq
HINDSIGHT_API_LLM_PROVIDER=groq
HINDSIGHT_API_LLM_API_KEY=gsk_...

# For OpenAI
HINDSIGHT_API_LLM_PROVIDER=openai
HINDSIGHT_API_LLM_API_KEY=sk-...

# For Anthropic
HINDSIGHT_API_LLM_PROVIDER=anthropic
HINDSIGHT_API_LLM_API_KEY=sk-ant-...
```

## Testing Your Setup

### 1. Test Hindsight Health

```bash
curl https://your-hindsight.onrender.com/health
# Should return: {"status":"healthy","database":"connected"}
```

### 2. Test Memory Write

```bash
curl -X POST https://your-hindsight.onrender.com/v1/default/banks/test/memories/retain \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test memory content",
    "tags": ["test"],
    "metadata": {"source": "api-test"}
  }'
```

### 3. Test Memory Search

```bash
curl -X POST https://your-hindsight.onrender.com/v1/default/banks/test/memories/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "top_k": 5
  }'
```

### 4. Test from Your App

Run the test script:
```bash
python3 test_hindsight_api.py
```

## Architecture Decisions

### Why Self-Hosted?

Hindsight is designed to be self-hosted so you:
- ✅ Own your data completely
- ✅ Control costs (no per-API-call charges)
- ✅ Customize and extend as needed
- ✅ Run on-premise if required

### Why Embedded PostgreSQL?

Hindsight uses embedded Postgres for:
- ✅ Zero external dependencies
- ✅ Simple deployment (single container)
- ✅ Vector search built-in
- ✅ ACID guarantees

### Local vs HTTP Backend

**Local (File-Based):**
- ✅ No external service needed
- ✅ Simple setup
- ✅ Fast (no network)
- ❌ Single instance only
- ❌ No horizontal scaling

**HTTP (Hindsight Service):**
- ✅ Can scale horizontally (multiple backend instances)
- ✅ Shared memory across services
- ✅ Better for production
- ✅ Advanced vector search
- ❌ Requires running Hindsight service

## Cost Estimation (Render)

**Hindsight Service:**
- Instance: $7/month (512MB)
- Disk: $0.25/GB/month (1GB = $0.25)
- **Total:** ~$7.25/month

**Plus your backend/frontend costs**

Much cheaper than hosted embedding/vector search services!

## Next Steps

1. **Deploy Hindsight** on Render with persistent disk
2. **Update backend** environment variables
3. **Test** with `test_hindsight_api.py`
4. **Monitor** logs for "Using HTTP Hindsight backend"
5. **Verify** memories persist across restarts

## Resources

- **Hindsight GitHub:** https://github.com/vectorize-io/hindsight
- **Vectorize.io:** https://vectorize.io
- **Docker Image:** ghcr.io/vectorize-io/hindsight:latest
- **API Docs:** Check Hindsight repo for latest API reference

---

**Summary:** Hindsight is self-hosted. Deploy it as a Docker service, mount persistent storage, and point your backend at it. The code has been updated to use the correct v1 API paths! 🚀
