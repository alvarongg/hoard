-- ============================================
-- COLLECTION MANAGER - Seed Data v2
-- Incluye ejemplos de colecciones multi-categoría
-- ============================================

-- ============================================
-- 1. CATEGORÍAS PRINCIPALES
-- ============================================
INSERT INTO main_categories (name, slug, description, icon, sort_order) VALUES
    ('Videojuegos', 'videogames', 'Consolas, juegos y periféricos', '🎮', 1),
    ('Música', 'music', 'Vinilos, CDs, cassettes', '🎵', 2),
    ('Libros', 'books', 'Literatura, cómics, manga', '📚', 3),
    ('TCG', 'trading-card-games', 'Trading Card Games', '🃏', 4),
    ('Juguetes', 'toys', 'Figuras de acción, coleccionables', '🧸', 5),
    ('Anime/Manga', 'anime-manga', 'Celdas de animación, merchandise', '🎌', 6);

-- ============================================
-- 2. SUB-CATEGORÍAS
-- ============================================

-- Videojuegos
INSERT INTO sub_categories (main_category_id, name, slug, description, sort_order) 
SELECT id, 'Consolas', 'consoles', 'Consolas de videojuegos', 1 FROM main_categories WHERE slug = 'videogames'
UNION ALL
SELECT id, 'Juegos', 'games', 'Juegos de videojuegos', 2 FROM main_categories WHERE slug = 'videogames'
UNION ALL
SELECT id, 'Periféricos', 'peripherals', 'Controles, accesorios, etc.', 3 FROM main_categories WHERE slug = 'videogames';

-- Música
INSERT INTO sub_categories (main_category_id, name, slug, description, sort_order)
SELECT id, 'Vinilos', 'vinyl', 'Discos de vinilo', 1 FROM main_categories WHERE slug = 'music'
UNION ALL
SELECT id, 'CDs', 'cds', 'Compact Discs', 2 FROM main_categories WHERE slug = 'music'
UNION ALL
SELECT id, 'Cassettes', 'cassettes', 'Cintas de cassette', 3 FROM main_categories WHERE slug = 'music';

-- Libros
INSERT INTO sub_categories (main_category_id, name, slug, description, sort_order)
SELECT id, 'Tolkien', 'tolkien', 'Obras de J.R.R. Tolkien', 1 FROM main_categories WHERE slug = 'books'
UNION ALL
SELECT id, 'Art Books', 'art-books', 'Libros de arte y diseño', 2 FROM main_categories WHERE slug = 'books'
UNION ALL
SELECT id, 'Fantasía', 'fantasy', 'Literatura fantástica', 3 FROM main_categories WHERE slug = 'books';

-- TCG
INSERT INTO sub_categories (main_category_id, name, slug, description, sort_order)
SELECT id, 'Pokemon', 'pokemon', 'Pokemon Trading Card Game', 1 FROM main_categories WHERE slug = 'trading-card-games'
UNION ALL
SELECT id, 'Magic: The Gathering', 'mtg', 'Magic: The Gathering TCG', 2 FROM main_categories WHERE slug = 'trading-card-games';

-- Juguetes
INSERT INTO sub_categories (main_category_id, name, slug, description, sort_order)
SELECT id, 'Figuras de Acción', 'action-figures', 'Figuras articuladas', 1 FROM main_categories WHERE slug = 'toys'
UNION ALL
SELECT id, 'Amiibo', 'amiibo', 'Figuras Nintendo Amiibo', 2 FROM main_categories WHERE slug = 'toys';

-- ============================================
-- 3. ESQUEMAS DE CAMPOS
-- ============================================

INSERT INTO category_field_schemas (sub_category_id, field_name, field_label, field_type, field_options, is_required, is_searchable, sort_order)
SELECT 
    sc.id, 'platform', 'Plataforma', 'select',
    '{"values": ["NES", "SNES", "Nintendo 64", "GameCube", "Wii", "Switch", "Game Boy", "PlayStation", "PlayStation 2", "Sega Genesis"]}'::jsonb,
    true, true, 1
FROM sub_categories sc
JOIN main_categories mc ON sc.main_category_id = mc.id
WHERE mc.slug = 'videogames' AND sc.slug = 'games';

-- ============================================
-- 4. COMPONENTES ESTÁNDAR
-- ============================================

INSERT INTO standard_components (sub_category_id, component_name, component_type, sort_order)
SELECT sc.id, 'Cartucho', 'required', 1
FROM sub_categories sc WHERE sc.slug = 'games'
UNION ALL
SELECT sc.id, 'Caja', 'common', 2
FROM sub_categories sc WHERE sc.slug = 'games'
UNION ALL
SELECT sc.id, 'Manual', 'common', 3
FROM sub_categories sc WHERE sc.slug = 'games';

