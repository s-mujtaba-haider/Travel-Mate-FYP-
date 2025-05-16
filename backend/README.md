# Places RAG Project Setup Guide

A comprehensive guide for setting up the Places RAG project environment on Windows and Ubuntu systems.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ database server

## Database Setup

### 1. Install PostgreSQL
- Windows: Download and install from [PostgreSQL official website](https://www.postgresql.org/download)
- Ubuntu: 
  ```bash
  sudo apt update
  sudo apt install postgresql postgresql-contrib
  ```

### 2. Create Database and Enable Extensions
Connect to PostgreSQL and run:
```sql
CREATE DATABASE your_database_name;
\c your_database_name
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

## Environment Setup

### Option 1: Using UV (Recommended)

1. **Install UV**
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Ubuntu
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create Virtual Environment**
   ```bash
   uv python install 3.11
   uv venv --python 3.11
   ```

3. **Activate Virtual Environment**
   ```bash
   # Windows
   .\.venv\Scripts\activate

   # Ubuntu
   source .venv/bin/activate
   ```

4. **Install Dependencies**
   ```bash
   uv sync
   ```

### Option 2: Using venv

1. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv .venv

   # Ubuntu
   python3 -m venv .venv
   ```

2. **Activate Virtual Environment**
   ```bash
   # Windows
   .\.venv\Scripts\activate

   # Ubuntu
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Environment Variables
Create `.env` file in the project root:
```ini
DB_USERNAME="db_username"
DB_PASSWORD="password"
DB_HOST="localhost"  # or your host
DB_PORT=5432        # or your port
DB_NAME="db_name"
```

### 2. Alembic Configuration
Update `alembic.ini`:
```ini
sqlalchemy.url = postgresql://username:password@localhost:5432/your_database_name
```

## Database Migration

Run migrations:
```bash
alembic upgrade head
```

## Running the Application

```bash
# Development server
fastapi dev main.py

# Production server
fastapi main.py
```

## API Documentation

### Accessing the Documentation
Navigate to `http://127.0.0.1:8000/docs` in your browser to view the Swagger UI documentation.

A Postman collection is also included for alternative testing.

### API Sections

1. **User APIs**
   - User creation and management endpoints

2. **Session APIs**
   - Session management endpoints

3. **Chat APIs**
   - Chat interaction endpoints

### Authentication
For protected endpoints (marked with a lock icon):
1. Click the "Authorize" button at the top or the lock icon
2. Add JWT token as `Bearer <token>`
3. Token can be obtained from the Login API

### Testing APIs
1. Select an endpoint
2. Click "Try it out"
3. Edit the request JSON
4. Click "Execute"



## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL service is running
- Check PostgreSQL version (15+ required)
- Validate credentials in `.env` and `alembic.ini`
- Ensure database exists and is accessible
- Check network connectivity to database host

### Python Environment Issues
- Verify Python version:
  ```bash
  python --version  # Should be 3.11+
  ```
- Confirm virtual environment activation
- Check dependency installation status

### Permission Issues (Ubuntu)
- Use `sudo` for PostgreSQL administrative commands
- Check file and directory permissions
- Ensure proper user access to PostgreSQL

### Common Error Messages
1. "Database connection refused"
   - Check if PostgreSQL service is running
   - Verify port configuration

2. "Module not found"
   - Verify virtual environment activation
   - Reinstall dependencies

3. "Permission denied"
   - Check file/directory permissions
   - Verify database user privileges

For additional support, please create an issue in the project repository.