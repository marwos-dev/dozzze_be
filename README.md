# 🛏️ Dozzze – Motor de Reservas

**Dozzze** es un motor de reservas desarrollado en Django, diseñado para
gestionar propiedades, zonas, reservas, clientes y la lógica de disponibilidad
para un sistema de alojamiento personalizado. Este proyecto actúa como backend
para la plataforma **Dozzze**, e incluye integración con Celery, almacenamiento
en AWS S3, JWT para autenticación y PostgreSQL con extensiones geográficas
mediante PostGIS.

---

## 🚀 Tecnologías

- **Python 3.11+**
- **Django 5.2.1**
- **PostgreSQL + PostGIS**
- **Celery + Redis**
- **AWS S3 para archivos estáticos y media**
- **Django Rest Framework + SimpleJWT**
- **Jazzmin para panel de administración**
- **Docker y Docker Compose**
- **Whitenoise para servir estáticos**
- **CORS habilitado para entorno frontend (Next.js, Vercel, etc.)**

---

## 📁 Estructura de apps

- `properties/`: Propiedades, habitaciones, servicios, métodos de comunicación.
- `reservations/`: Gestión de reservas.
- `zones/`: Zonas geográficas.
- `pms/`: Conectores a sistemas de gestión de propiedades.
- `customers/`: Registro, login y gestión de usuarios.

---

## ⚙️ Configuración del entorno

1. Copiá el archivo `.env.example` y completá tus variables:
   ```bash
   cp .env.example .env

2. Incia el proyecto con Docker:
   ```bash
   docker-compose up -d --build
   ```

## 🐳 Servicios Docker

- **db**: PostgreSQL con PostGIS.
- **redis**: Servicio para tareas en background con Celery.
- **web**: Aplicación Django.
- **celery_worker**: Trabajador de Celery.
- **celery_beat**: Scheduler de Celery.

## 🔐 Variables de entorno

- #### Base de datos
  ```
  DB_NAME=motor_reservas
  DB_USER=motor_reserva
  DB_PASSWORD=motor_reserva
  DB_HOST=db
  DB_PORT=5432
  ```

- #### AWS S3
    ```
    AWS_ACCESS_KEY_ID=your-access-key
    AWS_SECRET_ACCESS_KEY=your-secret-key
    AWS_STORAGE_BUCKET_NAME=your-bucket
    AWS_S3_REGION_NAME=us-east-1
    ```

- #### Email
    ```
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_HOST_USER=marwos97@gmail.com
    EMAIL_HOST_PASSWORD=your-password
    DEFAULT_FROM_EMAIL=marwos97@gmail.com
  ```

- #### Celery
  ```
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0
  ```

- #### JWT
  ```
  PUBLIC_API_KEY=clave-larga-y-unica
  MY_FRONTEND_SECRET_TOKEN=token-secreto
  ```

- #### Frontend
  ```
  FRONTEND_URL=http://localhost:3000
  DEVELOPMENT=true
  ```

## 🛠 Comandos útiles

- **Migraciones**:
  ```bash
  docker-compose exec web python manage.py migrate
  ```

- **Crear superusuario**:
  ```bash
  docker-compose exec web python manage.py createsuperuser
  ```

- **Colectar archivos estáticos**:
  ```bash
  docker-compose exec web python manage.py collectstatic --noinput
  ```


## 📮 Contacto
  Desarrollado por Marcos Olmedo
  © 2025 – Dozzze
