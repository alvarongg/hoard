# 🐉 H.O.A.R.D. - Hobby Organization, Archive & Registry Database

> **"Build your H.O.A.R.D."** - Sistema completo de gestión de colecciones multi-categoría

Sistema de gestión de colecciones con soporte para versiones, idiomas, variaciones y colecciones temáticas cross-category. Como un dragón que custodia sus tesoros, H.O.A.R.D. te ayuda a organizar, valorizar y proteger tu colección.

**Stack:** FastAPI + React.js + PostgreSQL + Docker

---

## 🎨 Branding

### Logo
**Concepto:** Dragón tipo Smaug sobre su montaña de tesoros

**Descripción visual:**
- Silueta de un dragón majestuoso (estilo Smaug de El Hobbit)
- Enroscado sobre una montaña de items de colección (juegos, libros, figuras, vinilos)
- Los items brillan con un resplandor dorado
- Paleta de colores: Dorado, rojo oscuro, negro
- Estilo: Minimalista pero épico, funcionando bien tanto en favicon como en logo completo

**Variantes:**
- **Logo completo:** Dragón + texto "H.O.A.R.D."
- **Icono/Favicon:** Solo silueta del dragón
- **Versión monocromática:** Para fondos claros/oscuros

### Tagline
**Principal:** "Build your H.O.A.R.D."
**Alternativo:** "Guard your treasures like a dragon"

---

## 🎯 Descripción del Proyecto

**H.O.A.R.D. (Hobby Organization, Archive & Registry Database)** es una aplicación web self-hosted para gestionar colecciones de cualquier tipo: videojuegos, música, libros, TCG, juguetes, figuras, etc. 

Como un dragón que custodia celosamente su tesoro, H.O.A.R.D. te permite organizar, valorizar y proteger tu colección con precisión y detalle. 

Permite crear:
- **Colecciones single-category**: Solo items de un tipo (ej: "Juegos de Nintendo 64")
- **Colecciones multi-category**: Items de diferentes categorías bajo un tema (ej: "Todo de Zelda" → juegos + música + libros + figuras)
- **Colecciones mixtas**: Sin restricciones

### Características Principales

✅ **Multi-categoría**: Soporte para múltiples tipos de colecciones  
✅ **Versiones e Idiomas**: Cada versión/idioma/región es un registro único  
✅ **Variaciones**: Soporte para variantes (color, edición, test print, etc.)  
✅ **Catálogos Importables**: Importa catálogos completos (JSON/CSV)  
✅ **Wishlist Avanzada**: Tracking de avistamientos con precios y lugares  
✅ **Historial de Precios**: Seguimiento del valor de mercado histórico  
✅ **Componentes Detallados**: Control granular de cada parte del item  
✅ **Stock de Accesorios**: Gestión de cajas protectoras, sleeves, etc.  
✅ **Imágenes Ilimitadas**: Upload y gestión de fotos (solo rutas en BD)  
✅ **Backups Automáticos**: Exportación a Google Drive/Dropbox/Local  
✅ **PWA**: Funciona offline y se puede instalar como app  
✅ **Self-hosted**: Docker compose para deployment fácil  
✅ **Open Source**: Código abierto y personalizable  

