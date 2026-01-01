# Install production dependencies only
```bash
uv sync --no-dev
```

# Install production + dev dependencies
```bash
uv sync
```

# Install và add dev dependency
```bash
uv add --dev pytest
```

# Remove dev dependency
```bash
uv remove --dev pytest
```

# Stop all docker container but don't remove its: 
```bash
docker stop $(docker ps -q)
```


# Push image to DockerHub
```bash
# 1. Login (create token with read&write permission)
docker login
# 2. Create tag 
# Command: docker tag <name-local> <username>/<new-name>:<tag>
docker tag ai-agent:1.0 username/ai-agent:1.0
# 3. Push to dockerhub 
docker push username/ai-agent:1.0
```
