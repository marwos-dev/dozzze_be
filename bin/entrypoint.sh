#!/bin/bash

# Espera a que la base de datos esté lista
echo "Esperando a la base de datos..."
while ! nc -z db 5432; do
  sleep 1
done

echo "Base de datos disponible. Corriendo migraciones..."
python manage.py migrate

echo "Creando usuario inicial si no existe..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin123")
    print("Superusuario creado: admin / admin123")
else:
    print("El superusuario ya existe.")
EOF

echo "Levantando servidor..."
exec python manage.py runserver 0.0.0.0:8000
