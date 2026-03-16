-- ============================================
-- COLLECTION MANAGER - Database Schema v2
-- PostgreSQL 14+
-- UPDATED: Soporte para colecciones multi-categoría
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- for similarity searches

-- ============================================
-- 1. CATEGORÍAS PRINCIPALES
-- ============================================
CREATE TABLE main_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE main_categories IS 'Categorías principales: Videojuegos, Música, Libros, TCG, Juguetes, etc.';

CREATE INDEX idx_main_categories_slug ON main_categories(slug);

-- ============================================
-- 2. SUB-CATEGORÍAS
-- ============================================
CREATE TABLE sub_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    main_category_id UUID NOT NULL REFERENCES main_categories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(main_category_id, slug)
);

COMMENT ON TABLE sub_categories IS 'Subcategorías: Consolas, Juegos, Vinilos, CDs, Pokemon, MTG, etc.';

CREATE INDEX idx_sub_categories_main ON sub_categories(main_category_id);
CREATE INDEX idx_sub_categories_slug ON sub_categories(slug);

-- ============================================
-- 3. ESQUEMAS DE CAMPOS PERSONALIZADOS
-- ============================================
CREATE TABLE category_field_schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_category_id UUID NOT NULL REFERENCES sub_categories(id) ON DELETE CASCADE,
    
    field_name VARCHAR(100) NOT NULL,
    field_label VARCHAR(200) NOT NULL,
    field_type VARCHAR(50) NOT NULL, 
    -- 'text', 'number', 'date', 'select', 'multiselect', 'boolean', 'textarea'
    
    field_options JSONB, -- para select/multiselect: {"values": ["Option1", "Option2"]}
    is_required BOOLEAN DEFAULT false,
    is_searchable BOOLEAN DEFAULT true,
    default_value TEXT,
    
    help_text TEXT,
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sub_category_id, field_name)
);

COMMENT ON TABLE category_field_schemas IS 'Define los campos custom que cada sub-categoría puede tener';

CREATE INDEX idx_category_fields_sub ON category_field_schemas(sub_category_id);

-- ============================================
-- 4. COMPONENTES ESTÁNDAR POR SUB-CATEGORÍA
-- ============================================
CREATE TABLE standard_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_category_id UUID NOT NULL REFERENCES sub_categories(id) ON DELETE CASCADE,
    
    component_name VARCHAR(100) NOT NULL,
    component_type VARCHAR(50) NOT NULL,
    -- 'required', 'common', 'optional', 'variant_specific'
    
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sub_category_id, component_name)
);

COMMENT ON TABLE standard_components IS 'Componentes típicos: caja, manual, cartucho, etc.';
COMMENT ON COLUMN standard_components.component_type IS 'required=obligatorio, common=usual, optional=opcional, variant_specific=depende de la variante';

CREATE INDEX idx_standard_components_sub ON standard_components(sub_category_id);

-- ============================================
-- 5. PROVEEDORES / LUGARES DE COMPRA
-- ============================================
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50), -- 'online', 'physical_store', 'marketplace', 'private_seller', 'auction'
    
    -- Ubicación
    country VARCHAR(2), -- ISO 3166-1 alpha-2
    state_province VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    postal_code VARCHAR(20),
    
    -- Contacto
    website VARCHAR(500),
    email VARCHAR(200),
    phone VARCHAR(50),
    
    -- Social/Marketplace
    marketplace_url VARCHAR(500),
    social_media JSONB, -- {"instagram": "@...", "facebook": "..."}
    
    -- Metadata
    rating DECIMAL(3, 2), -- 0.00 - 5.00
    notes TEXT,
    is_favorite BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE suppliers IS 'Proveedores, tiendas, vendedores, etc.';

CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_type ON suppliers(type);
CREATE INDEX idx_suppliers_country ON suppliers(country);
CREATE INDEX idx_suppliers_active ON suppliers(is_active);

