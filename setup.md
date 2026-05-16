# Docker Setup

## Перший запуск
```bash
cp .env.example .env
docker compose up --build -d
```

## Запуск
```bash
docker compose up -d
```

## Стоп
```bash
docker compose stop
```

## Видалення (контейнер + мережа)
```bash
docker compose down
```

## Повне видалення (з образом)
```bash
docker compose down --rmi local
```
