import os
import time
import asyncio
from datetime import datetime
import psutil
import logging
import yaml
from pathlib import Path
from aiohttp import web
import socketio
from jinja2 import Environment, FileSystemLoader
from db.database import Database
from db.models import SystemMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
def load_config():
    # Default configuration
    default_config = {
        'server': {
            'host': '0.0.0.0',
            'http': {'enabled': True, 'port': 3000},
            'https': {
                'enabled': True,
                'port': 3443,
                'certificates': {
                    'cert_file': 'ssl/cert.pem',
                    'key_file': 'ssl/key.pem',
                    'validity_days': 365
                }
            }
        },
        'monitoring': {
            'update_interval': 1.0,
            'metrics': {
                'cpu': True,
                'memory': True,
                'disk': True,
                'network': True,
                'processes': True
            }
        },
        'security': {
            'enable_cors': False,
            'cors_origins': ['*'],
            'secret_key': 'default-insecure-secret-key'
        }
    }
    
    # Try to load user config
    config_path = Path('config.yaml')
    if config_path.exists():
        try:
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                # Deep merge user config with defaults
                def merge_dicts(default, override):
                    for key, value in override.items():
                        if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                            merge_dicts(default[key], value)
                        else:
                            default[key] = value
                merge_dicts(default_config, user_config)
        except Exception as e:
            logging.warning(f"Error loading config.yaml: {e}. Using default configuration.")
    else:
        logging.info("No config.yaml found. Using default configuration.")
    
    return default_config

# Load configuration
config = load_config()

# Initialize database
db_url = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/systempulse')
db = Database(db_url)

# Set up Jinja2 templates
env = Environment(loader=FileSystemLoader('templates'))

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='aiohttp',
    cors_allowed_origins=config['security']['cors_origins'] if config['security']['enable_cors'] else []
)

# Create aiohttp web application
app = web.Application()
sio.attach(app)

# Monitoring interval (seconds)
MONITOR_INTERVAL = float(config['monitoring']['update_interval'])

# Data fetching
_last_net = psutil.net_io_counters()

def get_cpu_info():
    try:
        # Get CPU percent and load average
        load_1, load_5, load_15 = os.getloadavg()
        freq = psutil.cpu_freq()
        return {
            'percent': psutil.cpu_percent(interval=None),
            'load_1': round(load_1, 2),
            'load_5': round(load_5, 2),
            'load_15': round(load_15, 2),
            'cpu_freq_current': freq.current if freq else 0,
            'cpu_freq_min': freq.min if freq else 0,
            'cpu_freq_max': freq.max if freq else 0
        }
    except Exception as e:
        logging.error(f"CPU info error: {e}")
        return {
            'percent': 0, 'load_1': 0, 'load_5': 0, 'load_15': 0,
            'cpu_freq_current': 0, 'cpu_freq_min': 0, 'cpu_freq_max': 0,
            'error': str(e)
        }


def get_memory_info():
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'memory_total': mem.total,
            'memory_used': mem.used,
            'memory_available': mem.available,
            'memory_percent': mem.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_free': swap.free,
            'swap_percent': swap.percent
        }
    except Exception as e:
        logging.error(f"Memory info error: {e}")
        return {
            'memory_total': 0, 'memory_used': 0, 'memory_available': 0, 'memory_percent': 0,
            'swap_total': 0, 'swap_used': 0, 'swap_free': 0, 'swap_percent': 0,
            'error': str(e)
        }


def get_disk_info():
    parts = []
    try:
        for p in psutil.disk_partitions():
            if p.fstype:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    parts.append({
                        'device': p.device,
                        'mountpoint': p.mountpoint,
                        'total': usage.total,  # Return raw bytes
                        'used': usage.used,    # Return raw bytes
                        'free': usage.free,    # Return raw bytes
                        'percent': usage.percent
                    })
                except OSError as e:
                    logging.warning(f"Could not get usage for {p.mountpoint}: {e}")
    except Exception as e:
        logging.error(f"Disk info error: {e}")
    return parts