-- ============================================
-- 6. CATÁLOGOS
-- ============================================
CREATE TABLE catalogs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_category_id UUID NOT NULL REFERENCES sub_categories(id) ON DELETE RESTRICT,
    
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    
    -- Origen del catálogo
    source_type VARCHAR(50), -- 'import', 'manual', 'api', 'community'
    source_name VARCHAR(200), -- 'IGDB', 'PriceCharting', 'Discogs', 'Custom', etc.
    source_url VARCHAR(500),
    
    -- Metadata
    total_items INTEGER DEFAULT 0,
    is_official BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Permisos
    is_public BOOLEAN DEFAULT false,
    created_by VARCHAR(100), -- user_id en el futuro
    
    imported_at TIMESTAMP,
    last_sync_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE catalogs IS 'Catálogos maestros de productos (ej: "Todos los juegos de N64")';

CREATE INDEX idx_catalogs_sub_category ON catalogs(sub_category_id);
CREATE INDEX idx_catalogs_active ON catalogs(is_active);
CREATE INDEX idx_catalogs_public ON catalogs(is_public);

-- ============================================
-- 7. ITEMS DEL CATÁLOGO
-- ============================================
CREATE TABLE catalog_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_id UUID NOT NULL REFERENCES catalogs(id) ON DELETE CASCADE,
    
    -- Identificación base
    title VARCHAR(500) NOT NULL,
    subtitle VARCHAR(500),
    alternate_titles TEXT[],
    
    -- Códigos de producto
    sku VARCHAR(100),
    upc VARCHAR(50),
    ean VARCHAR(50),
    isbn VARCHAR(20),
    asin VARCHAR(20),
    
    -- Versión/Idioma/Región
    language VARCHAR(50), -- 'english', 'japanese', 'spanish', 'french', 'multi-language'
    language_codes TEXT[], -- ['en', 'ja'] ISO 639-1
    region VARCHAR(50), -- 'NTSC', 'PAL', 'NTSC-J', 'NTSC-K', 'Multi-region'
    version_name VARCHAR(200), -- 'USA Release', 'Japanese Release', 'European Release', 'Limited Edition'
    
    -- Variación específica
    variation VARCHAR(200), -- 'Red variant', 'Blue variant', 'Test Print', 'Promo', 'Alternate art'
    variation_details TEXT, -- descripción detallada de la variación
    
    -- Agrupación de versiones relacionadas
    related_items_group UUID, -- UUID para agrupar el mismo producto en diferentes versiones
    
    -- Descripción
    description TEXT,
    release_date DATE,
    
    -- Fabricante/Editorial/Desarrollador
    manufacturer VARCHAR(200), -- Fabricante (Mattel, Nintendo, Sony, Hasbro, Bandai)
    publisher VARCHAR(200), -- Distribuidor/Editorial/Sello (Nintendo, Minotauro, Sony Music, WotC)
    developer VARCHAR(200), -- Desarrollador (principalmente videojuegos - Rare, HAL Laboratory)
    brand VARCHAR(200), -- Marca/Línea (Hot Wheels, Funko Pop, Transformers)
    
    -- Campos dinámicos según la sub-categoría
    custom_fields JSONB NOT NULL DEFAULT '{}',
    
    -- Componentes que incluye esta versión específica
    standard_components_included UUID[],
    
    -- Imágenes de referencia
    cover_image_url VARCHAR(1000),
    images JSONB, -- [{"url": "...", "type": "box_front", "caption": "..."}, ...]
    
    -- Metadata de coleccionabilidad
    rarity VARCHAR(50), -- 'common', 'uncommon', 'rare', 'ultra_rare', 'grail'
    production_run INTEGER,
    is_limited_edition BOOLEAN DEFAULT false,
    is_promotional BOOLEAN DEFAULT false,
    is_prototype BOOLEAN DEFAULT false,
    
    -- Búsqueda full-text
    search_vector tsvector,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE catalog_items IS 'Items del catálogo maestro - cada versión/idioma/variación es un registro único';
