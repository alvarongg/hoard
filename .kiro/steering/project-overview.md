---
inclusion: always
---

# H.O.A.R.D. - Project Overview

H.O.A.R.D. (Hobby Organization, Archive & Registry Database) es un sistema de gestión de colecciones multi-categoría, self-hosted y open source.

## Stack Tecnológico

### Backend
- Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, PostgreSQL 14+, pytest

### Frontend
- React 18, TypeScript, Vite, TailwindCSS, shadcn/ui, i18next, react-aria, Vitest, Playwright, axe-core

### Infraestructura
- Docker, Docker Compose, Nginx

## Estructura del Proyecto

```
hoard/
├── backend/           # FastAPI Backend (Python)
│   ├── api/
│   │   ├── routes/    # Endpoints REST
│   │   ├── models/    # SQLAlchemy Models
│   │   ├── schemas/   # Pydantic Schemas
│   │   ├── services/  # Lógica de negocio
│   │   └── dependencies.py
│   ├── core/          # Config, DB, Security
│   ├── utils/         # Servicios auxiliares
│   ├── alembic/       # Migraciones DB
│   └── tests/         # Tests backend
├── frontend/          # React Frontend (TypeScript)
│   ├── src/
│   │   ├── components/  # Componentes React (.tsx)
│   │   ├── pages/       # Páginas (.tsx)
│   │   ├── hooks/       # Custom hooks (.ts)
│   │   ├── services/    # API clients (.ts)
│   │   ├── types/       # TypeScript types (.ts)
│   │   ├── i18n/        # Configuración i18n
│   │   └── utils/       # Utilidades (.ts)
│   └── tests/           # Tests frontend
├── database/          # SQL schemas, seeds, migraciones
├── docs/              # Documentación
└── nginx/             # Configuración Nginx
```

## Fases de Desarrollo

- Fase 1: MVP (CRUD básico, Docker, i18n ES/EN, tests >70%)
- Fase 2: Core (multi-category, wishlist, búsqueda, dark mode)
- Fase 3: Advanced (PWA, gráficos, import/export, backups)
- Fase 4: Integraciones (Google Drive, Dropbox, APIs externas)
- Fase 5: Production (multi-usuario, JWT, CI/CD, WCAG AA)

## Base de Datos

PostgreSQL con 17 tablas principales. Schema completo en `database/schema.sql`.
Tablas clave: main_categories, sub_categories, catalogs, catalog_items, collections, collection_items, wishlist_items, wishlist_sightings, suppliers, accessories_stock.

## Referencias Clave

- #[[file:KIRO_HANDOFF.md]] - Resumen ejecutivo completo
- #[[file:PROJECT_STRUCTURE.md]] - Estructura detallada
- #[[file:database/schema.sql]] - Schema PostgreSQL v2
- #[[file:docs/DOCKER_ARCHITECTURE.md]] - Arquitectura Docker
- #[[file:docs/USER_GUIDE.md]] - Guía del usuario
- #[[file:docs/BRANDING.md]] - Identidad de marca
