"""add cms fields to servers table

Revision ID: add_cms_fields_to_servers_table
Revises: 
Create Date: 2026-05-04 22:57:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cms_fields_to_servers_table'
down_revision = '20260415_0002'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to servers table
    op.add_column('servers', sa.Column('port', sa.Integer(), nullable=False, server_default='8443'))
    op.add_column('servers', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('servers', sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('servers', sa.Column('connection_status', sa.String(length=20), nullable=False, server_default='disconnected'))
    op.add_column('servers', sa.Column('last_connection_test', sa.DateTime(timezone=True), nullable=True))
    op.add_column('servers', sa.Column('connection_error', sa.Text(), nullable=True))
    op.add_column('servers', sa.Column('server_version', sa.String(length=50), nullable=True))
    op.add_column('servers', sa.Column('system_info', sa.Text(), nullable=True))
    op.add_column('servers', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes for new fields
    op.create_index('ix_servers_port', 'servers', ['port'], unique=False)
    op.create_index('ix_servers_is_active', 'servers', ['is_active'], unique=False)
    op.create_index('ix_servers_is_primary', 'servers', ['is_primary'], unique=False)
    op.create_index('ix_servers_connection_status', 'servers', ['connection_status'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_servers_port', table_name='servers')
    op.drop_index('ix_servers_is_active', table_name='servers')
    op.drop_index('ix_servers_is_primary', table_name='servers')
    op.drop_index('ix_servers_connection_status', table_name='servers')
    
    # Drop columns
    op.drop_column('servers', 'updated_at')
    op.drop_column('servers', 'system_info')
    op.drop_column('servers', 'server_version')
    op.drop_column('servers', 'connection_error')
    op.drop_column('servers', 'last_connection_test')
    op.drop_column('servers', 'connection_status')
    op.drop_column('servers', 'is_primary')
    op.drop_column('servers', 'is_active')
    op.drop_column('servers', 'port')
