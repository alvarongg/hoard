-- ============================================
-- EJEMPLOS DE USO: manufacturer, publisher, developer, brand
-- Ejemplos para diferentes categorías de productos
-- ============================================

-- ============================================
-- VIDEOJUEGOS
-- ============================================

-- Ejemplo 1: Developer y Publisher son DIFERENTES
-- Donkey Kong 64 - Desarrollado por Rare, publicado por Nintendo
INSERT INTO catalog_items (
    catalog_id, title, upc,
    language, region, version_name,
    manufacturer, publisher, developer,
    description, release_date, custom_fields
) VALUES (
    'uuid-catalog-n64',
    'Donkey Kong 64',
    '045496870154',
    'english', 'NTSC', 'USA Release',
    'Nintendo',           -- Fabricante (la consola es de Nintendo)
    'Nintendo',           -- Distribuidor
    'Rare',              -- Desarrollador (Rare hizo el juego)
    'Platformer developed by Rare for Nintendo 64.',
    '1999-11-22',
    '{"platform": "Nintendo 64", "genre": ["Platformer", "Adventure"]}'::jsonb
);

-- Ejemplo 2: Developer y Publisher IGUALES
-- Super Mario 64
INSERT INTO catalog_items (
    catalog_id, title,
    manufacturer, publisher, developer,
    description
) VALUES (
    'uuid-catalog-n64',
    'Super Mario 64',
    'Nintendo',
    'Nintendo',
    'Nintendo EAD',      -- División interna de Nintendo
    'Launch title for Nintendo 64.'
);

-- Ejemplo 3: Juego Third-Party
-- Metal Gear Solid (PlayStation)
INSERT INTO catalog_items (
    catalog_id, title,
    manufacturer, publisher, developer,
    description
) VALUES (
    'uuid-catalog-ps1',
    'Metal Gear Solid',
    'Sony',              -- Consola PlayStation
    'Konami',            -- Publicado por Konami
    'Konami',            -- Desarrollado por Konami
    'Stealth action game for PlayStation.'
);

-- ============================================
-- LIBROS
-- ============================================

-- Ejemplo 1: Editorial española (Minotauro)
-- El Señor de los Anillos
INSERT INTO catalog_items (
    catalog_id, title, isbn,
    language, region,
    manufacturer, publisher,
    description
) VALUES (
    'uuid-catalog-tolkien',
    'El Señor de los Anillos - La Comunidad del Anillo',
    '978-8445077528',
    'spanish', 'Spain',
    'Editorial Planeta',  -- Grupo editorial
    'Minotauro',         -- Sello/Editorial específica
    'Primera parte de la trilogía en español.'
);

-- Ejemplo 2: Editorial argentina
-- El Eternauta
INSERT INTO catalog_items (
    catalog_id, title,
    language, region,
    manufacturer, publisher,
    description
) VALUES (
    'uuid-catalog-comics-ar',
    'El Eternauta',
    'spanish', 'Argentina',
    'Biblioteca Clarín',
    'Biblioteca Clarín',
    'Clásico del cómic argentino.'
);

-- ============================================
-- MÚSICA (Vinilos/CDs)
-- ============================================

-- Ejemplo 1: Disco de vinilo
-- Dark Side of the Moon - Pink Floyd
INSERT INTO catalog_items (
    catalog_id, title,
    language, region,
    manufacturer, publisher,
    description, custom_fields
) VALUES (
    'uuid-catalog-vinyl',
    'The Dark Side of the Moon',
    'english', 'USA',
    'Columbia Records',   -- Fabricante del disco
    'Harvest Records',    -- Sello discográfico
    'Iconic Pink Floyd album on vinyl.',
    '{"artist": "Pink Floyd", "label": "Harvest", "pressing": "180g", "rpm": "33"}'::jsonb
);

