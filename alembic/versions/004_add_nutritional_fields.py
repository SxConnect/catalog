"""add nutritional fields to products

Revision ID: 004
Revises: 003
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar campos nutricionais à tabela products_catalog
    op.add_column('products_catalog', sa.Column('ingredients', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('products_catalog', sa.Column('nutritional_info', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Criar índice para busca por ingredientes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_ingredients_gin 
        ON products_catalog USING gin (ingredients)
    """)
    
    # Criar índice para informações nutricionais
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_nutrition_gin 
        ON products_catalog USING gin (nutritional_info)
    """)


def downgrade() -> None:
    # Remover índices
    op.execute("DROP INDEX IF EXISTS idx_product_nutrition_gin")
    op.execute("DROP INDEX IF EXISTS idx_product_ingredients_gin")
    
    # Remover colunas
    op.drop_column('products_catalog', 'nutritional_info')
    op.drop_column('products_catalog', 'ingredients')