-- ============================================
-- 5. PROVEEDORES
-- ============================================

INSERT INTO suppliers (name, type, country, city, website, is_favorite) VALUES
    ('MercadoLibre', 'marketplace', 'AR', 'Online', 'https://www.mercadolibre.com.ar', true),
    ('eBay', 'marketplace', 'US', 'Online', 'https://www.ebay.com', true),
    ('Retro Game Store Buenos Aires', 'physical_store', 'AR', 'Buenos Aires', null, true);

-- ============================================
-- 6. CATÁLOGOS
-- ============================================

-- Catálogo de juegos N64
INSERT INTO catalogs (sub_category_id, name, description, source_type, is_official)
SELECT id, 'Nintendo 64 - Librería Completa', 'Todos los juegos de N64', 'import', true
FROM sub_categories WHERE slug = 'games';

-- Catálogo de juegos NES
INSERT INTO catalogs (sub_category_id, name, description, source_type, is_official)
SELECT id, 'NES/Famicom - Librería Completa', 'Todos los juegos de NES', 'import', true
FROM sub_categories WHERE slug = 'games';

-- Catálogo de vinilos
INSERT INTO catalogs (sub_category_id, name, description, source_type, is_official)
SELECT id, 'Soundtracks de Videojuegos', 'OSTs oficiales en vinilo', 'manual', true
FROM sub_categories WHERE slug = 'vinyl';

-- Catálogo de art books
INSERT INTO catalogs (sub_category_id, name, description, source_type, is_official)
SELECT id, 'Art Books de Videojuegos', 'Libros de arte oficiales', 'manual', true
FROM sub_categories WHERE slug = 'art-books';

-- Catálogo de amiibo
INSERT INTO catalogs (sub_category_id, name, description, source_type, is_official)
SELECT id, 'Nintendo Amiibo', 'Figuras Amiibo oficiales', 'import', true
FROM sub_categories WHERE slug = 'amiibo';

-- ============================================
-- 7. ITEMS DEL CATÁLOGO
-- ============================================

-- Zelda: Ocarina of Time (juego N64)
DO $$
DECLARE
    catalog_n64_id UUID;
    related_group UUID := uuid_generate_v4();
BEGIN
    SELECT id INTO catalog_n64_id FROM catalogs WHERE name = 'Nintendo 64 - Librería Completa';
    
    INSERT INTO catalog_items (
        catalog_id, title, upc, language, region, version_name, variation,
        related_items_group, description, release_date, 
        manufacturer, publisher, developer,
        custom_fields, rarity
    ) VALUES (
        catalog_n64_id,
        'The Legend of Zelda: Ocarina of Time',
        '045496870027',
        'english', ARRAY['en'], 'NTSC', 'USA v1.2',
        'Gold Cartridge',
        related_group,
        'Collector edition with gold cartridge.',
        '1998-12-10',
        'Nintendo',
        'Nintendo',
        'Nintendo EAD',
        '{"platform": "Nintendo 64", "genre": ["Action", "Adventure"]}'::jsonb,
        'ultra_rare'
    );
END $$;

-- Zelda: Ocarina of Time (OST vinilo)
DO $$
DECLARE
    catalog_vinyl_id UUID;
    zelda_related_group UUID;
BEGIN
    SELECT id INTO catalog_vinyl_id FROM catalogs WHERE name = 'Soundtracks de Videojuegos';
    
    -- Usar un nuevo related_items_group para productos Zelda cross-category
    SELECT uuid_generate_v4() INTO zelda_related_group;
    
    INSERT INTO catalog_items (
        catalog_id, title, language, region, version_name,
        related_items_group, description, release_date, 
        manufacturer, publisher,
        custom_fields, rarity
    ) VALUES (
        catalog_vinyl_id,
        'The Legend of Zelda: Ocarina of Time - Original Soundtrack',
        'multi-language', ARRAY['en', 'ja'], 'Multi-region', '2LP Vinyl Edition',
        zelda_related_group,
        'Official soundtrack on double vinyl.',
        '2016-12-21',
        'Sony Music',
        'Sony Music',
        '{"label": "Sony Music", "pressing": "180g", "rpm": "33"}'::jsonb,
        'rare'
    );
END $$;

-- Zelda: Art Book
DO $$
DECLARE
    catalog_artbook_id UUID;
    zelda_related_group UUID;
