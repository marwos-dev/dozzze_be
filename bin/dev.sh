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

echo "Creando datos de ejemplo..."
python manage.py seed_demo

echo "Levantando servidor..."
exec python manage.py runserver 0.0.0.0:8000
