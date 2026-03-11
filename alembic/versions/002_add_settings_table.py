"""add settings table

Revision ID: 002
Revises: 001
Create Date: 2026-03-08

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(20), nullable=False, server_default='string'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('ix_settings_id', 'settings', ['id'])
    op.create_index('ix_settings_key', 'settings', ['key'])
    
    # Insert default settings
    op.execute("""
        INSERT INTO settings (key, value, value_type, description) VALUES
        ('groq_api_keys', '', 'string', 'Chaves de API Groq separadas por vírgula'),
        ('extractions_per_second', '10', 'int', 'Número de extrações por segundo no scraping'),
        ('scraping_url', '', 'string', 'URL base para web scraping'),
        ('scraping_enabled', 'false', 'bool', 'Habilitar web scraping automático'),
        ('max_concurrent_catalogs', '4', 'int', 'Número máximo de catálogos processados simultaneamente'),
        ('enable_deduplication', 'true', 'bool', 'Habilitar deduplicação automática'),
        ('similarity_threshold', '0.85', 'float', 'Limite de similaridade para deduplicação')
    """)


def downgrade() -> None:
    op.drop_index('ix_settings_key', table_name='settings')
    op.drop_index('ix_settings_id', table_name='settings')
    op.drop_table('settings')
