# Docker Setup for Online Fitness Store

This project is containerized using Docker and Docker Compose.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd online-fitness-store
   ```

2. **Create `.env` file:**
   ```bash
   # Copy the example or create your own
   # Required variables:
   DJANGO_SECRET_KEY=your-secret-key-here
   DJANGO_DEBUG=1
   POSTGRES_DB=fitness_club_db
   POSTGRES_USER=fitness_user
   POSTGRES_PASSWORD=your-secure-password
   DB_HOST=db
   POSTGRES_PORT=5432
   ```

3. **Build and start containers:**
   ```bash
   docker compose up --build
   ```

4. **Access the application:**
   - Web app: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Database: localhost:5432

## Docker Commands

### Start containers (detached mode):
```bash
docker compose up -d
```

### Stop containers:
```bash
docker compose down
```

### View logs:
```bash
docker compose logs -f
```

### Rebuild after code changes:
```bash
docker compose up --build
```

### Run Django management commands:
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic
```

### Access database:
```bash
docker compose exec db psql -U fitness_user -d fitness_club_db
```

## Project Structure

- `Dockerfile` - Web application container definition
- `docker-compose.yml` - Multi-container orchestration
- `.dockerignore` - Files excluded from Docker build context
- `.env` - Environment variables (not in git, create your own)

## Database

The PostgreSQL database runs in a separate container with persistent storage. Data persists in a Docker volume even after containers are stopped.

### Backup Database:
```bash
python tools/backup_postgres.py
```

### Restore Database:
See `RESTORE_DATABASE.md` for detailed instructions.

## Development vs Production

**Development (current setup):**
- Uses `runserver` for Django
- Debug mode enabled
- Hot-reload enabled via volume mounts

**Production (recommended changes):**
- Use a production WSGI server (gunicorn, uwsgi)
- Set `DJANGO_DEBUG=0` in `.env`
- Use a reverse proxy (nginx)
- Set up proper SSL/TLS
- Use environment-specific secrets

## Troubleshooting

### Containers won't start:
- Check if ports 8000 and 5432 are available
- Verify Docker Desktop is running
- Check logs: `docker compose logs`

### Database connection errors:
- Ensure database container is running: `docker compose ps`
- Check `.env` file has correct database credentials
- Verify `DB_HOST=db` in `.env` (not `localhost`)

### Permission errors:
- On Linux/Mac, you may need to adjust file permissions
- Check Docker volume permissions

## Notes

- The `.env` file is git-ignored for security
- Database backups are stored in `backups/` (also git-ignored)
- Media files are stored in `media/` (git-ignored)
- Static files are served from `static/` directory