-- Ejemplo 2: Soundtrack de videojuego
-- Chrono Trigger OST
INSERT INTO catalog_items (
    catalog_id, title,
    manufacturer, publisher,
    description
) VALUES (
    'uuid-catalog-soundtracks',
    'Chrono Trigger Original Sound Version',
    'Square Enix',
    'Square Enix',
    'Official soundtrack for Chrono Trigger.'
);

-- ============================================
-- TRADING CARD GAMES
-- ============================================

-- Ejemplo 1: Pokemon TCG
-- Charizard Base Set
INSERT INTO catalog_items (
    catalog_id, title, upc,
    manufacturer, publisher,
    description, custom_fields
) VALUES (
    'uuid-catalog-pokemon',
    'Charizard',
    '820650803505',
    'The Pokemon Company',      -- Dueños de la IP
    'Wizards of the Coast',     -- Quien imprime/distribuye (hasta 2003)
    'Rare holographic card from Base Set.',
    '{"set": "Base Set", "number": "4/102", "rarity": "Rare Holo"}'::jsonb
);

-- Ejemplo 2: Magic The Gathering
-- Black Lotus
INSERT INTO catalog_items (
    catalog_id, title,
    manufacturer, publisher,
    description, custom_fields
) VALUES (
    'uuid-catalog-mtg',
    'Black Lotus',
    'Wizards of the Coast',
    'Wizards of the Coast',
    'Power Nine card from Alpha set.',
    '{"set": "Alpha", "rarity": "Rare", "type": "Artifact"}'::jsonb
);

-- ============================================
-- JUGUETES / FIGURAS
-- ============================================

-- Ejemplo 1: Hot Wheels (sub-marca de Mattel)
-- Hot Wheels Car
INSERT INTO catalog_items (
    catalog_id, title, upc,
    manufacturer, brand, variation,
    description
) VALUES (
    'uuid-catalog-toys',
    'Hot Wheels - 1967 Camaro',
    '887961707342',
    'Mattel',            -- Fabricante
    'Hot Wheels',        -- Marca/Línea
    'Red',               -- Variación de color
    'Die-cast 1:64 scale car.'
);

-- Ejemplo 2: Transformers (Hasbro)
INSERT INTO catalog_items (
    catalog_id, title,
    manufacturer, brand, variation,
    description
) VALUES (
    'uuid-catalog-toys',
    'Optimus Prime',
    'Hasbro',
    'Transformers',
    'Generation 1',
    'Original G1 Optimus Prime figure.'
);

-- Ejemplo 3: Funko Pop
INSERT INTO catalog_items (
    catalog_id, title, upc,
    manufacturer, brand, variation,
    description, custom_fields
) VALUES (
    'uuid-catalog-funko',
    'Spider-Man',
    '889698453424',
    'Funko',
    'Funko Pop',
    'Metallic',           -- Variación Chase
    'Chase variant with metallic finish.',
    '{"series": "Marvel", "number": "593", "chase_ratio": "1:6"}'::jsonb
);

-- Ejemplo 4: LEGO
INSERT INTO catalog_items (
    catalog_id, title, upc,
    manufacturer, brand,
    description, custom_fields
) VALUES (
    'uuid-catalog-toys',
    'LEGO Star Wars Millennium Falcon',
    '673419282024',
    'LEGO Group',
    'LEGO Star Wars',
    'Ultimate Collector Series Millennium Falcon.',
    '{"pieces": 7541, "set_number": "75192"}'::jsonb
);

-- ============================================
-- CONSOLAS
-- ============================================

-- Ejemplo: Nintendo Switch
INSERT INTO catalog_items (
    catalog_id, title, upc,
    manufacturer, publisher, variation,
    description
) VALUES (
    'uuid-catalog-consoles',
    'Nintendo Switch',
    '045496590277',
    'Nintendo',
    'Nintendo',
    'Neon Red/Blue',     -- Variación de color
    'Hybrid gaming console.'
);

-- ============================================
-- QUERIES ÚTILES
-- ============================================

