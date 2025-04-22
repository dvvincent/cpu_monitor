"""Initial schema for SystemPulse

Revision ID: initial_schema
Create Date: 2025-04-21 23:07:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create extension for TimescaleDB
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE')
    
    # Create the system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('cpu_freq_current', sa.Float(), nullable=True),
        sa.Column('cpu_freq_min', sa.Float(), nullable=True),
        sa.Column('cpu_freq_max', sa.Float(), nullable=True),
        sa.Column('memory_total', sa.Float(), nullable=True),
        sa.Column('memory_available', sa.Float(), nullable=True),
        sa.Column('memory_used', sa.Float(), nullable=True),
        sa.Column('memory_percent', sa.Float(), nullable=True),
        sa.Column('swap_total', sa.Float(), nullable=True),
        sa.Column('swap_used', sa.Float(), nullable=True),
        sa.Column('swap_free', sa.Float(), nullable=True),
        sa.Column('swap_percent', sa.Float(), nullable=True),
        sa.Column('disk_total', sa.Float(), nullable=True),
        sa.Column('disk_used', sa.Float(), nullable=True),
        sa.Column('disk_free', sa.Float(), nullable=True),
        sa.Column('disk_percent', sa.Float(), nullable=True),
        sa.Column('network_bytes_sent', sa.Float(), nullable=True),
        sa.Column('network_bytes_recv', sa.Float(), nullable=True),
        sa.Column('network_send_rate', sa.Float(), nullable=True),
        sa.Column('network_recv_rate', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('boot_time', sa.DateTime(), nullable=True),
        sa.Column('hostname', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id', 'timestamp')
    )
    
    # Create indexes
    op.create_index('idx_system_metrics_timestamp', 'system_metrics', ['timestamp'])
    op.create_index('idx_system_metrics_hostname', 'system_metrics', ['hostname'])

def downgrade() -> None:
    op.drop_index('idx_system_metrics_hostname')
    op.drop_index('idx_system_metrics_timestamp')
    op.drop_table('system_metrics')
    op.execute('DROP EXTENSION IF EXISTS timescaledb')