---

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React PWA)                  │
│  - React 18 + Vite                                       │
│  - TailwindCSS + shadcn/ui                              │
│  - React Router                                          │
│  - React Query (cache & sync)                           │
│  - Service Workers (offline support)                    │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API (JSON)
┌─────────────────▼───────────────────────────────────────┐
│                 BACKEND (FastAPI)                        │
│  - FastAPI (Python 3.11+)                               │
│  - SQLAlchemy ORM                                        │
│  - Pydantic (validación)                                │
│  - Alembic (migraciones)                                │
│  - APScheduler (backups)                                │
│  - Pillow (procesamiento imágenes)                      │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              BASE DE DATOS (PostgreSQL 14+)              │
│  - 17 tablas principales                                │
│  - Full-text search                                     │
│  - Triggers automáticos                                 │
│  - Vistas materializadas                                │
└──────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              ALMACENAMIENTO (Filesystem)                 │
│  - Imágenes: /uploads/items/{item_id}/                 │
│  - Backups: /backups/{timestamp}/                       │
│  - Catálogos: /imports/catalogs/                        │
└──────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│            CLOUD STORAGE (Opcional)                      │
│  - Google Drive API                                      │
│  - Dropbox API                                          │
│  - AWS S3                                               │
└──────────────────────────────────────────────────────────┘
```

---

## 🗂️ Estructura del Proyecto

```
hoard/
├── backend/                    # FastAPI Backend
│   ├── api/
│   │   ├── routes/            # Endpoints REST
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
│   │   ├── models/            # SQLAlchemy Models
│   │   ├── schemas/           # Pydantic Schemas
│   │   ├── services/          # Lógica de negocio
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── utils/
│   │   ├── backup_service.py
│   │   ├── image_processor.py
│   │   ├── catalog_importer.py
│   │   ├── google_drive_client.py
│   │   └── dropbox_client.py
│   ├── alembic/               # Migraciones DB
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── frontend/                   # React Frontend
│   ├── public/
│   │   ├── manifest.json      # PWA manifest
│   │   └── service-worker.js
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   └── Footer.jsx
│   │   │   ├── collections/
│   │   │   │   ├── CollectionCard.jsx
│   │   │   │   ├── CollectionForm.jsx
│   │   │   │   ├── CollectionList.jsx
│   │   │   │   └── CollectionDetail.jsx
│   │   │   ├── items/
│   │   │   │   ├── ItemCard.jsx
│   │   │   │   ├── ItemForm.jsx
│   │   │   │   ├── ItemGrid.jsx
│   │   │   │   └── ItemDetail.jsx
│   │   │   ├── catalog/
│   │   │   │   ├── CatalogBrowser.jsx
│   │   │   │   ├── CatalogImporter.jsx
│   │   │   │   └── CatalogItemCard.jsx
│   │   │   ├── wishlist/
│   │   │   │   ├── WishlistCard.jsx
│   │   │   │   ├── WishlistForm.jsx
│   │   │   │   └── SightingForm.jsx
│   │   │   ├── images/
│   │   │   │   ├── ImageUploader.jsx
│   │   │   │   ├── ImageGallery.jsx
│   │   │   │   └── ImageEditor.jsx
│   │   │   ├── stats/
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── Charts.jsx
│   │   │   │   └── ValueTracker.jsx
│   │   │   └── ui/            # shadcn/ui components
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Collections.jsx
│   │   │   ├── CollectionDetail.jsx
│   │   │   ├── Catalog.jsx
│   │   │   ├── Wishlist.jsx
│   │   │   ├── Suppliers.jsx
│   │   │   ├── Accessories.jsx
│   │   │   ├── Stats.jsx
│   │   │   ├── Settings.jsx
│   │   │   └── Import.jsx
│   │   ├── hooks/
│   │   │   ├── useCollections.js
│   │   │   ├── useItems.js
│   │   │   ├── useCatalog.js
│   │   │   └── useOfflineSync.js
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── offlineService.js
│   │   │   └── syncService.js
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
│
├── database/
│   ├── schema.sql
│   ├── migrations/
│   └── seed_data.sql
│
├── uploads/                    # Archivos subidos
│   ├── items/
│   └── temp/
│
├── backups/                    # Backups automáticos
│   └── {timestamp}/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔧 BACKEND - Funcionalidades

### **1. API REST - Endpoints Principales**

#### **1.1 Autenticación (Futura)**
```
POST   /api/auth/register       - Registrar usuario
POST   /api/auth/login          - Login
POST   /api/auth/logout         - Logout
GET    /api/auth/me             - Usuario actual
```

#### **1.2 Categorías y Catálogos**
```
GET    /api/categories          - Listar categorías principales
GET    /api/categories/{id}/subcategories - Subcategorías
GET    /api/catalogs            - Listar catálogos
POST   /api/catalogs            - Crear catálogo
GET    /api/catalogs/{id}       - Detalle de catálogo
PUT    /api/catalogs/{id}       - Actualizar catálogo
DELETE /api/catalogs/{id}       - Eliminar catálogo
```

#### **1.3 Items del Catálogo**
```
GET    /api/catalog-items                     - Listar items (con filtros)
POST   /api/catalog-items                     - Crear item
GET    /api/catalog-items/{id}                - Detalle de item
PUT    /api/catalog-items/{id}                - Actualizar item
DELETE /api/catalog-items/{id}                - Eliminar item
GET    /api/catalog-items/search              - Búsqueda full-text
GET    /api/catalog-items/{id}/versions       - Versiones relacionadas
GET    /api/catalog-items/{id}/price-history  - Historial de precios
POST   /api/catalog-items/{id}/price          - Agregar precio histórico
```

