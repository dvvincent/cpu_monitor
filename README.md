# SystemPulse

A real-time system monitoring dashboard built with Python, aiohttp, and Socket.IO using asyncio.

## Features

- Real-time CPU usage monitoring
- Memory and swap usage tracking
- Disk usage statistics
- Network I/O monitoring
- Load average metrics
- Temperature sensors data
- System uptime and boot time

## Architecture Overview

### Backend (Python/aiohttp)

1. **Data Collection**:
   - `psutil` library collects system metrics
   - Each metric has a dedicated function (e.g., `get_cpu_info()`, `get_memory_info()`)
   - Data is collected at regular intervals defined by `MONITOR_INTERVAL`

2. **Server Setup**:
   - aiohttp serves the web application
   - python-socketio enables real-time bidirectional communication
   - asyncio provides asynchronous networking

3. **Background Task**:
   - `background_monitor()` runs as an async coroutine
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
- aiohttp
- python-socketio
- psutil
- jinja2

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python web_monitor.py`
4. Open a browser and navigate to `https://localhost:3443`

## Configuration

The application can be configured using a YAML configuration file. To get started:

1. Copy the example configuration:
   ```bash
   cp config.yaml.example config.yaml
   ```

2. Edit `config.yaml` to customize your settings:
   ```yaml
   server:
     host: "0.0.0.0"  # Server host
     http:
       enabled: true   # Enable HTTP server
       port: 3000      # HTTP port
     https:
       enabled: true   # Enable HTTPS server
       port: 3443      # HTTPS port
       certificates:
         cert_file: "ssl/cert.pem"  # SSL certificate path
         key_file: "ssl/key.pem"    # SSL key path
   
   monitoring:
     update_interval: 1.0  # Metric update interval
     metrics:
       cpu: true      # Enable CPU monitoring
       memory: true   # Enable memory monitoring
       disk: true     # Enable disk monitoring
       network: true  # Enable network monitoring
       processes: true # Enable process monitoring
   
   security:
     enable_cors: false     # Enable CORS
     cors_origins: ["*"]   # Allowed CORS origins
     secret_key: "change-this-to-a-secure-secret-key"
   ```

3. The configuration file supports the following features:
   - HTTP and HTTPS servers can be enabled/disabled independently
   - Custom ports for both HTTP and HTTPS
   - Configurable SSL certificate paths
   - Selective metric monitoring
   - CORS configuration for API access
   - Custom secret key for session management

If no `config.yaml` is found, the application will use default values.

## Environment Variables

- `FLASK_SECRET_KEY`: Secret key for Flask sessions (default: insecure key)
- `MONITOR_INTERVAL`: Interval for updating metrics in seconds (default: 1.0)
- `FLASK_HOST`: Host to bind the server (default: 0.0.0.0)
- `FLASK_PORT`: Port for HTTP server (default: 3000)
- `FLASK_SSL_PORT`: Port for HTTPS server (default: 3443)
- `USE_SSL`: Enable HTTPS (default: True)
- `SSL_CERT`: Path to SSL certificate (default: ssl/cert.pem)
- `SSL_KEY`: Path to SSL private key (default: ssl/key.pem)

## SSL Certificate Setup

To enable HTTPS support, you'll need to provide SSL certificates. For development, you can generate self-signed certificates:

1. Create the SSL directory:
   ```bash
   mkdir ssl
   ```

2. Generate a self-signed certificate (valid for 365 days):
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365
   ```

3. When prompted, fill in the certificate information or press Enter to use defaults.

**Note**: For production use, you should obtain proper SSL certificates from a trusted Certificate Authority (CA).

## HTTPS Configuration

By default, the application runs with HTTPS enabled using self-signed certificates. For production use, you should replace these with proper SSL certificates.

### Using Self-Signed Certificates
The application comes with a script to generate self-signed certificates:

```bash
# Generate certificates (already done during setup)
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365 -subj "/CN=localhost"
```

### Using Your Own Certificates
To use your own SSL certificates:

1. Place your certificate and private key files in a secure location
2. Set the environment variables to point to your certificates:
```bash
export SSL_CERT=/path/to/your/certificate.pem
export SSL_KEY=/path/to/your/private-key.pem
```

### Disabling HTTPS
To run without HTTPS:
```bash
export USE_SSL=false
