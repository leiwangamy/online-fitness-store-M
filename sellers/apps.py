from django.apps import AppConfig


class SellersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sellers'
    verbose_name = 'Sellers'
    
    def ready(self):
        """Import admin when app is ready to ensure it's registered"""
        # Import admin module to trigger @admin.register decorator
        try:
            from . import admin  # noqa: F401
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Could not import sellers.admin: {e}')
