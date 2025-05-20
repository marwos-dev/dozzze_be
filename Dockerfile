FROM python:3.11-alpine

# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias
RUN apk add --no-cache \
    python3=3.12.11-r0 \
    bash \
    build-base \
    gdal-dev \
    geos-dev \
    proj-dev \
    libpq-dev \
    postgresql-dev \
    py3-pip \
    python3-dev \
    musl-dev \
    && ln -sf python3 /usr/bin/python

# Link simbólico para GEOS (a veces requerido por dependencias C)
RUN ln -s /usr/lib/libgeos_c.so /usr/lib/libgeos_c.dylib || true

# Link simbólico si falta libgdal.so
RUN [ -f /usr/lib/libgdal.so ] || ln -s /usr/lib/libgdal.so.* /usr/lib/libgdal.so

# Configura variables de entorno para librerías compartidas
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so.1
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so

# Copia el archivo de requerimientos
COPY requirements.txt .

# Instala dependencias de Python
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

# Copia el resto del código fuente
COPY . .

# Exponer el puerto de desarrollo
EXPOSE 8000



CMD ["bin/production.sh"]
