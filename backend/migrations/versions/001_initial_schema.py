"""Initial database schema: users, provider_connections, file_metadata, search_history

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-24 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Provider connections table
    op.create_table(
        'provider_connections',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('account_identifier', sa.String(length=255), nullable=True),
        sa.Column('encrypted_access_token', sa.Text(), nullable=True),
        sa.Column('encrypted_refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='connected'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_provider_connections_user_id', 'provider_connections', ['user_id'])
    op.create_index('ix_provider_connections_provider', 'provider_connections', ['provider'])

    # File metadata table
    op.create_table(
        'file_metadata',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_file_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.Text(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('extension', sa.String(length=20), nullable=True),
        sa.Column('size', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('web_url', sa.Text(), nullable=True),
        sa.Column('downloadable', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_folder', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_file_metadata_user_id', 'file_metadata', ['user_id'])
    op.create_index('ix_file_metadata_provider', 'file_metadata', ['provider'])
    op.create_index('ix_file_metadata_name', 'file_metadata', ['name'])
    op.create_index('ix_file_metadata_content_hash', 'file_metadata', ['content_hash'])

    # Search history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('intent_summary', sa.Text(), nullable=True),
        sa.Column('number_of_results', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])


def downgrade() -> None:
    op.drop_table('search_history')
    op.drop_table('file_metadata')
    op.drop_table('provider_connections')
    op.drop_table('users')
