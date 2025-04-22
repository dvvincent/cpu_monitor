-- Enable compression on system_metrics table
ALTER TABLE system_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'hostname',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Set compression policy to compress chunks older than 1 hour
SELECT add_compression_policy('system_metrics', INTERVAL '1 hour');

-- Compress existing chunks that are older than 1 hour
SELECT compress_chunk(i) 
FROM show_chunks('system_metrics', older_than => INTERVAL '1 hour') i;
