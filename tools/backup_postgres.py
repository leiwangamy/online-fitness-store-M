import os
import subprocess
from datetime import datetime
from pathlib import Path

# -------------------------------
# Database settings (same as Django defaults)
# -------------------------------
DB_NAME = os.getenv("POSTGRES_DB", "fitness_club_db")
DB_USER = os.getenv("POSTGRES_USER", "fitness_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Fitness123!")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# -------------------------------
# Paths
# -------------------------------
PG_DUMP_PATH = r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"
BACKUP_DIR = Path(r"C:\Users\Lei\Documents\VS Code Projects\Backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
backup_file = BACKUP_DIR / f"{DB_NAME}_{timestamp}.backup"

# -------------------------------
# Environment (avoid password prompt)
# -------------------------------
env = os.environ.copy()
env["PGPASSWORD"] = "Fitness123!"

# -------------------------------
# pg_dump command
# -------------------------------
command = [
    PG_DUMP_PATH,
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-F", "c",
    "-b",
    "-v",
    "-f", str(backup_file),
    DB_NAME,
]

print("Starting database backup...")
print(f"Output file: {backup_file}")

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
    print("✅ Backup completed successfully.")
else:
    print("❌ Backup failed.")
    print(result.stderr)
