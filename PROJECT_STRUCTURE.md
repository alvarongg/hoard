# 📁 Estructura del Repositorio H.O.A.R.D.

```
hoard/
├── .github/
│   ├── workflows/
│   │   ├── backend-tests.yml       # CI para backend
│   │   ├── frontend-tests.yml      # CI para frontend
│   │   ├── accessibility.yml       # Tests de accesibilidad
│   │   └── docker-build.yml        # Build de imágenes Docker
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── translation.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── collections.py
│   │   │   ├── catalog_items.py
│   │   │   ├── collection_items.py
│   │   │   ├── wishlist.py
│   │   │   ├── suppliers.py
│   │   │   ├── accessories.py
│   │   │   ├── images.py
│   │   │   ├── backups.py
│   │   │   ├── import_export.py
│   │   │   └── stats.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── collection.py
│   │   │   ├── catalog.py
│   │   │   ├── item.py
│   │   │   ├── wishlist.py
│   │   │   ├── supplier.py
│   │   │   └── accessory.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── collection.py
│   │   │   ├── catalog.py
│   │   │   ├── item.py
│   │   │   └── wishlist.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── collection_service.py
│   │   │   ├── catalog_service.py
│   │   │   └── search_service.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── backup_service.py
│   │   ├── image_processor.py
│   │   ├── catalog_importer.py
│   │   ├── google_drive_client.py
│   │   └── dropbox_client.py
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_collections.py
│   │   ├── test_catalog.py
│   │   └── test_wishlist.py
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   ├── pytest.ini
│   └── main.py
│
├── frontend/
│   ├── public/
│   │   ├── locales/              # Archivos de traducción
│   │   │   ├── es/
│   │   │   │   └── translation.json
│   │   │   ├── en/
│   │   │   │   └── translation.json
│   │   │   ├── pt/
│   │   │   └── fr/
│   │   ├── icons/
│   │   │   ├── icon-192.png
│   │   │   ├── icon-512.png
│   │   │   └── favicon.ico
│   │   ├── manifest.json
│   │   └── robots.txt
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   ├── collections/
│   │   │   │   ├── CollectionCard.tsx
│   │   │   │   ├── CollectionForm.tsx
│   │   │   │   ├── CollectionList.tsx
│   │   │   │   └── CollectionDetail.tsx
│   │   │   ├── items/
│   │   │   │   ├── ItemCard.tsx
│   │   │   │   ├── ItemForm.tsx
│   │   │   │   ├── ItemGrid.tsx
│   │   │   │   └── ItemDetail.tsx
│   │   │   ├── catalog/
│   │   │   │   ├── CatalogBrowser.tsx
│   │   │   │   ├── CatalogImporter.tsx
│   │   │   │   └── CatalogItemCard.tsx
│   │   │   ├── wishlist/
│   │   │   │   ├── WishlistCard.tsx
│   │   │   │   ├── WishlistForm.tsx
│   │   │   │   └── SightingForm.tsx
│   │   │   ├── images/
│   │   │   │   ├── ImageUploader.tsx
│   │   │   │   ├── ImageGallery.tsx
│   │   │   │   └── ImageEditor.tsx
│   │   │   ├── stats/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── Charts.tsx
│   │   │   │   └── ValueTracker.tsx
│   │   │   └── ui/              # shadcn/ui components
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── dialog.tsx
│   │   │       └── ...
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Collections.tsx
│   │   │   ├── CollectionDetail.tsx
│   │   │   ├── Catalog.tsx
│   │   │   ├── Wishlist.tsx
│   │   │   ├── Suppliers.tsx
│   │   │   ├── Accessories.tsx
│   │   │   ├── Stats.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── Import.tsx
│   │   ├── hooks/
│   │   │   ├── useCollections.ts
│   │   │   ├── useItems.ts
│   │   │   ├── useCatalog.ts
│   │   │   ├── useOfflineSync.ts
│   │   │   └── useTranslation.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── offlineService.ts
│   │   │   └── syncService.ts
│   │   ├── i18n/
│   │   │   ├── index.ts
│   │   │   └── config.ts
│   │   ├── utils/
│   │   │   ├── accessibility.ts
│   │   │   └── helpers.ts
│   │   ├── types/
│   │   │   ├── collection.ts
│   │   │   ├── item.ts
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/
│   │   └── accessibility/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   └── .eslintrc.js
│
├── database/
│   ├── schema.sql                # Schema v2 completo
│   ├── seed_data.sql             # Datos de ejemplo
│   ├── migration_v1_to_v2.sql    # Migración de v1 a v2
│   ├── migration_add_manufacturer_fields.sql
│   └── examples.sql              # Ejemplos de uso
│
├── nginx/
│   ├── nginx.conf
│   ├── conf.d/
│   │   ├── default.conf
│   │   └── ssl.conf
│   └── Dockerfile
│
├── docs/
│   ├── BRANDING.md               # Guía de identidad de marca
│   ├── DOCKER_ARCHITECTURE.md    # Arquitectura Docker
│   ├── USER_GUIDE.md             # Guía del usuario
│   ├── API_DOCUMENTATION.md      # Documentación de API
│   ├── DEPLOYMENT.md             # Guía de deployment
│   ├── DEVELOPMENT.md            # Guía de desarrollo
│   ├── ACCESSIBILITY.md          # Guía de accesibilidad
│   └── I18N.md                   # Guía de internacionalización
│
├── scripts/
│   ├── setup-dev.sh              # Setup entorno desarrollo
│   ├── run-tests.sh              # Ejecutar todos los tests
│   ├── deploy.sh                 # Script de deploy
│   ├── backup.sh                 # Backup manual
│   └── restore.sh                # Restaurar backup
│
├── uploads/                       # Imágenes subidas (gitignored)
│   └── .gitkeep
│
├── backups/                       # Backups automáticos (gitignored)
│   └── .gitkeep
│
├── .github/
├── .gitignore
├── .env.example
├── docker-compose.yml            # Desarrollo
├── docker-compose.prod.yml       # Producción
├── README.md                     # README principal del proyecto
├── CONTRIBUTING.md               # Guía de contribución
├── LICENSE                       # Licencia MIT
└── CHANGELOG.md                  # Registro de cambios
```

## 📝 Notas

### Archivos de Configuración Importantes

- **`.env.example`**: Template de variables de entorno
- **`docker-compose.yml`**: Orquestación para desarrollo
- **`docker-compose.prod.yml`**: Orquestación para producción
- **`alembic.ini`**: Configuración de migraciones de BD
- **`pytest.ini`**: Configuración de tests backend
- **`vitest.config.ts`**: Configuración de tests frontend
- **`playwright.config.ts`**: Configuración de tests E2E
- **`tailwind.config.js`**: Configuración de Tailwind
- **`tsconfig.json`**: Configuración de TypeScript

### Directorios Especiales

- **`uploads/`**: Almacena imágenes de items (gitignored, solo .gitkeep)
- **`backups/`**: Backups automáticos (gitignored, solo .gitkeep)
- **`public/locales/`**: Archivos de traducción por idioma
- **`alembic/versions/`**: Archivos de migración de BD

### Convenciones

- Tests en `tests/` o `__tests__/` junto al código
- Componentes en PascalCase
- Hooks en camelCase con prefijo `use`
- Archivos de utilidades en snake_case (Python) o camelCase (TypeScript)
