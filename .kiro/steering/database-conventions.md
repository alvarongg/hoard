---
inclusion: fileMatch
fileMatchPattern: "**/*.sql,**/models/**,**/alembic/**,**/migrations/**"
---

# Database Conventions

## PostgreSQL

### Naming
- Tablas: `snake_case` plural (ej: `collection_items`, `wishlist_sightings`)
- Columnas: `snake_case` (ej: `created_at`, `catalog_item_id`)
- Índices: `idx_{table}_{column}` (ej: `idx_collections_type`)
- Constraints: `{type}_{table}_{description}` (ej: `check_single_category_restriction`)
- Foreign keys: `{referenced_table_singular}_id` (ej: `collection_id`, `supplier_id`)

### Estándares
- UUID como primary key (uuid_generate_v4)
- `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` en todas las tablas
- `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` con trigger automático en tablas mutables
- Soft delete cuando sea apropiado (`is_active BOOLEAN DEFAULT true`)
- JSONB para campos dinámicos/flexibles (custom_fields)
- TEXT[] para arrays de strings (tags, alternate_titles)
- DECIMAL(10,2) para valores monetarios

### Migraciones (Alembic)
- Una migración por cambio lógico
- Migraciones reversibles siempre que sea posible (upgrade + downgrade)
- Naming: `{revision}_{description}.py`
- NO modificar migraciones ya aplicadas, crear nuevas
- Testear migraciones en ambas direcciones antes de commitear

### Queries
- Usar SQLAlchemy ORM para queries estándar
- SQL raw solo para queries complejas de performance (full-text search, aggregations)
- Paginación obligatoria en listados (skip/limit o cursor-based)
- Índices para columnas usadas en WHERE, JOIN, ORDER BY frecuentes
- EXPLAIN ANALYZE para queries que toquen tablas grandes

### Schema Existente
El schema v2 está definido en `database/schema.sql` con 17 tablas.
Los modelos SQLAlchemy DEBEN reflejar exactamente este schema.
Cualquier cambio al schema requiere una migración Alembic.

Referencia: #[[file:database/schema.sql]]
