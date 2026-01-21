from django.db import OperationalError, ProgrammingError


def membership_context(request):
    """Add user's membership information to template context"""
    context = {
        'user_membership': None,
        'user_platform_memberships': [],
        'user_seller_memberships': [],
        'user_membership_status': "None",
        'user_seller_membership_status': "None",
        'has_platform_membership': False,
        'has_seller_membership': False,
    }
    
    try:
        from .models import MemberProfile, MembershipPlan, UserMembership
        
        if request.user.is_authenticated:
            try:
                membership = request.user.membership
                context['user_membership'] = membership
                
                # Get all active memberships using UserMembership model
                active_memberships = membership.get_active_memberships()
                
                # Separate platform and seller memberships
                platform_memberships = []
                seller_memberships = []
                
                for user_membership in active_memberships:
                    plan_obj = user_membership.get_plan_object()
                    if not plan_obj:
                        continue
                    
                    if user_membership.plan_type == 'platform':
                        platform_memberships.append({
                            'plan': plan_obj,
                            'user_membership': user_membership,
                        })
                    else:  # seller
                        seller_memberships.append({
                            'plan': plan_obj,
                            'user_membership': user_membership,
                            'seller': plan_obj.seller if hasattr(plan_obj, 'seller') else None,
                        })
                
                context['user_platform_memberships'] = platform_memberships
                context['user_seller_memberships'] = seller_memberships
                context['has_platform_membership'] = len(platform_memberships) > 0
                context['has_seller_membership'] = len(seller_memberships) > 0
                
                # Set status strings for display
                if platform_memberships:
                    plan_names = [m['plan'].name for m in platform_memberships]
                    context['user_membership_status'] = ", ".join(plan_names) if len(plan_names) == 1 else f"{len(plan_names)} Plans"
                else:
                    context['user_membership_status'] = "None"
                
                if seller_memberships:
                    seller_names = []
                    for m in seller_memberships:
                        seller_name = m['seller'].display_name if m.get('seller') and m['seller'].display_name else (m['seller'].user.username if m.get('seller') else '')
                        plan_name = m['plan'].name
                        seller_names.append(f"{seller_name} - {plan_name}" if seller_name else plan_name)
                    context['user_seller_membership_status'] = ", ".join(seller_names) if len(seller_names) == 1 else f"{len(seller_names)} Plans"
                else:
                    context['user_seller_membership_status'] = "None"
                    
            except MemberProfile.DoesNotExist:
                context['user_membership'] = None
                context['user_membership_status'] = "None"
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - return default values
        pass
    except Exception:
        # Any other error - return default values
        pass
    
    return context