COMMENT ON COLUMN catalog_items.related_items_group IS 'UUID compartido entre versiones del mismo producto (ej: Mega Man USA y Rockman Japan)';
COMMENT ON COLUMN catalog_items.variation IS 'Variación específica: color, forma, edición especial, test print, etc.';
COMMENT ON COLUMN catalog_items.manufacturer IS 'Fabricante del producto (Mattel, Hasbro, Nintendo, Sony, Bandai, etc.)';
COMMENT ON COLUMN catalog_items.publisher IS 'Distribuidor/Editorial/Sello (Nintendo, Minotauro, Sony Music, WotC, etc.)';
COMMENT ON COLUMN catalog_items.developer IS 'Desarrollador (principalmente para videojuegos - Rare, HAL Laboratory, etc.)';
COMMENT ON COLUMN catalog_items.brand IS 'Marca o línea de producto (Hot Wheels, Funko Pop, Transformers, etc.)';

CREATE INDEX idx_catalog_items_catalog ON catalog_items(catalog_id);
CREATE INDEX idx_catalog_items_sku ON catalog_items(sku);
CREATE INDEX idx_catalog_items_upc ON catalog_items(upc);
CREATE INDEX idx_catalog_items_ean ON catalog_items(ean);
CREATE INDEX idx_catalog_items_isbn ON catalog_items(isbn);
CREATE INDEX idx_catalog_items_language ON catalog_items(language);
CREATE INDEX idx_catalog_items_region ON catalog_items(region);
CREATE INDEX idx_catalog_items_variation ON catalog_items(variation);
CREATE INDEX idx_catalog_items_related_group ON catalog_items(related_items_group);
CREATE INDEX idx_catalog_items_manufacturer ON catalog_items(manufacturer);
CREATE INDEX idx_catalog_items_publisher ON catalog_items(publisher);
CREATE INDEX idx_catalog_items_developer ON catalog_items(developer);
CREATE INDEX idx_catalog_items_brand ON catalog_items(brand);
CREATE INDEX idx_catalog_items_publisher_developer ON catalog_items(publisher, developer);
CREATE INDEX idx_catalog_items_search ON catalog_items USING GIN(search_vector);
CREATE INDEX idx_catalog_items_title_trgm ON catalog_items USING GIN(title gin_trgm_ops);

-- ============================================
-- 8. HISTORIAL DE PRECIOS DE CATÁLOGO
-- ============================================
CREATE TABLE catalog_price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_item_id UUID NOT NULL REFERENCES catalog_items(id) ON DELETE CASCADE,
    
    -- Condición y completitud para el precio
    condition VARCHAR(50) NOT NULL, -- 'mint', 'near_mint', 'excellent', 'good', 'fair', 'poor'
    is_complete BOOLEAN NOT NULL DEFAULT true,
    completeness_description VARCHAR(200), -- 'CIB', 'Loose', 'Sealed', 'No manual', etc.
    
    -- Precio
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Origen del dato
    source VARCHAR(200), -- 'pricecharting', 'ebay_sold', 'manual', 'market_average'
    source_url VARCHAR(500),
    
    -- Fecha del precio
    price_date DATE NOT NULL,
    
    -- Metadata
    region VARCHAR(10),
    notes TEXT,
    
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_price_record UNIQUE(catalog_item_id, condition, is_complete, price_date, source)
);

COMMENT ON TABLE catalog_price_history IS 'Historial de precios del mercado para cada item del catálogo';

CREATE INDEX idx_catalog_price_history_item ON catalog_price_history(catalog_item_id);
CREATE INDEX idx_catalog_price_history_date ON catalog_price_history(price_date DESC);
CREATE INDEX idx_catalog_price_history_condition ON catalog_price_history(condition, is_complete);

