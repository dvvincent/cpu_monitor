#!/usr/bin/env python3

import json
import requests
import time
from datetime import datetime

def get_system_info():
    """Query the system info endpoint and return formatted data"""
    try:
        response = requests.get('http://localhost:3000/api/system_info')
        return response.json()
    except requests.RequestException as e:
        return {
            "cpu": {"percent": 0, "load_1": 0, "load_5": 0, "load_15": 0},
            "memory": {"total": "0 GB", "used": "0 GB", "percent": 0, "swap_total": "0 GB", "swap_used": "0 GB", "swap_percent": 0},
            "disk": [],
            "network": {"bytes_sent_total": "0", "bytes_recv_total": "0", "send_rate_mbps": "0", "recv_rate_mbps": "0"},
            "temperature": [],
            "system_time": {"boot_time": "N/A", "uptime": "N/A"},
            "error": str(e)
        }

def format_json(data):
    """Format JSON data with proper indentation"""
    return json.dumps(data, indent=2).replace('{', '{{').replace('}', '}}')

def generate_example_responses():
    """Generate example responses for different scenarios"""
    normal = {
        "cpu": {
            "percent": 35.2,
            "load_1": 1.25,
            "load_5": 1.15,
            "load_15": 0.95
        },
        "memory": {
            "total": "16.0 GB",
            "used": "8.5 GB",
            "percent": 53.1,
            "swap_total": "4.0 GB",
            "swap_used": "0.5 GB",
            "swap_percent": 12.5
        },
        "disk": [
            {
                "device": "/dev/sda1",
                "mountpoint": "/",
                "total": "256.0",
                "used": "128.5",
                "percent": 50.2
            },
            {
                "device": "/dev/sdb1",
                "mountpoint": "/home",
                "total": "512.0",
                "used": "256.0",
                "percent": 50.0
            }
        ],
        "network": {
            "bytes_sent_total": "1.25",
            "bytes_recv_total": "2.50",
            "send_rate_mbps": "15.5",
            "recv_rate_mbps": "22.3"
        },
        "temperature": [
            {
                "name": "coretemp: Core 0",
                "current": 45.0,
                "high": 80.0,
                "critical": 95.0
            },
            {
                "name": "coretemp: Core 1",
                "current": 46.5,
                "high": 80.0,
                "critical": 95.0
            }
        ],
        "system_time": {
            "boot_time": "2025-04-21 12:00:00",
            "uptime": "7d 02:30:15"
        }
    }

    high_load = {
        "cpu": {
            "percent": 92.5,
            "load_1": 8.56,
            "load_5": 7.89,
            "load_15": 6.45
        },
        "memory": {
            "total": "16.0 GB",
            "used": "15.2 GB",
            "percent": 95.0,
            "swap_total": "4.0 GB",
            "swap_used": "3.8 GB",
            "swap_percent": 95.0
        },
        "temperature": [
            {
                "name": "coretemp: Core 0",
                "current": 82.5,
                "high": 80.0,
                "critical": 95.0
            }
        ]
    }

    return {
        "normal": normal,
        "high_load": high_load
    }

def get_code_examples():
    """Get code examples for documentation"""
    return {
        'quick_start': {
            'python': '''import requests

# Get current system metrics (disable SSL verification for self-signed certs)
response = requests.get('https://localhost:3000/api/system_info', verify=False)
data = response.json()
print(f"CPU Usage: {data['cpu']['percent']}%")
print(f"Memory Used: {data['memory']['used']} of {data['memory']['total']}")''',
            'javascript': '''// Using Fetch API
fetch('https://localhost:3000/api/system_info')
  .then(response => response.json())
  .then(data => {
    console.log(`CPU Usage: ${data.cpu.percent}%`);
    console.log(`Memory Used: ${data.memory.used} of ${data.memory.total}`);
  });

// Using Socket.IO for real-time updates with SSL
const socket = io('https://localhost:3000', {
    rejectUnauthorized: false  // For self-signed certificates
});
socket.on('system_update', (data) => {
    console.log('System metrics updated:', data);
});''',
            'curl': '''# Get current system metrics (ignore SSL verification for self-signed certs)
curl -k https://localhost:3000/api/system_info'''
        },
        'use_cases': {
            'cpu': '''if data['cpu']['percent'] > 80:
    print(f"High CPU usage: {data['cpu']['percent']}%")
    print(f"Load averages: {data['cpu']['load_1']}, {data['cpu']['load_5']}, {data['cpu']['load_15']}")''',
            'memory': '''if data['memory']['percent'] > 90:
    print("Low memory warning!")
    print(f"Used: {data['memory']['used']} of {data['memory']['total']}")
    print(f"Swap usage: {data['memory']['swap_percent']}%")''',
            'temperature': '''for sensor in data['temperature']:
    if sensor['current'] > sensor['high']:
        print(f"Temperature warning: {sensor['name']} at {sensor['current']}°C")''',
            'network': '''print("Current network usage:")
print(f"Upload: {data['network']['send_rate_mbps']} Mbps")
print(f"Download: {data['network']['recv_rate_mbps']} Mbps")''',
            'disk': '''for disk in data['disk']:
    if disk['percent'] > 85:
        print(f"Low disk space on {disk['mountpoint']}: {disk['percent']}% used")'''
        }
    }

