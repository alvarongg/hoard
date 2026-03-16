-- ============================================
-- MIGRATION: Agregar manufacturer, publisher, developer
-- Agrega campos para fabricante/editorial/desarrollador a catalog_items
-- ============================================

-- ADVERTENCIA: Este script modifica catalog_items
-- Asegúrate de hacer un backup antes de ejecutar

BEGIN;

-- ============================================
-- 1. AGREGAR NUEVAS COLUMNAS A catalog_items
-- ============================================

-- Manufacturer/Fabricante (empresa que fabrica el producto)
-- Ejemplos: Mattel, Hasbro, Nintendo, Sony, Bandai
ALTER TABLE catalog_items 
ADD COLUMN manufacturer VARCHAR(200);

COMMENT ON COLUMN catalog_items.manufacturer IS 'Fabricante del producto (Mattel, Hasbro, Nintendo, Sony, Bandai, etc.)';

-- Publisher/Distribuidor/Editorial
-- Para videojuegos: quien distribuyó el juego (puede diferir del developer)
-- Para libros: editorial (Minotauro, Planeta, etc.)
-- Para música: sello discográfico (Sony Music, Warner, etc.)
-- Para TCG: empresa que publica (Wizards of the Coast, Pokemon Company, etc.)
ALTER TABLE catalog_items 
ADD COLUMN publisher VARCHAR(200);

COMMENT ON COLUMN catalog_items.publisher IS 'Distribuidor/Editorial/Sello (Nintendo, Minotauro, Sony Music, WotC, etc.)';

-- Developer/Desarrollador (específico para videojuegos)
-- Quien desarrolló el juego (puede ser diferente al publisher)
-- Ejemplo: Developer=Rare, Publisher=Nintendo
ALTER TABLE catalog_items 
ADD COLUMN developer VARCHAR(200);

COMMENT ON COLUMN catalog_items.developer IS 'Desarrollador (principalmente para videojuegos - Rare, HAL Laboratory, etc.)';

-- Brand/Marca (opcional, para productos con sub-marcas)
-- Ejemplos: Hot Wheels (sub-marca de Mattel), Funko Pop (sub-marca de Funko)
ALTER TABLE catalog_items 
ADD COLUMN brand VARCHAR(200);

COMMENT ON COLUMN catalog_items.brand IS 'Marca o línea de producto (Hot Wheels, Funko Pop, Transformers, etc.)';

-- ============================================
-- 2. CREAR ÍNDICES PARA BÚSQUEDA
-- ============================================

CREATE INDEX idx_catalog_items_manufacturer ON catalog_items(manufacturer);
CREATE INDEX idx_catalog_items_publisher ON catalog_items(publisher);
CREATE INDEX idx_catalog_items_developer ON catalog_items(developer);
CREATE INDEX idx_catalog_items_brand ON catalog_items(brand);

-- Índice compuesto para búsquedas comunes en videojuegos
CREATE INDEX idx_catalog_items_publisher_developer ON catalog_items(publisher, developer);

-- ============================================
-- 3. ACTUALIZAR SEARCH VECTOR
-- ============================================

-- Actualizar la función de search vector para incluir los nuevos campos
DROP TRIGGER IF EXISTS catalog_items_search_vector_trigger ON catalog_items;

CREATE OR REPLACE FUNCTION catalog_items_search_vector_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('spanish', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.subtitle, '')), 'B') ||
        setweight(to_tsvector('spanish', COALESCE(array_to_string(NEW.alternate_titles, ' '), '')), 'B') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.description, '')), 'C') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.variation, '')), 'B') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.manufacturer, '')), 'B') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.publisher, '')), 'B') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.developer, '')), 'C') ||
        setweight(to_tsvector('spanish', COALESCE(NEW.brand, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.subtitle, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.alternate_titles, ' '), '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.variation, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.manufacturer, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.publisher, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.developer, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.brand, '')), 'C');
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER catalog_items_search_vector_trigger
    BEFORE INSERT OR UPDATE ON catalog_items
    FOR EACH ROW EXECUTE FUNCTION catalog_items_search_vector_update();

-- ============================================
-- 4. MIGRAR DATOS EXISTENTES (si aplica)
-- ============================================

-- Si tenías datos en custom_fields con estos valores, puedes migrarlos:

-- Para videojuegos: extraer publisher y developer de custom_fields
UPDATE catalog_items
SET 
    publisher = custom_fields->>'publisher',
    developer = custom_fields->>'developer'
WHERE custom_fields ? 'publisher' OR custom_fields ? 'developer';

-- Para otros: extraer manufacturer si existe
UPDATE catalog_items
SET manufacturer = custom_fields->>'manufacturer'
WHERE custom_fields ? 'manufacturer';

-- ============================================
-- 5. ACTUALIZAR VISTAS (si es necesario)
-- ============================================

-- Recrear vista v_collection_items_full para incluir nuevos campos
DROP VIEW IF EXISTS v_collection_items_full CASCADE;

CREATE OR REPLACE VIEW v_collection_items_full AS
SELECT 
    ci.*,
    cat.title as catalog_title,
    cat.language,
    cat.region,
    cat.version_name,
    cat.variation,
    cat.manufacturer,
    cat.publisher,
    cat.developer,
    cat.brand,
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

COMMIT;

-- ============================================
-- VERIFICACIÓN POST-MIGRACIÓN
-- ============================================

-- Verificar que los campos se agregaron correctamente
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'catalog_items' 
    AND column_name IN ('manufacturer', 'publisher', 'developer', 'brand')
ORDER BY column_name;

-- Verificar índices creados
SELECT 
    indexname, 
    indexdef
FROM pg_indexes
WHERE tablename = 'catalog_items' 
    AND indexname LIKE '%manufacturer%' 
    OR indexname LIKE '%publisher%' 
    OR indexname LIKE '%developer%'
    OR indexname LIKE '%brand%';

-- ============================================
-- EJEMPLOS DE USO
-- ============================================

-- Ejemplo 1: Videojuego con developer y publisher diferentes
-- UPDATE catalog_items SET
--     manufacturer = 'Nintendo',
--     publisher = 'Nintendo',
--     developer = 'Rare'
-- WHERE title = 'Donkey Kong 64';

-- Ejemplo 2: Libro
-- UPDATE catalog_items SET
--     publisher = 'Minotauro',
--     manufacturer = 'Editorial Planeta'
-- WHERE title = 'El Señor de los Anillos';

-- Ejemplo 3: Juguete
-- UPDATE catalog_items SET
--     manufacturer = 'Mattel',
--     brand = 'Hot Wheels'
-- WHERE title LIKE 'Hot Wheels%';

-- Ejemplo 4: TCG
-- UPDATE catalog_items SET
--     manufacturer = 'The Pokemon Company',
--     publisher = 'Wizards of the Coast'
-- WHERE title LIKE 'Pokemon%';

-- ============================================
-- QUERIES ÚTILES
-- ============================================

-- Buscar todos los juegos de un desarrollador
-- SELECT title, publisher, developer FROM catalog_items 
-- WHERE developer = 'Rare';

-- Buscar todos los productos de un fabricante
-- SELECT title, manufacturer, brand FROM catalog_items 
-- WHERE manufacturer = 'Nintendo';

-- Buscar libros de una editorial
-- SELECT title, publisher FROM catalog_items 
-- WHERE publisher = 'Minotauro';
