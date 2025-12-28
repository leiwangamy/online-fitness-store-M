"""
Database restore script for PostgreSQL
Run from project root: python tools/restore_postgres.py <backup_file>
Or from tools folder: python restore_postgres.py <backup_file>

Example:
    python tools/restore_postgres.py backups/fitness_club_db_2025-12-26_01-22-21.backup
"""
import os
import sys
import subprocess
from pathlib import Path

# Setup Django to get settings
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_club.fitness_club.settings')

import django
django.setup()

from django.conf import settings

# -------------------------------
# Get backup file from command line
# -------------------------------
if len(sys.argv) < 2:
    print("=" * 70)
    print("POSTGRESQL DATABASE RESTORE")
    print("=" * 70)
    print("\n❌ Error: Please provide the backup file path.")
    print("\nUsage:")
    print("  python tools/restore_postgres.py <backup_file>")
    print("\nExample:")
    print("  python tools/restore_postgres.py backups/fitness_club_db_2025-12-26_01-22-21.backup")
    print("\nAvailable backups:")
    backup_dir = Path(project_root) / "backups"
    if backup_dir.exists():
        backups = list(backup_dir.glob("*.backup"))
        if backups:
            for i, backup in enumerate(sorted(backups, reverse=True), 1):
                size_mb = backup.stat().st_size / (1024 * 1024)
                print(f"  {i}. {backup.name} ({size_mb:.2f} MB)")
        else:
            print("  No backup files found.")
    sys.exit(1)

backup_file = Path(sys.argv[1])
if not backup_file.is_absolute():
    backup_file = Path(project_root) / backup_file

if not backup_file.exists():
    print(f"❌ Error: Backup file not found: {backup_file}")
    sys.exit(1)

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
# Find pg_restore
# -------------------------------
PG_RESTORE_PATH = os.getenv('PG_RESTORE_PATH', None)
if not PG_RESTORE_PATH:
    # Common PostgreSQL installation paths
    possible_paths = [
        r"C:\Program Files\PostgreSQL\16\bin\pg_restore.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_restore.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_restore.exe",
        r"C:\Program Files\PostgreSQL\13\bin\pg_restore.exe",
        "pg_restore",  # If in PATH
    ]
    for path in possible_paths:
        if path == "pg_restore" or os.path.exists(path):
            PG_RESTORE_PATH = path
            break

if not PG_RESTORE_PATH:
    print("❌ Error: pg_restore not found. Please set PG_RESTORE_PATH environment variable.")
    print("   Example: set PG_RESTORE_PATH=C:\\Program Files\\PostgreSQL\\16\\bin\\pg_restore.exe")
    sys.exit(1)

# -------------------------------
# Confirmation
# -------------------------------
print("=" * 70)
print("POSTGRESQL DATABASE RESTORE")
print("=" * 70)
print(f"\n⚠️  WARNING: This will REPLACE all data in the database!")
print(f"\nDatabase: {DB_NAME}")
print(f"Host: {DB_HOST}:{DB_PORT}")
print(f"User: {DB_USER}")
print(f"Backup file: {backup_file}")
print(f"File size: {backup_file.stat().st_size / (1024 * 1024):.2f} MB")

response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("❌ Restore cancelled.")
    sys.exit(0)

# -------------------------------
# Environment (avoid password prompt)
# -------------------------------
env = os.environ.copy()
if DB_PASSWORD:
    env["PGPASSWORD"] = DB_PASSWORD

# -------------------------------
# Drop existing database objects (optional - use with caution)
# -------------------------------
print("\n⚠️  Note: If the database already has data, you may need to:")
print("   1. Drop the database and recreate it, OR")
print("   2. Use --clean flag to drop objects before restoring")
print("\nProceeding with restore (using --clean flag)...")

# -------------------------------
# pg_restore command
# -------------------------------
command = [
    PG_RESTORE_PATH,
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-d", DB_NAME,
    "--clean",      # Clean (drop) database objects before recreating
    "--if-exists",  # Don't error if objects don't exist
    "--verbose",    # Verbose output
    str(backup_file),
]

print(f"\nStarting restore...")
print(f"Command: {' '.join(command)}")

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
    print(f"\n✅ Restore completed successfully!")
    print(f"\nNext steps:")
    print(f"   1. Verify the data in your Django admin or database")
    print(f"   2. Run migrations if needed: python manage.py migrate")
else:
    print(f"\n❌ Restore failed!")
    print(f"   Error code: {result.returncode}")
    if result.stderr:
        print(f"\nError output:")
        print(result.stderr)
    if result.stdout:
        print(f"\nStandard output:")
        print(result.stdout)
    
    # Common error: database doesn't exist
    if "does not exist" in result.stderr or "database" in result.stderr.lower():
        print(f"\n💡 Tip: If the database doesn't exist, create it first:")
        print(f"   createdb -U {DB_USER} -h {DB_HOST} -p {DB_PORT} {DB_NAME}")
    
    sys.exit(1)

