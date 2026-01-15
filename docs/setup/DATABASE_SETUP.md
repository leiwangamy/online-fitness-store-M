# PostgreSQL Database Setup Guide

## Step 1: Install PostgreSQL Driver

The `psycopg2-binary` package has been added to `requirements.txt`. Install it:

```bash
pip install psycopg2-binary
```

Or install all requirements:
```bash

```

## Step 2: Create PostgreSQL Database and User

Open PostgreSQL command line (psql) or pgAdmin and run:

```sql
-- Create database
CREATE DATABASE fitness_club_db;

-- Create user (if it doesn't exist)
CREATE USER fitness_user WITH PASSWORD 'Fitness123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fitness_club_db TO fitness_user;

-- If using PostgreSQL 15+, you may also need:
ALTER DATABASE fitness_club_db OWNER TO fitness_user;
```

## Step 3: Verify PostgreSQL is Running

**Windows:**
- Check Services (services.msc) - look for "postgresql" service
- Or run: `pg_ctl status` in command prompt

**Linux/Mac:**
```bash
sudo systemctl status postgresql
# or
pg_ctl status
```

## Step 4: Test Connection

You can test the connection using Django:

```bash
python manage.py dbshell
```

Or test with Python:
```python
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    database="fitness_club_db",
    user="fitness_user",
    password="Fitness123!",
    port="5432"
)
print("Connection successful!")
conn.close()
```

## Step 5: Run Migrations

Once connected, create the database tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Troubleshooting

### Error: "could not connect to server"
- **Solution:** Make sure PostgreSQL service is running

### Error: "database does not exist"
- **Solution:** Create the database using the SQL commands above

### Error: "password authentication failed"
- **Solution:** Check the password in settings.py matches the PostgreSQL user password

### Error: "permission denied"
- **Solution:** Grant privileges to the user (see Step 2)

### Using Environment Variables (Recommended)

Create a `.env` file in your project root:

```
POSTGRES_DB=fitness_club_db
POSTGRES_USER=fitness_user
POSTGRES_PASSWORD=Fitness123!
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

This way, you don't hardcode credentials in settings.py.