-- ============================================
-- 9. COLECCIONES PERSONALES (UPDATED - MULTI-CATEGORY SUPPORT)
-- ============================================
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- NUEVO: Tipo de colección
    collection_type VARCHAR(50) DEFAULT 'single_category' CHECK (collection_type IN ('single_category', 'multi_category', 'mixed')),
    -- 'single_category' = solo items de una subcategoría (ej: solo juegos N64)
    -- 'multi_category' = items de múltiples subcategorías bajo un tema (ej: todo de Zelda)
    -- 'mixed' = sin restricción alguna
    
    -- NUEVO: Tema/Franquicia (para colecciones multi-category)
    theme VARCHAR(100), -- 'The Legend of Zelda', 'Star Wars', 'Pokemon', null
    theme_description TEXT,
    
    -- Restricción de categoría (solo para single_category)
    restricted_to_sub_category_id UUID REFERENCES sub_categories(id) ON DELETE RESTRICT,
    
    -- Objetivos de la colección
    goal_description TEXT,
    goal_items_count INTEGER,
    
    -- Display
    display_order VARCHAR(50) DEFAULT 'custom', -- 'alphabetical', 'release_date', 'acquisition_date', 'custom', 'value', 'category'
    is_public BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: si es single_category, debe tener restricted_to_sub_category_id
    CONSTRAINT check_single_category_restriction CHECK (
        (collection_type = 'single_category' AND restricted_to_sub_category_id IS NOT NULL) OR
        (collection_type != 'single_category')
    )
);

COMMENT ON TABLE collections IS 'Colecciones personales - pueden ser single-category o multi-category';
COMMENT ON COLUMN collections.collection_type IS 'single_category=una sola subcategoría, multi_category=múltiples bajo un tema, mixed=sin restricción';
COMMENT ON COLUMN collections.theme IS 'Tema/franquicia para colecciones multi-category (ej: The Legend of Zelda, Star Wars)';

CREATE INDEX idx_collections_type ON collections(collection_type);
CREATE INDEX idx_collections_theme ON collections(theme);
CREATE INDEX idx_collections_restricted_sub ON collections(restricted_to_sub_category_id);
CREATE INDEX idx_collections_active ON collections(is_active);

