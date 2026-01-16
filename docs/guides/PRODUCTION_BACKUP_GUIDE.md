# Production Database Backup Guide

This guide explains how to backup your production database on EC2.

## Quick Backup Command

SSH to your EC2 server and run:

```bash
cd ~/online-fitness-store-M
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U fitness_user -F c -b fitness_club_db > "backups/fitness_club_db_prod_$(date +%Y-%m-%d_%H-%M-%S).backup"
```

## Step-by-Step Instructions

### Step 1: SSH to Your EC2 Instance

```bash
ssh -i your-key.pem ec2-user@ec2-15-223-56-68.ca-central-1.compute.amazonaws.com
```

(Replace `your-key.pem` with your actual SSH key file path)

### Step 2: Navigate to Your Project Directory

```bash
cd ~/online-fitness-store-M
```

### Step 3: Create Backups Directory (if it doesn't exist)

```bash
mkdir -p backups
```

### Step 4: Create the Backup

```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U fitness_user -F c -b fitness_club_db > "backups/fitness_club_db_prod_$(date +%Y-%m-%d_%H-%M-%S).backup"
```

This will create a backup file with a timestamp like:
- `backups/fitness_club_db_prod_2026-01-11_14-30-45.backup`

### Step 5: Verify the Backup

```bash
ls -lh backups/
```

You should see the backup file with a reasonable size (usually a few MB).

## Backup Options

### Option 1: Custom Format (Compressed) - Recommended

```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U fitness_user -F c -b fitness_club_db > "backups/fitness_club_db_prod_$(date +%Y-%m-%d_%H-%M-%S).backup"
```

**Pros:**
- Compressed (smaller file size)
- Can restore specific tables
- Includes blobs and large objects

### Option 2: SQL Format (Plain Text)

```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U fitness_user -F p fitness_club_db > "backups/fitness_club_db_prod_$(date +%Y-%m-%d_%H-%M-%S).sql"
```

**Pros:**
- Human-readable SQL
- Can edit before restoring
- Works with any PostgreSQL version

**Cons:**
- Larger file size
- Slower to restore

## Automated Backup Script

Create a backup script for easier use:

```bash
nano ~/online-fitness-store-M/backup_production.sh
```

Add this content:

```bash
#!/bin/bash
# Production Database Backup Script
# Creates a backup and automatically keeps only the 3 most recent production backups

set -e  # Exit on error

BACKUP_DIR="$HOME/online-fitness-store-M/backups"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/fitness_club_db_prod_$TIMESTAMP.backup"

# Create backups directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "========================================="
echo "Production Database Backup"
echo "========================================="
echo "Backup file: $BACKUP_FILE"
echo "Starting backup..."

# Create backup
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U fitness_user -F c -b fitness_club_db > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo ""
    echo "✅ Backup completed successfully!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $FILE_SIZE"
    
    # Clean up old production backups (keep only 3 most recent)
    echo ""
    echo "Cleaning up old production backups (keeping 3 most recent)..."
    cd "$BACKUP_DIR"
    
    # Find all production backups, sort by modification time (newest first), skip first 3, delete rest
    find . -name "fitness_club_db_prod_*.backup" -type f -printf '%T@ %p\n' | \
        sort -rn | \
        tail -n +4 | \
        cut -d' ' -f2- | \
        while read -r old_backup; do
            if [ -f "$old_backup" ]; then
                rm -f "$old_backup"
                echo "   Deleted: $(basename "$old_backup")"
            fi
        done
    
    REMAINING=$(find . -name "fitness_club_db_prod_*.backup" -type f | wc -l)
    echo "   Kept $REMAINING production backup(s)"
    
    echo ""
    echo "To restore this backup:"
    echo "   docker compose -f docker-compose.prod.yml exec -T db pg_restore -U fitness_user -d fitness_club_db --clean --if-exists < $BACKUP_FILE"
else
    echo ""
    echo "❌ Backup failed!"
    exit 1
fi
```

**Note:** This script automatically keeps only the 3 most recent production backups. Older backups are deleted automatically.

Make it executable:

```bash
chmod +x ~/online-fitness-store-M/backup_production.sh
```

Then run it:

```bash
~/online-fitness-store-M/backup_production.sh
```

## Download Backup to Local Machine

To download the backup to your local machine:

```bash
# From your local machine (PowerShell on Windows)
scp -i your-key.pem ec2-user@ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:~/online-fitness-store-M/backups/fitness_club_db_prod_*.backup ./
```

Or download a specific backup:

```bash
scp -i your-key.pem ec2-user@ec2-15-223-56-68.ca-central-1.compute.amazonaws.com:~/online-fitness-store-M/backups/fitness_club_db_prod_2026-01-11_14-30-45.backup ./backups/
```

## Restore from Backup

**⚠️ WARNING: Restoring will replace all current data!**

To restore a backup:

```bash
cd ~/online-fitness-store-M
docker compose -f docker-compose.prod.yml exec -T db pg_restore -U fitness_user -d fitness_club_db --clean --if-exists < backups/fitness_club_db_prod_YYYY-MM-DD_HH-MM-SS.backup
```

Or if you need to restore to a new database:

```bash
# Create new database first
docker compose -f docker-compose.prod.yml exec db psql -U fitness_user -c "CREATE DATABASE fitness_club_db_restore;"

# Restore to new database
docker compose -f docker-compose.prod.yml exec -T db pg_restore -U fitness_user -d fitness_club_db_restore < backups/fitness_club_db_prod_YYYY-MM-DD_HH-MM-SS.backup
```

## Schedule Automatic Backups (Optional)

To set up automatic daily backups using cron:

```bash
# Edit crontab
crontab -e

# Add this line to backup daily at 2 AM
0 2 * * * cd ~/online-fitness-store-M && docker compose -f docker-compose.prod.yml exec -T db pg_dump -U fitness_user -F c -b fitness_club_db > "backups/fitness_club_db_prod_$(date +\%Y-\%m-\%d_\%H-\%M-\%S).backup"

# Or use the backup script
0 2 * * * ~/online-fitness-store-M/backup_production.sh
```

## Clean Up Old Backups

To keep only the last 7 days of backups:

```bash
find ~/online-fitness-store-M/backups -name "fitness_club_db_prod_*.backup" -mtime +7 -delete
```

Or add to cron to run daily:

```bash
0 3 * * * find ~/online-fitness-store-M/backups -name "fitness_club_db_prod_*.backup" -mtime +7 -delete
```

## Backup Checklist

- [ ] SSH to EC2 server
- [ ] Navigate to project directory
- [ ] Create backups directory
- [ ] Run backup command
- [ ] Verify backup file exists and has reasonable size
- [ ] (Optional) Download backup to local machine
- [ ] (Optional) Set up automatic backups

## Troubleshooting

**Error: "docker compose: command not found"**
- Use `docker-compose` instead of `docker compose` (older versions)

**Error: "pg_dump: command not found"**
- Make sure you're running the command inside the Docker container using `docker compose exec`

**Error: "Permission denied"**
- Make sure the backups directory is writable: `chmod 755 backups/`

**Backup file is empty or very small**
- Check if the database container is running: `docker compose -f docker-compose.prod.yml ps`
- Check database connection: `docker compose -f docker-compose.prod.yml exec db psql -U fitness_user -d fitness_club_db -c "SELECT COUNT(*) FROM django_migrations;"`

