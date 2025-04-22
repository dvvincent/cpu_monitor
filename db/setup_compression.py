import asyncio
import asyncpg
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_compression():
    # Connect using the same credentials as the main app
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/systempulse')
    
    try:
        # Check if TimescaleDB extension is enabled
        logger.info("Checking TimescaleDB status...")
        is_timescaledb = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_extension WHERE extname = 'timescaledb';
        """)
        
        if not is_timescaledb:
            logger.error("TimescaleDB extension is not enabled in this database")
            return
        
        # Check if system_metrics is a hypertable
        logger.info("Checking if system_metrics is a hypertable...")
        is_hypertable = await conn.fetchval("""
            SELECT COUNT(*) FROM _timescaledb_catalog.hypertable
            WHERE table_name = 'system_metrics';
        """)
        
        if not is_hypertable:
            logger.info("Converting system_metrics to a hypertable...")
            await conn.execute("""
                SELECT create_hypertable('system_metrics', 'timestamp',
                    if_not_exists => TRUE,
                    migrate_data => TRUE
                );
            """)
        
        # Enable compression
        logger.info("\nEnabling compression on system_metrics table...")
        try:
            await conn.execute("""
                ALTER TABLE system_metrics SET (
                    timescaledb.compress,
                    timescaledb.compress_orderby = 'timestamp DESC'
                );
            """)
            logger.info("Compression enabled successfully")
        except Exception as e:
            if 'already compressed' in str(e).lower():
                logger.info("Table is already compressed")
            else:
                raise
        
        # Get table size before compression
        logger.info("\nChecking table size before compression...")
        size_before = await conn.fetchrow("""
            SELECT 
                pg_size_pretty(pg_total_relation_size('system_metrics')) as pretty_size,
                pg_total_relation_size('system_metrics') as bytes
            ;
        """)
        logger.info(f"Current table size: {size_before['pretty_size']}")
        
        # Add compression policy
        logger.info("\nSetting up compression policy...")
        try:
            await conn.execute("""
                SELECT add_compression_policy('system_metrics', INTERVAL '1 hour');
            """)
            logger.info("Compression policy added successfully")
        except Exception as e:
            if 'already exists' in str(e).lower():
                logger.info("Compression policy already exists")
            else:
                raise
        
        # Compress existing chunks
        logger.info("\nCompressing existing chunks...")
        try:
            await conn.execute("""
                SELECT compress_chunk(i, if_not_compressed => true)
                FROM (SELECT show_chunks('system_metrics', older_than => INTERVAL '1 hour')) as s(i);
            """)
            logger.info("Existing chunks compressed successfully")
        except Exception as e:
            if 'no chunks for compression' in str(e).lower():
                logger.info("No chunks found that need compression")
            else:
                raise
        
        # Get table size after compression
        logger.info("\nChecking table size after compression...")
        size_after = await conn.fetchrow("""
            SELECT 
                pg_size_pretty(pg_total_relation_size('system_metrics')) as pretty_size,
                pg_total_relation_size('system_metrics') as bytes
            ;
        """)
        logger.info(f"Final table size: {size_after['pretty_size']}")
        
        # Calculate savings
        if size_before['bytes'] > 0:
            savings = (1 - size_after['bytes']/size_before['bytes']) * 100
            logger.info(f"Space savings: {savings:.1f}%")
        
        # Show compression settings
        logger.info("\nCompression settings:")
        settings = await conn.fetch("""
            SELECT 
                format('%I.%I', schema_name, table_name) as table_name,
                compression_state,
                compress_orderby,
                compress_segmentby
            FROM _timescaledb_catalog.hypertable
            WHERE table_name = 'system_metrics';
        """)
        for setting in settings:
            logger.info(f"Table: {setting['table_name']}")
            logger.info(f"Compression state: {setting['compression_state']}")
            logger.info(f"Order by: {setting['compress_orderby']}")
            logger.info(f"Segment by: {setting['compress_segmentby'] or 'None'}")
        
    except Exception as e:
        logger.error(f"Error setting up compression: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_compression())
