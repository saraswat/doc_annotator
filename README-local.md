# Document Annotation System - Local Development Setup

This guide explains how to run the Document Annotation System locally without Docker.

## Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 14+** 
- **Redis** (optional, for real-time features)

## Quick Start

1. **Run the setup script:**
   ```bash
   ./setup-local.sh
   ```

2. **Create the PostgreSQL database:**
   ```bash
   createdb annotation_db
   # Or if you need to specify user/host:
   createdb -U annotation_user -h localhost annotation_db
   ```

3. **Start the backend** (in one terminal):
   ```bash
   ./start-backend.sh          # Default port 8000
   # Or with custom port:
   ./start-backend.sh 8080
   ```

4. **Start the frontend** (in another terminal):
   ```bash
   ./start-frontend.sh         # Default ports: frontend=3000, backend=8000
   # Or with custom ports:
   ./start-frontend.sh 3001 8080  # frontend on 3001, backend on 8080
   ```

5. **Open your browser** to http://localhost:3000 (or your custom frontend port)

## Default Admin Access

- **Email:** admin@test.com
- **Password:** temppass123 (must be changed on first login)

## Manual Setup (if scripts don't work)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://annotation_user:annotation_pass@localhost:5432/annotation_db"
export SECRET_KEY="your-secret-key-here"
export ADMIN_USER_EMAIL="admin@test.com"
export ADMIN_INITIAL_PASSWORD="temppass123"

# Start server
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install

# Set environment variables  
export REACT_APP_API_URL="http://localhost:8000/api"

# Start development server
npm start
```

## Configuration

### Backend Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://annotation_user:annotation_pass@localhost:5432/annotation_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin User
ADMIN_USER_EMAIL=admin@test.com
ADMIN_INITIAL_PASSWORD=temppass123

# OAuth (optional)
OAUTH_PROVIDER=google
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend Environment Variables (.env)
```bash
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000
```

## Database Setup

### PostgreSQL Installation

#### macOS

**Option 1: Homebrew (Recommended)**
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@16
brew services start postgresql@16

# Add PostgreSQL to PATH (works for both bash and zsh)
if [[ "$SHELL" == *"zsh"* ]]; then
    echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    echo "Added to ~/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.bash_profile
    source ~/.bash_profile
    echo "Added to ~/.bash_profile"
else
    echo "Manual PATH setup required - add this to your shell config:"
    echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"'
fi

# Create database
createdb annotation_db
```

**Option 2: Postgres.app**
```bash
# Download and install Postgres.app from https://postgresapp.com
# Start Postgres.app
# Add to PATH (works for both bash and zsh)
if [[ "$SHELL" == *"zsh"* ]]; then
    echo 'export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    echo "Added to ~/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    echo 'export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"' >> ~/.bash_profile
    source ~/.bash_profile
    echo "Added to ~/.bash_profile"
else
    echo "Manual PATH setup required - add this to your shell config:"
    echo 'export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"'
fi

# Create database
createdb annotation_db
```

**Option 3: Official Installer**
```bash
# Download from https://www.postgresql.org/download/macosx/
# Follow installer instructions
# Add to PATH if needed
# Create database using psql or pgAdmin
```

#### Linux

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib postgresql-client

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user and database
sudo -u postgres psql -c "CREATE USER annotation_user WITH PASSWORD 'annotation_pass';"
sudo -u postgres psql -c "CREATE DATABASE annotation_db OWNER annotation_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE annotation_db TO annotation_user;"

# Test connection
psql -h localhost -U annotation_user -d annotation_db -c "SELECT version();"

# Note: On Linux, you may need to reload your shell configuration
# For bash: source ~/.bashrc or source ~/.bash_profile
# For zsh: source ~/.zshrc
```

**CentOS/RHEL/Fedora:**
```bash
# Install PostgreSQL
sudo dnf install postgresql postgresql-server postgresql-contrib  # Fedora
# OR
sudo yum install postgresql postgresql-server postgresql-contrib  # CentOS/RHEL

# Initialize database
sudo postgresql-setup --initdb

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user and database
sudo -u postgres psql -c "CREATE USER annotation_user WITH PASSWORD 'annotation_pass';"
sudo -u postgres psql -c "CREATE DATABASE annotation_db OWNER annotation_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE annotation_db TO annotation_user;"
```

**Arch Linux:**
```bash
# Install PostgreSQL
sudo pacman -S postgresql

# Initialize database cluster
sudo -u postgres initdb -D /var/lib/postgres/data

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user and database
sudo -u postgres psql -c "CREATE USER annotation_user WITH PASSWORD 'annotation_pass';"
sudo -u postgres psql -c "CREATE DATABASE annotation_db OWNER annotation_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE annotation_db TO annotation_user;"
```

#### Windows

**Option 1: Official Installer (Recommended)**
```bash
# 1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
# 2. Run installer with these settings:
#    - Install directory: Default (C:\Program Files\PostgreSQL\16)
#    - Data directory: Default
#    - Password: Set a password for 'postgres' user
#    - Port: 5432 (default)
#    - Locale: Default
# 3. Add PostgreSQL to PATH:
#    - Add C:\Program Files\PostgreSQL\16\bin to system PATH
# 4. Open Command Prompt or PowerShell as Administrator:

