-- ============================================
-- MIGRATION: v1 to v2
-- Actualiza el schema para soportar colecciones multi-categoría
-- ============================================

-- ADVERTENCIA: Este script modifica la estructura de la tabla collections
-- Asegúrate de hacer un backup antes de ejecutar

BEGIN;

-- ============================================
-- 1. AGREGAR NUEVAS COLUMNAS A collections
-- ============================================

-- Agregar collection_type
ALTER TABLE collections 
ADD COLUMN collection_type VARCHAR(50) DEFAULT 'single_category' 
CHECK (collection_type IN ('single_category', 'multi_category', 'mixed'));

COMMENT ON COLUMN collections.collection_type IS 'single_category=una sola subcategoría, multi_category=múltiples bajo un tema, mixed=sin restricción';

-- Agregar theme
ALTER TABLE collections 
ADD COLUMN theme VARCHAR(100);

ALTER TABLE collections 
ADD COLUMN theme_description TEXT;

COMMENT ON COLUMN collections.theme IS 'Tema/franquicia para colecciones multi-category (ej: The Legend of Zelda, Star Wars)';

-- Renombrar catalog_id a restricted_to_sub_category_id
-- Primero, obtener la sub_category_id del catálogo actual
ALTER TABLE collections 
ADD COLUMN restricted_to_sub_category_id UUID;

-- Poblar el nuevo campo basado en catalog_id existente
UPDATE collections c
SET restricted_to_sub_category_id = cat.sub_category_id
FROM catalogs cat
WHERE c.catalog_id = cat.id;

-- Agregar constraint
ALTER TABLE collections
ADD CONSTRAINT check_single_category_restriction CHECK (
    (collection_type = 'single_category' AND restricted_to_sub_category_id IS NOT NULL) OR
    (collection_type != 'single_category')
);

-- Agregar FK constraint
ALTER TABLE collections
ADD CONSTRAINT fk_collections_restricted_sub 
FOREIGN KEY (restricted_to_sub_category_id) 
REFERENCES sub_categories(id) ON DELETE RESTRICT;

-- Eliminar el campo catalog_id antiguo
ALTER TABLE collections DROP CONSTRAINT IF EXISTS collections_catalog_id_fkey;
ALTER TABLE collections DROP COLUMN catalog_id;

-- ============================================
-- 2. ACTUALIZAR ÍNDICES
-- ============================================

CREATE INDEX idx_collections_type ON collections(collection_type);
CREATE INDEX idx_collections_theme ON collections(theme);
CREATE INDEX idx_collections_restricted_sub ON collections(restricted_to_sub_category_id);

-- Eliminar índice antiguo si existe
DROP INDEX IF EXISTS idx_collections_catalog;

-- ============================================
-- 3. ACTUALIZAR VISTAS
-- ============================================

-- Drop vistas antiguas
DROP VIEW IF EXISTS v_collection_items_full CASCADE;
DROP VIEW IF EXISTS v_wishlist_with_avg_price CASCADE;
DROP VIEW IF EXISTS v_collection_stats CASCADE;

-- Recrear vistas con nueva estructura

-- Vista de items con información completa del catálogo
CREATE OR REPLACE VIEW v_collection_items_full AS
SELECT 
    ci.*,
    cat.title as catalog_title,
    cat.language,
    cat.region,
    cat.version_name,
    cat.variation,
    cat.cover_image_url,
    cat.rarity,
    c.name as collection_name,
    c.collection_type,
    c.theme as collection_theme,
    cat_catalog.name as catalog_name,
    sc.name as subcategory_name,
    mc.name as main_category_name,
    s.name as supplier_name
FROM collection_items ci
JOIN catalog_items cat ON ci.catalog_item_id = cat.id
JOIN collections c ON ci.collection_id = c.id
JOIN catalogs cat_catalog ON cat.catalog_id = cat_catalog.id
JOIN sub_categories sc ON cat_catalog.sub_category_id = sc.id
JOIN main_categories mc ON sc.main_category_id = mc.id
LEFT JOIN suppliers s ON ci.supplier_id = s.id;

COMMENT ON VIEW v_collection_items_full IS 'Vista completa de items con toda la información relacionada';

-- NUEVA VISTA: Items agrupados por categoría dentro de colecciones multi-category
CREATE OR REPLACE VIEW v_collection_items_by_category AS
SELECT 
    c.id as collection_id,
    c.name as collection_name,
    c.collection_type,
    c.theme,
    mc.id as main_category_id,
    mc.name as main_category,
    sc.id as sub_category_id,
    sc.name as sub_category,
    COUNT(ci.id) as items_count,
    SUM(ci.purchase_price) as total_invested,
    SUM(ci.current_market_value) as total_current_value,
    SUM(ci.current_market_value) - SUM(ci.purchase_price) as value_gain
