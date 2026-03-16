# 🐳 H.O.A.R.D. - Arquitectura Docker

Guía completa de la arquitectura Docker para H.O.A.R.D.

---

## 📐 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                        NGINX (Reverse Proxy)                 │
│                         Port 80/443                          │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
    ┌─────────▼─────────┐       ┌─────────▼──────────┐
    │    FRONTEND       │       │     BACKEND        │
    │   (React SPA)     │       │    (FastAPI)       │
    │   Port 3000       │       │    Port 8000       │
    └───────────────────┘       └─────────┬──────────┘
                                          │
                                ┌─────────▼──────────┐
                                │    POSTGRESQL      │
                                │    Port 5432       │
                                └────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      VOLUMES (Persistencia)                   │
├──────────────────────────────────────────────────────────────┤
│  - postgres_data (base de datos)                             │
│  - uploads (imágenes de items)                               │
│  - backups (backups automáticos)                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Estructura de Contenedores

### **1. PostgreSQL (Base de Datos)**

**Responsabilidades:**
- Almacenar todas las colecciones, items, catálogos
- Ejecutar búsquedas full-text
- Gestionar relaciones entre entidades
- Triggers y procedimientos automáticos

**Configuración:**
```yaml
db:
  image: postgres:14-alpine
  container_name: hoard_db
  restart: unless-stopped
  environment:
    POSTGRES_DB: hoard_db
    POSTGRES_USER: hoard_user
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=es_ES.UTF-8"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
  ports:
    - "5432:5432"
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U hoard_user -d hoard_db"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Volúmenes:**
- `postgres_data`: Persistencia de la BD
- `init.sql`: Script de inicialización con schema

---

### **2. Backend (FastAPI)**

**Responsabilidades:**
- API REST para todas las operaciones CRUD
- Autenticación y autorización (futuro)
- Procesamiento de imágenes
- Backups automáticos programados
- Integración con APIs externas (Google Drive, Dropbox)
- Importación/Exportación de catálogos

**Configuración:**
```yaml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
  container_name: hoard_backend
  restart: unless-stopped
  environment:
    DATABASE_URL: postgresql://hoard_user:${DB_PASSWORD}@db:5432/hoard_db
    SECRET_KEY: ${SECRET_KEY}
    UPLOAD_DIR: /app/uploads
    BACKUP_DIR: /app/backups
    CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}
    GOOGLE_DRIVE_ENABLED: ${GOOGLE_DRIVE_ENABLED:-false}
    GOOGLE_DRIVE_CREDENTIALS: ${GOOGLE_DRIVE_CREDENTIALS}
    DROPBOX_ENABLED: ${DROPBOX_ENABLED:-false}
    DROPBOX_TOKEN: ${DROPBOX_TOKEN}
  volumes:
    - ./uploads:/app/uploads
    - ./backups:/app/backups
    - ./backend:/app
  ports:
    - "8000:8000"
  depends_on:
    db:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Dockerfile Backend:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/uploads /app/backups

# Usuario no-root
RUN useradd -m -u 1000 hoard && \
    chown -R hoard:hoard /app
USER hoard

EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Volúmenes:**
- `uploads`: Imágenes de items
- `backups`: Backups automáticos
- `backend` (desarrollo): Hot reload

---

### **3. Frontend (React)**

**Responsabilidades:**
- Interfaz de usuario SPA
- PWA con soporte offline
- Gestión de estado (React Query)
- i18n (multi-idioma)
- Accesibilidad WCAG 2.1 AA

**Configuración:**
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    args:
      VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
  container_name: hoard_frontend
  restart: unless-stopped
  environment:
    VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
  volumes:
    - ./frontend:/app
    - /app/node_modules
  ports:
    - "3000:3000"
  depends_on:
    - backend
```

**Dockerfile Frontend (Desarrollo):**
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Dependencias
COPY package*.json ./
RUN npm ci

# Código
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Dockerfile Frontend (Producción):**
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

### **4. NGINX (Reverse Proxy - Producción)**

**Responsabilidades:**
- Servir frontend estático
- Proxy a backend API
- SSL/TLS termination
- Compresión gzip
- Caching de assets

**Configuración:**
```yaml
nginx:
  image: nginx:alpine
  container_name: hoard_nginx
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    - ./nginx/conf.d:/etc/nginx/conf.d
    - ./frontend/dist:/usr/share/nginx/html
    - ./certbot/conf:/etc/letsencrypt
    - ./certbot/www:/var/www/certbot
  depends_on:
    - frontend
    - backend