# Create database user and database
psql -U postgres -c "CREATE USER annotation_user WITH PASSWORD 'annotation_pass';"
psql -U postgres -c "CREATE DATABASE annotation_db OWNER annotation_user;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE annotation_db TO annotation_user;"
```

**Option 2: Docker (if you prefer)**
```bash
# Run PostgreSQL in Docker
docker run --name postgres-annotation -e POSTGRES_USER=annotation_user -e POSTGRES_PASSWORD=annotation_pass -e POSTGRES_DB=annotation_db -p 5432:5432 -d postgres:16

# The database will be available at localhost:5432
```

### Verifying PostgreSQL Installation

After installation, verify everything works:

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection to your database
psql -h localhost -U annotation_user -d annotation_db -c "SELECT version();"

# Expected output should show PostgreSQL version
```

### Shell Configuration Notes

The installation scripts detect your shell and update the appropriate config file:

**For Bash users:**
- Updates `~/.bash_profile` (macOS) or `~/.bashrc` (Linux)
- Reload with: `source ~/.bash_profile` or `source ~/.bashrc`

**For Zsh users:**
- Updates `~/.zshrc`
- Reload with: `source ~/.zshrc`

**Manual PATH setup (if auto-detection fails):**
```bash
# Find your shell
echo $SHELL

# Add to appropriate config file:
# For bash: ~/.bash_profile (macOS) or ~/.bashrc (Linux)
# For zsh: ~/.zshrc
# For fish: ~/.config/fish/config.fish

# Example for bash:
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

### Common Issues

**Connection refused:**
- Make sure PostgreSQL service is running
- Check if PostgreSQL is listening on port 5432: `netstat -an | grep 5432`

**Authentication failed:**
- Verify username/password are correct
- Check pg_hba.conf allows local connections (usually in /etc/postgresql/*/main/)

**Database does not exist:**
- Create it: `createdb -U annotation_user annotation_db`
- Or via SQL: `CREATE DATABASE annotation_db;`

**Permission denied:**
- Make sure the user has privileges: `GRANT ALL PRIVILEGES ON DATABASE annotation_db TO annotation_user;`

**PATH not working after installation:**
- Check which shell you're using: `echo $SHELL`
- Reload your shell config or open a new terminal
- Verify PostgreSQL is in PATH: `which psql`

### Custom Database Configuration

If you have different PostgreSQL credentials, update the DATABASE_URL in `backend/.env`:

```bash
DATABASE_URL=postgresql+asyncpg://YOUR_USER:YOUR_PASSWORD@localhost:5432/YOUR_DATABASE
```

## Troubleshooting

### Backend Issues

**Database connection error:**
- Make sure PostgreSQL is running: `brew services start postgresql` (macOS)
- Check if database exists: `psql -l | grep annotation_db`
- Create database: `createdb annotation_db`

**Import errors:**
- Make sure virtual environment is activated: `source backend/venv/bin/activate`
- Reinstall dependencies: `pip install -r backend/requirements.txt`

**Permission errors:**
- Make scripts executable: `chmod +x *.sh`

### Frontend Issues

**Module not found:**
- Delete node_modules and reinstall: `rm -rf frontend/node_modules && cd frontend && npm install`

**API connection failed:**
- Make sure backend is running on port 8000
- Check REACT_APP_API_URL in frontend/.env

**CORS errors:**
- Check CORS_ORIGINS in backend/.env includes http://localhost:3000

## Features Available in Local Mode

- ✅ User authentication (password + OAuth)
- ✅ Document upload and viewing (HTML, Markdown, PDF)
- ✅ PDF annotations with highlighting
- ✅ Admin dashboard (user management, document controls)
- ✅ Document visibility controls (public/private)
- ⚠️ Real-time collaboration (requires Redis)

## Adding OAuth

To enable Google OAuth:

1. **Create Google OAuth app:**
   - Go to Google Cloud Console
   - Create OAuth 2.0 credentials
   - Add http://localhost:3000/auth/callback as redirect URI

2. **Update backend/.env:**
   ```bash
   OAUTH_CLIENT_ID=your-google-client-id
   OAUTH_CLIENT_SECRET=your-google-client-secret
   ```

## Production Considerations

For production deployment:
- Use a managed PostgreSQL service
- Set proper SECRET_KEY (not the generated one)
- Configure proper CORS origins
- Use environment-specific .env files
- Set up Redis for real-time features
- Configure proper logging