FROM collections c
LEFT JOIN collection_items ci ON c.id = ci.collection_id
LEFT JOIN catalog_items cat ON ci.catalog_item_id = cat.id
LEFT JOIN catalogs catlog ON cat.catalog_id = catlog.id
LEFT JOIN sub_categories sc ON catlog.sub_category_id = sc.id
LEFT JOIN main_categories mc ON sc.main_category_id = mc.id
GROUP BY c.id, mc.id, sc.id
ORDER BY c.name, mc.name, sc.name;

COMMENT ON VIEW v_collection_items_by_category IS 'Desagregación de items por categoría en colecciones multi-category';

-- Vista de wishlist con precios promedio
CREATE OR REPLACE VIEW v_wishlist_with_avg_price AS
SELECT 
    wi.*,
    cat.title as item_title,
    cat.language,
    cat.region,
    cat.variation,
    c.name as collection_name,
    c.theme as collection_theme,
    AVG(ws.price) as avg_sighting_price,
    MIN(ws.price) as min_sighting_price,
    MAX(ws.price) as max_sighting_price,
    COUNT(ws.id) as total_sightings,
    COUNT(CASE WHEN ws.is_available THEN 1 END) as available_sightings
FROM wishlist_items wi
JOIN catalog_items cat ON wi.catalog_item_id = cat.id
JOIN collections c ON wi.collection_id = c.id
LEFT JOIN wishlist_sightings ws ON wi.id = ws.wishlist_item_id
WHERE wi.is_active = true AND wi.is_acquired = false
GROUP BY wi.id, cat.id, c.id;

COMMENT ON VIEW v_wishlist_with_avg_price IS 'Wishlist con estadísticas de precios de avistamientos';

-- Vista de estadísticas por colección
CREATE OR REPLACE VIEW v_collection_stats AS
SELECT 
    c.id,
    c.name,
    c.collection_type,
    c.theme,
    c.restricted_to_sub_category_id,
    sc.name as restricted_subcategory_name,
    COUNT(ci.id) as total_items,
    COUNT(DISTINCT cat_catalog.sub_category_id) as different_categories_count,
    SUM(ci.purchase_price) as total_invested,
    SUM(ci.current_market_value) as current_value,
    SUM(ci.current_market_value) - SUM(ci.purchase_price) as value_gain,
    CASE 
        WHEN SUM(ci.purchase_price) > 0 
        THEN ((SUM(ci.current_market_value) - SUM(ci.purchase_price)) / SUM(ci.purchase_price) * 100)
        ELSE 0 
    END as roi_percentage,
    COUNT(CASE WHEN ci.is_complete THEN 1 END) as complete_items,
    COUNT(CASE WHEN ci.is_graded THEN 1 END) as graded_items
FROM collections c
LEFT JOIN collection_items ci ON c.id = ci.collection_id
LEFT JOIN catalog_items cat ON ci.catalog_item_id = cat.id
LEFT JOIN catalogs cat_catalog ON cat.catalog_id = cat_catalog.id
LEFT JOIN sub_categories sc ON c.restricted_to_sub_category_id = sc.id
GROUP BY c.id, sc.name;

COMMENT ON VIEW v_collection_stats IS 'Estadísticas resumidas por colección';

COMMIT;

-- ============================================
-- VERIFICACIÓN POST-MIGRACIÓN
-- ============================================

-- Verificar que todas las colecciones tienen el tipo correcto
SELECT 
    id, 
    name, 
    collection_type, 
    restricted_to_sub_category_id,
    theme
FROM collections
ORDER BY collection_type, name;

-- Verificar integridad de datos
SELECT 
    collection_type,
    COUNT(*) as count,
    COUNT(restricted_to_sub_category_id) as with_restriction,
    COUNT(theme) as with_theme
FROM collections
GROUP BY collection_type;

-- ============================================
-- NOTAS
-- ============================================

-- Después de esta migración:
-- 1. Todas las colecciones existentes quedarán como 'single_category'
-- 2. El campo 'restricted_to_sub_category_id' apuntará a la subcategoría del catálogo original
-- 3. Ahora puedes crear nuevas colecciones 'multi_category' con un theme
-- 4. Las colecciones 'multi_category' NO tienen restricted_to_sub_category_id
-- 5. Los items en collection_items siguen funcionando igual, ya que referencian catalog_item_id directamente
