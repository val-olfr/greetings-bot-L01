# Greetings bot (Telegam)

## Initial 

## Details

## Installation steps

### Build dockerfiles:

```
docker build -f dockerfiles/Dockerfile_poller -t gr_bot_puller:latest .
docker build -f dockerfiles/Dockerfile_worker -t gr_bot_worker:latest .
```

### Build and run with docker-compose file:

```
docker compose -f docker-compose.yaml down
docker compose -f docker-compose.yaml up --build -d
```