def generate_markdown():
    """Generate markdown documentation with examples"""
    data = get_system_info()
    examples = get_code_examples()
    doc = """# System Monitor API Documentation

## API Base URL

The API is available over both HTTP and HTTPS:
- HTTPS (recommended): `https://localhost:3000`
- HTTP: `http://localhost:3000`

## Quick Start

### Using cURL
```bash
{curl_example}
```

### Using Python
```python
{python_example}
```

### Using JavaScript
```javascript
{js_example}
```
```

## Overview
This document provides details about the System Monitor API endpoints and their responses.

## API Endpoints

### GET /api/system_info
Returns real-time system metrics including CPU, memory, disk, network, temperature, and system time information.

#### Response Format
The response is a JSON object containing the following main sections:

- `cpu`: CPU usage and load average metrics
- `memory`: RAM and swap usage statistics
- `disk`: Mounted partitions and their usage
- `network`: Network I/O statistics
- `temperature`: System temperature sensor readings
- `system_time`: System uptime and boot time information

#### Example Responses

##### Normal System Load
```json
{normal_example}
```

##### High System Load
```json
{high_load_example}
```

##### Current System State
```json
# Timestamp: {timestamp}
{example_response}
```

#### Common Use Cases

1. **Monitoring CPU Usage**
```python
{cpu_example}
```

2. **Checking Memory Status**
```python
{memory_example}
```

3. **Monitoring Temperature**
```python
{temperature_example}
```

4. **Network Bandwidth Monitoring**
```python
{network_example}
```

5. **Disk Space Alerts**
```python
{disk_example}
```

### Response Fields Explanation

#### CPU Information
- `percent`: Current CPU usage percentage
- `load_1`: 1-minute load average
- `load_5`: 5-minute load average
- `load_15`: 15-minute load average

#### Memory Information
- `total`: Total RAM available
- `used`: Currently used RAM
- `percent`: RAM usage percentage
- `swap_total`: Total swap space
- `swap_used`: Currently used swap space
- `swap_percent`: Swap usage percentage

#### Disk Information
Array of mounted partitions with:
- `device`: Device name
- `mountpoint`: Mount location
- `total`: Total space
- `used`: Used space
- `percent`: Usage percentage

#### Network Information
- `bytes_sent_total`: Total bytes sent
- `bytes_recv_total`: Total bytes received
- `send_rate_mbps`: Current send rate in Mbps
- `recv_rate_mbps`: Current receive rate in Mbps

#### Temperature Information
Array of temperature sensors with:
- `name`: Sensor name
- `current`: Current temperature in °C
- `high`: High temperature threshold (if available)
- `critical`: Critical temperature threshold (if available)

#### System Time Information
- `boot_time`: System boot timestamp
- `uptime`: System uptime duration

## WebSocket Events

The API also supports real-time updates via WebSocket (Socket.IO):

### Event: 'system_update'
Emitted every {interval} seconds with the same data structure as the REST endpoint.

```javascript
socket.on('system_update', (data) => {{
    console.log('Received system update:', data);
}});
```

## Error Handling

If the server is unavailable or encounters an error, the API will return an appropriate HTTP status code and error message.

Example error response:
```json
{{
    "error": "Internal server error"
}}
```
"""
    
    # Format the example response and add timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    examples = get_code_examples()
    formatted_doc = doc.format(
        timestamp=current_time,
        example_response=format_json(data),
        normal_example=format_json(generate_example_responses()['normal']),
        high_load_example=format_json(generate_example_responses()['high_load']),
        interval=1.0,
        curl_example=examples['quick_start']['curl'],
        python_example=examples['quick_start']['python'],
        js_example=examples['quick_start']['javascript'],
        cpu_example=examples['use_cases']['cpu'],
        memory_example=examples['use_cases']['memory'],
        temperature_example=examples['use_cases']['temperature'],
        network_example=examples['use_cases']['network'],
        disk_example=examples['use_cases']['disk']
    )
    
    # Write to file
    with open('API_DOCUMENTATION.md', 'w') as f:
        f.write(formatted_doc)

if __name__ == '__main__':
    # Ensure the backend is running before generating docs
    print("Generating API documentation...")
    generate_markdown()
    print("Documentation generated in API_DOCUMENTATION.md")
