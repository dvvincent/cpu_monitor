#!/usr/bin/env python3
from flask import Flask, render_template
from flask_socketio import SocketIO
import json
from cpu_temp import get_detailed_cpu_temperatures
import psutil
import time
import threading
from datetime import datetime, timedelta
import platform

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def get_system_info():
    return {
        'os': f"{platform.system()} {platform.release()}",
        'cpu_model': platform.processor(),
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }

def get_memory_info():
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

def get_network_info():
    net_io = psutil.net_io_counters()
    net_connections = len(psutil.net_connections())
    return {
        'bytes_sent': f"{net_io.bytes_sent / (1024**2):.1f} MB",
        'bytes_recv': f"{net_io.bytes_recv / (1024**2):.1f} MB",
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv,
        'active_connections': net_connections
    }

def get_disk_info():
    disk_usage = psutil.disk_usage('/')
    disk_io = psutil.disk_io_counters()
    return {
        'total': f"{disk_usage.total / (1024**3):.1f} GB",
        'used': f"{disk_usage.used / (1024**3):.1f} GB",
        'free': f"{disk_usage.free / (1024**3):.1f} GB",
        'percent': disk_usage.percent,
        'read_bytes': f"{disk_io.read_bytes / (1024**2):.1f} MB",
        'write_bytes': f"{disk_io.write_bytes / (1024**2):.1f} MB",
        'read_count': disk_io.read_count,
        'write_count': disk_io.write_count
    }

def get_load_and_freq():
    load1, load5, load15 = psutil.getloadavg()
    cpu_freq = psutil.cpu_freq()
    return {
        'load_avg': {
            '1min': load1,
            '5min': load5,
            '15min': load15
        },
        'cpu_freq': {
            'current': f"{cpu_freq.current:.1f} MHz" if cpu_freq else "N/A",
            'min': f"{cpu_freq.min:.1f} MHz" if cpu_freq and hasattr(cpu_freq, 'min') else "N/A",
            'max': f"{cpu_freq.max:.1f} MHz" if cpu_freq and hasattr(cpu_freq, 'max') else "N/A"
        }
    }

def get_system_alerts(cpu_percent, memory_percent, disk_percent):
    alerts = []
    if cpu_percent > 80:
        alerts.append({
            'level': 'critical',
            'message': f'CPU usage is very high: {cpu_percent:.1f}%'
        })
    elif cpu_percent > 60:
        alerts.append({
            'level': 'warning',
            'message': f'CPU usage is elevated: {cpu_percent:.1f}%'
        })
    
    if memory_percent > 90:
        alerts.append({
            'level': 'critical',
            'message': f'Memory usage is very high: {memory_percent:.1f}%'
        })
    elif memory_percent > 75:
        alerts.append({
            'level': 'warning',
            'message': f'Memory usage is elevated: {memory_percent:.1f}%'
        })
    
    if disk_percent > 90:
        alerts.append({
            'level': 'critical',
            'message': f'Disk usage is very high: {disk_percent:.1f}%'
        })
    elif disk_percent > 75:
        alerts.append({
            'level': 'warning',
            'message': f'Disk usage is elevated: {disk_percent:.1f}%'
        })
    
    return alerts

def get_uptime():
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

def get_cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    return {
        'per_cpu': cpu_percent,
        'average': sum(cpu_percent) / len(cpu_percent)
    }

def get_top_processes(limit=10, target_user='adminuser'):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'status', 'cmdline']):
        try:
            if proc.username() != target_user:
                continue
                
            pinfo = proc.info
            # Update CPU percent for each process
            pinfo['cpu_percent'] = proc.cpu_percent(interval=None)
            
            # Get the full command line
            try:
                cmdline = proc.cmdline()
                # Use the first argument (full path) if available, otherwise use the name
                full_path = cmdline[0] if cmdline else proc.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                full_path = pinfo['name']
                
            pinfo['full_path'] = full_path
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Sort by CPU usage and get top processes
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]
    
    return [{
        'pid': p['pid'],
        'name': p['name'],
        'full_path': p['full_path'],
        'cpu_percent': p['cpu_percent'],
        'memory_percent': round(p['memory_percent'], 1) if p['memory_percent'] is not None else 0.0,
        'status': p['status']
    } for p in top_processes]

def background_thread():
    temp_history = {}
    while True:
        temps = get_detailed_cpu_temperatures()
        
        # Update temperature history
        for sensor_name, readings in temps.items():
            if sensor_name not in temp_history:
                temp_history[sensor_name] = {}
            for reading in readings:
                label = reading['label']
                current = float(reading['current'].replace('°C', ''))
                if label not in temp_history[sensor_name]:
                    temp_history[sensor_name][label] = {'min': current, 'max': current}
                else:
                    temp_history[sensor_name][label]['min'] = min(temp_history[sensor_name][label]['min'], current)
                    temp_history[sensor_name][label]['max'] = max(temp_history[sensor_name][label]['max'], current)
        
        cpu_usage = get_cpu_usage()
        memory_info = get_memory_info()
        disk_info = get_disk_info()
        
        system_data = {
            'temperatures': temps,
            'temp_history': temp_history,
            'cpu_usage': cpu_usage,
            'memory': memory_info,
            'disk': disk_info,
            'network': get_network_info(),
            'load_and_freq': get_load_and_freq(),
            'uptime': get_uptime(),
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'top_processes': get_top_processes(),
            'alerts': get_system_alerts(
                cpu_usage['average'],
                memory_info['percent'],
                disk_info['percent']
            )
        }
        
        socketio.emit('system_update', {'data': system_data})
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    thread = threading.Thread(target=background_thread)
    thread.daemon = True
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