def get_system_time_info():
    try:
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # Convert boot time to readable format
        boot_datetime = datetime.fromtimestamp(boot_time)
        
        # Format uptime
        days = int(uptime // (24 * 3600))
        uptime = uptime % (24 * 3600)
        hours = int(uptime // 3600)
        uptime %= 3600
        minutes = int(uptime // 60)
        seconds = int(uptime % 60)
        
        uptime_str = ''
        if days > 0:
            uptime_str += f"{days}d "
        uptime_str += f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return {
            'boot_time': boot_datetime, # Return the datetime object
            'uptime': uptime_str
        }
    except Exception as e:
        logging.error(f"System time info error: {e}")
        return {'boot_time': None, 'uptime': 'N/A'} # Return None for boot_time on error


def get_temperature_info():
    try:
        temps = psutil.sensors_temperatures()
        result = []
        for name, entries in temps.items():
            for entry in entries:
                result.append({
                    'name': f"{name}: {entry.label}" if entry.label else name,
                    'current': round(entry.current, 1),
                    'high': round(entry.high, 1) if entry.high is not None else None,
                    'critical': round(entry.critical, 1) if entry.critical is not None else None
                })
        return result
    except Exception as e:
        logging.error(f"Temperature info error: {e}")
        return []


def get_network_info():
    global _last_net
    try:
        current = psutil.net_io_counters()
        sent = current.bytes_sent - _last_net.bytes_sent
        recv = current.bytes_recv - _last_net.bytes_recv
        _last_net = current
        # Calculate rates in Mbps (Megabits per second)
        send_rate = (sent * 8) / (MONITOR_INTERVAL * (1024**2))
        recv_rate = (recv * 8) / (MONITOR_INTERVAL * (1024**2))
        return {
            'bytes_sent_total': current.bytes_sent, # Return raw bytes
            'bytes_recv_total': current.bytes_recv, # Return raw bytes
            'send_rate_mbps': send_rate,           # Return raw Mbps
            'recv_rate_mbps': recv_rate           # Return raw Mbps
        }
    except Exception as e:
        logging.error(f"Network info error: {e}")
        return {'bytes_sent_total': 0, 'bytes_recv_total': 0, 'send_rate_mbps': 0, 'recv_rate_mbps': 0, 'error': str(e)}


async def background_monitor(sid):
    logging.info(f"Background monitor started for {sid} (interval={MONITOR_INTERVAL}s)")
    await asyncio.sleep(0.1)
    current_process = psutil.Process(os.getpid()) # Get current process
    while True:
        try:
            # Collect metrics
            cpu_info = get_cpu_info()
            memory_info = get_memory_info()
            disk_info = get_disk_info()
            network_info = get_network_info()
            temp_info = get_temperature_info()
            time_info = get_system_time_info()
            
            # Create metrics object for database
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_info['percent'],
                cpu_freq_current=cpu_info['cpu_freq_current'],
                cpu_freq_min=cpu_info['cpu_freq_min'],
                cpu_freq_max=cpu_info['cpu_freq_max'],
                memory_total=memory_info['memory_total'],
                memory_available=memory_info['memory_available'],
                memory_used=memory_info['memory_used'],
                memory_percent=memory_info['memory_percent'],
                swap_total=memory_info['swap_total'],
                swap_used=memory_info['swap_used'],
                swap_free=memory_info['swap_free'],
                swap_percent=memory_info['swap_percent'],
                disk_total=disk_info[0]['total'] if disk_info else 0,
                disk_used=disk_info[0]['used'] if disk_info else 0,
                disk_free=disk_info[0]['free'] if disk_info else 0, # Use the 'free' value directly
                disk_percent=disk_info[0]['percent'] if disk_info else 0,
                network_bytes_sent=network_info['bytes_sent_total'],
                network_bytes_recv=network_info['bytes_recv_total'],
                network_send_rate=network_info['send_rate_mbps'],
                network_recv_rate=network_info['recv_rate_mbps'],
                temperature=temp_info[0]['current'] if temp_info else 0,
                boot_time=time_info['boot_time'],
                hostname=os.uname().nodename
            )
            
            # Store in database
            await db.store_metrics(metrics)
            
            # Prepare data for client emission (convert datetime)
            time_info_for_client = time_info.copy()
            if isinstance(time_info_for_client.get('boot_time'), datetime):
                time_info_for_client['boot_time'] = time_info_for_client['boot_time'].isoformat() # Convert to ISO string
            
            # Emit to client
            data = {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'temperature': temp_info,
                'system_time': time_info_for_client # Use the modified copy
            }
            
            # Log own memory usage
            mem_info = current_process.memory_info()
            rss_mb = mem_info.rss / (1024 * 1024) # Convert bytes to MB
            logging.info(f"Process Memory Usage (PID: {current_process.pid}): {rss_mb:.2f} MB RSS")
            
            await sio.emit('system_update', data, room=sid)
            
            await asyncio.sleep(MONITOR_INTERVAL)
        except Exception as e:
            logging.error(f"Error in background monitor: {e}")
            break


# Routes
async def index(request):
    template = env.get_template('index.html')
    html = template.render()
    return web.Response(text=html, content_type='text/html')


async def api_system_info(request):
    try:
        import platform
        info = {
            'os': f"{platform.system()} {platform.release()}",
            'hostname': platform.node(),
            'cpu_model': platform.processor(),
            'cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
            'python_version': platform.python_version()
        }
        return web.json_response(info)
    except Exception as e:
        logging.error(f"Static info error: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_metrics_history(request):
    """Get historical metrics data with optional time range and aggregation."""
    try:
        # Get query parameters
        interval = request.query.get('interval', '5 minutes')
        limit = int(request.query.get('limit', '100'))
        
        # Validate interval
        valid_intervals = ['1 minute', '5 minutes', '1 hour']
        if interval not in valid_intervals:
            return web.json_response(
                {'error': f'Invalid interval. Must be one of: {valid_intervals}'}, 
                status=400
            )
        
        # Get metrics from database
        metrics = await db.get_metrics(interval, limit)
        
        # Format response
        response = {
            'interval': interval,
            'data_points': len(metrics),
            'metrics': [{
                'timestamp': row.bucket.isoformat(),
                'cpu_percent': row.cpu_percent_avg,
                'memory_percent': row.memory_percent_avg,
                'disk_percent': row.disk_percent_avg,
                'swap_percent': row.swap_percent_avg, # Added swap percent
                'temperature': row.temperature_avg,
                'network_send_rate': row.network_send_rate_avg,
                'network_recv_rate': row.network_recv_rate_avg
            } for row in metrics]
        }
        
        return web.json_response(response)
    except Exception as e:
        logging.error(f"Error getting metrics history: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_metrics_summary(request):
    """Get a summary of system metrics over different time periods."""
    try:
        summaries = {}
        for interval in ['1 minute', '5 minutes', '1 hour']:
            metrics = await db.get_metrics(interval, 1)
            if metrics and len(metrics) > 0:
                latest = metrics[0]
                summaries[interval.replace(' ', '_')] = {
                    'timestamp': latest.bucket.isoformat(),
                    'cpu_percent': latest.cpu_percent_avg,
                    'memory_percent': latest.memory_percent_avg,
                    'disk_percent': latest.disk_percent_avg,
                    'temperature': latest.temperature_avg,
                    'network_send_rate': latest.network_send_rate_avg,
                    'network_recv_rate': latest.network_recv_rate_avg
                }
        
        return web.json_response({
            'summaries': summaries,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting metrics summary: {e}")
        return web.json_response({'error': str(e)}, status=500)


# Socket events
@sio.event
async def connect(sid, environ):
    logging.info(f'Client connected: {sid}')
    asyncio.create_task(background_monitor(sid))
    await sio.emit('connection_ack', {'message': 'Connected'}, room=sid)


@sio.event
async def disconnect(sid):
    logging.info(f'Client disconnected: {sid}')


async def main():
    host = config['server']['host']
    
    # Initialize database
    try:
        await db.init_db()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        return
    
    # Set up routes
    app.router.add_get('/', index)
    app.router.add_get('/api/system_info', api_system_info)
    app.router.add_get('/api/metrics/history', get_metrics_history)
    app.router.add_get('/api/metrics/summary', get_metrics_summary)
    
    if config['server']['https']['enabled']:
        # HTTPS server
        cert_file = config['server']['https']['certificates']['cert_file']
        key_file = config['server']['https']['certificates']['key_file']
        https_port = config['server']['https']['port']
        
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            logging.error("SSL certificates not found. Cannot start HTTPS server.")
            exit(1)
        
        import ssl
        logging.info(f"Starting HTTPS server at https://{host}:{https_port}")
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_file, key_file)
        
        # Run the server with SSL
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            host,
            https_port,
            ssl_context=context
        )
        await site.start()
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)
    
    elif config['server']['http']['enabled']:
        # HTTP server
        http_port = config['server']['http']['port']
        logging.info(f"Starting HTTP server at http://{host}:{http_port}")
        
        # Run the server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            host,
            http_port
        )
        await site.start()
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)
    
    else:
        logging.error("Neither HTTP nor HTTPS is enabled. At least one must be enabled.")
        exit(1)

if __name__ == '__main__':
    asyncio.run(main())
