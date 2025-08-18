# Document Annotation System - Local Development Setup

This guide explains how to run the Document Annotation System locally without Docker.

## Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Database**: PostgreSQL 14+ OR MySQL 8.0+ OR SQLite 3.31+ (built into Python)
- **Redis** (optional, for real-time features)
- **OpenSSL** (for HTTPS certificate generation)

## Quick Start

### Option A: PostgreSQL (Default)

**For HTTPS (Recommended for intranet environments):**
```bash
# Generate SSL certificates first
./generate-ssl-certs.sh

# Setup and start with HTTPS
./setup-local.sh postgresql
./start-backend.sh 8000 postgresql
./start-frontend.sh 3000 8000
```

**For HTTP (Development only):**

1. **Run the setup script:**
   ```bash
   ./setup-local.sh postgresql
   ```

2. **Start the backend:**
   ```bash
   ./start-backend.sh 8000 postgresql
   ```

3. **Start the frontend:**
   ```bash
   ./start-frontend.sh 3000 8000
   ```

### Option B: MySQL

1. **Run the setup script:**
   ```bash
   ./setup-local.sh mysql
   ```

2. **Start the backend:**
   ```bash
   ./start-backend.sh 8000 mysql
   ```

3. **Start the frontend:**
   ```bash
   ./start-frontend.sh 3000 8000
   ```

### Option C: SQLite (No Installation Required)

1. **Run the setup script:**
   ```bash
   ./setup-local.sh sqlite
   ```

2. **Start the backend:**
   ```bash
   ./start-backend.sh 8000 sqlite
   ```

3. **Start the frontend:**
   ```bash
   ./start-frontend.sh 3000 8000
   ```

### Custom Ports

```bash
# Backend on port 8080, MySQL database
./start-backend.sh 8080 mysql

# Backend on port 8080, SQLite database
./start-backend.sh 8080 sqlite

# Frontend on port 3001, connecting to backend on 8080
./start-frontend.sh 3001 8080
```

**Open your browser** to https://localhost:3000 (or http://localhost:3000 if not using SSL)

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

## HTTPS Setup (Required for Intranet Environments)

For intranet environments requiring HTTPS communication, follow these steps:

### 1. Generate SSL Certificates

```bash
# Generate self-signed certificates for development
./generate-ssl-certs.sh
```

This creates:
- `ssl/key.pem` - Private key
- `ssl/cert.pem` - Self-signed certificate

### 2. Start Services with HTTPS

```bash
# Backend will automatically use HTTPS if certificates exist
./start-backend.sh 8000 [database_type]

# Frontend will use HTTPS if certificates exist
./start-frontend.sh 3000 8000
```

### 3. Browser Certificate Warning

Since these are self-signed certificates, your browser will show a security warning:
1. Click "Advanced" 
2. Click "Proceed to localhost (unsafe)"
3. Accept the certificate for both frontend and backend

### 4. Production Certificates

For production intranet deployment, replace the self-signed certificates with:
- CA-issued certificates from your organization
- Internal certificate authority certificates
- Place them as `ssl/cert.pem` and `ssl/key.pem`

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
OAUTH_REDIRECT_URI=https://localhost:3000/auth/callback

# CORS (use HTTPS for intranet)
CORS_ORIGINS=["https://localhost:3000"]
```

### Frontend Environment Variables (.env)
```bash
# For HTTPS (recommended)
REACT_APP_API_URL=https://localhost:8000/api
REACT_APP_WS_URL=wss://localhost:8000

# For HTTP (development only)
# REACT_APP_API_URL=http://localhost:8000/api
# REACT_APP_WS_URL=ws://localhost:8000
```

## Database Setup

You can use PostgreSQL, MySQL, or SQLite as your database. Choose one of the options below.

### SQLite Installation (Easiest - No Setup Required)

SQLite is built into Python and requires no additional installation or configuration. The database file will be automatically created at `./data/annotation.db`.

**Advantages:**
- Zero configuration required
- Perfect for development and testing
- Database file is portable
- No server process to manage

**Usage:**
```bash
# Setup with SQLite
./setup-local.sh sqlite
./start-backend.sh 8000 sqlite
```

The database file will be created automatically in the `data/` directory.

### PostgreSQL Installation (Default)

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

#### PostgreSQL Issues

**Connection refused:**
- Make sure PostgreSQL service is running: `sudo systemctl status postgresql`
- Check if PostgreSQL is listening on port 5432: `netstat -an | grep 5432`

**Authentication failed:**
- Verify username/password are correct
- Check pg_hba.conf allows local connections (usually in /etc/postgresql/*/main/)

**Database does not exist:**
- Create it: `createdb -U annotation_user annotation_db`
- Or via SQL: `CREATE DATABASE annotation_db;`

**Permission denied for schema public:**
- Grant schema permissions: `GRANT ALL ON SCHEMA public TO annotation_user;`

#### MySQL Issues

**Connection refused:**
- Make sure MySQL service is running: `sudo systemctl status mysql` or `sudo systemctl status mysqld`
- Check if MySQL is listening on port 3306: `netstat -an | grep 3306`

**Access denied for user:**
- Verify username/password are correct
- Make sure user exists: `SELECT User, Host FROM mysql.user WHERE User='annotation_user';`
- Grant privileges: `GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';`

