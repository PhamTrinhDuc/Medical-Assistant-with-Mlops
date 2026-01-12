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

# Runner Github-Action 
- Once you have installed the Runner as a Service (using ./svc.sh install), you no longer need to run any commands each time you want to start it. Ubuntu's systemd will automatically manage it
```bash
sudo ./svc.sh install
sudo ./svc.sh start
```
- When you want to maintain the server and don't want to receive jobs from GitHub.
```bash
sudo ./svc.sh stop
```