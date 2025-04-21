import eventlet
# Patch sockets to work with eventlet
eventlet.monkey_patch()

import os
import time
from datetime import datetime
import psutil
import logging
import yaml
from pathlib import Path
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit

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

# Create Flask app and SocketIO
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = config['security']['secret_key']

# Configure Socket.IO
socketio = SocketIO(
    app,
    async_mode='threading',
    cors_allowed_origins=config['security']['cors_origins'] if config['security']['enable_cors'] else [],
    secure=config['server']['https']['enabled'],
    ssl_verify=False
)

# Monitoring interval (seconds)
MONITOR_INTERVAL = float(config['monitoring']['update_interval'])

# Data fetching
_last_net = psutil.net_io_counters()

def get_cpu_info():
    try:
        # Get CPU percent and load average
        load_1, load_5, load_15 = os.getloadavg()
        return {
            'percent': psutil.cpu_percent(interval=None),
            'load_1': round(load_1, 2),
            'load_5': round(load_5, 2),
            'load_15': round(load_15, 2)
        }
    except Exception as e:
        logging.error(f"CPU info error: {e}")
        return {'percent': 0, 'load_1': 0, 'load_5': 0, 'load_15': 0, 'error': str(e)}


def get_memory_info():
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total': f"{mem.total / (1024**3):.1f} GB",
            'used': f"{mem.used / (1024**3):.1f} GB",
            'percent': mem.percent,
            'swap_total': f"{swap.total / (1024**3):.1f} GB",
            'swap_used': f"{swap.used / (1024**3):.1f} GB",
            'swap_percent': swap.percent
        }
    except Exception as e:
        logging.error(f"Memory info error: {e}")
        return {'total': 'N/A', 'used': 'N/A', 'percent': 0, 'swap_total': 'N/A', 'swap_used': 'N/A', 'swap_percent': 0, 'error': str(e)}


def get_disk_info():
    parts = []
    try:
        for p in psutil.disk_partitions():
            if p.fstype:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    total = usage.total / (1024**3)
                    used = usage.used / (1024**3)
                    parts.append({'device': p.device, 'mountpoint': p.mountpoint, 'total': f"{total:.1f}", 'used': f"{used:.1f}", 'percent': usage.percent})
                except Exception:
                    continue
    except Exception as e:
        logging.error(f"Disk partitions error: {e}")
    return parts


def get_system_time_info():
    try:
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # Convert boot time to readable format
        boot_datetime = datetime.fromtimestamp(boot_time)
        boot_str = boot_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
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
            'boot_time': boot_str,
            'uptime': uptime_str
        }
    except Exception as e:
        logging.error(f"System time info error: {e}")
        return {'boot_time': 'N/A', 'uptime': 'N/A'}

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
        send_rate = sent * 8 / (MONITOR_INTERVAL * (1024**2))
        recv_rate = recv * 8 / (MONITOR_INTERVAL * (1024**2))
        return {
            'bytes_sent_total': f"{current.bytes_sent/(1024**3):.2f}",
            'bytes_recv_total': f"{current.bytes_recv/(1024**3):.2f}",
            'send_rate_mbps': f"{send_rate:.2f}",
            'recv_rate_mbps': f"{recv_rate:.2f}"}
    except Exception as e:
        logging.error(f"Network info error: {e}")
        return {'bytes_sent_total': 0, 'bytes_recv_total': 0, 'send_rate_mbps': 0, 'recv_rate_mbps': 0, 'error': str(e)}


def background_monitor():
    logging.info(f"Background monitor started (interval={MONITOR_INTERVAL}s)")
    socketio.sleep(0.1)
    while True:
        data = {
            'cpu': get_cpu_info(),
            'memory': get_memory_info(),
            'disk': get_disk_info(),
            'network': get_network_info(),
            'temperature': get_temperature_info(),
            'system_time': get_system_time_info()
        }
        socketio.emit('system_update', data)
        socketio.sleep(MONITOR_INTERVAL)


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/system_info')
def api_system_info():
    try:
        info = {
            'os': f"{platform.system()} {platform.release()}",
            'hostname': platform.node(),
            'cpu_model': platform.processor(),
            'cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
            'python_version': platform.python_version()
        }
        return jsonify(info)
    except Exception as e:
        logging.error(f"Static info error: {e}")
        return jsonify({'error': str(e)}), 500


# Socket events
@socketio.on('connect')
def handle_connect():
    logging.info('Client connected')
    socketio.start_background_task(background_monitor)
    emit('connection_ack', {'message': 'Connected'})


@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')


if __name__ == '__main__':
    host = config['server']['host']
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
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
        socketio.run(
            app,
            host=host,
            port=https_port,
            debug=debug,
            ssl_context=context
        )
    
    elif config['server']['http']['enabled']:
        # HTTP server (only if HTTPS is disabled)
        http_port = config['server']['http']['port']
        logging.info(f"Starting HTTP server at http://{host}:{http_port}")
        socketio.run(
            app,
            host=host,
            port=http_port,
            debug=debug
        )
    
    else:
        logging.error("Neither HTTP nor HTTPS is enabled. At least one must be enabled.")
        exit(1)
