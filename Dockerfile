FROM python:3.12.10-alpine3.22

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (incluyendo GDAL, GEOS y PostgreSQL)
RUN apk add --no-cache \
    bash \
    gdal-dev \
    geos-dev \
    proj-dev \
    libpq-dev \
    build-base \
    python3-dev \
    postgresql-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    py3-pip \
    && ln -sf python3 /usr/bin/python

# Copiar archivo de requerimientos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar código fuente
COPY . .

# Variables de entorno para GDAL y GEOS (ajustadas para Alpine/Linux)
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["bin/dev.sh"]