#### **1.4 Colecciones**
```
GET    /api/collections         - Listar colecciones
POST   /api/collections         - Crear colección
GET    /api/collections/{id}    - Detalle de colección
PUT    /api/collections/{id}    - Actualizar colección
DELETE /api/collections/{id}    - Eliminar colección
GET    /api/collections/{id}/stats - Estadísticas de colección
GET    /api/collections/{id}/items - Items de la colección
GET    /api/collections/{id}/categories - Desglose por categorías (multi-category)
```

#### **1.5 Items de Colección**
```
GET    /api/collection-items              - Listar items
POST   /api/collection-items              - Agregar item a colección
GET    /api/collection-items/{id}         - Detalle de item
PUT    /api/collection-items/{id}         - Actualizar item
DELETE /api/collection-items/{id}         - Eliminar item
GET    /api/collection-items/{id}/images  - Imágenes del item
POST   /api/collection-items/{id}/images  - Subir imagen
DELETE /api/collection-items/{id}/images/{image_id} - Eliminar imagen
GET    /api/collection-items/{id}/components - Componentes del item
POST   /api/collection-items/{id}/components - Agregar componente
PUT    /api/collection-items/{id}/components/{comp_id} - Actualizar componente
DELETE /api/collection-items/{id}/components/{comp_id} - Eliminar componente
GET    /api/collection-items/{id}/transactions - Historial transacciones
POST   /api/collection-items/{id}/transactions - Agregar transacción
```

#### **1.6 Wishlist**
```
GET    /api/wishlist                       - Listar wishlist
POST   /api/wishlist                       - Agregar a wishlist
GET    /api/wishlist/{id}                  - Detalle wishlist item
PUT    /api/wishlist/{id}                  - Actualizar wishlist item
DELETE /api/wishlist/{id}                  - Eliminar de wishlist
GET    /api/wishlist/{id}/sightings        - Avistamientos
POST   /api/wishlist/{id}/sightings        - Agregar avistamiento
PUT    /api/wishlist/{id}/sightings/{sid}  - Actualizar avistamiento
DELETE /api/wishlist/{id}/sightings/{sid}  - Eliminar avistamiento
POST   /api/wishlist/{id}/acquire          - Marcar como adquirido
```

#### **1.7 Proveedores**
```
GET    /api/suppliers           - Listar proveedores
POST   /api/suppliers           - Crear proveedor
GET    /api/suppliers/{id}      - Detalle de proveedor
PUT    /api/suppliers/{id}      - Actualizar proveedor
DELETE /api/suppliers/{id}      - Eliminar proveedor
GET    /api/suppliers/{id}/purchases - Compras de ese proveedor
```

#### **1.8 Accesorios**
```
GET    /api/accessories         - Listar stock de accesorios
POST   /api/accessories         - Crear accesorio
GET    /api/accessories/{id}    - Detalle de accesorio
PUT    /api/accessories/{id}    - Actualizar accesorio (stock)
DELETE /api/accessories/{id}    - Eliminar accesorio
GET    /api/accessories/low-stock - Accesorios con stock bajo
```

#### **1.9 Importación/Exportación**
```
POST   /api/import/catalog      - Importar catálogo (JSON/CSV)
POST   /api/import/collection   - Importar colección
GET    /api/export/collection/{id} - Exportar colección (JSON)
GET    /api/export/catalog/{id}    - Exportar catálogo (JSON)
```

#### **1.10 Backups**
```
POST   /api/backups/create      - Crear backup manual
GET    /api/backups             - Listar backups
GET    /api/backups/{id}        - Descargar backup
POST   /api/backups/restore     - Restaurar desde backup
GET    /api/backups/schedule    - Ver configuración de backups
PUT    /api/backups/schedule    - Configurar backups automáticos
```

#### **1.11 Estadísticas**
```
GET    /api/stats/dashboard     - Dashboard general
GET    /api/stats/collections   - Stats de todas las colecciones
GET    /api/stats/value         - Valorización total
GET    /api/stats/categories    - Desglose por categorías
GET    /api/stats/timeline      - Timeline de adquisiciones
```

#### **1.12 Imágenes**
```
POST   /api/images/upload       - Upload de imagen
DELETE /api/images/{id}          - Eliminar imagen
GET    /api/images/{id}/thumbnail - Thumbnail
```

---

### **2. Servicios Backend**

#### **2.1 Backup Service**
- ✅ Backups automáticos programados (diario/semanal/mensual)
- ✅ Exportación a JSON (datos completos)
- ✅ Exportación a RAR/ZIP (datos + imágenes)
- ✅ Upload automático a Google Drive
- ✅ Upload automático a Dropbox
- ✅ Backups locales con rotación (mantener últimos N)
- ✅ Restauración desde backup