```

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name hoard.local;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
        
        # Caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API Backend
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Uploads
    location /uploads/ {
        proxy_pass http://backend:8000/uploads/;
        proxy_set_header Host $host;
    }

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

---

## 📦 docker-compose.yml Completo

### **Desarrollo:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    container_name: hoard_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: hoard_db
      POSTGRES_USER: hoard_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./database/seed_data.sql:/docker-entrypoint-initdb.d/02-seed.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hoard_user -d hoard_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: hoard_backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://hoard_user:${DB_PASSWORD}@db:5432/hoard_db
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: development
      RELOAD: "true"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
      - ./backups:/app/backups
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: hoard_frontend
    restart: unless-stopped
    environment:
      VITE_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### **Producción:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    container_name: hoard_db_prod
    restart: always
    environment:
      POSTGRES_DB: hoard_db
      POSTGRES_USER: hoard_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - hoard_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hoard_user -d hoard_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: hoard_backend_prod
    restart: always
    environment:
      DATABASE_URL: postgresql://hoard_user:${DB_PASSWORD}@db:5432/hoard_db
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    volumes:
      - ./uploads:/app/uploads
      - ./backups:/app/backups
    networks:
      - hoard_network
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: ${API_URL}
    container_name: hoard_frontend_prod
    restart: always
    networks:
      - hoard_network
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    container_name: hoard_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    networks:
      - hoard_network
    depends_on:
      - frontend
      - backend

  certbot:
    image: certbot/certbot
    container_name: hoard_certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:

networks:
  hoard_network:
    driver: bridge
```

---

## 🔧 Variables de Entorno

### **.env (Desarrollo)**
```bash
# Database
DB_PASSWORD=hoard_dev_password_2024

# Backend
SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000

# Cloud Storage (opcional)
GOOGLE_DRIVE_ENABLED=false
GOOGLE_DRIVE_CREDENTIALS=
DROPBOX_ENABLED=false
DROPBOX_TOKEN=

# Frontend
VITE_API_URL=http://localhost:8000
```

### **.env (Producción)**
```bash
# Database
DB_PASSWORD=STRONG_RANDOM_PASSWORD_HERE

# Backend
SECRET_KEY=STRONG_RANDOM_SECRET_KEY_HERE
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com

# Cloud
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_CREDENTIALS=/path/to/credentials.json
DROPBOX_ENABLED=false

# Frontend
API_URL=https://yourdomain.com
VITE_API_URL=https://yourdomain.com/api
```

---

## 🚀 Comandos Útiles

### **Desarrollo:**

```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend

# Reconstruir imágenes
docker-compose up -d --build

# Detener todo
docker-compose down

# Detener y eliminar volúmenes (¡CUIDADO!)
docker-compose down -v

# Ejecutar comando en contenedor
docker-compose exec backend bash
docker-compose exec db psql -U hoard_user -d hoard_db

# Ver estado de servicios
docker-compose ps

# Reiniciar un servicio
docker-compose restart backend
```

### **Base de Datos:**

```bash
# Aplicar migraciones
docker-compose exec backend alembic upgrade head

# Crear nueva migración
docker-compose exec backend alembic revision --autogenerate -m "descripcion"

# Backup manual
docker-compose exec db pg_dump -U hoard_user hoard_db > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker-compose exec -T db psql -U hoard_user hoard_db < backup_20240101.sql

# Acceder a psql
docker-compose exec db psql -U hoard_user -d hoard_db
```

### **Producción:**

```bash
# Deploy inicial
docker-compose -f docker-compose.prod.yml up -d --build

# Ver logs en producción
docker-compose -f docker-compose.prod.yml logs -f

# Actualizar código
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Backup de BD en producción
docker-compose -f docker-compose.prod.yml exec db pg_dump -U hoard_user hoard_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

## 📊 Recursos y Límites

### **Recomendaciones Mínimas:**
```yaml
services:
  db:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          memory: 512M

  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          memory: 512M

  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

---

## 🔒 Seguridad

### **Checklist de Seguridad:**

- [ ] Cambiar contraseñas por defecto
- [ ] Usar secrets de Docker para credenciales
- [ ] No exponer puertos innecesarios
- [ ] Ejecutar contenedores como usuario no-root
- [ ] Actualizar imágenes regularmente
- [ ] Usar HTTPS en producción
- [ ] Configurar firewall
- [ ] Limitar CORS adecuadamente
- [ ] Sanitizar inputs en backend
- [ ] Rate limiting en nginx

---

## 📚 Troubleshooting

### **Problema: Base de datos no se conecta**
```bash
# Verificar que el contenedor está corriendo
docker-compose ps

# Ver logs de la BD
docker-compose logs db

# Verificar health check
docker inspect hoard_db --format='{{.State.Health.Status}}'
```

### **Problema: Frontend no puede conectarse al backend**
```bash
# Verificar URL de API en frontend
docker-compose exec frontend env | grep VITE_API_URL

# Verificar que backend responde
curl http://localhost:8000/health
```

### **Problema: Volúmenes con permisos incorrectos**
```bash
# Ajustar permisos
sudo chown -R 1000:1000 ./uploads ./backups
```

---

## 🎯 Próximos Pasos

1. Implementar los Dockerfiles
2. Configurar docker-compose
3. Crear scripts de inicialización
4. Configurar nginx para producción
5. Setup de SSL/TLS con Let's Encrypt
6. Documentar proceso de deploy

---

**Arquitectura diseñada para:** Escalabilidad, Mantenibilidad, Seguridad
**Objetivo:** Deploy simple con `docker-compose up`
