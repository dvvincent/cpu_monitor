"""
Database connection and operations for SystemPulse.
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from .models import Base, SystemMetrics

class Database:
    def __init__(self, connection_url: str):
        self.engine = create_async_engine(
            connection_url,
            echo=True,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Initialize the database and create TimescaleDB hypertable."""
        async with self.engine.begin() as conn:
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            
            try:
                # Convert to TimescaleDB hypertable
                await conn.execute(
                    text("""
                    SELECT create_hypertable(
                        'system_metrics',
                        'timestamp',
                        if_not_exists => TRUE
                    );
                    """)
                )
                
                # Set retention policy (30 days)
                await conn.execute(
                    text("""
                    SELECT add_retention_policy(
                        'system_metrics',
                        INTERVAL '30 days',
                        if_not_exists => TRUE
                    );
                    """)
                )
                
                # Create time-bucket views for different intervals
                for interval in ['1 minute', '5 minutes', '1 hour']:
                    await conn.execute(
                        text(f"""
                        CREATE MATERIALIZED VIEW IF NOT EXISTS system_metrics_{interval.replace(' ', '_')} AS
                        SELECT
                            time_bucket('{interval}', timestamp) AS bucket,
                            avg(cpu_percent) as cpu_percent_avg,
                            avg(memory_percent) as memory_percent_avg,
                            avg(disk_percent) as disk_percent_avg,
                            avg(temperature) as temperature_avg,
                            avg(network_send_rate) as network_send_rate_avg,
                            avg(network_recv_rate) as network_recv_rate_avg
                        FROM system_metrics
                        GROUP BY bucket
                        ORDER BY bucket DESC;
                        """)
                    )
                
                logging.info("TimescaleDB setup completed successfully")
            except Exception as e:
                logging.error(f"Error setting up TimescaleDB: {e}")
                raise

    async def store_metrics(self, metrics: SystemMetrics):
        """Store system metrics in the database."""
        async with self.async_session() as session:
            session.add(metrics)
            await session.commit()

    async def get_metrics(self, interval: str = '5 minutes', limit: int = 100):
        """Retrieve metrics for a specific time interval."""
        async with self.async_session() as session:
            result = await session.execute(
                text(f"""
                SELECT * FROM system_metrics_{interval.replace(' ', '_')}
                ORDER BY bucket DESC
                LIMIT :limit
                """),
                {'limit': limit}
            )
            return result.fetchall()

    async def cleanup_old_data(self):
        """Manual cleanup of old data (if needed)."""
        async with self.async_session() as session:
            await session.execute(
                text("""
                SELECT remove_retention_policy('system_metrics');
                SELECT add_retention_policy('system_metrics', INTERVAL '30 days');
                """)
            )
            await session.commit()
