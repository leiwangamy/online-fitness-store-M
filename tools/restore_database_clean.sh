#!/bin/bash
# Clean restore script for Docker
# This script drops and recreates the database, then restores from backup

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; thenle>"
    echo "Example: ./restore_database_clean.sh backups/fitne
    echo "Usage: ./restore_database_clean.sh <backup_fiss_club_db_2025-12-26_01-22-21.backup"
    exit 1
fi

DB_NAME="fitness_club_db"
DB_USER="fitness_user"
CONTAINER_NAME="fitness_db"

echo "⚠️  WARNING: This will DROP and RECREATE the database!"
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Copy backup to container
echo "Copying backup to container..."
docker cp "$BACKUP_FILE" "$CONTAINER_NAME:/tmp/restore.backup"

# Drop and recreate database
echo "Dropping and recreating database..."
docker exec -e PGPASSWORD="Fitness123!" "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec -e PGPASSWORD="Fitness123!" "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"

# Restore
echo "Restoring backup..."
docker exec -e PGPASSWORD="Fitness123!" "$CONTAINER_NAME" pg_restore -U "$DB_USER" -d "$DB_NAME" --verbose /tmp/restore.backup

echo "✅ Restore complete!"

