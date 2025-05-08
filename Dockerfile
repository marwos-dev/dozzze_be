# backend/Dockerfile

FROM python:3.11-slim

# Instalamos dependencias del sistema necesarias para GDAL y PostgreSQL
RUN apt-get update && apt-get install -y \
    gdal-bin libgdal-dev libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Seteamos variables necesarias para compilar GDAL en Python
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Crear directorio del proyecto
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto (si estás corriendo con runserver)
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
