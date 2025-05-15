# Usa una imagen base de Python 3.11 en Alpine
FROM python:3.11-alpine

# Establece el directorio de trabajo
WORKDIR /app

# Instala las dependencias del sistema necesarias para GDAL, GEOS y PostgreSQL
RUN apk add --no-cache \
    python3=3.12.10-r0 \
    py3-pip \
    gdal-dev \
    geos-dev \
    proj-dev \
    libpq-dev \
    build-base \
    bash \
    && ln -sf python3 /usr/bin/python

# Asegúrate de que las bibliotecas de GEOS estén enlazadas correctamente
RUN ln -s /usr/lib/libgeos_c.so /usr/lib/libgeos_c.dylib

# Copia el archivo requirements.txt al contenedor
COPY requirements.txt .

# Actualiza pip e instala las dependencias de Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Configura la variable de entorno para GEOS
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so.1

# Copia todo el código (en dev, luego se sobreescribe por volumen)
COPY . .

# Expone el puerto 8000
EXPOSE 8000

CMD ["/app/entrypoint.sh"]