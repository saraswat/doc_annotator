# Deployment Scripts Guide

This project provides different startup scripts for various deployment scenarios.

## Script Types

### Local Development (HTTP)
For local development with HTTP and minimal setup:

- **`startup-backend-local.sh`** - Backend on `http://localhost:8000`
- **`startup-frontend-local.sh`** - Frontend on `http://localhost:3000`

### Production Deployment (HTTPS)
For production deployment with HTTPS and SSL certificates:

- **`start-backend.sh`** - Backend with HTTPS and configurable host
- **`start-frontend.sh`** - Frontend with HTTPS and configurable host

## Environment Variables

### Backend Scripts

#### Production Script (`start-backend.sh`)
```bash
# Option 1: Direct SSL (backend handles HTTPS)
export BACKEND_HOST=your-backend-host.com  # Default: 0.0.0.0
export FRONTEND_HOST=your-frontend-host.com  # Default: localhost
export SSL_KEYFILE=./ssl/key.pem  # Required for direct SSL
export SSL_CERTFILE=./ssl/cert.pem  # Required for direct SSL
export SSL_CA_CERTS=./ssl/ca.pem  # Optional CA certificate

# Option 2: Nginx SSL termination (backend runs as HTTP)
export USE_NGINX_SSL=true  # Enable nginx SSL termination mode
export BACKEND_HOST=127.0.0.1  # Internal host
export FRONTEND_HOST=your-domain.com  # Public domain

./start-backend.sh [port] [database_type]
```

#### Local Script (`startup-backend-local.sh`)
```bash
# No environment variables required
./startup-backend-local.sh
```

### Frontend Scripts

#### Production Script (`start-frontend.sh`)
```bash
# Option 1: Direct SSL (frontend handles HTTPS)
export FRONTEND_HOST=your-frontend-host.com  # Default: localhost
export BACKEND_HOST=your-backend-host.com   # Default: localhost
export SSL_KEYFILE=./frontend/ssl/key.pem   # Required for direct SSL
export SSL_CERTFILE=./frontend/ssl/cert.pem # Required for direct SSL

# Option 2: Nginx SSL termination (frontend runs as HTTP)
export USE_NGINX_SSL=true  # Enable nginx SSL termination mode
export FRONTEND_HOST=127.0.0.1  # Internal host
export BACKEND_HOST=your-domain.com  # Public domain (nginx endpoint)

./start-frontend.sh [frontend_port] [backend_port]
```

#### Local Script (`startup-frontend-local.sh`)
```bash
# No environment variables required
./startup-frontend-local.sh
```

## Usage Examples

### Local Development
```bash
# Terminal 1: Start backend (HTTP)
./startup-backend-local.sh

# Terminal 2: Start frontend (HTTP)
./startup-frontend-local.sh
```

### Production Deployment with Direct SSL
```bash
# Set environment variables
export BACKEND_HOST=api.yourdomain.com
export FRONTEND_HOST=app.yourdomain.com

# Terminal 1: Start backend (HTTPS)
./start-backend.sh 8000 postgresql

# Terminal 2: Start frontend (HTTPS)
./start-frontend.sh 3000 8000
```

### Production Deployment with Nginx SSL Termination
```bash
# Both services run as HTTP internally, nginx handles HTTPS publicly
export USE_NGINX_SSL=true
export BACKEND_HOST=127.0.0.1      # Internal backend
export FRONTEND_HOST=127.0.0.1     # Internal frontend  

# Terminal 1: Start backend (HTTP internally)
./start-backend.sh 8000 postgresql

# Terminal 2: Start frontend (HTTP internally)
./start-frontend.sh 3000 8000

# Public access via nginx: https://yourdomain.com
```

### Multi-Host Production
```bash
# Backend server
export BACKEND_HOST=10.0.1.10
export FRONTEND_HOST=app.yourdomain.com
./start-backend.sh 8000

# Frontend server (different machine)
export FRONTEND_HOST=0.0.0.0  # Bind to all interfaces
export BACKEND_HOST=10.0.1.10  # Backend server IP
./start-frontend.sh 3000 8000
```

