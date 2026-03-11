"""fix catalog status enum

Revision ID: 003
Revises: 002
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alterar o tipo da coluna temporariamente para text
    op.execute("ALTER TABLE catalogs ALTER COLUMN status TYPE text")
    
    # Dropar o enum antigo
    op.execute("DROP TYPE IF EXISTS catalogstatus")
    
    # Recriar o enum com valores corretos
    op.execute("CREATE TYPE catalogstatus AS ENUM ('uploaded', 'processing', 'completed', 'failed')")
    
    # Converter valores existentes para minúsculo
    op.execute("UPDATE catalogs SET status = LOWER(status)")
    
    # Alterar a coluna de volta para o enum
    op.execute("ALTER TABLE catalogs ALTER COLUMN status TYPE catalogstatus USING status::catalogstatus")
    
    # Definir default
    op.execute("ALTER TABLE catalogs ALTER COLUMN status SET DEFAULT 'uploaded'")


def downgrade() -> None:
    op.execute("ALTER TABLE catalogs ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE catalogs ALTER COLUMN status TYPE text")
    op.execute("DROP TYPE IF EXISTS catalogstatus")
    op.execute("CREATE TYPE catalogstatus AS ENUM ('uploaded', 'processing', 'completed', 'failed')")
    op.execute("ALTER TABLE catalogs ALTER COLUMN status TYPE catalogstatus USING status::catalogstatus")