**Database does not exist:**
- Create it: `mysql -u root -p -e "CREATE DATABASE annotation_db;"`

**MySQL service failed to start:**
- Check logs: `sudo journalctl -u mysql` or `sudo journalctl -u mysqld`
- On some systems, initialize first: `sudo mysqld --initialize`

**Can't connect to MySQL server:**
- Check if MySQL socket exists: `ls -la /var/run/mysqld/mysqld.sock`
- Try connecting via TCP: `mysql -h 127.0.0.1 -P 3306 -u annotation_user -p`

#### General Issues

**PATH not working after installation:**
- Check which shell you're using: `echo $SHELL`
- Reload your shell config or open a new terminal
- Verify database tools are in PATH: `which psql` or `which mysql`

**Python dependencies fail to install:**
- For MySQL: Make sure you have build tools: `sudo apt install build-essential libmysqlclient-dev`
- For PostgreSQL: Make sure you have: `sudo apt install libpq-dev`

### MySQL Installation (Alternative)

#### macOS

**Option 1: Homebrew (Recommended)**
```bash
# Install MySQL
brew install mysql
brew services start mysql

# Secure installation (optional but recommended)
mysql_secure_installation

# Add MySQL to PATH (works for both bash and zsh)
if [[ "$SHELL" == *"zsh"* ]]; then
    echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
elif [[ "$SHELL" == *"bash"* ]]; then
    echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.bash_profile
    source ~/.bash_profile
fi

# Create database and user
mysql -u root -p -e "CREATE DATABASE annotation_db;"
mysql -u root -p -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

**Option 2: Official Installer**
```bash
# Download MySQL installer from https://dev.mysql.com/downloads/mysql/
# Follow installation instructions
# Add to PATH if needed
# Use MySQL Workbench or command line to create database
```

#### Linux

**Ubuntu 22.04/20.04 LTS (x86_64/ARM64):**
```bash
# Update package list
sudo apt update

# Install MySQL Server and Client
sudo apt install mysql-server mysql-client

# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql

# Check MySQL is running
sudo systemctl status mysql

# Secure installation (recommended)
sudo mysql_secure_installation

# Create database and user
sudo mysql -e "CREATE DATABASE annotation_db;"
sudo mysql -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Test connection
mysql -h localhost -u annotation_user -p annotation_db -e "SELECT version();"
```

**Ubuntu 18.04 (x86_64):**
```bash
# For older Ubuntu versions, you may need to add MySQL APT repository
wget https://dev.mysql.com/get/mysql-apt-config_0.8.29-1_all.deb
sudo dpkg -i mysql-apt-config_0.8.29-1_all.deb
sudo apt update

# Install MySQL
sudo apt install mysql-server mysql-client

# Continue with standard setup...
sudo systemctl start mysql
sudo systemctl enable mysql
sudo mysql_secure_installation

# Create database and user
sudo mysql -e "CREATE DATABASE annotation_db;"
sudo mysql -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

**Debian 12/11 (x86_64/ARM64):**
```bash
# Update package list
sudo apt update

# Install MySQL
sudo apt install default-mysql-server default-mysql-client
# OR for latest MySQL 8.0:
sudo apt install mysql-server mysql-client

# Start and enable service
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -e "CREATE DATABASE annotation_db;"
sudo mysql -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

**CentOS Stream 9/RHEL 9 (x86_64/ARM64):**
```bash
# Enable MySQL module and install
sudo dnf module reset mysql
sudo dnf module enable mysql:8.0
sudo dnf install mysql-server mysql

# Start and enable service
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Get temporary root password
sudo grep 'temporary password' /var/log/mysqld.log

# Secure installation
sudo mysql_secure_installation

# Create database and user
mysql -u root -p -e "CREATE DATABASE annotation_db;"
mysql -u root -p -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

**Fedora 38/39 (x86_64/ARM64):**
```bash
# Install MySQL Community Server
sudo dnf install mysql-server mysql

# Start and enable service
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Secure installation
sudo mysql_secure_installation

# Create database and user
mysql -u root -p -e "CREATE DATABASE annotation_db;"
mysql -u root -p -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

**CentOS 7 (x86_64) - Legacy:**
```bash
# Add MySQL Yum repository
wget https://dev.mysql.com/get/mysql80-community-release-el7-7.noarch.rpm
sudo rpm -Uvh mysql80-community-release-el7-7.noarch.rpm

