# How to Restore PostgreSQL Database Backup

## Quick Start: Restore in Docker (Easiest Method)

**If you want a clean restore (drops existing database first):**

```powershell
# Step 1: Copy backup to container
docker cp backups/fitness_club_db_2025-12-26_01-22-21.backup fitness_db:/tmp/restore.backup

# Step 2: Drop and recreate database
$env:PGPASSWORD="Fitness123!"
docker exec fitness_db psql -U fitness_user -d postgres -c "DROP DATABASE IF EXISTS fitness_club_db;"
docker exec fitness_db psql -U fitness_user -d postgres -c "CREATE DATABASE fitness_club_db;"

# Step 3: Restore
docker exec fitness_db pg_restore -U fitness_user -d fitness_club_db --verbose /tmp/restore.backup
```

**If you want to restore without dropping (may have some errors but data will be restored):**

```powershell
# Copy backup and restore
docker cp backups/fitness_club_db_2025-12-26_01-22-21.backup fitness_db:/tmp/restore.backup
$env:PGPASSWORD="Fitness123!"
docker exec fitness_db pg_restore -U fitness_user -d fitness_club_db --clean --if-exists --verbose /tmp/restore.backup
```

---

## Method 1: Restore in Docker (Recommended)

If your database is running in Docker containers:

### Step 1: Make sure Docker containers are running
```bash
docker compose up -d db
```

### Step 2: Copy backup file to Docker container (if needed)
The backup file is already in your project folder, so you can access it from the container.

### Step 3: Restore using Docker exec
```bash
# Option A: Using pg_restore inside the database container
docker exec -i fitness_db pg_restore \
  -U fitness_user \
  -d fitness_club_db \
  --clean \
  --if-exists \
  --verbose \
  < backups/fitness_club_db_2025-12-26_01-22-21.backup

# Option B: Copy backup to container first, then restore
docker cp backups/fitness_club_db_2025-12-26_01-22-21.backup fitness_db:/tmp/backup.backup
docker exec -i fitness_db pg_restore \
  -U fitness_user \
  -d fitness_club_db \
  --clean \
  --if-exists \
  --verbose \
  /tmp/backup.backup
```

### Step 4: Set PGPASSWORD environment variable (to avoid password prompt)
```powershell
# Windows PowerShell
$env:PGPASSWORD="Fitness123!"
docker exec -i fitness_db pg_restore -U fitness_user -d fitness_club_db --clean --if-exists --verbose < backups/fitness_club_db_2025-12-26_01-22-21.backup
```

---

## Method 2: Restore from Host Machine (Local PostgreSQL)

If you have PostgreSQL installed locally and want to restore to a local database:

### Step 1: Activate virtual environment
```bash
venv\Scripts\activate
```

### Step 2: Run the restore script
```bash
python tools/restore_postgres.py backups/fitness_club_db_2025-12-26_01-22-21.backup
```

### Step 3: Or use pg_restore directly
```bash
# Set password (Windows PowerShell)
$env:PGPASSWORD="Fitness123!"

# Restore
pg_restore -U fitness_user -h localhost -p 5432 -d fitness_club_db --clean --if-exists --verbose backups/fitness_club_db_2025-12-26_01-22-21.backup
```

---

## Method 3: Restore to Docker from Host

If you want to restore from your host machine to the Docker database:

### Step 1: Make sure Docker database is running
```bash
docker compose up -d db
```

### Step 2: Restore using pg_restore from host
```powershell
# Windows PowerShell - Set password
$env:PGPASSWORD="Fitness123!"

# Restore (connecting to Docker database on localhost:5432)
pg_restore -U fitness_user -h localhost -p 5432 -d fitness_club_db --clean --if-exists --verbose backups/fitness_club_db_2025-12-26_01-22-21.backup
```

---

## Important Notes

⚠️ **WARNING**: Restoring will REPLACE all existing data in the database!

### Before Restoring:
1. **Backup current data** (if you have important changes):
   ```bash
   python tools/backup_postgres.py
   ```

2. **Stop the web application** (if running):
   ```bash
   docker compose stop web
   ```

### After Restoring:
1. **Restart the web application**:
   ```bash
   docker compose up -d
   ```

2. **Run migrations** (if needed):
   ```bash
   docker compose exec web python manage.py migrate
   ```

3. **Verify the data**:
   - Check Django admin
   - Verify your data is restored correctly

---

## Troubleshooting

### Error: "database does not exist"
Create the database first:
```bash
docker exec -i fitness_db createdb -U fitness_user fitness_club_db
```

### Error: "connection refused"
Make sure the database container is running:
```bash
docker compose ps
docker compose up -d db
```

### Error: "permission denied"
Check that the backup file is readable and the database user has proper permissions.

### Error: "pg_restore: error: input file appears to be a text format dump"
If your backup is in SQL format (`.sql`), use `psql` instead:
```bash
docker exec -i fitness_db psql -U fitness_user -d fitness_club_db < backups/your_backup.sql
```

---

## Quick Reference

**List available backups:**
```bash
ls backups/
```

**Check database connection:**
```bash
docker exec -i fitness_db psql -U fitness_user -d fitness_club_db -c "\dt"
```

**View database size:**
```bash
docker exec -i fitness_db psql -U fitness_user -d fitness_club_db -c "SELECT pg_size_pretty(pg_database_size('fitness_club_db'));"
```

