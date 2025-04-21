# System Monitor API Documentation

## Quick Start

### Using cURL
```bash
# Get current system metrics
curl http://localhost:3000/api/system_info
```

### Using Python
```python
import requests

# Get current system metrics
response = requests.get('http://localhost:3000/api/system_info')
data = response.json()
print(f"CPU Usage: {data['cpu']['percent']}%")
print(f"Memory Used: {data['memory']['used']} of {data['memory']['total']}")
```

### Using JavaScript
```javascript
// Using Fetch API
fetch('http://localhost:3000/api/system_info')
  .then(response => response.json())
  .then(data => {
    console.log(`CPU Usage: ${data.cpu.percent}%`);
    console.log(`Memory Used: ${data.memory.used} of ${data.memory.total}`);
  });

// Using Socket.IO for real-time updates
const socket = io('http://localhost:3000');
socket.on('system_update', (data) => {
    console.log('System metrics updated:', data);
});
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
{{
  "cpu": {{
    "percent": 35.2,
    "load_1": 1.25,
    "load_5": 1.15,
    "load_15": 0.95
  }},
  "memory": {{
    "total": "16.0 GB",
    "used": "8.5 GB",
    "percent": 53.1,
    "swap_total": "4.0 GB",
    "swap_used": "0.5 GB",
    "swap_percent": 12.5
  }},
  "disk": [
    {{
      "device": "/dev/sda1",
      "mountpoint": "/",
      "total": "256.0",
      "used": "128.5",
      "percent": 50.2
    }},
    {{
      "device": "/dev/sdb1",
      "mountpoint": "/home",
      "total": "512.0",
      "used": "256.0",
      "percent": 50.0
    }}
  ],
  "network": {{
    "bytes_sent_total": "1.25",
    "bytes_recv_total": "2.50",
    "send_rate_mbps": "15.5",
    "recv_rate_mbps": "22.3"
  }},
  "temperature": [
    {{
      "name": "coretemp: Core 0",
      "current": 45.0,
      "high": 80.0,
      "critical": 95.0
    }},
    {{
      "name": "coretemp: Core 1",
      "current": 46.5,
      "high": 80.0,
      "critical": 95.0
    }}
  ],
  "system_time": {{
    "boot_time": "2025-04-21 12:00:00",
    "uptime": "7d 02:30:15"
  }}
}}
```

##### High System Load
```json
{{
  "cpu": {{
    "percent": 92.5,
    "load_1": 8.56,
    "load_5": 7.89,
    "load_15": 6.45
  }},
  "memory": {{
    "total": "16.0 GB",
    "used": "15.2 GB",
    "percent": 95.0,
    "swap_total": "4.0 GB",
    "swap_used": "3.8 GB",
    "swap_percent": 95.0
  }},
  "temperature": [
    {{
      "name": "coretemp: Core 0",
      "current": 82.5,
      "high": 80.0,
      "critical": 95.0
    }}
  ]
}}
```

##### Current System State
```json
# Timestamp: 2025-04-21 19:43:50
{{
  "cores": 4,
  "cpu_model": "x86_64",
  "hostname": "digits",
  "os": "Linux 6.8.0-57-generic",
  "physical_cores": 4,
  "python_version": "3.12.3"
}}
```

#### Common Use Cases

1. **Monitoring CPU Usage**
```python
if data['cpu']['percent'] > 80:
    print(f"High CPU usage: {data['cpu']['percent']}%")
    print(f"Load averages: {data['cpu']['load_1']}, {data['cpu']['load_5']}, {data['cpu']['load_15']}")
```

2. **Checking Memory Status**
```python
if data['memory']['percent'] > 90:
    print("Low memory warning!")
    print(f"Used: {data['memory']['used']} of {data['memory']['total']}")
    print(f"Swap usage: {data['memory']['swap_percent']}%")
```

3. **Monitoring Temperature**
```python
for sensor in data['temperature']:
    if sensor['current'] > sensor['high']:
        print(f"Temperature warning: {sensor['name']} at {sensor['current']}°C")
```

4. **Network Bandwidth Monitoring**
```python
print("Current network usage:")
print(f"Upload: {data['network']['send_rate_mbps']} Mbps")
print(f"Download: {data['network']['recv_rate_mbps']} Mbps")
```

5. **Disk Space Alerts**
```python
for disk in data['disk']:
    if disk['percent'] > 85:
        print(f"Low disk space on {disk['mountpoint']}: {disk['percent']}% used")
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
Emitted every 1.0 seconds with the same data structure as the REST endpoint.

```javascript
socket.on('system_update', (data) => {
    console.log('Received system update:', data);
});
```

## Error Handling

If the server is unavailable or encounters an error, the API will return an appropriate HTTP status code and error message.

Example error response:
```json
{
    "error": "Internal server error"
}
```
