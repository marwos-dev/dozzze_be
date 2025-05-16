#!/bin/bash

# Espera a que la base de datos esté lista
echo "Esperando a la base de datos..."
while ! nc -z db 5432; do
  sleep 1
done

echo "Base de datos disponible."
python manage.py makemigrations

echo "Corriendo migraciones..."
python manage.py migrate

echo "Corriendo collectstatic..."
python manage.py collectstatic --noinput

echo "Creando usuario inicial si no existe..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "1234")
    print("Superusuario creado: admin / 1234")
else:
    print("El superusuario ya existe.")
EOF

echo "Levantando servidor..."
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