-- ============================================
-- 10. ITEMS DE LA COLECCIÓN (Lo que realmente tenés)
-- ============================================
CREATE TABLE collection_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    catalog_item_id UUID NOT NULL REFERENCES catalog_items(id) ON DELETE RESTRICT,
    
    -- Override de info (por si difiere del catálogo)
    title_override VARCHAR(500),
    notes TEXT,
    
    -- Estado general
    condition VARCHAR(50) NOT NULL, -- 'mint', 'near_mint', 'excellent', 'good', 'fair', 'poor'
    condition_notes TEXT,
    
    -- Completitud
    is_complete BOOLEAN DEFAULT false,
    completeness_notes TEXT,
    
    -- Variante específica (si aplica y difiere del catálogo)
    variant_description VARCHAR(200),
    
    -- Autenticidad
    is_authentic BOOLEAN DEFAULT true,
    authenticity_notes TEXT,
    
    -- Ubicación física
    storage_location VARCHAR(200),
    storage_position VARCHAR(100),
    
    -- Valorización
    purchase_price DECIMAL(10, 2),
    purchase_currency VARCHAR(3) DEFAULT 'USD',
    purchase_date DATE,
    
    current_market_value DECIMAL(10, 2),
    current_value_currency VARCHAR(3) DEFAULT 'USD',
    last_value_update TIMESTAMP,
    value_source VARCHAR(200),
    
    -- Adquisición principal
    acquisition_date DATE,
    acquisition_type VARCHAR(50), -- 'purchase', 'gift', 'trade', 'found', 'inherited'
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    
    -- Grading (si aplica)
    is_graded BOOLEAN DEFAULT false,
    grading_company VARCHAR(100), -- 'PSA', 'BGS', 'CGC', 'WATA', etc.
    grade VARCHAR(20),
    certification_number VARCHAR(100),
    grading_date DATE,
    
    -- Seguros/Protección
    is_insured BOOLEAN DEFAULT false,
    insurance_value DECIMAL(10, 2),
    insurance_company VARCHAR(200),
    
    -- Campos customizables adicionales
    custom_fields JSONB DEFAULT '{}',
    
    -- Tags personalizados
    tags TEXT[],
    
    -- Estado de venta
    for_sale BOOLEAN DEFAULT false,
    asking_price DECIMAL(10, 2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE collection_items IS 'Items reales que el usuario posee en su colección';

CREATE INDEX idx_collection_items_collection ON collection_items(collection_id);
CREATE INDEX idx_collection_items_catalog ON collection_items(catalog_item_id);
CREATE INDEX idx_collection_items_condition ON collection_items(condition);
CREATE INDEX idx_collection_items_tags ON collection_items USING GIN(tags);
CREATE INDEX idx_collection_items_graded ON collection_items(is_graded);
CREATE INDEX idx_collection_items_for_sale ON collection_items(for_sale);

-- ============================================
-- 11. COMPONENTES DEL ITEM REAL
-- ============================================
CREATE TABLE item_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_item_id UUID NOT NULL REFERENCES collection_items(id) ON DELETE CASCADE,
    standard_component_id UUID REFERENCES standard_components(id) ON DELETE SET NULL,
    
    -- Si no está en standard, es custom
    component_name VARCHAR(100) NOT NULL,
    component_type VARCHAR(50),
    
    is_present BOOLEAN DEFAULT true,
    condition VARCHAR(50),
    condition_notes TEXT,
    
    -- Para componentes que pueden tener variantes
    variant_description VARCHAR(200),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE item_components IS 'Componentes individuales de cada item (caja, manual, etc.)';

CREATE INDEX idx_item_components_item ON item_components(collection_item_id);
CREATE INDEX idx_item_components_standard ON item_components(standard_component_id);

-- ============================================
-- 12. IMÁGENES DE ITEMS REALES
-- ============================================
CREATE TABLE item_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_item_id UUID NOT NULL REFERENCES collection_items(id) ON DELETE CASCADE,
    
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    
    image_type VARCHAR(50), -- 'main', 'front', 'back', 'detail', 'component', 'damage', 'certificate', 'receipt'
    description TEXT,
    
    sort_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE item_images IS 'Imágenes de los items reales del usuario (solo rutas)';

CREATE INDEX idx_item_images_item ON item_images(collection_item_id);
CREATE INDEX idx_item_images_primary ON item_images(collection_item_id, is_primary) WHERE is_primary = true;
CREATE INDEX idx_item_images_type ON item_images(image_type);

-- ============================================
-- 13. HISTORIAL DE TRANSACCIONES
-- ============================================
CREATE TABLE item_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_item_id UUID NOT NULL REFERENCES collection_items(id) ON DELETE CASCADE,
    
    transaction_type VARCHAR(50) NOT NULL, 
    -- 'purchase', 'sale', 'trade_in', 'trade_out', 'gift_received', 'gift_given', 
    -- 'repair', 'appraisal', 'grading', 'insurance_claim'
    
    transaction_date DATE NOT NULL,
    
    -- Precio/Valor
    amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Costos adicionales
    shipping_cost DECIMAL(10, 2),
    tax_amount DECIMAL(10, 2),
    other_fees DECIMAL(10, 2),
    
    total_amount DECIMAL(10, 2) GENERATED ALWAYS AS (
        COALESCE(amount, 0) + COALESCE(shipping_cost, 0) + COALESCE(tax_amount, 0) + COALESCE(other_fees, 0)
    ) STORED,
    
    -- Contraparte
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    counterpart_name VARCHAR(200),
    
    -- Documentación
    invoice_number VARCHAR(100),
    receipt_path VARCHAR(500),
    payment_method VARCHAR(50), -- 'cash', 'credit_card', 'paypal', 'bank_transfer', 'crypto'
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE item_transactions IS 'Historial completo de transacciones de cada item';

CREATE INDEX idx_item_transactions_item ON item_transactions(collection_item_id);
CREATE INDEX idx_item_transactions_type ON item_transactions(transaction_type);
CREATE INDEX idx_item_transactions_date ON item_transactions(transaction_date DESC);
CREATE INDEX idx_item_transactions_supplier ON item_transactions(supplier_id);

-- ============================================
-- 14. WISHLIST
-- ============================================
CREATE TABLE wishlist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    catalog_item_id UUID NOT NULL REFERENCES catalog_items(id) ON DELETE RESTRICT,
    
    -- Criterios de búsqueda
    desired_condition VARCHAR(50),
    desired_condition_min VARCHAR(50), -- condición mínima aceptable
    must_be_complete BOOLEAN DEFAULT true,
    desired_completeness_description TEXT,
    
    -- Presupuesto
    max_price DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Variante específica buscada
    specific_variant_required BOOLEAN DEFAULT false,
    variant_description VARCHAR(200),
    
    -- Prioridad
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5), -- 1 (baja) a 5 (alta)
    urgency VARCHAR(50) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    
    -- Notas
    notes TEXT,
    search_notes TEXT,
    
    -- Tags
    tags TEXT[],
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    is_acquired BOOLEAN DEFAULT false,
    acquired_date DATE,
    acquired_collection_item_id UUID REFERENCES collection_items(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE wishlist_items IS 'Lista de deseos vinculada a items específicos del catálogo';

CREATE INDEX idx_wishlist_collection ON wishlist_items(collection_id);
CREATE INDEX idx_wishlist_catalog ON wishlist_items(catalog_item_id);
CREATE INDEX idx_wishlist_priority ON wishlist_items(priority DESC);
CREATE INDEX idx_wishlist_active ON wishlist_items(is_active, is_acquired);
CREATE INDEX idx_wishlist_tags ON wishlist_items USING GIN(tags);

-- ============================================
-- 15. AVISTAMIENTOS DE WISHLIST
-- ============================================
CREATE TABLE wishlist_sightings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wishlist_item_id UUID NOT NULL REFERENCES wishlist_items(id) ON DELETE CASCADE,
    
    sighted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Dónde se vio
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    location_description VARCHAR(500),
    url VARCHAR(1000),
    
    -- Detalles del producto visto
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    condition VARCHAR(50),
    is_complete BOOLEAN,
    description TEXT,
    
    -- Imágenes del avistamiento
    image_urls TEXT[],
    
    -- Disponibilidad
    is_available BOOLEAN DEFAULT true,
    quantity_available INTEGER DEFAULT 1,
    last_checked_at TIMESTAMP,
    
    -- Follow-up
    contacted BOOLEAN DEFAULT false,
    contacted_at TIMESTAMP,
    contact_method VARCHAR(50), -- 'email', 'phone', 'message', 'in_person'
    response_notes TEXT,
    
    -- Decisión
    decision VARCHAR(50), -- 'interested', 'pass', 'waiting', 'negotiating', 'purchased', 'lost'
    decision_notes TEXT,
    decision_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE wishlist_sightings IS 'Registro de cada vez que se encuentra un item de la wishlist';

CREATE INDEX idx_wishlist_sightings_item ON wishlist_sightings(wishlist_item_id);
CREATE INDEX idx_wishlist_sightings_supplier ON wishlist_sightings(supplier_id);
CREATE INDEX idx_wishlist_sightings_date ON wishlist_sightings(sighted_at DESC);
CREATE INDEX idx_wishlist_sightings_available ON wishlist_sightings(is_available);
CREATE INDEX idx_wishlist_sightings_decision ON wishlist_sightings(decision);

-- ============================================
-- 16. ACCESORIOS / STOCK DE PROTECCIÓN
-- ============================================
CREATE TABLE accessories_stock (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100), -- 'protective_case', 'sleeve', 'display_stand', 'storage_box', 'grading_holder'
    subcategory VARCHAR(100),
    
    -- Compatibilidad
    compatible_sub_categories UUID[],
    size_specifications JSONB, -- {"width": "10cm", "height": "15cm", "depth": "2cm"}
    
    -- Stock
    quantity_total INTEGER DEFAULT 0,
    quantity_in_use INTEGER DEFAULT 0,
    quantity_available INTEGER GENERATED ALWAYS AS (quantity_total - quantity_in_use) STORED,
    
    minimum_stock_alert INTEGER DEFAULT 5,
    reorder_quantity INTEGER,
    
    -- Valorización
    unit_cost DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Proveedor
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    supplier_sku VARCHAR(100),
    supplier_url VARCHAR(500),
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE accessories_stock IS 'Stock de accesorios de protección y almacenamiento';

CREATE INDEX idx_accessories_category ON accessories_stock(category);
CREATE INDEX idx_accessories_stock_alert ON accessories_stock(quantity_available) WHERE quantity_available <= minimum_stock_alert;

-- ============================================
-- 17. ASIGNACIÓN DE ACCESORIOS
-- ============================================
CREATE TABLE item_accessories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_item_id UUID NOT NULL REFERENCES collection_items(id) ON DELETE CASCADE,
    accessory_id UUID NOT NULL REFERENCES accessories_stock(id) ON DELETE RESTRICT,
    
    quantity_used INTEGER DEFAULT 1,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    UNIQUE(collection_item_id, accessory_id)
);

