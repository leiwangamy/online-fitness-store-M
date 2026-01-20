"""
Admin views for custom admin panel actions
"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse, FileResponse, HttpResponseServerError
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import AdminSettings


@staff_member_required
@require_http_methods(["POST"])
def toggle_platform_membership(request):
    """Toggle platform membership visibility"""
    try:
        admin_settings = AdminSettings.get_instance()
        # Use new field if exists, fallback to old field for migration compatibility
        if hasattr(admin_settings, 'show_platform_membership'):
            admin_settings.show_platform_membership = not admin_settings.show_platform_membership
            admin_settings.save()
            status = "shown" if admin_settings.show_platform_membership else "hidden"
        else:
            # Fallback for migration period
            admin_settings.show_membership_functions = not admin_settings.show_membership_functions
            admin_settings.save()
            status = "shown" if admin_settings.show_membership_functions else "hidden"
        messages.success(request, f"Platform membership is now {status}.")
    except Exception as e:
        messages.error(request, f"Error toggling platform membership visibility: {str(e)}")
    
    return redirect("admin:index")


@staff_member_required
@require_http_methods(["POST"])
def toggle_seller_membership(request):
    """Toggle seller membership visibility"""
    try:
        admin_settings = AdminSettings.get_instance()
        admin_settings.show_seller_membership = not admin_settings.show_seller_membership
        admin_settings.save()
        status = "shown" if admin_settings.show_seller_membership else "hidden"
        messages.success(request, f"Seller membership is now {status}.")
    except Exception as e:
        messages.error(request, f"Error toggling seller membership visibility: {str(e)}")
    
    return redirect("admin:index")


@staff_member_required
@require_http_methods(["GET", "POST"])
def backup_database(request):
    """Create a database backup and return it as a downloadable file"""
    try:
        # Setup Django to get settings
        db_config = settings.DATABASES['default']
        DB_NAME = db_config['NAME']
        DB_USER = db_config['USER']
        DB_PASSWORD = db_config.get('PASSWORD', '')
        DB_HOST = db_config.get('HOST', 'localhost')
        DB_PORT = db_config.get('PORT', '5432')
        
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
            messages.error(request, "pg_dump not found. Please set PG_DUMP_PATH environment variable.")
            return redirect("admin:index")
        
        # Create backup directory
        project_root = Path(settings.BASE_DIR)
        BACKUP_DIR = project_root / "backups"
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = BACKUP_DIR / f"{DB_NAME}_{timestamp}.backup"
        
        # Environment (avoid password prompt)
        env = os.environ.copy()
        if DB_PASSWORD:
            env["PGPASSWORD"] = DB_PASSWORD
        
        # pg_dump command
        command = [
            PG_DUMP_PATH,
            "-U", DB_USER,
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-F", "c",  # Custom format (compressed)
            "-b",      # Include blobs
            "-f", str(backup_file),
            DB_NAME,
        ]
        
        # Run backup
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            messages.error(request, f"Database backup failed: {error_msg}")
            return redirect("admin:index")
        
        # Check if file was created
        if not backup_file.exists():
            messages.error(request, "Backup file was not created.")
            return redirect("admin:index")
        
        # Return file as download
        file_size = backup_file.stat().st_size
        response = FileResponse(
            open(backup_file, 'rb'),
            content_type='application/octet-stream',
            as_attachment=True,
            filename=backup_file.name
        )
        response['Content-Length'] = file_size
        
        messages.success(request, f"Database backup created successfully! ({file_size / (1024*1024):.2f} MB)")
        return response
        
    except Exception as e:
        messages.error(request, f"Error creating database backup: {str(e)}")
        return redirect("admin:index")