BEGIN
    SELECT id INTO catalog_artbook_id FROM catalogs WHERE name = 'Art Books de Videojuegos';
    
    SELECT uuid_generate_v4() INTO zelda_related_group;
    
    INSERT INTO catalog_items (
        catalog_id, title, isbn, language, region, version_name,
        related_items_group, description, release_date, 
        manufacturer, publisher,
        custom_fields, rarity
    ) VALUES (
        catalog_artbook_id,
        'The Legend of Zelda: Hyrule Historia',
        '978-1616550417',
        'english', ARRAY['en'], 'USA', 'English Edition',
        zelda_related_group,
        'Official art book and history of the Zelda series.',
        '2013-01-29',
        'Dark Horse Comics',
        'Dark Horse Books',
        '{"pages": 274}'::jsonb,
        'uncommon'
    );
END $$;

-- Link Amiibo
DO $$
DECLARE
    catalog_amiibo_id UUID;
    zelda_related_group UUID;
BEGIN
    SELECT id INTO catalog_amiibo_id FROM catalogs WHERE name = 'Nintendo Amiibo';
    
    SELECT uuid_generate_v4() INTO zelda_related_group;
    
    INSERT INTO catalog_items (
        catalog_id, title, upc, language, region, version_name, variation,
        related_items_group, description, release_date, 
        manufacturer, publisher, brand,
        custom_fields, rarity
    ) VALUES (
        catalog_amiibo_id,
        'Link (The Legend of Zelda)',
        '045496891893',
        'multi-language', ARRAY['en', 'es', 'fr'], 'Multi-region', 'Super Smash Bros. Series',
        'Standard',
        zelda_related_group,
        'Link amiibo figure from Super Smash Bros. series.',
        '2014-11-28',
        'Nintendo',
        'Nintendo',
        'Amiibo',
        '{"series": "Super Smash Bros.", "number": "03", "compatibility": ["Switch", "Wii U", "3DS"]}'::jsonb,
        'common'
    );
END $$;

-- ============================================
-- 8. COLECCIONES
-- ============================================

-- Colección SINGLE CATEGORY: Solo juegos N64
INSERT INTO collections (
    name, description, collection_type, restricted_to_sub_category_id,
    goal_description, goal_items_count
)
SELECT 
    'Mi Colección Nintendo 64',
    'Juegos completos de Nintendo 64',
    'single_category',
    sc.id,
    'Completar todos los first-party de Nintendo',
    25
FROM sub_categories sc
WHERE sc.slug = 'games';

-- Colección MULTI-CATEGORY: Todo relacionado con Zelda
INSERT INTO collections (
    name, description, collection_type, theme, theme_description,
    goal_description
)
VALUES (
    'The Legend of Zelda - Colección Completa',
    'Todo lo relacionado con The Legend of Zelda: juegos, música, libros, figuras',
    'multi_category',
    'The Legend of Zelda',
    'Colección temática de la franquicia Zelda abarcando múltiples categorías',
    'Reunir todos los productos oficiales de Zelda en todas las categorías'
);

-- Colección MIXED: Sin restricciones
INSERT INTO collections (
    name, description, collection_type,
    goal_description
)
VALUES (
    'Mis Favoritos de Infancia',
    'Productos variados que me recuerdan a mi infancia',
    'mixed',
    'Coleccionar items nostálgicos sin restricción de categoría'
);

-- ============================================
-- 9. ITEMS EN COLECCIONES
-- ============================================

-- Agregar Zelda OOT (juego) a la colección N64
DO $$
DECLARE
    collection_n64_id UUID;
    catalog_zelda_game UUID;
    item_id UUID;
BEGIN
    SELECT id INTO collection_n64_id FROM collections WHERE name = 'Mi Colección Nintendo 64';
    SELECT id INTO catalog_zelda_game FROM catalog_items 
        WHERE title LIKE '%Ocarina of Time%' AND variation = 'Gold Cartridge';
    
    INSERT INTO collection_items (
        collection_id, catalog_item_id, condition, is_complete,
        storage_location, purchase_price, purchase_date, current_market_value
    ) VALUES (
        collection_n64_id, catalog_zelda_game,
        'excellent', true,
        'Estante A - Fila 2', 85.00, '2023-06-15', 120.00
    ) RETURNING id INTO item_id;
    
    -- Componentes
    INSERT INTO item_components (collection_item_id, component_name, component_type, is_present, condition)
    VALUES
        (item_id, 'Cartucho', 'required', true, 'excellent'),
        (item_id, 'Caja', 'common', true, 'good'),
        (item_id, 'Manual', 'common', true, 'excellent');
END $$;

-- Agregar items de ZELDA a la colección multi-category
DO $$
DECLARE
    collection_zelda_id UUID;
    catalog_zelda_game UUID;
    catalog_zelda_ost UUID;
    catalog_zelda_book UUID;
    catalog_zelda_amiibo UUID;
    item_game UUID;
    item_ost UUID;
    item_book UUID;
    item_amiibo UUID;