#### **2.2 Image Processing Service**
- ✅ Redimensionar imágenes automáticamente
- ✅ Generar thumbnails (150x150, 300x300)
- ✅ Optimización de tamaño (compresión)
- ✅ Conversión de formatos (HEIC → JPG)
- ✅ Watermarking (opcional)
- ✅ Detección de duplicados (hash de imagen)

#### **2.3 Catalog Importer Service**
- ✅ Importar desde JSON
- ✅ Importar desde CSV
- ✅ Importar desde API externa (IGDB, PriceCharting, Discogs)
- ✅ Validación de datos
- ✅ Merge con catálogos existentes
- ✅ Deduplicación automática

#### **2.4 Search Service**
- ✅ Full-text search con PostgreSQL
- ✅ Búsqueda por campos múltiples
- ✅ Filtros avanzados
- ✅ Ranking por relevancia
- ✅ Sugerencias de búsqueda
- ✅ Búsqueda fuzzy (typos)

#### **2.5 Notification Service (Futuro)**
- ✅ Notificaciones de wishlist (precio bajo)
- ✅ Alertas de stock bajo (accesorios)
- ✅ Recordatorios de valorización
- ✅ Notificaciones de backup

#### **2.6 Cloud Storage Service**
- ✅ Google Drive API integration
- ✅ Dropbox API integration
- ✅ AWS S3 integration (opcional)
- ✅ Sync bidireccional
- ✅ Gestión de permisos

---

### **3. Modelos de Datos (SQLAlchemy)**

- ✅ MainCategory
- ✅ SubCategory
- ✅ CategoryFieldSchema
- ✅ StandardComponent
- ✅ Supplier
- ✅ Catalog
- ✅ CatalogItem
- ✅ CatalogPriceHistory
- ✅ Collection
- ✅ CollectionItem
- ✅ ItemComponent
- ✅ ItemImage
- ✅ ItemTransaction
- ✅ WishlistItem
- ✅ WishlistSighting
- ✅ AccessoriesStock
- ✅ ItemAccessories

---

### **4. Schemas Pydantic (Validación)**

Para cada modelo, crear:
- ✅ `{Model}Base` - Campos base
- ✅ `{Model}Create` - Creación
- ✅ `{Model}Update` - Actualización
- ✅ `{Model}InDB` - Con ID y timestamps
- ✅ `{Model}Response` - Para respuesta API

Ejemplos:
```python
# CollectionCreate
class CollectionCreate(BaseModel):
    name: str
    collection_type: str
    theme: Optional[str]
    restricted_to_sub_category_id: Optional[UUID]

# CollectionResponse
class CollectionResponse(BaseModel):
    id: UUID
    name: str
    collection_type: str
    theme: Optional[str]
    total_items: int
    total_value: Decimal
    created_at: datetime
```

---

### **5. Base de Datos**

- ✅ PostgreSQL 14+
- ✅ 17 tablas principales
- ✅ Full-text search indexes
- ✅ Triggers automáticos (updated_at, stock, etc.)
- ✅ Vistas materializadas para stats
- ✅ Migraciones con Alembic

---

### **6. Seguridad**

- ✅ CORS configurado
- ✅ Rate limiting
- ✅ Validación de inputs (Pydantic)
- ✅ Sanitización de archivos subidos
- ✅ Autenticación JWT (futuro)
- ✅ HTTPS obligatorio en producción

---

## 🎨 FRONTEND - Funcionalidades

### **1. Páginas Principales**

#### **1.1 Home / Dashboard**
- ✅ Resumen de colecciones
- ✅ Estadísticas rápidas (items, valor total, ROI)
- ✅ Últimas adquisiciones
- ✅ Items destacados
- ✅ Gráficos de valorización
- ✅ Wishlist top priority
- ✅ Alertas (stock bajo, backups, etc.)

#### **1.2 Colecciones**
- ✅ Lista de todas las colecciones
- ✅ Filtros por tipo (single/multi/mixed)
- ✅ Ordenamiento (nombre, valor, items)
- ✅ Vista grid/lista
- ✅ Crear nueva colección
- ✅ Buscar colecciones

#### **1.3 Detalle de Colección**
- ✅ Información general
- ✅ Estadísticas (items, valor, completitud)
- ✅ Grid de items con filtros
- ✅ Vista por categoría (para multi-category)
- ✅ Gráficos de valorización
- ✅ Exportar colección
- ✅ Agregar item desde catálogo
- ✅ Agregar item manual

