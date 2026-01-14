# Migration Guide: Langfuse → Arize Phoenix

## Tổng quan thay đổi

### Thay đổi chính
- ✅ **Langfuse** → **Arize Phoenix** cho monitoring agent
- ✅ Phoenix sử dụng **OpenInference** instrumentation (automatic tracing)
- ✅ Không cần explicit callbacks - tracing tự động ở SDK level
- ✅ Tích hợp OTLP endpoint cho distributed tracing

## Dependencies Changed

### Removed
```toml
langfuse>=2.60.10
```

### Added
```toml
arize-phoenix>=12.29.0
arize-phoenix-otel>=0.14.0
openinference-instrumentation-langchain>=0.1.58
```

## Configuration Changes

### Environment Variables

**Removed:**
```bash
LANGFUSE_SECRET_KEY=xxx
LANGFUSE_PUBLIC_KEY=xxx
LANGFUSE_ENDPOINT=https://cloud.langfuse.com
```

**Added:**
```bash
# Phoenix Configuration
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=chatbot-hospital-healcare
```

### Config File (utils/config.py)

**Before:**
```python
LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_ENDPOINT: str = os.getenv("LANGFUSE_ENDPOINT")
```

**After:**
```python
PHOENIX_ENDPOINT: str = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006/v1/traces")
PHOENIX_PROJECT_NAME: str = os.getenv("PHOENIX_PROJECT_NAME", APP_NAME)
```

## Code Changes

### 1. Health Check (utils/check_connection.py)

**Before:**
```python
from langfuse import Langfuse

# Check Langfuse
langfuse = Langfuse(
    public_key=AppConfig.LANGFUSE_PUBLIC_KEY,
    secret_key=AppConfig.LANGFUSE_SECRET_KEY,
    host=AppConfig.LANGFUSE_ENDPOINT,
)
result = langfuse.auth_check()
```

**After:**
```python
import httpx

# Check Phoenix
phoenix_url = AppConfig.PHOENIX_ENDPOINT.replace("/v1/traces", "")
async with httpx.AsyncClient() as client:
    response = await client.get(f"{phoenix_url}/healthz", timeout=5.0)
    if response.status_code == 200:
        status["phoenix"] = True
```

### 2. Agent Callbacks (agents/hospital_rag_agent.py)

**Before:**
```python
def __init__(self, ...):
    self._callback = None

# Callbacks were referenced but never initialized (bug!)
callbacks=[self.callbacks]  # This would fail
```

**After:**
```python
@property
def callbacks(self):
    """
    Phoenix tracing is automatic via OpenInference instrumentation.
    No explicit callbacks needed - tracing happens at the SDK level.
    """
    return []
```

### 3. Application Startup (main.py)

**Before:**
```python
# Check external services
service_status = await _check_external_services()
critical_services = ["elasticsearch", "neo4j", "redis", "langfuse"]
```

**After:**
```python
# Setup Phoenix tracing FIRST
setup_phoenix_tracing()

# Check external services
service_status = await _check_external_services()
critical_services = ["elasticsearch", "neo4j", "redis"]  # Phoenix not critical

# Shutdown
shutdown_phoenix()
```

## How Phoenix Works

### Automatic Instrumentation

Phoenix uses **OpenInference** to automatically trace:
- ✅ LangChain agents
- ✅ LLM calls (OpenAI, Google, etc.)
- ✅ Chains & tools
- ✅ Vector stores
- ✅ Embeddings

**No manual callback setup needed!**

```python
from utils import setup_phoenix_tracing

# One-time setup at app start
setup_phoenix_tracing()

# All LangChain operations are now traced automatically
agent = HospitalRAGAgent(...)
result = agent.invoke("query")  # ← Automatically traced!
```

### Phoenix UI Access

- **URL**: http://localhost:6006
- **Username**: admin
- **Password**: admin (configurable)

### Features
- 📊 Real-time traces & spans
- 🔍 LLM I/O inspection
- 📈 Latency & cost tracking
- 🔗 Distributed tracing
- 💾 Persistent storage

## Docker Compose

Phoenix is already configured in `mlops/docker/docker-compose.yml`:

```yaml
phoenix:
  image: arizephoenix/phoenix:latest
  ports:
    - "6006:6006"
  environment:
    PHOENIX_USERNAME: admin
    PHOENIX_PASSWORD: admin
  volumes:
    - phoenix_data:/app/data
```

Start it:
```bash
docker-compose up -d phoenix
```

## Testing

### 1. Install dependencies
```bash
cd backend
uv sync
```

### 2. Set environment variables
```bash
# .env.dev
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=chatbot-hospital-healcare
```

### 3. Start Phoenix
```bash
docker-compose up -d phoenix
```

### 4. Run application
```bash
uv run uvicorn main:app --reload
```

### 5. Check Phoenix UI
Open http://localhost:6006 and make some requests to the API.

## Key Benefits

| Feature | Langfuse | Phoenix |
|---------|----------|---------|
| Setup complexity | High (auth keys, cloud) | Low (local, no auth) |
| Callback handling | Manual | Automatic |
| Local development | Requires cloud/self-host | Built-in local |
| LLM provider support | Good | Excellent |
| Trace visualization | Good | Excellent |
| Cost | Paid/self-host | Free & open-source |

## Migration Checklist

- [x] Update pyproject.toml dependencies
- [x] Remove Langfuse config from .env files
- [x] Add Phoenix config to AppConfig
- [x] Create phoenix_instrumentation.py
- [x] Update health check
- [x] Update HospitalRAGAgent callbacks
- [x] Update main.py startup/shutdown
- [x] Test with docker-compose
- [ ] Update team documentation
- [ ] Train team on Phoenix UI

## Troubleshooting

### Phoenix not connecting
```bash
# Check if Phoenix is running
curl http://localhost:6006/healthz

# Check logs
docker logs phoenix
```

### Traces not appearing
- Ensure `setup_phoenix_tracing()` is called at app startup
- Check PHOENIX_ENDPOINT is correct
- Verify OpenInference instrumentation is active

### Performance issues
Phoenix is lightweight, but if needed:
- Adjust sampling rate in instrumentation
- Use batch export for high-volume
- Enable data retention policies

## Resources

- [Phoenix Documentation](https://docs.arize.com/phoenix)
- [OpenInference Spec](https://github.com/Arize-ai/openinference)
- [LangChain Integration](https://docs.arize.com/phoenix/tracing/integrations-tracing/langchain)
