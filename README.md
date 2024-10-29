# Локальный запуск

### WSGI
```commandline
python manage.py runserver
```

Или

```commandline
gunicorn chat_api.wsgi:application
```

### ASGI
```commandline
daphne chat_api.asgi:application --port 8001
```


# Запуск контейнера
```commandline
docker-compose up --build
```

### Содержимое .env
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=test_task

DB_HOST=db
DB_NAME=test_task
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432
```

# Запуск тестов
```commandline
python manage.py test
```
Предварительно должен быть запущен Redis