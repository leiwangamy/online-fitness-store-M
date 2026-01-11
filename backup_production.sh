#!/bin/bash
# Production Database Backup Script
# Creates a backup and automatically keeps only the 3 most recent production backups

set -e  # Exit on error

BACKUP_DIR="$HOME/online-fitness-store-P/backups"
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

