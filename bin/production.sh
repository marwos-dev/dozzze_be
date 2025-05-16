#!/bin/bash

# Espera a que la base de datos esté lista
echo "Esperando a la base de datos..."
: "${DB_HOST:=db}"
until nc -z $DB_HOST 5432; do
  echo "Esperando a la base de datos en $DB_HOST:5432..."
  sleep 1
done
echo "Base de datos disponible."

echo "Corriendo collectstatic..."
python manage.py collectstatic --noinput

echo "Corriendo migraciones..."
python manage.py migrate

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
