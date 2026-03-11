"""initial schema with full-text search

Revision ID: 001
Revises: 
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent')
    
    # Create catalogs table
    op.create_table(
        'catalogs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=True),
        sa.Column('status', sa.Enum('uploaded', 'processing', 'completed', 'failed', name='catalogstatus'), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('processed_pages', sa.Integer(), nullable=True),
        sa.Column('products_found', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_catalogs_id', 'catalogs', ['id'])
    
    # Create ai_api_keys table
    op.create_table(
        'ai_api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(500), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('daily_limit', sa.Integer(), nullable=True),
        sa.Column('used_today', sa.Integer(), nullable=True),
        sa.Column('status', sa.Boolean(), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('ix_ai_api_keys_id', 'ai_api_keys', ['id'])
    
    # Create products_catalog table
    op.create_table(
        'products_catalog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ean', sa.String(50), nullable=True),
        sa.Column('name', sa.String(500), nullable=True),
        sa.Column('brand', sa.String(200), nullable=True),
        sa.Column('category', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('attributes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_catalog', sa.String(200), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('full_text', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ean')
    )
    
    # Create indexes
    op.create_index('ix_products_catalog_id', 'products_catalog', ['id'])
    op.create_index('ix_products_catalog_ean', 'products_catalog', ['ean'])
    op.create_index('ix_products_catalog_name', 'products_catalog', ['name'])
    op.create_index('ix_products_catalog_brand', 'products_catalog', ['brand'])
    op.create_index('ix_products_catalog_category', 'products_catalog', ['category'])
    
    # Composite indexes
    op.create_index('idx_product_search', 'products_catalog', ['name', 'brand', 'category'])
    op.create_index('idx_product_ean_brand', 'products_catalog', ['ean', 'brand'])
    
    # GIN indexes for full-text search
    op.create_index(
        'idx_product_full_text',
        'products_catalog',
        ['full_text'],
        postgresql_using='gin'
    )
    
    # Trigram indexes for fuzzy search
    op.create_index(
        'idx_product_name_trgm',
        'products_catalog',
        ['name'],
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'}
    )
    
    op.create_index(
        'idx_product_brand_trgm',
        'products_catalog',
        ['brand'],
        postgresql_using='gin',
        postgresql_ops={'brand': 'gin_trgm_ops'}
    )
    
    # Create trigger for automatic full_text update
    op.execute("""
        CREATE OR REPLACE FUNCTION products_catalog_full_text_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.full_text := 
                setweight(to_tsvector('portuguese', COALESCE(NEW.name, '')), 'A') ||
                setweight(to_tsvector('portuguese', COALESCE(NEW.brand, '')), 'B') ||
                setweight(to_tsvector('portuguese', COALESCE(NEW.category, '')), 'C') ||
                setweight(to_tsvector('portuguese', COALESCE(NEW.description, '')), 'D');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER products_catalog_full_text_update
        BEFORE INSERT OR UPDATE ON products_catalog
        FOR EACH ROW EXECUTE FUNCTION products_catalog_full_text_trigger();
    """)


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS products_catalog_full_text_update ON products_catalog')
    op.execute('DROP FUNCTION IF EXISTS products_catalog_full_text_trigger()')
    
    op.drop_index('idx_product_brand_trgm', table_name='products_catalog')
    op.drop_index('idx_product_name_trgm', table_name='products_catalog')
    op.drop_index('idx_product_full_text', table_name='products_catalog')
    op.drop_index('idx_product_ean_brand', table_name='products_catalog')
    op.drop_index('idx_product_search', table_name='products_catalog')
    
    op.drop_table('products_catalog')
    op.drop_table('ai_api_keys')
    op.drop_table('catalogs')
    
    op.execute('DROP EXTENSION IF EXISTS unaccent')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