#### **1.4 Catálogo**
- ✅ Explorar catálogos disponibles
- ✅ Buscar items en catálogo
- ✅ Filtros avanzados (categoría, fabricante, año, etc.)
- ✅ Ver versiones relacionadas
- ✅ Ver historial de precios (gráfico)
- ✅ Agregar a colección
- ✅ Agregar a wishlist
- ✅ Crear nuevo item en catálogo
- ✅ Importar catálogo externo

#### **1.5 Detalle de Item**
- ✅ Información completa del catálogo
- ✅ Galería de imágenes
- ✅ Componentes (caja, manual, etc.)
- ✅ Estado y valorización
- ✅ Historial de transacciones
- ✅ Accesorios asignados
- ✅ Editar item
- ✅ Eliminar item
- ✅ Ver en catálogo
- ✅ Compartir item

#### **1.6 Wishlist**
- ✅ Lista de items deseados
- ✅ Filtros por prioridad, colección
- ✅ Vista grid/lista
- ✅ Agregar item desde catálogo
- ✅ Ver avistamientos por item
- ✅ Agregar avistamiento
- ✅ Marcar como adquirido

#### **1.7 Avistamientos (Wishlist)**
- ✅ Lista de todos los avistamientos
- ✅ Filtros por disponibilidad, precio
- ✅ Ver item original de wishlist
- ✅ Editar avistamiento
- ✅ Marcar como no disponible
- ✅ Marcar como comprado

#### **1.8 Proveedores**
- ✅ Lista de proveedores
- ✅ Crear/editar proveedor
- ✅ Ver compras por proveedor
- ✅ Estadísticas de proveedor
- ✅ Marcar favoritos

#### **1.9 Accesorios**
- ✅ Lista de stock de accesorios
- ✅ Crear/editar accesorio
- ✅ Ver items que usan el accesorio
- ✅ Alertas de stock bajo
- ✅ Historial de uso

#### **1.10 Estadísticas**
- ✅ Dashboard general
- ✅ Valorización total
- ✅ ROI por colección
- ✅ Gráficos de crecimiento
- ✅ Timeline de adquisiciones
- ✅ Desglose por categorías
- ✅ Top items más valiosos
- ✅ Análisis de gastos

#### **1.11 Importar/Exportar**
- ✅ Importar catálogo (JSON/CSV)
- ✅ Importar colección
- ✅ Exportar colección
- ✅ Exportar todo
- ✅ Preview antes de importar
- ✅ Validación de datos

#### **1.12 Configuración**
- ✅ Configurar backups automáticos
- ✅ Conectar Google Drive
- ✅ Conectar Dropbox
- ✅ Configurar notificaciones
- ✅ Preferencias de visualización
- ✅ Gestión de categorías custom

---

### **2. Componentes Reutilizables**

#### **2.1 Layout**
- ✅ Header con navegación
- ✅ Sidebar colapsable
- ✅ Footer
- ✅ Breadcrumbs
- ✅ Notificaciones toast

#### **2.2 Colecciones**
- ✅ CollectionCard - Card de colección
- ✅ CollectionForm - Formulario crear/editar
- ✅ CollectionList - Lista de colecciones
- ✅ CollectionStats - Estadísticas

#### **2.3 Items**
- ✅ ItemCard - Card de item con imagen
- ✅ ItemGrid - Grid de items
- ✅ ItemForm - Formulario crear/editar
- ✅ ItemDetail - Vista detallada
- ✅ ComponentsManager - Gestión de componentes
- ✅ PriceHistory - Gráfico de precios

#### **2.4 Catálogo**
- ✅ CatalogBrowser - Explorador de catálogo
- ✅ CatalogSearch - Búsqueda avanzada
- ✅ CatalogImporter - Importador
- ✅ VersionsViewer - Ver versiones relacionadas

#### **2.5 Wishlist**
- ✅ WishlistCard - Card de wishlist
- ✅ WishlistForm - Formulario
- ✅ SightingCard - Card de avistamiento
- ✅ SightingForm - Formulario avistamiento

#### **2.6 Imágenes**
- ✅ ImageUploader - Subir múltiples imágenes
- ✅ ImageGallery - Galería con zoom
- ✅ ImageEditor - Crop/rotate básico
- ✅ ImagePreview - Preview antes de subir

#### **2.7 Stats**
- ✅ ValueChart - Gráfico de valorización
- ✅ CategoryPieChart - Pie chart por categorías
- ✅ TimelineChart - Timeline de adquisiciones
- ✅ StatsCard - Card de estadística

