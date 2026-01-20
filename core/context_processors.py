"""
Context processors for core app
"""
from .models import AdminSettings


def admin_settings(request):
    """Add admin settings to template context for all users (needed to hide/show membership links)"""
    try:
        admin_settings = AdminSettings.get_instance()
        # Ensure new fields exist (for migration compatibility)
        if not hasattr(admin_settings, 'show_platform_membership'):
            admin_settings.show_platform_membership = admin_settings.show_membership_functions
        if not hasattr(admin_settings, 'show_seller_membership'):
            admin_settings.show_seller_membership = True  # Default seller membership to visible
        return {
            'admin_settings': admin_settings,
        }
    except Exception:
        # If AdminSettings doesn't exist yet (before migration), return defaults
        class DefaultAdminSettings:
            show_membership_functions = True
            show_platform_membership = True
            show_seller_membership = True
        return {
            'admin_settings': DefaultAdminSettings(),
        }


def membership_availability(request):
    """Check if admin and seller membership plans are available"""
    has_admin_plans = False
    has_seller_plans = False
    seller_plans = []
    
    try:
        from members.models import MembershipPlan
        from sellers.models import SellerMembershipPlan
        
        # Check if membership functions are enabled
        try:
            admin_settings = AdminSettings.get_instance()
            # Use new fields if available, fallback to old field for migration
            platform_enabled = getattr(admin_settings, 'show_platform_membership', admin_settings.show_membership_functions)
            seller_enabled = getattr(admin_settings, 'show_seller_membership', True)
        except Exception:
            platform_enabled = True  # Default to enabled if settings don't exist
            seller_enabled = True
        
        # Check if admin membership plans exist and are active
        if platform_enabled:
            has_admin_plans = MembershipPlan.objects.filter(is_active=True).exists()
        
        # Check if seller membership plans exist and are active (only if seller membership is enabled)
        if seller_enabled:
            seller_plans = SellerMembershipPlan.objects.filter(is_active=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
            has_seller_plans = seller_plans.exists()
        else:
            seller_plans = []
            has_seller_plans = False
    except Exception:
        # If models don't exist or error occurs, default to False
        pass
    
    return {
        'has_admin_membership': has_admin_plans,
        'has_platform_membership': has_admin_plans,  # Alias for consistency
        'has_seller_membership': has_seller_plans,
        'has_both_memberships': has_admin_plans and has_seller_plans,
        'seller_plans': list(seller_plans) if seller_plans else [],
    }

