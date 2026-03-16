"""Initial schema — 17 tables from database/schema.sql

Revision ID: 001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all 17 tables, indexes, triggers, functions, and views."""

    # --- Extensions ---
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # --- 1. main_categories ---
    op.execute("""
        CREATE TABLE main_categories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(100) NOT NULL UNIQUE,
            slug VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            icon VARCHAR(50),
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_main_categories_slug ON main_categories(slug)"
    )

    # --- 2. sub_categories ---
    op.execute("""
        CREATE TABLE sub_categories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            main_category_id UUID NOT NULL
                REFERENCES main_categories(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(main_category_id, slug)
        )
    """)
    op.execute(
        "CREATE INDEX idx_sub_categories_main"
        " ON sub_categories(main_category_id)"
    )
    op.execute(
        "CREATE INDEX idx_sub_categories_slug ON sub_categories(slug)"
    )

    # --- 3. category_field_schemas ---
    op.execute("""
        CREATE TABLE category_field_schemas (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            sub_category_id UUID NOT NULL
                REFERENCES sub_categories(id) ON DELETE CASCADE,
            field_name VARCHAR(100) NOT NULL,
            field_label VARCHAR(200) NOT NULL,
            field_type VARCHAR(50) NOT NULL,
            field_options JSONB,
            is_required BOOLEAN DEFAULT false,
            is_searchable BOOLEAN DEFAULT true,
            default_value TEXT,
            help_text TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sub_category_id, field_name)
        )
    """)
    op.execute(
        "CREATE INDEX idx_category_fields_sub"
        " ON category_field_schemas(sub_category_id)"
    )

    # --- 4. standard_components ---
    op.execute("""
        CREATE TABLE standard_components (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            sub_category_id UUID NOT NULL
                REFERENCES sub_categories(id) ON DELETE CASCADE,
            component_name VARCHAR(100) NOT NULL,
            component_type VARCHAR(50) NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sub_category_id, component_name)
        )
    """)
    op.execute(
        "CREATE INDEX idx_standard_components_sub"
        " ON standard_components(sub_category_id)"
    )

    # --- 5. suppliers ---
    op.execute("""
        CREATE TABLE suppliers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(200) NOT NULL,
            type VARCHAR(50),
            country VARCHAR(2),
            state_province VARCHAR(100),
            city VARCHAR(100),
            address TEXT,
            postal_code VARCHAR(20),
            website VARCHAR(500),
            email VARCHAR(200),
            phone VARCHAR(50),
            marketplace_url VARCHAR(500),
            social_media JSONB,
            rating DECIMAL(3, 2),
            notes TEXT,
            is_favorite BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_suppliers_name ON suppliers(name)")
    op.execute("CREATE INDEX idx_suppliers_type ON suppliers(type)")
    op.execute("CREATE INDEX idx_suppliers_country ON suppliers(country)")
    op.execute(
        "CREATE INDEX idx_suppliers_active ON suppliers(is_active)"
    )

    # --- 6. catalogs ---
    op.execute("""
        CREATE TABLE catalogs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            sub_category_id UUID NOT NULL
                REFERENCES sub_categories(id) ON DELETE RESTRICT,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            version VARCHAR(50),
            source_type VARCHAR(50),
            source_name VARCHAR(200),
            source_url VARCHAR(500),
            total_items INTEGER DEFAULT 0,
            is_official BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            is_public BOOLEAN DEFAULT false,
            created_by VARCHAR(100),
            imported_at TIMESTAMP,
            last_sync_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_catalogs_sub_category"
        " ON catalogs(sub_category_id)"
    )
    op.execute(
        "CREATE INDEX idx_catalogs_active ON catalogs(is_active)"
    )
    op.execute(
        "CREATE INDEX idx_catalogs_public ON catalogs(is_public)"
    )

    # --- 7. catalog_items ---
    op.execute("""
        CREATE TABLE catalog_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            catalog_id UUID NOT NULL
                REFERENCES catalogs(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            subtitle VARCHAR(500),
            alternate_titles TEXT[],
            sku VARCHAR(100),
            upc VARCHAR(50),
            ean VARCHAR(50),
            isbn VARCHAR(20),
            asin VARCHAR(20),
            language VARCHAR(50),
            language_codes TEXT[],
            region VARCHAR(50),
            version_name VARCHAR(200),
            variation VARCHAR(200),
            variation_details TEXT,
            related_items_group UUID,
            description TEXT,
            release_date DATE,
            manufacturer VARCHAR(200),
            publisher VARCHAR(200),
            developer VARCHAR(200),
            brand VARCHAR(200),
            custom_fields JSONB NOT NULL DEFAULT '{}',
            standard_components_included UUID[],
            cover_image_url VARCHAR(1000),
            images JSONB,
            rarity VARCHAR(50),
            production_run INTEGER,
            is_limited_edition BOOLEAN DEFAULT false,
            is_promotional BOOLEAN DEFAULT false,
            is_prototype BOOLEAN DEFAULT false,
            search_vector tsvector,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_catalog_items_catalog"
        " ON catalog_items(catalog_id)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_sku ON catalog_items(sku)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_upc ON catalog_items(upc)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_ean ON catalog_items(ean)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_isbn ON catalog_items(isbn)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_language"
        " ON catalog_items(language)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_region"
        " ON catalog_items(region)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_variation"
        " ON catalog_items(variation)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_related_group"
        " ON catalog_items(related_items_group)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_manufacturer"
        " ON catalog_items(manufacturer)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_publisher"
        " ON catalog_items(publisher)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_developer"
        " ON catalog_items(developer)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_brand"
        " ON catalog_items(brand)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_publisher_developer"
        " ON catalog_items(publisher, developer)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_search"
        " ON catalog_items USING GIN(search_vector)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_items_title_trgm"
        " ON catalog_items USING GIN(title gin_trgm_ops)"
    )

    # --- 8. catalog_price_history ---
    op.execute("""
        CREATE TABLE catalog_price_history (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            catalog_item_id UUID NOT NULL
                REFERENCES catalog_items(id) ON DELETE CASCADE,
            condition VARCHAR(50) NOT NULL,
            is_complete BOOLEAN NOT NULL DEFAULT true,
            completeness_description VARCHAR(200),
            price DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            source VARCHAR(200),
            source_url VARCHAR(500),
            price_date DATE NOT NULL,
            region VARCHAR(10),
            notes TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_price_record UNIQUE(
                catalog_item_id, condition, is_complete,
                price_date, source
            )
        )
    """)
    op.execute(
        "CREATE INDEX idx_catalog_price_history_item"
        " ON catalog_price_history(catalog_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_price_history_date"
        " ON catalog_price_history(price_date DESC)"
    )
    op.execute(
        "CREATE INDEX idx_catalog_price_history_condition"
        " ON catalog_price_history(condition, is_complete)"
    )

    # --- 9. collections ---
    op.execute("""
        CREATE TABLE collections (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(200) NOT NULL,
            description TEXT,
            collection_type VARCHAR(50) DEFAULT 'single_category'
                CHECK (collection_type IN (
                    'single_category', 'multi_category', 'mixed'
                )),
            theme VARCHAR(100),
            theme_description TEXT,
            restricted_to_sub_category_id UUID
                REFERENCES sub_categories(id) ON DELETE RESTRICT,
            goal_description TEXT,
            goal_items_count INTEGER,
            display_order VARCHAR(50) DEFAULT 'custom',
            is_public BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_single_category_restriction CHECK (
                (collection_type = 'single_category'
                 AND restricted_to_sub_category_id IS NOT NULL)
                OR (collection_type != 'single_category')
            )
        )
    """)
    op.execute(
        "CREATE INDEX idx_collections_type"
        " ON collections(collection_type)"
    )
    op.execute(
        "CREATE INDEX idx_collections_theme ON collections(theme)"
    )
    op.execute(
        "CREATE INDEX idx_collections_restricted_sub"
        " ON collections(restricted_to_sub_category_id)"
    )
    op.execute(
        "CREATE INDEX idx_collections_active ON collections(is_active)"
    )

    # --- 10. collection_items ---
    op.execute("""
        CREATE TABLE collection_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            collection_id UUID NOT NULL
                REFERENCES collections(id) ON DELETE CASCADE,
            catalog_item_id UUID NOT NULL
                REFERENCES catalog_items(id) ON DELETE RESTRICT,
            title_override VARCHAR(500),
            notes TEXT,
            condition VARCHAR(50) NOT NULL,
            condition_notes TEXT,
            is_complete BOOLEAN DEFAULT false,
            completeness_notes TEXT,
            variant_description VARCHAR(200),
            is_authentic BOOLEAN DEFAULT true,
            authenticity_notes TEXT,
            storage_location VARCHAR(200),
            storage_position VARCHAR(100),
            purchase_price DECIMAL(10, 2),
            purchase_currency VARCHAR(3) DEFAULT 'USD',
            purchase_date DATE,
            current_market_value DECIMAL(10, 2),
            current_value_currency VARCHAR(3) DEFAULT 'USD',
            last_value_update TIMESTAMP,
            value_source VARCHAR(200),
            acquisition_date DATE,
            acquisition_type VARCHAR(50),
            supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
            is_graded BOOLEAN DEFAULT false,
            grading_company VARCHAR(100),
            grade VARCHAR(20),
            certification_number VARCHAR(100),
            grading_date DATE,
            is_insured BOOLEAN DEFAULT false,
            insurance_value DECIMAL(10, 2),
            insurance_company VARCHAR(200),
            custom_fields JSONB DEFAULT '{}',
            tags TEXT[],
            for_sale BOOLEAN DEFAULT false,
            asking_price DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_collection_items_collection"
        " ON collection_items(collection_id)"
    )
    op.execute(
        "CREATE INDEX idx_collection_items_catalog"
        " ON collection_items(catalog_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_collection_items_condition"
        " ON collection_items(condition)"
    )
    op.execute(
        "CREATE INDEX idx_collection_items_tags"
        " ON collection_items USING GIN(tags)"
    )
    op.execute(
        "CREATE INDEX idx_collection_items_graded"
        " ON collection_items(is_graded)"
    )
    op.execute(
        "CREATE INDEX idx_collection_items_for_sale"
        " ON collection_items(for_sale)"
    )

    # --- 11. item_components ---
    op.execute("""
        CREATE TABLE item_components (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            collection_item_id UUID NOT NULL
                REFERENCES collection_items(id) ON DELETE CASCADE,
            standard_component_id UUID
                REFERENCES standard_components(id) ON DELETE SET NULL,
            component_name VARCHAR(100) NOT NULL,
            component_type VARCHAR(50),
            is_present BOOLEAN DEFAULT true,
            condition VARCHAR(50),
            condition_notes TEXT,
            variant_description VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_item_components_item"
        " ON item_components(collection_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_item_components_standard"
        " ON item_components(standard_component_id)"
    )

    # --- 12. item_images ---
    op.execute("""
        CREATE TABLE item_images (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            collection_item_id UUID NOT NULL
                REFERENCES collection_items(id) ON DELETE CASCADE,
            file_path VARCHAR(1000) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_size INTEGER,
            mime_type VARCHAR(100),
            width INTEGER,
            height INTEGER,
            image_type VARCHAR(50),
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            is_primary BOOLEAN DEFAULT false,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_item_images_item"
        " ON item_images(collection_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_item_images_primary"
        " ON item_images(collection_item_id, is_primary)"
        " WHERE is_primary = true"
    )
    op.execute(
        "CREATE INDEX idx_item_images_type ON item_images(image_type)"
    )

    # --- 13. item_transactions ---
    op.execute("""
        CREATE TABLE item_transactions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            collection_item_id UUID NOT NULL
                REFERENCES collection_items(id) ON DELETE CASCADE,
            transaction_type VARCHAR(50) NOT NULL,
            transaction_date DATE NOT NULL,
            amount DECIMAL(10, 2),
            currency VARCHAR(3) DEFAULT 'USD',
            shipping_cost DECIMAL(10, 2),
            tax_amount DECIMAL(10, 2),
            other_fees DECIMAL(10, 2),
            total_amount DECIMAL(10, 2) GENERATED ALWAYS AS (
                COALESCE(amount, 0)
                + COALESCE(shipping_cost, 0)
                + COALESCE(tax_amount, 0)
                + COALESCE(other_fees, 0)
            ) STORED,
            supplier_id UUID
                REFERENCES suppliers(id) ON DELETE SET NULL,
            counterpart_name VARCHAR(200),
            invoice_number VARCHAR(100),
            receipt_path VARCHAR(500),
            payment_method VARCHAR(50),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_item_transactions_item"
        " ON item_transactions(collection_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_item_transactions_type"
        " ON item_transactions(transaction_type)"
    )
    op.execute(
        "CREATE INDEX idx_item_transactions_date"
        " ON item_transactions(transaction_date DESC)"
    )
    op.execute(
        "CREATE INDEX idx_item_transactions_supplier"
        " ON item_transactions(supplier_id)"
    )

    # --- 14. wishlist_items ---
    op.execute("""
        CREATE TABLE wishlist_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            collection_id UUID NOT NULL
                REFERENCES collections(id) ON DELETE CASCADE,
            catalog_item_id UUID NOT NULL
                REFERENCES catalog_items(id) ON DELETE RESTRICT,
            desired_condition VARCHAR(50),
            desired_condition_min VARCHAR(50),
            must_be_complete BOOLEAN DEFAULT true,
            desired_completeness_description TEXT,
            max_price DECIMAL(10, 2),
            currency VARCHAR(3) DEFAULT 'USD',
            specific_variant_required BOOLEAN DEFAULT false,
            variant_description VARCHAR(200),
            priority INTEGER DEFAULT 3
                CHECK (priority BETWEEN 1 AND 5),
            urgency VARCHAR(50) DEFAULT 'medium',
            notes TEXT,
            search_notes TEXT,
            tags TEXT[],
            is_active BOOLEAN DEFAULT true,
            is_acquired BOOLEAN DEFAULT false,
            acquired_date DATE,
            acquired_collection_item_id UUID
                REFERENCES collection_items(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_wishlist_collection"
        " ON wishlist_items(collection_id)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_catalog"
        " ON wishlist_items(catalog_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_priority"
        " ON wishlist_items(priority DESC)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_active"
        " ON wishlist_items(is_active, is_acquired)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_tags"
        " ON wishlist_items USING GIN(tags)"
    )

    # --- 15. wishlist_sightings ---
    op.execute("""
        CREATE TABLE wishlist_sightings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            wishlist_item_id UUID NOT NULL
                REFERENCES wishlist_items(id) ON DELETE CASCADE,
            sighted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            supplier_id UUID
                REFERENCES suppliers(id) ON DELETE SET NULL,
            location_description VARCHAR(500),
            url VARCHAR(1000),
            price DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            condition VARCHAR(50),
            is_complete BOOLEAN,
            description TEXT,
            image_urls TEXT[],
            is_available BOOLEAN DEFAULT true,
            quantity_available INTEGER DEFAULT 1,
            last_checked_at TIMESTAMP,
            contacted BOOLEAN DEFAULT false,
            contacted_at TIMESTAMP,
            contact_method VARCHAR(50),
            response_notes TEXT,
            decision VARCHAR(50),
            decision_notes TEXT,
            decision_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_wishlist_sightings_item"
        " ON wishlist_sightings(wishlist_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_sightings_supplier"
        " ON wishlist_sightings(supplier_id)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_sightings_date"
        " ON wishlist_sightings(sighted_at DESC)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_sightings_available"
        " ON wishlist_sightings(is_available)"
    )
    op.execute(
        "CREATE INDEX idx_wishlist_sightings_decision"
        " ON wishlist_sightings(decision)"
    )

    # --- 16. accessories_stock ---
    op.execute("""
        CREATE TABLE accessories_stock (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(200) NOT NULL,
            category VARCHAR(100),
            subcategory VARCHAR(100),
            compatible_sub_categories UUID[],
            size_specifications JSONB,
            quantity_total INTEGER DEFAULT 0,
            quantity_in_use INTEGER DEFAULT 0,
            quantity_available INTEGER GENERATED ALWAYS AS (
                quantity_total - quantity_in_use
            ) STORED,
            minimum_stock_alert INTEGER DEFAULT 5,
            reorder_quantity INTEGER,
            unit_cost DECIMAL(10, 2),
            currency VARCHAR(3) DEFAULT 'USD',
            supplier_id UUID
                REFERENCES suppliers(id) ON DELETE SET NULL,
            supplier_sku VARCHAR(100),
            supplier_url VARCHAR(500),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX idx_accessories_category"
        " ON accessories_stock(category)"
    )
    op.execute(
        "CREATE INDEX idx_accessories_stock_alert"
        " ON accessories_stock(quantity_available)"
        " WHERE quantity_available <= minimum_stock_alert"
    )

    # --- 17. item_accessories ---
    op.execute("""
        CREATE TABLE item_accessories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            collection_item_id UUID NOT NULL
                REFERENCES collection_items(id) ON DELETE CASCADE,
            accessory_id UUID NOT NULL
                REFERENCES accessories_stock(id) ON DELETE RESTRICT,
            quantity_used INTEGER DEFAULT 1,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            UNIQUE(collection_item_id, accessory_id)
        )
    """)
    op.execute(
        "CREATE INDEX idx_item_accessories_item"
        " ON item_accessories(collection_item_id)"
    )
    op.execute(
        "CREATE INDEX idx_item_accessories_accessory"
        " ON item_accessories(accessory_id)"
    )

    # --- Functions ---
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)

    # --- Triggers: updated_at ---
    _tables_with_updated_at = [
        "main_categories",
        "sub_categories",
        "suppliers",
        "catalogs",
        "catalog_items",
        "collections",
        "collection_items",
        "item_components",
        "wishlist_items",
        "accessories_stock",
    ]
    for table in _tables_with_updated_at:
        op.execute(
            f"CREATE TRIGGER update_{table}_updated_at"
            f" BEFORE UPDATE ON {table}"
            " FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
        )

    # --- Trigger: catalog total_items ---
    op.execute("""
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
        $$ language 'plpgsql'
    """)
    op.execute(
        "CREATE TRIGGER update_catalog_items_count"
        " AFTER INSERT OR DELETE ON catalog_items"
        " FOR EACH ROW EXECUTE FUNCTION update_catalog_total_items()"
    )

    # --- Trigger: accessory stock ---
    op.execute("""
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
                SET quantity_in_use = quantity_in_use
                    - OLD.quantity_used + NEW.quantity_used
                WHERE id = NEW.accessory_id;
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    op.execute(
        "CREATE TRIGGER update_accessory_stock_trigger"
        " AFTER INSERT OR UPDATE OR DELETE ON item_accessories"
        " FOR EACH ROW EXECUTE FUNCTION update_accessory_stock()"
    )

    # --- Trigger: search vector ---
    op.execute("""
        CREATE OR REPLACE FUNCTION catalog_items_search_vector_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.subtitle, '')), 'B') ||
                setweight(to_tsvector('spanish',
                    COALESCE(array_to_string(
                        NEW.alternate_titles, ' '), '')), 'B') ||
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.description, '')), 'C') ||
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.variation, '')), 'B') ||
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.manufacturer, '')), 'B') ||
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.publisher, '')), 'B') ||
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.developer, '')), 'C') ||
                setweight(to_tsvector('spanish',
                    COALESCE(NEW.brand, '')), 'C') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.subtitle, '')), 'B') ||
                setweight(to_tsvector('english',
                    COALESCE(array_to_string(
                        NEW.alternate_titles, ' '), '')), 'B') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.description, '')), 'C') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.variation, '')), 'B') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.manufacturer, '')), 'B') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.publisher, '')), 'B') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.developer, '')), 'C') ||
                setweight(to_tsvector('english',
                    COALESCE(NEW.brand, '')), 'C');
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    op.execute(
        "CREATE TRIGGER catalog_items_search_vector_trigger"
        " BEFORE INSERT OR UPDATE ON catalog_items"
        " FOR EACH ROW"
        " EXECUTE FUNCTION catalog_items_search_vector_update()"
    )

    # --- Views ---
    op.execute("""
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
        JOIN sub_categories sc
            ON cat_catalog.sub_category_id = sc.id
        JOIN main_categories mc ON sc.main_category_id = mc.id
        LEFT JOIN suppliers s ON ci.supplier_id = s.id
    """)

    op.execute("""
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
            SUM(ci.current_market_value)
                - SUM(ci.purchase_price) as value_gain
        FROM collections c
        LEFT JOIN collection_items ci ON c.id = ci.collection_id
        LEFT JOIN catalog_items cat
            ON ci.catalog_item_id = cat.id
        LEFT JOIN catalogs catlog ON cat.catalog_id = catlog.id
        LEFT JOIN sub_categories sc
            ON catlog.sub_category_id = sc.id
        LEFT JOIN main_categories mc
            ON sc.main_category_id = mc.id
        GROUP BY c.id, mc.id, sc.id
        ORDER BY c.name, mc.name, sc.name
    """)

    op.execute("""
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
            COUNT(CASE WHEN ws.is_available THEN 1 END)
                as available_sightings
        FROM wishlist_items wi
        JOIN catalog_items cat ON wi.catalog_item_id = cat.id
        JOIN collections c ON wi.collection_id = c.id
        LEFT JOIN wishlist_sightings ws
            ON wi.id = ws.wishlist_item_id
        WHERE wi.is_active = true AND wi.is_acquired = false
        GROUP BY wi.id, cat.id, c.id
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_collection_stats AS
        SELECT
            c.id,
            c.name,
            c.collection_type,
            c.theme,
            c.restricted_to_sub_category_id,
            sc.name as restricted_subcategory_name,
            COUNT(ci.id) as total_items,
            COUNT(DISTINCT cat_catalog.sub_category_id)
                as different_categories_count,
            SUM(ci.purchase_price) as total_invested,
            SUM(ci.current_market_value) as current_value,
            SUM(ci.current_market_value)
                - SUM(ci.purchase_price) as value_gain,
            CASE
                WHEN SUM(ci.purchase_price) > 0
                THEN (
                    (SUM(ci.current_market_value)
                     - SUM(ci.purchase_price))
                    / SUM(ci.purchase_price) * 100
                )
                ELSE 0
            END as roi_percentage,
            COUNT(CASE WHEN ci.is_complete THEN 1 END)
                as complete_items,
            COUNT(CASE WHEN ci.is_graded THEN 1 END)
                as graded_items
        FROM collections c
        LEFT JOIN collection_items ci ON c.id = ci.collection_id
        LEFT JOIN catalog_items cat
            ON ci.catalog_item_id = cat.id
        LEFT JOIN catalogs cat_catalog
            ON cat.catalog_id = cat_catalog.id
        LEFT JOIN sub_categories sc
            ON c.restricted_to_sub_category_id = sc.id
        GROUP BY c.id, sc.name
    """)


def downgrade() -> None:
    """Drop all views, triggers, functions, and tables in reverse order."""

    # Views
    op.execute("DROP VIEW IF EXISTS v_collection_stats CASCADE")
    op.execute(
        "DROP VIEW IF EXISTS v_wishlist_with_avg_price CASCADE"
    )
    op.execute(
        "DROP VIEW IF EXISTS v_collection_items_by_category CASCADE"
    )
    op.execute(
        "DROP VIEW IF EXISTS v_collection_items_full CASCADE"
    )

    # Triggers (dropped automatically with tables, but explicit for clarity)
    op.execute(
        "DROP TRIGGER IF EXISTS"
        " catalog_items_search_vector_trigger ON catalog_items"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS"
        " update_accessory_stock_trigger ON item_accessories"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS"
        " update_catalog_items_count ON catalog_items"
    )

    _tables_with_updated_at = [
        "accessories_stock",
        "wishlist_items",
        "item_components",
        "collection_items",
        "collections",
        "catalog_items",
        "catalogs",
        "suppliers",
        "sub_categories",
        "main_categories",
    ]
    for table in _tables_with_updated_at:
        op.execute(
            f"DROP TRIGGER IF EXISTS update_{table}_updated_at"
            f" ON {table}"
        )

    # Functions
    op.execute(
        "DROP FUNCTION IF EXISTS"
        " catalog_items_search_vector_update() CASCADE"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS update_accessory_stock() CASCADE"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS"
        " update_catalog_total_items() CASCADE"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS"
        " update_updated_at_column() CASCADE"
    )

    # Tables in reverse dependency order
    op.execute("DROP TABLE IF EXISTS item_accessories CASCADE")
    op.execute("DROP TABLE IF EXISTS accessories_stock CASCADE")
    op.execute("DROP TABLE IF EXISTS wishlist_sightings CASCADE")
    op.execute("DROP TABLE IF EXISTS wishlist_items CASCADE")
    op.execute("DROP TABLE IF EXISTS item_transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS item_images CASCADE")
    op.execute("DROP TABLE IF EXISTS item_components CASCADE")
    op.execute("DROP TABLE IF EXISTS collection_items CASCADE")
    op.execute("DROP TABLE IF EXISTS collections CASCADE")
    op.execute("DROP TABLE IF EXISTS catalog_price_history CASCADE")
    op.execute("DROP TABLE IF EXISTS catalog_items CASCADE")
    op.execute("DROP TABLE IF EXISTS catalogs CASCADE")
    op.execute("DROP TABLE IF EXISTS standard_components CASCADE")
    op.execute("DROP TABLE IF EXISTS category_field_schemas CASCADE")
    op.execute("DROP TABLE IF EXISTS sub_categories CASCADE")
    op.execute("DROP TABLE IF EXISTS main_categories CASCADE")
    op.execute("DROP TABLE IF EXISTS suppliers CASCADE")

    # Extensions
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
