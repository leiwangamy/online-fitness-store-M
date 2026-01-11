"""
Database backup script for PostgreSQL
Run from project root: python tools/backup_postgres.py
Or from tools folder: python backup_postgres.py
"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Setup Django to get settings
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_club.fitness_club.settings')

import django
django.setup()

from django.conf import settings

# -------------------------------
# Database settings from Django settings
# -------------------------------
db_config = settings.DATABASES['default']
DB_NAME = db_config['NAME']
DB_USER = db_config['USER']
DB_PASSWORD = db_config.get('PASSWORD', '')
DB_HOST = db_config.get('HOST', 'localhost')
DB_PORT = db_config.get('PORT', '5432')

# -------------------------------
# Paths (configurable)
# -------------------------------
# Try to find pg_dump in common locations
PG_DUMP_PATH = os.getenv('PG_DUMP_PATH', None)
if not PG_DUMP_PATH:
    # Common PostgreSQL installation paths
    possible_paths = [
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\13\bin\pg_dump.exe",
        "pg_dump",  # If in PATH
    ]
    for path in possible_paths:
        if path == "pg_dump" or os.path.exists(path):
            PG_DUMP_PATH = path
            break

if not PG_DUMP_PATH:
    print("❌ Error: pg_dump not found. Please set PG_DUMP_PATH environment variable.")
    print("   Example: set PG_DUMP_PATH=C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe")
    sys.exit(1)

# Backup directory (relative to project root)
BACKUP_DIR = Path(project_root) / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = BACKUP_DIR / f"{DB_NAME}_{timestamp}.backup"

# -------------------------------
# Environment (avoid password prompt)
# -------------------------------
env = os.environ.copy()
if DB_PASSWORD:
    env["PGPASSWORD"] = DB_PASSWORD

# -------------------------------
# pg_dump command
# -------------------------------
command = [
    PG_DUMP_PATH,
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-F", "c",  # Custom format (compressed)
    "-b",      # Include blobs
    "-v",      # Verbose
    "-f", str(backup_file),
    DB_NAME,
]

print("=" * 70)
print("POSTGRESQL DATABASE BACKUP")
print("=" * 70)
print(f"\nDatabase: {DB_NAME}")
print(f"Host: {DB_HOST}:{DB_PORT}")
print(f"User: {DB_USER}")
print(f"Backup directory: {BACKUP_DIR}")
print(f"Output file: {backup_file}")
print(f"\nStarting backup...")

result = subprocess.run(
    command,
    env=env,
    capture_output=True,
    text=True,
)

# -------------------------------
# Result handling
# -------------------------------
if result.returncode == 0:
    file_size = backup_file.stat().st_size / (1024 * 1024)  # Size in MB
    print(f"\n✅ Backup completed successfully!")
    print(f"   File: {backup_file}")
    print(f"   Size: {file_size:.2f} MB")
    
    # Clean up old local backups (keep only 3 most recent)
    # Only delete files that match the local backup pattern (without "prod" in name)
    local_backups = sorted(
        [f for f in BACKUP_DIR.glob(f"{DB_NAME}_*.backup") if "prod" not in f.name],
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    
    if len(local_backups) > 3:
        backups_to_delete = local_backups[3:]
        print(f"\nCleaning up old local backups (keeping 3 most recent)...")
        for old_backup in backups_to_delete:
            try:
                old_backup.unlink()
                print(f"   Deleted: {old_backup.name}")
            except Exception as e:
                print(f"   Warning: Could not delete {old_backup.name}: {e}")
        print(f"   Kept {len(local_backups) - len(backups_to_delete)} local backup(s)")
    
    print(f"\nTo restore this backup:")
    print(f"   pg_restore -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} {backup_file}")
else:
    print(f"\n❌ Backup failed!")
    print(f"   Error code: {result.returncode}")
    if result.stderr:
        print(f"\nError output:")
        print(result.stderr)
    if result.stdout:
        print(f"\nStandard output:")
        print(result.stdout)
    sys.exit(1)
