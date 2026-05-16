# Docker Setup

## First run
```powershell
Copy-Item .env.example .env
docker-compose up --build -d
```

## Run
```powershell
docker-compose up -d
```

## Stop
```powershell
docker-compose stop
```

## Remove
```powershell
docker-compose down
```

## Remove with image
```powershell
docker-compose down --rmi local
```