BEGIN
    SELECT id INTO collection_zelda_id FROM collections WHERE theme = 'The Legend of Zelda';
    
    -- Juego
    SELECT id INTO catalog_zelda_game FROM catalog_items 
        WHERE title LIKE '%Ocarina of Time%' AND variation = 'Gold Cartridge';
    
    -- OST
    SELECT id INTO catalog_zelda_ost FROM catalog_items 
        WHERE title LIKE '%Ocarina of Time - Original Soundtrack%';
    
    -- Art Book
    SELECT id INTO catalog_zelda_book FROM catalog_items 
        WHERE title LIKE '%Hyrule Historia%';
    
    -- Amiibo
    SELECT id INTO catalog_zelda_amiibo FROM catalog_items 
        WHERE title LIKE 'Link (The Legend of Zelda)%';
    
    -- Agregar el juego (puede ser el mismo item físico que en la otra colección)
    INSERT INTO collection_items (
        collection_id, catalog_item_id, condition, is_complete,
        purchase_price, purchase_date, current_market_value, notes
    ) VALUES (
        collection_zelda_id, catalog_zelda_game,
        'excellent', true,
        85.00, '2023-06-15', 120.00,
        'Pieza central de mi colección Zelda'
    ) RETURNING id INTO item_game;
    
    -- Agregar el OST
    INSERT INTO collection_items (
        collection_id, catalog_item_id, condition, is_complete,
        purchase_price, purchase_date, current_market_value, notes
    ) VALUES (
        collection_zelda_id, catalog_zelda_ost,
        'mint', true,
        45.00, '2024-01-10', 65.00,
        'OST sellado, nunca reproducido'
    ) RETURNING id INTO item_ost;
    
    -- Agregar el Art Book
    INSERT INTO collection_items (
        collection_id, catalog_item_id, condition, is_complete,
        purchase_price, purchase_date, current_market_value, notes
    ) VALUES (
        collection_zelda_id, catalog_zelda_book,
        'near_mint', true,
        25.00, '2023-08-20', 35.00,
        'Primera edición en inglés'
    ) RETURNING id INTO item_book;
    
    -- Agregar el Amiibo
    INSERT INTO collection_items (
        collection_id, catalog_item_id, condition, is_complete,
        purchase_price, purchase_date, current_market_value, notes
    ) VALUES (
        collection_zelda_id, catalog_zelda_amiibo,
        'mint', true,
        15.00, '2023-11-05', 25.00,
        'Sellado en caja original'
    ) RETURNING id INTO item_amiibo;
    
    -- Agregar imágenes de ejemplo
    INSERT INTO item_images (collection_item_id, file_path, file_name, image_type, is_primary)
    VALUES
        (item_game, '/uploads/items/' || item_game || '/front.jpg', 'front.jpg', 'front', true),
        (item_ost, '/uploads/items/' || item_ost || '/cover.jpg', 'cover.jpg', 'front', true),
        (item_book, '/uploads/items/' || item_book || '/cover.jpg', 'cover.jpg', 'front', true),
        (item_amiibo, '/uploads/items/' || item_amiibo || '/box.jpg', 'box.jpg', 'front', true);
END $$;

-- ============================================
-- 10. WISHLIST
-- ============================================

-- Wishlist en la colección Zelda multi-category
DO $$
DECLARE
    collection_zelda_id UUID;
    wishlist_id UUID;
BEGIN
    SELECT id INTO collection_zelda_id FROM collections WHERE theme = 'The Legend of Zelda';
    
    -- Aquí podrías agregar items de diferentes categorías a la wishlist
    -- Por ejemplo: un juego de Zelda que falta, un CD soundtrack, una figura exclusiva, etc.
END $$;

-- ============================================
-- QUERIES DE EJEMPLO
-- ============================================

-- Ver todas las colecciones y su tipo
-- SELECT id, name, collection_type, theme, restricted_to_sub_category_id FROM collections;

-- Ver items de la colección Zelda agrupados por categoría
-- SELECT * FROM v_collection_items_by_category WHERE collection_name LIKE '%Zelda%';

-- Ver estadísticas de la colección multi-category
-- SELECT * FROM v_collection_stats WHERE theme = 'The Legend of Zelda';

-- Ver items de Zelda en todas las colecciones
-- SELECT 
--     c.name as collection_name,
--     c.collection_type,
--     ci.catalog_title,
--     ci.main_category_name,
--     ci.subcategory_name
-- FROM v_collection_items_full ci
-- JOIN collections c ON ci.collection_id = c.id
-- WHERE ci.catalog_title LIKE '%Zelda%' OR c.theme LIKE '%Zelda%'
-- ORDER BY c.name, ci.main_category_name;