#### **2.8 Forms**
- ✅ SearchBar - Barra de búsqueda
- ✅ FilterPanel - Panel de filtros
- ✅ DateRangePicker - Selector de rango
- ✅ MultiSelect - Selector múltiple
- ✅ AutoComplete - Autocompletado

#### **2.9 UI (shadcn/ui)**
- ✅ Button
- ✅ Card
- ✅ Dialog/Modal
- ✅ Dropdown
- ✅ Input
- ✅ Select
- ✅ Checkbox
- ✅ Radio
- ✅ Tabs
- ✅ Table
- ✅ Toast
- ✅ Tooltip
- ✅ Badge
- ✅ Avatar
- ✅ Progress
- ✅ Skeleton

---

### **3. Funcionalidades PWA**

#### **3.1 Offline Support**
- ✅ Service Worker para cache
- ✅ Sincronización en background
- ✅ Queue de acciones offline
- ✅ Indicador de estado de conexión
- ✅ Resolución de conflictos

#### **3.2 Instalación**
- ✅ Manifest.json
- ✅ Icons (192x192, 512x512)
- ✅ Prompt de instalación
- ✅ Splash screen

#### **3.3 Performance**
- ✅ Lazy loading de componentes
- ✅ Infinite scroll
- ✅ Image lazy loading
- ✅ Virtual scrolling (listas grandes)
- ✅ Code splitting

---

### **4. Estado y Data Fetching**

#### **4.1 React Query**
- ✅ Cache de queries
- ✅ Refetch automático
- ✅ Optimistic updates
- ✅ Infinite queries (paginación)
- ✅ Mutations

#### **4.2 Context API**
- ✅ AuthContext (futuro)
- ✅ ThemeContext (dark/light)
- ✅ SettingsContext

#### **4.3 LocalStorage**
- ✅ Preferencias de usuario
- ✅ Filtros guardados
- ✅ Vistas preferidas
- ✅ Queue de sync offline

---

### **5. Hooks Personalizados**

```javascript
useCollections()      // CRUD de colecciones
useCollection(id)     // Detalle de colección
useItems(filters)     // Items con filtros
useItem(id)          // Detalle de item
useCatalog(filters)  // Catálogo con filtros
useWishlist()        // Wishlist
useSuppliers()       // Proveedores
useAccessories()     // Accesorios
useStats()           // Estadísticas
useImageUpload()     // Upload de imágenes
useOfflineSync()     // Sincronización offline
useBackups()         // Gestión de backups
useImportExport()    // Import/Export
```

---

### **6. Rutas (React Router)**

```javascript
/                              - Home/Dashboard
/collections                   - Lista de colecciones
/collections/:id               - Detalle de colección
/collections/new               - Crear colección
/catalog                       - Explorar catálogo
/catalog/:id                   - Detalle catalog item
/items/:id                     - Detalle collection item
/wishlist                      - Wishlist
/wishlist/:id                  - Detalle wishlist item
/suppliers                     - Proveedores
/suppliers/:id                 - Detalle proveedor
/accessories                   - Accesorios
/stats                         - Estadísticas
/import                        - Importar
/export                        - Exportar
/settings                      - Configuración
/settings/backups              - Configuración backups
/settings/integrations         - Integraciones (Drive, Dropbox)
```

---

## 🐳 Deployment con Docker

### **docker-compose.yml**

```yaml
version: '3.8'

services:
  # PostgreSQL
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: hoard_db
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"
  
  # Backend (FastAPI)
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/hoard_db
      GOOGLE_DRIVE_ENABLED: ${GOOGLE_DRIVE_ENABLED:-false}
      DROPBOX_ENABLED: ${DROPBOX_ENABLED:-false}
    volumes:
      - ./uploads:/app/uploads
      - ./backups:/app/backups
    ports:
      - "8000:8000"
    depends_on:
      - db
  
  # Frontend (React)
  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### **Comandos**

```bash
# Iniciar todo
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Rebuild
docker-compose up -d --build

# Ejecutar migraciones
docker-compose exec backend alembic upgrade head

