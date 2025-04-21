# System Monitor Dashboard

A real-time system monitoring dashboard built with Python Flask and Socket.IO.

## Features

- Real-time CPU usage monitoring
- Memory and swap usage tracking
- Disk usage statistics
- Network I/O monitoring
- Load average metrics
- Temperature sensors data
- System uptime and boot time

## Architecture Overview

### Backend (Python/Flask)

1. **Data Collection**:
   - `psutil` library collects system metrics
   - Each metric has a dedicated function (e.g., `get_cpu_info()`, `get_memory_info()`)
   - Data is collected at regular intervals defined by `MONITOR_INTERVAL`

2. **Server Setup**:
   - Flask serves the web application
   - Flask-SocketIO enables real-time bidirectional communication
   - Eventlet provides asynchronous networking

3. **Background Task**:
   - `background_monitor()` runs in a separate thread
   - Collects all system metrics periodically
   - Emits data via Socket.IO to connected clients

### Frontend (HTML/JavaScript)

1. **Initial Load**:
   - Browser loads the HTML template
   - Establishes Socket.IO connection to server
   - Initializes UI elements and event listeners

2. **Real-time Updates**:
   - Listens for 'system_update' events from server
   - Updates UI components with new data:
     - Progress bars for CPU/memory usage
     - Text displays for metrics
     - Dynamic cards for disk and temperature data

3. **Connection Management**:
   - Handles connection/disconnection events
   - Updates connection status indicator
   - Resets displays when disconnected

## Requirements

- Python 3.x
- Flask
- Flask-SocketIO
- psutil
- eventlet

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python web_monitor.py`
4. Open a browser and navigate to `http://localhost:3000`

## Configuration

The following environment variables can be set:

- `FLASK_SECRET_KEY`: Secret key for Flask sessions (default: insecure key)
- `MONITOR_INTERVAL`: Update interval in seconds (default: 1.0)
- `FLASK_HOST`: Host to bind the server (default: 0.0.0.0)
- `FLASK_PORT`: Port to run the server (default: 3000)