-- 1. Buscar todos los juegos desarrollados por Rare
SELECT 
    title, 
    manufacturer, 
    publisher, 
    developer, 
    release_date
FROM catalog_items
WHERE developer = 'Rare'
ORDER BY release_date;

-- 2. Buscar todos los libros de Editorial Minotauro
SELECT 
    title, 
    publisher, 
    isbn, 
    language
FROM catalog_items
WHERE publisher = 'Minotauro'
ORDER BY title;

-- 3. Buscar todos los productos de Mattel
SELECT 
    title, 
    manufacturer, 
    brand, 
    variation
FROM catalog_items
WHERE manufacturer = 'Mattel'
ORDER BY brand, title;

-- 4. Buscar juegos donde Developer ≠ Publisher
SELECT 
    title, 
    developer, 
    publisher,
    release_date
FROM catalog_items
WHERE developer IS NOT NULL 
    AND publisher IS NOT NULL 
    AND developer != publisher
ORDER BY release_date;

-- 5. Agrupar por fabricante (Top fabricantes por cantidad)
SELECT 
    manufacturer,
    COUNT(*) as total_items,
    COUNT(DISTINCT variation) as variations
FROM catalog_items
WHERE manufacturer IS NOT NULL
GROUP BY manufacturer
ORDER BY total_items DESC
LIMIT 20;

-- 6. Agrupar por desarrollador (videojuegos)
SELECT 
    developer,
    COUNT(*) as games_developed,
    MIN(release_date) as first_game,
    MAX(release_date) as latest_game
FROM catalog_items
WHERE developer IS NOT NULL
GROUP BY developer
ORDER BY games_developed DESC;

-- 7. Buscar productos con marca específica
SELECT 
    title,
    manufacturer,
    brand,
    variation
FROM catalog_items
WHERE brand = 'Hot Wheels'
ORDER BY title;

-- 8. Full-text search incluyendo manufacturer/publisher/developer
SELECT 
    title,
    manufacturer,
    publisher,
    developer
FROM catalog_items
WHERE search_vector @@ to_tsquery('english', 'Nintendo | Rare')
ORDER BY ts_rank(search_vector, to_tsquery('english', 'Nintendo | Rare')) DESC;

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista: Juegos por desarrollador y publisher
CREATE OR REPLACE VIEW v_games_by_developer_publisher AS
SELECT 
    developer,
    publisher,
    COUNT(*) as game_count,
    ARRAY_AGG(DISTINCT title ORDER BY title) as games
FROM catalog_items
WHERE developer IS NOT NULL 
GROUP BY developer, publisher
ORDER BY game_count DESC;

-- Vista: Productos por fabricante
CREATE OR REPLACE VIEW v_products_by_manufacturer AS
SELECT 
    mc.name as category,
    sc.name as subcategory,
    ci.manufacturer,
    ci.brand,
    COUNT(*) as product_count,
    MIN(ci.release_date) as first_release,
    MAX(ci.release_date) as latest_release
FROM catalog_items ci
JOIN catalogs cat ON ci.catalog_id = cat.id
JOIN sub_categories sc ON cat.sub_category_id = sc.id
JOIN main_categories mc ON sc.main_category_id = mc.id
WHERE ci.manufacturer IS NOT NULL
GROUP BY mc.name, sc.name, ci.manufacturer, ci.brand
ORDER BY product_count DESC;

-- Vista: Libros por editorial
CREATE OR REPLACE VIEW v_books_by_publisher AS
SELECT 
    publisher,
    language,
    COUNT(*) as book_count,
    ARRAY_AGG(DISTINCT title ORDER BY title) as titles
FROM catalog_items ci
JOIN catalogs cat ON ci.catalog_id = cat.id
JOIN sub_categories sc ON cat.sub_category_id = sc.id
JOIN main_categories mc ON sc.main_category_id = mc.id
WHERE mc.slug = 'books' 
    AND publisher IS NOT NULL
GROUP BY publisher, language
ORDER BY book_count DESC;