# Crear backup manual
docker-compose exec backend python -m utils.backup_service
```

---

## 🚀 Roadmap de Desarrollo

### **Fase 1: Fundamentos (MVP)**
**Objetivo:** Sistema funcional básico con colecciones single-category

**Backend:**
- Setup del proyecto (Docker, DB, estructura)
- Modelos SQLAlchemy + CRUD básico
- Endpoints REST principales
- Sistema de imágenes básico
- **Testing:** Tests unitarios de modelos y endpoints básicos

**Frontend:**
- Setup React + Vite + TailwindCSS
- Páginas principales (Home, Colecciones, Items)
- Componentes UI base
- Routing básico
- **Testing:** Tests de componentes y navegación

**Database:**
- Schema completo
- Migraciones Alembic
- Seed data inicial
- **Testing:** Tests de integridad referencial

**Accesibilidad:**
- Estructura semántica HTML
- ARIA labels básicos
- Navegación por teclado
- **Testing:** Tests automatizados de accesibilidad (axe-core)

---

### **Fase 2: Features Core**
**Objetivo:** Funcionalidades principales completas

**Backend:**
- Colecciones multi-category
- Wishlist completa con avistamientos
- Proveedores y suppliers
- Componentes de items
- Búsqueda avanzada (full-text)
- **Testing:** Tests de integración de workflows completos

**Frontend:**
- Detalle completo de colecciones
- Explorador de catálogo
- Sistema de filtros avanzados
- Wishlist con tracking
- Estadísticas básicas
- **Testing:** Tests E2E de flujos principales

**Accesibilidad:**
- Screen reader optimization
- Alto contraste / Dark mode
- Focus indicators mejorados
- Skip links
- **Testing:** Tests con lectores de pantalla (NVDA, JAWS)

**i18n:**
- Sistema de internacionalización configurado
- Idiomas iniciales: Español, Inglés
- Strings externalizados
- **Testing:** Tests de cobertura de traducciones

---

### **Fase 3: Features Avanzadas**
**Objetivo:** Completar funcionalidades premium

**Backend:**
- Historial de precios con gráficos
- Sistema de accesorios completo
- Import/Export (JSON, CSV)
- Backups automáticos programados
- APIs de catálogos externos
- **Testing:** Tests de importación/exportación y backups

**Frontend:**
- Gráficos de valorización
- Timeline de adquisiciones
- PWA offline support
- Sistema de notificaciones
- Gestión de accesorios
- **Testing:** Tests de PWA y offline mode

**Accesibilidad:**
- Reducción de movimiento (prefers-reduced-motion)
- Mensajes de estado (live regions)
- Tooltips accesibles
- **Testing:** Auditoría completa WCAG 2.1 AA

**i18n:**
- Portal de contribución de traducciones
- Interfaz para traductores comunitarios
- Más idiomas: Portugués, Francés, Alemán, Japonés
- **Testing:** Tests de RTL (Right-to-Left) para árabe/hebreo

---

### **Fase 4: Integraciones Cloud**
**Objetivo:** Conectividad con servicios externos

**Backend:**
- Google Drive API (backups)
- Dropbox API (backups)
- AWS S3 (opcional)
- Importadores de APIs externas (IGDB, PriceCharting, Discogs)
- **Testing:** Tests de integración con mocks de APIs

**Frontend:**
- Configuración de integraciones
- Sincronización visual
- Gestión de credenciales
- **Testing:** Tests de flujos OAuth

**Accesibilidad:**
- Formularios accesibles para configuración
- Feedback de progreso accesible
- **Testing:** Tests de accesibilidad en formularios complejos

---

### **Fase 5: Polish & Multi-usuario**
**Objetivo:** Refinamiento y preparación para producción

**Backend:**
- Sistema de autenticación JWT
- Multi-usuario con roles
- Permisos granulares
- API rate limiting
- Logs y monitoring
- **Testing:** Tests de seguridad (OWASP), tests de carga

**Frontend:**
- Optimización de performance
- Lazy loading completo
- Animaciones pulidas
- Onboarding mejorado
- Tour interactivo
- **Testing:** Tests de performance (Lighthouse), tests de UX

**Accesibilidad:**
- Auditoría externa profesional
- Certificación WCAG 2.1 AA (objetivo)
- Documentación de accesibilidad
- **Testing:** Tests con usuarios reales con discapacidades

**i18n:**
- Sistema de badges para traductores comunitarios
- Estadísticas de cobertura por idioma
- Integración con plataformas de traducción (Crowdin, Weblate)
- **Testing:** Tests de completitud de traducciones

**DevOps:**
- CI/CD completo (GitHub Actions)
- Deploy automatizado
- Documentación completa
- **Testing:** Tests de deploy, smoke tests en producción

---

## 📋 Principios de Testing

**Testing está integrado en TODAS las fases:**

### Testing Backend
- **Unitarios:** Pytest para modelos, servicios, utilidades
- **Integración:** Tests de endpoints con TestClient de FastAPI
- **Base de datos:** Tests con DB en memoria o contenedor temporal

### Testing Frontend
- **Componentes:** Vitest + Testing Library
- **E2E:** Playwright para flujos completos
- **Accesibilidad:** axe-core en todos los tests de componentes
- **Visual:** Percy/Chromatic para regression visual

### Testing de Accesibilidad
- **Automatizado:** axe-core, Pa11y, Lighthouse
- **Manual:** Navegación por teclado, lectores de pantalla
- **Con usuarios:** Tests con personas con discapacidades reales

### Testing de i18n
- **Cobertura:** Scripts que verifican strings sin traducir
- **Formato:** Tests de plurales, formatos de fecha/número
- **Contexto:** Review manual de traducciones en contexto

---

## ✅ Checklist de Features por Fase

### Fase 1: MVP
- [ ] Setup Docker completo
- [ ] Base de datos + migraciones
- [ ] CRUD básico de colecciones
- [ ] CRUD básico de items
- [ ] Upload de imágenes
- [ ] Navegación funcional
- [ ] i18n configurado (ES/EN)
- [ ] ARIA básico implementado
- [ ] Tests unitarios >70% coverage
- [ ] Tests E2E de flujos críticos

### Fase 2: Core Features
- [ ] Colecciones multi-category
- [ ] Wishlist completa
- [ ] Búsqueda avanzada
- [ ] Estadísticas básicas
- [ ] Dark mode accesible
- [ ] Navegación por teclado completa
- [ ] 3+ idiomas soportados
- [ ] Tests de integración completos
- [ ] Tests con screen readers

### Fase 3: Advanced
- [ ] Gráficos de valorización
- [ ] Import/Export funcional
- [ ] PWA instalable
- [ ] Offline mode
- [ ] Backups automáticos
- [ ] Reducción de movimiento
- [ ] 5+ idiomas soportados
- [ ] Tests de PWA
- [ ] Auditoría WCAG 2.1 AA

### Fase 4: Integraciones
- [ ] Google Drive conectado
- [ ] Dropbox conectado
- [ ] Importadores de APIs
- [ ] Portal de traducción activo
- [ ] Tests de APIs externas
- [ ] Tests de OAuth flows

### Fase 5: Production Ready
- [ ] Multi-usuario
- [ ] Autenticación segura
- [ ] Rate limiting
- [ ] CI/CD configurado
- [ ] Documentación completa
- [ ] Certificación WCAG (objetivo)
- [ ] 10+ idiomas soportados
- [ ] Community de traductores activa
- [ ] Tests de seguridad
- [ ] Tests de carga
- [ ] Lighthouse score >90

---

## 🛠️ Stack Tecnológico

### **Backend**
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- APScheduler
- Pillow
- google-api-python-client
- dropbox
- pytest

### **Frontend**
- React 18
- Vite
- React Router 6
- TanStack Query (React Query)
- TailwindCSS
- shadcn/ui
- Recharts
- Workbox (PWA)
- Axios
- **i18next** (internacionalización)
- **react-i18next**

### **Accesibilidad**
- **ARIA landmarks** y labels
- **axe-core** (testing automatizado)
- **Pa11y** (CI accessibility checks)
- **react-aria** (componentes accesibles)
- **focus-trap-react**
- Soporte para **screen readers** (NVDA, JAWS, VoiceOver)
- **Lighthouse** audits
- Cumplimiento **WCAG 2.1 AA**

### **Database**
- PostgreSQL 14+

### **Infrastructure**
- Docker
- Docker Compose
- Nginx (reverse proxy)

### **Testing**
- **Backend:** pytest, pytest-cov
- **Frontend:** Vitest, Testing Library, Playwright
- **Accesibilidad:** axe-core, Pa11y
- **E2E:** Playwright
- **Visual:** Percy/Chromatic (opcional)

---

## 📖 Documentación Adicional

- **[Database Schema](./DATABASE_SCHEMA.md)** - Documentación de la BD
- **[API Documentation](./API_DOCS.md)** - Documentación de endpoints
- **[Development Guide](./DEVELOPMENT.md)** - Guía de desarrollo
- **[Deployment Guide](./DEPLOYMENT.md)** - Guía de deployment

---

## 🤝 Contribuciones

Este es un proyecto open source. Las contribuciones son bienvenidas.

## 📄 Licencia

MIT License - Úsalo como quieras para tu proyecto personal.