# Install MySQL
sudo yum install mysql-server mysql

# Start and enable service
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Get temporary root password
sudo grep 'temporary password' /var/log/mysqld.log

# Secure installation
sudo mysql_secure_installation

# Create database and user
mysql -u root -p -e "CREATE DATABASE annotation_db;"
mysql -u root -p -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

**Arch Linux (x86_64/ARM64):**
```bash
# Install MySQL
sudo pacman -S mysql

# Initialize MySQL data directory
sudo mysqld --initialize --user=mysql --datadir=/var/lib/mysql

# Start and enable service
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Get initial root password
sudo cat /var/lib/mysql/[hostname].err | grep 'temporary password'

# Secure installation
sudo mysql_secure_installation

# Create database and user
mysql -u root -p -e "CREATE DATABASE annotation_db;"
mysql -u root -p -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

**OpenSUSE Leap/Tumbleweed (x86_64/ARM64):**
```bash
# Install MySQL
sudo zypper install mysql mysql-client

# Start and enable service
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation

# Create database and user
mysql -u root -p -e "CREATE DATABASE annotation_db;"
mysql -u root -p -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

**Alternative: MySQL via Docker (Any Linux x86_64/ARM64):**
```bash
# Run MySQL in Docker container
docker run --name mysql-annotation \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=annotation_db \
  -e MYSQL_USER=annotation_user \
  -e MYSQL_PASSWORD=annotation_pass \
  -p 3306:3306 \
  -d mysql:8.0

# Verify container is running
docker ps | grep mysql-annotation

# Test connection
mysql -h 127.0.0.1 -P 3306 -u annotation_user -p annotation_db -e "SELECT version();"
```

#### Windows

**Option 1: Official Installer (x86_64)**
```bash
# 1. Download MySQL installer from https://dev.mysql.com/downloads/installer/
# 2. Run installer and select "Server only" or "Full" installation
# 3. Configure root password during installation
# 4. Add MySQL to PATH (usually C:\Program Files\MySQL\MySQL Server 8.0\bin)
# 5. Open Command Prompt or PowerShell:

# Create database and user
mysql -u root -p -e "CREATE DATABASE annotation_db;"
mysql -u root -p -e "CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

### Verifying Database Installation

**PostgreSQL:**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection
psql -h localhost -U annotation_user -d annotation_db -c "SELECT version();"
```

**MySQL:**
```bash
# Check MySQL is running
mysqladmin -u annotation_user -p ping

# Test connection
mysql -h localhost -u annotation_user -p annotation_db -e "SELECT version();"
```

### Database Selection

**Setup with PostgreSQL (default):**
```bash
./setup-local.sh postgresql
./start-backend.sh 8000 postgresql
```

**Setup with MySQL:**
```bash
./setup-local.sh mysql
./start-backend.sh 8000 mysql
```

**Setup with SQLite:**
```bash
./setup-local.sh sqlite
./start-backend.sh 8000 sqlite
```

### Custom Database Configuration

If you have different database credentials, update the DATABASE_URL in `backend/.env`:

**For PostgreSQL:**
```bash
DATABASE_URL=postgresql+asyncpg://YOUR_USER:YOUR_PASSWORD@localhost:5432/YOUR_DATABASE
DATABASE_TYPE=postgresql
```

**For MySQL:**
```bash
DATABASE_URL=mysql+aiomysql://YOUR_USER:YOUR_PASSWORD@localhost:3306/YOUR_DATABASE
DATABASE_TYPE=mysql
```

**For SQLite:**
```bash
DATABASE_URL=sqlite+aiosqlite:///./data/YOUR_DATABASE.db
DATABASE_TYPE=sqlite
```

## Troubleshooting

### Backend Issues

**Database connection error:**
- **PostgreSQL:** Make sure PostgreSQL is running: `brew services start postgresql` (macOS)
- **PostgreSQL:** Check if database exists: `psql -l | grep annotation_db`
- **PostgreSQL:** Create database: `createdb annotation_db`
- **MySQL:** Make sure MySQL is running: `brew services start mysql` (macOS)
- **SQLite:** Check if `data/` directory exists and is writable

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
- Use a managed PostgreSQL or MySQL service (SQLite not recommended for production)
- Set proper SECRET_KEY (not the generated one)
- Configure proper CORS origins
- Use environment-specific .env files
- Set up Redis for real-time features
- Configure proper logging

**Database Recommendations by Use Case:**
- **Development/Testing:** SQLite (zero setup)
- **Small Production:** PostgreSQL or MySQL
- **Large Production:** PostgreSQL with proper scaling