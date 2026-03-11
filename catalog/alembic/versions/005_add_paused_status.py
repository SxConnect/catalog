"""add paused status to catalog enum

Revision ID: 005
Revises: 004
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar o valor 'paused' ao enum catalogstatus
    op.execute("ALTER TYPE catalogstatus ADD VALUE 'paused'")


def downgrade() -> None:
    # Não é possível remover valores de enum no PostgreSQL
    # Em caso de rollback, seria necessário recriar o enum
    pass