COMMENT ON TABLE item_accessories IS 'Relación entre items y los accesorios que usan';

CREATE INDEX idx_item_accessories_item ON item_accessories(collection_item_id);
CREATE INDEX idx_item_accessories_accessory ON item_accessories(accessory_id);

-- ============================================
-- FUNCIONES Y TRIGGERS
-- ============================================

-- Función para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a todas las tablas con updated_at
CREATE TRIGGER update_main_categories_updated_at BEFORE UPDATE ON main_categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sub_categories_updated_at BEFORE UPDATE ON sub_categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_catalogs_updated_at BEFORE UPDATE ON catalogs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_catalog_items_updated_at BEFORE UPDATE ON catalog_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collection_items_updated_at BEFORE UPDATE ON collection_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_item_components_updated_at BEFORE UPDATE ON item_components 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wishlist_items_updated_at BEFORE UPDATE ON wishlist_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accessories_stock_updated_at BEFORE UPDATE ON accessories_stock 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para actualizar total_items en catalogs
CREATE OR REPLACE FUNCTION update_catalog_total_items()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE catalogs 
    SET total_items = (
        SELECT COUNT(*) 
        FROM catalog_items 
        WHERE catalog_id = COALESCE(NEW.catalog_id, OLD.catalog_id)
    )
    WHERE id = COALESCE(NEW.catalog_id, OLD.catalog_id);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_catalog_items_count 
    AFTER INSERT OR DELETE ON catalog_items
    FOR EACH ROW EXECUTE FUNCTION update_catalog_total_items();

-- Trigger para stock de accesorios
CREATE OR REPLACE FUNCTION update_accessory_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE accessories_stock 
        SET quantity_in_use = quantity_in_use + NEW.quantity_used
        WHERE id = NEW.accessory_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE accessories_stock 
        SET quantity_in_use = quantity_in_use - OLD.quantity_used
        WHERE id = OLD.accessory_id;
    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE accessories_stock 
        SET quantity_in_use = quantity_in_use - OLD.quantity_used + NEW.quantity_used
        WHERE id = NEW.accessory_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_accessory_stock_trigger 
    AFTER INSERT OR UPDATE OR DELETE ON item_accessories
    FOR EACH ROW EXECUTE FUNCTION update_accessory_stock();

-- Trigger para search vector en catalog_items
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
-- VISTAS ÚTILES
-- ============================================

-- Vista de items con información completa del catálogo
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

-- ============================================
-- COMENTARIOS FINALES
-- ============================================

COMMENT ON DATABASE hoard IS 'Collection Manager v2 - Sistema de gestión de colecciones multi-categoría con soporte para versiones, idiomas y variaciones';