## SSL Certificate Requirements

### Two SSL Deployment Options

The production scripts support two SSL deployment modes:

1. **Direct SSL**: Applications handle SSL certificates directly
2. **Nginx SSL Termination**: Nginx handles SSL, applications run as HTTP internally

### Direct SSL Mode (Default)
When `USE_NGINX_SSL` is not set, the production scripts require SSL certificates and will exit with an error if certificates are not found.

### Nginx SSL Termination Mode  
When `USE_NGINX_SSL=true`, the applications run as HTTP internally and nginx handles HTTPS publicly. No SSL certificates are required for the applications themselves.

#### Backend SSL Files
```
./ssl/key.pem      # Private key (required)
./ssl/cert.pem     # Certificate (required)
./ssl/ca.pem       # CA certificate (optional)
```

#### Frontend SSL Files
```
./frontend/ssl/key.pem   # Private key (required)
./frontend/ssl/cert.pem  # Certificate (required)
```

### Creating SSL Certificates

#### Self-Signed Certificates (Development)
```bash
# Create backend SSL directory
mkdir -p ssl

# Generate backend certificates
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes

# Create frontend SSL directory
mkdir -p frontend/ssl

# Copy or generate frontend certificates
cp ssl/key.pem frontend/ssl/
cp ssl/cert.pem frontend/ssl/
```

#### Production Certificates
Use Let's Encrypt, your cloud provider's certificate manager, or purchase certificates from a CA.

## OAuth Login Behavior

### Automatic OAuth Disabling for Intranet Deployments

When using nginx SSL termination (`USE_NGINX_SSL=true`), OAuth login is automatically disabled because:

1. **Intranet Assumption**: Nginx SSL termination typically indicates internal/intranet deployment
2. **OAuth Requirements**: OAuth providers (Google, etc.) require public internet access
3. **Security**: Internal networks may not allow external OAuth callbacks

### Login Methods by Deployment Type

| Deployment Type | OAuth Login | Password Login | Primary Use Case |
|----------------|-------------|----------------|------------------|
| **Local Development** | ✅ Enabled | ✅ Enabled | Developer testing |
| **Public Internet** | ✅ Enabled | ✅ Enabled | External users |
| **Intranet (Nginx)** | ❌ Disabled | ✅ Enabled | Internal company users |

### Environment Variables

The frontend automatically sets these based on deployment type:

```bash
# Public/Direct SSL deployment
REACT_APP_DISABLE_OAUTH=false
REACT_APP_DEPLOYMENT_TYPE=public

# Intranet/Nginx SSL deployment  
REACT_APP_DISABLE_OAUTH=true
REACT_APP_DEPLOYMENT_TYPE=intranet

# Local development
REACT_APP_DISABLE_OAUTH=false
REACT_APP_DEPLOYMENT_TYPE=local
```

## Configuration Differences

| Feature | Local Scripts | Production Scripts (Direct SSL) | Production Scripts (Nginx SSL) |
|---------|---------------|----------------------------------|-------------------------------|
| Protocol | HTTP | HTTPS (required) | HTTP internally, HTTPS via nginx |
| SSL Certificates | Not required | Required | Not required (nginx handles) |
| Host Configuration | Fixed to localhost | Environment variable | Environment variable |
| CORS Origins | localhost:3000 | Based on FRONTEND_HOST | Based on FRONTEND_HOST |
| OAuth Login | Enabled | Enabled | **Disabled** (intranet) |
| Error Handling | Warnings only | Exits on missing SSL | Exits on nginx connectivity |
| Target Use Case | Development | Public internet deployment | Intranet/private network |

## Troubleshooting

### "SSL certificates not found" Error
This means you're using a production script without SSL certificates. Either:
1. Create SSL certificates (see above)
2. Use local development scripts instead
3. Set up a reverse proxy (nginx/caddy) with SSL termination

### CORS Issues
Make sure `FRONTEND_HOST` is set correctly for your deployment and matches the domain users will access.

### Port Conflicts
If ports are in use:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill processes if needed
kill $(lsof -ti :8000)
kill $(lsof -ti :3000)
```