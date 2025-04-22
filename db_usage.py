import asyncio
import asyncpg
from datetime import datetime, timedelta

async def check_database_usage():
    # Connect using the same credentials as the main app
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/systempulse')
    
    try:
        # Get database size
        db_size = await conn.fetchrow("""
            SELECT pg_size_pretty(pg_database_size('systempulse')) as size,
                   pg_database_size('systempulse') as bytes
        """)
        
        # Get table sizes and row counts
        tables = await conn.fetch("""
            SELECT 
                relname as table_name,
                pg_size_pretty(pg_total_relation_size(C.oid)) as total_size,
                pg_size_pretty(pg_table_size(C.oid)) as table_size,
                pg_size_pretty(pg_indexes_size(C.oid)) as index_size,
                reltuples::bigint as row_estimate
            FROM pg_class C
            LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
            WHERE nspname NOT IN ('pg_catalog', 'information_schema')
                AND C.relkind = 'r'
            ORDER BY pg_total_relation_size(C.oid) DESC;
        """)
        
        # Get chunk information for TimescaleDB hypertables
        try:
            chunks = await conn.fetch("""
            SELECT 
                h.schema_name || '.' || h.table_name as hypertable,
                c.schema_name || '.' || c.table_name as chunk,
                pg_size_pretty(pg_total_relation_size(format('%I.%I', c.schema_name, c.table_name)::regclass)) as size,
                pg_total_relation_size(format('%I.%I', c.schema_name, c.table_name)::regclass) as bytes,
                _timescaledb_internal.to_timestamp(c.range_start) as range_start,
                _timescaledb_internal.to_timestamp(c.range_end) as range_end
            FROM _timescaledb_catalog.hypertable h
            JOIN _timescaledb_catalog.chunk c ON h.id = c.hypertable_id
            ORDER BY c.range_end DESC
            LIMIT 5;
            """)
        except Exception as e:
            print(f"Note: Could not fetch chunk information: {e}")
            chunks = []

        # Get compression status
        try:
            compression = await conn.fetch("""
            SELECT 
                schema_name || '.' || table_name as hypertable,
                CASE WHEN compression_state = 0 THEN 'Uncompressed' 
                     WHEN compression_state = 1 THEN 'Compressed'
                     ELSE 'Unknown' END as compression_status,
                pg_size_pretty(pg_total_relation_size(format('%I.%I', schema_name, table_name)::regclass)) as current_size
            FROM _timescaledb_catalog.hypertable
            WHERE compressed = true;
            """)
        except Exception as e:
            print(f"Note: Could not fetch compression information: {e}")
            compression = []

        # Print results
        print("\n=== Database Usage Report ===")
        print(f"Total Database Size: {db_size['size']}")
        
        print("\n=== Table Sizes ===")
        for table in tables:
            print(f"\nTable: {table['table_name']}")
            print(f"Total Size: {table['total_size']}")
            print(f"Table Size: {table['table_size']}")
            print(f"Index Size: {table['index_size']}")
            print(f"Estimated Rows: {table['row_estimate']:,}")
        
        print("\n=== Recent Chunks ===")
        for chunk in chunks:
            print(f"\nHypertable: {chunk['hypertable']}")
            print(f"Chunk: {chunk['chunk']}")
            print(f"Size: {chunk['size']}")
            print(f"Range: {chunk['range_start']} to {chunk['range_end']}")
        
        print("\n=== Compression Status ===")
        for stat in compression:
            print(f"\nHypertable: {stat['hypertable']}")
            print(f"Status: {stat['compression_status']}")
            print(f"Current Size: {stat['current_size']}")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_database_usage())
